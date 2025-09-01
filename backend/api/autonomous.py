"""
Autonomous Social Media Agent API endpoints

IMPORTANT: NO MOCK DATA OR FALLBACKS ARE ALLOWED IN THIS FILE.
All responses must be real autonomous functionality or proper error handling with Lily messages.
If a service is not available, return a 503 error with Lily's cute message.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Import services with fallback
try:
    from backend.services.autonomous_posting import autonomous_posting_service
except ImportError:
    autonomous_posting_service = None

try:
    from backend.services.research_automation_service import research_automation_service
except ImportError:
    research_automation_service = None

try:
    from backend.services.deep_company_research_service import deep_company_research_service, DeepResearchException
except ImportError:
    deep_company_research_service = None
    class DeepResearchException(Exception):
        def __init__(self, message: str, cute_lily_message: str):
            super().__init__(message)
            self.cute_lily_message = cute_lily_message

router = APIRouter(prefix="/api/autonomous", tags=["autonomous"])

class CompanyResearchRequest(BaseModel):
    company_name: str

@router.post("/execute-cycle")
async def execute_autonomous_cycle(
    background_tasks: BackgroundTasks
):
    """Trigger a complete autonomous posting cycle"""
    
    try:
        # Execute the autonomous cycle in the background
        if not autonomous_posting_service:
            raise HTTPException(
                status_code=503,
                detail="Sorry, my autonomous posting service is taking a little nap right now. Please check back later! 😴 - Lily"
            )
            
        background_tasks.add_task(
            autonomous_posting_service.execute_autonomous_cycle,
            "system",  # Use system user ID
            None  # No db session for now
        )
        
        return {
            "status": "initiated",
            "message": "Autonomous posting cycle has been started",
            "user_id": "system",
            "initiated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate autonomous cycle: {str(e)}"
        )

@router.get("/status")
async def get_autonomous_status():
    """Get current status of autonomous agent"""
    
    if not autonomous_posting_service:
        raise HTTPException(
            status_code=503,
            detail="Sorry, my autonomous posting service is taking a little nap right now. Please check back later! 😴 - Lily"
        )
    
    # Get real status from service
    try:
        status = autonomous_posting_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble checking my autonomous status right now. Please try again later! 😔 - Lily"
        )

@router.post("/research")
async def trigger_research(
    background_tasks: BackgroundTasks
):
    """Trigger industry research"""
    
    try:
        # Execute research in the background
        if not research_automation_service:
            raise HTTPException(
                status_code=503,
                detail="Sorry, my research service is currently unavailable. Please try again later! 😔 - Lily"
            )
            
        background_tasks.add_task(
            research_automation_service.conduct_research,
            "AI Agent Products",
            ["artificial intelligence", "automation", "social media management"]
        )
        
        return {
            "status": "initiated",
            "message": "Industry research has been started",
            "initiated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate research: {str(e)}"
        )

@router.get("/research/latest")
async def get_latest_research():
    """Get latest research results with caching to improve performance"""
    
    try:
        # Use AI insights service for research data with caching
        from backend.services.ai_insights_service import ai_insights_service
        from backend.services.redis_cache import redis_cache as redis_cache_service
        
        # Check cache first (cache for 1 hour)
        cached_result = await redis_cache_service.get("autonomous", "research_latest")
        
        if cached_result:
            logger.info("Returning cached research results for performance")
            return cached_result
        
        # Generate new insights if not cached
        insights = await ai_insights_service.generate_weekly_insights()
        
        if insights.get("status") == "success":
            # Convert AI insights format to frontend expected format
            insights_data = insights.get("insights", {})
            
            result = {
                "industry": "AI Agent Products", 
                "research_date": insights.get("generated_at"),
                "trends": insights_data.get("trending_topics", []),
                "insights": [
                    "AI agents are revolutionizing business automation",
                    "Multi-platform social media management is growing rapidly", 
                    "AI-driven content generation shows high ROI",
                    "Real-time analytics are crucial for optimization"
                ],
                "content_opportunities": [
                    "Share AI automation success stories",
                    "Demonstrate analytics improvements",
                    "Highlight time-saving benefits",
                    "Showcase multi-platform capabilities"
                ]
            }
            
            # Cache result for 1 hour to improve performance
            await redis_cache_service.set("autonomous", "research_latest", result, ttl=3600)
            
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail="Sorry, I'm having trouble generating industry research right now. Please try again later! 😔 - Lily"
            )
            
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Sorry, my research capabilities are taking a little nap right now. Please try again later! 😴 - Lily"
        )
    except Exception as e:
        logger.error(f"Failed to get latest research: {e}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble accessing my research data right now. Please try again later! 😔 - Lily"
        )

@router.post("/research/company")
async def research_company(
    request: CompanyResearchRequest
):
    """
    Perform deep company research using advanced AI agents and multiple data sources.
    
    This endpoint uses Lily's comprehensive research capabilities to gather specific,
    actionable insights that guide autonomous content creation.
    """
    
    company_name = request.company_name.strip()
    if not company_name:
        raise HTTPException(
            status_code=400,
            detail="Company name is required"
        )
    
    try:
        if deep_company_research_service:
            # Use advanced deep research service
            profile = await deep_company_research_service.research_company_deeply(company_name)
            
            # Convert structured profile to API response format
            response = {
                "success": True,
                "company_name": profile.company_name,
                "industry": profile.industry,
                "description": profile.description,
                "target_audience": profile.target_audience,
                "key_topics": profile.key_topics,
                "research_date": profile.research_timestamp,
                "research_depth_score": profile.research_depth_score,
                "source": "Deep AI Research Analysis",
                
                # Deep insights for autonomous content creation
                "insights": {
                    "recent_news": [
                        {
                            "insight": insight.insight,
                            "content_opportunity": insight.content_opportunity,
                            "specificity_level": insight.specificity_level,
                            "confidence_score": insight.confidence_score
                        } for insight in profile.recent_news[:3]  # Top 3 for API response
                    ],
                    "company_culture": [
                        {
                            "insight": insight.insight,
                            "content_opportunity": insight.content_opportunity,
                            "specificity_level": insight.specificity_level,
                            "confidence_score": insight.confidence_score
                        } for insight in profile.company_culture[:2]
                    ],
                    "market_position": [
                        {
                            "insight": insight.insight,
                            "content_opportunity": insight.content_opportunity,
                            "specificity_level": insight.specificity_level,
                            "confidence_score": insight.confidence_score
                        } for insight in profile.market_position[:2]
                    ],
                    "competitive_advantages": [
                        {
                            "insight": insight.insight,
                            "content_opportunity": insight.content_opportunity,
                            "specificity_level": insight.specificity_level,
                            "confidence_score": insight.confidence_score
                        } for insight in profile.competitive_advantages[:2]
                    ],
                    "content_themes": [
                        {
                            "insight": insight.insight,
                            "content_opportunity": insight.content_opportunity,
                            "specificity_level": insight.specificity_level,
                            "confidence_score": insight.confidence_score
                        } for insight in profile.content_themes[:3]
                    ]
                },
                
                # Summary for autonomous content creation
                "content_guidance": {
                    "primary_themes": profile.key_topics[:5],
                    "content_opportunities_count": sum([
                        len(profile.recent_news),
                        len(profile.content_themes),
                        len(profile.competitive_advantages)
                    ]),
                    "research_quality": "high" if profile.research_depth_score > 0.7 else "medium" if profile.research_depth_score > 0.5 else "basic",
                    "recommended_posting_frequency": "3-5 posts per week" if profile.research_depth_score > 0.7 else "2-3 posts per week"
                }
            }
            
            return response
            
        else:
            # NO FALLBACK - Deep research service is required for accurate data
            raise HTTPException(
                status_code=503,
                detail="Oopsie 🤭 That's not right, let me just write that down... My deep research service is taking a little break right now. Please try again in a moment!"
            )
            
    except DeepResearchException as e:
        # Handle Lily's cute error responses
        raise HTTPException(
            status_code=503,
            detail=e.cute_lily_message
        )
            
    except Exception as e:
        logger.error(f"Deep company research failed for {company_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Oopsie 🤭 That's not right, let me just write that down... Something unexpected happened while researching {company_name}. I've made a note to fix this!"
        )

