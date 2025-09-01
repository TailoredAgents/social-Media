"""
Mock Embedding Service for Development
Temporary replacement for OpenAI embedding service
"""
from typing import List
import logging
import random

logger = logging.getLogger(__name__)

class EmbeddingServiceMock:
    """Mock embedding service for development"""
    
    def __init__(self):
        logger.info("Mock Embedding Service initialized")
    
    async def create_embedding(self, text: str) -> List[float]:
        """Mock create embedding method"""
        # Return mock embedding vector (384 dimensions)
        embedding = [random.random() for _ in range(384)]
        logger.debug(f"Mock: Created embedding for text of length {len(text)}")
        return embedding