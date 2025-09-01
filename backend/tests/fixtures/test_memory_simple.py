"""
Simple test for memory system without requiring OpenAI API
"""
import os
import sys

# Set a fake OpenAI API key for testing
os.environ['OPENAI_API_KEY'] = 'test-key'

try:
    from backend.core.memory import FAISSMemorySystem
    print("✅ Memory system imported successfully")
    
    # Initialize memory system
    memory_system = FAISSMemorySystem()
    print("✅ Memory system initialized")
    
    # Check if using fallback
    if hasattr(memory_system, '_simple_search'):
        print("🔄 Using simple vector search fallback (FAISS not available)")
        print(f"   - Index dimension: {memory_system._simple_search.dimension}")
        print(f"   - Current vectors: {memory_system._simple_search.ntotal}")
    else:
        print("🚀 Using FAISS vector search")
        print(f"   - Index dimension: {memory_system.dimension}")
        print(f"   - Current vectors: {memory_system.index.ntotal}")
    
    # Test basic operations without API calls
    print("\n📊 Memory system ready for integration")
    
    # Test properties
    print(f"   - Total vectors: {memory_system.index.ntotal}")
    print(f"   - Metadata entries: {len(memory_system.metadata)}")
    
    print("\n✅ Memory integration test completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)