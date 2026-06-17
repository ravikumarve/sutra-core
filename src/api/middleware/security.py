"""
API Middleware
Authentication, rate limiting, and request validation
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Callable
from functools import wraps
import logging
import time
import hashlib
from collections import defaultdict

from src.security.auth import auth_manager, rate_limiter
from src.security.rbac import tenant_context, Role
from src.config.settings import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class SecurityMiddleware(BaseHTTPMiddleware):
    """General security middleware for common security checks"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and apply security measures"""
        # Add security headers
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


class AuthenticationMiddleware:
    """Middleware for JWT authentication"""
    
    def __init__(self):
        self.optional_routes = {
            "/health",
            "/auth/login",
            "/auth/register",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request and authenticate user"""
        # Skip authentication for public routes
        if any(request.url.path.startswith(route) for route in self.optional_routes):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        
        try:
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Decode and verify token
            payload = auth_manager.decode_token(token)
            
            # Set tenant context
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")
            role_str = payload.get("role")
            
            if user_id and tenant_id and role_str:
                try:
                    role = Role(role_str)
                    tenant_context.set_tenant_context(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        role=role
                    )
                    logger.debug(
                        f"User authenticated: user_id={user_id}, "
                        f"tenant_id={tenant_id}, role={role}"
                    )
                except ValueError:
                    logger.warning(f"Invalid role in token: {role_str}")
            
            # Process request
            response = await call_next(request)
            
            # Clear context after request
            tenant_context.clear_context()
            
            return response
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


class RateLimitMiddleware:
    """Middleware for rate limiting"""
    
    def __init__(self):
        self.request_counts = defaultdict(list)
        self.blocked_ips = defaultdict(float)
    
    async def __call__(self, request: Request, call_next):
        """Process request and apply rate limiting"""
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create unique identifier
        identifier = f"{client_ip}:{user_agent}"
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            block_expiry = self.blocked_ips[client_ip]
            if time.time() < block_expiry:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )
            else:
                del self.blocked_ips[client_ip]
        
        # Check rate limit
        if not rate_limiter.is_allowed(identifier):
            # Block IP for 1 hour
            self.blocked_ips[client_ip] = time.time() + 3600
            
            logger.warning(f"Rate limit exceeded for {client_ip}")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add rate limit headers
        remaining = rate_limiter.get_remaining_requests(identifier)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + settings.rate_limit_period)
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RequestSizeMiddleware:
    """Middleware for request size limiting"""
    
    def __init__(self):
        self.max_size = settings.max_request_size
    
    async def __call__(self, request: Request, call_next):
        """Process request and check size"""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request too large. Maximum size is {self.max_size} bytes"
                )
        
        # Process request
        return await call_next(request)


class SecurityHeadersMiddleware:
    """Middleware for security headers"""
    
    async def __call__(self, request: Request, call_next):
        """Process request and add security headers"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RequestLoggingMiddleware:
    """Middleware for request logging"""
    
    async def __call__(self, request: Request, call_next):
        """Process request and log details"""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"took {process_time:.3f}s"
        )
        
        return response


class RequestIDMiddleware:
    """Middleware for request ID tracking"""
    
    async def __call__(self, request: Request, call_next):
        """Process request and add request ID"""
        # Generate request ID
        request_id = hashlib.sha256(
            f"{time.time()}:{request.client.host}".encode()
        ).hexdigest()[:16]
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


# Decorator for requiring authentication
def require_auth():
    """Decorator to require authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Authentication is handled by middleware
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Decorator for requiring specific role
def require_role(role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_role = tenant_context.get_role()
            
            if current_role != role and current_role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {role} role"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Decorator for requiring admin role
def require_admin():
    """Decorator to require admin role"""
    return require_role(Role.ADMIN)


# Decorator for requiring minimum role
def require_min_role(min_role: Role):
    """Decorator to require minimum role level"""
    role_hierarchy = {
        Role.VIEWER: 0,
        Role.STAFF: 1,
        Role.MANAGER: 2,
        Role.SHOP_OWNER: 3,
        Role.ADMIN: 4,
    }
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_role = tenant_context.get_role()
            current_level = role_hierarchy.get(current_role, 0)
            min_level = role_hierarchy.get(min_role, 0)
            
            if current_level < min_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires at least {min_role} role"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global middleware instances
auth_middleware = AuthenticationMiddleware()
rate_limit_middleware = RateLimitMiddleware()
request_size_middleware = RequestSizeMiddleware()
security_headers_middleware = SecurityHeadersMiddleware()
request_logging_middleware = RequestLoggingMiddleware()
request_id_middleware = RequestIDMiddleware()