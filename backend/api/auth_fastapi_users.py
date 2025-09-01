"""
FastAPI Users authentication routes
Production-ready authentication without OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from backend.auth.fastapi_users_config import (
    auth_backend,
    fastapi_users,
    current_active_user,
    UserTable,
)

# User schemas
class UserRead(schemas.BaseUser[int]):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    tier: str = "base"
    auth_provider: str = "local"

class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None

# Create router
router = APIRouter(prefix="/api/auth-legacy", tags=["authentication-legacy"])

# Include FastAPI Users auth routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)

# Additional custom endpoints
@router.get("/me", response_model=UserRead)
async def get_current_user(user: UserTable = Depends(current_active_user)):
    """Get current authenticated user"""
    return user

@router.post("/logout")
async def logout(user: UserTable = Depends(current_active_user)):
    """Logout current user (client should remove token)"""
    return {"message": "Successfully logged out"}

@router.get("/check")
async def check_auth(user: UserTable = Depends(current_active_user)):
    """Check if user is authenticated"""
    return {
        "authenticated": True,
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
    }

# Password strength validation endpoint
class PasswordStrengthRequest(BaseModel):
    password: str = Field(..., min_length=8)

@router.post("/password-strength")
async def check_password_strength(request: PasswordStrengthRequest):
    """Check password strength"""
    password = request.password
    strength = "weak"
    score = 0
    
    # Check length
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Check for uppercase
    if any(c.isupper() for c in password):
        score += 1
    
    # Check for lowercase
    if any(c.islower() for c in password):
        score += 1
    
    # Check for digits
    if any(c.isdigit() for c in password):
        score += 1
    
    # Check for special characters
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    
    if score >= 5:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    
    return {
        "strength": strength,
        "score": score,
        "max_score": 6,
    }