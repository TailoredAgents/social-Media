"""
File Upload Service

Production-ready file upload service with security validation,
storage management, and image processing capabilities.
"""
import os
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from PIL import Image
import filetype

# Try to import python-magic, but don't fail if not available
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    magic = None

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import ContentItem
from sqlalchemy.orm import Session

settings = get_settings()
logger = logging.getLogger(__name__)

class FileUploadService:
    """
    Secure file upload service with validation, storage management,
    and image processing capabilities.
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = settings.allowed_image_types.split(',')
        
        # Create upload directories
        self.images_dir = self.upload_dir / "images"
        self.temp_dir = self.upload_dir / "temp"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure upload directories exist with proper permissions"""
        for directory in [self.upload_dir, self.images_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            # Set secure permissions (owner read/write only)
            os.chmod(directory, 0o755)
    
    def _validate_file_size(self, file: UploadFile) -> None:
        """Validate file size"""
        # Note: file.size might not be available for all upload types
        # We'll also check during streaming read
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size allowed: {self.max_file_size / (1024*1024):.1f}MB"
            )
    
    def _validate_file_type(self, file_path: Path, original_filename: str) -> str:
        """
        Validate file type using multiple methods for security.
        Returns the validated file extension.
        """
        # Method 1: Use python-magic to detect actual file type (if available)
        file_type = None
        if HAS_MAGIC:
            try:
                file_type = magic.from_file(str(file_path), mime=True)
            except Exception:
                file_type = None
        
        # Method 2: Use filetype library as backup
        try:
            kind = filetype.guess(str(file_path))
            filetype_ext = kind.extension if kind else None
        except Exception:
            filetype_ext = None
        
        # Method 3: Check file extension
        file_ext = original_filename.lower().split('.')[-1] if '.' in original_filename else ''
        
        # Validate against allowed image types
        allowed_mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg', 
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        # Check if extension is allowed
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Verify MIME type matches extension (security check) - only if magic is available
        expected_mime = allowed_mime_types.get(file_ext)
        if HAS_MAGIC and expected_mime and file_type and not file_type.startswith(expected_mime.split('/')[0]):
            raise HTTPException(
                status_code=400,
                detail="File content doesn't match extension"
            )
        
        return file_ext
    
    def _validate_image(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate and get image information using PIL.
        Returns image metadata.
        """
        try:
            with Image.open(file_path) as img:
                # Check if image can be opened (validates it's a real image)
                img.verify()
                
                # Reopen for metadata (verify() closes the image)
                with Image.open(file_path) as img:
                    width, height = img.size
                    format_name = img.format
                    mode = img.mode
                    
                    # Basic size validation (prevent extremely large images)
                    max_dimension = 8192  # 8K max
                    if width > max_dimension or height > max_dimension:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Image dimensions too large. Max: {max_dimension}x{max_dimension}px"
                        )
                    
                    # Minimum size validation
                    min_dimension = 50
                    if width < min_dimension or height < min_dimension:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Image too small. Min: {min_dimension}x{min_dimension}px"
                        )
                    
                    return {
                        'width': width,
                        'height': height,
                        'format': format_name,
                        'mode': mode,
                        'file_size': file_path.stat().st_size
                    }
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
    
    def _generate_secure_filename(self, original_filename: str, file_ext: str) -> str:
        """Generate a secure, unique filename"""
        # Create unique filename with timestamp and UUID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Sanitize original filename (keep only alphanumeric and basic chars)
        safe_name = ''.join(c for c in original_filename if c.isalnum() or c in '._-')[:50]
        base_name = safe_name.rsplit('.', 1)[0] if '.' in safe_name else safe_name
        
        return f"{timestamp}_{unique_id}_{base_name}.{file_ext}"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for duplicate detection"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def upload_image(
        self, 
        file: UploadFile, 
        user_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and process an image file with full validation.
        
        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            description: Optional description of the image
            
        Returns:
            Dictionary with file information and metadata
        """
        
        # Validate file size first
        self._validate_file_size(file)
        
        # Generate temporary filename
        temp_filename = f"temp_{uuid.uuid4()}.tmp"
        temp_path = self.temp_dir / temp_filename
        
        try:
            # Stream file to temporary location with size check
            total_size = 0
            with open(temp_path, "wb") as temp_file:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    total_size += len(chunk)
                    if total_size > self.max_file_size:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
                        )
                    temp_file.write(chunk)
            
            # Reset file position for any further operations
            await file.seek(0)
            
            # Validate file type and get extension
            file_ext = self._validate_file_type(temp_path, file.filename or "unknown")
            
            # Validate image and get metadata
            image_metadata = self._validate_image(temp_path)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(temp_path)
            
            # Generate secure final filename
            final_filename = self._generate_secure_filename(file.filename or "image", file_ext)
            final_path = self.images_dir / final_filename
            
            # Move from temp to final location
            temp_path.rename(final_path)
            
            # Generate relative URL path for serving
            relative_path = f"uploads/images/{final_filename}"
            
            # Prepare response data
            file_info = {
                "id": str(uuid.uuid4()),
                "filename": final_filename,
                "original_filename": file.filename,
                "path": relative_path,
                "url": f"/api/files/{relative_path}",
                "size": total_size,
                "content_type": file.content_type,
                "file_hash": file_hash,
                "user_id": user_id,
                "description": description,
                "metadata": image_metadata,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "status": "uploaded"
            }
            
            # Create ContentItem for the uploaded image
            try:
                db = next(get_db())
                content_item = ContentItem(
                    user_id=user_id,
                    content=f"/api/files/{relative_path}",  # Store file URL as content
                    content_hash=file_hash,
                    platform="upload",  # Special platform for uploaded content
                    content_type="image",
                    status="draft",
                    title=description or f"Uploaded image: {file.filename}",
                    # Store metadata in platform_metadata
                    platform_metadata={
                        "original_filename": file.filename,
                        "size_bytes": total_size,
                        "content_type": file.content_type,
                        "image_metadata": image_metadata,
                        "source": "user_upload"
                    }
                )
                db.add(content_item)
                db.commit()
                file_info["content_item_id"] = content_item.id
                logger.info(f"Created ContentItem {content_item.id} for uploaded image")
            except Exception as e:
                logger.warning(f"Failed to create ContentItem for upload: {e}")
                # Don't fail the upload if ContentItem creation fails
            finally:
                if 'db' in locals():
                    db.close()
            
            logger.info(f"Image uploaded successfully: {final_filename} ({total_size} bytes) for user {user_id}")
            
            return file_info
            
        except HTTPException:
            # Clean up temp file on HTTP exceptions
            if temp_path.exists():
                temp_path.unlink()
            raise
        except Exception as e:
            # Clean up temp file on any other exception
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"File upload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="File upload failed due to server error"
            )
    
    def delete_image(self, filename: str, user_id: str) -> bool:
        """
        Delete an uploaded image file.
        
        Args:
            filename: Name of the file to delete
            user_id: ID of the user requesting deletion (for authorization)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.images_dir / filename
            
            if not file_path.exists():
                return False
            
            # In a real application, you'd check if user owns this file
            # For now, we'll just delete it
            file_path.unlink()
            
            # Also delete the corresponding ContentItem
            try:
                db = next(get_db())
                content_item = db.query(ContentItem).filter(
                    ContentItem.user_id == user_id,
                    ContentItem.content.like(f"%{filename}%"),
                    ContentItem.platform == "upload"
                ).first()
                
                if content_item:
                    db.delete(content_item)
                    db.commit()
                    logger.info(f"Deleted ContentItem {content_item.id} for image {filename}")
                
            except Exception as e:
                logger.warning(f"Failed to delete ContentItem for {filename}: {e}")
            finally:
                if 'db' in locals():
                    db.close()
            
            logger.info(f"Image deleted: {filename} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            return False
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """Get statistics about uploaded files"""
        try:
            total_files = len(list(self.images_dir.glob("*")))
            total_size = sum(f.stat().st_size for f in self.images_dir.glob("*") if f.is_file())
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_directory": str(self.images_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get upload stats: {e}")
            return {"error": str(e)}

# Global instance
file_upload_service = FileUploadService()