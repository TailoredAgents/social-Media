"""
Organization management API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field, ConfigDict, EmailStr
import uuid
from datetime import datetime, timedelta

from backend.db.database import get_db
from backend.auth.dependencies import get_current_active_user
from backend.db.models import User
from backend.db.multi_tenant_models import (
    Organization, Team, Role, Permission, UserOrganizationRole, 
    OrganizationInvitation, user_teams
)
from backend.middleware.tenant_isolation import (
    get_tenant_context, require_organization_context, setup_tenant_context,
    create_personal_organization
)
from backend.auth.permissions import PermissionChecker
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/organizations", tags=["organizations"])


async def send_invitation_email(
    invitation: OrganizationInvitation, 
    organization: Organization, 
    invited_by: User,
    custom_message: Optional[str] = None
):
    """
    Send organization invitation email
    """
    try:
        from backend.services.email_service import email_service, EmailTemplates
        
        # Generate join URL (this should match your frontend route)
        join_url = f"https://yourdomain.com/accept-invitation?token={invitation.token}"  # Update with your domain
        
        # Create email from template
        email_message = EmailTemplates.organization_invitation(
            organization.name,
            invited_by.full_name or invited_by.username,
            join_url
        )
        email_message.to = invitation.email
        
        # Add custom message if provided
        if custom_message:
            # Inject custom message into the email body
            custom_section = f"""
            <p><strong>Personal message from {invited_by.full_name or invited_by.username}:</strong></p>
            <p style="font-style: italic; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #007cba;">
                {custom_message}
            </p>
            """
            email_message.html_body = email_message.html_body.replace(
                "<p>If you don't want to join this organization", 
                custom_section + "<p>If you don't want to join this organization"
            )
        
        # Send email
        result = await email_service.send_email(email_message)
        
        if result["status"] == "success":
            logger.info(f"Organization invitation email sent successfully to {invitation.email}")
        else:
            logger.error(f"Failed to send organization invitation email to {invitation.email}: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"Error sending organization invitation email to {invitation.email}: {str(e)}")


# Pydantic models for API requests/responses
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = Field(None, max_length=500)
    plan_type: str = Field(default="starter")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    plan_type: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_teams: Optional[int] = Field(None, ge=1)
    max_social_accounts: Optional[int] = Field(None, ge=1)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    plan_type: str
    max_users: int
    max_teams: int
    max_social_accounts: int
    subscription_status: str
    owner_id: int
    created_at: datetime
    user_role: Optional[str] = None
    user_permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    default_role: str = Field(default="member")


class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    default_role: str
    is_default: bool
    created_at: datetime
    member_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member")
    team_id: Optional[str] = None
    message: Optional[str] = Field(None, max_length=500)


class InvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    team_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all organizations the current user has access to
    """
    try:
        permission_checker = PermissionChecker(db)
        organizations_data = permission_checker.get_user_organizations(current_user)
        
        organizations = []
        for org_data in organizations_data:
            organization = db.query(Organization).filter(
                Organization.id == org_data['id']
            ).first()
            
            if organization:
                # Get user permissions in this organization
                user_permissions = permission_checker.get_user_permissions(
                    current_user, organization.id
                )
                
                org_response = OrganizationResponse(
                    id=organization.id,
                    name=organization.name,
                    slug=organization.slug,
                    description=organization.description,
                    plan_type=organization.plan_type,
                    max_users=organization.max_users,
                    max_teams=organization.max_teams,
                    max_social_accounts=organization.max_social_accounts,
                    subscription_status=organization.subscription_status,
                    owner_id=organization.owner_id,
                    created_at=organization.created_at,
                    user_role=org_data['role'],
                    user_permissions=user_permissions
                )
                organizations.append(org_response)
        
        return organizations
        
    except Exception as e:
        logger.error(f"Error listing organizations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization
    """
    try:
        # Check if slug is already taken
        existing_org = db.query(Organization).filter(
            Organization.slug == organization_data.slug
        ).first()
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists"
            )
        
        # Create organization
        organization = Organization(
            id=str(uuid.uuid4()),
            name=organization_data.name,
            slug=organization_data.slug,
            description=organization_data.description,
            plan_type=organization_data.plan_type,
            owner_id=current_user.id
        )
        
        db.add(organization)
        db.flush()  # Get the ID
        
        # Assign user as organization owner
        org_owner_role = db.query(Role).filter(Role.name == 'org_owner').first()
        if org_owner_role:
            user_org_role = UserOrganizationRole(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                organization_id=organization.id,
                role_id=org_owner_role.id,
                assigned_by_id=current_user.id,
                is_active=True
            )
            db.add(user_org_role)
        
        # Create default team
        default_team = Team(
            id=str(uuid.uuid4()),
            organization_id=organization.id,
            name="General",
            description="Default team for all organization members",
            is_default=True,
            created_by_id=current_user.id
        )
        db.add(default_team)
        
        db.commit()
        
        # Get user permissions for response
        permission_checker = PermissionChecker(db)
        user_permissions = permission_checker.get_user_permissions(
            current_user, organization.id
        )
        user_role = permission_checker.get_user_role_in_organization(
            current_user, organization.id
        )
        
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            plan_type=organization.plan_type,
            max_users=organization.max_users,
            max_teams=organization.max_teams,
            max_social_accounts=organization.max_social_accounts,
            subscription_status=organization.subscription_status,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            user_role=user_role,
            user_permissions=user_permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get organization details
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("organizations.read")
        
        organization = tenant_context.organization
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user permissions and role
        user_permissions = tenant_context.permission_checker.get_user_permissions(
            current_user, organization.id
        )
        user_role = tenant_context.permission_checker.get_user_role_in_organization(
            current_user, organization.id
        )
        
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            plan_type=organization.plan_type,
            max_users=organization.max_users,
            max_teams=organization.max_teams,
            max_social_accounts=organization.max_social_accounts,
            subscription_status=organization.subscription_status,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            user_role=user_role,
            user_permissions=user_permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization"
        )


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update organization settings
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("organizations.update")
        
        organization = tenant_context.organization
        
        # Update fields
        if update_data.name is not None:
            organization.name = update_data.name
        if update_data.description is not None:
            organization.description = update_data.description
        if update_data.plan_type is not None:
            organization.plan_type = update_data.plan_type
        if update_data.max_users is not None:
            organization.max_users = update_data.max_users
        if update_data.max_teams is not None:
            organization.max_teams = update_data.max_teams
        if update_data.max_social_accounts is not None:
            organization.max_social_accounts = update_data.max_social_accounts
        
        organization.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(organization)
        
        # Get updated user permissions
        user_permissions = tenant_context.permission_checker.get_user_permissions(
            current_user, organization.id
        )
        user_role = tenant_context.permission_checker.get_user_role_in_organization(
            current_user, organization.id
        )
        
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            plan_type=organization.plan_type,
            max_users=organization.max_users,
            max_teams=organization.max_teams,
            max_social_accounts=organization.max_social_accounts,
            subscription_status=organization.subscription_status,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            user_role=user_role,
            user_permissions=user_permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.get("/{organization_id}/teams", response_model=List[TeamResponse])
async def list_organization_teams(
    organization_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List teams in organization
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("teams.read")
        
        teams = db.query(Team).filter(
            Team.organization_id == organization_id
        ).all()
        
        # Get member counts for each team
        team_responses = []
        for team in teams:
            member_count = db.query(user_teams).filter(
                user_teams.c.team_id == team.id,
                user_teams.c.is_active == True
            ).count()
            
            team_responses.append(TeamResponse(
                id=team.id,
                name=team.name,
                description=team.description,
                default_role=team.default_role,
                is_default=team.is_default,
                created_at=team.created_at,
                member_count=member_count
            ))
        
        return team_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing teams for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teams"
        )


@router.post("/{organization_id}/teams", response_model=TeamResponse)
async def create_team(
    organization_id: str,
    team_data: TeamCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new team in organization
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("teams.create")
        
        # Check if team name already exists in organization
        existing_team = db.query(Team).filter(
            and_(
                Team.organization_id == organization_id,
                Team.name == team_data.name
            )
        ).first()
        
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team name already exists in organization"
            )
        
        # Create team
        team = Team(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=team_data.name,
            description=team_data.description,
            default_role=team_data.default_role,
            created_by_id=current_user.id
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            default_role=team.default_role,
            is_default=team.is_default,
            created_at=team.created_at,
            member_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team in organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )


@router.post("/{organization_id}/invite", response_model=InvitationResponse)
async def invite_user_to_organization(
    organization_id: str,
    invite_data: InviteUserRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Invite a user to join the organization
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("users.create")
        
        # Check if user is already in organization
        existing_user = db.query(User).filter(User.email == invite_data.email).first()
        if existing_user:
            existing_role = db.query(UserOrganizationRole).filter(
                and_(
                    UserOrganizationRole.user_id == existing_user.id,
                    UserOrganizationRole.organization_id == organization_id,
                    UserOrganizationRole.is_active == True
                )
            ).first()
            
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of this organization"
                )
        
        # Check if there's already a pending invitation
        existing_invitation = db.query(OrganizationInvitation).filter(
            and_(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.email == invite_data.email,
                OrganizationInvitation.status == "pending"
            )
        ).first()
        
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already sent to this email"
            )
        
        # Validate role exists
        role = db.query(Role).filter(Role.name == invite_data.role).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role specified"
            )
        
        # Validate team if specified
        team = None
        if invite_data.team_id:
            team = db.query(Team).filter(
                and_(
                    Team.id == invite_data.team_id,
                    Team.organization_id == organization_id
                )
            ).first()
            
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid team specified"
                )
        
        # Create invitation
        invitation = OrganizationInvitation(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            team_id=invite_data.team_id,
            email=invite_data.email,
            role=invite_data.role,
            token=str(uuid.uuid4()),
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),  # 7 days to accept
            invited_by_id=current_user.id
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        # Send invitation email in background task
        background_tasks.add_task(
            send_invitation_email, 
            invitation, 
            tenant_context.organization, 
            current_user, 
            invite_data.message
        )
        
        return InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            team_name=team.name if team else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting user to organization {organization_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation"
        )


@router.get("/{organization_id}/invitations", response_model=List[InvitationResponse])
async def list_organization_invitations(
    organization_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List pending invitations for organization
    """
    try:
        # Setup tenant context
        tenant_context = setup_tenant_context(request, current_user, db, organization_id)
        tenant_context.ensure_organization_access()
        tenant_context.require_permission("users.read")
        
        invitations = db.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == organization_id
        ).all()
        
        invitation_responses = []
        for invitation in invitations:
            team_name = None
            if invitation.team_id:
                team = db.query(Team).filter(Team.id == invitation.team_id).first()
                team_name = team.name if team else None
            
            invitation_responses.append(InvitationResponse(
                id=invitation.id,
                email=invitation.email,
                role=invitation.role,
                status=invitation.status,
                expires_at=invitation.expires_at,
                created_at=invitation.created_at,
                team_name=team_name
            ))
        
        return invitation_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing invitations for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )