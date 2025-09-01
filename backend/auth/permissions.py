"""
Role-based access control (RBAC) permission system
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.db.models import User
from backend.db.multi_tenant_models import (
    Organization, Team, Role, Permission, UserOrganizationRole, user_teams
)
import logging

logger = logging.getLogger(__name__)


class PermissionChecker:
    """
    Centralized permission checking system for multi-tenant RBAC
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def user_has_permission(
        self, 
        user: User, 
        permission_name: str, 
        organization_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has a specific permission within an organization/team context
        
        Args:
            user: User object
            permission_name: Permission name like 'content.create', 'users.read'
            organization_id: Optional organization context
            team_id: Optional team context
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # Super admin always has all permissions
            if user.is_superuser:
                logger.debug(f"Super admin {user.id} granted permission {permission_name}")
                return True
            
            # If no organization context, use user's default organization
            if not organization_id and user.default_organization_id:
                organization_id = user.default_organization_id
            
            if not organization_id:
                logger.warning(f"No organization context for permission check: user={user.id}, permission={permission_name}")
                return False
            
            # Get user's role in the organization
            user_org_role = self.db.query(UserOrganizationRole).filter(
                and_(
                    UserOrganizationRole.user_id == user.id,
                    UserOrganizationRole.organization_id == organization_id,
                    UserOrganizationRole.is_active == True
                )
            ).first()
            
            if not user_org_role:
                logger.debug(f"User {user.id} has no role in organization {organization_id}")
                return False
            
            # Check if the role has the required permission
            permission_exists = self.db.query(Permission).join(
                Permission.roles
            ).filter(
                and_(
                    Role.id == user_org_role.role_id,
                    Permission.name == permission_name
                )
            ).first()
            
            has_permission = permission_exists is not None
            logger.debug(f"Permission check: user={user.id}, permission={permission_name}, org={organization_id}, result={has_permission}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission {permission_name} for user {user.id}: {e}")
            return False
    
    def user_has_any_permission(
        self, 
        user: User, 
        permission_names: List[str], 
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has any of the specified permissions
        """
        return any(
            self.user_has_permission(user, perm, organization_id) 
            for perm in permission_names
        )
    
    def user_has_all_permissions(
        self, 
        user: User, 
        permission_names: List[str], 
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has all of the specified permissions
        """
        return all(
            self.user_has_permission(user, perm, organization_id) 
            for perm in permission_names
        )
    
    def get_user_permissions(
        self, 
        user: User, 
        organization_id: Optional[str] = None
    ) -> List[str]:
        """
        Get all permissions for a user in an organization context
        
        Returns:
            List[str]: List of permission names
        """
        try:
            # Super admin has all permissions
            if user.is_superuser:
                all_permissions = self.db.query(Permission.name).all()
                return [perm.name for perm in all_permissions]
            
            # If no organization context, use user's default organization
            if not organization_id and user.default_organization_id:
                organization_id = user.default_organization_id
            
            if not organization_id:
                return []
            
            # Get user's role in the organization
            user_org_role = self.db.query(UserOrganizationRole).filter(
                and_(
                    UserOrganizationRole.user_id == user.id,
                    UserOrganizationRole.organization_id == organization_id,
                    UserOrganizationRole.is_active == True
                )
            ).first()
            
            if not user_org_role:
                return []
            
            # Get all permissions for the user's role
            permissions = self.db.query(Permission.name).join(
                Permission.roles
            ).filter(
                Role.id == user_org_role.role_id
            ).all()
            
            return [perm.name for perm in permissions]
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user.id}: {e}")
            return []
    
    def get_user_role_in_organization(
        self, 
        user: User, 
        organization_id: str
    ) -> Optional[str]:
        """
        Get user's role name in a specific organization
        
        Returns:
            Optional[str]: Role name or None if no role
        """
        try:
            user_org_role = self.db.query(UserOrganizationRole).join(
                Role
            ).filter(
                and_(
                    UserOrganizationRole.user_id == user.id,
                    UserOrganizationRole.organization_id == organization_id,
                    UserOrganizationRole.is_active == True
                )
            ).first()
            
            if user_org_role:
                role = self.db.query(Role).filter(Role.id == user_org_role.role_id).first()
                return role.name if role else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting role for user {user.id} in org {organization_id}: {e}")
            return None
    
    def get_user_organizations(self, user: User) -> List[Dict[str, Any]]:
        """
        Get all organizations where user has access
        
        Returns:
            List[Dict]: Organization info with user's role
        """
        try:
            organizations = self.db.query(
                Organization.id,
                Organization.name,
                Organization.slug,
                Role.name.label('role_name'),
                Role.display_name.label('role_display_name')
            ).join(
                UserOrganizationRole, Organization.id == UserOrganizationRole.organization_id
            ).join(
                Role, UserOrganizationRole.role_id == Role.id
            ).filter(
                and_(
                    UserOrganizationRole.user_id == user.id,
                    UserOrganizationRole.is_active == True
                )
            ).all()
            
            return [
                {
                    'id': org.id,
                    'name': org.name,
                    'slug': org.slug,
                    'role': org.role_name,
                    'role_display_name': org.role_display_name
                }
                for org in organizations
            ]
            
        except Exception as e:
            logger.error(f"Error getting organizations for user {user.id}: {e}")
            return []
    
    def user_can_access_organization(
        self, 
        user: User, 
        organization_id: str
    ) -> bool:
        """
        Check if user has any access to an organization
        """
        try:
            if user.is_superuser:
                return True
            
            user_org_role = self.db.query(UserOrganizationRole).filter(
                and_(
                    UserOrganizationRole.user_id == user.id,
                    UserOrganizationRole.organization_id == organization_id,
                    UserOrganizationRole.is_active == True
                )
            ).first()
            
            return user_org_role is not None
            
        except Exception as e:
            logger.error(f"Error checking organization access for user {user.id}: {e}")
            return False
    
    def is_organization_owner(
        self, 
        user: User, 
        organization_id: str
    ) -> bool:
        """
        Check if user is the owner of an organization
        """
        try:
            organization = self.db.query(Organization).filter(
                and_(
                    Organization.id == organization_id,
                    Organization.owner_id == user.id
                )
            ).first()
            
            return organization is not None
            
        except Exception as e:
            logger.error(f"Error checking organization ownership for user {user.id}: {e}")
            return False


# Utility functions for common permission patterns
def require_permission(permission_name: str, organization_id: Optional[str] = None):
    """
    Decorator to require a specific permission for an endpoint
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used with dependency injection in FastAPI
            # Implementation depends on how we structure the API dependencies
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_content_access(
    user: User, 
    content_user_id: int, 
    organization_id: str,
    permission_checker: PermissionChecker
) -> bool:
    """
    Check if user can access content (either owns it or has permission)
    """
    # User can access their own content
    if user.id == content_user_id:
        return True
    
    # Or if they have content read permission in the organization
    return permission_checker.user_has_permission(
        user, 'content.read', organization_id
    )


def check_admin_access(
    user: User, 
    organization_id: str,
    permission_checker: PermissionChecker
) -> bool:
    """
    Check if user has administrative access in organization
    """
    if user.is_superuser:
        return True
    
    return permission_checker.user_has_any_permission(
        user, 
        ['organizations.update', 'users.create', 'users.update'],
        organization_id
    )