"""
Production configuration and graceful degradation for missing dependencies
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ProductionConfig:
    """Handle production environment configuration and graceful degradation"""
    
    def __init__(self):
        self.is_production = os.getenv("ENVIRONMENT", "development") == "production"
        self.missing_deps = []
        self.available_features = []
        
    def check_dependencies(self):
        """Check for optional dependencies and enable features accordingly"""
        
        # Check for CrewAI (autonomous features)
        try:
            import crewai
            self.available_features.append("autonomous_posting")
        except ImportError:
            self.missing_deps.append("crewai")
            logger.warning("CrewAI not available - autonomous features disabled")
        
        # Check for Redis
        try:
            import redis
            self.available_features.append("redis_cache")
        except ImportError:
            self.missing_deps.append("redis")
            logger.warning("Redis not available - using fallback cache")
        
        # Check for vector search
        try:
            import faiss
            self.available_features.append("vector_search")
        except ImportError:
            self.missing_deps.append("faiss-cpu")
            logger.warning("FAISS not available - vector search disabled")
        
        # Always available features
        self.available_features.extend([
            "content_generation", 
            "image_generation",
            "memory_storage",
            "goals_tracking",
            "auth_system"
        ])
        
        logger.info(f"Available features: {self.available_features}")
        if self.missing_deps:
            logger.info(f"Missing optional dependencies: {self.missing_deps}")
    
    def get_feature_status(self):
        """Get status of all features for health checks"""
        return {
            "environment": "production" if self.is_production else "development",
            "available_features": self.available_features,
            "missing_dependencies": self.missing_deps,
            "total_features": len(self.available_features),
            "status": "healthy" if len(self.available_features) >= 4 else "degraded"
        }

# Global instance
production_config = ProductionConfig()
production_config.check_dependencies()