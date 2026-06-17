"""
Health Check Endpoints
Comprehensive health monitoring and status endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime
from src.db.connection import check_database_health, get_db_manager
from src.db.monitoring import db_monitor
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns overall system health status
    """
    try:
        # Check database health
        db_health = await check_database_health()
        
        # Determine overall status
        overall_status = "healthy"
        if db_health["status"] == "degraded":
            overall_status = "degraded"
        elif db_health["status"] == "unhealthy":
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
            "components": {
                "database": db_health,
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@router.get("/database")
async def database_health() -> Dict[str, Any]:
    """
    Detailed database health check
    Returns database connection status and performance metrics
    """
    try:
        health = await check_database_health()
        
        # Get additional database metrics
        db_manager = get_db_manager()
        pool_status = db_manager.get_pool_status()
        
        return {
            "status": health["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": health["latency_ms"],
            "pool_status": pool_status,
            "error": health.get("error"),
        }
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed"
        )


@router.get("/database/detailed")
async def database_detailed_health() -> Dict[str, Any]:
    """
    Comprehensive database health report
    Returns detailed database metrics and analysis
    """
    try:
        report = await db_monitor.get_comprehensive_health_report()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "report": report,
        }
    
    except Exception as e:
        logger.error(f"Detailed database health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detailed database health check failed"
        )


@router.get("/database/connections")
async def database_connections() -> Dict[str, Any]:
    """
    Database connection statistics
    Returns current connection pool status
    """
    try:
        stats = await db_monitor.get_connection_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
        }
    
    except Exception as e:
        logger.error(f"Database connections check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connections check failed"
        )


@router.get("/database/tables")
async def database_tables() -> Dict[str, Any]:
    """
    Database table statistics
    Returns table sizes and row counts
    """
    try:
        tables = await db_monitor.get_table_sizes()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "tables": tables,
            "total_tables": len(tables),
        }
    
    except Exception as e:
        logger.error(f"Database tables check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database tables check failed"
        )


@router.get("/database/slow-queries")
async def database_slow_queries(limit: int = 10) -> Dict[str, Any]:
    """
    Slow queries analysis
    Returns list of slowest queries
    """
    try:
        queries = await db_monitor.get_slow_queries(limit=limit)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "slow_queries": queries,
            "total_slow_queries": len(queries),
        }
    
    except Exception as e:
        logger.error(f"Slow queries check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slow queries check failed"
        )


@router.get("/database/indexes")
async def database_indexes() -> Dict[str, Any]:
    """
    Database index usage statistics
    Returns index usage and performance
    """
    try:
        indexes = await db_monitor.get_index_usage()
        
        # Calculate statistics
        total_indexes = len(indexes)
        unused_indexes = len([i for i in indexes if i["usage_status"] == "unused"])
        low_usage_indexes = len([i for i in indexes if i["usage_status"] == "low_usage"])
        active_indexes = len([i for i in indexes if i["usage_status"] == "active"])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "indexes": indexes,
            "statistics": {
                "total": total_indexes,
                "unused": unused_indexes,
                "low_usage": low_usage_indexes,
                "active": active_indexes,
            }
        }
    
    except Exception as e:
        logger.error(f"Database indexes check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database indexes check failed"
        )


@router.get("/database/cache")
async def database_cache() -> Dict[str, Any]:
    """
    Database cache hit ratio
    Returns buffer cache performance
    """
    try:
        cache_stats = await db_monitor.get_cache_hit_ratio()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": cache_stats,
        }
    
    except Exception as e:
        logger.error(f"Database cache check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database cache check failed"
        )


@router.get("/database/locks")
async def database_locks() -> Dict[str, Any]:
    """
    Database lock status
    Returns current database locks
    """
    try:
        locks = await db_monitor.get_locks()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "locks": locks,
            "total_locks": len(locks),
        }
    
    except Exception as e:
        logger.error(f"Database locks check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database locks check failed"
        )


@router.get("/database/active-queries")
async def database_active_queries() -> Dict[str, Any]:
    """
    Active database queries
    Returns currently running queries
    """
    try:
        queries = await db_monitor.get_active_queries()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_queries": queries,
            "total_active_queries": len(queries),
        }
    
    except Exception as e:
        logger.error(f"Active queries check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Active queries check failed"
        )


@router.get("/database/vacuum")
async def database_vacuum_stats() -> Dict[str, Any]:
    """
    Database vacuum statistics
    Returns vacuum and analyze statistics
    """
    try:
        stats = await db_monitor.get_vacuum_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "vacuum_stats": stats,
            "total_tables": len(stats),
        }
    
    except Exception as e:
        logger.error(f"Vacuum stats check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vacuum stats check failed"
        )


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    Returns whether the application is ready to accept traffic
    """
    try:
        # Check database connectivity
        db_health = await check_database_health()
        
        if db_health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Readiness check failed"
        )


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint
    Returns whether the application is running
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    Application metrics endpoint
    Returns application-level metrics
    """
    try:
        db_manager = get_db_manager()
        pool_status = db_manager.get_pool_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
            },
            "database": {
                "pool_status": pool_status,
            },
        }
    
    except Exception as e:
        logger.error(f"Metrics check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics check failed"
        )