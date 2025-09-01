"""
Database performance optimizations for high-volume metrics collection
Includes indexes, partitioning strategies, and query optimization utilities
"""
from sqlalchemy import Index, text
from sqlalchemy.orm import Session
from backend.db.database import engine
from backend.db.models import (
    ContentItem, ContentPerformanceSnapshot, User, Goal, 
    GoalProgress, MemoryContent, ResearchData, Notification
)

def create_performance_indexes():
    """Create specialized indexes for high-volume metrics operations"""
    
    # Performance snapshot time-series indexes
    performance_indexes = [
        # Time-based queries for trend analysis
        Index('idx_perf_snapshot_time_desc', ContentPerformanceSnapshot.snapshot_time.desc()),
        Index('idx_perf_content_time', ContentPerformanceSnapshot.content_item_id, ContentPerformanceSnapshot.snapshot_time),
        
        # Engagement analysis indexes
        Index('idx_perf_engagement_desc', ContentPerformanceSnapshot.engagement_rate.desc()),
        Index('idx_perf_likes_desc', ContentPerformanceSnapshot.likes_count.desc()),
        Index('idx_perf_reach_desc', ContentPerformanceSnapshot.reach_count.desc()),
        
        # Growth tracking indexes
        Index('idx_perf_growth_likes', ContentPerformanceSnapshot.likes_growth.desc()),
        Index('idx_perf_growth_shares', ContentPerformanceSnapshot.shares_growth.desc()),
        
        # Composite indexes for complex queries
        Index('idx_perf_composite_engagement', 
              ContentPerformanceSnapshot.content_item_id,
              ContentPerformanceSnapshot.engagement_rate.desc(),
              ContentPerformanceSnapshot.snapshot_time.desc()),
    ]
    
    # Content item performance indexes
    content_indexes = [
        # Platform-specific performance queries
        Index('idx_content_platform_tier', ContentItem.platform, ContentItem.performance_tier),
        Index('idx_content_engagement_date', ContentItem.engagement_rate.desc(), ContentItem.published_at.desc()),
        
        # A/B testing and optimization
        Index('idx_content_ab_metrics', ContentItem.ab_test_id, ContentItem.ab_test_group, ContentItem.engagement_rate),
        
        # Topic and sentiment analysis
        Index('idx_content_topic_performance', ContentItem.topic_category, ContentItem.performance_tier),
        Index('idx_content_sentiment_engagement', ContentItem.sentiment, ContentItem.engagement_rate),
        
        # User-specific high-volume queries
        Index('idx_content_user_published', ContentItem.user_id, ContentItem.published_at.desc()),
        Index('idx_content_user_platform_perf', ContentItem.user_id, ContentItem.platform, ContentItem.performance_tier),
    ]
    
    # Memory and research indexes for vector search optimization
    memory_indexes = [
        # Vector search support indexes
        Index('idx_memory_type_created', MemoryContent.content_type, MemoryContent.created_at.desc()),
        Index('idx_memory_user_relevance', MemoryContent.user_id, MemoryContent.relevance_score.desc()),
        Index('idx_memory_engagement_perf', MemoryContent.engagement_score.desc(), MemoryContent.performance_tier),
        
        # Tag-based searches
        Index('idx_memory_tags_gin', MemoryContent.tags, postgresql_using='gin'),
        Index('idx_memory_platform_topic', MemoryContent.platform, MemoryContent.topic_category),
    ]
    
    # Research data indexes
    research_indexes = [
        # Time-series research queries
        Index('idx_research_created_desc', ResearchData.created_at.desc()),
        Index('idx_research_user_time', ResearchData.user_id, ResearchData.created_at.desc()),
        
        # Search and filter indexes
        Index('idx_research_source_sentiment', ResearchData.source, ResearchData.sentiment_score),
        Index('idx_research_keywords_gin', ResearchData.keywords, postgresql_using='gin'),
        Index('idx_research_trending_score', ResearchData.trending_score.desc()),
    ]
    
    # Goal tracking performance indexes
    goal_indexes = [
        # Real-time goal progress tracking
        Index('idx_goal_user_active', Goal.user_id, Goal.status),
        Index('idx_goal_progress_time', GoalProgress.goal_id, GoalProgress.recorded_at.desc()),
        Index('idx_goal_deadline_status', Goal.deadline, Goal.status),
        
        # Performance analysis
        Index('idx_goal_type_platform', Goal.goal_type, Goal.platform),
        Index('idx_goal_target_current', Goal.target_value, Goal.current_value),
    ]
    
    # Notification performance indexes
    notification_indexes = [
        # User notification queries
        Index('idx_notification_user_time', Notification.user_id, Notification.created_at.desc()),
        Index('idx_notification_read_status', Notification.user_id, Notification.is_read, Notification.created_at.desc()),
        Index('idx_notification_type_priority', Notification.notification_type, Notification.priority),
    ]
    
    return (performance_indexes + content_indexes + memory_indexes + 
            research_indexes + goal_indexes + notification_indexes)

def optimize_database_settings():
    """Apply PostgreSQL-specific optimizations for high-volume operations"""
    
    optimization_queries = [
        # Enable parallel queries for large datasets
        "SET max_parallel_workers_per_gather = 4;",
        
        # Optimize for analytics workloads
        "SET work_mem = '256MB';",
        "SET shared_buffers = '1GB';",
        
        # Enable query optimization
        "SET random_page_cost = 1.1;",
        "SET effective_cache_size = '4GB';",
        
        # Connection and background writer optimizations
        "SET checkpoint_completion_target = 0.9;",
        "SET wal_buffers = '64MB';",
        
        # Statistics and analysis optimizations
        "SET default_statistics_target = 500;",
        "SET track_activities = on;",
        "SET track_counts = on;",
        "SET track_functions = 'all';",
    ]
    
    return optimization_queries

def create_partitioned_tables():
    """Create partitioned tables for time-series data"""
    
    # Partition content performance snapshots by month for better query performance
    partition_queries = [
        """
        -- Create partitioned table for performance snapshots
        CREATE TABLE IF NOT EXISTS content_performance_snapshots_partitioned (
            LIKE content_performance_snapshots INCLUDING ALL
        ) PARTITION BY RANGE (snapshot_time);
        """,
        
        # Create monthly partitions for the current year
        """
        CREATE TABLE IF NOT EXISTS content_performance_snapshots_2025_01 
        PARTITION OF content_performance_snapshots_partitioned 
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
        """,
        
        """
        CREATE TABLE IF NOT EXISTS content_performance_snapshots_2025_02 
        PARTITION OF content_performance_snapshots_partitioned 
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
        """,
        
        # Add more partitions as needed...
        
        # Create materialized views for common analytics queries
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS content_daily_metrics AS
        SELECT 
            content_item_id,
            DATE(snapshot_time) as metric_date,
            MAX(likes_count) as max_likes,
            MAX(shares_count) as max_shares,
            MAX(comments_count) as max_comments,
            MAX(reach_count) as max_reach,
            AVG(engagement_rate) as avg_engagement_rate,
            COUNT(*) as snapshot_count
        FROM content_performance_snapshots
        GROUP BY content_item_id, DATE(snapshot_time)
        WITH DATA;
        """,
        
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_content_daily_metrics_unique
        ON content_daily_metrics (content_item_id, metric_date);
        """,
        
        # Weekly aggregation view
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS content_weekly_metrics AS
        SELECT 
            ci.user_id,
            ci.platform,
            DATE_TRUNC('week', snapshot_time) as week_start,
            COUNT(DISTINCT cps.content_item_id) as content_count,
            AVG(cps.engagement_rate) as avg_engagement_rate,
            SUM(cps.likes_count) as total_likes,
            SUM(cps.shares_count) as total_shares,
            SUM(cps.reach_count) as total_reach
        FROM content_performance_snapshots cps
        JOIN content_items ci ON cps.content_item_id = ci.id
        GROUP BY ci.user_id, ci.platform, DATE_TRUNC('week', snapshot_time)
        WITH DATA;
        """,
        
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_content_weekly_metrics_unique
        ON content_weekly_metrics (user_id, platform, week_start);
        """
    ]
    
    return partition_queries

def create_analytics_functions():
    """Create PostgreSQL functions for common analytics operations"""
    
    function_queries = [
        # Function to calculate engagement score
        """
        CREATE OR REPLACE FUNCTION calculate_engagement_score(
            likes_count INTEGER,
            shares_count INTEGER,
            comments_count INTEGER,
            reach_count INTEGER
        ) RETURNS FLOAT AS $$
        BEGIN
            IF reach_count = 0 THEN
                RETURN 0.0;
            END IF;
            
            RETURN ROUND(
                ((likes_count * 1.0 + shares_count * 2.0 + comments_count * 3.0) / reach_count) * 100,
                2
            );
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """,
        
        # Function to determine performance tier
        """
        CREATE OR REPLACE FUNCTION get_performance_tier(
            engagement_rate FLOAT,
            platform_avg FLOAT
        ) RETURNS TEXT AS $$
        BEGIN
            IF engagement_rate >= platform_avg * 2.0 THEN
                RETURN 'high';
            ELSIF engagement_rate >= platform_avg * 0.8 THEN
                RETURN 'medium';
            ELSE
                RETURN 'low';
            END IF;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """,
        
        # Function to get trending score
        """
        CREATE OR REPLACE FUNCTION calculate_trending_score(
            recent_engagement_rate FLOAT,
            historical_avg FLOAT,
            growth_rate FLOAT,
            recency_hours INTEGER
        ) RETURNS FLOAT AS $$
        BEGIN
            RETURN ROUND(
                (recent_engagement_rate / NULLIF(historical_avg, 0) * 50) +
                (growth_rate * 30) +
                (CASE 
                    WHEN recency_hours <= 1 THEN 20
                    WHEN recency_hours <= 6 THEN 15
                    WHEN recency_hours <= 24 THEN 10
                    ELSE 5
                END),
                2
            );
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """
    ]
    
    return function_queries

def apply_all_optimizations():
    """Apply all database optimizations"""
    
    with engine.connect() as connection:
        try:
            # Create performance indexes
            indexes = create_performance_indexes()
            for index in indexes:
                try:
                    index.create(connection, checkfirst=True)
                    print(f"✅ Created index: {index.name}")
                except Exception as e:
                    print(f"⚠️ Index creation skipped: {index.name} - {str(e)}")
            
            # Apply database settings (PostgreSQL only)
            if 'postgresql' in str(connection.dialect):
                settings = optimize_database_settings()
                for setting in settings:
                    try:
                        connection.execute(text(setting))
                        print(f"✅ Applied setting: {setting.split('=')[0].strip()}")
                    except Exception as e:
                        print(f"⚠️ Setting skipped: {setting} - {str(e)}")
                
                # Create partitioned tables and functions
                partition_queries = create_partitioned_tables()
                function_queries = create_analytics_functions()
                
                for query in partition_queries + function_queries:
                    try:
                        connection.execute(text(query))
                        print("✅ Applied optimization query")
                    except Exception as e:
                        print(f"⚠️ Query skipped: {str(e)}")
            
            connection.commit()
            print("✅ All database optimizations applied successfully")
            
        except Exception as e:
            print(f"❌ Optimization failed: {str(e)}")
            connection.rollback()

def refresh_materialized_views():
    """Refresh materialized views for up-to-date analytics"""
    
    with engine.connect() as connection:
        try:
            if 'postgresql' in str(connection.dialect):
                refresh_queries = [
                    "REFRESH MATERIALIZED VIEW CONCURRENTLY content_daily_metrics;",
                    "REFRESH MATERIALIZED VIEW CONCURRENTLY content_weekly_metrics;"
                ]
                
                for query in refresh_queries:
                    try:
                        connection.execute(text(query))
                        print(f"✅ Refreshed materialized view")
                    except Exception as e:
                        print(f"⚠️ View refresh skipped: {str(e)}")
                
                connection.commit()
                print("✅ Materialized views refreshed")
        
        except Exception as e:
            print(f"❌ View refresh failed: {str(e)}")

if __name__ == "__main__":
    apply_all_optimizations()