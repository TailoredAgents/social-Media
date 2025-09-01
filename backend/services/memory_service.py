"""
Content Memory Service
Provides high-level memory management functionality including content storage,
retrieval, and semantic search operations using FAISS vector database.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Lazy import to avoid loading FAISS at startup
# from backend.core.memory import FAISSMemorySystem
from backend.db.models import Memory, Content
from backend.db.database import get_db
from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing memory system with lazy FAISS loading"""
    
    def __init__(self):
        self._faiss_memory = None
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced workers
    
    @property
    def faiss_memory(self):
        """Lazy-load FAISS memory system only when needed"""
        if self._faiss_memory is None:
            try:
                from backend.core.memory import FAISSMemorySystem
                self._faiss_memory = FAISSMemorySystem()
                logger.info("FAISS memory system loaded on-demand")
            except Exception as e:
                logger.warning(f"Failed to load FAISS memory system: {e}")
                # Use a mock object that returns empty results
                self._faiss_memory = self._create_fallback_memory()
        return self._faiss_memory
    
    def _create_fallback_memory(self):
        """Create fallback memory object when FAISS is not available"""
        class FallbackMemory:
            def store_content(self, content, metadata):
                return f"fallback_{hash(content)}"
            def search_similar(self, query, top_k=5, threshold=0.8):
                return []
            def get_high_performing_content(self, days_back=30):
                return []
            def analyze_content_patterns(self):
                return {"patterns": [], "insights": []}
            def cleanup_old_content(self, days_back=90):
                return 0
        return FallbackMemory()
    
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Dict[str, Any],
        db: Session
    ) -> Optional[Memory]:
        """Store content in both database and FAISS index"""
        try:
            # Store in FAISS index (run in thread pool for async)
            loop = asyncio.get_event_loop()
            content_id = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.store_content,
                content,
                {
                    'type': memory_type,
                    **metadata
                }
            )
            
            if not content_id:
                return None
            
            # Store in database
            db_memory = Memory(
                content=content,
                memory_type=memory_type,
                memory_metadata=metadata,
                vector_id=content_id,
                relevance_score=1.0
            )
            
            db.add(db_memory)
            db.commit()
            db.refresh(db_memory)
            
            return db_memory
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing memory: {e}")
            return None
    
    async def search_similar_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using FAISS"""
        try:
            # Perform vector search
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.search_similar,
                query,
                limit * 2,  # Get more results for filtering
                threshold
            )
            
            # Filter by memory type if specified
            if memory_type:
                search_results = [
                    r for r in search_results 
                    if r.get('metadata', {}).get('type') == memory_type
                ]
            
            # Enhance results with database information if available
            if db:
                enhanced_results = []
                for result in search_results[:limit]:
                    vector_id = result.get('content_id')
                    if vector_id:
                        db_memory = db.query(Memory).filter(
                            Memory.vector_id == vector_id
                        ).first()
                        
                        if db_memory:
                            enhanced_results.append({
                                'id': db_memory.id,
                                'content': db_memory.content,
                                'memory_type': db_memory.memory_type,
                                'similarity_score': result['similarity_score'],
                                'metadata': db_memory.memory_metadata,
                                'created_at': db_memory.created_at,
                                'tags': db_memory.tags
                            })
                        else:
                            enhanced_results.append(result)
                
                return enhanced_results[:limit]
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def find_memories_for_content_creation(
        self,
        topic: str,
        platform: str,
        db: Session
    ) -> Dict[str, Any]:
        """Find relevant memories for content creation"""
        try:
            # Search for similar content
            similar_content = await self.search_similar_memories(
                query=f"{topic} {platform} content",
                memory_type="content",
                limit=5,
                db=db
            )
            
            # Search for research insights
            research_insights = await self.search_similar_memories(
                query=topic,
                memory_type="research",
                limit=5,
                db=db
            )
            
            # Search for successful templates
            templates = await self.search_similar_memories(
                query=f"{platform} template",
                memory_type="template",
                limit=3,
                db=db
            )
            
            # Get high-performing content
            loop = asyncio.get_event_loop()
            high_performing = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.get_high_performing_content,
                5.0,  # min engagement rate
                5
            )
            
            return {
                'similar_content': similar_content,
                'research_insights': research_insights,
                'templates': templates,
                'high_performing_examples': high_performing,
                'total_relevant_memories': len(similar_content) + len(research_insights)
            }
            
        except Exception as e:
            logger.error(f"Error finding memories for content: {e}")
            return {
                'similar_content': [],
                'research_insights': [],
                'templates': [],
                'high_performing_examples': [],
                'total_relevant_memories': 0
            }
    
    async def analyze_content_performance(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze content performance patterns"""
        try:
            # Get pattern analysis from FAISS
            loop = asyncio.get_event_loop()
            patterns = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.analyze_content_patterns
            )
            
            # Get database statistics
            total_memories = db.query(func.count(Memory.id)).scalar()
            
            # Memory type distribution
            type_stats = db.query(
                Memory.memory_type,
                func.count(Memory.id)
            ).group_by(Memory.memory_type).all()
            
            # Recent high-performing content
            recent_high_performing = db.query(Memory).filter(
                Memory.created_at >= datetime.utcnow() - timedelta(days=30)
            ).order_by(desc(Memory.relevance_score)).limit(10).all()
            
            # Combine results
            return {
                'total_memories': total_memories,
                'vector_index_stats': patterns,
                'memory_type_distribution': {
                    memory_type: count for memory_type, count in type_stats
                },
                'recent_high_performing': [
                    {
                        'id': m.id,
                        'content': m.content[:200] + '...' if len(m.content) > 200 else m.content,
                        'type': m.memory_type,
                        'relevance_score': m.relevance_score,
                        'created_at': m.created_at
                    }
                    for m in recent_high_performing
                ],
                'index_health': {
                    'total_indexed': patterns.get('total_content', 0),
                    'avg_engagement': patterns.get('avg_engagement', 0),
                    'top_topics': patterns.get('top_topics', [])[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {e}")
            return {
                'error': str(e),
                'total_memories': 0,
                'vector_index_stats': {},
                'memory_type_distribution': {},
                'recent_high_performing': [],
                'index_health': {}
            }
    
    async def sync_database_with_faiss(self, db: Session) -> Dict[str, int]:
        """Sync database memories with FAISS index"""
        try:
            # Get memories without vector IDs
            unindexed_memories = db.query(Memory).filter(
                Memory.vector_id == None
            ).limit(100).all()
            
            indexed_count = 0
            failed_count = 0
            
            for memory in unindexed_memories:
                try:
                    # Create metadata for FAISS
                    metadata = memory.memory_metadata or {}
                    metadata.update({
                        'type': memory.memory_type,
                        'db_id': memory.id,
                        'tags': memory.tags or []
                    })
                    
                    # Store in FAISS
                    loop = asyncio.get_event_loop()
                    vector_id = await loop.run_in_executor(
                        self.executor,
                        self.faiss_memory.store_content,
                        memory.content,
                        metadata
                    )
                    
                    if vector_id:
                        memory.vector_id = vector_id
                        indexed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error indexing memory {memory.id}: {e}")
                    failed_count += 1
            
            # Commit all updates
            if indexed_count > 0:
                db.commit()
            
            return {
                'indexed': indexed_count,
                'failed': failed_count,
                'remaining': db.query(func.count(Memory.id)).filter(
                    Memory.vector_id == None
                ).scalar()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing database with FAISS: {e}")
            return {'indexed': 0, 'failed': 0, 'remaining': 0, 'error': str(e)}
    
    async def cleanup_old_memories(
        self,
        days_to_keep: int = 365,
        db: Session = None
    ) -> int:
        """Clean up old memories from both database and FAISS"""
        try:
            # Clean up FAISS index
            loop = asyncio.get_event_loop()
            faiss_cleaned = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.cleanup_old_content,
                days_to_keep
            )
            
            # Clean up database if session provided
            db_cleaned = 0
            if db:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                db_cleaned = db.query(Memory).filter(
                    Memory.created_at < cutoff_date
                ).delete()
                db.commit()
            
            return max(faiss_cleaned, db_cleaned)
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Error cleaning up memories: {e}")
            return 0

# Global memory service instance
memory_service = MemoryService()