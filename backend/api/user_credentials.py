"""
User Credentials API
Secure management of per-user social media platform credentials
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.db.database import get_db
from backend.db.user_credentials import UserCredentials, SocialMediaPlatformConfig
from backend.auth.dependencies import get_current_active_user, AuthUser

router = APIRouter(prefix="/api/credentials", tags=["user-credentials"])


# Pydantic Models
class CredentialCreate(BaseModel):
    platform: str
    credentials: Dict[str, str]
    platform_username: Optional[str] = None
    credential_type: str = "api_key"

class CredentialUpdate(BaseModel):
    credentials: Optional[Dict[str, str]] = None
    platform_username: Optional[str] = None
    is_active: Optional[bool] = None

class CredentialResponse(BaseModel):
    id: int
    platform: str
    platform_username: Optional[str]
    credential_type: str
    is_active: bool
    last_verified: Optional[datetime]
    verification_error: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]
    # Note: We never return the actual credentials for security

class PlatformConfigResponse(BaseModel):
    platform_name: str
    display_name: str
    requires_oauth: bool
    requires_app_credentials: bool
    required_fields: Dict[str, Any]
    optional_fields: Dict[str, Any]
    setup_instructions: Optional[str]
    help_url: Optional[str]


@router.get("/platforms", response_model=List[PlatformConfigResponse])
async def get_supported_platforms(db: Session = Depends(get_db)):
    """Get list of supported social media platforms and their configuration"""
    platforms = db.query(SocialMediaPlatformConfig).filter(
        SocialMediaPlatformConfig.is_active == True
    ).all()
    
    return platforms


@router.get("/", response_model=List[CredentialResponse])
async def get_user_credentials(
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all credentials for the current user"""
    credentials = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id
    ).all()
    
    return credentials


@router.post("/", response_model=CredentialResponse)
async def create_credential(
    credential: CredentialCreate,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add new social media platform credentials for the user"""
    
    # Check if platform is supported
    platform_config = db.query(SocialMediaPlatformConfig).filter(
        SocialMediaPlatformConfig.platform_name == credential.platform,
        SocialMediaPlatformConfig.is_active == True
    ).first()
    
    if not platform_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{credential.platform}' is not supported"
        )
    
    # Validate required fields
    required_fields = platform_config.required_fields
    missing_fields = []
    for field_name, field_config in required_fields.items():
        if field_name not in credential.credentials:
            missing_fields.append(field_name)
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    # Check if user already has credentials for this platform
    existing = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == credential.platform
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credentials for platform '{credential.platform}' already exist. Use PUT to update."
        )
    
    # Create new credential entry
    new_credential = UserCredentials(
        user_id=current_user.user_id,
        platform=credential.platform,
        platform_username=credential.platform_username,
        credential_type=credential.credential_type
    )
    
    # Set encrypted credentials
    new_credential.set_credentials(credential.credentials)
    
    db.add(new_credential)
    db.commit()
    db.refresh(new_credential)
    
    return new_credential


@router.get("/{platform}", response_model=CredentialResponse)
async def get_platform_credential(
    platform: str,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get credentials for a specific platform"""
    credential = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == platform
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for platform '{platform}'"
        )
    
    return credential


@router.put("/{platform}", response_model=CredentialResponse)
async def update_platform_credential(
    platform: str,
    credential_update: CredentialUpdate,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update credentials for a specific platform"""
    credential = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == platform
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for platform '{platform}'"
        )
    
    # Update fields
    if credential_update.credentials is not None:
        # Validate required fields if updating credentials
        platform_config = db.query(SocialMediaPlatformConfig).filter(
            SocialMediaPlatformConfig.platform_name == platform,
            SocialMediaPlatformConfig.is_active == True
        ).first()
        
        if platform_config:
            required_fields = platform_config.required_fields
            missing_fields = []
            for field_name in required_fields.keys():
                if field_name not in credential_update.credentials:
                    missing_fields.append(field_name)
            
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
        
        credential.set_credentials(credential_update.credentials)
        credential.verification_error = None  # Clear any previous errors
    
    if credential_update.platform_username is not None:
        credential.platform_username = credential_update.platform_username
    
    if credential_update.is_active is not None:
        credential.is_active = credential_update.is_active
    
    db.commit()
    db.refresh(credential)
    
    return credential


@router.delete("/{platform}")
async def delete_platform_credential(
    platform: str,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete credentials for a specific platform"""
    credential = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == platform
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for platform '{platform}'"
        )
    
    db.delete(credential)
    db.commit()
    
    return {"message": f"Credentials for platform '{platform}' deleted successfully"}


@router.post("/{platform}/verify")
async def verify_platform_credential(
    platform: str,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify that platform credentials are working"""
    credential = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == platform
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for platform '{platform}'"
        )
    
    # Verify credentials (this would call platform-specific verification)
    try:
        is_valid = credential.verify_credentials()
        
        if is_valid:
            credential.last_verified = datetime.utcnow()
            credential.verification_error = None
            credential.is_active = True
        else:
            credential.verification_error = "Credentials verification failed"
            credential.is_active = False
        
        db.commit()
        
        return {
            "platform": platform,
            "is_valid": is_valid,
            "verified_at": credential.last_verified,
            "error": credential.verification_error
        }
        
    except Exception as e:
        credential.verification_error = str(e)
        credential.is_active = False
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/{platform}/status")
async def get_credential_status(
    platform: str,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status and health of platform credentials"""
    credential = db.query(UserCredentials).filter(
        UserCredentials.user_id == current_user.user_id,
        UserCredentials.platform == platform
    ).first()
    
    if not credential:
        return {
            "platform": platform,
            "connected": False,
            "message": "No credentials configured"
        }
    
    return {
        "platform": platform,
        "connected": credential.is_active,
        "last_verified": credential.last_verified,
        "last_used": credential.last_used,
        "expires_at": credential.expires_at,
        "verification_error": credential.verification_error,
        "platform_username": credential.platform_username
    }