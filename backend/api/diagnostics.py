"""
AI Features Diagnostics API

Provides comprehensive diagnostics for all AI features and their dependencies.
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

# Test imports for all AI services
ai_service_status = {}

# Test OpenAI import and API key
try:
    from openai import AsyncOpenAI
    ai_service_status["openai_import"] = {"status": "available", "error": None}
except ImportError as e:
    ai_service_status["openai_import"] = {"status": "failed", "error": str(e)}

# Test AI Insights Service
try:
    from backend.services.ai_insights_service import ai_insights_service
    ai_service_status["ai_insights_service"] = {"status": "available", "error": None}
except ImportError as e:
    ai_service_status["ai_insights_service"] = {"status": "failed", "error": str(e)}

# Test Image Generation Service
try:
    from backend.services.image_generation_service import ImageGenerationService
    ai_service_status["image_generation_service"] = {"status": "available", "error": None}
except ImportError as e:
    ai_service_status["image_generation_service"] = {"status": "failed", "error": str(e)}

@router.get("/ai-features")
async def diagnose_ai_features():
    """
    Comprehensive diagnostics for all AI features and their dependencies
    """
    try:
        settings = get_settings()
        
        # Check API Keys
        api_keys_status = {
            "openai_api_key": {
                "configured": bool(settings.openai_api_key and settings.openai_api_key != ""),
                "length": len(settings.openai_api_key) if settings.openai_api_key else 0,
                "starts_with_sk": settings.openai_api_key.startswith("sk-") if settings.openai_api_key else False
            },
            "serper_api_key": {
                "configured": bool(settings.serper_api_key and settings.serper_api_key != "your_serper_api_key_here"),
                "length": len(settings.serper_api_key) if settings.serper_api_key else 0,
                "is_placeholder": settings.serper_api_key == "your_serper_api_key_here"
            }
        }
        
        # Test OpenAI Connection
        openai_test = {"status": "not_tested", "error": None}
        if api_keys_status["openai_api_key"]["configured"]:
            try:
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                response = await client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": "Test connection - respond with 'OK'"}],
                    max_completion_tokens=5  # GPT-5 uses max_completion_tokens
                )
                openai_test = {"status": "connected", "response": response.choices[0].message.content}
            except Exception as e:
                openai_test = {"status": "failed", "error": str(e)}
        else:
            openai_test = {"status": "no_api_key", "error": "OpenAI API key not configured"}
        
        # Test AI Insights Service
        ai_insights_test = {"status": "not_tested", "error": None}
        if ai_service_status["ai_insights_service"]["status"] == "available":
            try:
                insights = await ai_insights_service.generate_weekly_insights()
                if insights.get("status") == "success":
                    ai_insights_test = {"status": "working", "insights_generated": True}
                else:
                    ai_insights_test = {"status": "failed", "error": insights.get("error", "Unknown error")}
            except Exception as e:
                ai_insights_test = {"status": "failed", "error": str(e)}
        else:
            ai_insights_test = {"status": "service_unavailable", "error": ai_service_status["ai_insights_service"]["error"]}
        
        # Service availability summary
        service_summary = {
            "total_services": len(ai_service_status),
            "available_services": sum(1 for s in ai_service_status.values() if s["status"] == "available"),
            "failed_services": [k for k, v in ai_service_status.items() if v["status"] == "failed"],
            "critical_issues": []
        }
        
        # Identify critical issues
        if not api_keys_status["openai_api_key"]["configured"]:
            service_summary["critical_issues"].append("OpenAI API key not configured")
        
        if openai_test["status"] == "failed":
            service_summary["critical_issues"].append("OpenAI API connection failed: " + str(openai_test["error"]))
        
        if ai_insights_test["status"] == "failed":
            service_summary["critical_issues"].append("AI Insights service failed: " + str(ai_insights_test["error"]))
        
        return {
            "status": "diagnostic_complete",
            "timestamp": datetime.now().isoformat(),
            "api_keys": api_keys_status,
            "service_imports": ai_service_status,
            "connection_tests": {
                "openai": openai_test,
                "ai_insights": ai_insights_test
            },
            "summary": service_summary,
            "lily_message": "I've checked all my AI capabilities! 🔍 - Lily" if len(service_summary["critical_issues"]) == 0 else "I found some issues with my AI tools! 😔 - Lily"
        }
        
    except Exception as e:
        logger.error("Diagnostics failed: " + str(e))
        raise HTTPException(status_code=500, detail="Diagnostics failed: " + str(e))

@router.get("/industry-research")
async def diagnose_industry_research():
    """
    Specific diagnostics for industry research functionality
    """
    try:
        settings = get_settings()
        
        # Check if AI insights service is available
        if ai_service_status["ai_insights_service"]["status"] != "available":
            return {
                "status": "service_unavailable",
                "error": "AI Insights Service could not be imported",
                "import_error": ai_service_status["ai_insights_service"]["error"],
                "lily_message": "Sorry, my research capabilities are taking a little nap! 😴 - Lily"
            }
        
        # Test OpenAI for analysis
        openai_test = {"status": "not_tested", "error": None}
        if settings.openai_api_key:
            try:
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                response = await client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": "Test research analysis: What are AI agents? One sentence."}],
                    max_completion_tokens=50  # GPT-5 uses max_completion_tokens
                )
                openai_test = {"status": "working", "sample_response": response.choices[0].message.content}
            except Exception as e:
                openai_test = {"status": "failed", "error": str(e)}
        else:
            openai_test = {"status": "no_api_key"}
        
        # Test search capability
        search_config = {
            "serper_api_configured": bool(settings.serper_api_key and settings.serper_api_key != "your_serper_api_key_here"),
            "search_method": "serper" if settings.serper_api_key and settings.serper_api_key != "your_serper_api_key_here" else "alternative"
        }
        
        # Test full insights generation
        full_test = {"status": "not_tested", "error": None}
        try:
            insights = await ai_insights_service.generate_weekly_insights()
            if insights.get("status") == "success":
                full_test = {
                    "status": "success",
                    "insights_generated": True,
                    "has_real_time_data": insights.get("metadata", {}).get("has_real_time_data", False)
                }
            else:
                full_test = {"status": "failed", "error": insights.get("error", "Unknown error")}
        except Exception as e:
            full_test = {"status": "failed", "error": str(e)}
        
        # Generate recommendations
        recommendations = []
        if not settings.openai_api_key:
            recommendations.append("Set OPENAI_API_KEY environment variable")
        if openai_test["status"] == "failed":
            recommendations.append("Check OpenAI API key and account status")
        if not search_config["serper_api_configured"]:
            recommendations.append("Set SERPER_API_KEY for better web search results")
        if full_test["status"] == "failed":
            recommendations.append("Check AI Insights service configuration")
        
        return {
            "status": "diagnosis_complete",
            "timestamp": datetime.now().isoformat(),
            "openai_connection": openai_test,
            "search_capability": search_config,
            "insights_generation": full_test,
            "recommendations": recommendations,
            "lily_message": "I've checked my research tools! 🔍 - Lily" if full_test["status"] == "success" else "I found some research issues! 😔 - Lily"
        }
        
    except Exception as e:
        logger.error("Industry research diagnostics failed: " + str(e))
        return {
            "status": "diagnostic_failed",
            "error": str(e),
            "lily_message": "Oops! I had trouble checking my research capabilities! 😅 - Lily"
        }