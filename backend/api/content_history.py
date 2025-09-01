"""
Content History API Endpoints
Provides comprehensive content history retrieval and analytics functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from backend.db.database import get_db
from backend.db.models import ContentItem, ContentPerformanceSnapshot, ContentCategory, User
from backend.services.performance_tracking import performance_tracker
from backend.services.content_categorization import content_categorizer
from backend.services.embedding_service import embedding_service

# Get logger (use application's logging configuration)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content-history"])

# Pydantic models for request/response
class ContentHistoryFilter(BaseModel):
    """Filter parameters for content history queries"""
    platforms: Optional[List[str]] = Field(None, description="Filter by platforms")
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")
    performance_tiers: Optional[List[str]] = Field(None, description="Filter by performance tiers")
    categories: Optional[List[str]] = Field(None, description="Filter by topic categories")
    sentiments: Optional[List[str]] = Field(None, description="Filter by sentiment")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    min_engagement_rate: Optional[float] = Field(None, description="Minimum engagement rate")
    max_engagement_rate: Optional[float] = Field(None, description="Maximum engagement rate")
    search_text: Optional[str] = Field(None, description="Text search in content")

class ContentHistoryItem(BaseModel):
    """Content history item response model"""
    id: str
    content: str
    platform: str
    content_type: str
    status: str
    published_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    
    # Performance metrics
    likes_count: int = 0
    shares_count: int = 0
    comments_count: int = 0
    reach_count: int = 0
    engagement_rate: float = 0.0
    performance_tier: str = "unknown"
    viral_score: float = 0.0
    
    # Categorization
    topic_category: Optional[str]
    sentiment: Optional[str]
    tone: Optional[str]
    
    # Metadata
    hashtags: List[str] = []
    keywords: List[str] = []
    ai_generated: bool = False
    
    created_at: datetime
    updated_at: Optional[datetime]

class ContentHistoryResponse(BaseModel):
    """Paginated content history response"""
    items: List[ContentHistoryItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class ContentAnalytics(BaseModel):
    """Content analytics summary"""
    total_content: int
    platforms_summary: Dict[str, int]
    performance_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    avg_engagement_rate: float
    total_engagement: Dict[str, int]
    top_performing_content: List[ContentHistoryItem]
    recent_trends: Dict[str, Any]

class SimilarContentResponse(BaseModel):
    """Similar content search response"""
    query_content: str
    similar_items: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float

@router.get("/history", response_model=ContentHistoryResponse)
async def get_content_history(
    user_id: int = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms"),
    content_types: Optional[str] = Query(None, description="Comma-separated content types"),
    performance_tiers: Optional[str] = Query(None, description="Comma-separated performance tiers"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    sentiments: Optional[str] = Query(None, description="Comma-separated sentiments"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    min_engagement: Optional[float] = Query(None, ge=0, le=1, description="Min engagement rate"),
    max_engagement: Optional[float] = Query(None, ge=0, le=1, description="Max engagement rate"),
    search_text: Optional[str] = Query(None, description="Search in content text"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated content history with filtering and search capabilities
    """
    try:
        # Build base query
        query = db.query(ContentItem).filter(ContentItem.user_id == user_id)
        
        # Apply filters
        if platforms:
            platform_list = [p.strip() for p in platforms.split(",")]
            query = query.filter(ContentItem.platform.in_(platform_list))
        
        if content_types:
            type_list = [t.strip() for t in content_types.split(",")]
            query = query.filter(ContentItem.content_type.in_(type_list))
        
        if performance_tiers:
            tier_list = [t.strip() for t in performance_tiers.split(",")]
            query = query.filter(ContentItem.performance_tier.in_(tier_list))
        
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
            query = query.filter(ContentItem.topic_category.in_(category_list))
        
        if sentiments:
            sentiment_list = [s.strip() for s in sentiments.split(",")]
            query = query.filter(ContentItem.sentiment.in_(sentiment_list))
        
        if date_from:
            query = query.filter(ContentItem.created_at >= date_from)
        
        if date_to:
            query = query.filter(ContentItem.created_at <= date_to)
        
        if min_engagement is not None:
            query = query.filter(ContentItem.engagement_rate >= min_engagement)
        
        if max_engagement is not None:
            query = query.filter(ContentItem.engagement_rate <= max_engagement)
        
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.filter(ContentItem.content.ilike(search_pattern))
        
        # Apply sorting
        if sort_order.lower() == "desc":
            if sort_by == "engagement_rate":
                query = query.order_by(desc(ContentItem.engagement_rate))
            elif sort_by == "likes_count":
                query = query.order_by(desc(ContentItem.likes_count))
            elif sort_by == "published_at":
                query = query.order_by(desc(ContentItem.published_at))
            else:
                query = query.order_by(desc(ContentItem.created_at))
        else:
            if sort_by == "engagement_rate":
                query = query.order_by(ContentItem.engagement_rate)
            elif sort_by == "likes_count":
                query = query.order_by(ContentItem.likes_count)
            elif sort_by == "published_at":
                query = query.order_by(ContentItem.published_at)
            else:
                query = query.order_by(ContentItem.created_at)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # Convert to response models
        content_items = []
        for item in items:
            content_items.append(ContentHistoryItem(
                id=item.id,
                content=item.content,
                platform=item.platform,
                content_type=item.content_type,
                status=item.status,
                published_at=item.published_at,
                scheduled_for=item.scheduled_for,
                likes_count=item.likes_count or 0,
                shares_count=item.shares_count or 0,
                comments_count=item.comments_count or 0,
                reach_count=item.reach_count or 0,
                engagement_rate=item.engagement_rate or 0.0,
                performance_tier=item.performance_tier or "unknown",
                viral_score=item.viral_score or 0.0,
                topic_category=item.topic_category,
                sentiment=item.sentiment,
                tone=item.tone,
                hashtags=item.hashtags or [],
                keywords=item.keywords or [],
                ai_generated=item.ai_generated or False,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return ContentHistoryResponse(
            items=content_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error retrieving content history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve content history: {str(e)}")

@router.get("/{content_id}/analytics")
async def get_content_analytics(
    content_id: str = Path(..., description="Content ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for a specific content item
    """
    try:
        # Get content item
        content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Get performance trends
        trends = performance_tracker.get_performance_trends(db, content_id, days=30)
        
        # Get similar content for comparison
        similar_content = []
        if content_item.embedding_id:
            similar_results = embedding_service.search_similar_content(
                content_item.content, k=5, threshold=0.7
            )
            for result in similar_results:
                if result['content_id'] != content_id:  # Exclude self
                    similar_content.append({
                        "content_id": result['content_id'],
                        "similarity_score": result['similarity_score'],
                        "content": result.get('content', '')[:100] + '...',
                        "engagement_rate": result.get('engagement_rate', 0)
                    })
        
        # Get performance snapshots
        snapshots = db.query(ContentPerformanceSnapshot).filter(
            ContentPerformanceSnapshot.content_item_id == content_id
        ).order_by(desc(ContentPerformanceSnapshot.snapshot_time)).limit(10).all()
        
        snapshot_data = []
        for snapshot in snapshots:
            snapshot_data.append({
                "timestamp": snapshot.snapshot_time,
                "likes_count": snapshot.likes_count,
                "shares_count": snapshot.shares_count,
                "comments_count": snapshot.comments_count,
                "engagement_rate": snapshot.engagement_rate,
                "engagement_velocity": snapshot.engagement_velocity
            })
        
        return {
            "content_id": content_id,
            "content_item": ContentHistoryItem.from_orm(content_item),
            "performance_trends": trends,
            "similar_content": similar_content,
            "performance_snapshots": snapshot_data,
            "recommendations": performance_tracker._generate_recommendations(
                content_item,
                performance_tracker.PerformanceMetrics(
                    likes_count=content_item.likes_count or 0,
                    shares_count=content_item.shares_count or 0,
                    comments_count=content_item.comments_count or 0,
                    reach_count=content_item.reach_count or 0,
                    engagement_rate=content_item.engagement_rate or 0.0,
                    performance_tier=content_item.performance_tier or "unknown"
                ),
                performance_tracker.PerformanceMetrics(),  # Empty old metrics for comparison
                {"likes_growth": 0, "shares_growth": 0, "comments_growth": 0, "reach_growth": 0}
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/summary", response_model=ContentAnalytics)
async def get_content_analytics_summary(
    user_id: int = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive content analytics summary for a user
    """
    try:
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's content in the date range
        content_query = db.query(ContentItem).filter(
            and_(
                ContentItem.user_id == user_id,
                ContentItem.created_at >= start_date,
                ContentItem.created_at <= end_date
            )
        )
        
        content_items = content_query.all()
        total_content = len(content_items)
        
        if total_content == 0:
            return ContentAnalytics(
                total_content=0,
                platforms_summary={},
                performance_distribution={},
                category_distribution={},
                sentiment_distribution={},
                avg_engagement_rate=0.0,
                total_engagement={},
                top_performing_content=[],
                recent_trends={}
            )
        
        # Platform summary
        platforms_summary = {}
        performance_distribution = {}
        category_distribution = {}
        sentiment_distribution = {}
        
        total_likes = 0
        total_shares = 0
        total_comments = 0
        total_reach = 0
        engagement_rates = []
        
        for item in content_items:
            # Platform counts
            platforms_summary[item.platform] = platforms_summary.get(item.platform, 0) + 1
            
            # Performance tier distribution
            tier = item.performance_tier or "unknown"
            performance_distribution[tier] = performance_distribution.get(tier, 0) + 1
            
            # Category distribution
            category = item.topic_category or "general"
            category_distribution[category] = category_distribution.get(category, 0) + 1
            
            # Sentiment distribution
            sentiment = item.sentiment or "neutral"
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
            
            # Aggregate metrics
            total_likes += item.likes_count or 0
            total_shares += item.shares_count or 0
            total_comments += item.comments_count or 0
            total_reach += item.reach_count or 0
            
            if item.engagement_rate:
                engagement_rates.append(item.engagement_rate)
        
        # Calculate average engagement rate
        avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
        
        # Get top performing content
        top_content = sorted(
            content_items,
            key=lambda x: x.engagement_rate or 0,
            reverse=True
        )[:5]
        
        top_performing_items = []
        for item in top_content:
            top_performing_items.append(ContentHistoryItem(
                id=item.id,
                content=item.content[:200] + "..." if len(item.content) > 200 else item.content,
                platform=item.platform,
                content_type=item.content_type,
                status=item.status,
                published_at=item.published_at,
                scheduled_for=item.scheduled_for,
                likes_count=item.likes_count or 0,
                shares_count=item.shares_count or 0,
                comments_count=item.comments_count or 0,
                reach_count=item.reach_count or 0,
                engagement_rate=item.engagement_rate or 0.0,
                performance_tier=item.performance_tier or "unknown",
                viral_score=item.viral_score or 0.0,
                topic_category=item.topic_category,
                sentiment=item.sentiment,
                tone=item.tone,
                hashtags=item.hashtags or [],
                keywords=item.keywords or [],
                ai_generated=item.ai_generated or False,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))
        
        # Analyze recent trends (last 7 days vs previous 7 days)
        mid_date = end_date - timedelta(days=7)
        
        recent_items = [item for item in content_items if item.created_at >= mid_date]
        previous_items = [item for item in content_items if item.created_at < mid_date]
        
        recent_engagement = sum(item.engagement_rate or 0 for item in recent_items) / max(len(recent_items), 1)
        previous_engagement = sum(item.engagement_rate or 0 for item in previous_items) / max(len(previous_items), 1)
        
        engagement_trend = "up" if recent_engagement > previous_engagement else "down" if recent_engagement < previous_engagement else "stable"
        
        recent_trends = {
            "engagement_trend": engagement_trend,
            "recent_avg_engagement": recent_engagement,
            "previous_avg_engagement": previous_engagement,
            "trend_percentage": ((recent_engagement - previous_engagement) / max(previous_engagement, 0.01)) * 100,
            "total_recent_content": len(recent_items),
            "total_previous_content": len(previous_items)
        }
        
        return ContentAnalytics(
            total_content=total_content,
            platforms_summary=platforms_summary,
            performance_distribution=performance_distribution,
            category_distribution=category_distribution,
            sentiment_distribution=sentiment_distribution,
            avg_engagement_rate=avg_engagement_rate,
            total_engagement={
                "likes": total_likes,
                "shares": total_shares,
                "comments": total_comments,
                "reach": total_reach
            },
            top_performing_content=top_performing_items,
            recent_trends=recent_trends
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

@router.post("/search/similar", response_model=SimilarContentResponse)
async def search_similar_content(
    query: str = Query(..., description="Content to find similar items for"),
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms to search"),
    db: Session = Depends(get_db)
):
    """
    Find similar content using semantic search
    """
    try:
        import time
        start_time = time.time()
        
        # Use embedding service to find similar content
        similar_results = embedding_service.search_similar_content(
            query=query,
            k=limit * 2,  # Get more results to filter by user and platform
            threshold=threshold
        )
        
        # Filter results by user and platform
        filtered_results = []
        for result in similar_results:
            # Get full content item from database
            content_item = db.query(ContentItem).filter(
                ContentItem.id == result['content_id']
            ).first()
            
            if content_item and content_item.user_id == user_id:
                # Check platform filter if provided
                if platforms:
                    platform_list = [p.strip() for p in platforms.split(",")]
                    if content_item.platform not in platform_list:
                        continue
                
                filtered_results.append({
                    "content_id": result['content_id'],
                    "content": content_item.content,
                    "platform": content_item.platform,
                    "content_type": content_item.content_type,
                    "similarity_score": result['similarity_score'],
                    "engagement_rate": content_item.engagement_rate or 0.0,
                    "performance_tier": content_item.performance_tier or "unknown",
                    "published_at": content_item.published_at,
                    "topic_category": content_item.topic_category,
                    "sentiment": content_item.sentiment
                })
                
                if len(filtered_results) >= limit:
                    break
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SimilarContentResponse(
            query_content=query,
            similar_items=filtered_results,
            total_found=len(filtered_results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error searching similar content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search similar content: {str(e)}")

@router.get("/export")
async def export_content_history(
    user_id: int = Query(..., description="User ID"),
    format: str = Query("json", description="Export format (json, csv)"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms"),
    db: Session = Depends(get_db)
):
    """
    Export content history in various formats
    """
    try:
        from fastapi.responses import StreamingResponse
        import json
        import csv
        from io import StringIO
        
        # Build query with filters
        query = db.query(ContentItem).filter(ContentItem.user_id == user_id)
        
        if date_from:
            query = query.filter(ContentItem.created_at >= date_from)
        if date_to:
            query = query.filter(ContentItem.created_at <= date_to)
        if platforms:
            platform_list = [p.strip() for p in platforms.split(",")]
            query = query.filter(ContentItem.platform.in_(platform_list))
        
        content_items = query.order_by(desc(ContentItem.created_at)).all()
        
        if format.lower() == "csv":
            # Create CSV export
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "ID", "Content", "Platform", "Content Type", "Status",
                "Published At", "Likes", "Shares", "Comments", "Reach",
                "Engagement Rate", "Performance Tier", "Topic Category",
                "Sentiment", "AI Generated", "Created At"
            ])
            
            # Write data
            for item in content_items:
                writer.writerow([
                    item.id,
                    item.content.replace('\n', ' ').replace('\r', ''),  # Clean content
                    item.platform,
                    item.content_type,
                    item.status,
                    item.published_at.isoformat() if item.published_at else "",
                    item.likes_count or 0,
                    item.shares_count or 0,
                    item.comments_count or 0,
                    item.reach_count or 0,
                    item.engagement_rate or 0.0,
                    item.performance_tier or "unknown",
                    item.topic_category or "",
                    item.sentiment or "",
                    item.ai_generated or False,
                    item.created_at.isoformat()
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=content_history_{user_id}.csv"}
            )
        
        else:  # JSON format
            export_data = []
            for item in content_items:
                export_data.append({
                    "id": item.id,
                    "content": item.content,
                    "platform": item.platform,
                    "content_type": item.content_type,
                    "status": item.status,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                    "performance_metrics": {
                        "likes_count": item.likes_count or 0,
                        "shares_count": item.shares_count or 0,
                        "comments_count": item.comments_count or 0,
                        "reach_count": item.reach_count or 0,
                        "engagement_rate": item.engagement_rate or 0.0,
                        "performance_tier": item.performance_tier or "unknown",
                        "viral_score": item.viral_score or 0.0
                    },
                    "categorization": {
                        "topic_category": item.topic_category,
                        "sentiment": item.sentiment,
                        "tone": item.tone
                    },
                    "metadata": {
                        "hashtags": item.hashtags or [],
                        "keywords": item.keywords or [],
                        "ai_generated": item.ai_generated or False
                    },
                    "timestamps": {
                        "created_at": item.created_at.isoformat(),
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                        "scheduled_for": item.scheduled_for.isoformat() if item.scheduled_for else None
                    }
                })
            
            json_string = json.dumps({
                "export_info": {
                    "user_id": user_id,
                    "export_date": datetime.utcnow().isoformat(),
                    "total_items": len(export_data),
                    "filters_applied": {
                        "date_from": date_from.isoformat() if date_from else None,
                        "date_to": date_to.isoformat() if date_to else None,
                        "platforms": platforms.split(",") if platforms else None
                    }
                },
                "content_history": export_data
            }, indent=2)
            
            return StreamingResponse(
                iter([json_string]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=content_history_{user_id}.json"}
            )
        
    except Exception as e:
        logger.error(f"Error exporting content history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export content history: {str(e)}")

@router.delete("/{content_id}")
async def delete_content_item(
    content_id: str = Path(..., description="Content ID"),
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Delete a content item and its associated data
    """
    try:
        # Get content item and verify ownership
        content_item = db.query(ContentItem).filter(
            and_(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id
            )
        ).first()
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found or unauthorized")
        
        # Delete associated performance snapshots
        db.query(ContentPerformanceSnapshot).filter(
            ContentPerformanceSnapshot.content_item_id == content_id
        ).delete()
        
        # Remove from vector store if it has an embedding
        if content_item.embedding_id:
            # Note: FAISS doesn't support efficient deletion, but we mark as deleted in metadata
            from backend.core.vector_store import vector_store
            vector_store.remove_by_content_id(content_item.embedding_id)
        
        # Delete the content item
        db.delete(content_item)
        db.commit()
        
        logger.info(f"Deleted content item {content_id} for user {user_id}")
        
        return {"message": "Content item deleted successfully", "content_id": content_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content item: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete content item: {str(e)}")

# Additional utility endpoints

@router.get("/statistics/performance")
async def get_performance_statistics(
    user_id: int = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance statistics and trends
    """
    try:
        return performance_tracker.get_user_performance_summary(db, user_id, days)
    except Exception as e:
        logger.error(f"Error getting performance statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance statistics: {str(e)}")

@router.get("/categories")
async def get_content_categories(db: Session = Depends(get_db)):
    """
    Get available content categories
    """
    try:
        categories = db.query(ContentCategory).all()
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "color": cat.color,
                "keywords": cat.keywords or [],
                "total_content_count": cat.total_content_count or 0,
                "avg_engagement_rate": cat.avg_engagement_rate or 0.0
            }
            for cat in categories
        ]
    except Exception as e:
        logger.error(f"Error getting content categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content categories: {str(e)}")