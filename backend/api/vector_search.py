from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.auth.dependencies import get_current_active_user
from backend.services.memory_service import memory_service
from backend.api.validation import validate_text_length, clean_text_input

router = APIRouter(
    prefix="/api/vector",
    tags=["vector-search"],
    dependencies=[Depends(get_current_active_user)]
)

class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    memory_type: Optional[str] = Field(None, description="Filter by memory type")
    limit: int = Field(10, ge=1, le=50, description="Number of results")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")

class ContentCreationSearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="Content topic")
    platform: str = Field(..., description="Target platform")

class MemoryStoreRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000, description="Content to store")
    memory_type: str = Field(..., description="Type of memory (content, research, template, trend)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

@router.post("/search")
async def vector_search(
    request: VectorSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform vector similarity search across stored memories
    """
    try:
        # Clean and validate input
        query = clean_text_input(request.query)
        validate_text_length(query, min_length=1, max_length=1000)
        
        # Perform search
        results = await memory_service.search_similar_memories(
            query=query,
            memory_type=request.memory_type,
            limit=request.limit,
            threshold=request.threshold,
            db=db
        )
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results,
            "search_params": {
                "memory_type": request.memory_type,
                "limit": request.limit,
                "threshold": request.threshold
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search/content-creation")
async def search_for_content_creation(
    request: ContentCreationSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Find relevant memories for content creation
    """
    try:
        # Clean inputs
        topic = clean_text_input(request.topic)
        platform = clean_text_input(request.platform).lower()
        
        # Validate platform
        valid_platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
            )
        
        # Search for relevant memories
        results = await memory_service.find_memories_for_content_creation(
            topic=topic,
            platform=platform,
            db=db
        )
        
        return {
            "status": "success",
            "topic": topic,
            "platform": platform,
            "results": results,
            "recommendations": {
                "use_templates": len(results.get('templates', [])) > 0,
                "leverage_insights": len(results.get('research_insights', [])) > 0,
                "study_high_performers": len(results.get('high_performing_examples', [])) > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content search failed: {str(e)}")

@router.post("/store")
async def store_memory_vector(
    request: MemoryStoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Store new memory with vector embedding
    """
    try:
        # Clean and validate inputs
        content = clean_text_input(request.content)
        validate_text_length(content, min_length=10, max_length=10000)
        
        # Validate memory type
        valid_types = ["content", "research", "template", "trend", "insight"]
        if request.memory_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid memory type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Prepare metadata
        metadata = request.metadata or {}
        metadata['tags'] = request.tags
        metadata['stored_via'] = 'vector_api'
        metadata['timestamp'] = datetime.utcnow().isoformat()
        
        # Store memory
        memory = await memory_service.store_memory(
            content=content,
            memory_type=request.memory_type,
            metadata=metadata,
            db=db
        )
        
        if not memory:
            raise HTTPException(status_code=500, detail="Failed to store memory")
        
        return {
            "status": "success",
            "memory_id": memory.id,
            "vector_id": memory.vector_id,
            "memory_type": memory.memory_type,
            "message": "Memory stored successfully with vector embedding"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

@router.get("/analytics")
async def get_vector_analytics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get analytics on vector memory system
    """
    try:
        analytics = await memory_service.analyze_content_performance(db)
        
        return {
            "status": "success",
            "analytics": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.post("/sync")
async def sync_vector_index(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync database memories with FAISS vector index
    """
    try:
        # Run sync operation
        sync_results = await memory_service.sync_database_with_faiss(db)
        
        # Schedule background cleanup if needed
        if sync_results.get('remaining', 0) > 0:
            background_tasks.add_task(
                memory_service.sync_database_with_faiss,
                db
            )
        
        return {
            "status": "success",
            "sync_results": sync_results,
            "message": "Vector index sync completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_vectors(
    days_to_keep: int = Query(365, ge=30, le=730, description="Days to keep memories"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clean up old memories from vector index
    """
    try:
        cleaned_count = await memory_service.cleanup_old_memories(
            days_to_keep=days_to_keep,
            db=db
        )
        
        return {
            "status": "success",
            "cleaned_count": cleaned_count,
            "days_kept": days_to_keep,
            "message": f"Cleaned up {cleaned_count} old memories"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/similar/{memory_id}")
async def find_similar_to_memory(
    memory_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of similar items"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Find memories similar to a specific memory ID
    """
    try:
        # Get the memory from database
        from backend.db.models import Memory
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Search for similar content
        similar = await memory_service.search_similar_memories(
            query=memory.content,
            memory_type=memory.memory_type,
            limit=limit + 1,  # Get one extra to exclude self
            db=db
        )
        
        # Filter out the original memory
        similar = [m for m in similar if m.get('id') != memory_id][:limit]
        
        return {
            "status": "success",
            "original_memory": {
                "id": memory.id,
                "content": memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                "type": memory.memory_type
            },
            "similar_memories": similar,
            "count": len(similar)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar search failed: {str(e)}")