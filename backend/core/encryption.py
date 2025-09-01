"""
Versioned encryption utilities for sensitive data with key rotation support
"""
import json
import base64
import logging
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet, InvalidToken
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Base exception for encryption operations"""
    pass

class VersionedEncryption:
    """
    Handles versioned encryption with envelope format for key rotation support
    
    Envelope format:
    {
        "enc_version": 1,
        "enc_kid": "default",  # Key ID for rotation
        "ciphertext": "<base64_encoded_encrypted_data>"
    }
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize with encryption key from settings or provided key
        
        Args:
            encryption_key: Optional encryption key, uses settings if not provided
        """
        self.settings = get_settings()
        self.current_version = 1
        self.default_kid = "default"
        
        # Initialize encryption keys
        self.keys = {}
        
        # Primary key (current)
        key = encryption_key or getattr(self.settings, 'token_encryption_key', None)
        if not key:
            raise EncryptionError("TOKEN_ENCRYPTION_KEY not configured")
        
        # Ensure key is properly formatted for Fernet
        if isinstance(key, str):
            try:
                # Test if it's already a valid Fernet key
                Fernet(key.encode())
                self.keys[self.default_kid] = Fernet(key.encode())
            except Exception:
                # If not, generate a Fernet key from the string
                # For production, use proper key derivation
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'stable_salt_for_consistency',  # In production, use proper salt management
                    iterations=100000,
                )
                key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
                self.keys[self.default_kid] = Fernet(key_bytes)
        else:
            self.keys[self.default_kid] = Fernet(key)
    
    def encrypt(self, plaintext: str, kid: str = None) -> str:
        """
        Encrypt plaintext and return versioned envelope JSON string
        
        Args:
            plaintext: String to encrypt
            kid: Key ID to use (defaults to default_kid)
            
        Returns:
            JSON string with versioned envelope
            
        Raises:
            EncryptionError: If encryption fails
        """
        if plaintext is None:
            raise EncryptionError("Cannot encrypt None value")
        
        if not plaintext:
            return ""
        
        try:
            kid = kid or self.default_kid
            if kid not in self.keys:
                raise EncryptionError(f"Key ID '{kid}' not found")
            
            # Encrypt the plaintext
            encrypted_data = self.keys[kid].encrypt(plaintext.encode('utf-8'))
            
            # Create versioned envelope
            envelope = {
                "enc_version": self.current_version,
                "enc_kid": kid,
                "ciphertext": base64.b64encode(encrypted_data).decode('utf-8')
            }
            
            return json.dumps(envelope, separators=(',', ':'))
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, envelope_json: str) -> str:
        """
        Decrypt versioned envelope JSON string
        
        Args:
            envelope_json: JSON string with versioned envelope
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            EncryptionError: If decryption fails
        """
        if not envelope_json:
            return ""
        
        try:
            # Parse envelope
            envelope = json.loads(envelope_json)
            
            # Validate envelope structure
            required_fields = ["enc_version", "enc_kid", "ciphertext"]
            for field in required_fields:
                if field not in envelope:
                    raise EncryptionError(f"Invalid envelope: missing '{field}' field")
            
            # Check version compatibility
            version = envelope["enc_version"]
            if version != self.current_version:
                logger.warning(f"Decrypting data with version {version}, current is {self.current_version}")
            
            # Get appropriate key
            kid = envelope["enc_kid"]
            if kid not in self.keys:
                raise EncryptionError(f"Key ID '{kid}' not available for decryption")
            
            # Decrypt
            ciphertext = base64.b64decode(envelope["ciphertext"])
            decrypted_data = self.keys[kid].decrypt(ciphertext)
            
            return decrypted_data.decode('utf-8')
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid envelope JSON: {e}")
            raise EncryptionError("Invalid envelope format")
        except InvalidToken as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError("Failed to decrypt data: invalid token")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    def add_key(self, kid: str, key: bytes) -> None:
        """
        Add a new encryption key for rotation
        
        Args:
            kid: Key identifier
            key: Encryption key bytes
        """
        try:
            self.keys[kid] = Fernet(key)
            logger.info(f"Added encryption key: {kid}")
        except Exception as e:
            logger.error(f"Failed to add key {kid}: {e}")
            raise EncryptionError(f"Failed to add encryption key: {e}")
    
    def rotate_default_key(self, new_kid: str) -> None:
        """
        Set a new default key for encryption (decryption still works with old keys)
        
        Args:
            new_kid: Key ID to use as new default
        """
        if new_kid not in self.keys:
            raise EncryptionError(f"Key ID '{new_kid}' not found")
        
        old_default = self.default_kid
        self.default_kid = new_kid
        logger.info(f"Rotated default key from {old_default} to {new_kid}")
    
    def get_envelope_info(self, envelope_json: str) -> Dict[str, Any]:
        """
        Get metadata from encrypted envelope without decrypting
        
        Args:
            envelope_json: JSON string with versioned envelope
            
        Returns:
            Dictionary with envelope metadata
        """
        if not envelope_json:
            return {}
        
        try:
            envelope = json.loads(envelope_json)
            return {
                "enc_version": envelope.get("enc_version"),
                "enc_kid": envelope.get("enc_kid"),
                "has_ciphertext": "ciphertext" in envelope
            }
        except json.JSONDecodeError:
            return {"error": "Invalid envelope format"}


# Global instance for application use
_encryption_instance = None

def get_encryption() -> VersionedEncryption:
    """Get singleton encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = VersionedEncryption()
    return _encryption_instance

def encrypt_token(token: str) -> str:
    """Convenience function to encrypt a token"""
    return get_encryption().encrypt(token)

def decrypt_token(encrypted_token: str) -> str:
    """Convenience function to decrypt a token"""
    return get_encryption().decrypt(encrypted_token)