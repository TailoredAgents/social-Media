"""
Autonomous Deep Research Agent - GPT-5 Powered
Industry Intelligence & Knowledge Base Management System

This agent autonomously researches industries, maintains knowledge bases,
and provides continuous intelligence for social media content creation.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import time

from openai import OpenAI
from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

try:
    from backend.services.embedding_service import EmbeddingService
    from backend.core.vector_store import VectorStore
except ImportError:
    # Fallback to mock services when FAISS is not available
    logger.warning("FAISS not available, using mock services for development")
    from backend.services.embedding_service_mock import EmbeddingServiceMock as EmbeddingService
    from backend.core.vector_store_mock import VectorStoreMock as VectorStore

from backend.agents.tools import web_scraper, openai_tool

@dataclass
class ResearchTopic:
    """Research topic definition"""
    name: str
    keywords: List[str]
    priority: int  # 1-10 scale
    last_researched: Optional[datetime] = None
    research_depth: str = "comprehensive"  # basic, standard, comprehensive, deep
    sources: List[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []

@dataclass
class ResearchFinding:
    """Individual research finding"""
    id: str
    topic: str
    title: str
    content: str
    source_url: str
    source_type: str  # article, report, news, social, academic
    relevance_score: float
    credibility_score: float
    publish_date: datetime
    discovered_at: datetime
    keywords: List[str]
    summary: str
    insights: List[str]
    implications: List[str]
    trending_indicators: Dict[str, Any]

@dataclass
class IndustryIntelligence:
    """Comprehensive industry intelligence report"""
    industry: str
    generated_at: datetime
    research_period: Tuple[datetime, datetime]
    key_trends: List[Dict[str, Any]]
    market_developments: List[Dict[str, Any]]
    competitive_landscape: Dict[str, Any]
    emerging_technologies: List[Dict[str, Any]]
    regulatory_changes: List[Dict[str, Any]]
    consumer_behavior_shifts: List[Dict[str, Any]]
    content_opportunities: List[Dict[str, Any]]
    risk_factors: List[Dict[str, Any]]
    confidence_score: float
    source_quality_metrics: Dict[str, Any]

class DeepResearchAgent:
    """
    Autonomous Deep Research Agent powered by GPT-5 and GPT-5 mini
    
    Features:
    - Continuous industry monitoring
    - Multi-source intelligence gathering
    - AI-powered content analysis and synthesis
    - Knowledge base management
    - Trend prediction and opportunity identification
    - Automated research scheduling
    """
    
    def __init__(self):
        """Initialize the Deep Research Agent"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        # Model selection based on task type
        self.routine_research_model = "gpt-5-mini"  # For hourly/daily research
        self.deep_research_model = "gpt-5-mini"  # For weekly deep dives (with Serper)
        self.analysis_model = "gpt-5-mini"  # For comprehensive analysis (with Serper)
        
        # Research configuration
        self.max_sources_per_topic = 50
        self.min_relevance_threshold = 0.7
        self.research_depth_configs = {
            "basic": {"sources": 10, "analysis_depth": "surface"},
            "standard": {"sources": 25, "analysis_depth": "moderate"},
            "comprehensive": {"sources": 50, "analysis_depth": "deep"},
            "deep": {"sources": 100, "analysis_depth": "exhaustive"}
        }
        
        # Knowledge base paths
        self.knowledge_base_path = Path("data/knowledge_base")
        self.research_cache_path = Path("data/research_cache")
        self.intelligence_reports_path = Path("data/intelligence_reports")
        
        # Create directories
        for path in [self.knowledge_base_path, self.research_cache_path, self.intelligence_reports_path]:
            path.mkdir(parents=True, exist_ok=True)
            
        logger.info("Deep Research Agent initialized with GPT-5 and GPT-5 mini")
    
    async def initialize_research_topics(self, industry: str, business_context: Dict[str, Any]) -> List[ResearchTopic]:
        """
        Initialize research topics based on industry and business context
        
        Args:
            industry: Target industry (e.g., "fintech", "healthcare", "e-commerce")
            business_context: Business-specific context and goals
            
        Returns:
            List of research topics to monitor
        """
        prompt = f"""
        As an expert research strategist, define comprehensive research topics for continuous monitoring in the {industry} industry.
        
        Business Context:
        {json.dumps(business_context, indent=2)}
        
        Create research topics that cover:
        1. Core industry trends and developments
        2. Competitive landscape changes
        3. Regulatory and compliance updates
        4. Technology innovations and disruptions
        5. Consumer behavior and market shifts
        6. Economic factors and market conditions
        7. Emerging opportunities and threats
        8. Content marketing trends specific to this industry
        
        For each topic, provide:
        - Descriptive name
        - 5-10 relevant keywords
        - Priority score (1-10)
        - Recommended research depth
        - Key sources to monitor
        
        Return as JSON array with this structure:
        {{
            "name": "Topic Name",
            "keywords": ["keyword1", "keyword2", ...],
            "priority": 8,
            "research_depth": "comprehensive",
            "sources": ["source_type1", "source_type2", ...]
        }}
        """
        
        try:
            response = await self._call_gpt5_mini_with_search(prompt, use_web_search=True)
            topics_data = json.loads(response)
            
            topics = []
            for topic_data in topics_data:
                topic = ResearchTopic(
                    name=topic_data["name"],
                    keywords=topic_data["keywords"],
                    priority=topic_data["priority"],
                    research_depth=topic_data.get("research_depth", "comprehensive"),
                    sources=topic_data.get("sources", [])
                )
                topics.append(topic)
            
            logger.info(f"Initialized {len(topics)} research topics for {industry}")
            return topics
            
        except Exception as e:
            logger.error(f"Failed to initialize research topics: {e}")
            return self._get_default_research_topics(industry)
    
    async def conduct_weekly_research(self, industry: str, topics: List[ResearchTopic]) -> IndustryIntelligence:
        """
        Conduct comprehensive weekly research across all topics
        
        Args:
            industry: Target industry
            topics: Research topics to investigate
            
        Returns:
            Comprehensive industry intelligence report
        """
        logger.info(f"Starting weekly research for {industry} industry")
        start_time = datetime.utcnow()
        research_period = (start_time - timedelta(days=7), start_time)
        
        all_findings = []
        
        # Research each topic
        for topic in topics:
            try:
                logger.info(f"Researching topic: {topic.name}")
                findings = await self._research_topic(topic)
                all_findings.extend(findings)
                
                # Update last researched timestamp
                topic.last_researched = start_time
                
                # Brief pause to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to research topic {topic.name}: {e}")
                continue
        
        # Analyze and synthesize findings
        intelligence_report = await self._synthesize_intelligence(
            industry, all_findings, research_period
        )
        
        # Store in knowledge base
        await self._store_intelligence_report(intelligence_report)
        await self._update_knowledge_base(all_findings)
        
        # Generate actionable insights
        await self._generate_content_opportunities(intelligence_report)
        
        logger.info(f"Weekly research completed. Found {len(all_findings)} insights.")
        return intelligence_report
    
    async def _research_topic(self, topic: ResearchTopic) -> List[ResearchFinding]:
        """Research a specific topic comprehensively using GPT-5's built-in web search"""
        try:
            # Use GPT-5's built-in web search for streamlined research
            if topic.research_depth == "deep":
                findings = await self._research_topic_deep(topic)
            else:
                findings = await self._research_topic_standard(topic)
            
            return findings[:self.max_sources_per_topic]
            
        except Exception as e:
            logger.error(f"GPT-5 research failed for topic {topic.name}: {e}")
            # Fallback to traditional research method
            return await self._research_topic_fallback(topic)
    
    async def _generate_search_queries(self, topic: ResearchTopic) -> List[str]:
        """Generate diverse search queries for comprehensive topic coverage"""
        prompt = f"""
        Generate 15-20 diverse, specific search queries to comprehensively research this topic:
        
        Topic: {topic.name}
        Keywords: {', '.join(topic.keywords)}
        Priority: {topic.priority}/10
        
        Create queries that cover:
        1. Recent developments and news
        2. Market trends and statistics
        3. Expert opinions and analysis
        4. Case studies and examples
        5. Future predictions and forecasts
        6. Regulatory and policy changes
        7. Technology and innovation aspects
        8. Consumer behavior insights
        
        Make queries specific, current, and likely to return high-quality results.
        Include date constraints like "2024" or "recent" where appropriate.
        
        Return as JSON array of strings.
        """
        
        try:
            # Use GPT-5 mini to generate search queries - it can also do initial research
            response = await self._call_gpt5_mini_with_search(prompt, use_web_search=False)
            queries = json.loads(response)
            return queries
        except Exception as e:
            logger.error(f"Failed to generate search queries: {e}")
            return [f"{topic.name} {kw}" for kw in topic.keywords[:10]]
    
    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using multiple sources"""
        results = []
        
        try:
            # Use Serper API if available
            if settings.serper_api_key and settings.serper_api_key != "your_serper_api_key_here":
                serper_results = await self._search_serper(query)
                results.extend(serper_results)
            else:
                # Fallback to basic web scraping
                basic_results = await self._basic_web_search(query)
                results.extend(basic_results)
                
        except Exception as e:
            logger.warning(f"Web search failed for query '{query}': {e}")
        
        return results
    
    async def _search_serper(self, query: str) -> List[Dict[str, Any]]:
        """Search using Serper API"""
        url = "https://google.serper.dev/search"
        
        payload = {
            "q": query,
            "num": 10,
            "hl": "en",
            "gl": "us"
        }
        
        headers = {
            "X-API-KEY": settings.serper_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "serper"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []
    
    async def _basic_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Basic web search using predefined sources"""
        # This is a simplified implementation
        # In production, you might integrate with other search APIs
        search_urls = [
            f"https://news.google.com/search?q={query.replace(' ', '%20')}",
            f"https://www.reddit.com/search/?q={query.replace(' ', '%20')}",
        ]
        
        results = []
        for url in search_urls:
            try:
                # Basic scraping (implement proper scraping logic)
                results.append({
                    "title": f"Search result for {query}",
                    "url": url,
                    "snippet": f"Search results for {query}",
                    "source": "basic"
                })
            except Exception as e:
                logger.warning(f"Basic search failed for {url}: {e}")
                continue
        
        return results
    
    async def _process_search_result(self, result: Dict[str, Any], topic: ResearchTopic) -> Optional[ResearchFinding]:
        """Process and analyze a search result"""
        try:
            # Scrape content
            scraped_data = web_scraper.scrape_url(result["url"])
            
            if scraped_data["status"] != "success":
                return None
            
            content = scraped_data["content"]
            
            # AI-powered analysis
            analysis = await self._analyze_content(content, topic, result)
            
            if not analysis:
                return None
            
            # Create finding
            finding_id = hashlib.md5(f"{result['url']}{topic.name}{datetime.utcnow()}".encode()).hexdigest()
            
            finding = ResearchFinding(
                id=finding_id,
                topic=topic.name,
                title=result.get("title", ""),
                content=content[:2000],  # Limit content size
                source_url=result["url"],
                source_type=analysis["source_type"],
                relevance_score=analysis["relevance_score"],
                credibility_score=analysis["credibility_score"],
                publish_date=analysis.get("publish_date", datetime.utcnow()),
                discovered_at=datetime.utcnow(),
                keywords=analysis["keywords"],
                summary=analysis["summary"],
                insights=analysis["insights"],
                implications=analysis["implications"],
                trending_indicators=analysis["trending_indicators"]
            )
            
            return finding
            
        except Exception as e:
            logger.warning(f"Failed to process search result {result.get('url', 'unknown')}: {e}")
            return None
    
    async def _analyze_content(self, content: str, topic: ResearchTopic, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI-powered content analysis using GPT-5 Mini"""
        prompt = f"""
        Analyze this content for relevance to the research topic and extract key insights.
        
        Research Topic: {topic.name}
        Keywords: {', '.join(topic.keywords)}
        Source: {result.get('title', 'Unknown')}
        
        Content:
        {content[:3000]}
        
        Provide analysis in JSON format:
        {{
            "relevance_score": 0.85,  // 0-1 scale
            "credibility_score": 0.90,  // 0-1 scale based on source quality
            "source_type": "news",  // news, academic, blog, report, social
            "publish_date": "2024-01-15",  // estimated if not clear
            "keywords": ["keyword1", "keyword2"],  // extracted relevant keywords
            "summary": "Brief summary of key points",
            "insights": ["insight 1", "insight 2"],  // key insights extracted
            "implications": ["implication 1", "implication 2"],  // business implications
            "trending_indicators": {{
                "urgency": "high",  // low, medium, high
                "impact_potential": "significant",  // minimal, moderate, significant, transformative
                "time_sensitivity": "immediate"  // immediate, short-term, long-term
            }}
        }}
        
        Only return JSON, no other text.
        """
        
        try:
            response = await self._call_gpt5_mini_with_search(prompt, use_web_search=True)
            analysis = json.loads(response)
            return analysis
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return None
    
    async def _analyze_and_rank_findings(self, findings: List[ResearchFinding], topic: ResearchTopic) -> List[ResearchFinding]:
        """Analyze and rank findings by importance and relevance"""
        if not findings:
            return findings
        
        # Sort by combined score (relevance * credibility * recency)
        def calculate_score(finding: ResearchFinding) -> float:
            recency_factor = 1.0
            days_old = (datetime.utcnow() - finding.discovered_at).days
            if days_old > 0:
                recency_factor = max(0.1, 1.0 - (days_old * 0.05))  # Decay over time
            
            return finding.relevance_score * finding.credibility_score * recency_factor
        
        findings.sort(key=calculate_score, reverse=True)
        return findings
    
    async def _synthesize_intelligence(self, industry: str, findings: List[ResearchFinding], research_period: Tuple[datetime, datetime]) -> IndustryIntelligence:
        """Synthesize all findings into comprehensive industry intelligence"""
        prompt = f"""
        Synthesize comprehensive industry intelligence from research findings.
        
        Industry: {industry}
        Research Period: {research_period[0].strftime('%Y-%m-%d')} to {research_period[1].strftime('%Y-%m-%d')}
        Total Findings: {len(findings)}
        
        Key Findings Summary:
        {self._format_findings_for_analysis(findings[:20])}
        
        Create comprehensive intelligence report in JSON format:
        {{
            "key_trends": [
                {{
                    "name": "Trend Name",
                    "description": "Detailed description",
                    "impact_level": "high",  // low, medium, high
                    "confidence": 0.85,
                    "supporting_evidence": ["evidence 1", "evidence 2"],
                    "timeline": "short-term"  // immediate, short-term, medium-term, long-term
                }}
            ],
            "market_developments": [
                {{
                    "category": "Product Innovation",
                    "description": "Development description",
                    "impact": "Market disruption potential",
                    "key_players": ["Company A", "Company B"],
                    "implications": ["implication 1", "implication 2"]
                }}
            ],
            "competitive_landscape": {{
                "market_leaders": ["Company A", "Company B"],
                "emerging_players": ["Startup A", "Startup B"],
                "competitive_dynamics": "Description of current dynamics",
                "market_consolidation": "Assessment of consolidation trends"
            }},
            "emerging_technologies": [
                {{
                    "technology": "AI/ML Integration",
                    "adoption_stage": "early majority",
                    "disruption_potential": "high",
                    "implementation_timeline": "6-12 months",
                    "key_applications": ["application 1", "application 2"]
                }}
            ],
            "regulatory_changes": [
                {{
                    "regulation": "New Data Privacy Law",
                    "status": "proposed",
                    "impact_assessment": "significant",
                    "compliance_requirements": ["requirement 1", "requirement 2"],
                    "implementation_date": "2024-06-01"
                }}
            ],
            "consumer_behavior_shifts": [
                {{
                    "shift": "Increased Digital Adoption",
                    "magnitude": "significant",
                    "demographics_affected": ["millennials", "gen-z"],
                    "business_implications": ["implication 1", "implication 2"],
                    "adaptation_strategies": ["strategy 1", "strategy 2"]
                }}
            ],
            "content_opportunities": [
                {{
                    "opportunity": "Educational Content on New Regulations",
                    "content_types": ["blog posts", "infographics", "webinars"],
                    "target_audience": "business decision makers",
                    "urgency": "high",
                    "competitive_advantage": "first-mover advantage"
                }}
            ],
            "risk_factors": [
                {{
                    "risk": "Economic Downturn Impact",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation_strategies": ["strategy 1", "strategy 2"],
                    "monitoring_indicators": ["indicator 1", "indicator 2"]
                }}
            ],
            "confidence_score": 0.85,
            "source_quality_metrics": {{
                "high_credibility_sources": 15,
                "medium_credibility_sources": 8,
                "low_credibility_sources": 2,
                "average_recency_days": 3.2
            }}
        }}
        """
        
        try:
            # Use GPT-5 with enhanced reasoning for comprehensive weekly intelligence synthesis
            response = await self._call_gpt5_deep_research(prompt)
            intelligence_data = json.loads(response)
            
            intelligence = IndustryIntelligence(
                industry=industry,
                generated_at=datetime.utcnow(),
                research_period=research_period,
                key_trends=intelligence_data["key_trends"],
                market_developments=intelligence_data["market_developments"],
                competitive_landscape=intelligence_data["competitive_landscape"],
                emerging_technologies=intelligence_data["emerging_technologies"],
                regulatory_changes=intelligence_data["regulatory_changes"],
                consumer_behavior_shifts=intelligence_data["consumer_behavior_shifts"],
                content_opportunities=intelligence_data["content_opportunities"],
                risk_factors=intelligence_data["risk_factors"],
                confidence_score=intelligence_data["confidence_score"],
                source_quality_metrics=intelligence_data["source_quality_metrics"]
            )
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Intelligence synthesis failed: {e}")
            # Return basic intelligence structure
            return self._create_basic_intelligence(industry, findings, research_period)
    
    def _format_findings_for_analysis(self, findings: List[ResearchFinding]) -> str:
        """Format findings for AI analysis"""
        formatted = []
        for finding in findings:
            formatted.append(f"""
            Title: {finding.title}
            Topic: {finding.topic}
            Summary: {finding.summary}
            Insights: {'; '.join(finding.insights)}
            Relevance: {finding.relevance_score:.2f}
            Credibility: {finding.credibility_score:.2f}
            """)
        return '\n---\n'.join(formatted)
    
    async def _store_intelligence_report(self, intelligence: IndustryIntelligence):
        """Store intelligence report in knowledge base"""
        try:
            filename = f"{intelligence.industry}_{intelligence.generated_at.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.intelligence_reports_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(intelligence), f, indent=2, default=str)
            
            logger.info(f"Intelligence report stored: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to store intelligence report: {e}")
    
    async def _update_knowledge_base(self, findings: List[ResearchFinding]):
        """Update vector knowledge base with new findings"""
        try:
            for finding in findings:
                # Create embedding
                embedding_text = f"{finding.title}\n{finding.summary}\n{'; '.join(finding.insights)}"
                embedding = await self.embedding_service.create_embedding(embedding_text)
                
                # Store in vector database
                metadata = {
                    "id": finding.id,
                    "topic": finding.topic,
                    "source_url": finding.source_url,
                    "relevance_score": finding.relevance_score,
                    "credibility_score": finding.credibility_score,
                    "discovered_at": finding.discovered_at.isoformat(),
                    "keywords": finding.keywords
                }
                
                await self.vector_store.add_document(
                    document_id=finding.id,
                    content=embedding_text,
                    embedding=embedding,
                    metadata=metadata
                )
            
            logger.info(f"Updated knowledge base with {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}")
    
    async def _generate_content_opportunities(self, intelligence: IndustryIntelligence):
        """Generate specific content opportunities based on intelligence"""
        try:
            # This could trigger content planning workflows
            opportunities_file = self.knowledge_base_path / f"content_opportunities_{intelligence.industry}_{datetime.utcnow().strftime('%Y%m%d')}.json"
            
            with open(opportunities_file, 'w') as f:
                json.dump({
                    "industry": intelligence.industry,
                    "generated_at": datetime.utcnow().isoformat(),
                    "opportunities": intelligence.content_opportunities,
                    "trends_to_leverage": intelligence.key_trends[:5],
                    "urgent_topics": [
                        opp for opp in intelligence.content_opportunities 
                        if opp.get("urgency") == "high"
                    ]
                }, f, indent=2)
            
            logger.info(f"Content opportunities generated: {opportunities_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate content opportunities: {e}")
    
    async def _call_gpt5_mini_with_search(self, prompt: str, temperature: float = 0.7, use_web_search: bool = True) -> str:
        """Call GPT-5 mini with web search via Responses API for research"""
        try:
            if use_web_search:
                # Use Responses API with web search
                response = self.client.responses.create(
                    model=self.routine_research_model,
                    input=f"You are an expert research analyst. Use web search to provide current, thorough research on: {prompt}",
                    tools=[
                        {
                            "type": "web_search"
                        }
                    ]
                )
                return response.output_text if hasattr(response, 'output_text') else str(response)
            else:
                # Fallback to Chat Completions without web search
                response = self.client.chat.completions.create(
                    model=self.routine_research_model,
                    messages=[
                        {"role": "system", "content": "You are an expert research analyst and industry intelligence specialist. Provide thorough, accurate, and actionable insights based on your knowledge."},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=4000
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"GPT-5 mini call failed: {e}")
            # Fallback to routine research without web search
            return await self._call_research_model_fallback(prompt, temperature)
    
    async def _call_gpt5_deep_research(self, prompt: str, temperature: float = 0.7) -> str:
        """Call GPT-5 full model with enhanced reasoning and web search for deep research"""
        try:
            # Use Responses API with web search for deep research
            response = self.client.responses.create(
                model=self.deep_research_model,
                input=f"Conduct deep industry analysis with comprehensive web research on: {prompt}. Provide well-cited insights with strategic implications.",
                tools=[
                    {
                        "type": "web_search"
                    }
                ],
                reasoning={"effort": "high"},  # Use enhanced reasoning for deep dives
                text={"verbosity": "high"}  # Comprehensive responses for deep research
            )
            
            return response.output_text if hasattr(response, 'output_text') else str(response)
            
        except Exception as e:
            logger.error(f"GPT-5 deep research call failed: {e}")
            # Fallback to GPT-5 mini with search
            return await self._call_gpt5_mini_with_search(prompt, temperature, True)
    
    async def _call_research_model_fallback(self, prompt: str, temperature: float = 0.7) -> str:
        """Fallback method for research calls without built-in web search"""
        try:
            # Use the old method as fallback
            response = self.client.chat.completions.create(
                model="gpt-5-mini",  # Fallback to GPT-5 mini model
                messages=[
                    {"role": "system", "content": "You are an expert research analyst and industry intelligence specialist. Provide thorough, accurate, and actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Fallback research model call failed: {e}")
            raise
    
    async def _research_topic_standard(self, topic: ResearchTopic) -> List[ResearchFinding]:
        """Standard research using GPT-5 mini with built-in web search"""
        prompt = f"""
        Conduct comprehensive research on the following topic using web search:
        
        Topic: {topic.name}
        Keywords: {', '.join(topic.keywords)}
        Priority: {topic.priority}/10
        Research Depth: {topic.research_depth}
        
        Please research and provide:
        1. Recent developments and trends (last 6 months)
        2. Key market statistics and data
        3. Expert insights and analysis
        4. Notable case studies or examples
        5. Future outlook and predictions
        
        For each finding, provide:
        - Title and summary
        - Source URL and credibility assessment
        - Relevance score (0.0-1.0)
        - Key insights and implications
        - Publication date if available
        
        Return results as a JSON array of research findings with proper citations.
        """
        
        response = await self._call_gpt5_mini_with_search(prompt, temperature=0.3, use_web_search=True)
        return await self._parse_research_response(response, topic)
    
    async def _research_topic_deep(self, topic: ResearchTopic) -> List[ResearchFinding]:
        """Deep research using GPT-5 full model with enhanced reasoning"""
        prompt = f"""
        Conduct deep, comprehensive industry research on the following topic:
        
        Topic: {topic.name}
        Keywords: {', '.join(topic.keywords)}
        Priority: {topic.priority}/10
        Research Depth: DEEP ANALYSIS REQUIRED
        
        Please perform exhaustive research covering:
        1. Historical context and evolution
        2. Current market dynamics and trends
        3. Competitive landscape analysis
        4. Regulatory environment and changes
        5. Technology disruptions and innovations
        6. Consumer behavior shifts
        7. Future predictions and scenario analysis
        8. Strategic implications for businesses
        
        Use multiple sources and cross-reference information. Provide:
        - Comprehensive analysis with strategic insights
        - Source credibility assessment
        - Confidence levels for predictions
        - Risk factors and opportunities
        - Actionable recommendations
        
        Return as detailed JSON with extensive research findings and analysis.
        """
        
        response = await self._call_gpt5_deep_research(prompt, temperature=0.2)
        return await self._parse_research_response(response, topic)
    
    async def _research_topic_fallback(self, topic: ResearchTopic) -> List[ResearchFinding]:
        """Fallback research method using traditional approach"""
        findings = []
        
        # Get research configuration
        config = self.research_depth_configs.get(topic.research_depth, self.research_depth_configs["comprehensive"])
        
        # Multi-source research
        search_queries = await self._generate_search_queries(topic)
        
        for query in search_queries[:config["sources"]]:
            try:
                # Web search and scraping
                search_results = await self._search_web(query)
                
                for result in search_results[:5]:  # Top 5 results per query
                    finding = await self._process_search_result(result, topic)
                    if finding and finding.relevance_score >= self.min_relevance_threshold:
                        findings.append(finding)
                        
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Search query failed: {query} - {e}")
                continue
        
        # Analyze and rank findings
        findings = await self._analyze_and_rank_findings(findings, topic)
        
        return findings[:self.max_sources_per_topic]
    
    async def _parse_research_response(self, response: str, topic: ResearchTopic) -> List[ResearchFinding]:
        """Parse GPT-5 research response into ResearchFinding objects"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('[') or response.strip().startswith('{'):
                data = json.loads(response)
                if isinstance(data, dict) and 'findings' in data:
                    data = data['findings']
                elif not isinstance(data, list):
                    data = [data]
            else:
                # If not JSON, extract structured information
                data = await self._extract_structured_findings(response, topic)
            
            findings = []
            for item in data:
                if isinstance(item, dict):
                    finding = self._create_research_finding(item, topic)
                    if finding:
                        findings.append(finding)
            
            return findings
            
        except Exception as e:
            logger.error(f"Failed to parse research response: {e}")
            # Return a single finding with the raw response
            return [ResearchFinding(
                id=hashlib.md5(f"{topic.name}_{datetime.now()}".encode()).hexdigest(),
                topic=topic.name,
                title=f"Research Summary: {topic.name}",
                content=response,
                source_url="gpt-5-research",
                source_type="ai_research",
                relevance_score=0.8,
                credibility_score=0.9,
                publish_date=datetime.now(),
                discovered_at=datetime.now(),
                keywords=topic.keywords,
                summary=response[:500] + "..." if len(response) > 500 else response,
                insights=["AI-generated research insights"],
                implications=["Strategic implications from AI analysis"],
                trending_indicators={"ai_confidence": 0.8}
            )]
    
    async def _extract_structured_findings(self, response: str, topic: ResearchTopic) -> List[Dict[str, Any]]:
        """Extract structured findings from unstructured response"""
        # This method can be enhanced to parse markdown, bullet points, etc.
        return [{
            "title": f"Research Findings: {topic.name}",
            "content": response,
            "source_url": "gpt-5-research",
            "relevance_score": 0.8,
            "credibility_score": 0.9,
            "insights": ["AI-generated insights"],
            "implications": ["Strategic implications"]
        }]
    
    def _create_research_finding(self, data: Dict[str, Any], topic: ResearchTopic) -> Optional[ResearchFinding]:
        """Create ResearchFinding from parsed data"""
        try:
            return ResearchFinding(
                id=hashlib.md5(f"{data.get('title', topic.name)}_{datetime.now()}".encode()).hexdigest(),
                topic=topic.name,
                title=data.get('title', f"Research: {topic.name}"),
                content=data.get('content', ''),
                source_url=data.get('source_url', 'gpt-5-research'),
                source_type=data.get('source_type', 'ai_research'),
                relevance_score=float(data.get('relevance_score', 0.8)),
                credibility_score=float(data.get('credibility_score', 0.9)),
                publish_date=datetime.now(),
                discovered_at=datetime.now(),
                keywords=topic.keywords,
                summary=data.get('summary', data.get('content', '')[:500]),
                insights=data.get('insights', []),
                implications=data.get('implications', []),
                trending_indicators=data.get('trending_indicators', {})
            )
        except Exception as e:
            logger.error(f"Failed to create research finding: {e}")
            return None
    
    def _get_default_research_topics(self, industry: str) -> List[ResearchTopic]:
        """Get default research topics if AI generation fails"""
        default_topics = [
            ResearchTopic(
                name=f"{industry} Market Trends",
                keywords=[industry, "trends", "market", "growth", "forecast"],
                priority=9,
                research_depth="comprehensive"
            ),
            ResearchTopic(
                name=f"{industry} Technology Innovation",
                keywords=[industry, "technology", "innovation", "AI", "automation"],
                priority=8,
                research_depth="comprehensive"
            ),
            ResearchTopic(
                name=f"{industry} Regulatory Changes",
                keywords=[industry, "regulation", "compliance", "policy", "law"],
                priority=7,
                research_depth="standard"
            ),
            ResearchTopic(
                name=f"{industry} Consumer Behavior",
                keywords=[industry, "consumer", "behavior", "preferences", "adoption"],
                priority=8,
                research_depth="comprehensive"
            ),
            ResearchTopic(
                name=f"{industry} Competitive Analysis",
                keywords=[industry, "competition", "market share", "strategy", "leadership"],
                priority=9,
                research_depth="comprehensive"
            )
        ]
        
        return default_topics
    
    def _create_basic_intelligence(self, industry: str, findings: List[ResearchFinding], research_period: Tuple[datetime, datetime]) -> IndustryIntelligence:
        """Create basic intelligence structure if synthesis fails"""
        return IndustryIntelligence(
            industry=industry,
            generated_at=datetime.utcnow(),
            research_period=research_period,
            key_trends=[],
            market_developments=[],
            competitive_landscape={},
            emerging_technologies=[],
            regulatory_changes=[],
            consumer_behavior_shifts=[],
            content_opportunities=[],
            risk_factors=[],
            confidence_score=0.5,
            source_quality_metrics={"total_findings": len(findings)}
        )
    
    async def query_knowledge_base(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information"""
        try:
            # Create query embedding
            query_embedding = await self.embedding_service.create_embedding(query)
            
            # Search vector store
            results = await self.vector_store.similarity_search(
                query_embedding=query_embedding,
                limit=limit,
                similarity_threshold=0.7
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge base query failed: {e}")
            return []
    
    async def get_recent_intelligence(self, industry: str, days: int = 7) -> Optional[IndustryIntelligence]:
        """Get most recent intelligence report for an industry"""
        try:
            intelligence_files = list(self.intelligence_reports_path.glob(f"{industry}_*.json"))
            
            if not intelligence_files:
                return None
            
            # Sort by modification time (most recent first)
            intelligence_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            with open(intelligence_files[0], 'r') as f:
                data = json.load(f)
                
            # Convert back to IndustryIntelligence object
            # This is a simplified conversion - you might need more sophisticated handling
            return IndustryIntelligence(**data)
            
        except Exception as e:
            logger.error(f"Failed to get recent intelligence: {e}")
            return None

# Global instance
deep_research_agent = DeepResearchAgent()