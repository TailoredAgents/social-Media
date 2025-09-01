# Service initialization - lazy loading to reduce startup memory
# Don't import memory_service at startup to avoid FAISS loading
# Services will be imported on-demand

__all__ = []