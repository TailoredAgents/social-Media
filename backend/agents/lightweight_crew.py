"""
Lightweight CrewAI setup - minimal memory footprint
Only loads essential components for social media automation
"""
import os
from typing import Optional, Dict, Any

# Lazy imports to reduce memory usage
def get_openai_client():
    """Lazy load OpenAI client only when needed"""
    from openai import OpenAI, AsyncOpenAI
    from backend.core.config import get_settings
    settings = get_settings()
    return {
        'sync': OpenAI(api_key=settings.openai_api_key),
        'async': AsyncOpenAI(api_key=settings.openai_api_key)
    }

def get_search_tool():
    """Lazy load search tool only when needed"""
    try:
        from crewai_tools import SerperDevTool
        from backend.core.config import get_settings
        settings = get_settings()
        return SerperDevTool(api_key=settings.serper_api_key)
    except ImportError:
        return None

class LightweightAgent:
    """Minimal agent without heavy CrewAI dependencies"""
    
    def __init__(self, role: str, goal: str, backstory: str):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self._openai_client = None
        self._search_tool = None
    
    @property
    def openai_client(self):
        if self._openai_client is None:
            self._openai_client = get_openai_client()
        return self._openai_client
    
    @property
    def search_tool(self):
        if self._search_tool is None:
            self._search_tool = get_search_tool()
        return self._search_tool
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task using minimal resources with model fallback"""
        # Define fallback models
        models_to_try = ["gpt-5-mini", "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        
        for model in models_to_try:
            try:
                # Use async OpenAI client to avoid blocking
                async_client = self.openai_client['async']
                
                # Import utility for correct parameters
                from backend.core.openai_utils import get_openai_completion_params
                
                # Get correct parameters for the model
                params = get_openai_completion_params(
                    model=model,
                    max_tokens=500,
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": f"You are a {self.role}. {self.backstory}"},
                        {"role": "user", "content": f"Goal: {self.goal}\n\nTask: {task_description}"}
                    ]
                )
                
                # Make async API call
                response = await async_client.chat.completions.create(**params)
                
                return {
                    "status": "success",
                    "result": response.choices[0].message.content.strip(),
                    "agent": self.role,
                    "model_used": model,
                    "memory_efficient": True
                }
                
            except Exception as e:
                # Log the error and try next model
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"LightweightAgent failed with {model}: {e}")
                
                # Check if this is the last model
                if model == models_to_try[-1]:
                    return {
                        "status": "error",
                        "error": f"All models failed. Last error: {str(e)}",
                        "agent": self.role
                    }
                continue

# Pre-defined lightweight agents
research_agent = LightweightAgent(
    role="Research Specialist",
    goal="Find trending topics and insights",
    backstory="You efficiently research social media trends using minimal resources."
)

content_agent = LightweightAgent(
    role="Content Creator",
    goal="Create engaging social media content",
    backstory="You create compelling content optimized for different platforms."
)

async def lightweight_daily_workflow(topic: str = "social media trends") -> Dict[str, Any]:
    """Lightweight version of daily content workflow"""
    
    # Step 1: Research (minimal)
    research_result = await research_agent.execute_task(
        f"Research current trends about {topic}. Provide 3 key insights in bullet points."
    )
    
    if research_result["status"] != "success":
        return {"status": "error", "step": "research", "error": research_result.get("error")}
    
    # Step 2: Content generation
    research_insights = research_result["result"]
    content_result = await content_agent.execute_task(
        f"Based on these insights: {research_insights}\n\nCreate 2 social media posts - one for Twitter and one for Instagram. Include relevant hashtags."
    )
    
    return {
        "status": "success",
        "workflow": "lightweight_daily",
        "research": research_insights,
        "content": content_result.get("result", ""),
        "memory_optimized": True
    }