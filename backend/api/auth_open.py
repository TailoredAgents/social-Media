"""
Open SaaS Authentication API - No registration keys required
Includes email verification, password reset, and OAuth support
"""
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from backend.db.database import get_db
from backend.db.models import User
from backend.core.security import JWTHandler
from backend.services.email_service import email_methods
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
jwt_handler = JWTHandler()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request/Response Models
class OpenRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    accept_terms: bool = Field(..., description="User must accept terms of service")

class EmailVerificationRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    username: str
    email_verified: bool
    tier: str
    is_superuser: bool

# Helper Functions
def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

def generate_password_reset_token() -> str:
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def get_current_time() -> datetime:
    """Get current UTC time with timezone awareness"""
    return datetime.now(timezone.utc)

def token_is_expired(sent_at: datetime, hours: int) -> bool:
    """Check if a token has expired"""
    if not sent_at:
        return True
    expiry_time = sent_at + timedelta(hours=hours)
    return get_current_time() > expiry_time

# Endpoints
@router.post("/register", response_model=TokenResponse)
async def open_register(
    request: OpenRegisterRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Open registration - no registration key required
    Sends email verification after signup
    """
    
    # Check if registration is enabled
    if not settings.enable_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently closed. Please contact an administrator."
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == request.email) | (User.username == request.username)
    ).first()
    
    if existing_user:
        if existing_user.email == request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if terms were accepted
    if not request.accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms of service"
        )
    
    # Create new user
    hashed_password = jwt_handler.hash_password(request.password)
    verification_token = generate_verification_token()
    
    # Check if this is the first user (make them superuser)
    user_count = db.query(User).count()
    is_first_user = user_count == 0
    
    new_user = User(
        email=request.email,
        username=request.username,
        full_name=request.full_name or request.username,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=is_first_user,  # First user becomes admin
        email_verified=not settings.require_email_verification,  # Auto-verify if verification disabled
        email_verification_token=verification_token if settings.require_email_verification else None,
        email_verification_sent_at=get_current_time() if settings.require_email_verification else None,
        tier="free",  # Start with free tier
        subscription_status="free",
        auth_provider="local"
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    # Send verification email in background only if required
    if settings.require_email_verification:
        background_tasks.add_task(
            email_methods.send_verification_email,
            new_user.email,
            new_user.username,
            verification_token
        )
    
    # Generate JWT access token and refresh token
    try:
        access_token = jwt_handler.create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )
        
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )
    except Exception as e:
        logger.error(f"Failed to create JWT tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access token: {str(e)}"
        )
    
    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="none",  # Allow cross-origin cookies (frontend ↔ api domains)
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        path="/"
    )
    
    logger.info(f"New user registered: {new_user.email} (First user: {is_first_user})")
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        email_verified=new_user.email_verified,
        tier=new_user.tier,
        is_superuser=new_user.is_superuser
    )

@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify user's email address with token from email"""
    
    user = db.query(User).filter(
        User.email_verification_token == request.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    # Check if token is expired (24 hours)
    if token_is_expired(user.email_verification_sent_at, 24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one."
        )
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    
    db.commit()
    
    logger.info(f"Email verified for user: {user.email}")
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend email verification link"""
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Check rate limiting (max 1 request per hour)
    if user.email_verification_sent_at:
        time_since_last = get_current_time() - user.email_verification_sent_at
        if time_since_last < timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification email"
            )
    
    # Generate new token
    verification_token = generate_verification_token()
    user.email_verification_token = verification_token
    user.email_verification_sent_at = get_current_time()
    
    db.commit()
    
    # Send email in background
    background_tasks.add_task(
        email_methods.send_verification_email,
        user.email,
        user.username,
        verification_token
    )
    
    return {"message": "Verification email sent"}

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset link"""
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Check rate limiting (max 1 request per hour)
    if user.password_reset_sent_at:
        time_since_last = get_current_time() - user.password_reset_sent_at
        if time_since_last < timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another reset email"
            )
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    user.password_reset_token = reset_token
    user.password_reset_sent_at = get_current_time()
    
    db.commit()
    
    # Send reset email in background
    background_tasks.add_task(
        email_methods.send_password_reset_email,
        user.email,
        user.username,
        reset_token
    )
    
    logger.info(f"Password reset requested for: {user.email}")
    
    return {"message": "Password reset link sent"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password with token from email"""
    
    user = db.query(User).filter(
        User.password_reset_token == request.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Check if token is expired (2 hours)
    if token_is_expired(user.password_reset_sent_at, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Update password
    hashed_password = jwt_handler.hash_password(request.new_password)
    user.hashed_password = hashed_password
    user.password_reset_token = None
    user.password_reset_sent_at = None
    
    db.commit()
    
    logger.info(f"Password reset successful for: {user.email}")
    
    return {"message": "Password reset successfully"}

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login with email and password - email verification recommended but not required"""
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated"
        )
    
    # Verify password
    if not jwt_handler.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT access token and refresh token
    access_token = jwt_handler.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="none",  # Allow cross-origin cookies (frontend ↔ api domains)
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        path="/"
    )
    
    logger.info(f"User logged in: {user.email} (Verified: {user.email_verified})")
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        username=user.username,
        email_verified=user.email_verified,
        tier=user.tier,
        is_superuser=user.is_superuser
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from HTTP-only cookie or Authorization header
    Supports backwards compatibility during migration
    """
    # Try to get refresh token from cookie first (new method)
    refresh_token = request.cookies.get("refresh_token")
    
    # Fall back to Authorization header for backwards compatibility
    if not refresh_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # During transition, accept access tokens and create new refresh tokens
            access_token = auth_header.split(" ")[1]
            try:
                # Verify the access token and extract user info
                payload = jwt_handler.verify_token(access_token)
                user_id = int(payload.get("sub"))
                
                # Get user from database
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                # Generate new tokens (both access and refresh)
                new_access_token = jwt_handler.create_access_token(
                    data={"sub": str(user.id), "email": user.email}
                )
                
                new_refresh_token = jwt_handler.create_refresh_token(
                    data={"sub": str(user.id), "email": user.email}
                )
                
                # Set refresh token in HTTP-only cookie for future requests
                response.set_cookie(
                    key="refresh_token",
                    value=new_refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=7 * 24 * 60 * 60,
                    path="/"
                )
                
                logger.info(f"Token refreshed via Authorization header (migration): {user.email}")
                
                return TokenResponse(
                    access_token=new_access_token,
                    user_id=user.id,
                    email=user.email,
                    username=user.username,
                    email_verified=user.email_verified,
                    tier=user.tier,
                    is_superuser=user.is_superuser
                )
                
            except Exception as e:
                logger.error(f"Failed to refresh via Authorization header: {e}")
                # Continue to error below
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookie or Authorization header"
        )
    
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(refresh_token)
        
        # Ensure this is a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        new_access_token = jwt_handler.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Generate new refresh token for rotation (security best practice)
        new_refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Set new refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="none",  # Allow cross-origin cookies (frontend ↔ api domains)
            max_age=7 * 24 * 60 * 60,  # 7 days in seconds
            path="/"
        )
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return TokenResponse(
            access_token=new_access_token,
            user_id=user.id,
            email=user.email,
            username=user.username,
            email_verified=user.email_verified,
            tier=user.tier,
            is_superuser=user.is_superuser
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

@router.get("/me", response_model=TokenResponse)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current user information from JWT token
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verify token
        payload = jwt_handler.verify_token(token)
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return TokenResponse(
            access_token=token,  # Return the same token
            user_id=user.id,
            email=user.email,
            username=user.username,
            email_verified=user.email_verified,
            tier=user.tier,
            is_superuser=user.is_superuser
        )
        
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears the refresh token cookie
    Frontend should discard the access token
    """
    # Clear the refresh token cookie with same attributes as when set
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="none"  # Must match the original cookie attributes
    )
    
    return {"message": "Logout successful", "status": "success"}