"""
Unit tests for versioned encryption utilities
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from backend.core.encryption import (
    VersionedEncryption, 
    EncryptionError, 
    get_encryption,
    encrypt_token,
    decrypt_token
)


class TestVersionedEncryption:
    """Test the VersionedEncryption class"""
    
    @pytest.fixture
    def test_key(self):
        """Generate a test Fernet key"""
        return Fernet.generate_key().decode()
    
    @pytest.fixture
    def encryption(self, test_key):
        """Create encryption instance with test key"""
        return VersionedEncryption(test_key)
    
    def test_encryption_initialization(self, test_key):
        """Test proper initialization of encryption instance"""
        enc = VersionedEncryption(test_key)
        assert enc.current_version == 1
        assert enc.default_kid == "default"
        assert "default" in enc.keys
    
    def test_encryption_initialization_without_key_fails(self):
        """Test that initialization fails without proper key"""
        with patch('backend.core.encryption.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(token_encryption_key=None)
            with pytest.raises(EncryptionError, match="TOKEN_ENCRYPTION_KEY not configured"):
                VersionedEncryption()
    
    def test_encrypt_decrypt_cycle(self, encryption):
        """Test basic encrypt/decrypt functionality"""
        plaintext = "sensitive_access_token_12345"
        
        # Encrypt
        encrypted = encryption.encrypt(plaintext)
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        
        # Verify envelope structure
        envelope = json.loads(encrypted)
        assert envelope["enc_version"] == 1
        assert envelope["enc_kid"] == "default"
        assert "ciphertext" in envelope
        
        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_empty_string(self, encryption):
        """Test encryption of empty string"""
        encrypted = encryption.encrypt("")
        assert encrypted == ""
        
        decrypted = encryption.decrypt("")
        assert decrypted == ""
    
    def test_encrypt_none_raises_error(self, encryption):
        """Test that encrypting None raises appropriate error"""
        with pytest.raises(EncryptionError, match="Cannot encrypt None value"):
            encryption.encrypt(None)
    
    def test_decrypt_invalid_json_raises_error(self, encryption):
        """Test that invalid JSON raises EncryptionError"""
        with pytest.raises(EncryptionError, match="Invalid envelope format"):
            encryption.decrypt("not_valid_json")
    
    def test_decrypt_missing_fields_raises_error(self, encryption):
        """Test that missing envelope fields raise error"""
        invalid_envelope = json.dumps({"enc_version": 1, "ciphertext": "test"})
        with pytest.raises(EncryptionError, match="missing 'enc_kid' field"):
            encryption.decrypt(invalid_envelope)
    
    def test_decrypt_unknown_key_id_raises_error(self, encryption):
        """Test that unknown key ID raises error"""
        envelope = {
            "enc_version": 1,
            "enc_kid": "unknown_key",
            "ciphertext": "dGVzdA=="  # base64 encoded "test"
        }
        with pytest.raises(EncryptionError, match="Key ID 'unknown_key' not available"):
            encryption.decrypt(json.dumps(envelope))
    
    def test_decrypt_invalid_ciphertext_raises_error(self, encryption):
        """Test that invalid ciphertext raises error"""
        envelope = {
            "enc_version": 1,
            "enc_kid": "default",
            "ciphertext": "invalid_base64_===="
        }
        with pytest.raises(EncryptionError, match="Failed to decrypt data"):
            encryption.decrypt(json.dumps(envelope))
    
    def test_add_key_functionality(self, encryption):
        """Test adding new encryption keys"""
        new_key = Fernet.generate_key()
        encryption.add_key("backup", new_key)
        
        assert "backup" in encryption.keys
        
        # Test encryption with new key
        plaintext = "test with backup key"
        encrypted = encryption.encrypt(plaintext, kid="backup")
        envelope = json.loads(encrypted)
        assert envelope["enc_kid"] == "backup"
        
        # Should still be able to decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_key_rotation(self, encryption):
        """Test key rotation functionality"""
        # Add a new key
        new_key = Fernet.generate_key()
        encryption.add_key("v2", new_key)
        
        # Encrypt with old default key
        old_encrypted = encryption.encrypt("old key data")
        old_envelope = json.loads(old_encrypted)
        assert old_envelope["enc_kid"] == "default"
        
        # Rotate to new key
        encryption.rotate_default_key("v2")
        assert encryption.default_kid == "v2"
        
        # New encryptions use new key
        new_encrypted = encryption.encrypt("new key data")
        new_envelope = json.loads(new_encrypted)
        assert new_envelope["enc_kid"] == "v2"
        
        # But old data can still be decrypted
        assert encryption.decrypt(old_encrypted) == "old key data"
        assert encryption.decrypt(new_encrypted) == "new key data"
    
    def test_rotate_to_nonexistent_key_raises_error(self, encryption):
        """Test that rotating to non-existent key raises error"""
        with pytest.raises(EncryptionError, match="Key ID 'nonexistent' not found"):
            encryption.rotate_default_key("nonexistent")
    
    def test_get_envelope_info(self, encryption):
        """Test envelope metadata extraction"""
        plaintext = "test data"
        encrypted = encryption.encrypt(plaintext)
        
        info = encryption.get_envelope_info(encrypted)
        assert info["enc_version"] == 1
        assert info["enc_kid"] == "default"
        assert info["has_ciphertext"] is True
        
        # Test with empty string
        empty_info = encryption.get_envelope_info("")
        assert empty_info == {}
        
        # Test with invalid JSON
        invalid_info = encryption.get_envelope_info("invalid json")
        assert "error" in invalid_info
    
    def test_unicode_support(self, encryption):
        """Test encryption/decryption of unicode strings"""
        unicode_text = "Test with émojis 🔐🔑 and ünicode"
        encrypted = encryption.encrypt(unicode_text)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == unicode_text
    
    def test_long_text_support(self, encryption):
        """Test encryption of long text"""
        long_text = "x" * 10000  # 10KB of text
        encrypted = encryption.encrypt(long_text)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == long_text


class TestGlobalEncryptionFunctions:
    """Test global encryption convenience functions"""
    
    @pytest.fixture(autouse=True)
    def setup_mock_settings(self):
        """Mock settings for global functions"""
        test_key = Fernet.generate_key().decode()
        with patch('backend.core.encryption.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(token_encryption_key=test_key)
            yield
    
    def test_get_encryption_singleton(self):
        """Test that get_encryption returns singleton"""
        enc1 = get_encryption()
        enc2 = get_encryption()
        assert enc1 is enc2
    
    def test_encrypt_decrypt_token_functions(self):
        """Test convenience functions for token encryption"""
        token = "access_token_12345"
        
        encrypted = encrypt_token(token)
        assert encrypted != token
        
        decrypted = decrypt_token(encrypted)
        assert decrypted == token
    
    def test_encrypt_decrypt_empty_token(self):
        """Test convenience functions with empty tokens"""
        assert encrypt_token("") == ""
        assert decrypt_token("") == ""


class TestEncryptionKeyDerivation:
    """Test key derivation from string keys"""
    
    def test_string_key_derivation(self):
        """Test that string keys are properly derived"""
        string_key = "my_secret_key_string"
        enc = VersionedEncryption(string_key)
        
        # Should be able to encrypt/decrypt
        plaintext = "test data"
        encrypted = enc.encrypt(plaintext)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_same_string_key_produces_same_derived_key(self):
        """Test that same string key produces consistent derived key"""
        string_key = "consistent_key"
        
        enc1 = VersionedEncryption(string_key)
        data = "test data"
        encrypted1 = enc1.encrypt(data)
        
        enc2 = VersionedEncryption(string_key)
        # Should be able to decrypt with second instance
        decrypted = enc2.decrypt(encrypted1)
        assert decrypted == data
    
    def test_different_string_keys_produce_different_derived_keys(self):
        """Test that different string keys can't decrypt each other's data"""
        enc1 = VersionedEncryption("key1")
        enc2 = VersionedEncryption("key2")
        
        data = "test data"
        encrypted_with_key1 = enc1.encrypt(data)
        
        # Should not be able to decrypt with different key
        with pytest.raises(EncryptionError):
            enc2.decrypt(encrypted_with_key1)