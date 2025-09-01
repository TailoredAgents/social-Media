"""
FastAPI Users configuration with SQLAlchemy
Production-ready authentication without OAuth
"""
import os
from typing import Optional, AsyncGenerator
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.database import Base, get_db
from backend.core.config import settings

# User database model for FastAPI Users
class UserTable(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    tier = Column(String, default="base")
    auth_provider = Column(String, default="local")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create async engine for FastAPI Users
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserTable)

# User manager configuration
class UserManager(IntegerIDMixin, BaseUserManager[UserTable, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    
    async def on_after_register(self, user: UserTable, request: Optional[Request] = None):
        """Called after a user registers"""
        print(f"User {user.id} has registered with email {user.email}")
    
    async def on_after_forgot_password(
        self, user: UserTable, token: str, request: Optional[Request] = None
    ):
        """Called after forgot password request"""
        print(f"User {user.id} has forgot their password. Reset token: {token}")
        
        # Send password reset email
        try:
            from backend.services.email_service import email_service, EmailTemplates
            
            # Generate reset URL (this should match your frontend route)
            if request:
                base_url = f"{request.url.scheme}://{request.url.netloc}"
            else:
                base_url = "https://yourdomain.com"  # Fallback - update with your domain
            
            reset_url = f"{base_url}/reset-password?token={token}"
            
            # Create email from template
            email_message = EmailTemplates.password_reset(reset_url, user.full_name or user.username)
            email_message.to = user.email
            
            # Send email
            result = await email_service.send_email(email_message)
            
            if result["status"] == "success":
                print(f"Password reset email sent successfully to {user.email}")
            else:
                print(f"Failed to send password reset email to {user.email}: {result.get('message')}")
                
        except Exception as e:
            print(f"Error sending password reset email to {user.email}: {str(e)}")
    
    async def on_after_request_verify(
        self, user: UserTable, token: str, request: Optional[Request] = None
    ):
        """Called after verification request"""
        print(f"Verification requested for user {user.id}. Verification token: {token}")
        
        # Send verification email
        try:
            from backend.services.email_service import email_service, EmailMessage
            
            # Generate verification URL (this should match your frontend route)
            if request:
                base_url = f"{request.url.scheme}://{request.url.netloc}"
            else:
                base_url = "https://yourdomain.com"  # Fallback - update with your domain
            
            verify_url = f"{base_url}/verify-email?token={token}"
            
            # Create verification email
            subject = "Verify Your Email Address"
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Welcome to Social Media Agent!</h2>
                <p>Hi {user.full_name or user.username},</p>
                <p>Please verify your email address by clicking the button below:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background-color: #007cba; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                        Verify Email Address
                    </a>
                </p>
                <p>If you didn't create an account, please ignore this email.</p>
                <p>Best regards,<br>The Social Media Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Hi {user.full_name or user.username},
            
            Please verify your email address by clicking the link below:
            {verify_url}
            
            If you didn't create an account, please ignore this email.
            
            Best regards,
            The Social Media Team
            """
            
            email_message = EmailMessage(
                to=user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            # Send email
            result = await email_service.send_email(email_message)
            
            if result["status"] == "success":
                print(f"Verification email sent successfully to {user.email}")
            else:
                print(f"Failed to send verification email to {user.email}: {result.get('message')}")
                
        except Exception as e:
            print(f"Error sending verification email to {user.email}: {str(e)}")
    
    async def on_after_update(
        self, user: UserTable, update_dict: dict, request: Optional[Request] = None
    ):
        """Called after a user updates their profile"""
        print(f"User {user.id} has been updated with {update_dict}")
    
    async def on_after_login(
        self, user: UserTable, request: Optional[Request] = None
    ):
        """Called after successful login"""
        print(f"User {user.id} logged in successfully")

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# JWT Strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=3600,  # 1 hour access token
    )

# Authentication backend
bearer_transport = BearerTransport(tokenUrl="/api/auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPIUsers instance
fastapi_users = FastAPIUsers[UserTable, int](
    get_user_manager,
    [auth_backend],
)

# Dependency shortcuts
current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)