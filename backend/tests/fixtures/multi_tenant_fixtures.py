"""
Test fixtures for multi-tenancy and RBAC testing
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock

from backend.db.models import User
from backend.db.multi_tenant_models import (
    Organization, Team, Role, Permission, UserOrganizationRole,
    OrganizationInvitation, user_teams
)
from backend.auth.permissions import PermissionChecker
from backend.middleware.tenant_isolation import TenantContext


@pytest.fixture
def test_permissions(db_session: Session):
    """Create test permissions in database"""
    permissions = [
        Permission(
            id="users_read",
            name="users.read",
            display_name="View Users",
            description="View user information",
            resource="users",
            action="read",
            is_system_permission=True
        ),
        Permission(
            id="users_create",
            name="users.create",
            display_name="Create Users",
            description="Create new user accounts",
            resource="users",
            action="create",
            is_system_permission=True
        ),
        Permission(
            id="organizations_read",
            name="organizations.read",
            display_name="View Organizations",
            description="View organization information",
            resource="organizations",
            action="read",
            is_system_permission=True
        ),
        Permission(
            id="organizations_update",
            name="organizations.update",
            display_name="Update Organizations",
            description="Update organization settings",
            resource="organizations",
            action="update",
            is_system_permission=True
        ),
        Permission(
            id="content_create",
            name="content.create",
            display_name="Create Content",
            description="Create new content",
            resource="content",
            action="create",
            is_system_permission=True
        ),
        Permission(
            id="content_read",
            name="content.read",
            display_name="View Content",
            description="View content",
            resource="content",
            action="read",
            is_system_permission=True
        ),
    ]
    
    for permission in permissions:
        db_session.add(permission)
    
    db_session.commit()
    return {perm.name: perm for perm in permissions}


@pytest.fixture
def test_roles(db_session: Session, test_permissions):
    """Create test roles with permissions"""
    # Create roles
    roles = [
        Role(
            id="super_admin",
            name="super_admin",
            display_name="Super Admin",
            description="Full system access",
            level=100,
            is_system_role=True,
            color="#DC2626"
        ),
        Role(
            id="org_owner",
            name="org_owner",
            display_name="Organization Owner",
            description="Full access within organization",
            level=90,
            is_system_role=True,
            color="#7C3AED"
        ),
        Role(
            id="admin",
            name="admin",
            display_name="Administrator",
            description="Administrative access within organization",
            level=80,
            is_system_role=True,
            color="#059669"
        ),
        Role(
            id="member",
            name="member",
            display_name="Member",
            description="Standard user access",
            level=50,
            is_system_role=True,
            color="#6B7280"
        ),
        Role(
            id="viewer",
            name="viewer",
            display_name="Viewer",
            description="Read-only access",
            level=30,
            is_system_role=True,
            color="#9CA3AF"
        ),
    ]
    
    for role in roles:
        db_session.add(role)
    
    db_session.flush()  # Get IDs
    
    # Assign permissions to roles
    role_permissions = {
        "super_admin": list(test_permissions.keys()),
        "org_owner": ["users.read", "users.create", "organizations.read", "organizations.update", "content.create", "content.read"],
        "admin": ["users.read", "organizations.read", "content.create", "content.read"],
        "member": ["users.read", "organizations.read", "content.create", "content.read"],
        "viewer": ["users.read", "organizations.read", "content.read"],
    }
    
    for role in roles:
        if role.name in role_permissions:
            for perm_name in role_permissions[role.name]:
                if perm_name in test_permissions:
                    role.permissions.append(test_permissions[perm_name])
    
    db_session.commit()
    return {role.name: role for role in roles}


@pytest.fixture
def test_organization(db_session: Session):
    """Create a test organization"""
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Organization",
        slug="test-org",
        description="Test organization for unit tests",
        plan_type="starter",
        max_users=10,
        max_teams=5,
        max_social_accounts=3,
        owner_id=1  # Will be updated when we have actual users
    )
    
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_team(db_session: Session, test_organization):
    """Create a test team within the organization"""
    team = Team(
        id=str(uuid.uuid4()),
        organization_id=test_organization.id,
        name="Test Team",
        description="Test team for unit tests",
        default_role="member",
        is_default=True,
        created_by_id=1  # Will be updated when we have actual users
    )
    
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture
def test_user_with_org(db_session: Session, test_organization, test_roles):
    """Create a test user with organization membership"""
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        default_organization_id=test_organization.id
    )
    
    db_session.add(user)
    db_session.flush()  # Get user ID
    
    # Update organization owner
    test_organization.owner_id = user.id
    
    # Assign user to organization with role
    user_org_role = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=test_organization.id,
        role_id=test_roles["org_owner"].id,
        assigned_by_id=user.id,
        is_active=True
    )
    
    db_session.add(user_org_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session: Session, test_organization, test_roles):
    """Create a test admin user"""
    user = User(
        id=2,
        email="admin@example.com",
        username="adminuser",
        full_name="Admin User",
        is_active=True,
        default_organization_id=test_organization.id
    )
    
    db_session.add(user)
    db_session.flush()
    
    # Assign admin role
    user_org_role = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=test_organization.id,
        role_id=test_roles["admin"].id,
        assigned_by_id=1,  # Assigned by org owner
        is_active=True
    )
    
    db_session.add(user_org_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_member_user(db_session: Session, test_organization, test_roles):
    """Create a test member user"""
    user = User(
        id=3,
        email="member@example.com",
        username="memberuser",
        full_name="Member User",
        is_active=True,
        default_organization_id=test_organization.id
    )
    
    db_session.add(user)
    db_session.flush()
    
    # Assign member role
    user_org_role = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=test_organization.id,
        role_id=test_roles["member"].id,
        assigned_by_id=1,  # Assigned by org owner
        is_active=True
    )
    
    db_session.add(user_org_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_viewer_user(db_session: Session, test_organization, test_roles):
    """Create a test viewer user"""
    user = User(
        id=4,
        email="viewer@example.com",
        username="vieweruser",
        full_name="Viewer User",
        is_active=True,
        default_organization_id=test_organization.id
    )
    
    db_session.add(user)
    db_session.flush()
    
    # Assign viewer role
    user_org_role = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user.id,
        organization_id=test_organization.id,
        role_id=test_roles["viewer"].id,
        assigned_by_id=1,  # Assigned by org owner
        is_active=True
    )
    
    db_session.add(user_org_role)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_invitation(db_session: Session, test_organization, test_team, test_user_with_org):
    """Create a test organization invitation"""
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
    return invitation


@pytest.fixture
def permission_checker(db_session: Session):
    """Create a permission checker instance"""
    return PermissionChecker(db_session)


@pytest.fixture
def mock_tenant_context(test_organization, test_user_with_org, permission_checker):
    """Create a mock tenant context"""
    context = TenantContext(
        organization_id=test_organization.id,
        organization=test_organization,
        user=test_user_with_org
    )
    context._permission_checker = permission_checker
    return context


@pytest.fixture
def sample_org_data():
    """Sample organization data for API testing"""
    return {
        "name": "New Test Organization",
        "slug": "new-test-org",
        "description": "A new organization for testing",
        "plan_type": "professional"
    }


@pytest.fixture
def sample_team_data():
    """Sample team data for API testing"""
    return {
        "name": "Development Team",
        "description": "Team for development activities",
        "default_role": "member"
    }


@pytest.fixture
def sample_invitation_data():
    """Sample invitation data for API testing"""
    return {
        "email": "newinvite@example.com",
        "role": "member",
        "message": "Welcome to our organization!"
    }


@pytest.fixture
def superuser(db_session: Session):
    """Create a superuser for testing"""
    user = User(
        id=99,
        email="superuser@example.com",
        username="superuser",
        full_name="Super User",
        is_active=True,
        is_superuser=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def multi_org_setup(db_session: Session, test_roles):
    """Create multiple organizations for testing cross-org isolation"""
    # Organization 1
    org1 = Organization(
        id=str(uuid.uuid4()),
        name="Organization One",
        slug="org-one",
        description="First test organization",
        plan_type="starter",
        owner_id=10
    )
    
    # Organization 2
    org2 = Organization(
        id=str(uuid.uuid4()),
        name="Organization Two",
        slug="org-two",
        description="Second test organization",
        plan_type="professional",
        owner_id=11
    )
    
    db_session.add_all([org1, org2])
    
    # Users for each org
    user1 = User(
        id=10,
        email="user1@org1.com",
        username="user1",
        full_name="User One",
        is_active=True,
        default_organization_id=org1.id
    )
    
    user2 = User(
        id=11,
        email="user2@org2.com",
        username="user2",
        full_name="User Two",
        is_active=True,
        default_organization_id=org2.id
    )
    
    db_session.add_all([user1, user2])
    db_session.flush()
    
    # Assign roles
    role1 = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user1.id,
        organization_id=org1.id,
        role_id=test_roles["org_owner"].id,
        assigned_by_id=user1.id,
        is_active=True
    )
    
    role2 = UserOrganizationRole(
        id=str(uuid.uuid4()),
        user_id=user2.id,
        organization_id=org2.id,
        role_id=test_roles["org_owner"].id,
        assigned_by_id=user2.id,
        is_active=True
    )
    
    db_session.add_all([role1, role2])
    db_session.commit()
    
    return {
        "org1": org1,
        "org2": org2,
        "user1": user1,
        "user2": user2
    }