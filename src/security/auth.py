"""
Security Utilities
Authentication, encryption, and input validation
"""
import jwt
import hashlib
import secrets
import re
import base64
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, status
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationManager:
    """Manages JWT authentication and password hashing"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify token and return payload"""
        payload = self.decode_token(token)
        
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}"
            )
        
        return payload


class EncryptionManager:
    """Manages data encryption and decryption using AES-256"""
    
    def __init__(self):
        self.encryption_key = settings.encryption_key
        self._fernet = None
        
        if not self.encryption_key:
            # Generate a key if not provided (not recommended for production)
            self.encryption_key = secrets.token_urlsafe(32)
            logger.warning("Generated random encryption key - not recommended for production")
        
        # Initialize Fernet with the key
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize Fernet cipher with proper key derivation"""
        try:
            # Use PBKDF2 to derive a proper Fernet key from the encryption key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'sutra_salt',  # In production, use a random salt per deployment
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data using AES-256 (via Fernet)
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""
        
        try:
            # Convert string to bytes
            data_bytes = data.encode('utf-8')
            
            # Encrypt using Fernet (AES-128 in CBC mode with HMAC)
            encrypted_bytes = self._fernet.encrypt(data_bytes)
            
            # Return as base64 string
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using AES-256 (via Fernet)
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plain text string
        """
        if not encrypted_data:
            return ""
        
        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt using Fernet
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Convert back to string
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt all string values in a dictionary
        
        Args:
            data: Dictionary with string values
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_dict(value)
            else:
                encrypted[key] = value
        return encrypted
    
    def decrypt_dict(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypt all string values in a dictionary
        
        Args:
            data: Dictionary with encrypted string values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except ValueError:
                    # If decryption fails, keep original value
                    decrypted[key] = value
            elif isinstance(value, dict):
                decrypted[key] = self.decrypt_dict(value)
            else:
                decrypted[key] = value
        return decrypted
    
    def generate_key(self) -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64 encoded encryption key
        """
        return secrets.token_urlsafe(32)


class InputValidator:
    """Validates and sanitizes user input"""
    
    # Phone number patterns
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    
    # Email pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # GSTIN pattern (Indian GST identification)
    GSTIN_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
    
    # HSN code pattern
    HSN_PATTERN = re.compile(r'^[0-9]{4,8}$')
    
    # Safe characters for text input
    SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,@#$%&*()!?\'":;]+$')
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        return bool(InputValidator.PHONE_PATTERN.match(phone))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """Validate GSTIN format"""
        if not gstin:
            return False
        return bool(InputValidator.GSTIN_PATTERN.match(gstin))
    
    @staticmethod
    def validate_hsn_code(hsn: str) -> bool:
        """Validate HSN code format"""
        if not hsn:
            return False
        return bool(InputValidator.HSN_PATTERN.match(hsn))
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        text = text[:max_length]
        
        return text
    
    @staticmethod
    def sanitize_sql_input(input_str: str) -> str:
        """Basic SQL injection prevention"""
        if not input_str:
            return ""
        
        # Remove dangerous SQL characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "exec"]
        for char in dangerous_chars:
            input_str = input_str.replace(char, "")
        
        return input_str
    
    @staticmethod
    def validate_positive_number(value: float, field_name: str = "value") -> bool:
        """Validate that a number is positive"""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")
        if value < 0:
            raise ValueError(f"{field_name} must be positive")
        return True
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str = "value") -> bool:
        """Validate that a string is not empty"""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")
        if not value.strip():
            raise ValueError(f"{field_name} cannot be empty")
        return True
    
    @staticmethod
    def validate_enum(value: str, allowed_values: List[str], field_name: str = "value") -> bool:
        """Validate that value is in allowed enum values"""
        if value not in allowed_values:
            raise ValueError(
                f"{field_name} must be one of {allowed_values}, got '{value}'"
            )
        return True
    
    @staticmethod
    def validate_length(value: str, min_length: int = 0, max_length: int = 1000, field_name: str = "value") -> bool:
        """Validate string length"""
        if len(value) < min_length:
            raise ValueError(
                f"{field_name} must be at least {min_length} characters"
            )
        if len(value) > max_length:
            raise ValueError(
                f"{field_name} must be at most {max_length} characters"
            )
        return True


class WebhookSecurity:
    """Webhook signature verification and security"""
    
    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        app_secret: str
    ) -> bool:
        """Verify Meta webhook signature"""
        # Meta uses HMAC-SHA256 for webhook signatures
        expected_signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures securely
        return secrets.compare_digest(signature, expected_signature)
    
    @staticmethod
    def generate_webhook_signature(payload: bytes, app_secret: str) -> str:
        """Generate webhook signature for testing"""
        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return signature


class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}  # In-memory storage (use Redis in production)
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = None,
        period: int = None
    ) -> bool:
        """Check if request is allowed"""
        max_requests = max_requests or settings.rate_limit_requests
        period = period or settings.rate_limit_period
        
        now = datetime.utcnow()
        timestamp = now.timestamp()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if timestamp - req_time < period
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(timestamp)
        return True
    
    def get_remaining_requests(
        self,
        identifier: str,
        max_requests: int = None
    ) -> int:
        """Get remaining requests for identifier"""
        max_requests = max_requests or settings.rate_limit_requests
        
        if identifier not in self.requests:
            return max_requests
        
        return max_requests - len(self.requests[identifier])


# Global instances
auth_manager = AuthenticationManager()
encryption_manager = EncryptionManager()
input_validator = InputValidator()
webhook_security = WebhookSecurity()
rate_limiter = RateLimiter()


# Import hmac at module level
import hmac


# Convenience functions for backward compatibility
def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify JWT token (wrapper for auth_manager.verify_token)"""
    return auth_manager.verify_token(token, token_type)


def get_current_user(credentials) -> Dict[str, Any]:
    """Get current user from credentials (wrapper for auth_manager.get_current_user)"""
    from fastapi import HTTPException, status
    try:
        return auth_manager.verify_token(credentials.credentials, "access")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )