"""
Database Connection Management
Async PostgreSQL connection with pooling and monitoring
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event
from contextlib import asynccontextmanager
import logging
import time
from typing import Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._connection_pool_monitor = None
        
    def create_engine(self, test_mode: bool = False):
        """Create async database engine with connection pooling"""
        pool_settings = {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_recycle": settings.database_pool_recycle,
            "pool_pre_ping": True,  # Verify connections before using
            "echo": settings.debug,  # Log SQL queries in debug mode
        }
        
        # Use NullPool for testing to avoid connection issues
        if test_mode:
            pool_settings = {"poolclass": NullPool}
        
        self.engine = create_async_engine(
            settings.database_url_async,
            **pool_settings
        )
        
        # Set up connection pool monitoring
        self._setup_pool_monitoring()
        
        # Create session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info(
            f"Database engine created: pool_size={pool_settings.get('pool_size')}, "
            f"max_overflow={pool_settings.get('max_overflow')}"
        )
        
        return self.engine
    
    def _setup_pool_monitoring(self):
        """Set up connection pool monitoring"""
        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new connections"""
            logger.debug(f"New database connection established: {id(dbapi_conn)}")
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkout"""
            logger.debug(f"Connection checked out: {id(dbapi_conn)}")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection checkin"""
            logger.debug(f"Connection checked in: {id(dbapi_conn)}")
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        if self.async_session_maker is None:
            raise RuntimeError("Database engine not initialized. Call create_engine() first.")
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}", exc_info=True)
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")
    
    def get_pool_status(self) -> dict:
        """Get connection pool status for monitoring"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.sync_engine.pool
        return {
            "status": "active",
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool._max_overflow,
            "timeout": pool._timeout,
        }


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def get_db_session():
    """Dependency injection for FastAPI routes and standalone async with usage"""
    async with db_manager.get_session() as session:
        yield session


async def init_database(test_mode: bool = False):
    """Initialize database engine"""
    db_manager.create_engine(test_mode=test_mode)
    logger.info("Database initialized successfully")


async def close_database():
    """Close all database connections"""
    await db_manager.close()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager


# Database health check
async def check_database_health() -> dict:
    """Check database connectivity and performance"""
    health_status = {
        "status": "healthy",
        "latency_ms": None,
        "pool_status": None,
        "error": None,
    }
    
    try:
        start_time = time.time()
        
        # Test connection
        async with db_manager.get_session() as session:
            await session.execute("SELECT 1")
        
        latency_ms = (time.time() - start_time) * 1000
        health_status["latency_ms"] = round(latency_ms, 2)
        
        # Get pool status
        health_status["pool_status"] = db_manager.get_pool_status()
        
        # Check if latency is acceptable
        if latency_ms > 100:  # 100ms threshold
            health_status["status"] = "degraded"
            logger.warning(f"Database latency high: {latency_ms:.2f}ms")
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        logger.error(f"Database health check failed: {e}", exc_info=True)
    
    return health_status


# Slow query logging
class SlowQueryLogger:
    """Logs slow queries for performance monitoring"""
    
    SLOW_QUERY_THRESHOLD_MS = 100  # 100ms threshold
    
    @staticmethod
    async def log_query(query: str, params: dict, duration_ms: float):
        """Log query if it exceeds threshold"""
        if duration_ms > SlowQueryLogger.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms - {query[:200]}... "
                f"Params: {params}"
            )


# Transaction management
@asynccontextmanager
async def transaction(session: AsyncSession):
    """Context manager for transactions with automatic rollback on error"""
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction failed, rolled back: {e}", exc_info=True)
        raise


# Tenant-aware session helper
async def get_tenant_session(tenant_id: str):
    """Get database session scoped to specific tenant"""
    async with db_manager.get_session() as session:
        # Set tenant context for the session
        # This will be used by row-level security
        await session.execute(f"SET app.current_tenant_id = '{tenant_id}'")
        yield session