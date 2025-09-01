"""
Integration tests for organization management APIs
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db


class TestOrganizationListAPI:
    """Test organization listing endpoints"""
    
    def test_list_user_organizations_authenticated(self, client, test_user_with_org, override_get_db):
        """Test listing organizations for authenticated user"""
        # Override dependencies
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/organizations/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        org = data[0]
        assert "id" in org
        assert "name" in org
        assert "slug" in org
        assert "user_role" in org
        assert "user_permissions" in org
        assert org["user_role"] == "org_owner"
    
    def test_list_organizations_unauthenticated(self, client):
        """Test that unauthenticated requests are rejected"""
        response = client.get("/api/organizations/")
        
        # Should require authentication
        assert response.status_code in [401, 422]  # Depends on auth setup


class TestOrganizationCreateAPI:
    """Test organization creation endpoints"""
    
    def test_create_organization_success(self, client, test_user_with_org, override_get_db, sample_org_data):
        """Test successful organization creation"""
        # Override dependencies
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.post(
            "/api/organizations/",
            json=sample_org_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_org_data["name"]
        assert data["slug"] == sample_org_data["slug"]
        assert data["description"] == sample_org_data["description"]
        assert data["plan_type"] == sample_org_data["plan_type"]
        assert data["user_role"] == "org_owner"  # Creator becomes owner
        assert "user_permissions" in data
        assert len(data["user_permissions"]) > 0
    
    def test_create_organization_duplicate_slug(self, client, test_user_with_org, test_organization, override_get_db):
        """Test creation with duplicate slug fails"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        duplicate_org_data = {
            "name": "Another Organization",
            "slug": test_organization.slug,  # Same slug as existing org
            "description": "This should fail",
            "plan_type": "starter"
        }
        
        response = client.post(
            "/api/organizations/",
            json=duplicate_org_data
        )
        
        assert response.status_code == 400
        assert "slug already exists" in response.json()["detail"]
    
    def test_create_organization_invalid_data(self, client, test_user_with_org, override_get_db):
        """Test creation with invalid data fails"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        invalid_data = {
            "name": "",  # Empty name
            "slug": "invalid slug!",  # Invalid characters
            "plan_type": "invalid_plan"
        }
        
        response = client.post(
            "/api/organizations/",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error


class TestOrganizationDetailAPI:
    """Test organization detail endpoints"""
    
    def test_get_organization_success(self, client, test_user_with_org, test_organization, override_get_db):
        """Test getting organization details"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get(
            f"/api/organizations/{test_organization.id}",
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_organization.id
        assert data["name"] == test_organization.name
        assert data["slug"] == test_organization.slug
        assert data["user_role"] == "org_owner"
        assert "user_permissions" in data
    
    def test_get_organization_no_access(self, client, test_member_user, test_organization, override_get_db, multi_org_setup):
        """Test getting organization user has no access to"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_member_user
        
        # Try to access a different organization
        other_org = multi_org_setup["org2"]
        
        response = client.get(
            f"/api/organizations/{other_org.id}",
            headers={"X-Organization-ID": other_org.id}
        )
        
        assert response.status_code == 403  # Access denied
    
    def test_get_organization_not_found(self, client, test_user_with_org, override_get_db):
        """Test getting non-existent organization"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get(
            "/api/organizations/nonexistent-org-id",
            headers={"X-Organization-ID": "nonexistent-org-id"}
        )
        
        assert response.status_code == 404


class TestOrganizationUpdateAPI:
    """Test organization update endpoints"""
    
    def test_update_organization_success(self, client, test_user_with_org, test_organization, override_get_db):
        """Test successful organization update"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description",
            "max_users": 20
        }
        
        response = client.put(
            f"/api/organizations/{test_organization.id}",
            json=update_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["max_users"] == update_data["max_users"]
    
    def test_update_organization_no_permission(self, client, test_member_user, test_organization, override_get_db):
        """Test that users without update permission cannot update organization"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_member_user
        
        update_data = {
            "name": "Should Not Work"
        }
        
        response = client.put(
            f"/api/organizations/{test_organization.id}",
            json=update_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 403  # Permission denied


class TestTeamManagementAPI:
    """Test team management endpoints"""
    
    def test_list_organization_teams(self, client, test_user_with_org, test_organization, test_team, override_get_db):
        """Test listing teams in organization"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get(
            f"/api/organizations/{test_organization.id}/teams",
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        team = data[0]
        assert team["id"] == test_team.id
        assert team["name"] == test_team.name
        assert "member_count" in team
    
    def test_create_team_success(self, client, test_user_with_org, test_organization, override_get_db, sample_team_data):
        """Test successful team creation"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/teams",
            json=sample_team_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_team_data["name"]
        assert data["description"] == sample_team_data["description"]
        assert data["default_role"] == sample_team_data["default_role"]
        assert data["member_count"] == 0
    
    def test_create_team_duplicate_name(self, client, test_user_with_org, test_organization, test_team, override_get_db):
        """Test that duplicate team names in same organization fail"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        duplicate_team_data = {
            "name": test_team.name,  # Same name as existing team
            "description": "Should fail",
            "default_role": "member"
        }
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/teams",
            json=duplicate_team_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_team_no_permission(self, client, test_viewer_user, test_organization, override_get_db, sample_team_data):
        """Test that users without team creation permission cannot create teams"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_viewer_user
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/teams",
            json=sample_team_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 403  # Permission denied


class TestInvitationAPI:
    """Test user invitation endpoints"""
    
    def test_invite_user_success(self, client, test_user_with_org, test_organization, test_team, override_get_db, sample_invitation_data):
        """Test successful user invitation"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        invitation_data = {
            **sample_invitation_data,
            "team_id": test_team.id
        }
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/invite",
            json=invitation_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == invitation_data["email"]
        assert data["role"] == invitation_data["role"]
        assert data["status"] == "pending"
        assert data["team_name"] == test_team.name
        assert "expires_at" in data
    
    def test_invite_existing_user(self, client, test_user_with_org, test_admin_user, test_organization, override_get_db):
        """Test inviting user who is already in organization"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        invitation_data = {
            "email": test_admin_user.email,  # User already in org
            "role": "member"
        }
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/invite",
            json=invitation_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"]
    
    def test_invite_duplicate_email(self, client, test_user_with_org, test_organization, test_invitation, override_get_db):
        """Test inviting same email twice"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        invitation_data = {
            "email": test_invitation.email,  # Same email as existing invitation
            "role": "member"
        }
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/invite",
            json=invitation_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 400
        assert "already sent" in response.json()["detail"]
    
    def test_invite_no_permission(self, client, test_member_user, test_organization, override_get_db, sample_invitation_data):
        """Test that users without invitation permission cannot invite"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_member_user
        
        response = client.post(
            f"/api/organizations/{test_organization.id}/invite",
            json=sample_invitation_data,
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 403  # Permission denied
    
    def test_list_invitations(self, client, test_user_with_org, test_organization, test_invitation, override_get_db):
        """Test listing organization invitations"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get(
            f"/api/organizations/{test_organization.id}/invitations",
            headers={"X-Organization-ID": test_organization.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        invitation = data[0]
        assert invitation["id"] == test_invitation.id
        assert invitation["email"] == test_invitation.email
        assert invitation["status"] == test_invitation.status


class TestTenantIsolation:
    """Test tenant isolation in organization APIs"""
    
    def test_organization_isolation(self, client, multi_org_setup, override_get_db):
        """Test that users can only access their own organization data"""
        user1 = multi_org_setup["user1"]
        user2 = multi_org_setup["user2"]
        org1 = multi_org_setup["org1"]
        org2 = multi_org_setup["org2"]
        
        # User1 trying to access org2 should fail
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: user1
        
        response = client.get(
            f"/api/organizations/{org2.id}",
            headers={"X-Organization-ID": org2.id}
        )
        
        assert response.status_code == 403  # Access denied
        
        # User2 trying to access org1 should fail
        client.app.dependency_overrides[get_current_user] = lambda: user2
        
        response = client.get(
            f"/api/organizations/{org1.id}",
            headers={"X-Organization-ID": org1.id}
        )
        
        assert response.status_code == 403  # Access denied
    
    def test_missing_organization_header(self, client, test_user_with_org, test_organization, override_get_db):
        """Test that missing organization header is handled properly"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # Request without X-Organization-ID header
        response = client.get(f"/api/organizations/{test_organization.id}")
        
        # Should use user's default organization or fail gracefully
        # Exact behavior depends on implementation
        assert response.status_code in [200, 400, 403]


class TestAPIErrorHandling:
    """Test error handling in organization APIs"""
    
    def test_database_error_handling(self, client, test_user_with_org, override_get_db):
        """Test graceful handling of database errors"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # Mock database error
        with patch('backend.api.organizations.db_session') as mock_db:
            mock_db.query.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/organizations/")
            
            assert response.status_code == 500
            assert "Failed to retrieve organizations" in response.json()["detail"]
    
    def test_invalid_organization_id(self, client, test_user_with_org, override_get_db):
        """Test handling of invalid organization IDs"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get(
            "/api/organizations/invalid-uuid-format",
            headers={"X-Organization-ID": "invalid-uuid-format"}
        )
        
        # Should handle invalid UUID gracefully
        assert response.status_code in [400, 404, 422]