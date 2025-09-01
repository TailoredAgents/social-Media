import json
import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleMemorySystem:
    """Simplified memory system without FAISS dependency"""
    
    def __init__(self, data_path: str = "data/memory.json"):
        self.data_path = data_path
        self.content_store: Dict[str, Dict] = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from disk"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    self.content_store = json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            self.content_store = {}
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump(self.content_store, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def store_content(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store content with metadata"""
        content_id = str(uuid.uuid4())
        
        self.content_store[content_id] = {
            'content_id': content_id,
            'content': content,
            'metadata': metadata,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self._save_memory()
        return content_id
    
    def search_similar(self, query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict]:
        """Simple text-based search"""
        results = []
        query_lower = query.lower()
        
        for content_id, item in self.content_store.items():
            content_lower = item['content'].lower()
            
            # Simple similarity based on word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            if query_words and content_words:
                overlap = len(query_words.intersection(content_words))
                total_words = len(query_words.union(content_words))
                similarity = overlap / total_words if total_words > 0 else 0
                
                if similarity >= threshold:
                    results.append({
                        'content_id': content_id,
                        'content': item['content'],
                        'similarity_score': similarity,
                        'metadata': item['metadata'],
                        'created_at': item['created_at']
                    })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]
    
    def get_content_by_type(self, content_type: str, limit: int = 10) -> List[Dict]:
        """Get content by type"""
        results = []
        
        for content_id, item in self.content_store.items():
            if item['metadata'].get('type') == content_type:
                results.append({
                    'content_id': content_id,
                    'content': item['content'],
                    'metadata': item['metadata'],
                    'created_at': item['created_at']
                })
        
        # Sort by creation date
        results.sort(key=lambda x: x['created_at'], reverse=True)
        return results[:limit]
    
    def get_high_performing_content(self, min_engagement: float = 5.0, limit: int = 10) -> List[Dict]:
        """Get high-performing content"""
        results = []
        
        for content_id, item in self.content_store.items():
            engagement = item['metadata'].get('engagement_rate', 0)
            if engagement >= min_engagement:
                results.append({
                    'content_id': content_id,
                    'content': item['content'],
                    'engagement_rate': engagement,
                    'metadata': item['metadata'],
                    'created_at': item['created_at']
                })
        
        # Sort by engagement
        results.sort(key=lambda x: x['engagement_rate'], reverse=True)
        return results[:limit]
    
    def analyze_content_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in stored content"""
        if not self.content_store:
            return {'error': 'No content available for analysis'}
        
        patterns = {
            'total_content': len(self.content_store),
            'content_types': {},
            'platforms': {},
            'avg_engagement': 0,
        }
        
        engagements = []
        for item in self.content_store.values():
            metadata = item.get('metadata', {})
            
            # Content types
            content_type = metadata.get('type', 'unknown')
            patterns['content_types'][content_type] = patterns['content_types'].get(content_type, 0) + 1
            
            # Platforms  
            platform = metadata.get('platform', 'unknown')
            patterns['platforms'][platform] = patterns['platforms'].get(platform, 0) + 1
            
            # Engagement
            engagement = metadata.get('engagement_rate', 0)
            if engagement > 0:
                engagements.append(engagement)
        
        if engagements:
            patterns['avg_engagement'] = sum(engagements) / len(engagements)
        
        return patterns

# Global memory instance
memory_system = SimpleMemorySystem()