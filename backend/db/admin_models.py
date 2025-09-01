"""
Admin system database models
Separate admin authentication and user management system
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class AdminRole(str, enum.Enum):
    """Admin role types"""
    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                  # User management, settings
    MODERATOR = "moderator"          # User management only
    SUPPORT = "support"              # Read-only access


class AdminUser(Base):
    """
    Separate admin user table for administrative access
    """
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # Admin-specific fields
    role = Column(Enum(AdminRole), nullable=False, default=AdminRole.ADMIN)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Security fields
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=func.now())
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("admin_users.id"), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String, ForeignKey("admin_users.id"), nullable=True)
    
    # Relationships
    admin_sessions = relationship("AdminSession", back_populates="admin_user", cascade="all, delete-orphan")
    audit_logs = relationship("AdminAuditLog", back_populates="admin_user", cascade="all, delete-orphan")
    managed_users = relationship("UserManagement", back_populates="managed_by", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AdminUser(id={self.id}, email={self.email}, role={self.role.value})>"


class AdminSession(Base):
    """
    Track admin user sessions for security
    """
    __tablename__ = "admin_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    admin_user_id = Column(String, ForeignKey("admin_users.id"), nullable=False, index=True)
    session_token = Column(String, unique=True, nullable=False, index=True)
    refresh_token = Column(String, unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    
    # Session lifecycle
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    logout_at = Column(DateTime, nullable=True)
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="admin_sessions")
    
    def __repr__(self):
        return f"<AdminSession(id={self.id}, admin_user_id={self.admin_user_id}, active={self.is_active})>"


class UserManagement(Base):
    """
    Enhanced user management with admin controls
    """
    __tablename__ = "user_management"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # User API keys and secrets
    api_key = Column(String, unique=True, nullable=True, index=True)
    api_secret = Column(String, nullable=True)  # Encrypted
    api_key_created_at = Column(DateTime, nullable=True)
    api_key_last_used = Column(DateTime, nullable=True)
    api_key_usage_count = Column(Integer, default=0)
    
    # User limits and quotas
    monthly_request_limit = Column(Integer, default=1000)
    monthly_requests_used = Column(Integer, default=0)
    daily_request_limit = Column(Integer, default=100)
    daily_requests_used = Column(Integer, default=0)
    
    # User status management
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text, nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    suspension_expires = Column(DateTime, nullable=True)
    
    # Account verification
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Billing and subscription (future)
    subscription_tier = Column(String, default="free")
    subscription_expires = Column(DateTime, nullable=True)
    billing_customer_id = Column(String, nullable=True)
    
    # Admin tracking
    managed_by = relationship("AdminUser", back_populates="managed_users")
    managed_by_id = Column(String, ForeignKey("admin_users.id"), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="management_info")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_management_api_key', 'api_key'),
        Index('idx_user_management_user_id', 'user_id'),
        Index('idx_user_management_managed_by', 'managed_by_id'),
    )
    
    def __repr__(self):
        return f"<UserManagement(user_id={self.user_id}, api_key={self.api_key[:8] if self.api_key else None}...)>"


class AdminAuditLog(Base):
    """
    Comprehensive audit logging for admin actions
    """
    __tablename__ = "admin_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    admin_user_id = Column(String, ForeignKey("admin_users.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String, nullable=False, index=True)  # CREATE_USER, DELETE_USER, UPDATE_SETTINGS, etc.
    resource_type = Column(String, nullable=False)  # user, admin_user, settings, etc.
    resource_id = Column(String, nullable=True)
    
    # Action metadata
    details = Column(JSON, nullable=True)  # Additional action details
    old_values = Column(JSON, nullable=True)  # Previous values for updates
    new_values = Column(JSON, nullable=True)  # New values for updates
    
    # Request context
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String, nullable=True)  # For tracing
    
    # Status and results
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="audit_logs")
    
    # Indexes for querying
    __table_args__ = (
        Index('idx_audit_admin_action', 'admin_user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AdminAuditLog(id={self.id}, action={self.action}, admin_user_id={self.admin_user_id})>"


class SystemSettings(Base):
    """
    Global system settings manageable by admins
    """
    __tablename__ = "system_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    
    # Setting metadata
    description = Column(Text, nullable=True)
    setting_type = Column(String, nullable=False)  # string, integer, boolean, json, etc.
    is_public = Column(Boolean, default=False)  # Can regular users see this setting?
    is_readonly = Column(Boolean, default=False)  # Can only super admins modify?
    
    # Validation
    validation_rules = Column(JSON, nullable=True)  # JSON schema or validation rules
    default_value = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, ForeignKey("admin_users.id"), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String, ForeignKey("admin_users.id"), nullable=True)
    
    def __repr__(self):
        return f"<SystemSettings(key={self.key}, value={self.value})>"


class RegistrationKey(Base):
    """
    Registration keys generated by admins for new user registration
    """
    __tablename__ = "registration_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    key = Column(String, unique=True, nullable=False, index=True)  # The actual key users will enter
    
    # Key metadata
    description = Column(String, nullable=True)  # Optional description (e.g., "For company employees")
    max_uses = Column(Integer, default=1)  # How many times this key can be used
    current_uses = Column(Integer, default=0)  # How many times it has been used
    is_active = Column(Boolean, default=True)  # Can this key still be used?
    
    # Restrictions
    email_domain_restriction = Column(String, nullable=True)  # e.g., "@company.com"
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, ForeignKey("admin_users.id"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Track usage - DISABLED for open SaaS (no registration keys required)
    # users_registered = relationship("User", back_populates="registered_with_key", foreign_keys="User.registration_key_id")
    created_by_admin = relationship("AdminUser", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<RegistrationKey(key={self.key[:8]}..., uses={self.current_uses}/{self.max_uses})>"
    
    def is_valid(self) -> bool:
        """Check if this registration key can still be used"""
        if not self.is_active:
            return False
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def can_register_email(self, email: str) -> bool:
        """Check if this key allows registration for the given email"""
        if not self.is_valid():
            return False
        if self.email_domain_restriction:
            email_domain = email.split('@')[1] if '@' in email else ''
            if not email_domain.endswith(self.email_domain_restriction.lstrip('@')):
                return False
        return True


class ApiKeyRevocation(Base):
    """
    Track revoked API keys for security
    """
    __tablename__ = "api_key_revocations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    api_key = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Revocation details
    revoked_at = Column(DateTime, default=func.now(), nullable=False)
    revoked_by = Column(String, ForeignKey("admin_users.id"), nullable=False)
    reason = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Expiration (keys remain revoked until this date)
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ApiKeyRevocation(api_key={self.api_key[:8]}..., user_id={self.user_id})>"