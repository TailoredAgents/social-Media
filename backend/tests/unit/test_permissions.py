"""
Unit tests for the permission system
"""
import pytest
from unittest.mock import Mock, patch

from backend.auth.permissions import (
    PermissionChecker, check_content_access, check_admin_access
)
from backend.db.models import User
from backend.db.multi_tenant_models import Organization, Role, Permission


class TestPermissionChecker:
    """Test the PermissionChecker class"""
    
    def test_superuser_has_all_permissions(self, db_session, test_organization, superuser):
        """Test that superusers have all permissions regardless of organization roles"""
        permission_checker = PermissionChecker(db_session)
        
        # Superuser should have any permission
        assert permission_checker.user_has_permission(
            superuser, "any.permission", test_organization.id
        ) is True
        
        assert permission_checker.user_has_permission(
            superuser, "nonexistent.permission", test_organization.id
        ) is True
    
    def test_user_with_org_role_permissions(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test that users with organization roles have correct permissions"""
        # User has org_owner role, should have organizations.read permission
        assert permission_checker.user_has_permission(
            test_user_with_org, "organizations.read", test_organization.id
        ) is True
        
        # Should also have organizations.update permission
        assert permission_checker.user_has_permission(
            test_user_with_org, "organizations.update", test_organization.id
        ) is True
        
        # Should have content.create permission
        assert permission_checker.user_has_permission(
            test_user_with_org, "content.create", test_organization.id
        ) is True
    
    def test_user_without_org_role_no_permissions(self, db_session, test_organization):
        """Test that users without organization roles have no permissions"""
        permission_checker = PermissionChecker(db_session)
        
        # Create user without any organization roles
        user = User(
            id=999,
            email="norole@example.com",
            username="norole",
            full_name="No Role User",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        # User should not have any permissions
        assert permission_checker.user_has_permission(
            user, "organizations.read", test_organization.id
        ) is False
        
        assert permission_checker.user_has_permission(
            user, "content.create", test_organization.id
        ) is False
    
    def test_member_vs_admin_permissions(self, db_session, test_organization, test_member_user, test_admin_user, permission_checker):
        """Test different permission levels between member and admin users"""
        # Member should have content.read but not users.create
        assert permission_checker.user_has_permission(
            test_member_user, "content.read", test_organization.id
        ) is True
        
        assert permission_checker.user_has_permission(
            test_member_user, "users.create", test_organization.id
        ) is False
        
        # Admin should have both content.read and users.create (but not users.delete)
        assert permission_checker.user_has_permission(
            test_admin_user, "content.read", test_organization.id
        ) is True
        
        # Admin doesn't have users.create in our test setup
        # (only org_owner and super_admin do)
        assert permission_checker.user_has_permission(
            test_admin_user, "users.create", test_organization.id
        ) is False
    
    def test_viewer_permissions(self, db_session, test_organization, test_viewer_user, permission_checker):
        """Test that viewer users have read-only permissions"""
        # Viewer should have read permissions
        assert permission_checker.user_has_permission(
            test_viewer_user, "content.read", test_organization.id
        ) is True
        
        assert permission_checker.user_has_permission(
            test_viewer_user, "organizations.read", test_organization.id
        ) is True
        
        # Viewer should not have write permissions
        assert permission_checker.user_has_permission(
            test_viewer_user, "content.create", test_organization.id
        ) is False
        
        assert permission_checker.user_has_permission(
            test_viewer_user, "organizations.update", test_organization.id
        ) is False
    
    def test_user_has_any_permission(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test the user_has_any_permission method"""
        # User should have at least one of these permissions
        assert permission_checker.user_has_any_permission(
            test_user_with_org, 
            ["nonexistent.permission", "organizations.read", "another.nonexistent"],
            test_organization.id
        ) is True
        
        # User should not have any of these permissions
        assert permission_checker.user_has_any_permission(
            test_user_with_org,
            ["nonexistent.permission1", "nonexistent.permission2"],
            test_organization.id
        ) is False
    
    def test_user_has_all_permissions(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test the user_has_all_permissions method"""
        # User should have all of these permissions (org_owner role)
        assert permission_checker.user_has_all_permissions(
            test_user_with_org,
            ["organizations.read", "content.read"],
            test_organization.id
        ) is True
        
        # User should not have all of these permissions
        assert permission_checker.user_has_all_permissions(
            test_user_with_org,
            ["organizations.read", "nonexistent.permission"],
            test_organization.id
        ) is False
    
    def test_get_user_permissions(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test getting all permissions for a user"""
        permissions = permission_checker.get_user_permissions(
            test_user_with_org, test_organization.id
        )
        
        assert isinstance(permissions, list)
        assert "organizations.read" in permissions
        assert "organizations.update" in permissions
        assert "content.create" in permissions
        assert "content.read" in permissions
    
    def test_get_user_role_in_organization(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test getting user's role in organization"""
        role_name = permission_checker.get_user_role_in_organization(
            test_user_with_org, test_organization.id
        )
        
        assert role_name == "org_owner"
    
    def test_get_user_organizations(self, db_session, test_user_with_org, permission_checker):
        """Test getting all organizations for a user"""
        organizations = permission_checker.get_user_organizations(test_user_with_org)
        
        assert isinstance(organizations, list)
        assert len(organizations) >= 1
        
        org_info = organizations[0]
        assert "id" in org_info
        assert "name" in org_info
        assert "slug" in org_info
        assert "role" in org_info
        assert org_info["role"] == "org_owner"
    
    def test_user_can_access_organization(self, db_session, test_user_with_org, test_organization, permission_checker):
        """Test checking if user can access organization"""
        # User should be able to access their organization
        assert permission_checker.user_can_access_organization(
            test_user_with_org, test_organization.id
        ) is True
        
        # User should not be able to access non-existent organization
        assert permission_checker.user_can_access_organization(
            test_user_with_org, "nonexistent-org-id"
        ) is False
    
    def test_is_organization_owner(self, db_session, test_user_with_org, test_admin_user, test_organization, permission_checker):
        """Test checking if user is organization owner"""
        # test_user_with_org is the owner
        assert permission_checker.is_organization_owner(
            test_user_with_org, test_organization.id
        ) is True
        
        # test_admin_user is not the owner
        assert permission_checker.is_organization_owner(
            test_admin_user, test_organization.id
        ) is False
    
    def test_default_organization_context(self, db_session, test_user_with_org, permission_checker):
        """Test that user's default organization is used when no org specified"""
        # Should use user's default organization when no organization_id provided
        assert permission_checker.user_has_permission(
            test_user_with_org, "organizations.read"  # No org_id provided
        ) is True
    
    def test_cross_organization_isolation(self, db_session, multi_org_setup, test_roles, permission_checker):
        """Test that users cannot access permissions in other organizations"""
        user1 = multi_org_setup["user1"]
        user2 = multi_org_setup["user2"]
        org1 = multi_org_setup["org1"]
        org2 = multi_org_setup["org2"]
        
        # User1 should have permissions in org1 but not org2
        assert permission_checker.user_has_permission(
            user1, "organizations.read", org1.id
        ) is True
        
        assert permission_checker.user_has_permission(
            user1, "organizations.read", org2.id
        ) is False
        
        # User2 should have permissions in org2 but not org1
        assert permission_checker.user_has_permission(
            user2, "organizations.read", org2.id
        ) is True
        
        assert permission_checker.user_has_permission(
            user2, "organizations.read", org1.id
        ) is False


class TestPermissionUtilityFunctions:
    """Test utility functions for permission checking"""
    
    def test_check_content_access_own_content(self, db_session, test_user_with_org, test_organization):
        """Test that users can access their own content"""
        permission_checker = PermissionChecker(db_session)
        
        # User accessing their own content
        assert check_content_access(
            test_user_with_org,
            test_user_with_org.id,  # Same user ID
            test_organization.id,
            permission_checker
        ) is True
    
    def test_check_content_access_other_content_with_permission(self, db_session, test_admin_user, test_organization):
        """Test that users with content.read permission can access other's content"""
        permission_checker = PermissionChecker(db_session)
        
        # Admin user accessing other user's content (should have content.read permission)
        assert check_content_access(
            test_admin_user,
            999,  # Different user ID
            test_organization.id,
            permission_checker
        ) is True  # Admin has content.read permission
    
    def test_check_content_access_no_permission(self, db_session, test_viewer_user, test_organization):
        """Test that users without content.read permission cannot access other's content"""
        permission_checker = PermissionChecker(db_session)
        
        # Create a user without content.read permission for this test
        # Note: our test viewer actually has content.read, so let's create a special user
        limited_user = User(
            id=998,
            email="limited@example.com",
            username="limited",
            full_name="Limited User",
            is_active=True,
            default_organization_id=test_organization.id
        )
        
        db_session.add(limited_user)
        db_session.commit()
        
        # Limited user accessing other user's content (no content.read permission)
        assert check_content_access(
            limited_user,
            999,  # Different user ID
            test_organization.id,
            permission_checker
        ) is False
    
    def test_check_admin_access_superuser(self, db_session, superuser, test_organization):
        """Test that superusers have admin access"""
        permission_checker = PermissionChecker(db_session)
        
        assert check_admin_access(
            superuser,
            test_organization.id,
            permission_checker
        ) is True
    
    def test_check_admin_access_org_owner(self, db_session, test_user_with_org, test_organization):
        """Test that organization owners have admin access"""
        permission_checker = PermissionChecker(db_session)
        
        # Org owner should have admin access (has organizations.update permission)
        assert check_admin_access(
            test_user_with_org,
            test_organization.id,
            permission_checker
        ) is True
    
    def test_check_admin_access_regular_user(self, db_session, test_member_user, test_organization):
        """Test that regular users don't have admin access"""
        permission_checker = PermissionChecker(db_session)
        
        # Member user should not have admin access
        assert check_admin_access(
            test_member_user,
            test_organization.id,
            permission_checker
        ) is False


class TestPermissionCheckerErrorHandling:
    """Test error handling in PermissionChecker"""
    
    def test_permission_check_with_database_error(self, db_session):
        """Test graceful handling of database errors"""
        permission_checker = PermissionChecker(db_session)
        
        user = User(id=1, email="test@example.com", username="test")
        
        # Mock a database error
        with patch.object(db_session, 'query', side_effect=Exception("Database error")):
            # Should return False on error, not raise exception
            result = permission_checker.user_has_permission(
                user, "test.permission", "test-org-id"
            )
            assert result is False
    
    def test_get_permissions_with_database_error(self, db_session):
        """Test graceful handling of database errors in get_user_permissions"""
        permission_checker = PermissionChecker(db_session)
        
        user = User(id=1, email="test@example.com", username="test")
        
        # Mock a database error
        with patch.object(db_session, 'query', side_effect=Exception("Database error")):
            # Should return empty list on error, not raise exception
            result = permission_checker.get_user_permissions(user, "test-org-id")
            assert result == []
    
    def test_no_organization_context(self, db_session):
        """Test permission checking without organization context"""
        permission_checker = PermissionChecker(db_session)
        
        user = User(id=1, email="test@example.com", username="test")
        
        # No organization ID provided and user has no default organization
        result = permission_checker.user_has_permission(
            user, "test.permission"  # No organization_id
        )
        assert result is False