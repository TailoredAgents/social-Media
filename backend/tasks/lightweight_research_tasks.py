"""
Memory-optimized research tasks using GPT-5-mini with web search
Replaces heavy CrewAI agents with lightweight GPT-5 Responses API calls with real-time web search
"""
import logging
import asyncio
import gc
from typing import List, Dict, Any
from celery import current_task
from backend.tasks.celery_app import celery_app
from backend.services.ai_insights_service import ai_insights_service
from backend.core.openai_utils import get_openai_completion_params
from openai import AsyncOpenAI
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@celery_app.task(bind=True)
def lightweight_daily_research(self, topics=None):
    """Memory-optimized daily research without CrewAI agents"""
    if topics is None:
        topics = [
            "AI marketing trends",
            "social media best practices", 
            "content marketing insights"
        ]
    
    try:
        results = []
        total_topics = len(topics)
        
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': total_topics, 'status': 'Starting lightweight research...'}
        )
        
        # Use existing AI insights service instead of CrewAI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, topic in enumerate(topics):
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': i+1, 'total': total_topics, 'status': f'Researching: {topic}'}
                )
                
                # Simple research using existing service
                research_result = loop.run_until_complete(
                    _lightweight_topic_research(topic)
                )
                
                results.append({
                    'topic': topic,
                    'insights': research_result.get('insights', []),
                    'status': 'completed'
                })
                
                # Force garbage collection between topics
                gc.collect()
        finally:
            loop.close()
        
        return {
            'status': 'success',
            'message': f'Lightweight research completed for {len(results)} topics',
            'topics_researched': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Lightweight daily research failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Research failed: {str(exc)}'
        }

async def _lightweight_topic_research(topic: str) -> Dict[str, Any]:
    """Research topic using GPT-5-mini with web search via Responses API"""
    try:
        # Use GPT-5-mini with web search for current information
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        prompt = f"""Use web search to provide 3-5 current insights about {topic}. Focus on:
        1. Recent developments (last 30 days)
        2. Current best practices
        3. Actionable tips from industry leaders
        
        Base your response on real, current web information. Keep each insight concise (1-2 sentences)."""
        
        # Use Responses API with web search tool
        response = await client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            tools=[
                {
                    "type": "web_search"
                }
            ],
            text={"verbosity": "low"}  # Concise responses for Celery tasks
        )
        
        # Extract insights from response
        insights_text = response.output_text if hasattr(response, 'output_text') else str(response)
        insights = [line.strip() for line in insights_text.split('\n') if line.strip()]
        
        return {
            'topic': topic,
            'insights': insights[:5],  # Limit to 5 insights
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Lightweight research failed for {topic}: {e}")
        return {
            'topic': topic,
            'insights': [],
            'status': 'error',
            'error': str(e)
        }

@celery_app.task(bind=True)
def lightweight_content_generation(self, research_insights: List[str], platform: str = "twitter"):
    """Memory-optimized content generation"""
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 2, 'status': 'Generating content...'}
        )
        
        # Simple OpenAI call instead of CrewAI content agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            content = loop.run_until_complete(
                _generate_simple_content(research_insights, platform)
            )
            
            return {
                'status': 'success',
                'content': content,
                'platform': platform
            }
        finally:
            loop.close()
            gc.collect()
        
    except Exception as exc:
        logger.error(f"Lightweight content generation failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Content generation failed: {str(exc)}'
        }

async def _generate_simple_content(insights: List[str], platform: str) -> str:
    """Content generation using GPT-5-mini with web search for trends"""
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        insights_text = "\n".join(insights[:3])  # Use only first 3 insights
        
        prompt = f"""Use web search to find current {platform} trends, then create a post based on these insights:
        {insights_text}
        
        Requirements:
        - Research current viral {platform} formats
        - Engaging and professional tone
        - Include 1-2 trending hashtags
        - Keep within {platform} character limits
        - Make it actionable and timely"""
        
        # Use Responses API with web search for trending content
        response = await client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            tools=[
                {
                    "type": "web_search"
                }
            ],
            text={"verbosity": "low"}  # Concise for social media
        )
        
        return response.output_text.strip() if hasattr(response, 'output_text') else str(response).strip()
        
    except Exception as e:
        logger.error(f"Simple content generation failed: {e}")
        return f"Error generating content: {str(e)}"

# Disable the heavy CrewAI tasks by default
@celery_app.task(bind=True)
def disabled_heavy_research_task(self):
    """Placeholder for disabled heavy research tasks"""
    return {
        'status': 'disabled',
        'message': 'Heavy CrewAI tasks disabled to prevent memory issues',
        'recommendation': 'Use lightweight_daily_research instead'
    }