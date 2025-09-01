from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.simple_memory import memory_system

router = APIRouter(prefix="/api/memory", tags=["memory"])

class ContentRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.7

@router.get("/")
async def get_all_memory(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get all stored memory content with pagination"""
    try:
        # Get all memory entries (simplified pagination for now)
        all_entries = list(memory_system.content_store.values())
        
        # Calculate pagination
        total = len(all_entries)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Get paginated results
        paginated_entries = all_entries[start_idx:end_idx]
        
        return {
            "status": "success",
            "content": paginated_entries,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory content: {str(e)}")

@router.post("/store")
async def store_content(request: ContentRequest):
    """Store content in memory system"""
    try:
        content_id = memory_system.store_content(request.content, request.metadata)
        
        if content_id:
            return {
                "status": "success",
                "content_id": content_id,
                "message": "Content stored successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to store content")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing content: {str(e)}")

@router.post("/search")
async def search_content(request: SearchRequest):
    """Search for similar content"""
    try:
        results = memory_system.search_similar(
            request.query, 
            request.top_k, 
            request.threshold
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching content: {str(e)}")

@router.get("/content/{content_type}")
async def get_content_by_type(
    content_type: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """Get content by type"""
    try:
        results = memory_system.get_content_by_type(content_type, limit)
        
        return {
            "status": "success",
            "content_type": content_type,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving content: {str(e)}")

@router.get("/high-performing")
async def get_high_performing_content(
    min_engagement: float = Query(default=5.0, ge=0.0),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get high-performing content for learning"""
    try:
        results = memory_system.get_high_performing_content(min_engagement, limit)
        
        return {
            "status": "success",
            "min_engagement": min_engagement,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving high-performing content: {str(e)}")

@router.get("/repurpose")
async def get_repurpose_candidates(
    days_old: int = Query(default=30, ge=1, le=365),
    min_engagement: float = Query(default=3.0, ge=0.0)
):
    """Get content suitable for repurposing"""
    try:
        results = memory_system.get_content_for_repurposing(days_old, min_engagement)
        
        return {
            "status": "success",
            "criteria": {
                "days_old": days_old,
                "min_engagement": min_engagement
            },
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving repurpose candidates: {str(e)}")

@router.get("/analytics")
async def get_memory_analytics():
    """Get analytics on stored content patterns"""
    try:
        patterns = memory_system.analyze_content_patterns()
        
        return {
            "status": "success",
            "analytics": patterns
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content patterns: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_content(days_to_keep: int = Query(default=365, ge=30, le=1095)):
    """Clean up old content from memory"""
    try:
        removed_count = memory_system.cleanup_old_content(days_to_keep)
        
        return {
            "status": "success",
            "message": f"Cleaned up {removed_count} old content items",
            "removed_count": removed_count,
            "days_kept": days_to_keep
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up content: {str(e)}")

@router.get("/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    try:
        total_content = len(memory_system.metadata)
        index_size = memory_system.index.ntotal if memory_system.index else 0
        
        # Content type distribution
        content_types = {}
        for meta in memory_system.metadata.values():
            content_type = meta.get('metadata', {}).get('type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            "status": "success",
            "stats": {
                "total_content_items": total_content,
                "index_size": index_size,
                "content_types": content_types,
                "memory_system_version": "1.0",
                "last_updated": max(
                    [meta.get('created_at', '') for meta in memory_system.metadata.values()],
                    default='No content'
                )
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory stats: {str(e)}")