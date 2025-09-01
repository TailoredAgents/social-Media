"""
User Settings API endpoints
Handles user preferences, brand settings, and configuration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
import logging

from backend.db.database import get_db
from backend.db.models import User, UserSetting
from backend.core.security import JWTHandler
from backend.auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

# Authentication setup
security = HTTPBearer()
jwt_handler = JWTHandler()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Verify JWT token
        payload = jwt_handler.verify_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

router = APIRouter(prefix="/api/user-settings", tags=["user-settings"])

# Request/Response Models
class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    
    # Brand settings
    brand_name: Optional[str] = None
    brand_voice: str = "professional"
    primary_color: str = "#3b82f6"
    secondary_color: str = "#10b981"
    logo_url: Optional[str] = None
    
    # Industry & Visual Style Settings
    industry_type: str = "general"
    visual_style: str = "modern"
    image_mood: List[str] = ["professional", "clean"]
    brand_keywords: List[str] = []
    avoid_list: List[str] = []
    
    # Image Generation Preferences
    enable_auto_image_generation: bool = True
    preferred_image_style: Dict[str, str] = {"lighting": "natural", "composition": "rule_of_thirds", "color_temperature": "neutral"}
    custom_image_prompts: Dict[str, str] = {}
    image_quality: str = "high"
    image_aspect_ratio: str = "1:1"
    
    # Content preferences  
    content_frequency: int = 3
    preferred_platforms: List[str] = ["twitter", "instagram"]
    posting_times: Dict[str, str] = {"twitter": "09:00", "instagram": "10:00"}
    
    # AI settings
    creativity_level: float = 0.7
    enable_images: bool = True
    enable_repurposing: bool = True
    
    # Autonomous mode settings
    enable_autonomous_mode: bool = False
    auto_response_enabled: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class UpdateUserSettingsRequest(BaseModel):
    # Brand settings
    brand_name: Optional[str] = None
    brand_voice: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    logo_url: Optional[str] = None
    
    # Industry & Visual Style Settings  
    industry_type: Optional[str] = None
    visual_style: Optional[str] = None
    image_mood: Optional[List[str]] = None
    brand_keywords: Optional[List[str]] = None
    avoid_list: Optional[List[str]] = None
    
    # Image Generation Preferences
    enable_auto_image_generation: Optional[bool] = None
    preferred_image_style: Optional[Dict[str, str]] = None
    custom_image_prompts: Optional[Dict[str, str]] = None
    image_quality: Optional[str] = None
    image_aspect_ratio: Optional[str] = None
    
    # Content preferences
    content_frequency: Optional[int] = Field(None, ge=1, le=20)
    preferred_platforms: Optional[List[str]] = None
    posting_times: Optional[Dict[str, str]] = None
    
    # AI settings
    creativity_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    enable_images: Optional[bool] = None
    enable_repurposing: Optional[bool] = None
    
    # Autonomous mode settings
    enable_autonomous_mode: Optional[bool] = None
    auto_response_enabled: Optional[bool] = None

def get_or_create_user_settings(db: Session, user_id: int) -> UserSetting:
    """Get existing user settings or create default settings"""
    settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    if not settings:
        # Create default settings
        settings = UserSetting(
            user_id=user_id,
            brand_voice="professional",
            primary_color="#3b82f6",
            content_frequency=3,
            preferred_platforms=["twitter", "instagram"],
            posting_times={"twitter": "09:00", "instagram": "10:00"},
            creativity_level=0.7,
            enable_images=True,
            enable_repurposing=True,
            enable_autonomous_mode=False,
            auto_response_enabled=False
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info(f"Created default user settings for user {user_id}")
    
    return settings

@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's settings"""
    try:
        settings = get_or_create_user_settings(db, current_user.id)
        
        # Convert to response model format
        return UserSettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            brand_name=settings.brand_name,
            brand_voice=settings.brand_voice or "professional",
            primary_color=settings.primary_color or "#3b82f6",
            logo_url=settings.logo_url,
            content_frequency=settings.content_frequency or 3,
            preferred_platforms=settings.preferred_platforms or ["twitter", "instagram"],
            posting_times=settings.posting_times or {"twitter": "09:00", "instagram": "10:00"},
            creativity_level=settings.creativity_level or 0.7,
            enable_images=settings.enable_images if settings.enable_images is not None else True,
            enable_repurposing=settings.enable_repurposing if settings.enable_repurposing is not None else True,
            enable_autonomous_mode=getattr(settings, 'enable_autonomous_mode', False),
            auto_response_enabled=getattr(settings, 'auto_response_enabled', False)
        )
        
    except Exception as e:
        logger.error(f"Error getting user settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user settings"
        )

@router.put("/", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UpdateUserSettingsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's settings"""
    try:
        settings = get_or_create_user_settings(db, current_user.id)
        
        # Update only provided fields
        update_data = settings_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        
        logger.info(f"Updated user settings for user {current_user.id}: {list(update_data.keys())}")
        
        # Return updated settings
        return UserSettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            brand_name=settings.brand_name,
            brand_voice=settings.brand_voice or "professional",
            primary_color=settings.primary_color or "#3b82f6",
            logo_url=settings.logo_url,
            content_frequency=settings.content_frequency or 3,
            preferred_platforms=settings.preferred_platforms or ["twitter", "instagram"],
            posting_times=settings.posting_times or {"twitter": "09:00", "instagram": "10:00"},
            creativity_level=settings.creativity_level or 0.7,
            enable_images=settings.enable_images if settings.enable_images is not None else True,
            enable_repurposing=settings.enable_repurposing if settings.enable_repurposing is not None else True,
            enable_autonomous_mode=getattr(settings, 'enable_autonomous_mode', False),
            auto_response_enabled=getattr(settings, 'auto_response_enabled', False)
        )
        
    except Exception as e:
        logger.error(f"Error updating user settings for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )

@router.get("/defaults")
async def get_default_settings():
    """Get default settings structure (for new users or reference)"""
    return {
        "brand_voice": "professional",
        "primary_color": "#3b82f6",
        "content_frequency": 3,
        "preferred_platforms": ["twitter", "instagram"],
        "posting_times": {"twitter": "09:00", "instagram": "10:00"},
        "creativity_level": 0.7,
        "enable_images": True,
        "enable_repurposing": True,
        "enable_autonomous_mode": False,
        "auto_response_enabled": False
    }