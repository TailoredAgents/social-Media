# pgvector Migration Guide

## Overview

This migration replaces all mock vector stores and FAISS file-based storage with production-ready pgvector for semantic search.

## What Was Replaced

### Mock Services Removed
- `backend/core/vector_store_mock.py` - Mock vector storage with hardcoded similarities
- `backend/services/embedding_service_mock.py` - Fake embeddings with random vectors
- FAISS file-based storage dependencies

### New Production Services Added
- `backend/services/pgvector_service.py` - Production vector service using PostgreSQL + pgvector
- `backend/api/vector_search_production.py` - Production REST API for vector search
- `backend/services/memory_service_production.py` - Production memory service
- Database migration `009_add_pgvector_tables.py` - Creates vector tables with HNSW indexes

## Architecture Changes

### Before (Mock/FAISS)
```
Content → FAISS Files (.npy, .json) → SimpleVectorSearch → Mock Results
Memory → File Storage → Random Similarities
```

### After (pgvector)
```
Content → PostgreSQL Vector Columns → pgvector HNSW Index → Real Semantic Search
Memory → Database Tables → OpenAI Embeddings → Cosine Similarity
```

## Database Schema

### New Tables Created

#### content_embeddings
```sql
CREATE TABLE content_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB,
    embedding_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX content_embeddings_embedding_idx ON content_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

#### memory_embeddings
```sql
CREATE TABLE memory_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(100) NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    embedding_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX memory_embeddings_embedding_idx ON memory_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

## API Endpoints

### Production Vector Search API (`/api/vector-search/*`)

- `POST /api/vector-search/content/store` - Store content embeddings
- `POST /api/vector-search/memory/store` - Store memory embeddings  
- `POST /api/vector-search/content/search` - Search similar content
- `POST /api/vector-search/memory/search` - Search similar memories
- `DELETE /api/vector-search/content/{id}` - Delete content embedding
- `DELETE /api/vector-search/memory/{id}` - Delete memory embedding
- `GET /api/vector-search/stats` - Get embedding statistics

## Migration Steps

### 1. Database Setup
```bash
# Enable pgvector extension (requires PostgreSQL 11+)
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migration
alembic upgrade head
```

### 2. Environment Variables Required
```bash
# Required for embeddings
OPENAI_API_KEY=your_openai_api_key

# PostgreSQL with pgvector
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Development vs Production

#### Development (SQLite)
- Falls back to text storage instead of vector columns
- No HNSW indexes (uses basic similarity)
- Still uses real OpenAI embeddings

#### Production (PostgreSQL + pgvector)
- Full vector columns with 1536 dimensions
- HNSW indexes for fast similarity search
- Cosine similarity with `<=>` operator

## Performance Improvements

### Before (Mock/FAISS)
- Hardcoded 0.85 similarity scores
- No real semantic understanding
- File-based storage issues
- Memory leaks with large datasets

### After (pgvector)
- Real semantic similarity using OpenAI embeddings
- Cosine distance calculations with `1 - (embedding <=> query)`
- Database-backed with proper indexing
- Scalable with PostgreSQL replication

## Usage Examples

### Store Content for Search
```python
from backend.services.pgvector_service import PgVectorService

vector_service = PgVectorService(db_session)
embedding_id = vector_service.store_content_embedding(
    user_id=1,
    content_id=123,
    content_text="AI and machine learning trends for 2025",
    metadata={"platform": "twitter", "engagement": 4.2}
)
```

### Search Similar Content
```python
results = vector_service.similarity_search_content(
    user_id=1,
    query_text="artificial intelligence trends",
    limit=5,
    similarity_threshold=0.7
)

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Content: {result['content_text'][:100]}...")
```

## Memory Types Supported

- `general` - General knowledge and insights
- `research` - Research findings and data
- `insight` - AI-generated insights and patterns
- `content` - High-performing content for inspiration

## Configuration

### Vector Dimensions
- Using `text-embedding-3-small` (1536 dimensions) for cost efficiency
- Can be upgraded to `text-embedding-3-large` (3072 dimensions) for better quality

### Similarity Thresholds
- `0.9+` - Very similar (near duplicates)
- `0.8-0.9` - Highly similar (same topic, different angle)
- `0.7-0.8` - Moderately similar (related topics)
- `0.6-0.7` - Somewhat similar (broad category match)
- `<0.6` - Not similar enough for recommendations

## Migration Checklist

- [x] Remove FAISS dependency from requirements.txt
- [x] Add pgvector to requirements.txt
- [x] Create pgvector service with OpenAI embeddings
- [x] Create production vector search API
- [x] Create production memory service
- [x] Add database migration for vector tables
- [x] Update router registry with production endpoints
- [x] Test build and syntax validation

## Next Steps

1. Run database migration: `alembic upgrade head`
2. Test with real data in development environment
3. Configure PostgreSQL with pgvector for production deployment
4. Remove legacy vector search endpoints after testing
5. Update frontend to use new vector search APIs