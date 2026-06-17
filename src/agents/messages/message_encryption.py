"""
Message Encryption and Security
Handles encryption, decryption, and security for agent messages
"""

import json
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MessageEncryption:
    """
    Handles message encryption and decryption
    Uses Fernet symmetric encryption
    """
    
    def __init__(self):
        self._key: Optional[bytes] = None
        self._cipher: Optional[Fernet] = None
        self._initialize_encryption()
    
    def _initialize_encryption(self) -> None:
        """
        Initialize encryption with secret key
        """
        try:
            # Get encryption key from settings
            secret_key = settings.SECRET_KEY.encode()
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'sutra_salt',  # In production, use random salt per tenant
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key))
            
            self._key = key
            self._cipher = Fernet(key)
            
            logger.info("Message encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data string
        Returns encrypted base64 string
        """
        try:
            if not self._cipher:
                raise RuntimeError("Encryption not initialized")
            
            # Encrypt data
            encrypted = self._cipher.encrypt(data.encode())
            
            # Return as base64 string
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data string
        Returns original data string
        """
        try:
            if not self._cipher:
                raise RuntimeError("Encryption not initialized")
            
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt data
            decrypted = self._cipher.decrypt(encrypted_bytes)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt dictionary
        Returns encrypted base64 string
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt encrypted data to dictionary
        """
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)
    
    def encrypt_message(self, message: str) -> str:
        """
        Encrypt message (alias for encrypt)
        """
        return self.encrypt(message)
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """
        Decrypt message (alias for decrypt)
        """
        return self.decrypt(encrypted_message)


class TenantEncryption:
    """
    Handles tenant-specific encryption
    Each tenant gets isolated encryption keys
    """
    
    def __init__(self):
        self._tenant_keys: Dict[str, bytes] = {}
        self._tenant_ciphers: Dict[str, Fernet] = {}
    
    def get_tenant_key(self, tenant_id: str) -> bytes:
        """
        Get or create tenant-specific encryption key
        """
        if tenant_id not in self._tenant_keys:
            # Generate tenant-specific key
            # In production, store this securely (e.g., in database)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=tenant_id.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.SECRET_KEY.encode())
            )
            
            self._tenant_keys[tenant_id] = key
            self._tenant_ciphers[tenant_id] = Fernet(key)
        
        return self._tenant_keys[tenant_id]
    
    def encrypt_tenant_message(
        self,
        tenant_id: str,
        data: str
    ) -> str:
        """
        Encrypt message for specific tenant
        """
        try:
            cipher = self._tenant_ciphers.get(tenant_id)
            
            if not cipher:
                self.get_tenant_key(tenant_id)
                cipher = self._tenant_ciphers[tenant_id]
            
            encrypted = cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt tenant message: {e}")
            raise
    
    def decrypt_tenant_message(
        self,
        tenant_id: str,
        encrypted_data: str
    ) -> str:
        """
        Decrypt message for specific tenant
        """
        try:
            cipher = self._tenant_ciphers.get(tenant_id)
            
            if not cipher:
                self.get_tenant_key(tenant_id)
                cipher = self._tenant_ciphers[tenant_id]
            
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to decrypt tenant message: {e}")
            raise


class MessageSecurity:
    """
    Security utilities for message handling
    """
    
    @staticmethod
    def sanitize_message(message: str) -> str:
        """
        Sanitize message to prevent injection attacks
        """
        # Remove potential script tags
        sanitized = message.replace("<script", "").replace("</script>", "")
        
        # Remove other potentially dangerous patterns
        sanitized = sanitized.replace("javascript:", "")
        sanitized = sanitized.replace("onerror=", "")
        sanitized = sanitized.replace("onload=", "")
        
        return sanitized
    
    @staticmethod
    def validate_message_size(message: str, max_size: int = 10485760) -> bool:
        """
        Validate message size
        Default max size: 10MB
        """
        return len(message.encode()) <= max_size
    
    @staticmethod
    def validate_message_format(message: str) -> bool:
        """
        Validate message format
        Checks if message is valid JSON
        """
        try:
            json.loads(message)
            return True
        except json.JSONDecodeError:
            return False
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in message payload
        """
        sensitive_fields = [
            "password", "api_key", "secret", "token",
            "credit_card", "ssn", "phone", "email"
        ]
        
        masked = data.copy()
        
        for key, value in masked.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(value, str) and len(value) > 4:
                    # Show first and last 2 characters
                    masked[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                else:
                    masked[key] = "***"
            elif isinstance(value, dict):
                masked[key] = MessageSecurity.mask_sensitive_data(value)
        
        return masked
    
    @staticmethod
    def generate_message_hash(message: str) -> str:
        """
        Generate hash for message integrity verification
        """
        import hashlib
        return hashlib.sha256(message.encode()).hexdigest()
    
    @staticmethod
    def verify_message_integrity(message: str, expected_hash: str) -> bool:
        """
        Verify message integrity using hash
        """
        actual_hash = MessageSecurity.generate_message_hash(message)
        return actual_hash == expected_hash


# Global instances
message_encryption = MessageEncryption()
tenant_encryption = TenantEncryption()