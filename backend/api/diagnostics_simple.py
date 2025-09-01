from fastapi import APIRouter
from backend.core.config import get_settings
import logging

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])
logger = logging.getLogger(__name__)

@router.get("/ai-features")
async def diagnose_ai_features():
    settings = get_settings()
    
    # Check API Keys
    openai_configured = bool(settings.openai_api_key and settings.openai_api_key != "")
    serper_configured = bool(settings.serper_api_key and settings.serper_api_key != "your_serper_api_key_here")
    
    # Test service imports
    services = {}
    
    try:
        from backend.services.ai_insights_service import ai_insights_service
        services["ai_insights"] = "available"
    except Exception as e:
        services["ai_insights"] = f"failed: {e}"
    
    try:
        from backend.services.image_generation_service import ImageGenerationService
        services["image_generation"] = "available"
    except Exception as e:
        services["image_generation"] = f"failed: {e}"
    
    return {
        "status": "diagnostic_complete",
        "api_keys": {
            "openai_configured": openai_configured,
            "serper_configured": serper_configured
        },
        "services": services,
        "lily_message": "I've checked my AI capabilities! 🔍 - Lily"
    }

@router.get("/industry-research")
async def diagnose_industry_research():
    settings = get_settings()
    
    issues = []
    if not settings.openai_api_key:
        issues.append("OpenAI API key not configured")
    if not settings.serper_api_key or settings.serper_api_key == "your_serper_api_key_here":
        issues.append("Serper API key not configured - using fallback search")
    
    try:
        from backend.services.ai_insights_service import ai_insights_service
        service_available = True
    except Exception as e:
        service_available = False
        issues.append(f"AI Insights service import failed: {e}")
    
    return {
        "status": "diagnosis_complete",
        "service_available": service_available,
        "issues": issues,
        "lily_message": "I've checked my research tools! 🔍 - Lily" if len(issues) == 0 else f"I found {len(issues)} research issues! 😔 - Lily"
    }