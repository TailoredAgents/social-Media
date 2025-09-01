"""
Enhanced memory API endpoints with FAISS vector search integration
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from backend.core.error_handler import (
    handle_errors, ErrorCode, APIError, ValidationError, 
    NotFoundError, ExternalServiceError, safe_execute
)
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import Memory, User
from backend.auth.dependencies import get_current_active_user
from backend.services.memory_service import memory_service

router = APIRouter(prefix="/api/memory/vector", tags=["memory-vector"])

# Pydantic models
class VectorStoreRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    memory_type: str = Field(..., pattern="^(insight|research|template|trend|generated_content|optimization)$")
    platform: Optional[str] = Field(None, pattern="^(twitter|linkedin|instagram|facebook|tiktok|all)$")
    tags: Optional[List[str]] = Field(default_factory=list)
    engagement_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    threshold: float = Field(0.7, ge=0.0, le=1.0)
    memory_type: Optional[str] = None

class VectorMemoryResponse(BaseModel):
    id: int
    content_id: str
    content: str
    memory_type: str
    similarity_score: Optional[float] = None
    metadata: Dict[str, Any]
    created_at: datetime
    vector_indexed: bool

    model_config = ConfigDict(from_attributes=True)

class ContentPatternAnalysis(BaseModel):
    total_content: int
    content_types: Dict[str, int]
    platforms: Dict[str, int]
    avg_engagement: float
    engagement_distribution: Dict[str, float]

@router.post("/store", response_model=VectorMemoryResponse)
@handle_errors("store_vector_memory")
async def store_vector_memory(
    request: VectorStoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Store content with vector embeddings for semantic search"""
    
    # Prepare metadata
    metadata = {
        "platform": request.platform,
        "tags": request.tags,
        "engagement_rate": request.engagement_rate,
        **request.metadata
    }
    
    # Store in FAISS and database using safe execution
    result = await safe_execute(
        "memory storage",
        memory_service.store_memory,
        db=db,
        content=request.content,
        memory_type=request.memory_type,
        metadata=metadata,
        user_id=current_user.id,
        error_code=ErrorCode.MEMORY_STORAGE_ERROR
    )
    
    # Get the stored memory from database
    memory = db.query(Memory).filter(
        Memory.content_id == result['content_id']
    ).first()
    
    if not memory:
        raise NotFoundError(
            ErrorCode.MEMORY_STORAGE_ERROR,
            "Failed to retrieve stored memory from database"
        ).to_http_exception()
    
    return VectorMemoryResponse(
        id=memory.id,
        content_id=memory.content_id,
        content=memory.content,
        memory_type=memory.memory_type,
        metadata=memory.metadata,
        created_at=memory.created_at,
        vector_indexed=memory.vector_indexed
    )

@router.post("/search", response_model=List[VectorMemoryResponse])
async def search_similar_memories(
    request: VectorSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for similar content using vector similarity"""
    
    try:
        # Search using FAISS
        results = await memory_service.search_similar_content(
            query=request.query,
            user_id=current_user.id,
            top_k=request.top_k,
            threshold=request.threshold,
            memory_type=request.memory_type
        )
        
        # Format results
        response = []
        for result in results:
            # Get full memory record from database
            memory = db.query(Memory).filter(
                Memory.content_id == result['content_id']
            ).first()
            
            if memory:
                response.append(VectorMemoryResponse(
                    id=memory.id,
                    content_id=memory.content_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    similarity_score=result['similarity_score'],
                    metadata=memory.metadata,
                    created_at=memory.created_at,
                    vector_indexed=memory.vector_indexed
                ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/high-performing", response_model=List[VectorMemoryResponse])
async def get_high_performing_content(
    min_engagement: float = Query(5.0, ge=0.0, le=100.0),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get high-performing content for learning and optimization"""
    
    try:
        results = await memory_service.get_high_performing_content(
            user_id=current_user.id,
            min_engagement=min_engagement,
            limit=limit
        )
        
        response = []
        for result in results:
            memory = db.query(Memory).filter(
                Memory.content_id == result['content_id']
            ).first()
            
            if memory:
                response.append(VectorMemoryResponse(
                    id=memory.id,
                    content_id=memory.content_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    metadata=memory.metadata,
                    created_at=memory.created_at,
                    vector_indexed=memory.vector_indexed
                ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get high-performing content: {str(e)}"
        )

@router.get("/repurposing-candidates", response_model=List[VectorMemoryResponse])
async def get_repurposing_candidates(
    days_old: int = Query(30, ge=7, le=365),
    min_engagement: float = Query(3.0, ge=0.0, le=100.0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Find old high-performing content suitable for repurposing"""
    
    try:
        results = await memory_service.find_content_for_repurposing(
            user_id=current_user.id,
            days_old=days_old,
            min_engagement=min_engagement
        )
        
        response = []
        for result in results:
            memory = db.query(Memory).filter(
                Memory.content_id == result['content_id']
            ).first()
            
            if memory:
                response.append(VectorMemoryResponse(
                    id=memory.id,
                    content_id=memory.content_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    metadata={
                        **memory.metadata,
                        'age_days': result['age_days'],
                        'original_engagement': result['engagement_rate']
                    },
                    created_at=memory.created_at,
                    vector_indexed=memory.vector_indexed
                ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find repurposing candidates: {str(e)}"
        )

@router.get("/patterns", response_model=ContentPatternAnalysis)
async def analyze_content_patterns(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze patterns in user's stored content"""
    
    try:
        patterns = await memory_service.analyze_user_content_patterns(
            user_id=current_user.id
        )
        
        return ContentPatternAnalysis(**patterns)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze patterns: {str(e)}"
        )

@router.get("/stats")
async def get_vector_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get FAISS vector index statistics"""
    
    try:
        stats = await memory_service.get_memory_stats(user_id=current_user.id)
        
        # Add database stats
        total_memories = db.query(Memory).filter(
            Memory.user_id == current_user.id
        ).count()
        
        indexed_memories = db.query(Memory).filter(
            Memory.user_id == current_user.id,
            Memory.vector_indexed == True
        ).count()
        
        return {
            **stats,
            "total_memories": total_memories,
            "indexed_memories": indexed_memories,
            "unindexed_memories": total_memories - indexed_memories
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

@router.post("/sync")
async def sync_database_to_faiss(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync unindexed database memories to FAISS"""
    
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only admins can sync the vector index"
        )
    
    try:
        result = await memory_service.sync_database_to_faiss(db)
        
        return {
            "status": "success",
            "indexed": result['indexed'],
            "failed": result['failed'],
            "total_vectors": result['total_memories']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )

@router.get("/by-type/{memory_type}", response_model=List[VectorMemoryResponse])
async def get_memories_by_type(
    memory_type: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get memories by type"""
    
    try:
        results = await memory_service.get_content_by_type(
            user_id=current_user.id,
            content_type=memory_type,
            limit=limit
        )
        
        response = []
        for result in results:
            memory = db.query(Memory).filter(
                Memory.content_id == result['content_id']
            ).first()
            
            if memory:
                response.append(VectorMemoryResponse(
                    id=memory.id,
                    content_id=memory.content_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    metadata=memory.metadata,
                    created_at=memory.created_at,
                    vector_indexed=memory.vector_indexed
                ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memories by type: {str(e)}"
        )