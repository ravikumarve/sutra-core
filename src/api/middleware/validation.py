"""
Input Validation and Sanitization
Comprehensive input validation and sanitization utilities
"""
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, validator, Field
from typing import Any, Dict, List, Optional, Union
import re
import html
import logging
from urllib.parse import urlparse

from src.security.auth import input_validator
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


class SanitizedString(str):
    """Sanitized string type"""
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        return cls(v)
    
    def __str__(self):
        return self


class InputSanitizer:
    """Input sanitization utilities"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|SCRIPT)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b|\bAND\b).*=.*=",
        r"(\bWHERE\b.*=.*\bOR\b)",
        r"(\bWHERE\b.*=.*\bAND\b)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe.*?>.*?</iframe>",
        r"<object.*?>.*?</object>",
        r"<embed.*?>.*?</embed>",
    ]
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            input_str: Input string
            max_length: Maximum allowed length
        
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """
        Sanitize HTML input (escape HTML entities)
        
        Args:
            input_str: Input string with potential HTML
        
        Returns:
            Sanitized string with HTML escaped
        """
        if not input_str:
            return ""
        
        # Escape HTML entities
        sanitized = html.escape(input_str)
        
        return sanitized
    
    @staticmethod
    def sanitize_sql(input_str: str) -> str:
        """
        Sanitize SQL input (basic SQL injection prevention)
        
        Args:
            input_str: Input string
        
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        sanitized = input_str
        
        # Remove dangerous SQL characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "exec"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized
    
    @staticmethod
    def sanitize_filename(input_str: str) -> str:
        """
        Sanitize filename input
        
        Args:
            input_str: Input filename
        
        Returns:
            Sanitized filename
        """
        if not input_str:
            return ""
        
        # Remove path traversal attempts
        sanitized = input_str.replace("..", "").replace("/", "").replace("\\", "")
        
        # Remove dangerous characters
        dangerous_chars = ["<", ">", ":", "\"", "|", "?", "*"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Limit length
        sanitized = sanitized[:255]
        
        return sanitized
    
    @staticmethod
    def sanitize_url(input_str: str) -> str:
        """
        Sanitize URL input
        
        Args:
            input_str: Input URL
        
        Returns:
            Sanitized URL or empty string if invalid
        """
        if not input_str:
            return ""
        
        try:
            # Parse URL
            parsed = urlparse(input_str)
            
            # Only allow http and https
            if parsed.scheme not in ["http", "https"]:
                return ""
            
            # Reconstruct URL
            sanitized = parsed.geturl()
            
            return sanitized
        
        except Exception:
            return ""
    
    @staticmethod
    def sanitize_email(input_str: str) -> str:
        """
        Sanitize email input
        
        Args:
            input_str: Input email
        
        Returns:
            Sanitized email or empty string if invalid
        """
        if not input_str:
            return ""
        
        # Validate email format
        if not input_validator.validate_email(input_str):
            return ""
        
        # Convert to lowercase
        sanitized = input_str.lower().strip()
        
        return sanitized
    
    @staticmethod
    def sanitize_phone(input_str: str) -> str:
        """
        Sanitize phone number input
        
        Args:
            input_str: Input phone number
        
        Returns:
            Sanitized phone number or empty string if invalid
        """
        if not input_str:
            return ""
        
        # Remove all non-numeric characters
        sanitized = re.sub(r"[^\d+]", "", input_str)
        
        # Validate phone number format
        if not input_validator.validate_phone_number(sanitized):
            return ""
        
        return sanitized


class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_sql_injection(input_str: str) -> bool:
        """
        Check for SQL injection patterns
        
        Args:
            input_str: Input string to check
        
        Returns:
            True if safe, False if SQL injection detected
        """
        if not input_str:
            return True
        
        # Check against SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {input_str[:100]}")
                return False
        
        return True
    
    @staticmethod
    def validate_xss(input_str: str) -> bool:
        """
        Check for XSS patterns
        
        Args:
            input_str: Input string to check
        
        Returns:
            True if safe, False if XSS detected
        """
        if not input_str:
            return True
        
        # Check against XSS patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {input_str[:100]}")
                return False
        
        return True
    
    @staticmethod
    def validate_length(input_str: str, min_length: int = 0, max_length: int = 1000) -> bool:
        """
        Validate string length
        
        Args:
            input_str: Input string
            min_length: Minimum allowed length
            max_length: Maximum allowed length
        
        Returns:
            True if valid, False otherwise
        """
        if not input_str:
            return min_length == 0
        
        length = len(input_str)
        return min_length <= length <= max_length
    
    @staticmethod
    def validate_range(value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float]) -> bool:
        """
        Validate numeric range
        
        Args:
            value: Numeric value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            True if valid, False otherwise
        """
        return min_value <= value <= max_value
    
    @staticmethod
    def validate_enum(value: str, allowed_values: List[str]) -> bool:
        """
        Validate enum value
        
        Args:
            value: Value to validate
            allowed_values: List of allowed values
        
        Returns:
            True if valid, False otherwise
        """
        return value in allowed_values
    
    @staticmethod
    def validate_regex(input_str: str, pattern: str) -> bool:
        """
        Validate against regex pattern
        
        Args:
            input_str: Input string
            pattern: Regex pattern
        
        Returns:
            True if valid, False otherwise
        """
        if not input_str:
            return False
        
        return bool(re.match(pattern, input_str))
    
    @staticmethod
    def validate_no_null_bytes(input_str: str) -> bool:
        """
        Check for null bytes
        
        Args:
            input_str: Input string
        
        Returns:
            True if safe, False if null bytes detected
        """
        return '\x00' not in input_str
    
    @staticmethod
    def validate_no_control_chars(input_str: str) -> bool:
        """
        Check for control characters (except newline, tab, carriage return)
        
        Args:
            input_str: Input string
        
        Returns:
            True if safe, False if control characters detected
        """
        # Allow newline, tab, carriage return
        allowed_control_chars = {'\n', '\t', '\r'}
        
        for char in input_str:
            if ord(char) < 32 and char not in allowed_control_chars:
                logger.warning(f"Control character detected: {ord(char)}")
                return False
        
        return True


class RequestValidator:
    """Request validation middleware"""
    
    @staticmethod
    async def validate_request(request: Request) -> Dict[str, Any]:
        """
        Validate incoming request
        
        Args:
            request: FastAPI request
        
        Returns:
            Validated request data
        
        Raises:
            HTTPException: If validation fails
        """
        # Get content type
        content_type = request.headers.get("content-type", "")
        
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > settings.max_request_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request too large. Maximum size is {settings.max_request_size} bytes"
                )
        
        # Only validate body for methods that typically have a body
        if request.method in ["POST", "PUT", "PATCH"]:
            # Get request body
            try:
                body = await request.json()
            except Exception as e:
                logger.error(f"Failed to parse request body: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request body"
                )
            
            # Validate body structure
            if not isinstance(body, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request body structure"
                )
            
            return body
        
        # For other methods (GET, DELETE, etc.), return empty dict
        return {}
    
    @staticmethod
    def validate_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query parameters
        
        Args:
            params: Query parameters
        
        Returns:
            Validated parameters
        
        Raises:
            HTTPException: If validation fails
        """
        validated = {}
        
        for key, value in params.items():
            # Sanitize string values
            if isinstance(value, str):
                # Check for SQL injection
                if not InputValidator.validate_sql_injection(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid parameter: {key}"
                    )
                
                # Check for XSS
                if not InputValidator.validate_xss(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid parameter: {key}"
                    )
                
                # Sanitize
                validated[key] = InputSanitizer.sanitize_string(value)
            else:
                validated[key] = value
        
        return validated


class ValidationMiddleware(BaseHTTPMiddleware):
    """Validation middleware for FastAPI"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate"""
        # Skip validation for certain routes
        skip_routes = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/agents/restart",
            "/api/v1/tenants/system/status",
        }
        # Skip body validation for POST/PUT/PATCH requests without a JSON body
        # (bodyless POST endpoints like /restart should not fail validation)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type or "application/json" not in content_type:
                return await call_next(request)
        
        if any(request.url.path.startswith(route) for route in skip_routes):
            return await call_next(request)
        
        try:
            # Validate request
            await RequestValidator.validate_request(request)
            
            # Process request
            response = await call_next(request)
            
            return response
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request validation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request validation failed"
            )


# Global instances
input_sanitizer = InputSanitizer()
input_validator = InputValidator()
request_validator = RequestValidator()