"""
Unit tests for tenant isolation middleware
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request, HTTPException

from backend.middleware.tenant_isolation import (
    TenantContext, TenantIsolationMiddleware, get_tenant_context,
    require_organization_context, setup_tenant_context, 
    filter_by_organization, ensure_user_in_organization,
    get_user_default_organization, create_personal_organization
)
from backend.db.models import User
from backend.db.multi_tenant_models import Organization, UserOrganizationRole


class TestTenantContext:
    """Test the TenantContext class"""
    
    def test_tenant_context_creation(self, test_organization, test_user_with_org):
        """Test creating a tenant context"""
        context = TenantContext(
            organization_id=test_organization.id,
            organization=test_organization,
            user=test_user_with_org
        )
        
        assert context.organization_id == test_organization.id
        assert context.organization == test_organization
        assert context.user == test_user_with_org
        assert context.permissions_checked is False
        assert context.permission_checker is None
    
    def test_set_permission_checker(self, db_session, mock_tenant_context):
        """Test setting permission checker"""
        context = TenantContext()
        context.set_permission_checker(db_session)
        
        assert context.permission_checker is not None
    
    def test_has_permission(self, mock_tenant_context):
        """Test permission checking through tenant context"""
        # Mock permission checker
        mock_tenant_context._permission_checker.user_has_permission.return_value = True
        
        result = mock_tenant_context.has_permission("test.permission")
        
        assert result is True
        mock_tenant_context._permission_checker.user_has_permission.assert_called_once()
    
    def test_has_permission_no_user(self, db_session):
        """Test permission checking without user"""
        context = TenantContext()
        context.set_permission_checker(db_session)
        
        result = context.has_permission("test.permission")
        
        assert result is False
    
    def test_require_permission_success(self, mock_tenant_context):
        """Test requiring permission that user has"""
        mock_tenant_context._permission_checker.user_has_permission.return_value = True
        
        # Should not raise exception
        mock_tenant_context.require_permission("test.permission")
    
    def test_require_permission_failure(self, mock_tenant_context):
        """Test requiring permission that user doesn't have"""
        mock_tenant_context._permission_checker.user_has_permission.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            mock_tenant_context.require_permission("test.permission")
        
        assert exc_info.value.status_code == 403
        assert "Permission denied" in str(exc_info.value.detail)
    
    def test_ensure_organization_access_success(self, mock_tenant_context):
        """Test ensuring organization access with valid user and organization"""
        mock_tenant_context._permission_checker.user_can_access_organization.return_value = True
        
        # Should not raise exception
        mock_tenant_context.ensure_organization_access()
    
    def test_ensure_organization_access_no_user(self, db_session):
        """Test ensuring organization access without user"""
        context = TenantContext(organization_id="test-org")
        context.set_permission_checker(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            context.ensure_organization_access()
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    def test_ensure_organization_access_no_org(self, db_session, test_user_with_org):
        """Test ensuring organization access without organization"""
        context = TenantContext(user=test_user_with_org)
        context.set_permission_checker(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            context.ensure_organization_access()
        
        assert exc_info.value.status_code == 400
        assert "Organization context required" in str(exc_info.value.detail)
    
    def test_ensure_organization_access_no_permission(self, mock_tenant_context):
        """Test ensuring organization access without permission"""
        mock_tenant_context._permission_checker.user_can_access_organization.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            mock_tenant_context.ensure_organization_access()
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)


class TestTenantIsolationMiddleware:
    """Test the TenantIsolationMiddleware class"""
    
    def test_extract_organization_from_header(self):
        """Test extracting organization ID from header"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request with organization header
        request = Mock()
        request.headers = {"X-Organization-ID": "test-org-123"}
        request.query_params = {}
        request.path_params = {}
        
        org_id = middleware._extract_organization_id(request)
        
        assert org_id == "test-org-123"
    
    def test_extract_organization_from_query_param(self):
        """Test extracting organization ID from query parameter"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request with query parameter
        request = Mock()
        request.headers = {}
        request.query_params = {"org_id": "test-org-456"}
        request.path_params = {}
        
        org_id = middleware._extract_organization_id(request)
        
        assert org_id == "test-org-456"
    
    def test_extract_organization_from_path_param(self):
        """Test extracting organization ID from path parameter"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request with path parameter
        request = Mock()
        request.headers = {}
        request.query_params = {}
        request.path_params = {"organization_id": "test-org-789"}
        
        org_id = middleware._extract_organization_id(request)
        
        assert org_id == "test-org-789"
    
    def test_extract_organization_priority(self):
        """Test that header takes priority over query param and path param"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request with all sources
        request = Mock()
        request.headers = {"X-Organization-ID": "header-org"}
        request.query_params = {"org_id": "query-org"}
        request.path_params = {"organization_id": "path-org"}
        
        org_id = middleware._extract_organization_id(request)
        
        assert org_id == "header-org"  # Header should win
    
    def test_extract_organization_no_source(self):
        """Test extracting organization when no source is available"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request with no organization context
        request = Mock()
        request.headers = {}
        request.query_params = {}
        request.path_params = {}
        
        org_id = middleware._extract_organization_id(request)
        
        assert org_id is None
    
    @pytest.mark.asyncio
    async def test_middleware_call(self):
        """Test middleware call processing"""
        middleware = TenantIsolationMiddleware()
        
        # Mock request
        request = Mock()
        request.headers = {"X-Organization-ID": "test-org"}
        request.query_params = {}
        request.path_params = {}
        request.state = Mock()
        
        # Mock call_next function
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)
        
        response = await middleware(request, call_next)
        
        # Verify tenant context was set
        assert hasattr(request.state, 'tenant_context')
        assert request.state.tenant_context.organization_id == "test-org"
        
        # Verify call_next was called
        call_next.assert_called_once_with(request)
        
        # Verify response was returned
        assert response == mock_response


class TestTenantContextHelpers:
    """Test helper functions for tenant context"""
    
    def test_get_tenant_context_existing(self):
        """Test getting existing tenant context from request"""
        request = Mock()
        existing_context = TenantContext(organization_id="test-org")
        request.state.tenant_context = existing_context
        
        context = get_tenant_context(request)
        
        assert context == existing_context
    
    def test_get_tenant_context_create_new(self):
        """Test creating new tenant context when none exists"""
        request = Mock()
        request.state = Mock()
        del request.state.tenant_context  # Simulate missing context
        
        context = get_tenant_context(request)
        
        assert isinstance(context, TenantContext)
        assert request.state.tenant_context == context
    
    def test_require_organization_context_success(self):
        """Test requiring organization context when it exists"""
        request = Mock()
        context = TenantContext(organization_id="test-org")
        request.state.tenant_context = context
        
        result = require_organization_context(request)
        
        assert result == context
    
    def test_require_organization_context_missing(self):
        """Test requiring organization context when it's missing"""
        request = Mock()
        context = TenantContext()  # No organization_id
        request.state.tenant_context = context
        
        with pytest.raises(HTTPException) as exc_info:
            require_organization_context(request)
        
        assert exc_info.value.status_code == 400
        assert "Organization context required" in str(exc_info.value.detail)
    
    def test_setup_tenant_context_with_org_id(self, db_session, test_user_with_org, test_organization):
        """Test setting up tenant context with organization ID"""
        request = Mock()
        request.state = Mock()
        request.state.tenant_context = TenantContext()
        
        context = setup_tenant_context(
            request, test_user_with_org, db_session, test_organization.id
        )
        
        assert context.organization_id == test_organization.id
        assert context.user == test_user_with_org
        assert context.organization == test_organization
        assert context.permission_checker is not None
    
    def test_setup_tenant_context_use_default_org(self, db_session, test_user_with_org):
        """Test setting up tenant context using user's default organization"""
        request = Mock()
        request.state = Mock()
        request.state.tenant_context = TenantContext()
        
        context = setup_tenant_context(request, test_user_with_org, db_session)
        
        assert context.organization_id == test_user_with_org.default_organization_id
        assert context.user == test_user_with_org
        assert context.permission_checker is not None
    
    def test_setup_tenant_context_org_not_found(self, db_session, test_user_with_org):
        """Test setting up tenant context with non-existent organization"""
        request = Mock()
        request.state = Mock()
        request.state.tenant_context = TenantContext()
        
        with pytest.raises(HTTPException) as exc_info:
            setup_tenant_context(
                request, test_user_with_org, db_session, "nonexistent-org"
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)


class TestTenantUtilityFunctions:
    """Test utility functions for tenant operations"""
    
    def test_filter_by_organization_with_org_field(self, db_session):
        """Test filtering query by organization when model has organization_id field"""
        # Mock model class with organization_id
        mock_model = Mock()
        mock_model.organization_id = Mock()
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = "filtered_query"
        
        result = filter_by_organization(mock_query, mock_model, "test-org")
        
        assert result == "filtered_query"
        mock_query.filter.assert_called_once()
    
    def test_filter_by_organization_with_user_field(self, db_session):
        """Test filtering query by organization when model has user_id field"""
        # Mock model class with user_id but no organization_id
        mock_model = Mock()
        mock_model.user_id = Mock()
        del mock_model.organization_id  # Remove organization_id attribute
        
        # Mock query with join
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value = "joined_filtered_query"
        
        result = filter_by_organization(mock_query, mock_model, "test-org")
        
        assert result == "joined_filtered_query"
        mock_query.join.assert_called_once()
    
    def test_ensure_user_in_organization_success(self, db_session, test_user_with_org, test_organization):
        """Test ensuring user is in organization when they are"""
        result = ensure_user_in_organization(
            test_user_with_org, test_organization.id, db_session
        )
        
        assert result is True
    
    def test_ensure_user_in_organization_superuser(self, db_session, superuser, test_organization):
        """Test that superusers can access any organization"""
        result = ensure_user_in_organization(
            superuser, test_organization.id, db_session
        )
        
        assert result is True
    
    def test_ensure_user_in_organization_not_member(self, db_session, test_organization):
        """Test ensuring user is in organization when they're not"""
        # Create user not in organization
        user = User(
            id=999,
            email="outsider@example.com",
            username="outsider",
            full_name="Outsider User",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        result = ensure_user_in_organization(user, test_organization.id, db_session)
        
        assert result is False
    
    def test_get_user_default_organization_with_default(self, db_session, test_user_with_org):
        """Test getting user's default organization when they have one"""
        result = get_user_default_organization(test_user_with_org, db_session)
        
        assert result == test_user_with_org.default_organization_id
    
    def test_get_user_default_organization_find_first(self, db_session, test_admin_user, test_organization):
        """Test getting user's first organization when no default is set"""
        # Clear default organization
        test_admin_user.default_organization_id = None
        db_session.commit()
        
        result = get_user_default_organization(test_admin_user, db_session)
        
        # Should return the organization they're a member of
        assert result == test_organization.id
    
    def test_get_user_default_organization_no_orgs(self, db_session):
        """Test getting default organization for user with no organizations"""
        user = User(
            id=998,
            email="noorg@example.com",
            username="noorg",
            full_name="No Org User",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        result = get_user_default_organization(user, db_session)
        
        assert result is None
    
    def test_create_personal_organization(self, db_session, test_roles):
        """Test creating a personal organization for a new user"""
        user = User(
            id=997,
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        org = create_personal_organization(user, db_session)
        
        assert org is not None
        assert org.name == "New User's Organization"
        assert org.slug == "newuser-org"
        assert org.owner_id == user.id
        assert org.plan_type == "starter"
        
        # Verify user is assigned as owner
        db_session.refresh(user)
        assert user.default_organization_id == org.id
        
        # Verify user has org_owner role
        user_org_role = db_session.query(UserOrganizationRole).filter(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == org.id
        ).first()
        
        assert user_org_role is not None
        assert user_org_role.role_id == test_roles["org_owner"].id