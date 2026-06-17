"""
Rate Limiting Middleware
Implements token bucket algorithm for rate limiting
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from src.security.auth import rate_limiter
from src.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    Implements token bucket algorithm for rate limiting
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Rate limit storage: {identifier: {tokens: int, last_update: datetime}}
        self.rate_limits: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Default rate limits
        self.default_requests = settings.RATE_LIMIT_REQUESTS
        self.default_period = settings.RATE_LIMIT_PERIOD
        
        # Rate limits per endpoint
        self.endpoint_limits = {
            "/api/v1/webhooks/whatsapp": {"requests": 1000, "period": 60},
            "/api/v1/auth/login": {"requests": 5, "period": 60},
            "/api/v1/auth/register": {"requests": 3, "period": 3600},
        }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting
        """
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        identifier = self._get_identifier(request)
        
        # Get rate limit for endpoint
        limit = self._get_rate_limit(request.url.path)
        
        # Check rate limit
        if not self._check_rate_limit(identifier, limit):
            logger.warning(f"Rate limit exceeded for {identifier}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Rate limit exceeded",
                    "retry_after": limit["period"]
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, identifier, limit)
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        """
        # Try to get from X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Try to get from X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit(self, path: str) -> Dict[str, int]:
        """
        Get rate limit for endpoint
        """
        # Check if endpoint has specific limit
        for endpoint_pattern, limit in self.endpoint_limits.items():
            if path.startswith(endpoint_pattern):
                return limit
        
        # Return default limit
        return {
            "requests": self.default_requests,
            "period": self.default_period
        }
    
    def _check_rate_limit(
        self,
        identifier: str,
        limit: Dict[str, int]
    ) -> bool:
        """
        Check if request is within rate limit
        """
        now = datetime.utcnow()
        period = timedelta(seconds=limit["period"])
        max_requests = limit["requests"]
        
        # Get or create rate limit entry
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = {
                "tokens": max_requests - 1,
                "last_update": now
            }
            return True
        
        rate_limit = self.rate_limits[identifier]
        
        # Check if period has elapsed
        time_since_update = now - rate_limit["last_update"]
        if time_since_update >= period:
            # Reset tokens
            rate_limit["tokens"] = max_requests - 1
            rate_limit["last_update"] = now
            return True
        
        # Check if tokens available
        if rate_limit["tokens"] > 0:
            rate_limit["tokens"] -= 1
            return True
        
        # Rate limit exceeded
        return False
    
    def _add_rate_limit_headers(
        self,
        response: Response,
        identifier: str,
        limit: Dict[str, int]
    ) -> None:
        """
        Add rate limit headers to response
        """
        rate_limit = self.rate_limits.get(identifier, {})
        tokens = rate_limit.get("tokens", limit["requests"])
        
        response.headers["X-RateLimit-Limit"] = str(limit["requests"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, tokens))
        response.headers["X-RateLimit-Reset"] = str(
            int((rate_limit.get("last_update", datetime.utcnow()) + 
                timedelta(seconds=limit["period"])).timestamp())
        )
    
    def cleanup_old_entries(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old rate limit entries
        Returns number of entries cleaned
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Find old entries
            old_identifiers = [
                identifier
                for identifier, data in self.rate_limits.items()
                if data.get("last_update", datetime.utcnow()) < cutoff_time
            ]
            
            # Remove old entries
            for identifier in old_identifiers:
                del self.rate_limits[identifier]
            
            logger.info(f"Cleaned up {len(old_identifiers)} old rate limit entries")
            return len(old_identifiers)
            
        except Exception as e:
            logger.error(f"Error cleaning up rate limit entries: {e}")
            return 0


# Global middleware instance