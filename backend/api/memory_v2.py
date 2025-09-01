"""
Memory system API endpoints with database integration
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

from backend.db.database import get_db
from backend.db.models import MemoryContent, User
from backend.auth.dependencies import get_current_active_user
from backend.core.vector_store import VectorStore
from backend.services.embedding_service import EmbeddingService
from backend.services.cache_decorators import cached, cache_invalidate

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Initialize FAISS services
vector_store = VectorStore()
embedding_service = EmbeddingService()

# Pydantic models
class StoreContentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field(..., pattern="^(research|post|insight|trend|note|template)$")
    source: Optional[str] = Field(None, max_length=200)
    platform: Optional[str] = Field(None, pattern="^(twitter|linkedin|instagram|facebook|tiktok|web|manual)$")
    tags: Optional[List[str]] = Field(default_factory=list)
    sentiment: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$")
    topic_category: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    content_types: Optional[List[str]] = Field(default_factory=list)
    platforms: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    min_relevance: float = Field(0.5, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=50)

class UpdateContentRequest(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    tags: Optional[List[str]] = None
    sentiment: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$")
    topic_category: Optional[str] = Field(None, max_length=100)
    engagement_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    performance_tier: Optional[str] = Field(None, pattern="^(high|medium|low|unknown)$")
    metadata: Optional[Dict[str, Any]] = None

class MemoryContentResponse(BaseModel):
    id: str
    content: str
    content_type: str
    source: Optional[str]
    platform: Optional[str]
    tags: List[str]
    sentiment: Optional[str]
    topic_category: Optional[str]
    relevance_score: float
    engagement_score: float
    performance_tier: str
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class SearchResult(BaseModel):
    content: MemoryContentResponse
    similarity_score: float
    match_reason: str

@cache_invalidate("memory", "search")  # Invalidate search cache when new content is added
@router.post("/store", response_model=MemoryContentResponse)
async def store_content(
    request: StoreContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Store content in memory system"""
    
    try:
        # Generate embedding for the content
        embedding = await embedding_service.generate_embedding(request.content)
        
        # Create memory content entry
        memory_content = MemoryContent(
            id=str(uuid.uuid4()),
            content=request.content,
            content_type=request.content_type,
            source=request.source,
            platform=request.platform,
            tags=request.tags or [],
            sentiment=request.sentiment,
            topic_category=request.topic_category,
            relevance_score=0.5,  # Default relevance
            engagement_score=0.0,
            performance_tier="unknown",
            metadata=request.metadata or {}
        )
        
        # Store content in database first to get the ID
        db.add(memory_content)
        db.commit()
        db.refresh(memory_content)
        
        # Prepare metadata for FAISS
        faiss_metadata = {
            "content_id": memory_content.id,
            "content_type": request.content_type,
            "source": request.source or "",
            "platform": request.platform or "",
            "tags": request.tags or [],
            "sentiment": request.sentiment or "",
            "topic_category": request.topic_category or "",
            "created_at": memory_content.created_at.isoformat(),
            "content": request.content[:500]  # Store truncated content for quick access
        }
        
        # Store embedding in FAISS vector store
        vector_id = vector_store.add_vector(embedding, faiss_metadata)
        
        # Update memory content with embedding ID
        memory_content.embedding_id = str(vector_id)
        db.commit()
        db.refresh(memory_content)
        
        return memory_content
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to store content in memory system: {str(e)}"
        )

@cached("memory", "search", ttl=600)  # 10 minute cache for search results
@router.post("/search", response_model=List[SearchResult])
async def search_content(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for similar content using FAISS semantic search"""
    
    try:
        # Generate embedding for the search query
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        # Perform FAISS similarity search
        search_results = vector_store.search(
            query_vector=query_embedding,
            k=request.limit * 2,  # Get more results to allow for filtering
            similarity_threshold=request.min_relevance
        )
        
        # Extract content IDs from FAISS results
        content_ids = []
        faiss_scores = {}
        
        for result in search_results:
            content_id = result['metadata'].get('content_id')
            if content_id:
                content_ids.append(content_id)
                faiss_scores[content_id] = result['similarity_score']
        
        if not content_ids:
            return []
        
        # Fetch corresponding database records
        query = db.query(MemoryContent).filter(MemoryContent.id.in_(content_ids))
        
        # Apply additional filters
        if request.content_types:
            query = query.filter(MemoryContent.content_type.in_(request.content_types))
        
        if request.platforms:
            query = query.filter(MemoryContent.platform.in_(request.platforms))
        
        content_items = query.all()
        
        # Filter by tags if specified
        if request.tags:
            content_items = [
                item for item in content_items 
                if any(tag in (item.tags or []) for tag in request.tags)
            ]
        
        # Create search results with FAISS similarity scores
        results = []
        for item in content_items:
            similarity_score = faiss_scores.get(item.id, 0.0)
            
            # Skip items below minimum relevance threshold
            if similarity_score < request.min_relevance:
                continue
            
            # Determine match reason based on FAISS metadata and filters
            match_reasons = ["semantic similarity"]
            
            # Check for exact matches to enhance match reason
            query_lower = request.query.lower()
            content_lower = item.content.lower()
            
            if query_lower in content_lower:
                match_reasons.append("exact phrase match")
            elif any(word in content_lower for word in query_lower.split()):
                match_reasons.append("keyword match")
            
            if request.tags and any(tag in (item.tags or []) for tag in request.tags):
                match_reasons.append("tag match")
            
            if (item.topic_category and 
                item.topic_category.lower() in query_lower):
                match_reasons.append("category match")
            
            match_reason = ", ".join(match_reasons)
            
            results.append(SearchResult(
                content=item,
                similarity_score=round(similarity_score, 3),
                match_reason=match_reason
            ))
        
        # Sort by FAISS similarity score (already sorted, but ensure order)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit final results
        return results[:request.limit]
        
    except Exception as e:
        # Fallback to simple text search if FAISS fails
        query = db.query(MemoryContent)
        
        # Apply filters
        if request.content_types:
            query = query.filter(MemoryContent.content_type.in_(request.content_types))
        
        if request.platforms:
            query = query.filter(MemoryContent.platform.in_(request.platforms))
        
        query = query.filter(MemoryContent.relevance_score >= request.min_relevance)
        
        # Fallback text search
        content_items = query.filter(
            MemoryContent.content.ilike(f"%{request.query}%")
        ).order_by(MemoryContent.created_at.desc()).limit(request.limit).all()
        
        # Apply tag filter
        if request.tags:
            content_items = [
                item for item in content_items 
                if any(tag in (item.tags or []) for tag in request.tags)
            ]
        
        # Create fallback results
        results = []
        for item in content_items:
            # Simple text overlap similarity as fallback
            query_words = set(request.query.lower().split())
            content_words = set(item.content.lower().split())
            similarity = (len(query_words.intersection(content_words)) / 
                         len(query_words.union(content_words))) if query_words.union(content_words) else 0.0
            
            results.append(SearchResult(
                content=item,
                similarity_score=round(similarity, 3),
                match_reason="text search (fallback)"
            ))
        
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results

@router.get("/", response_model=List[MemoryContentResponse])
async def get_memory_content(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    content_type: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    performance_tier: Optional[str] = Query(None, pattern="^(high|medium|low|unknown)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get stored memory content with filtering"""
    
    query = db.query(MemoryContent)
    
    if content_type:
        query = query.filter(MemoryContent.content_type == content_type)
    if platform:
        query = query.filter(MemoryContent.platform == platform)
    if performance_tier:
        query = query.filter(MemoryContent.performance_tier == performance_tier)
    
    content_items = query.order_by(MemoryContent.created_at.desc()).offset(offset).limit(limit).all()
    
    return content_items

@router.get("/{content_id}", response_model=MemoryContentResponse)
async def get_memory_item(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific memory content by ID"""
    
    content = db.query(MemoryContent).filter(MemoryContent.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Memory content not found")
    
    return content

@router.put("/{content_id}", response_model=MemoryContentResponse)
async def update_memory_content(
    content_id: str,
    request: UpdateContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update memory content"""
    
    content = db.query(MemoryContent).filter(MemoryContent.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Memory content not found")
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    content.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(content)
    
    return content

@router.delete("/{content_id}")
async def delete_memory_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete memory content"""
    
    content = db.query(MemoryContent).filter(MemoryContent.id == content_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Memory content not found")
    
    db.delete(content)
    db.commit()
    
    return {"message": "Memory content deleted successfully"}

@router.get("/analytics/summary")
async def get_memory_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get memory system analytics"""
    
    # Get all memory content
    all_content = db.query(MemoryContent).all()
    
    # Calculate statistics
    total_items = len(all_content)
    
    content_by_type = {}
    content_by_platform = {}
    content_by_performance = {}
    
    for content in all_content:
        # Type stats
        content_type = content.content_type
        content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        # Platform stats
        if content.platform:
            platform = content.platform
            content_by_platform[platform] = content_by_platform.get(platform, 0) + 1
        
        # Performance stats
        performance = content.performance_tier
        content_by_performance[performance] = content_by_performance.get(performance, 0) + 1
    
    # Get high-performing content
    high_performing = db.query(MemoryContent).filter(
        MemoryContent.performance_tier == "high"
    ).order_by(MemoryContent.engagement_score.desc()).limit(5).all()
    
    # Get recent additions
    recent_content = db.query(MemoryContent).order_by(
        MemoryContent.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_items": total_items,
        "content_by_type": content_by_type,
        "content_by_platform": content_by_platform,
        "content_by_performance": content_by_performance,
        "high_performing_content": [
            {
                "id": content.id,
                "content": content.content[:100] + "..." if len(content.content) > 100 else content.content,
                "content_type": content.content_type,
                "engagement_score": content.engagement_score,
                "created_at": content.created_at
            }
            for content in high_performing
        ],
        "recent_additions": [
            {
                "id": content.id,
                "content": content.content[:100] + "..." if len(content.content) > 100 else content.content,
                "content_type": content.content_type,
                "created_at": content.created_at
            }
            for content in recent_content
        ]
    }

@router.get("/tags/popular")
async def get_popular_tags(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=50)
):
    """Get most popular tags"""
    
    # Get all memory content with tags
    content_with_tags = db.query(MemoryContent).filter(
        MemoryContent.tags.isnot(None)
    ).all()
    
    # Count tag frequency
    tag_counts = {}
    for content in content_with_tags:
        for tag in content.tags or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by frequency
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [
        {"tag": tag, "count": count}
        for tag, count in popular_tags
    ]


@router.post("/recommendations", response_model=List[SearchResult])
async def get_content_recommendations(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(5, ge=1, le=20)
):
    """Get FAISS-based content recommendations for a given content item"""
    
    # Get the source content
    source_content = db.query(MemoryContent).filter(
        MemoryContent.id == content_id
    ).first()
    
    if not source_content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    try:
        # Generate embedding for the source content
        source_embedding = await embedding_service.generate_embedding(source_content.content)
        
        # Find similar content using FAISS
        search_results = vector_store.search(
            query_vector=source_embedding,
            k=limit + 1,  # +1 to exclude the source content
            similarity_threshold=0.3  # Lower threshold for recommendations
        )
        
        # Filter out the source content and prepare recommendations
        recommendations = []
        for result in search_results:
            result_content_id = result['metadata'].get('content_id')
            
            # Skip the source content itself
            if result_content_id == content_id:
                continue
            
            # Get content from database
            content = db.query(MemoryContent).filter(
                MemoryContent.id == result_content_id
            ).first()
            
            if content:
                recommendations.append(SearchResult(
                    content=content,
                    similarity_score=round(result['similarity_score'], 3),
                    match_reason="semantic similarity recommendation"
                ))
        
        return recommendations[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/bulk-store")
async def bulk_store_content(
    contents: List[StoreContentRequest],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk store multiple content items with FAISS embeddings"""
    
    if len(contents) > 100:
        raise HTTPException(
            status_code=400, 
            detail="Cannot store more than 100 items at once"
        )
    
    try:
        stored_items = []
        embeddings_to_store = []
        
        # Generate embeddings for all content in batch
        content_texts = [content.content for content in contents]
        embeddings = await embedding_service.generate_embeddings_batch(content_texts)
        
        # Create database entries
        for i, request in enumerate(contents):
            memory_content = MemoryContent(
                id=str(uuid.uuid4()),
                content=request.content,
                content_type=request.content_type,
                source=request.source,
                platform=request.platform,
                tags=request.tags or [],
                sentiment=request.sentiment,
                topic_category=request.topic_category,
                relevance_score=0.5,
                engagement_score=0.0,
                performance_tier="unknown",
                metadata=request.metadata or {}
            )
            
            db.add(memory_content)
            stored_items.append(memory_content)
            
            # Prepare FAISS metadata
            faiss_metadata = {
                "content_id": memory_content.id,
                "content_type": request.content_type,
                "source": request.source or "",
                "platform": request.platform or "",
                "tags": request.tags or [],
                "sentiment": request.sentiment or "",
                "topic_category": request.topic_category or "",
                "content": request.content[:500]
            }
            
            embeddings_to_store.append({
                "embedding": embeddings[i],
                "metadata": faiss_metadata,
                "content_id": memory_content.id
            })
        
        # Commit database changes
        db.commit()
        
        # Update created_at timestamps in metadata
        for i, item in enumerate(stored_items):
            db.refresh(item)
            embeddings_to_store[i]["metadata"]["created_at"] = item.created_at.isoformat()
        
        # Batch store in FAISS
        embedding_vectors = [item["embedding"] for item in embeddings_to_store]
        embedding_metadata = [item["metadata"] for item in embeddings_to_store]
        
        vector_ids = vector_store.add_vectors_batch(embedding_vectors, embedding_metadata)
        
        # Update database with FAISS vector IDs
        for i, item in enumerate(stored_items):
            item.embedding_id = str(vector_ids[i])
        
        db.commit()
        
        return {
            "message": f"Successfully stored {len(stored_items)} items",
            "stored_count": len(stored_items),
            "items": [
                {
                    "id": item.id,
                    "content_type": item.content_type,
                    "embedding_id": item.embedding_id
                }
                for item in stored_items
            ]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to bulk store content: {str(e)}"
        )


@router.get("/vector-stats")
async def get_vector_store_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get FAISS vector store statistics and health metrics"""
    
    try:
        stats = vector_store.get_statistics()
        
        return {
            "faiss_statistics": stats,
            "status": "healthy" if stats.get("total_vectors", 0) > 0 else "empty",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "faiss_statistics": {"error": str(e)},
            "status": "error",
            "last_updated": datetime.utcnow().isoformat()
        }