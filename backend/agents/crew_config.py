from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool
from openai import OpenAI
import os
from backend.core.config import get_settings

settings = get_settings()

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

# Initialize tools
search_tool = SerperDevTool(api_key=settings.serper_api_key)
web_tool = WebsiteSearchTool()

# Research Sub-Agent
research_agent = Agent(
    role="Social Media Research Specialist",
    goal="Analyze daily trends and gather insights from social media and web sources",
    backstory="""You are an expert social media researcher with deep knowledge of 
    trending topics, audience behavior, and content performance. You excel at identifying 
    emerging trends and understanding what content resonates with different audiences.""",
    tools=[search_tool, web_tool],
    verbose=False,  # Reduce memory from logging
    allow_delegation=False,
    max_iter=2  # Reduce iterations to save memory
)

# Content Generation Sub-Agent
content_agent = Agent(
    role="Creative Content Generator",
    goal="Create engaging, brand-aligned social media content across multiple platforms",
    backstory="""You are a creative content strategist specializing in social media 
    marketing. You understand platform-specific best practices and can create compelling 
    content that drives engagement while maintaining brand consistency.""",
    tools=[],
    verbose=False,  # Reduce memory from logging
    allow_delegation=False,
    max_iter=2  # Reduce iterations to save memory
)

# Posting Sub-Agent
posting_agent = Agent(
    role="Social Media Posting Manager",
    goal="Schedule and publish content across social platforms with optimal timing",
    backstory="""You are a social media manager with expertise in platform APIs, 
    posting schedules, and cross-platform optimization. You ensure content reaches 
    the right audience at the right time.""",
    tools=[],
    verbose=False,  # Reduce memory from logging
    allow_delegation=False,
    max_iter=1  # Minimal iterations for posting
)

# Optimizer Sub-Agent
optimizer_agent = Agent(
    role="Performance Optimization Analyst",
    goal="Analyze content performance and provide data-driven optimization recommendations",
    backstory="""You are a data analyst specializing in social media metrics and 
    performance optimization. You excel at identifying patterns in engagement data 
    and providing actionable insights to improve content strategy.""",
    tools=[],
    verbose=False,  # Reduce memory from logging
    allow_delegation=False,
    max_iter=2  # Reduce iterations to save memory
)

def create_research_task(topic: str = "social media trends"):
    return Task(
        description=f"""Research current trends and insights related to {topic}. 
        Analyze social media discussions, news articles, and web content to identify:
        1. Emerging trends and topics gaining momentum
        2. Audience sentiment and engagement patterns  
        3. Key influencers and thought leaders discussing the topic
        4. Content formats performing well (text, images, videos)
        
        Provide a comprehensive research summary with actionable insights.""",
        agent=research_agent,
        expected_output="A detailed research report with trending topics, key insights, and content recommendations"
    )

def create_content_generation_task(research_context: str, brand_voice: str = "professional"):
    return Task(
        description=f"""Based on the research findings: {research_context}
        
        Create 3 pieces of social media content with the following requirements:
        1. Content should align with {brand_voice} brand voice
        2. Include platform-specific versions (Twitter, LinkedIn, Instagram)
        3. Incorporate trending topics and relevant hashtags
        4. Create engaging headlines and descriptions
        5. Suggest visual content ideas (images/graphics)
        
        Each piece should be original, engaging, and optimized for its target platform.""",
        agent=content_agent,
        expected_output="3 complete content pieces with platform-specific versions, headlines, and visual suggestions"
    )

def create_posting_task(content: str):
    return Task(
        description=f"""Schedule and prepare the following content for posting: {content}
        
        Tasks:
        1. Determine optimal posting times for each platform
        2. Format content appropriately for each platform's requirements
        3. Add relevant hashtags and mentions
        4. Schedule posts to maximize engagement
        5. Set up monitoring for post performance
        
        Provide a posting schedule and formatted content ready for publication.""",
        agent=posting_agent,
        expected_output="Complete posting schedule with formatted content for each platform"
    )

def create_optimization_task(performance_data: dict):
    return Task(
        description=f"""Analyze the following performance data: {performance_data}
        
        Provide optimization recommendations:
        1. Identify best and worst performing content
        2. Analyze engagement patterns and timing
        3. Suggest content format improvements
        4. Recommend hashtag and mention strategies
        5. Provide A/B testing suggestions
        
        Focus on actionable insights that can improve future content performance.""",
        agent=optimizer_agent,
        expected_output="Detailed performance analysis with specific optimization recommendations"
    )

def create_daily_crew(topic: str = "social media trends", brand_voice: str = "professional"):
    """Create a crew for daily content workflow"""
    
    # Create tasks - CrewAI automatically passes outputs between sequential tasks
    research_task = create_research_task(topic)
    
    # Content task will automatically receive research_task output as context
    content_task = create_content_generation_task("Use the research findings from the previous task as context.", brand_voice)
    
    # Posting task will automatically receive content_task output as context  
    posting_task = create_posting_task("Use the content generated from the previous task.")
    
    # Create crew with sequential processing - outputs flow automatically between tasks
    crew = Crew(
        agents=[research_agent, content_agent, posting_agent],
        tasks=[research_task, content_task, posting_task],
        process=Process.sequential,
        memory=False,  # Disable crew memory to reduce RAM usage
        verbose=0  # Disable verbose logging
    )
    
    return crew

def create_optimization_crew(performance_data: dict):
    """Create a crew for performance optimization"""
    
    optimization_task = create_optimization_task(performance_data)
    
    crew = Crew(
        agents=[optimizer_agent],
        tasks=[optimization_task],
        process=Process.sequential,
        memory=False,  # Disable crew memory to reduce RAM usage
        verbose=0  # Disable verbose logging
    )
    
    return crew