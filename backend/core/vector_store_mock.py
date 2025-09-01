"""
Mock Vector Store for Development
Temporary replacement for FAISS-based vector store
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VectorStoreMock:
    """Mock vector store for development when FAISS is not available"""
    
    def __init__(self):
        self.documents = {}
        logger.info("Mock Vector Store initialized")
    
    async def add_document(self, document_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]):
        """Mock add document method"""
        self.documents[document_id] = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }
        logger.debug(f"Mock: Added document {document_id}")
    
    async def similarity_search(self, query_embedding: List[float], limit: int = 10, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Mock similarity search method"""
        # Return mock results
        results = []
        for doc_id, doc_data in list(self.documents.items())[:limit]:
            results.append({
                "id": doc_id,
                "content": doc_data["content"],
                "metadata": doc_data["metadata"],
                "similarity_score": 0.85  # Mock score
            })
        
        logger.debug(f"Mock: Returned {len(results)} search results")
        return results