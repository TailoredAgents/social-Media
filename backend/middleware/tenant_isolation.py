"""
Tenant isolation middleware to ensure data separation between organizations
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from backend.auth.permissions import PermissionChecker
from backend.db.models import User
from backend.db.multi_tenant_models import Organization
import logging

logger = logging.getLogger(__name__)


class TenantContext:
    """
    Container for current tenant context in a request
    """
    def __init__(
        self, 
        organization_id: Optional[str] = None,
        organization: Optional[Organization] = None,
        user: Optional[User] = None
    ):
        self.organization_id = organization_id
        self.organization = organization
        self.user = user
        self.permissions_checked = False
        self._permission_checker: Optional[PermissionChecker] = None
    
    @property
    def permission_checker(self) -> Optional[PermissionChecker]:
        return self._permission_checker
    
    def set_permission_checker(self, db: Session):
        """Set the permission checker with database session"""
        self._permission_checker = PermissionChecker(db)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if current user has permission in current organization context"""
        if not self.user or not self._permission_checker:
            return False
        
        return self._permission_checker.user_has_permission(
            self.user, 
            permission_name, 
            self.organization_id
        )
    
    def require_permission(self, permission_name: str):
        """Raise exception if user doesn't have permission"""
        if not self.has_permission(permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_name} required"
            )
    
    def ensure_organization_access(self):
        """Ensure user has access to current organization"""
        if not self.user or not self._permission_checker:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not self.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization context required"
            )
        
        if not self._permission_checker.user_can_access_organization(
            self.user, self.organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization"
            )


class TenantIsolationMiddleware:
    """
    Middleware to extract and validate tenant context from requests
    """
    
    def __init__(self):
        self.tenant_header = "X-Organization-ID"
        self.tenant_query_param = "org_id"
    
    async def __call__(self, request: Request, call_next):
        """
        Process request to extract tenant context
        """
        # Extract organization ID from various sources
        organization_id = self._extract_organization_id(request)
        
        # Create tenant context and attach to request
        tenant_context = TenantContext(organization_id=organization_id)
        request.state.tenant_context = tenant_context
        
        # Continue with request processing
        response = await call_next(request)
        
        return response
    
    def _extract_organization_id(self, request: Request) -> Optional[str]:
        """
        Extract organization ID from request headers, query params, or path
        
        Priority:
        1. X-Organization-ID header
        2. org_id query parameter
        3. organization_id in path parameters
        4. org_id in path parameters
        """
        # Check header first
        org_id = request.headers.get(self.tenant_header)
        if org_id:
            logger.debug(f"Organization ID from header: {org_id}")
            return org_id
        
        # Check query parameters
        org_id = request.query_params.get(self.tenant_query_param)
        if org_id:
            logger.debug(f"Organization ID from query param: {org_id}")
            return org_id
        
        # Check path parameters (if available)
        if hasattr(request, 'path_params'):
            org_id = request.path_params.get('organization_id') or request.path_params.get('org_id')
            if org_id:
                logger.debug(f"Organization ID from path param: {org_id}")
                return org_id
        
        logger.debug("No organization ID found in request")
        return None


def get_tenant_context(request: Request) -> TenantContext:
    """
    Get tenant context from request state
    """
    if not hasattr(request.state, 'tenant_context'):
        # Create empty context if not set by middleware
        request.state.tenant_context = TenantContext()
    
    return request.state.tenant_context


def require_organization_context(request: Request) -> TenantContext:
    """
    Get tenant context and ensure organization is set
    """
    tenant_context = get_tenant_context(request)
    
    if not tenant_context.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required. Provide X-Organization-ID header or org_id parameter."
        )
    
    return tenant_context


def setup_tenant_context(
    request: Request, 
    user: User, 
    db: Session,
    organization_id: Optional[str] = None
) -> TenantContext:
    """
    Setup complete tenant context with user and permission checker
    """
    tenant_context = get_tenant_context(request)
    
    # Set organization ID if provided
    if organization_id:
        tenant_context.organization_id = organization_id
    
    # If no organization context, use user's default
    if not tenant_context.organization_id and user.default_organization_id:
        tenant_context.organization_id = user.default_organization_id
    
    # Set user and permission checker
    tenant_context.user = user
    tenant_context.set_permission_checker(db)
    
    # Load organization details if we have an ID
    if tenant_context.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == tenant_context.organization_id
        ).first()
        tenant_context.organization = organization
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {tenant_context.organization_id} not found"
            )
    
    return tenant_context


# Utility functions for common tenant operations
def filter_by_organization(query, model_class, organization_id: str):
    """
    Add organization filter to SQLAlchemy query
    
    Assumes model has organization_id field
    """
    if hasattr(model_class, 'organization_id'):
        return query.filter(model_class.organization_id == organization_id)
    elif hasattr(model_class, 'user_id'):
        # For user-owned resources, filter by users in organization
        from backend.db.multi_tenant_models import UserOrganizationRole
        return query.join(
            UserOrganizationRole, 
            model_class.user_id == UserOrganizationRole.user_id
        ).filter(
            UserOrganizationRole.organization_id == organization_id,
            UserOrganizationRole.is_active == True
        )
    else:
        logger.warning(f"Model {model_class.__name__} has no organization relationship")
        return query


def ensure_user_in_organization(
    user: User, 
    organization_id: str, 
    db: Session
) -> bool:
    """
    Verify user belongs to organization
    """
    from backend.db.multi_tenant_models import UserOrganizationRole
    
    if user.is_superuser:
        return True
    
    user_org_role = db.query(UserOrganizationRole).filter(
        UserOrganizationRole.user_id == user.id,
        UserOrganizationRole.organization_id == organization_id,
        UserOrganizationRole.is_active == True
    ).first()
    
    return user_org_role is not None


def get_user_default_organization(user: User, db: Session) -> Optional[str]:
    """
    Get user's default organization ID
    """
    if user.default_organization_id:
        return user.default_organization_id
    
    # If no default set, get first organization user belongs to
    from backend.db.multi_tenant_models import UserOrganizationRole
    
    user_org_role = db.query(UserOrganizationRole).filter(
        UserOrganizationRole.user_id == user.id,
        UserOrganizationRole.is_active == True
    ).first()
    
    return user_org_role.organization_id if user_org_role else None


def create_personal_organization(user: User, db: Session) -> Organization:
    """
    Create a personal organization for a new user
    """
    from backend.db.multi_tenant_models import Organization, UserOrganizationRole, Role
    import uuid
    
    # Create organization
    organization = Organization(
        id=str(uuid.uuid4()),
        name=f"{user.full_name or user.username}'s Organization",
        slug=f"{user.username}-org",
        description="Personal organization",
        plan_type="starter",
        max_users=1,
        max_teams=1,
        max_social_accounts=3,
        owner_id=user.id
    )
    
    db.add(organization)
    db.flush()  # Get the ID
    
    # Set as user's default organization
    user.default_organization_id = organization.id
    
    # Assign user as organization owner
    org_owner_role = db.query(Role).filter(Role.name == 'org_owner').first()
    if org_owner_role:
        user_org_role = UserOrganizationRole(
            id=str(uuid.uuid4()),
            user_id=user.id,
            organization_id=organization.id,
            role_id=org_owner_role.id,
            assigned_by_id=user.id,  # Self-assigned
            is_active=True
        )
        db.add(user_org_role)
    
    db.commit()
    
    logger.info(f"Created personal organization {organization.id} for user {user.id}")
    return organization