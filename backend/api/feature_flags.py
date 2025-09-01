from fastapi import APIRouter
from backend.core.feature_flags import feature_flags

router = APIRouter(prefix="/api/feature-flags", tags=["feature-flags"])

@router.get("/")
def get_flags():
    """Get all feature flags (read-only)"""
    return feature_flags()