"""
Multi-Tenancy Middleware
Tenant isolation and context management
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
from functools import wraps
import logging
from src.security.rbac import tenant_context, Role
from src.security.auth import auth_manager

logger = logging.getLogger(__name__)

security = HTTPBearer()


class TenantMiddleware:
    """Middleware for tenant isolation and context management"""
    
    def __init__(self):
        self.tenant_header = "X-Tenant-ID"
        self.user_header = "X-User-ID"
        self.role_header = "X-User-Role"
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ):
        """Process request and set tenant context"""
        # Extract tenant ID from header or JWT token
        tenant_id = self._extract_tenant_id(request)
        user_id = self._extract_user_id(request)
        role = self._extract_role(request)
        
        # Set tenant context
        if tenant_id and user_id and role:
            tenant_context.set_tenant_context(
                tenant_id=tenant_id,
                user_id=user_id,
                role=role
            )
            logger.debug(
                f"Tenant context set: tenant_id={tenant_id}, "
                f"user_id={user_id}, role={role}"
            )
        
        # Process request
        response = await call_next(request)
        
        # Clear context after request
        tenant_context.clear_context()
        
        return response
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        # Try header first
        tenant_id = request.headers.get(self.tenant_header)
        if tenant_id:
            return tenant_id
        
        # Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = auth_manager.decode_token(token)
                return payload.get("tenant_id")
            except Exception as e:
                logger.warning(f"Failed to extract tenant_id from token: {e}")
        
        return None
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try header first
        user_id = request.headers.get(self.user_header)
        if user_id:
            return user_id
        
        # Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = auth_manager.decode_token(token)
                return payload.get("user_id")
            except Exception as e:
                logger.warning(f"Failed to extract user_id from token: {e}")
        
        return None
    
    def _extract_role(self, request: Request) -> Optional[Role]:
        """Extract user role from request"""
        # Try header first
        role_str = request.headers.get(self.role_header)
        if role_str:
            try:
                return Role(role_str)
            except ValueError:
                logger.warning(f"Invalid role in header: {role_str}")
        
        # Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = auth_manager.decode_token(token)
                role_str = payload.get("role")
                if role_str:
                    return Role(role_str)
            except Exception as e:
                logger.warning(f"Failed to extract role from token: {e}")
        
        return None


class TenantIsolationMixin:
    """Mixin for tenant isolation in database queries"""
    
    @staticmethod
    def add_tenant_filter(query, tenant_id: str):
        """Add tenant filter to query"""
        # This will be implemented based on ORM used
        # For SQLAlchemy async:
        # return query.filter(Model.tenant_id == tenant_id)
        return query
    
    @staticmethod
    def verify_tenant_access(entity_tenant_id: str, user_tenant_id: str):
        """Verify entity belongs to user's tenant"""
        if entity_tenant_id != user_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Entity belongs to different tenant"
            )


def require_tenant_context():
    """Decorator to require tenant context"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                tenant_id = tenant_context.get_tenant_id()
                user_id = tenant_context.get_user_id()
                role = tenant_context.get_role()
                
                logger.debug(
                    f"Tenant context verified: tenant_id={tenant_id}, "
                    f"user_id={user_id}, role={role}"
                )
                
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Tenant context verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Valid tenant context required"
                )
        return wrapper
    return decorator


def require_tenant_admin():
    """Decorator to require tenant admin access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                role = tenant_context.get_role()
                
                if role not in [Role.ADMIN, Role.SHOP_OWNER]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin access required"
                    )
                
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Tenant admin verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
        return wrapper
    return decorator


class TenantQueryBuilder:
    """Helper for building tenant-aware queries"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    def build_filter(self, model_class):
        """Build tenant filter for model"""
        # This will be implemented based on ORM used
        # For SQLAlchemy async:
        # return model_class.tenant_id == self.tenant_id
        pass
    
    def apply_to_query(self, query, model_class):
        """Apply tenant filter to query"""
        # This will be implemented based on ORM used
        # return query.filter(self.build_filter(model_class))
        return query


# Global tenant middleware instance
tenant_middleware = TenantMiddleware()


# Row-Level Security (RLS) helpers for PostgreSQL
class RLSPolicy:
    """Row-Level Security policy definitions"""
    
    @staticmethod
    def create_tenant_policy(table_name: str) -> str:
        """Create tenant isolation policy for table"""
        return f"""
        CREATE POLICY tenant_isolation ON {table_name}
        FOR ALL
        TO sutra_app
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """
    
    @staticmethod
    def enable_rls(table_name: str) -> str:
        """Enable RLS on table"""
        return f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
    
    @staticmethod
    def create_tenant_function() -> str:
        """Create function to set current tenant"""
        return """
        CREATE OR REPLACE FUNCTION set_tenant_id(tenant_id uuid)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
    
    @staticmethod
    def get_rls_setup_commands(tables: list) -> list:
        """Get complete RLS setup commands"""
        commands = [
            RLSPolicy.create_tenant_function(),
        ]
        
        for table in tables:
            commands.extend([
                RLSPolicy.enable_rls(table),
                RLSPolicy.create_tenant_policy(table),
            ])
        
        return commands


# Tenant-specific Redis key management
class TenantRedisKeys:
    """Helper for tenant-specific Redis keys"""
    
    @staticmethod
    def get_tenant_key(tenant_id: str, key: str) -> str:
        """Get tenant-specific Redis key"""
        return f"sutra:{tenant_id}:{key}"
    
    @staticmethod
    def get_stream_key(tenant_id: str, stream_name: str) -> str:
        """Get tenant-specific Redis stream key"""
        return f"sutra:{tenant_id}:streams:{stream_name}"
    
    @staticmethod
    def get_cache_key(tenant_id: str, cache_type: str, identifier: str) -> str:
        """Get tenant-specific cache key"""
        return f"sutra:{tenant_id}:cache:{cache_type}:{identifier}"
    
    @staticmethod
    def get_lock_key(tenant_id: str, resource: str) -> str:
        """Get tenant-specific lock key"""
        return f"sutra:{tenant_id}:locks:{resource}"
    
    @staticmethod
    def get_rate_limit_key(tenant_id: str, user_id: str) -> str:
        """Get tenant-specific rate limit key"""
        return f"sutra:{tenant_id}:ratelimit:{user_id}"


# Tenant configuration management
class TenantConfig:
    """Manage tenant-specific configuration"""
    
    @staticmethod
    def get_default_config(industry: str) -> dict:
        """Get default configuration for industry"""
        configs = {
            "textiles": {
                "units": ["meter", "than", "peti", "lot"],
                "gst_categories": ["50", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"],
                "default_gst_rate": 12.0,
            },
            "hardware": {
                "units": ["piece", "kg", "nag", "patti", "pipe", "fitting"],
                "gst_categories": ["73", "74", "75", "76", "82", "83", "84"],
                "default_gst_rate": 18.0,
            },
            "kirana": {
                "units": ["kg", "piece", "bora", "peethi", "dozen"],
                "gst_categories": ["07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"],
                "default_gst_rate": 5.0,
            },
            "pharma": {
                "units": ["piece", "strip", "box", "vial", "bottle"],
                "gst_categories": ["30"],
                "default_gst_rate": 12.0,
            },
        }
        
        return configs.get(industry, {})
    
    @staticmethod
    def validate_config(config: dict) -> bool:
        """Validate tenant configuration"""
        required_fields = ["units", "gst_categories", "default_gst_rate"]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required config field: {field}")
                return False
        
        return True