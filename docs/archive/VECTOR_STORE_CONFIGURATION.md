# Vector Store Configuration

## Current Setup

The platform uses a **fallback vector implementation** for development and testing purposes. In production, we recommend using **pgvector** with PostgreSQL for better performance and scalability.

## FAISS Warning Explanation

You may see this warning in the logs:
```
FAISS not available, install faiss-cpu for better performance
FAISS not available, using fallback implementation
```

**This is intentional and not an error.** 

### Why FAISS is Not Installed

1. **Production uses pgvector**: For production deployments, we use PostgreSQL with the pgvector extension, which provides:
   - Native database integration
   - Better scalability
   - Persistent storage
   - No additional memory requirements

2. **Reduced memory footprint**: FAISS requires significant memory (2GB+), which can impact deployment costs on platforms like Render

3. **Simplified dependencies**: The fallback implementation works for basic vector operations without external dependencies

## Vector Store Options

### Option 1: Fallback Implementation (Current)
- ✅ No additional dependencies
- ✅ Works out of the box
- ✅ Low memory footprint
- ⚠️ Limited to basic similarity search
- ⚠️ In-memory only (not persistent)

### Option 2: PostgreSQL with pgvector (Recommended for Production)
- ✅ Native database integration
- ✅ Persistent storage
- ✅ Scalable
- ✅ Production-ready
- ⚠️ Requires PostgreSQL extension

To enable pgvector:
1. Install the pgvector extension in your PostgreSQL database
2. The system will automatically detect and use it

### Option 3: FAISS (Optional for High-Performance)
- ✅ Highest performance for similarity search
- ✅ Advanced indexing algorithms
- ⚠️ 2GB+ memory requirement
- ⚠️ Additional dependency

To enable FAISS (if needed):
```bash
pip install faiss-cpu
```

## Configuration

The vector store automatically selects the best available backend:
1. Checks for FAISS availability
2. Falls back to in-memory implementation
3. Uses pgvector when database is PostgreSQL with extension

No configuration changes needed - the system adapts automatically.

## Performance Impact

For most use cases, the performance difference is negligible:
- **Content similarity**: Works well with fallback
- **Embedding search**: Adequate for < 10,000 vectors
- **Research automation**: No noticeable impact

## Recommendations

- **Development**: Use fallback implementation (current setup)
- **Production**: Use PostgreSQL with pgvector
- **High-volume**: Consider FAISS if processing millions of vectors

The warning can be safely ignored for normal operation.