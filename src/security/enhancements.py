"""
Security Enhancements
Additional security features including headers, monitoring, and access control
"""
import logging
import time
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import ipaddress
from collections import defaultdict
from src.config.settings import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for enhanced security
    Adds security headers to all HTTP responses
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class SecurityEventLogger:
    """
    Security event logging and monitoring
    Logs security-related events for audit and monitoring
    """
    
    def __init__(self):
        self.security_events: List[Dict[str, Any]] = []
        self.event_types = {
            "AUTH_SUCCESS": "info",
            "AUTH_FAILURE": "warning",
            "AUTH_TOKEN_EXPIRED": "warning",
            "AUTH_TOKEN_INVALID": "warning",
            "RATE_LIMIT_EXCEEDED": "warning",
            "IP_BLOCKED": "error",
            "SUSPICIOUS_ACTIVITY": "warning",
            "DATA_ACCESS": "info",
            "DATA_MODIFICATION": "info",
            "PRIVILEGE_ESCALATION": "error",
        }
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security event
        
        Args:
            event_type: Type of security event
            user_id: User ID (if applicable)
            tenant_id: Tenant ID (if applicable)
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional event details
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        # Add to event log
        self.security_events.append(event)
        
        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        # Log based on event type severity
        log_level = self.event_types.get(event_type, "info")
        log_method = getattr(logger, log_level)
        
        log_method(
            f"Security Event: {event_type} - "
            f"User: {user_id}, Tenant: {tenant_id}, IP: {ip_address}"
        )
    
    def get_security_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get security events with optional filtering
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            limit: Maximum number of events to return
            
        Returns:
            List of security events
        """
        events = self.security_events
        
        # Apply filters
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        if user_id:
            events = [e for e in events if e["user_id"] == user_id]
        
        if tenant_id:
            events = [e for e in events if e["tenant_id"] == tenant_id]
        
        # Return most recent events
        return events[-limit:]
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security summary for specified time period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Security summary statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_events = [
            e for e in self.security_events
            if datetime.fromisoformat(e["timestamp"]) >= cutoff_time
        ]
        
        # Count events by type
        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event["event_type"]] += 1
        
        # Count unique users and IPs
        unique_users = len(set(e["user_id"] for e in recent_events if e["user_id"]))
        unique_ips = len(set(e["ip_address"] for e in recent_events if e["ip_address"]))
        
        return {
            "total_events": len(recent_events),
            "event_counts": dict(event_counts),
            "unique_users": unique_users,
            "unique_ips": unique_ips,
            "time_period_hours": hours
        }


class IPAccessControl:
    """
    IP-based access control and rate limiting
    Manages IP whitelisting, blacklisting, and rate limiting
    """
    
    def __init__(self):
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.suspicious_ips: Set[str] = set()
        
        # Default rate limits
        self.default_rate_limit = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
    
    def add_to_whitelist(self, ip_address: str) -> None:
        """Add IP address to whitelist"""
        try:
            ip = ipaddress.ip_address(ip_address)
            self.whitelist.add(str(ip))
            logger.info(f"Added IP to whitelist: {ip_address}")
        except ValueError as e:
            logger.error(f"Invalid IP address: {ip_address} - {e}")
    
    def add_to_blacklist(self, ip_address: str) -> None:
        """Add IP address to blacklist"""
        try:
            ip = ipaddress.ip_address(ip_address)
            self.blacklist.add(str(ip))
            logger.warning(f"Added IP to blacklist: {ip_address}")
        except ValueError as e:
            logger.error(f"Invalid IP address: {ip_address} - {e}")
    
    def remove_from_whitelist(self, ip_address: str) -> None:
        """Remove IP address from whitelist"""
        self.whitelist.discard(ip_address)
        logger.info(f"Removed IP from whitelist: {ip_address}")
    
    def remove_from_blacklist(self, ip_address: str) -> None:
        """Remove IP address from blacklist"""
        self.blacklist.discard(ip_address)
        logger.info(f"Removed IP from blacklist: {ip_address}")
    
    def is_whitelisted(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return any(ip in ipaddress.ip_network(whitelist_ip) for whitelist_ip in self.whitelist)
        except ValueError:
            return False
    
    def is_blacklisted(self, ip_address: str) -> bool:
        """Check if IP address is blacklisted"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return any(ip in ipaddress.ip_network(blacklist_ip) for blacklist_ip in self.blacklist)
        except ValueError:
            return False
    
    def check_rate_limit(
        self,
        ip_address: str,
        endpoint: str = "default"
    ) -> bool:
        """
        Check if IP address has exceeded rate limit
        
        Args:
            ip_address: Client IP address
            endpoint: Endpoint identifier
            
        Returns:
            True if rate limit not exceeded, False otherwise
        """
        now = datetime.utcnow()
        key = f"{ip_address}:{endpoint}"
        
        # Initialize rate limit tracking if not exists
        if key not in self.rate_limits:
            self.rate_limits[key] = {
                "requests": [],
                "blocked_until": None
            }
        
        rate_limit_data = self.rate_limits[key]
        
        # Check if IP is currently blocked
        if rate_limit_data["blocked_until"] and now < rate_limit_data["blocked_until"]:
            return False
        
        # Clean old requests (older than 1 day)
        rate_limit_data["requests"] = [
            req_time for req_time in rate_limit_data["requests"]
            if now - req_time < timedelta(days=1)
        ]
        
        # Check rate limits
        requests = rate_limit_data["requests"]
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        if len([r for r in requests if r >= minute_ago]) >= self.default_rate_limit["requests_per_minute"]:
            # Block for 1 minute
            rate_limit_data["blocked_until"] = now + timedelta(minutes=1)
            logger.warning(f"Rate limit exceeded (per-minute) for IP: {ip_address}")
            return False
        
        # Check per-hour limit
        hour_ago = now - timedelta(hours=1)
        if len([r for r in requests if r >= hour_ago]) >= self.default_rate_limit["requests_per_hour"]:
            # Block for 10 minutes
            rate_limit_data["blocked_until"] = now + timedelta(minutes=10)
            logger.warning(f"Rate limit exceeded (per-hour) for IP: {ip_address}")
            return False
        
        # Check per-day limit
        day_ago = now - timedelta(days=1)
        if len([r for r in requests if r >= day_ago]) >= self.default_rate_limit["requests_per_day"]:
            # Block for 1 hour
            rate_limit_data["blocked_until"] = now + timedelta(hours=1)
            logger.warning(f"Rate limit exceeded (per-day) for IP: {ip_address}")
            return False
        
        # Add current request
        rate_limit_data["requests"].append(now)
        
        return True
    
    def mark_suspicious(self, ip_address: str, reason: str) -> None:
        """
        Mark IP address as suspicious
        
        Args:
            ip_address: IP address to mark
            reason: Reason for marking as suspicious
        """
        self.suspicious_ips.add(ip_address)
        logger.warning(f"Marked IP as suspicious: {ip_address} - Reason: {reason}")
    
    def is_suspicious(self, ip_address: str) -> bool:
        """Check if IP address is marked as suspicious"""
        return ip_address in self.suspicious_ips
    
    def get_rate_limit_status(self, ip_address: str) -> Dict[str, Any]:
        """
        Get rate limit status for IP address
        
        Args:
            ip_address: IP address to check
            
        Returns:
            Rate limit status information
        """
        now = datetime.utcnow()
        status = {
            "ip_address": ip_address,
            "is_whitelisted": self.is_whitelisted(ip_address),
            "is_blacklisted": self.is_blacklisted(ip_address),
            "is_suspicious": self.is_suspicious(ip_address),
            "is_blocked": False,
            "blocked_until": None,
            "request_counts": {
                "per_minute": 0,
                "per_hour": 0,
                "per_day": 0
            }
        }
        
        # Check if blocked
        for key, data in self.rate_limits.items():
            if key.startswith(ip_address):
                if data["blocked_until"] and now < data["blocked_until"]:
                    status["is_blocked"] = True
                    status["blocked_until"] = data["blocked_until"].isoformat()
                
                # Count requests
                requests = data["requests"]
                now = datetime.utcnow()
                
                status["request_counts"]["per_minute"] = len([
                    r for r in requests if r >= now - timedelta(minutes=1)
                ])
                status["request_counts"]["per_hour"] = len([
                    r for r in requests if r >= now - timedelta(hours=1)
                ])
                status["request_counts"]["per_day"] = len([
                    r for r in requests if r >= now - timedelta(days=1)
                ])
                break
        
        return status


class SessionManager:
    """
    Enhanced session management
    Manages user sessions with security features
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout_minutes = 30
    
    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """
        Create new user session
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "is_active": True
        }
        
        self.sessions[session_id] = session
        logger.info(f"Created session for user {user_id}: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session is expired
        if datetime.utcnow() - session["last_activity"] > timedelta(minutes=self.session_timeout_minutes):
            self.invalidate_session(session_id)
            return None
        
        # Update last activity
        session["last_activity"] = datetime.utcnow()
        
        return session
    
    def invalidate_session(self, session_id: str) -> None:
        """
        Invalidate session
        
        Args:
            session_id: Session ID to invalidate
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["is_active"] = False
            logger.info(f"Invalidated session: {session_id}")
    
    def invalidate_user_sessions(self, user_id: str) -> None:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User ID
        """
        invalidated_count = 0
        for session_id, session in self.sessions.items():
            if session["user_id"] == user_id and session["is_active"]:
                self.invalidate_session(session_id)
                invalidated_count += 1
        
        logger.info(f"Invalidated {invalidated_count} sessions for user {user_id}")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if not session["is_active"] or (now - session["last_activity"] > timedelta(minutes=self.session_timeout_minutes)):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get active sessions
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of active sessions
        """
        active_sessions = []
        
        for session in self.sessions.values():
            if session["is_active"]:
                if user_id is None or session["user_id"] == user_id:
                    active_sessions.append(session)
        
        return active_sessions


class SecurityMonitor:
    """
    Comprehensive security monitoring
    Combines all security monitoring features
    """
    
    def __init__(self):
        self.event_logger = SecurityEventLogger()
        self.ip_access_control = IPAccessControl()
        self.session_manager = SessionManager()
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security event"""
        self.event_logger.log_security_event(
            event_type, user_id, tenant_id, ip_address, user_agent, details
        )
    
    def check_ip_access(self, ip_address: str, endpoint: str = "default") -> bool:
        """Check IP access control"""
        # Check blacklist first
        if self.ip_access_control.is_blacklisted(ip_address):
            self.log_security_event(
                "IP_BLOCKED",
                ip_address=ip_address,
                details={"reason": "IP is blacklisted"}
            )
            return False
        
        # Check whitelist (if whitelist is not empty, only allow whitelisted IPs)
        if self.ip_access_control.whitelist and not self.ip_access_control.is_whitelisted(ip_address):
            self.log_security_event(
                "IP_BLOCKED",
                ip_address=ip_address,
                details={"reason": "IP is not whitelisted"}
            )
            return False
        
        # Check rate limit
        if not self.ip_access_control.check_rate_limit(ip_address, endpoint):
            self.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                ip_address=ip_address,
                details={"endpoint": endpoint}
            )
            return False
        
        return True
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        return {
            "security_events": self.event_logger.get_security_summary(),
            "ip_access_control": {
                "whitelist_size": len(self.ip_access_control.whitelist),
                "blacklist_size": len(self.ip_access_control.blacklist),
                "suspicious_ips": len(self.ip_access_control.suspicious_ips),
                "active_rate_limits": len(self.ip_access_control.rate_limits)
            },
            "session_manager": {
                "active_sessions": len(self.session_manager.get_active_sessions()),
                "total_sessions": len(self.session_manager.sessions)
            }
        }


# Global security monitor instance
security_monitor = SecurityMonitor()
