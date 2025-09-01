"""
Similarity Search API Endpoints
Integration Specialist Component - Advanced content similarity and recommendation APIs
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from backend.db.database import get_db
from backend.auth.dependencies import get_current_active_user
from backend.services.similarity_service import similarity_service, SimilarityResult, ContentRecommendation
from backend.api.validation import validate_text_length, clean_text_input
from backend.db.models import User, ContentItem, Memory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/similarity",
    tags=["similarity-search"],
    dependencies=[Depends(get_current_active_user)]
)

# Request models
class SimilaritySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Search query text")
    content_type: Optional[str] = Field(None, description="Filter by content type (content, research, template, trend)")
    platform: Optional[str] = Field(None, description="Filter by platform (twitter, linkedin, instagram, facebook, tiktok)")
    limit: int = Field(10, ge=1, le=50, description="Number of results to return")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_performance: bool = Field(True, description="Include performance data and metrics")

class ContentRecommendationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="Content topic or theme")
    target_platform: str = Field(..., description="Target social media platform")
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences and settings")
    recommendation_types: List[str] = Field(
        default=["repurpose", "template", "inspiration", "trend"],
        description="Types of recommendations to include"
    )

class RepurposingRequest(BaseModel):
    content_id: str = Field(..., description="ID of content to repurpose")
    target_platforms: List[str] = Field(..., description="Target platforms for repurposing")
    maintain_performance: bool = Field(True, description="Prioritize high-performing elements")

class ContentAnalysisRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000, description="Content to analyze")
    platform: Optional[str] = Field(None, description="Target platform for analysis")

# Response models
class SimilaritySearchResponse(BaseModel):
    status: str
    query: str
    results_count: int
    results: List[Dict[str, Any]]
    search_metadata: Dict[str, Any]

class ContentRecommendationResponse(BaseModel):
    status: str
    topic: str
    target_platform: str
    recommendations_count: int
    recommendations: List[Dict[str, Any]]
    generation_metadata: Dict[str, Any]

@router.post("/search", response_model=SimilaritySearchResponse)
async def advanced_similarity_search(
    request: SimilaritySearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> SimilaritySearchResponse:
    """
    Advanced similarity search with performance analysis and enhanced metadata
    """
    try:
        # Clean and validate input
        query = clean_text_input(request.query)
        validate_text_length(query, min_length=1, max_length=2000)
        
        # Validate platform if provided
        if request.platform:
            valid_platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok"]
            if request.platform not in valid_platforms:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
                )
        
        # Perform enhanced similarity search
        results = await similarity_service.find_similar_content(
            query=query,
            content_type=request.content_type,
            platform=request.platform,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            include_performance_data=request.include_performance,
            db=db
        )
        
        # Convert results to response format
        formatted_results = []
        for result in results:
            formatted_result = {
                "content_id": result.content_id,
                "content": result.content,
                "similarity_score": result.similarity_score,
                "content_type": result.content_type,
                "platform": result.platform,
                "performance_tier": result.performance_tier,
                "repurposing_potential": result.repurposing_potential,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "tags": result.tags,
                "engagement_metrics": result.engagement_metrics,
                "related_content_ids": result.related_content_ids
            }
            formatted_results.append(formatted_result)
        
        # Generate search metadata
        search_metadata = {
            "search_parameters": {
                "content_type": request.content_type,
                "platform": request.platform,
                "similarity_threshold": request.similarity_threshold,
                "include_performance": request.include_performance
            },
            "performance_distribution": _analyze_performance_distribution(results),
            "content_type_distribution": _analyze_content_type_distribution(results),
            "platform_distribution": _analyze_platform_distribution(results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Similarity search completed: {len(results)} results for query '{query[:50]}...'")
        
        return SimilaritySearchResponse(
            status="success",
            query=query,
            results_count=len(results),
            results=formatted_results,
            search_metadata=search_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")

@router.post("/recommend", response_model=ContentRecommendationResponse)
async def get_content_recommendations(
    request: ContentRecommendationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ContentRecommendationResponse:
    """
    Get comprehensive content recommendations for a topic and platform
    """
    try:
        # Clean and validate inputs
        topic = clean_text_input(request.topic)
        target_platform = clean_text_input(request.target_platform).lower()
        
        # Validate platform
        valid_platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok"]
        if target_platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
            )
        
        # Get recommendations
        recommendations = await similarity_service.get_content_recommendations(
            topic=topic,
            target_platform=target_platform,
            user_preferences=request.user_preferences,
            db=db
        )
        
        # Filter by requested recommendation types
        if request.recommendation_types:
            recommendations = [
                rec for rec in recommendations 
                if rec.recommendation_type in request.recommendation_types
            ]
        
        # Format recommendations for response
        formatted_recommendations = []
        for rec in recommendations:
            formatted_rec = {
                "recommendation_type": rec.recommendation_type,
                "confidence_score": rec.confidence_score,
                "reasoning": rec.reasoning,
                "content_suggestions": [
                    {
                        "content_id": suggestion.content_id,
                        "content": suggestion.content,
                        "similarity_score": suggestion.similarity_score,
                        "performance_tier": suggestion.performance_tier,
                        "repurposing_potential": suggestion.repurposing_potential,
                        "engagement_metrics": suggestion.engagement_metrics,
                        "created_at": suggestion.created_at.isoformat() if suggestion.created_at else None
                    }
                    for suggestion in rec.content_suggestions
                ],
                "platform_adaptations": rec.platform_adaptations,
                "timing_recommendations": rec.timing_recommendations,
                "hashtag_suggestions": rec.hashtag_suggestions
            }
            formatted_recommendations.append(formatted_rec)
        
        # Generate recommendation metadata
        generation_metadata = {
            "user_preferences": request.user_preferences,
            "recommendation_types_requested": request.recommendation_types,
            "total_content_analyzed": sum(len(rec.content_suggestions) for rec in recommendations),
            "average_confidence": sum(rec.confidence_score for rec in recommendations) / len(recommendations) if recommendations else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Generated {len(recommendations)} recommendations for topic '{topic}' on {target_platform}")
        
        return ContentRecommendationResponse(
            status="success",
            topic=topic,
            target_platform=target_platform,
            recommendations_count=len(formatted_recommendations),
            recommendations=formatted_recommendations,
            generation_metadata=generation_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")

@router.post("/repurpose")
async def repurpose_content(
    request: RepurposingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate platform-specific adaptations for existing content
    """
    try:
        # Find the original content
        original_content = db.query(ContentItem).filter(
            ContentItem.id == request.content_id,
            ContentItem.user_id == current_user.id
        ).first()
        
        if not original_content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Validate target platforms
        valid_platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok"]
        invalid_platforms = [p for p in request.target_platforms if p not in valid_platforms]
        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platforms: {', '.join(invalid_platforms)}"
            )
        
        adaptations = {}
        
        # Generate adaptations for each target platform
        for platform in request.target_platforms:
            # Get similar high-performing content for the platform if requested
            if request.maintain_performance:
                similar_content = await similarity_service.find_similar_content(
                    query=original_content.content,
                    platform=platform,
                    limit=3,
                    similarity_threshold=0.6,
                    include_performance_data=True,
                    db=db
                )
                
                # Find the highest performing similar content for inspiration
                high_performing = [c for c in similar_content if c.performance_tier in ["high", "viral"]]
                if high_performing:
                    performance_insights = {
                        "best_performing_similar": high_performing[0].content,
                        "performance_tier": high_performing[0].performance_tier,
                        "engagement_rate": high_performing[0].engagement_metrics.get("engagement_rate", 0)
                    }
                else:
                    performance_insights = None
            else:
                performance_insights = None
            
            # Generate platform-specific adaptation
            adapted_content = similarity_service._adapt_content_for_platform(
                original_content.content, platform
            )
            
            # Get timing and hashtag recommendations
            timing_rec = similarity_service._get_timing_recommendations(platform)
            hashtag_rec = similarity_service._generate_hashtag_suggestions(
                original_content.topic_category or "general", platform
            )
            
            adaptations[platform] = {
                "adapted_content": adapted_content,
                "original_length": len(original_content.content),
                "adapted_length": len(adapted_content),
                "timing_recommendations": timing_rec,
                "hashtag_suggestions": hashtag_rec,
                "performance_insights": performance_insights,
                "adaptation_notes": f"Optimized for {platform} audience and format requirements"
            }
        
        return {
            "status": "success",
            "original_content": {
                "id": original_content.id,
                "content": original_content.content,
                "platform": original_content.platform,
                "performance_tier": original_content.performance_tier
            },
            "adaptations": adaptations,
            "total_platforms": len(request.target_platforms),
            "maintain_performance": request.maintain_performance,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error repurposing content: {e}")
        raise HTTPException(status_code=500, detail=f"Content repurposing failed: {str(e)}")

@router.post("/analyze")
async def analyze_content_similarity(
    request: ContentAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze content for similarity to existing high-performing content
    """
    try:
        # Clean and validate content
        content = clean_text_input(request.content)
        validate_text_length(content, min_length=10, max_length=10000)
        
        # Find similar existing content
        similar_content = await similarity_service.find_similar_content(
            query=content,
            platform=request.platform,
            limit=10,
            similarity_threshold=0.5,
            include_performance_data=True,
            db=db
        )
        
        # Analyze similarity patterns
        analysis = {
            "content_length": len(content),
            "similar_content_found": len(similar_content),
            "highest_similarity": max([c.similarity_score for c in similar_content]) if similar_content else 0.0,
            "average_similarity": sum([c.similarity_score for c in similar_content]) / len(similar_content) if similar_content else 0.0,
            "performance_prediction": _predict_content_performance(content, similar_content),
            "optimization_suggestions": _generate_optimization_suggestions(content, similar_content, request.platform),
            "duplicate_risk": "high" if any(c.similarity_score > 0.9 for c in similar_content) else "low",
            "similar_content_breakdown": [
                {
                    "content_id": c.content_id,
                    "similarity_score": c.similarity_score,
                    "performance_tier": c.performance_tier,
                    "platform": c.platform,
                    "engagement_rate": c.engagement_metrics.get("engagement_rate", 0)
                }
                for c in similar_content[:5]  # Top 5 most similar
            ]
        }
        
        return {
            "status": "success",
            "analyzed_content": content[:200] + "..." if len(content) > 200 else content,
            "platform": request.platform,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.get("/trending")
async def get_trending_content(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    days_back: int = Query(7, ge=1, le=30, description="Days to look back for trending content"),
    limit: int = Query(20, ge=5, le=100, description="Number of trending items to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get trending content based on recent performance metrics
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Query for high-performing recent content
        query = db.query(ContentItem).filter(
            ContentItem.created_at >= start_date,
            ContentItem.created_at <= end_date,
            ContentItem.performance_tier.in_(["viral", "high"]),
            ContentItem.engagement_rate > 5.0
        )
        
        # Apply filters
        if platform:
            query = query.filter(ContentItem.platform == platform)
        if content_type:
            query = query.filter(ContentItem.content_type == content_type)
        
        # Order by engagement rate and viral score
        trending_content = query.order_by(
            ContentItem.viral_score.desc(),
            ContentItem.engagement_rate.desc()
        ).limit(limit).all()
        
        # Format results
        trending_items = []
        for item in trending_content:
            # Find similar content to this trending item
            similar_items = await similarity_service.find_similar_content(
                query=item.content,
                limit=3,
                similarity_threshold=0.7,
                db=db
            )
            
            trending_items.append({
                "content_id": item.id,
                "content": item.content,
                "platform": item.platform,
                "content_type": item.content_type,
                "engagement_rate": item.engagement_rate,
                "viral_score": item.viral_score,
                "performance_tier": item.performance_tier,
                "likes_count": item.likes_count,
                "shares_count": item.shares_count,
                "comments_count": item.comments_count,
                "hashtags": item.hashtags,
                "topic_category": item.topic_category,
                "created_at": item.created_at.isoformat(),
                "similar_content_count": len(similar_items),
                "platform_url": item.platform_url
            })
        
        # Generate trending analysis
        analysis = {
            "total_trending_items": len(trending_items),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": days_back
            },
            "platform_breakdown": _analyze_platform_distribution([
                type('obj', (object,), {'platform': item['platform']}) for item in trending_items
            ]),
            "avg_engagement_rate": sum([item['engagement_rate'] for item in trending_items]) / len(trending_items) if trending_items else 0,
            "top_hashtags": _extract_top_hashtags([item['hashtags'] for item in trending_items]),
            "top_topics": _extract_top_topics([item['topic_category'] for item in trending_items])
        }
        
        return {
            "status": "success",
            "trending_content": trending_items,
            "analysis": analysis,
            "filters_applied": {
                "platform": platform,
                "content_type": content_type,
                "days_back": days_back
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending content: {e}")
        raise HTTPException(status_code=500, detail=f"Trending content retrieval failed: {str(e)}")

# Helper functions
def _analyze_performance_distribution(results: List[SimilarityResult]) -> Dict[str, int]:
    """Analyze performance tier distribution in results"""
    distribution = {"viral": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    for result in results:
        tier = result.performance_tier
        if tier in distribution:
            distribution[tier] += 1
        else:
            distribution["unknown"] += 1
    return distribution

def _analyze_content_type_distribution(results: List[SimilarityResult]) -> Dict[str, int]:
    """Analyze content type distribution in results"""
    distribution = {}
    for result in results:
        content_type = result.content_type
        distribution[content_type] = distribution.get(content_type, 0) + 1
    return distribution

def _analyze_platform_distribution(results: List) -> Dict[str, int]:
    """Analyze platform distribution in results"""
    distribution = {}
    for result in results:
        platform = getattr(result, 'platform', 'unknown')
        if platform:
            distribution[platform] = distribution.get(platform, 0) + 1
    return distribution

def _predict_content_performance(content: str, similar_content: List[SimilarityResult]) -> Dict[str, Any]:
    """Predict performance based on similar content analysis"""
    if not similar_content:
        return {"predicted_tier": "unknown", "confidence": 0.0, "reasoning": "No similar content found"}
    
    # Calculate weighted average based on similarity scores
    total_weight = sum(c.similarity_score for c in similar_content)
    
    if total_weight == 0:
        return {"predicted_tier": "unknown", "confidence": 0.0, "reasoning": "No similar content found"}
    
    # Weight engagement rates by similarity
    weighted_engagement = sum(
        c.engagement_metrics.get("engagement_rate", 0) * c.similarity_score 
        for c in similar_content
    ) / total_weight
    
    # Predict tier based on weighted engagement
    if weighted_engagement >= 10.0:
        predicted_tier = "high"
    elif weighted_engagement >= 5.0:
        predicted_tier = "medium"
    else:
        predicted_tier = "low"
    
    # Calculate confidence based on similarity scores and sample size
    avg_similarity = sum(c.similarity_score for c in similar_content) / len(similar_content)
    confidence = min(0.95, avg_similarity * (len(similar_content) / 10))
    
    return {
        "predicted_tier": predicted_tier,
        "predicted_engagement_rate": round(weighted_engagement, 2),
        "confidence": round(confidence, 2),
        "similar_samples": len(similar_content),
        "reasoning": f"Based on {len(similar_content)} similar content pieces with average engagement of {weighted_engagement:.1f}%"
    }

def _generate_optimization_suggestions(content: str, similar_content: List[SimilarityResult], platform: Optional[str]) -> List[str]:
    """Generate content optimization suggestions"""
    suggestions = []
    
    if not similar_content:
        suggestions.append("Consider researching similar content to identify optimization opportunities")
        return suggestions
    
    # Analyze high-performing similar content
    high_performing = [c for c in similar_content if c.performance_tier in ["high", "viral"]]
    
    if high_performing:
        avg_length_high = sum(len(c.content) for c in high_performing) / len(high_performing)
        content_length = len(content)
        
        if content_length < avg_length_high * 0.7:
            suggestions.append(f"Consider expanding content - high-performing similar content averages {int(avg_length_high)} characters")
        elif content_length > avg_length_high * 1.5:
            suggestions.append(f"Consider shortening content - high-performing similar content averages {int(avg_length_high)} characters")
        
        # Analyze hashtags
        common_hashtags = []
        for c in high_performing:
            common_hashtags.extend(c.tags)
        
        if common_hashtags:
            from collections import Counter
            top_hashtags = [tag for tag, count in Counter(common_hashtags).most_common(3)]
            suggestions.append(f"Consider using popular hashtags: {', '.join(top_hashtags)}")
    
    # Platform-specific suggestions
    if platform:
        platform_suggestions = {
            "twitter": ["Keep it concise", "Use trending hashtags", "Include a call-to-action"],
            "linkedin": ["Add professional insights", "Use industry keywords", "Include data or statistics"],
            "instagram": ["Focus on visual appeal", "Use story-telling", "Include lifestyle elements"],
            "facebook": ["Encourage community engagement", "Ask questions", "Share personal experiences"],
            "tiktok": ["Keep it trendy and fun", "Use popular sounds", "Include challenges or trends"]
        }
        suggestions.extend(platform_suggestions.get(platform, []))
    
    return suggestions[:5]  # Return top 5 suggestions

def _extract_top_hashtags(hashtag_lists: List[List[str]], limit: int = 10) -> List[Dict[str, Any]]:
    """Extract most common hashtags from a list of hashtag lists"""
    all_hashtags = []
    for hashtags in hashtag_lists:
        if hashtags:
            all_hashtags.extend(hashtags)
    
    if not all_hashtags:
        return []
    
    from collections import Counter
    hashtag_counts = Counter(all_hashtags)
    
    return [
        {"hashtag": hashtag, "count": count}
        for hashtag, count in hashtag_counts.most_common(limit)
    ]

def _extract_top_topics(topics: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """Extract most common topics"""
    if not topics:
        return []
    
    # Filter out None values
    valid_topics = [topic for topic in topics if topic]
    
    if not valid_topics:
        return []
    
    from collections import Counter
    topic_counts = Counter(valid_topics)
    
    return [
        {"topic": topic, "count": count}
        for topic, count in topic_counts.most_common(limit)
    ]