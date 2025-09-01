#!/usr/bin/env python3
"""
Complete Database Setup Script

This script provides a comprehensive database setup for the AI Social Media Content Agent.
It handles table creation, data seeding, and system initialization.

Usage:
    python setup_database.py [--env {dev|test|prod}] [--seed] [--reset]
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.core.config import get_settings
from backend.db.database import Base, engine, SessionLocal
from backend.db.models import *
from backend.core.vector_store import VectorStore

def create_sample_data(session):
    """Create sample data for development/testing"""
    
    print("🌱 Creating sample data...")
    
    try:
        # Create sample user
        sample_user = User(
            email="demo@example.com",
            username="demo_user",
            full_name="Demo User",
            is_active=True,
            tier="pro",
            auth_provider="local"
        )
        session.add(sample_user)
        session.flush()  # Get the user ID
        
        # Create sample goals
        sample_goals = [
            Goal(
                id=str(uuid.uuid4()),
                user_id=sample_user.id,
                title="Twitter Follower Growth",
                description="Grow Twitter following to increase brand awareness",
                goal_type="follower_growth",
                target_value=10000,
                current_value=5500,
                target_date=datetime.utcnow() + timedelta(days=90),
                status="active",
                platform="twitter",
                goal_metadata={"initial_followers": 5000, "growth_rate": "steady"}
            ),
            Goal(
                id=str(uuid.uuid4()),
                user_id=sample_user.id,
                title="LinkedIn Engagement Rate",
                description="Achieve consistent 5% engagement rate on LinkedIn posts",
                goal_type="engagement_rate",
                target_value=5.0,
                current_value=3.2,
                target_date=datetime.utcnow() + timedelta(days=60),
                status="active",
                platform="linkedin",
                goal_metadata={"target_posts_per_week": 3, "focus_topics": ["AI", "Technology"]}
            ),
            Goal(
                id=str(uuid.uuid4()),
                user_id=sample_user.id,
                title="Content Volume Goal",
                description="Publish 50 high-quality posts across all platforms",
                goal_type="content_volume",
                target_value=50,
                current_value=28,
                target_date=datetime.utcnow() + timedelta(days=30),
                status="active",
                platform="all",
                goal_metadata={"weekly_target": 12, "quality_threshold": "high"}
            )
        ]
        
        session.add_all(sample_goals)
        session.flush()
        
        # Create sample milestones for the first goal
        twitter_goal = sample_goals[0]
        sample_milestones = [
            Milestone(
                goal_id=twitter_goal.id,
                title="7K Followers Milestone",
                description="Reach 7,000 followers - 70% of goal",
                target_value=7000,
                target_date=datetime.utcnow() + timedelta(days=30),
                achieved=False
            ),
            Milestone(
                goal_id=twitter_goal.id,
                title="8.5K Followers Milestone",
                description="Reach 8,500 followers - 85% of goal",
                target_value=8500,
                target_date=datetime.utcnow() + timedelta(days=60),
                achieved=False
            )
        ]
        
        session.add_all(sample_milestones)
        
        # Create sample memory content
        sample_memory_content = [
            MemoryContent(
                id=str(uuid.uuid4()),
                content="AI is transforming how we approach social media marketing. The key is to maintain authenticity while leveraging automation for efficiency.",
                content_type="insight",
                source="research",
                platform="web",
                tags=["AI", "social media", "marketing", "automation"],
                sentiment="positive",
                topic_category="AI & Marketing",
                relevance_score=0.9,
                engagement_score=85.0,
                performance_tier="high",
                content_metadata={"source_url": "example.com/ai-marketing", "author": "Industry Expert"}
            ),
            MemoryContent(
                id=str(uuid.uuid4()),
                content="Best practices for LinkedIn content: 1) Hook in first line, 2) Use data-driven insights, 3) Include call-to-action, 4) Engage with comments quickly",
                content_type="template",
                source="manual",
                platform="linkedin",
                tags=["LinkedIn", "best practices", "engagement", "content strategy"],
                sentiment="neutral",
                topic_category="Content Strategy",
                relevance_score=0.8,
                engagement_score=72.0,
                performance_tier="high",
                content_metadata={"template_type": "best_practices", "platform_optimized": True}
            ),
            MemoryContent(
                id=str(uuid.uuid4()),
                content="Twitter thread idea: The evolution of AI tools in 2024 - from ChatGPT to specialized business applications. Include personal experiences and practical tips.",
                content_type="post",
                source="manual",
                platform="twitter",
                tags=["Twitter", "AI tools", "2024 trends", "thread idea"],
                sentiment="positive",
                topic_category="AI Trends",
                relevance_score=0.7,
                engagement_score=0.0,
                performance_tier="unknown",
                content_metadata={"post_type": "thread", "estimated_length": "8-10 tweets"}
            )
        ]
        
        session.add_all(sample_memory_content)
        
        # Create sample notifications
        sample_notifications = [
            Notification(
                id=str(uuid.uuid4()),
                user_id=sample_user.id,
                goal_id=twitter_goal.id,
                title="Great Progress on Twitter Goal! 🎉",
                message="You're 55% of the way to your Twitter follower goal. Keep up the excellent work!",
                notification_type="milestone_progress",
                priority="medium",
                is_read=False,
                metadata={"progress_percentage": 55, "milestone_type": "progress_update"}
            ),
            Notification(
                id=str(uuid.uuid4()),
                user_id=sample_user.id,
                title="Weekly Goal Review Available",
                message="Your weekly goal progress report is ready. Check your achievements and plan for next week.",
                notification_type="goal_report",
                priority="low",
                is_read=False,
                metadata={"report_type": "weekly", "goals_reviewed": 3}
            )
        ]
        
        session.add_all(sample_notifications)
        
        session.commit()
        print("✅ Sample data created successfully")
        
        return {
            "users": 1,
            "goals": len(sample_goals),
            "milestones": len(sample_milestones),
            "memory_content": len(sample_memory_content),
            "notifications": len(sample_notifications)
        }
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise

def initialize_vector_store():
    """Initialize FAISS vector store"""
    
    print("🧠 Initializing FAISS vector store...")
    
    try:
        vector_store = VectorStore()
        stats = vector_store.get_statistics()
        
        print(f"✅ FAISS vector store initialized")
        print(f"   - Index type: {stats.get('index_type', 'unknown')}")
        print(f"   - Total vectors: {stats.get('total_vectors', 0)}")
        print(f"   - Index size: {stats.get('index_size_mb', 0):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing vector store: {e}")
        return False

def setup_database(environment="dev", create_sample_data_flag=False, reset_db=False):
    """Complete database setup"""
    
    print("🚀 AI Social Media Content Agent - Database Setup")
    print(f"Environment: {environment.upper()}")
    print(f"Create Sample Data: {create_sample_data_flag}")
    print(f"Reset Database: {reset_db}")
    print("=" * 60)
    
    # Get settings
    settings = get_settings()
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            print(f"   Database URL: {settings.database_url}")
    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Reset database if requested
    if reset_db:
        print("\n🗑️  Resetting database...")
        try:
            Base.metadata.drop_all(bind=engine)
            
            # Drop alembic_version table
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                conn.commit()
            
            print("✅ Database reset completed")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False
    
    # Create all tables
    print("\n🏗️  Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            # Get table names (PostgreSQL specific)
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='public' 
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"   Created tables: {', '.join(tables)}")
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    # Create sample data if requested
    sample_stats = None
    if create_sample_data_flag:
        print("\n🌱 Setting up sample data...")
        
        session = SessionLocal()
        try:
            sample_stats = create_sample_data(session)
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # Initialize vector store
    print("\n🧠 Setting up FAISS vector store...")
    vector_success = initialize_vector_store()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    
    if sample_stats:
        print("\n📊 Sample Data Summary:")
        for key, value in sample_stats.items():
            print(f"   - {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🔧 Vector Store: {'✅ Ready' if vector_success else '❌ Failed'}")
    
    print("\n🚀 The AI Social Media Content Agent database is now ready!")
    print("   - Run `python -m backend.main` to start the API server")
    print("   - Access API docs at http://localhost:8000/docs")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="AI Social Media Content Agent Database Setup")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="dev",
                       help="Environment to set up (default: dev)")
    parser.add_argument("--seed", action="store_true",
                       help="Create sample data for development/testing")
    parser.add_argument("--reset", action="store_true",
                       help="Reset database (drop all tables)")
    
    args = parser.parse_args()
    
    success = setup_database(
        environment=args.env,
        create_sample_data_flag=args.seed,
        reset_db=args.reset
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()