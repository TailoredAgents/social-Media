"""
Unit tests for partner OAuth models (SocialConnection and SocialAudit)
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.db.database import Base
from backend.db.models import SocialConnection, SocialAudit
from backend.db.multi_tenant_models import Organization
from backend.db.models import User


class TestSocialConnectionModel:
    """Test SocialConnection model functionality"""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)
        session = TestingSessionLocal()
        
        # Create test organization
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Organization",
            slug="test-org",
            plan_type="professional"
        )
        session.add(org)
        session.commit()
        
        yield session, org.id
        session.close()
    
    def test_social_connection_creation(self, db_session):
        """Test creating a social connection"""
        session, org_id = db_session
        
        connection = SocialConnection(
            organization_id=org_id,
            platform="meta",
            connection_name="My Facebook Page",
            platform_account_id="page_123456",
            platform_username="MyBusiness",
            access_token='{"enc_version":1,"enc_kid":"default","ciphertext":"encrypted_token"}',
            scopes=["pages_manage_posts", "pages_read_engagement"],
            platform_metadata={"page_id": "123456", "ig_business_id": "789012"},
            token_expires_at=datetime.now(timezone.utc) + timedelta(days=60)
        )
        
        session.add(connection)
        session.commit()
        
        # Verify creation
        assert connection.id is not None
        assert connection.organization_id == org_id
        assert connection.platform == "meta"
        assert connection.is_active is True
        assert connection.revoked_at is None
        assert connection.enc_version == 1
        assert connection.enc_kid == "default"
        assert connection.created_at is not None
        assert connection.updated_at is not None
    
    def test_social_connection_required_fields(self, db_session):
        """Test that required fields are enforced"""
        session, org_id = db_session
        
        # Missing organization_id should fail
        with pytest.raises(IntegrityError):
            connection = SocialConnection(
                platform="meta",
                connection_name="Test Connection"
            )
            session.add(connection)
            session.commit()
    
    def test_social_connection_unique_constraint(self, db_session):
        """Test unique constraint on org_id + platform + platform_account_id"""
        session, org_id = db_session
        
        # Create first connection
        connection1 = SocialConnection(
            organization_id=org_id,
            platform="meta",
            platform_account_id="page_123",
            connection_name="First Connection"
        )
        session.add(connection1)
        session.commit()
        
        # Try to create duplicate (should fail)
        with pytest.raises(IntegrityError):
            connection2 = SocialConnection(
                organization_id=org_id,
                platform="meta",
                platform_account_id="page_123",  # Same platform account
                connection_name="Duplicate Connection"
            )
            session.add(connection2)
            session.commit()
    
    def test_social_connection_json_fields(self, db_session):
        """Test JSON field handling"""
        session, org_id = db_session
        
        scopes = ["scope1", "scope2", "scope3"]
        metadata = {
            "page_id": "123456",
            "ig_business_id": "789012",
            "page_name": "My Business Page",
            "ig_username": "mybusiness"
        }
        
        connection = SocialConnection(
            organization_id=org_id,
            platform="meta",
            scopes=scopes,
            platform_metadata=metadata
        )
        
        session.add(connection)
        session.commit()
        session.refresh(connection)
        
        # Verify JSON fields
        assert connection.scopes == scopes
        assert connection.platform_metadata == metadata
        assert connection.platform_metadata["page_id"] == "123456"
    
    def test_social_connection_token_expiry(self, db_session):
        """Test token expiry handling"""
        session, org_id = db_session
        
        # Create connection with expired token
        expired_time = datetime.now(timezone.utc) - timedelta(days=1)
        connection = SocialConnection(
            organization_id=org_id,
            platform="x",
            token_expires_at=expired_time
        )
        
        session.add(connection)
        session.commit()
        
        # Verify expiry
        assert connection.token_expires_at < datetime.now(timezone.utc)
    
    def test_social_connection_platform_types(self, db_session):
        """Test different platform types"""
        session, org_id = db_session
        
        platforms = ["meta", "x", "linkedin", "tiktok"]
        
        for platform in platforms:
            connection = SocialConnection(
                organization_id=org_id,
                platform=platform,
                platform_account_id=f"{platform}_account_123"
            )
            session.add(connection)
        
        session.commit()
        
        # Verify all platforms were created
        connections = session.query(SocialConnection).filter(
            SocialConnection.organization_id == org_id
        ).all()
        
        assert len(connections) == len(platforms)
        created_platforms = [conn.platform for conn in connections]
        for platform in platforms:
            assert platform in created_platforms


class TestSocialAuditModel:
    """Test SocialAudit model functionality"""
    
    @pytest.fixture
    def db_session_with_connection(self):
        """Create database with organization and social connection"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)
        session = TestingSessionLocal()
        
        # Create test data
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Organization",
            slug="test-org"
        )
        session.add(org)
        
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password"
        )
        session.add(user)
        
        connection = SocialConnection(
            organization_id=org.id,
            platform="meta",
            connection_name="Test Connection"
        )
        session.add(connection)
        session.commit()
        
        yield session, org.id, connection.id, user.id
        session.close()
    
    def test_social_audit_creation(self, db_session_with_connection):
        """Test creating a social audit entry"""
        session, org_id, connection_id, user_id = db_session_with_connection
        
        audit = SocialAudit(
            organization_id=org_id,
            connection_id=connection_id,
            action="connect",
            platform="meta",
            user_id=user_id,
            audit_metadata={"ip_address": "192.168.1.1", "user_agent": "TestAgent"},
            status="success"
        )
        
        session.add(audit)
        session.commit()
        
        # Verify creation
        assert audit.id is not None
        assert audit.organization_id == org_id
        assert audit.connection_id == connection_id
        assert audit.action == "connect"
        assert audit.platform == "meta"
        assert audit.user_id == user_id
        assert audit.status == "success"
        assert audit.created_at is not None
        assert audit.audit_metadata["ip_address"] == "192.168.1.1"
    
    def test_social_audit_actions(self, db_session_with_connection):
        """Test different audit action types"""
        session, org_id, connection_id, user_id = db_session_with_connection
        
        actions = ["connect", "disconnect", "refresh", "publish", "webhook_verify"]
        
        for action in actions:
            audit = SocialAudit(
                organization_id=org_id,
                connection_id=connection_id,
                action=action,
                platform="meta",
                user_id=user_id,
                status="success"
            )
            session.add(audit)
        
        session.commit()
        
        # Verify all actions were created
        audits = session.query(SocialAudit).filter(
            SocialAudit.organization_id == org_id
        ).all()
        
        assert len(audits) == len(actions)
        created_actions = [audit.action for audit in audits]
        for action in actions:
            assert action in created_actions
    
    def test_social_audit_error_handling(self, db_session_with_connection):
        """Test audit entries with errors"""
        session, org_id, connection_id, user_id = db_session_with_connection
        
        audit = SocialAudit(
            organization_id=org_id,
            connection_id=connection_id,
            action="refresh",
            platform="meta",
            user_id=user_id,
            status="failure",
            error_message="Token refresh failed: invalid_grant",
            audit_metadata={"error_code": "invalid_grant", "attempt": 3}
        )
        
        session.add(audit)
        session.commit()
        
        # Verify error handling
        assert audit.status == "failure"
        assert audit.error_message == "Token refresh failed: invalid_grant"
        assert audit.audit_metadata["error_code"] == "invalid_grant"
        assert audit.audit_metadata["attempt"] == 3
    
    def test_social_audit_optional_fields(self, db_session_with_connection):
        """Test audit with minimal required fields"""
        session, org_id, connection_id, user_id = db_session_with_connection
        
        # Create audit with only required field (action)
        audit = SocialAudit(action="webhook_verify")
        session.add(audit)
        session.commit()
        
        # Verify creation with nulls
        assert audit.id is not None
        assert audit.organization_id is None
        assert audit.connection_id is None
        assert audit.platform is None
        assert audit.user_id is None
        assert audit.action == "webhook_verify"
    
    def test_social_audit_foreign_key_cascade(self, db_session_with_connection):
        """Test foreign key cascading behavior"""
        session, org_id, connection_id, user_id = db_session_with_connection
        
        # Create audit entry
        audit = SocialAudit(
            organization_id=org_id,
            connection_id=connection_id,
            action="connect",
            user_id=user_id
        )
        session.add(audit)
        session.commit()
        audit_id = audit.id
        
        # Delete the connection (should cascade to audit)
        connection = session.query(SocialConnection).filter(
            SocialConnection.id == connection_id
        ).first()
        session.delete(connection)
        session.commit()
        
        # Verify audit was deleted due to cascade
        remaining_audit = session.query(SocialAudit).filter(
            SocialAudit.id == audit_id
        ).first()
        assert remaining_audit is None


class TestSocialConnectionAuditRelationship:
    """Test relationship between SocialConnection and SocialAudit"""
    
    @pytest.fixture
    def db_session_with_data(self):
        """Create database with test data"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)
        session = TestingSessionLocal()
        
        # Create test organization
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Organization",
            slug="test-org"
        )
        session.add(org)
        session.commit()
        
        yield session, org.id
        session.close()
    
    def test_connection_audit_relationship(self, db_session_with_data):
        """Test that connection can access its audit logs"""
        session, org_id = db_session_with_data
        
        # Create connection
        connection = SocialConnection(
            organization_id=org_id,
            platform="meta",
            connection_name="Test Connection"
        )
        session.add(connection)
        session.commit()
        
        # Create audit entries
        for i in range(3):
            audit = SocialAudit(
                organization_id=org_id,
                connection_id=connection.id,
                action=f"action_{i}",
                status="success"
            )
            session.add(audit)
        
        session.commit()
        session.refresh(connection)
        
        # Test relationship
        assert len(connection.audit_logs) == 3
        for i, audit in enumerate(connection.audit_logs):
            assert audit.action == f"action_{i}"
            assert audit.connection_id == connection.id