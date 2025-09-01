"""
Unit tests for multi-tenant database models
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from backend.db.multi_tenant_models import (
    Organization, Team, Role, Permission, UserOrganizationRole,
    OrganizationInvitation, user_teams
)
from backend.db.models import User


class TestOrganizationModel:
    """Test the Organization model"""
    
    def test_create_organization(self, db_session):
        """Test creating a basic organization"""
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Company",
            slug="test-company",
            description="A test company",
            plan_type="starter",
            owner_id=1
        )
        
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.id is not None
        assert org.name == "Test Company"
        assert org.slug == "test-company"
        assert org.plan_type == "starter"
        assert org.max_users == 5  # Default value
        assert org.subscription_status == "active"  # Default value
        assert org.created_at is not None
    
    def test_organization_slug_unique(self, db_session):
        """Test that organization slugs must be unique"""
        org1 = Organization(
            id=str(uuid.uuid4()),
            name="Company One",
            slug="duplicate-slug",
            owner_id=1
        )
        
        org2 = Organization(
            id=str(uuid.uuid4()),
            name="Company Two",
            slug="duplicate-slug",  # Same slug
            owner_id=2
        )
        
        db_session.add(org1)
        db_session.commit()
        
        db_session.add(org2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_organization_defaults(self, db_session):
        """Test organization default values"""
        org = Organization(
            id=str(uuid.uuid4()),
            name="Default Test",
            slug="default-test",
            owner_id=1
        )
        
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.plan_type == "starter"
        assert org.max_users == 5
        assert org.max_teams == 2
        assert org.max_social_accounts == 3
        assert org.subscription_status == "active"
        assert org.settings == {}
        assert org.features_enabled == ["basic_posting", "scheduling", "analytics"]


class TestTeamModel:
    """Test the Team model"""
    
    def test_create_team(self, db_session, test_organization):
        """Test creating a team"""
        team = Team(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Engineering Team",
            description="Software engineering team",
            default_role="member",
            created_by_id=1
        )
        
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        assert team.id is not None
        assert team.name == "Engineering Team"
        assert team.organization_id == test_organization.id
        assert team.default_role == "member"
        assert team.is_default is False
        assert team.created_at is not None
    
    def test_team_name_unique_within_organization(self, db_session, test_organization):
        """Test that team names must be unique within an organization"""
        team1 = Team(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Duplicate Team",
            created_by_id=1
        )
        
        team2 = Team(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Duplicate Team",  # Same name, same org
            created_by_id=1
        )
        
        db_session.add(team1)
        db_session.commit()
        
        db_session.add(team2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_team_name_can_duplicate_across_organizations(self, db_session, multi_org_setup):
        """Test that team names can be the same across different organizations"""
        org1 = multi_org_setup["org1"]
        org2 = multi_org_setup["org2"]
        
        team1 = Team(
            id=str(uuid.uuid4()),
            organization_id=org1.id,
            name="Same Name Team",
            created_by_id=org1.owner_id
        )
        
        team2 = Team(
            id=str(uuid.uuid4()),
            organization_id=org2.id,
            name="Same Name Team",  # Same name, different org
            created_by_id=org2.owner_id
        )
        
        db_session.add_all([team1, team2])
        db_session.commit()  # Should not raise an error
        
        assert team1.name == team2.name
        assert team1.organization_id != team2.organization_id


class TestRoleAndPermissionModels:
    """Test Role and Permission models"""
    
    def test_create_role(self, db_session):
        """Test creating a role"""
        role = Role(
            id=str(uuid.uuid4()),
            name="test_role",
            display_name="Test Role",
            description="A test role",
            level=50,
            is_system_role=False,
            color="#6B7280"
        )
        
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        
        assert role.id is not None
        assert role.name == "test_role"
        assert role.display_name == "Test Role"
        assert role.level == 50
        assert role.is_system_role is False
        assert role.created_at is not None
    
    def test_create_permission(self, db_session):
        """Test creating a permission"""
        permission = Permission(
            id=str(uuid.uuid4()),
            name="test.action",
            display_name="Test Action",
            description="A test permission",
            resource="test",
            action="action",
            is_system_permission=False
        )
        
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)
        
        assert permission.id is not None
        assert permission.name == "test.action"
        assert permission.resource == "test"
        assert permission.action == "action"
        assert permission.is_system_permission is False
    
    def test_role_permission_relationship(self, db_session):
        """Test the many-to-many relationship between roles and permissions"""
        role = Role(
            id=str(uuid.uuid4()),
            name="test_role",
            display_name="Test Role",
            description="A test role",
            level=50
        )
        
        permission1 = Permission(
            id=str(uuid.uuid4()),
            name="test.read",
            display_name="Test Read",
            description="Read test resources",
            resource="test",
            action="read"
        )
        
        permission2 = Permission(
            id=str(uuid.uuid4()),
            name="test.write",
            display_name="Test Write",
            description="Write test resources",
            resource="test",
            action="write"
        )
        
        db_session.add_all([role, permission1, permission2])
        db_session.flush()
        
        # Add permissions to role
        role.permissions.extend([permission1, permission2])
        db_session.commit()
        
        # Verify relationship
        assert len(role.permissions) == 2
        assert permission1 in role.permissions
        assert permission2 in role.permissions
        
        # Verify reverse relationship
        assert role in permission1.roles
        assert role in permission2.roles
    
    def test_permission_unique_constraint(self, db_session):
        """Test that resource+action combinations must be unique"""
        permission1 = Permission(
            id=str(uuid.uuid4()),
            name="test.read",
            display_name="Test Read",
            resource="test",
            action="read"
        )
        
        permission2 = Permission(
            id=str(uuid.uuid4()),
            name="duplicate.read",  # Different name
            display_name="Duplicate Read",
            resource="test",  # Same resource
            action="read"     # Same action
        )
        
        db_session.add(permission1)
        db_session.commit()
        
        db_session.add(permission2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserOrganizationRole:
    """Test UserOrganizationRole model"""
    
    def test_create_user_org_role(self, db_session, test_user_with_org, test_organization, test_roles):
        """Test creating a user organization role"""
        role = test_roles["member"]
        
        user_org_role = UserOrganizationRole(
            id=str(uuid.uuid4()),
            user_id=test_user_with_org.id,
            organization_id=test_organization.id,
            role_id=role.id,
            assigned_by_id=test_user_with_org.id,
            is_active=True
        )
        
        db_session.add(user_org_role)
        db_session.commit()
        db_session.refresh(user_org_role)
        
        assert user_org_role.id is not None
        assert user_org_role.user_id == test_user_with_org.id
        assert user_org_role.organization_id == test_organization.id
        assert user_org_role.role_id == role.id
        assert user_org_role.is_active is True
        assert user_org_role.assigned_at is not None
    
    def test_user_organization_unique_constraint(self, db_session, test_user_with_org, test_organization, test_roles):
        """Test that a user can only have one role per organization"""
        role1 = test_roles["member"]
        role2 = test_roles["admin"]
        
        # First role assignment
        user_org_role1 = UserOrganizationRole(
            id=str(uuid.uuid4()),
            user_id=test_user_with_org.id,
            organization_id=test_organization.id,
            role_id=role1.id,
            assigned_by_id=test_user_with_org.id,
            is_active=True
        )
        
        # Second role assignment (should fail due to unique constraint)
        user_org_role2 = UserOrganizationRole(
            id=str(uuid.uuid4()),
            user_id=test_user_with_org.id,
            organization_id=test_organization.id,  # Same user, same org
            role_id=role2.id,
            assigned_by_id=test_user_with_org.id,
            is_active=True
        )
        
        db_session.add(user_org_role1)
        db_session.commit()
        
        db_session.add(user_org_role2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestOrganizationInvitation:
    """Test OrganizationInvitation model"""
    
    def test_create_invitation(self, db_session, test_organization, test_team, test_user_with_org):
        """Test creating an organization invitation"""
        invitation = OrganizationInvitation(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            team_id=test_team.id,
            email="newuser@example.com",
            role="member",
            token=str(uuid.uuid4()),
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            invited_by_id=test_user_with_org.id
        )
        
        db_session.add(invitation)
        db_session.commit()
        db_session.refresh(invitation)
        
        assert invitation.id is not None
        assert invitation.email == "newuser@example.com"
        assert invitation.role == "member"
        assert invitation.status == "pending"
        assert invitation.expires_at > datetime.utcnow()
        assert invitation.token is not None
        assert invitation.created_at is not None
    
    def test_invitation_token_unique(self, db_session, test_organization, test_user_with_org):
        """Test that invitation tokens must be unique"""
        duplicate_token = str(uuid.uuid4())
        
        invitation1 = OrganizationInvitation(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            email="user1@example.com",
            role="member",
            token=duplicate_token,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            invited_by_id=test_user_with_org.id
        )
        
        invitation2 = OrganizationInvitation(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            email="user2@example.com",
            role="member",
            token=duplicate_token,  # Same token
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            invited_by_id=test_user_with_org.id
        )
        
        db_session.add(invitation1)
        db_session.commit()
        
        db_session.add(invitation2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_organization_teams_relationship(self, db_session, test_organization):
        """Test organization-teams relationship"""
        team1 = Team(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Team 1",
            created_by_id=1
        )
        
        team2 = Team(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Team 2",
            created_by_id=1
        )
        
        db_session.add_all([team1, team2])
        db_session.commit()
        db_session.refresh(test_organization)
        
        assert len(test_organization.teams) == 2
        assert team1 in test_organization.teams
        assert team2 in test_organization.teams
    
    def test_user_organization_relationship(self, db_session, test_user_with_org, test_organization):
        """Test user-organization relationship through UserOrganizationRole"""
        db_session.refresh(test_user_with_org)
        
        # User should have organization roles
        assert len(test_user_with_org.organization_roles) >= 1
        
        # Check the relationship
        user_org_role = test_user_with_org.organization_roles[0]
        assert user_org_role.organization_id == test_organization.id
        assert user_org_role.user_id == test_user_with_org.id