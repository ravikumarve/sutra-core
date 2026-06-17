"""
Role-Based Access Control (RBAC)
Multi-tenant access control and permissions
"""
from enum import Enum
from typing import List, Set, Dict, Optional
from fastapi import HTTPException, status
from src.config.settings import settings


class Role(str, Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"              # Full system access
    SHOP_OWNER = "shop_owner"    # Full tenant access
    MANAGER = "manager"          # Most tenant operations
    STAFF = "staff"              # Limited operations
    VIEWER = "viewer"            # Read-only access


class Permission(str, Enum):
    """Granular permissions"""
    # Tenant management
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    TENANT_DELETE = "tenant:delete"
    
    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Inventory management
    INVENTORY_READ = "inventory:read"
    INVENTORY_WRITE = "inventory:write"
    INVENTORY_DELETE = "inventory:delete"
    
    # Order management
    ORDER_READ = "order:read"
    ORDER_WRITE = "order:write"
    ORDER_DELETE = "order:delete"
    ORDER_CANCEL = "order:cancel"
    
    # Customer management
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    CUSTOMER_DELETE = "customer:delete"
    
    # Credit management
    CREDIT_READ = "credit:read"
    CREDIT_WRITE = "credit:write"
    CREDIT_DELETE = "credit:delete"
    CREDIT_APPROVE = "credit:approve"
    
    # Financial operations
    FINANCIAL_READ = "financial:read"
    FINANCIAL_WRITE = "financial:write"
    
    # Reports and analytics
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    
    # System administration
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # All permissions
        Permission.TENANT_READ, Permission.TENANT_WRITE, Permission.TENANT_DELETE,
        Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
        Permission.INVENTORY_READ, Permission.INVENTORY_WRITE, Permission.INVENTORY_DELETE,
        Permission.ORDER_READ, Permission.ORDER_WRITE, Permission.ORDER_DELETE, Permission.ORDER_CANCEL,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_WRITE, Permission.CUSTOMER_DELETE,
        Permission.CREDIT_READ, Permission.CREDIT_WRITE, Permission.CREDIT_DELETE, Permission.CREDIT_APPROVE,
        Permission.FINANCIAL_READ, Permission.FINANCIAL_WRITE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
        Permission.SYSTEM_READ, Permission.SYSTEM_WRITE, Permission.SYSTEM_ADMIN,
    },
    Role.SHOP_OWNER: {
        # Full tenant access except system admin
        Permission.TENANT_READ,
        Permission.USER_READ, Permission.USER_WRITE,
        Permission.INVENTORY_READ, Permission.INVENTORY_WRITE, Permission.INVENTORY_DELETE,
        Permission.ORDER_READ, Permission.ORDER_WRITE, Permission.ORDER_DELETE, Permission.ORDER_CANCEL,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_WRITE, Permission.CUSTOMER_DELETE,
        Permission.CREDIT_READ, Permission.CREDIT_WRITE, Permission.CREDIT_DELETE, Permission.CREDIT_APPROVE,
        Permission.FINANCIAL_READ, Permission.FINANCIAL_WRITE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
    },
    Role.MANAGER: {
        # Most operations except delete and credit approval
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.INVENTORY_READ, Permission.INVENTORY_WRITE,
        Permission.ORDER_READ, Permission.ORDER_WRITE, Permission.ORDER_CANCEL,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_WRITE,
        Permission.CREDIT_READ, Permission.CREDIT_WRITE,
        Permission.FINANCIAL_READ,
        Permission.REPORT_READ,
    },
    Role.STAFF: {
        # Limited operations
        Permission.INVENTORY_READ,
        Permission.ORDER_READ, Permission.ORDER_WRITE,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_WRITE,
        Permission.CREDIT_READ,
    },
    Role.VIEWER: {
        # Read-only access
        Permission.INVENTORY_READ,
        Permission.ORDER_READ,
        Permission.CUSTOMER_READ,
        Permission.CREDIT_READ,
        Permission.FINANCIAL_READ,
        Permission.REPORT_READ,
    },
}


class RBACManager:
    """Manages role-based access control"""
    
    @staticmethod
    def get_permissions(role: Role) -> Set[Permission]:
        """Get all permissions for a role"""
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(role: Role, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in RBACManager.get_permissions(role)
    
    @staticmethod
    def has_any_permission(role: Role, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        role_permissions = RBACManager.get_permissions(role)
        return any(perm in role_permissions for perm in permissions)
    
    @staticmethod
    def has_all_permissions(role: Role, permissions: List[Permission]) -> bool:
        """Check if role has all of the specified permissions"""
        role_permissions = RBACManager.get_permissions(role)
        return all(perm in role_permissions for perm in permissions)
    
    @staticmethod
    def check_permission(role: Role, permission: Permission) -> None:
        """Raise exception if role doesn't have permission"""
        if not RBACManager.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' does not have permission '{permission}'"
            )
    
    @staticmethod
    def check_any_permission(role: Role, permissions: List[Permission]) -> None:
        """Raise exception if role doesn't have any of the permissions"""
        if not RBACManager.has_any_permission(role, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' does not have any of the required permissions: {permissions}"
            )
    
    @staticmethod
    def check_all_permissions(role: Role, permissions: List[Permission]) -> None:
        """Raise exception if role doesn't have all permissions"""
        if not RBACManager.has_all_permissions(role, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' does not have all required permissions: {permissions}"
            )


class TenantContext:
    """Manages tenant isolation and context"""
    
    def __init__(self):
        self._current_tenant_id: Optional[str] = None
        self._current_user_id: Optional[str] = None
        self._current_role: Optional[Role] = None
    
    def set_tenant_context(
        self,
        tenant_id: str,
        user_id: str,
        role: Role
    ) -> None:
        """Set current tenant context"""
        self._current_tenant_id = tenant_id
        self._current_user_id = user_id
        self._current_role = role
    
    def get_tenant_id(self) -> str:
        """Get current tenant ID"""
        if not self._current_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No tenant context set"
            )
        return self._current_tenant_id
    
    def get_user_id(self) -> str:
        """Get current user ID"""
        if not self._current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user context set"
            )
        return self._current_user_id
    
    def get_role(self) -> Role:
        """Get current user role"""
        if not self._current_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No role context set"
            )
        return self._current_role
    
    def clear_context(self) -> None:
        """Clear current context"""
        self._current_tenant_id = None
        self._current_user_id = None
        self._current_role = None
    
    def is_tenant_isolated(self) -> bool:
        """Check if tenant isolation is enabled"""
        return settings.tenant_isolation_enabled
    
    def verify_tenant_access(self, requested_tenant_id: str) -> None:
        """Verify user has access to requested tenant"""
        if not self.is_tenant_isolated():
            return
        
        current_tenant_id = self.get_tenant_id()
        if current_tenant_id != requested_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to tenant '{requested_tenant_id}'"
            )


class AccessControl:
    """High-level access control utilities"""
    
    def __init__(self, rbac: RBACManager, tenant_context: TenantContext):
        self.rbac = rbac
        self.tenant_context = tenant_context
    
    def can_read_inventory(self) -> bool:
        """Check if user can read inventory"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.INVENTORY_READ)
    
    def can_write_inventory(self) -> bool:
        """Check if user can write inventory"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.INVENTORY_WRITE)
    
    def can_delete_inventory(self) -> bool:
        """Check if user can delete inventory"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.INVENTORY_DELETE)
    
    def can_read_orders(self) -> bool:
        """Check if user can read orders"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.ORDER_READ)
    
    def can_write_orders(self) -> bool:
        """Check if user can write orders"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.ORDER_WRITE)
    
    def can_cancel_orders(self) -> bool:
        """Check if user can cancel orders"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.ORDER_CANCEL)
    
    def can_manage_credit(self) -> bool:
        """Check if user can manage credit"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.CREDIT_WRITE)
    
    def can_approve_credit(self) -> bool:
        """Check if user can approve credit"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.CREDIT_APPROVE)
    
    def can_view_financials(self) -> bool:
        """Check if user can view financial data"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.FINANCIAL_READ)
    
    def can_modify_financials(self) -> bool:
        """Check if user can modify financial data"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.FINANCIAL_WRITE)
    
    def can_export_reports(self) -> bool:
        """Check if user can export reports"""
        role = self.tenant_context.get_role()
        return self.rbac.has_permission(role, Permission.REPORT_EXPORT)


# Global instances
rbac_manager = RBACManager()
tenant_context = TenantContext()
access_control = AccessControl(rbac_manager, tenant_context)


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            role = tenant_context.get_role()
            rbac_manager.check_permission(role, permission)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            role = tenant_context.get_role()
            rbac_manager.check_any_permission(role, list(permissions))
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_tenant_access(tenant_id: str):
    """Decorator to require tenant access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tenant_context.verify_tenant_access(tenant_id)
            return await func(*args, **kwargs)
        return wrapper
    return decorator