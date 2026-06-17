"""
Row-Level Security (RLS) Implementation
Database-level tenant isolation and security policies
"""
from sqlalchemy import text
from typing import List
import logging
from src.db.connection import db_manager

logger = logging.getLogger(__name__)


class RLSPolicyManager:
    """Manages Row-Level Security policies for tenant isolation"""
    
    def __init__(self):
        self.tables = [
            'tenants',
            'users',
            'inventory',
            'customers',
            'orders',
            'order_items',
            'credit_ledger',
            'audit_log',
            'webhook_events',
        ]
    
    async def create_rls_function(self) -> str:
        """Create function to set current tenant context"""
        sql = """
        CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id UUID)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
        return sql
    
    async def create_tenant_isolation_policy(self, table_name: str) -> str:
        """Create tenant isolation policy for table"""
        sql = f"""
        CREATE POLICY tenant_isolation ON {table_name}
        FOR ALL
        TO sutra_app
        USING (
            tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR current_setting('app.current_tenant_id', true) IS NULL
        )
        WITH CHECK (
            tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR current_setting('app.current_tenant_id', true) IS NULL
        );
        """
        return sql
    
    async def create_admin_policy(self, table_name: str) -> str:
        """Create admin policy for full access"""
        sql = f"""
        CREATE POLICY admin_full_access ON {table_name}
        FOR ALL
        TO sutra_admin
        USING (true)
        WITH CHECK (true);
        """
        return sql
    
    async def enable_rls(self, table_name: str) -> str:
        """Enable RLS on table"""
        sql = f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
        return sql
    
    async def disable_rls(self, table_name: str) -> str:
        """Disable RLS on table (for admin operations)"""
        sql = f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;"
        return sql
    
    async def get_rls_setup_commands(self) -> List[str]:
        """Get complete RLS setup commands"""
        commands = []
        
        # Create tenant context function
        commands.append(await self.create_rls_function())
        
        # Create policies for each table
        for table in self.tables:
            commands.append(await self.enable_rls(table))
            commands.append(await self.create_tenant_isolation_policy(table))
            commands.append(await self.create_admin_policy(table))
        
        return commands
    
    async def apply_rls_policies(self):
        """Apply RLS policies to all tables"""
        try:
            async with db_manager.get_session() as session:
                commands = await self.get_rls_setup_commands()
                
                for command in commands:
                    await session.execute(text(command))
                
                await session.commit()
                logger.info("RLS policies applied successfully to all tables")
                
        except Exception as e:
            logger.error(f"Failed to apply RLS policies: {e}", exc_info=True)
            raise
    
    async def verify_rls_policies(self) -> dict:
        """Verify RLS policies are in place"""
        verification_results = {
            "status": "success",
            "tables": {},
            "errors": []
        }
        
        try:
            async with db_manager.get_session() as session:
                for table in self.tables:
                    # Check if RLS is enabled
                    result = await session.execute(text(f"""
                        SELECT relrowsecurity 
                        FROM pg_class 
                        WHERE relname = '{table}'
                    """))
                    rls_enabled = result.scalar()
                    
                    # Check if policies exist
                    result = await session.execute(text(f"""
                        SELECT COUNT(*) 
                        FROM pg_policies 
                        WHERE tablename = '{table}'
                    """))
                    policy_count = result.scalar()
                    
                    verification_results["tables"][table] = {
                        "rls_enabled": rls_enabled,
                        "policy_count": policy_count,
                        "status": "ok" if rls_enabled and policy_count > 0 else "warning"
                    }
                    
                    if not rls_enabled:
                        verification_results["errors"].append(
                            f"RLS not enabled for table {table}"
                        )
                    if policy_count == 0:
                        verification_results["errors"].append(
                            f"No policies found for table {table}"
                        )
                
                if verification_results["errors"]:
                    verification_results["status"] = "warning"
                
        except Exception as e:
            verification_results["status"] = "error"
            verification_results["errors"].append(str(e))
            logger.error(f"RLS verification failed: {e}", exc_info=True)
        
        return verification_results


class DatabaseRoleManager:
    """Manages database roles and permissions"""
    
    async def create_roles(self) -> List[str]:
        """Create database roles with appropriate permissions"""
        commands = []
        
        # Create application role
        commands.append("""
        CREATE ROLE IF NOT EXISTS sutra_app WITH LOGIN PASSWORD 'change_me_in_production';
        """)
        
        # Create admin role
        commands.append("""
        CREATE ROLE IF NOT EXISTS sutra_admin WITH LOGIN PASSWORD 'change_me_in_production';
        """)
        
        # Create read-only role
        commands.append("""
        CREATE ROLE IF NOT EXISTS sutra_readonly WITH LOGIN PASSWORD 'change_me_in_production';
        """)
        
        # Grant admin role to application role
        commands.append("""
        GRANT sutra_admin TO sutra_app;
        """)
        
        return commands
    
    async def grant_permissions(self) -> List[str]:
        """Grant permissions to roles"""
        commands = []
        
        # Grant basic permissions to sutra_app
        commands.append("""
        GRANT USAGE ON SCHEMA public TO sutra_app;
        """)
        
        commands.append("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sutra_app;
        """)
        
        commands.append("""
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sutra_app;
        """)
        
        commands.append("""
        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO sutra_app;
        """)
        
        # Grant read-only permissions to sutra_readonly
        commands.append("""
        GRANT USAGE ON SCHEMA public TO sutra_readonly;
        """)
        
        commands.append("""
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO sutra_readonly;
        """)
        
        # Grant admin permissions to sutra_admin
        commands.append("""
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sutra_admin;
        """)
        
        commands.append("""
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sutra_admin;
        """)
        
        commands.append("""
        GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sutra_admin;
        """)
        
        # Set up default privileges for future objects
        commands.append("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sutra_app;
        """)
        
        commands.append("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO sutra_app;
        """)
        
        commands.append("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT EXECUTE ON FUNCTIONS TO sutra_app;
        """)
        
        return commands
    
    async def apply_roles_and_permissions(self):
        """Apply roles and permissions"""
        try:
            async with db_manager.get_session() as session:
                commands = []
                commands.extend(await self.create_roles())
                commands.extend(await self.grant_permissions())
                
                for command in commands:
                    await session.execute(text(command))
                
                await session.commit()
                logger.info("Database roles and permissions applied successfully")
                
        except Exception as e:
            logger.error(f"Failed to apply roles and permissions: {e}", exc_info=True)
            raise
    
    async def verify_roles(self) -> dict:
        """Verify roles are properly configured"""
        verification_results = {
            "status": "success",
            "roles": {},
            "errors": []
        }
        
        try:
            async with db_manager.get_session() as session:
                # Check if roles exist
                roles = ['sutra_app', 'sutra_admin', 'sutra_readonly']
                
                for role in roles:
                    result = await session.execute(text(f"""
                        SELECT rolname FROM pg_roles WHERE rolname = '{role}'
                    """))
                    role_exists = result.scalar() is not None
                    
                    verification_results["roles"][role] = {
                        "exists": role_exists,
                        "status": "ok" if role_exists else "error"
                    }
                    
                    if not role_exists:
                        verification_results["errors"].append(
                            f"Role {role} does not exist"
                        )
                
                if verification_results["errors"]:
                    verification_results["status"] = "error"
                
        except Exception as e:
            verification_results["status"] = "error"
            verification_results["errors"].append(str(e))
            logger.error(f"Role verification failed: {e}", exc_info=True)
        
        return verification_results


class TenantSchemaManager:
    """Manages tenant-specific schemas"""
    
    async def create_tenant_schema(self, tenant_id: str) -> str:
        """Create schema for specific tenant"""
        sql = f"""
        CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id};
        """
        return sql
    
    async def grant_tenant_schema_permissions(self, tenant_id: str) -> str:
        """Grant permissions on tenant schema"""
        sql = f"""
        GRANT ALL ON SCHEMA tenant_{tenant_id} TO sutra_app;
        GRANT ALL ON SCHEMA tenant_{tenant_id} TO sutra_admin;
        """
        return sql
    
    async def create_tenant_tables(self, tenant_id: str) -> List[str]:
        """Create tenant-specific tables (if needed)"""
        # For now, we're using row-level security instead of separate schemas
        # This function is reserved for future use if we need tenant-specific tables
        return []
    
    async def provision_tenant(self, tenant_id: str):
        """Provision schema for new tenant"""
        try:
            async with db_manager.get_session() as session:
                commands = []
                commands.append(await self.create_tenant_schema(tenant_id))
                commands.append(await self.grant_tenant_schema_permissions(tenant_id))
                commands.extend(await self.create_tenant_tables(tenant_id))
                
                for command in commands:
                    await session.execute(text(command))
                
                await session.commit()
                logger.info(f"Tenant {tenant_id} provisioned successfully")
                
        except Exception as e:
            logger.error(f"Failed to provision tenant {tenant_id}: {e}", exc_info=True)
            raise
    
    async def deprovision_tenant(self, tenant_id: str):
        """Remove tenant schema"""
        try:
            async with db_manager.get_session() as session:
                # Drop schema and all objects
                await session.execute(text(f"""
                    DROP SCHEMA IF EXISTS tenant_{tenant_id} CASCADE;
                """))
                
                await session.commit()
                logger.info(f"Tenant {tenant_id} deprovisioned successfully")
                
        except Exception as e:
            logger.error(f"Failed to deprovision tenant {tenant_id}: {e}", exc_info=True)
            raise


# Global instances
rls_manager = RLSPolicyManager()
role_manager = DatabaseRoleManager()
tenant_schema_manager = TenantSchemaManager()


async def setup_database_security():
    """Set up complete database security (RLS, roles, permissions)"""
    logger.info("Setting up database security...")
    
    # Apply roles and permissions
    await role_manager.apply_roles_and_permissions()
    
    # Apply RLS policies
    await rls_manager.apply_rls_policies()
    
    logger.info("Database security setup complete")


async def verify_database_security() -> dict:
    """Verify database security is properly configured"""
    logger.info("Verifying database security...")
    
    results = {
        "roles": await role_manager.verify_roles(),
        "rls": await rls_manager.verify_rls_policies(),
        "overall_status": "success"
    }
    
    if results["roles"]["status"] == "error" or results["rls"]["status"] == "error":
        results["overall_status"] = "error"
    elif results["roles"]["status"] == "warning" or results["rls"]["status"] == "warning":
        results["overall_status"] = "warning"
    
    logger.info(f"Database security verification complete: {results['overall_status']}")
    return results