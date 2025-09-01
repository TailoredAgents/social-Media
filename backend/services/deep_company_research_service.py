"""
Deep Company Research Service for Lily AI

This service performs comprehensive company research using CrewAI agents,
web scraping, and multiple data sources to provide specific insights
that guide autonomous content creation.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re
from dataclasses import dataclass

try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import SerperDevTool, WebsiteSearchTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create mock classes if CrewAI not available
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
    
    class Task:
        def __init__(self, *args, **kwargs):
            pass
    
    class Crew:
        def __init__(self, *args, **kwargs):
            pass
        
        def kickoff(self):
            return "Mock CrewAI result"

from backend.core.config import get_settings
def log_api_error(endpoint: str, method: str, error: Exception, request_data: Optional[Dict] = None, user_id: Optional[int] = None):
    """Production-ready error logging with structured format"""
    logger = logging.getLogger(__name__)
    logger.error(
        f"Deep research API error",
        extra={
            "endpoint": endpoint,
            "method": method,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "request_data": request_data,
            "service": "deep_company_research",
            "crewai_available": CREWAI_AVAILABLE
        },
        exc_info=True
    )

try:
    from backend.services.web_research_service import web_research_service, CompanyWebData, WebSearchException
    WEB_RESEARCH_AVAILABLE = True
except ImportError:
    WEB_RESEARCH_AVAILABLE = False
    web_research_service = None
    class WebSearchException(Exception):
        def __init__(self, message: str, cute_lily_message: str):
            super().__init__(message)
            self.cute_lily_message = cute_lily_message

class DeepResearchException(Exception):
    """Exception raised when deep research fails completely"""
    def __init__(self, message: str, cute_lily_message: str):
        super().__init__(message)
        self.cute_lily_message = cute_lily_message

settings = get_settings()
logger = logging.getLogger(__name__)

@dataclass
class CompanyInsight:
    """Structured company insight for content creation"""
    category: str  # e.g., "recent_news", "company_culture", "market_position"
    insight: str
    specificity_level: str  # "high", "medium", "low"
    content_opportunity: str
    source: str
    confidence_score: float

@dataclass
class DeepCompanyProfile:
    """Comprehensive company research results"""
    company_name: str
    industry: str
    description: str
    target_audience: str
    key_topics: List[str]
    
    # Deep insights for content creation
    recent_news: List[CompanyInsight]
    company_culture: List[CompanyInsight]
    market_position: List[CompanyInsight]
    competitive_advantages: List[CompanyInsight]
    customer_pain_points: List[CompanyInsight]
    content_themes: List[CompanyInsight]
    social_presence: List[CompanyInsight]
    
    research_timestamp: datetime
    research_depth_score: float

class DeepCompanyResearchService:
    """
    Advanced company research service using CrewAI agents and multiple data sources
    to provide specific, actionable insights for autonomous content creation.
    """
    
    def __init__(self):
        self.search_tool = None
        self.web_tool = None
        self.research_agent = None
        self.content_strategist = None
        self.market_analyst = None
        
        if CREWAI_AVAILABLE and hasattr(settings, 'serper_api_key'):
            try:
                self._initialize_research_tools()
                self._initialize_research_agents()
            except Exception as e:
                logger.warning(f"CrewAI initialization failed: {e}")
                
    def _initialize_research_tools(self):
        """Initialize research tools"""
        try:
            if settings.serper_api_key:
                self.search_tool = SerperDevTool(api_key=settings.serper_api_key)
            self.web_tool = WebsiteSearchTool()
        except Exception as e:
            logger.warning(f"Tool initialization failed: {e}")
    
    def _initialize_research_agents(self):
        """Initialize specialized research agents"""
        try:
            # Deep Research Agent - Gathers comprehensive company data
            self.research_agent = Agent(
                role="Deep Company Intelligence Researcher",
                goal="Conduct comprehensive research on companies, gathering specific details about their business, culture, recent developments, and market position",
                backstory="""You are an elite business intelligence researcher with expertise in 
                corporate analysis, market research, and competitive intelligence. You excel at 
                finding specific, actionable insights that can be used for strategic content creation. 
                You dig deep beyond surface-level information to uncover unique angles and opportunities.""",
                tools=[self.search_tool, self.web_tool] if self.search_tool else [self.web_tool] if self.web_tool else [],
                verbose=True,
                allow_delegation=False,
                max_iter=5
            )
            
            # Content Strategy Agent - Analyzes research for content opportunities  
            self.content_strategist = Agent(
                role="Content Strategy Analyst",
                goal="Analyze company research to identify specific content creation opportunities, themes, and messaging strategies",
                backstory="""You are a strategic content analyst who specializes in transforming 
                business intelligence into actionable content strategies. You understand what makes 
                content engaging, shareable, and valuable to different audiences. You can identify 
                unique angles and content opportunities that others miss.""",
                tools=[],
                verbose=True,
                allow_delegation=False,
                max_iter=3
            )
            
            # Market Position Agent - Analyzes competitive landscape
            self.market_analyst = Agent(
                role="Market Position Analyst",
                goal="Analyze company's market position, competitive advantages, and industry trends to inform content strategy",
                backstory="""You are a market research expert who understands competitive landscapes, 
                industry trends, and market positioning. You can identify what makes a company unique 
                in their market and how they can leverage that uniqueness in their content strategy.""",
                tools=[self.search_tool] if self.search_tool else [],
                verbose=True,
                allow_delegation=False,
                max_iter=4
            )
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            
    async def research_company_deeply(self, company_name: str) -> DeepCompanyProfile:
        """
        Perform deep company research using real web data and AI analysis.
        
        Args:
            company_name: The company to research
            
        Returns:
            DeepCompanyProfile with comprehensive insights from real web data
        """
        logger.info(f"Starting deep research for: {company_name}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Perform real web research if available
            web_data = None
            if WEB_RESEARCH_AVAILABLE and web_research_service:
                logger.info(f"Performing real web research for: {company_name}")
                web_data = await web_research_service.research_company_web(company_name)
                logger.info(f"Web research completed with confidence: {web_data.confidence_score}")
            
            # Step 2: Use CrewAI for deep analysis (if available)
            crew_result = None
            if CREWAI_AVAILABLE and self.research_agent and web_data:
                try:
                    logger.info(f"Enhancing web data with AI analysis for: {company_name}")
                    # Create enhanced research tasks using web data
                    tasks = self._create_enhanced_research_tasks(company_name, web_data)
                    
                    crew = Crew(
                        agents=[self.research_agent, self.content_strategist, self.market_analyst],
                        tasks=tasks,
                        process=Process.sequential,
                        verbose=True
                    )
                    
                    crew_result = await asyncio.to_thread(crew.kickoff)
                    logger.info("AI analysis enhancement completed")
                except Exception as e:
                    logger.warning(f"AI analysis enhancement failed, using web data only: {e}")
            
            # Step 3: Process results into structured profile
            if web_data:
                profile = await self._process_web_research_results(company_name, web_data, crew_result, start_time)
                logger.info(f"Deep research completed for {company_name} with depth score: {profile.research_depth_score}")
                return profile
            else:
                # NO FALLBACK - Web research is required for accurate data
                raise DeepResearchException(
                    f"Web research service unavailable or failed for {company_name}",
                    f"Oopsie 🤭 That's not right, let me just write that down... I need my web research tools to give you accurate information about {company_name}, but they seem to be taking a little nap right now!"
                )
            
        except WebSearchException as e:
            # Handle web search specific errors with Lily's message
            log_api_error(
                endpoint="/deep-research",
                method="POST",
                error=e,
                request_data={"company_name": company_name},
                user_id=None
            )
            raise DeepResearchException(str(e), e.cute_lily_message)
            
        except Exception as e:
            # Log the error properly
            log_api_error(
                endpoint="/deep-research", 
                method="POST",
                error=e,
                request_data={"company_name": company_name},
                user_id=None
            )
            
            # Lily's cute error response
            cute_message = f"Oopsie 🤭 That's not right, let me just write that down... Something went a bit wonky while researching {company_name}. My research brain needs a tiny reboot!"
            
            raise DeepResearchException(
                f"Deep research failed for {company_name}: {str(e)}",
                cute_message
            )
    
    def _create_research_tasks(self, company_name: str) -> List[Task]:
        """Create comprehensive research tasks"""
        tasks = []
        
        # Task 1: Basic Company Intelligence
        basic_research_task = Task(
            description=f"""
            Conduct comprehensive research on {company_name}. Gather the following information:
            
            1. Company Overview:
               - Full company description and business model
               - Industry and market sector
               - Target audience and customer segments
               - Company size, founding date, headquarters
            
            2. Recent Developments (last 6 months):
               - Major news, announcements, product launches
               - Executive changes, partnerships, acquisitions
               - Financial performance and milestones
               - Awards, recognitions, or controversies
            
            3. Company Culture & Values:
               - Mission statement and core values
               - Company culture initiatives
               - Employee testimonials and workplace culture
               - Social responsibility and sustainability efforts
            
            Provide specific, detailed information with sources. Focus on unique aspects that could inform content strategy.
            """,
            agent=self.research_agent,
            expected_output="Detailed company intelligence report with specific facts, recent developments, and cultural insights"
        )
        
        # Task 2: Market Position & Competitive Analysis
        market_analysis_task = Task(
            description=f"""
            Analyze {company_name}'s market position and competitive landscape:
            
            1. Market Position:
               - Market share and ranking in their industry
               - Key competitive advantages and differentiators
               - Unique value propositions
               - Market challenges and opportunities
            
            2. Competitive Analysis:
               - Main competitors and how they compare
               - Industry trends affecting the company
               - Market gaps the company addresses
               - Future market predictions
            
            3. Customer Perspective:
               - Customer reviews and feedback patterns
               - Common customer pain points the company solves
               - Customer success stories and case studies
               - Brand perception and reputation
            
            Focus on specific, actionable insights that could inform content creation.
            """,
            agent=self.market_analyst,
            expected_output="Comprehensive market position analysis with specific competitive insights and customer perspectives"
        )
        
        # Task 3: Content Strategy Opportunities
        content_strategy_task = Task(
            description=f"""
            Based on the research about {company_name}, identify specific content creation opportunities:
            
            1. Content Themes:
               - Key topics the company should focus on
               - Unique angles and perspectives they can offer
               - Trending topics relevant to their industry
               - Educational content opportunities
            
            2. Content Opportunities:
               - Specific post ideas based on recent developments
               - Behind-the-scenes content possibilities
               - Thought leadership opportunities
               - User-generated content strategies
            
            3. Social Media Presence Analysis:
               - Current social media performance and gaps
               - Platform-specific opportunities
               - Engagement strategies that would work for their audience
               - Content formats that would resonate
            
            4. Messaging Strategy:
               - Key messages that align with company values
               - Tone and voice recommendations
               - Hashtag strategies
               - Call-to-action opportunities
            
            Provide specific, actionable recommendations for autonomous content creation.
            """,
            agent=self.content_strategist,
            expected_output="Detailed content strategy with specific themes, post ideas, and messaging recommendations"
        )
        
        tasks.extend([basic_research_task, market_analysis_task, content_strategy_task])
        return tasks
    
    async def _process_research_results(self, company_name: str, crew_result: Any, start_time: datetime) -> DeepCompanyProfile:
        """Process CrewAI research results into structured profile"""
        try:
            # Extract insights from crew result
            research_text = str(crew_result)
            
            # Parse different types of insights using AI or regex patterns
            insights = await self._extract_insights_from_text(research_text)
            
            # Determine industry and basic info
            industry = await self._extract_industry(research_text)
            description = await self._extract_description(research_text)
            target_audience = await self._extract_target_audience(research_text)
            key_topics = await self._extract_key_topics(research_text)
            
            # Calculate research depth score based on insight quality and quantity
            depth_score = self._calculate_depth_score(insights)
            
            profile = DeepCompanyProfile(
                company_name=company_name,
                industry=industry,
                description=description,
                target_audience=target_audience,
                key_topics=key_topics,
                recent_news=insights.get('recent_news', []),
                company_culture=insights.get('company_culture', []),
                market_position=insights.get('market_position', []),
                competitive_advantages=insights.get('competitive_advantages', []),
                customer_pain_points=insights.get('customer_pain_points', []),
                content_themes=insights.get('content_themes', []),
                social_presence=insights.get('social_presence', []),
                research_timestamp=start_time,
                research_depth_score=depth_score
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to process research results: {e}")
            # NO FALLBACK - Raise the error properly
            raise Exception(f"Failed to process research results for {company_name}: {str(e)}")
    
    async def _extract_insights_from_text(self, research_text: str) -> Dict[str, List[CompanyInsight]]:
        """Extract structured insights from research text"""
        insights = {
            'recent_news': [],
            'company_culture': [],
            'market_position': [],
            'competitive_advantages': [],
            'customer_pain_points': [],
            'content_themes': [],
            'social_presence': []
        }
        
        # Use patterns to extract different types of insights
        # This is a simplified version - in production, you'd use more sophisticated NLP
        
        lines = research_text.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify content categories
            if any(keyword in line.lower() for keyword in ['recent', 'news', 'announcement', 'launched']):
                current_category = 'recent_news'
            elif any(keyword in line.lower() for keyword in ['culture', 'values', 'mission', 'workplace']):
                current_category = 'company_culture'
            elif any(keyword in line.lower() for keyword in ['market', 'position', 'competitive', 'advantage']):
                current_category = 'market_position'
            elif any(keyword in line.lower() for keyword in ['content', 'social media', 'post', 'theme']):
                current_category = 'content_themes'
            
            if current_category and line.startswith('- ') or line.startswith('• '):
                insight_text = line[2:].strip()
                if insight_text:
                    insight = CompanyInsight(
                        category=current_category,
                        insight=insight_text,
                        specificity_level="high" if len(insight_text) > 50 else "medium",
                        content_opportunity=f"Create content around: {insight_text[:100]}...",
                        source="CrewAI Research",
                        confidence_score=0.8
                    )
                    insights[current_category].append(insight)
        
        return insights
    
    async def _extract_industry(self, research_text: str) -> str:
        """Extract industry from research text"""
        # Simple pattern matching - in production use more sophisticated extraction
        industry_keywords = {
            'technology': ['software', 'tech', 'AI', 'cloud', 'SaaS'],
            'automotive': ['car', 'vehicle', 'automotive', 'transportation'],
            'finance': ['bank', 'financial', 'fintech', 'investment'],
            'healthcare': ['health', 'medical', 'pharmaceutical', 'biotech'],
            'retail': ['retail', 'ecommerce', 'shopping', 'marketplace']
        }
        
        text_lower = research_text.lower()
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry.title()
        
        return "Technology"  # Default fallback
    
    async def _extract_description(self, research_text: str) -> str:
        """Extract company description from research text"""
        # Look for description patterns
        lines = research_text.split('\n')
        for line in lines:
            if 'description' in line.lower() or 'company' in line.lower():
                if len(line) > 50:  # Substantial description
                    return line.strip()
        
        # Fallback to first substantial line
        for line in lines:
            if len(line) > 100:
                return line.strip()
        
        return f"Research-based comprehensive analysis of the company reveals detailed business insights."
    
    async def _extract_target_audience(self, research_text: str) -> str:
        """Extract target audience from research text"""
        # Look for audience-related content
        audience_keywords = ['audience', 'customer', 'target', 'demographic', 'segment']
        lines = research_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in audience_keywords):
                if len(line) > 30:
                    return line.strip()
        
        return "Professionals, businesses, and individuals interested in innovative solutions and industry insights"
    
    async def _extract_key_topics(self, research_text: str) -> List[str]:
        """Extract key topics from research text"""
        # Extract important keywords and topics
        topics = set()
        
        # Common business topics that might appear
        potential_topics = [
            'innovation', 'technology', 'growth', 'leadership', 'strategy',
            'customer success', 'digital transformation', 'sustainability',
            'market trends', 'competitive advantage', 'brand awareness'
        ]
        
        text_lower = research_text.lower()
        for topic in potential_topics:
            if topic in text_lower:
                topics.add(topic)
        
        # Add some research-derived topics
        topics.update(['industry insights', 'business intelligence', 'market analysis'])
        
        return list(topics)[:10]  # Limit to top 10 topics
    
    def _calculate_depth_score(self, insights: Dict[str, List[CompanyInsight]]) -> float:
        """Calculate research depth score based on insight quality and quantity"""
        total_insights = sum(len(category_insights) for category_insights in insights.values())
        
        if total_insights == 0:
            return 0.3  # Minimum score
        
        # Score based on insight distribution and quality
        category_coverage = len([cat for cat, insights_list in insights.items() if insights_list])
        coverage_score = category_coverage / 7.0  # 7 total categories
        
        # Quality score based on specificity
        quality_scores = []
        for category_insights in insights.values():
            for insight in category_insights:
                if insight.specificity_level == "high":
                    quality_scores.append(1.0)
                elif insight.specificity_level == "medium":
                    quality_scores.append(0.7)
                else:
                    quality_scores.append(0.4)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        
        # Quantity score (with diminishing returns)
        quantity_score = min(total_insights / 20.0, 1.0)
        
        # Weighted final score
        final_score = (coverage_score * 0.4 + avg_quality * 0.4 + quantity_score * 0.2)
        
        return round(min(final_score, 1.0), 2)
    
    def _create_enhanced_research_tasks(self, company_name: str, web_data: 'CompanyWebData') -> List[Task]:
        """Create research tasks enhanced with real web data"""
        if not CREWAI_AVAILABLE:
            return []
            
        tasks = []
        
        # Enhanced analysis task using real web data
        web_analysis_task = Task(
            description=f"""
            Analyze the following real web data about {company_name} and provide deeper insights:
            
            Company: {company_name}
            Industry: {web_data.industry}
            Description: {web_data.description}
            Website: {web_data.website_url}
            Founded: {web_data.founded}
            Headquarters: {web_data.headquarters}
            
            Recent News Headlines:
            {chr(10).join([f"- {news.title}: {news.snippet}" for news in web_data.recent_news[:3]])}
            
            Based on this real data, provide:
            1. Detailed analysis of market positioning and competitive advantages
            2. Specific content opportunities based on recent developments
            3. Industry trends that affect this company
            4. Recommendations for social media strategy
            
            Focus on specific, actionable insights that go beyond the basic web data.
            """,
            agent=self.research_agent,
            expected_output="Deep analysis report with specific insights based on real company data"
        )
        
        tasks.append(web_analysis_task)
        return tasks
    
    async def _process_web_research_results(self, company_name: str, web_data: 'CompanyWebData', crew_result: Any, start_time: datetime) -> DeepCompanyProfile:
        """Process real web research results into structured profile"""
        try:
            # Extract insights from web data
            insights = await self._extract_insights_from_web_data(web_data)
            
            # Enhance with AI analysis if available
            if crew_result:
                ai_insights = await self._extract_insights_from_text(str(crew_result))
                # Merge AI insights with web insights
                for category in insights:
                    if category in ai_insights:
                        insights[category].extend(ai_insights[category])
            
            # Use web data for basic info, enhanced with intelligent analysis
            industry = web_data.industry or "Technology & Innovation"
            description = web_data.description or f"{company_name} is a company in the {industry} sector."
            target_audience = await self._derive_target_audience_from_industry(industry)
            key_topics = await self._derive_key_topics_from_web_data(web_data)
            
            # Calculate enhanced depth score
            depth_score = max(web_data.confidence_score, self._calculate_depth_score(insights))
            
            profile = DeepCompanyProfile(
                company_name=company_name,
                industry=industry,
                description=description,
                target_audience=target_audience,
                key_topics=key_topics,
                recent_news=insights.get('recent_news', []),
                company_culture=insights.get('company_culture', []),
                market_position=insights.get('market_position', []),
                competitive_advantages=insights.get('competitive_advantages', []),
                customer_pain_points=insights.get('customer_pain_points', []),
                content_themes=insights.get('content_themes', []),
                social_presence=insights.get('social_presence', []),
                research_timestamp=start_time,
                research_depth_score=depth_score
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to process web research results: {e}")
            # NO FALLBACK - Raise the error properly
            raise Exception(f"Failed to process web research results for {company_name}: {str(e)}")
    
    async def _extract_insights_from_web_data(self, web_data: 'CompanyWebData') -> Dict[str, List[CompanyInsight]]:
        """Extract structured insights from real web data"""
        insights = {
            'recent_news': [],
            'company_culture': [],
            'market_position': [],
            'competitive_advantages': [],
            'customer_pain_points': [],
            'content_themes': [],
            'social_presence': []
        }
        
        # Process recent news
        for news in web_data.recent_news[:3]:
            insights['recent_news'].append(CompanyInsight(
                category='recent_news',
                insight=f"{news.title}: {news.snippet}",
                specificity_level='high',
                content_opportunity=f"Create content around: {news.title} - share insights and analysis",
                source='Real Web Research',
                confidence_score=web_data.confidence_score
            ))
        
        # Generate market position insights from web data
        if web_data.industry:
            insights['market_position'].append(CompanyInsight(
                category='market_position',
                insight=f"{web_data.company_name} operates in {web_data.industry} with established market presence",
                specificity_level='high',
                content_opportunity=f"Develop industry leadership content for {web_data.industry}",
                source='Real Web Research',
                confidence_score=web_data.confidence_score
            ))
        
        # Generate competitive advantages from company details
        if web_data.founded:
            insights['competitive_advantages'].append(CompanyInsight(
                category='competitive_advantages',
                insight=f"Established company with experience since {web_data.founded}, bringing market maturity and expertise",
                specificity_level='medium',
                content_opportunity="Create content highlighting company experience and market knowledge",
                source='Real Web Research',
                confidence_score=web_data.confidence_score
            ))
        
        # Generate content themes based on industry and web presence
        industry_themes = await self._get_industry_content_themes(web_data.industry)
        for theme in industry_themes[:3]:
            insights['content_themes'].append(CompanyInsight(
                category='content_themes',
                insight=f"Content theme: {theme} - highly relevant for {web_data.industry}",
                specificity_level='high',
                content_opportunity=f"Develop content series around {theme}",
                source='Real Web Research',
                confidence_score=0.85
            ))
        
        return insights
    
    async def _derive_target_audience_from_industry(self, industry: str) -> str:
        """Derive target audience based on industry"""
        audience_mapping = {
            'Software Development': 'Developers, IT professionals, and technology decision-makers',
            'SaaS & Cloud Computing': 'Business leaders, IT managers, and enterprise customers',
            'Artificial Intelligence & ML': 'Data scientists, researchers, and AI-focused businesses',
            'E-commerce': 'Online consumers, retailers, and e-commerce professionals',
            'Healthcare': 'Healthcare professionals, patients, and medical institutions',
            'Finance': 'Financial professionals, investors, and business owners',
            'Marketing & Advertising': 'Marketing professionals, business owners, and brand managers',
            'Real Estate': 'Property buyers, investors, and real estate professionals',
            'Food & Beverage': 'Consumers, food service professionals, and hospitality industry',
            'Education': 'Educators, students, and educational institutions',
        }
        
        return audience_mapping.get(industry, 'Business professionals and industry stakeholders')
    
    async def _derive_key_topics_from_web_data(self, web_data: 'CompanyWebData') -> List[str]:
        """Derive key topics from web research data"""
        topics = []
        
        # Extract topics from industry
        if web_data.industry:
            industry_topics = await self._get_industry_content_themes(web_data.industry)
            topics.extend(industry_topics[:5])
        
        # Extract topics from company description and news
        text_content = web_data.description + " " + " ".join([news.snippet for news in web_data.recent_news])
        
        # Simple keyword extraction (in production, use more sophisticated NLP)
        keywords = ['innovation', 'technology', 'growth', 'customer success', 'market leadership', 
                   'digital transformation', 'industry insights', 'business strategy', 'solutions']
        
        for keyword in keywords:
            if keyword.lower() in text_content.lower() and keyword not in topics:
                topics.append(keyword)
        
        return topics[:8]  # Limit to 8 topics
    
    async def _get_industry_content_themes(self, industry: str) -> List[str]:
        """Get content themes specific to industry"""
        theme_mapping = {
            'Software Development': ['coding best practices', 'software architecture', 'development tools', 'programming languages'],
            'SaaS & Cloud Computing': ['cloud migration', 'SaaS metrics', 'scalability', 'API integration'],
            'Artificial Intelligence & ML': ['machine learning models', 'AI ethics', 'data science', 'automation'],
            'E-commerce': ['online shopping trends', 'customer experience', 'conversion optimization', 'digital payments'],
            'Healthcare': ['patient care', 'medical technology', 'healthcare innovation', 'wellness'],
            'Finance': ['financial planning', 'investment strategies', 'fintech innovation', 'regulatory compliance'],
            'Marketing & Advertising': ['digital marketing', 'brand strategy', 'customer acquisition', 'analytics'],
            'Real Estate': ['property investment', 'market trends', 'real estate technology', 'property management'],
            'Food & Beverage': ['culinary trends', 'food safety', 'restaurant management', 'sustainable food'],
            'Education': ['educational technology', 'learning methods', 'student success', 'curriculum development'],
        }
        
        return theme_mapping.get(industry, ['industry innovation', 'business growth', 'customer success', 'market insights'])
    
    

# Global service instance
deep_company_research_service = DeepCompanyResearchService()