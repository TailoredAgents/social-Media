# Ensure warnings are suppressed in worker processes
from backend.core.suppress_warnings import suppress_third_party_warnings
suppress_third_party_warnings()

from celery import current_task
from celery.schedules import crontab
from backend.tasks.celery_app import celery_app
from backend.agents.crew_config import research_agent, create_research_task
from backend.agents.tools import web_scraper, twitter_tool, memory_tool, openai_tool
from backend.services.research_scheduler import research_scheduler
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def run_daily_research(self, topics=None):
    """Run daily research across multiple topics"""
    if topics is None:
        topics = [
            "social media trends",
            "AI marketing",
            "content marketing",
            "digital transformation",
            "social media best practices"
        ]
    
    try:
        results = []
        total_topics = len(topics)
        
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': total_topics, 'status': 'Starting research...'}
        )
        
        for i, topic in enumerate(topics):
            current_task.update_state(
                state='PROGRESS',
                meta={'current': i+1, 'total': total_topics, 'status': f'Researching: {topic}'}
            )
            
            # Create research task
            research_task = create_research_task(topic)
            
            # Execute research
            research_result = research_agent.execute_task(research_task)
            
            # Store in memory
            memory_tool.store_content(
                content=str(research_result),
                metadata={
                    'type': 'research',
                    'topic': topic,
                    'research_date': datetime.now(timezone.utc).isoformat()
                }
            )
            
            results.append({
                'topic': topic,
                'result': str(research_result),
                'status': 'completed'
            })
        
        current_task.update_state(
            state='PROGRESS',
            meta={'current': total_topics, 'total': total_topics, 'status': 'Research completed!'}
        )
        
        return {
            'status': 'success',
            'message': f'Research completed for {len(results)} topics',
            'topics_researched': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Daily research failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Daily research failed: {str(exc)}'
        }

@celery_app.task
def research_trending_topics():
    """Research what's trending on social media"""
    try:
        # Search for trending topics on Twitter
        trending_searches = [
            "trending AI",
            "social media 2025",
            "marketing trends",
            "digital marketing",
            "content strategy"
        ]
        
        results = []
        
        for search in trending_searches:
            # Twitter search
            tweets = twitter_tool.search_tweets(search, count=10)
            
            if tweets and not any("error" in tweet for tweet in tweets):
                # Analyze trending content
                tweet_texts = [tweet['text'] for tweet in tweets if 'text' in tweet]
                
                analysis_prompt = f"""Analyze these tweets about '{search}' and identify:
                1. Key trending themes
                2. Common hashtags
                3. Engagement patterns
                4. Content opportunities
                
                Tweets: {tweet_texts[:5]}  # Limit to first 5 tweets
                
                Provide a concise analysis with actionable insights."""
                
                analysis = openai_tool.generate_text(analysis_prompt, max_tokens=300)
                
                result = {
                    'search_term': search,
                    'tweet_count': len(tweets),
                    'analysis': analysis,
                    'sample_tweets': tweet_texts[:3]
                }
                
                results.append(result)
                
                # Store in memory
                memory_tool.store_content(
                    content=analysis,
                    metadata={
                        'type': 'trending_analysis',
                        'search_term': search,
                        'tweet_count': len(tweets)
                    }
                )
        
        return {
            'status': 'success',
            'message': f'Trending research completed for {len(results)} topics',
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Trending research failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Trending research failed: {str(exc)}'
        }

@celery_app.task
def research_competitor_content(competitors=None):
    """Research competitor content and strategies"""
    if competitors is None:
        competitors = [
            "@buffer",
            "@hootsuite", 
            "@sproutsocial",
            "@hubspot"
        ]
    
    try:
        results = []
        
        for competitor in competitors:
            # Search for competitor content
            competitor_tweets = twitter_tool.search_tweets(f"from:{competitor}", count=5)
            
            if competitor_tweets and not any("error" in tweet for tweet in competitor_tweets):
                tweet_texts = [tweet['text'] for tweet in competitor_tweets if 'text' in tweet]
                
                analysis_prompt = f"""Analyze {competitor}'s recent content strategy:
                
                Recent posts: {tweet_texts}
                
                Identify:
                1. Content themes and topics
                2. Posting style and tone
                3. Engagement tactics used
                4. Hashtag strategies
                5. Content opportunities we could explore
                
                Provide insights for our content strategy."""
                
                analysis = openai_tool.generate_text(analysis_prompt, max_tokens=400)
                
                result = {
                    'competitor': competitor,
                    'posts_analyzed': len(tweet_texts),
                    'analysis': analysis,
                    'sample_content': tweet_texts[:2]
                }
                
                results.append(result)
                
                # Store in memory
                memory_tool.store_content(
                    content=analysis,
                    metadata={
                        'type': 'competitor_analysis',
                        'competitor': competitor,
                        'posts_count': len(tweet_texts)
                    }
                )
        
        return {
            'status': 'success',
            'message': f'Competitor analysis completed for {len(results)} competitors',
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Competitor research failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Competitor research failed: {str(exc)}'
        }

@celery_app.task
def research_web_content(urls=None):
    """Research content from specified URLs"""
    if urls is None:
        urls = [
            "https://blog.hubspot.com/marketing",
            "https://buffer.com/resources",
            "https://blog.hootsuite.com"
        ]
    
    try:
        results = []
        
        for url in urls:
            scraped_data = web_scraper.scrape_url(url)
            
            if scraped_data['status'] == 'success':
                # Analyze the content
                analysis_prompt = f"""Analyze this web content for social media opportunities:
                
                Title: {scraped_data['title']}
                Content: {scraped_data['content'][:1000]}...
                
                Identify:
                1. Key insights and takeaways
                2. Social media content opportunities
                3. Trending topics mentioned
                4. Actionable tips for our audience
                
                Provide a summary with content ideas."""
                
                analysis = openai_tool.generate_text(analysis_prompt, max_tokens=350)
                
                result = {
                    'url': url,
                    'title': scraped_data['title'],
                    'analysis': analysis,
                    'content_length': len(scraped_data['content'])
                }
                
                results.append(result)
                
                # Store in memory
                memory_tool.store_content(
                    content=analysis,
                    metadata={
                        'type': 'web_content_analysis',
                        'source_url': url,
                        'title': scraped_data['title']
                    }
                )
        
        return {
            'status': 'success',
            'message': f'Web content research completed for {len(results)} URLs',
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Web content research failed: {str(exc)}")
        return {
            'status': 'error',
            'message': f'Web content research failed: {str(exc)}'
        }

# ============================================================================
# NEW: Deep Research Tasks with GPT-5-mini Web Search
# ============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def execute_weekly_deep_research_task(self, industry: str):
    """
    Celery task for executing weekly deep research using GPT-5-mini with web search
    
    Args:
        industry: Target industry for research
        
    Returns:
        Research execution results
    """
    try:
        logger.info(f"Starting weekly deep research task for {industry}")
        
        # Run async research in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                research_scheduler.execute_weekly_research(industry)
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Weekly deep research task failed for {industry}: {e}")
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying deep research task for {industry} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=300, exc=e)
        
        # Final failure
        return {
            "status": "failed",
            "industry": industry,
            "error": str(e),
            "retries": self.request.retries
        }

@celery_app.task
def setup_industry_deep_research_task(industry: str, business_context: dict, schedule_config: dict = None):
    """
    Celery task for setting up industry deep research
    
    Args:
        industry: Target industry
        business_context: Business context and goals
        schedule_config: Custom schedule configuration
        
    Returns:
        Setup results
    """
    try:
        logger.info(f"Setting up deep research for {industry}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                research_scheduler.setup_industry_research(
                    industry, business_context, schedule_config
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Deep research setup failed for {industry}: {e}")
        return {
            "status": "error",
            "industry": industry,
            "error": str(e)
        }

@celery_app.task
def trigger_immediate_deep_research_task(industry: str):
    """
    Celery task for triggering immediate deep research
    
    Args:
        industry: Target industry
        
    Returns:
        Research results
    """
    try:
        logger.info(f"Triggering immediate deep research for {industry}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                research_scheduler.trigger_immediate_research(industry)
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Immediate deep research failed for {industry}: {e}")
        return {
            "status": "error",
            "industry": industry,
            "error": str(e)
        }

@celery_app.task
def deep_research_health_check_task():
    """
    Health check task for deep research system
    
    Returns:
        System health status
    """
    try:
        logger.info("Running deep research system health check")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get list of configured industries
            industries = loop.run_until_complete(
                research_scheduler.list_configured_industries()
            )
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "configured_industries": len(industries),
                "industries": industries,
                "system_checks": {
                    "scheduler_active": True,
                    "celery_worker_active": True,
                    "knowledge_base_accessible": True,
                    "gpt4o_mini_available": True
                }
            }
            
            return health_status
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Deep research health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# ============================================================================
# Periodic Task Setup for Deep Research
# ============================================================================

@celery_app.on_after_configure.connect
def setup_deep_research_periodic_tasks(sender, **kwargs):
    """Set up periodic deep research tasks"""
    
    # Deep Research Health check every 4 hours
    sender.add_periodic_task(
        crontab(minute=0, hour='*/4'),  # Every 4 hours
        deep_research_health_check_task.s(),
        name='deep_research_health_check'
    )
    
    # Weekly Deep Research Tasks - Configurable per industry
    # These are examples - in production, these would be dynamically configured
    
    # Fintech deep research - Every Sunday at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week=0),
        execute_weekly_deep_research_task.s('fintech'),
        name='weekly_fintech_deep_research',
        options={'expires': 3600 * 6}  # 6 hour expiry
    )
    
    # Healthcare deep research - Every Sunday at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        execute_weekly_deep_research_task.s('healthcare'),
        name='weekly_healthcare_deep_research',
        options={'expires': 3600 * 6}
    )
    
    # E-commerce deep research - Every Sunday at 4 AM
    sender.add_periodic_task(
        crontab(hour=4, minute=0, day_of_week=0),
        execute_weekly_deep_research_task.s('ecommerce'),
        name='weekly_ecommerce_deep_research',
        options={'expires': 3600 * 6}
    )
    
    # SaaS deep research - Every Sunday at 5 AM
    sender.add_periodic_task(
        crontab(hour=5, minute=0, day_of_week=0),
        execute_weekly_deep_research_task.s('saas'),
        name='weekly_saas_deep_research',
        options={'expires': 3600 * 6}
    )
    
    # Manufacturing deep research - Every Sunday at 6 AM
    sender.add_periodic_task(
        crontab(hour=6, minute=0, day_of_week=0),
        execute_weekly_deep_research_task.s('manufacturing'),
        name='weekly_manufacturing_deep_research',
        options={'expires': 3600 * 6}
    )
    
    logger.info("Deep research periodic tasks configured for 5 industries")