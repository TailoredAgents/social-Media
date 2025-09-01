"""
Production Vector Search API - replaces all mock implementations
Uses pgvector for real semantic search capabilities
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from backend.db.database import get_db
from backend.auth.fastapi_users_config import current_active_user, UserTable
from backend.services.pgvector_service import PgVectorService

router = APIRouter(prefix="/api/vector-search", tags=["vector-search"])
logger = logging.getLogger(__name__)

# Pydantic models
class ContentEmbeddingRequest(BaseModel):
    content_id: int
    content_text: str
    metadata: Optional[Dict[str, Any]] = {}

class MemoryEmbeddingRequest(BaseModel):
    title: str
    content: str
    memory_type: str = "general"
    metadata: Optional[Dict[str, Any]] = {}

class SimilaritySearchRequest(BaseModel):
    query_text: str
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
    memory_type: Optional[str] = None

class VectorSearchResponse(BaseModel):
    id: int
    content_text: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    memory_type: Optional[str] = None
    similarity: float
    metadata: Dict[str, Any]
    created_at: str

@router.post("/content/store")
async def store_content_embedding(
    request: ContentEmbeddingRequest,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Store content embedding for semantic search"""
    try:
        vector_service = PgVectorService(db)
        
        embedding_id = vector_service.store_content_embedding(
            user_id=current_user.id,
            content_id=request.content_id,
            content_text=request.content_text,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "embedding_id": embedding_id,
            "message": "Content embedding stored successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to store content embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store content embedding"
        )

@router.post("/memory/store")
async def store_memory_embedding(
    request: MemoryEmbeddingRequest,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Store memory embedding for semantic search"""
    try:
        vector_service = PgVectorService(db)
        
        memory_id = vector_service.store_memory_embedding(
            user_id=current_user.id,
            title=request.title,
            content=request.content,
            memory_type=request.memory_type,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory embedding stored successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to store memory embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory embedding"
        )

@router.post("/content/search", response_model=List[VectorSearchResponse])
async def search_similar_content(
    request: SimilaritySearchRequest,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Search for similar content using semantic similarity"""
    try:
        vector_service = PgVectorService(db)
        
        results = vector_service.similarity_search_content(
            user_id=current_user.id,
            query_text=request.query_text,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert to response format
        search_results = []
        for result in results:
            search_results.append(VectorSearchResponse(
                id=result['id'],
                content_text=result['content_text'],
                similarity=result['similarity'],
                metadata=result['metadata'],
                created_at=result['created_at']
            ))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Failed to search similar content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search similar content"
        )

@router.post("/memory/search", response_model=List[VectorSearchResponse])
async def search_similar_memories(
    request: SimilaritySearchRequest,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Search for similar memories using semantic similarity"""
    try:
        vector_service = PgVectorService(db)
        
        results = vector_service.similarity_search_memories(
            user_id=current_user.id,
            query_text=request.query_text,
            memory_type=request.memory_type,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert to response format
        search_results = []
        for result in results:
            search_results.append(VectorSearchResponse(
                id=result['id'],
                title=result['title'],
                content=result['content'],
                memory_type=result['memory_type'],
                similarity=result['similarity'],
                metadata=result['metadata'],
                created_at=result['created_at']
            ))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Failed to search similar memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search similar memories"
        )

@router.delete("/content/{content_id}")
async def delete_content_embedding(
    content_id: int,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Delete content embedding"""
    try:
        vector_service = PgVectorService(db)
        
        deleted = vector_service.delete_content_embedding(
            user_id=current_user.id,
            content_id=content_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content embedding not found"
            )
        
        return {
            "success": True,
            "message": "Content embedding deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete content embedding"
        )

@router.delete("/memory/{memory_id}")
async def delete_memory_embedding(
    memory_id: int,
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Delete memory embedding"""
    try:
        vector_service = PgVectorService(db)
        
        deleted = vector_service.delete_memory_embedding(
            user_id=current_user.id,
            memory_id=memory_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory embedding not found"
            )
        
        return {
            "success": True,
            "message": "Memory embedding deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory embedding"
        )

@router.get("/stats")
async def get_embedding_stats(
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get embedding statistics for the current user"""
    try:
        vector_service = PgVectorService(db)
        
        stats = vector_service.get_embedding_stats(current_user.id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get embedding stats"
        )

@router.post("/setup")
async def setup_pgvector(
    current_user: UserTable = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Setup pgvector extension (admin endpoint)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can setup pgvector"
            )
        
        vector_service = PgVectorService(db)
        await vector_service.ensure_extension()
        
        return {
            "success": True,
            "message": "pgvector extension setup completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup pgvector: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup pgvector extension"
        )