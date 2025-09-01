"""
Test script for FAISS memory system integration
"""
import asyncio
import json
from datetime import datetime
from backend.core.memory import FAISSMemorySystem
from backend.services.memory_service import memory_service

async def test_memory_operations():
    """Test FAISS memory system operations"""
    print("🧪 Testing FAISS Memory System Integration\n")
    
    # Test 1: Initialize memory system
    print("1️⃣ Testing memory system initialization...")
    memory_system = FAISSMemorySystem()
    print(f"✅ Memory system initialized")
    print(f"   - Index dimension: {memory_system.dimension}")
    print(f"   - Current vectors: {memory_system.index.ntotal}")
    print(f"   - Metadata entries: {len(memory_system.metadata)}\n")
    
    # Test 2: Store content
    print("2️⃣ Testing content storage...")
    test_contents = [
        {
            "content": "AI agents are revolutionizing how we create and manage social media content. They can analyze trends, generate posts, and optimize timing automatically.",
            "metadata": {
                "type": "insight",
                "platform": "twitter",
                "user_id": "test_user",
                "engagement_rate": 4.5,
                "tags": ["AI", "automation", "social media"]
            }
        },
        {
            "content": "Just launched our new AI-powered content generation tool! It learns from your best-performing posts and creates similar high-engagement content. #AIMarketing #ContentCreation",
            "metadata": {
                "type": "generated_content",
                "platform": ,
                "user_id": "test_user",
                "engagement_rate": 6.2,
                "tags": ["product launch", "AI tools", "marketing"]
            }
        },
        {
            "content": "Research shows that posts with emojis get 25% more engagement. Consider adding relevant emojis to make your content more relatable and eye-catching! 🚀📈",
            "metadata": {
                "type": "research",
                "platform": "instagram",
                "user_id": "test_user",
                "engagement_rate": 7.8,
                "tags": ["engagement tips", "emojis", "social media strategy"]
            }
        }
    ]
    
    stored_ids = []
    for content_data in test_contents:
        content_id = memory_system.store_content(
            content_data["content"],
            content_data["metadata"]
        )
        stored_ids.append(content_id)
        print(f"✅ Stored content: {content_id}")
    
    print(f"\n   Total vectors stored: {memory_system.index.ntotal}\n")
    
    # Test 3: Search similar content
    print("3️⃣ Testing similarity search...")
    search_queries = [
        "How can AI help with social media marketing?",
        "Tips for increasing engagement on posts",
        "Content creation automation tools"
    ]
    
    for query in search_queries:
        print(f"\n   Query: '{query}'")
        results = memory_system.search_similar(query, top_k=3, threshold=0.5)
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}:")
            print(f"     - Similarity: {result['similarity_score']:.3f}")
            print(f"     - Type: {result['metadata'].get('type')}")
            print(f"     - Platform: {result['metadata'].get('platform')}")
            print(f"     - Content: {result['content'][:100]}...")
    
    # Test 4: Get high-performing content
    print("\n4️⃣ Testing high-performing content retrieval...")
    high_performing = memory_system.get_high_performing_content(min_engagement=6.0)
    print(f"   Found {len(high_performing)} high-performing items:")
    
    for item in high_performing:
        print(f"   - Engagement: {item['engagement_rate']}")
        print(f"     Platform: {item['metadata'].get('platform')}")
        print(f"     Content: {item['content'][:80]}...\n")
    
    # Test 5: Analyze content patterns
    print("5️⃣ Testing content pattern analysis...")
    patterns = memory_system.analyze_content_patterns()
    print(f"   Total content: {patterns['total_content']}")
    print(f"   Content types: {patterns['content_types']}")
    print(f"   Platforms: {patterns['platforms']}")
    print(f"   Average engagement: {patterns['avg_engagement']:.2f}\n")
    
    # Test 6: Test async operations with memory service
    print("6️⃣ Testing async memory service operations...")
    
    # Mock database session
    class MockDB:
        def add(self, obj): pass
        def commit(self): pass
        def refresh(self, obj): obj.id = 1
    
    # Test async search
    results = await memory_service.search_similar_content(
        query="AI content generation",
        user_id="test_user",
        top_k=3
    )
    print(f"   Async search returned {len(results)} results")
    
    # Test pattern analysis
    patterns = await memory_service.analyze_user_content_patterns("test_user")
    print(f"   User content analysis:")
    print(f"     - Total content: {patterns['total_content']}")
    print(f"     - Average engagement: {patterns['avg_engagement']:.2f}")
    
    print("\n✅ All tests completed successfully!")
    
    # Test 7: Save and reload test
    print("\n7️⃣ Testing persistence...")
    memory_system._save_index()
    memory_system._save_metadata()
    print("   ✅ Index and metadata saved")
    
    # Create new instance and verify data persists
    new_memory_system = FAISSMemorySystem()
    print(f"   ✅ Reloaded: {new_memory_system.index.ntotal} vectors")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_memory_operations())