"""
Database Performance Monitoring Queries
Comprehensive monitoring and performance analysis queries
"""
from typing import Dict, List, Any
from sqlalchemy import text
from src.db.connection import db_manager
import logging

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Database performance monitoring and health checks"""
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) filter (where state = 'active') as active_connections,
                    count(*) filter (where state = 'idle') as idle_connections,
                    count(*) filter (where state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            
            row = result.fetchone()
            return {
                "total_connections": row[0],
                "active_connections": row[1],
                "idle_connections": row[2],
                "idle_in_transaction": row[3],
                "status": "healthy" if row[3] == 0 else "warning"
            }
    
    async def get_table_sizes(self) -> List[Dict[str, Any]]:
        """Get table sizes and row counts"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                    n_live_tup as row_count,
                    n_dead_tup as dead_row_count,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """))
            
            tables = []
            for row in result:
                tables.append({
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "size_bytes": row[3],
                    "row_count": row[4],
                    "dead_row_count": row[5],
                    "last_vacuum": str(row[6]) if row[6] else None,
                    "last_autovacuum": str(row[7]) if row[7] else None,
                    "last_analyze": str(row[8]) if row[8] else None,
                    "last_autoanalyze": str(row[9]) if row[9] else None,
                })
            
            return tables
    
    async def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow queries from pg_stat_statements"""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(text(f"""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        max_time,
                        rows
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT {limit}
                """))
                
                queries = []
                for row in result:
                    queries.append({
                        "query": row[0][:200],  # Truncate long queries
                        "calls": row[1],
                        "total_time": round(row[2], 2),
                        "mean_time": round(row[3], 2),
                        "max_time": round(row[4], 2),
                        "rows": row[5],
                    })
                
                return queries
        except Exception as e:
            logger.warning(f"Could not get slow queries (pg_stat_statements may not be enabled): {e}")
            return []
    
    async def get_index_usage(self) -> List[Dict[str, Any]]:
        """Get index usage statistics"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan,
                    CASE 
                        WHEN idx_scan = 0 THEN 'unused'
                        WHEN idx_scan < 10 THEN 'low_usage'
                        ELSE 'active'
                    END as usage_status
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan ASC
            """))
            
            indexes = []
            for row in result:
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "tuples_read": row[3],
                    "tuples_fetched": row[4],
                    "scans": row[5],
                    "usage_status": row[6],
                })
            
            return indexes
    
    async def get_cache_hit_ratio(self) -> Dict[str, Any]:
        """Get buffer cache hit ratio"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) as ratio
                FROM pg_statio_user_tables
            """))
            
            row = result.fetchone()
            ratio = round(row[2] * 100, 2) if row[2] else 0
            
            return {
                "heap_read": row[0],
                "heap_hit": row[1],
                "hit_ratio": ratio,
                "status": "good" if ratio > 95 else "needs_optimization"
            }
    
    async def get_locks(self) -> List[Dict[str, Any]]:
        """Get current database locks"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    l.locktype,
                    l.database,
                    l.relation,
                    l.page,
                    l.tuple,
                    l.virtualxid,
                    l.transactionid,
                    l.classid,
                    l.objid,
                    l.objsubid,
                    l.mode,
                    l.granted,
                    a.query,
                    a.query_start,
                    a.usename,
                    a.application_name
                FROM pg_locks l
                LEFT JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE NOT l.granted
                ORDER BY a.query_start
            """))
            
            locks = []
            for row in result:
                locks.append({
                    "lock_type": row[0],
                    "database": row[1],
                    "relation": row[2],
                    "mode": row[10],
                    "granted": row[11],
                    "query": row[12][:100] if row[12] else None,
                    "query_start": str(row[13]) if row[13] else None,
                    "user": row[14],
                    "application": row[15],
                })
            
            return locks
    
    async def get_replication_lag(self) -> Dict[str, Any]:
        """Get replication lag (if replication is configured)"""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        pg_current_wal_lsn() as current_lsn,
                        pg_last_wal_replay_lsn() as replay_lsn,
                        pg_wal_lsn_diff(pg_current_wal_lsn(), pg_last_wal_replay_lsn()) as lag_bytes
                """))
                
                row = result.fetchone()
                lag_mb = round(row[2] / 1024 / 1024, 2) if row[2] else 0
                
                return {
                    "current_lsn": str(row[0]),
                    "replay_lsn": str(row[1]),
                    "lag_bytes": row[2],
                    "lag_mb": lag_mb,
                    "status": "healthy" if lag_mb < 100 else "warning"
                }
        except Exception as e:
            logger.warning(f"Could not get replication lag (replication may not be configured): {e}")
            return {
                "status": "not_configured",
                "message": "Replication not configured"
            }
    
    async def get_database_size(self) -> Dict[str, Any]:
        """Get database size information"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as total_size,
                    pg_database_size(current_database()) as size_bytes
            """))
            
            row = result.fetchone()
            return {
                "total_size": row[0],
                "size_bytes": row[1],
            }
    
    async def get_active_queries(self) -> List[Dict[str, Any]]:
        """Get currently running queries"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state,
                    usename,
                    application_name,
                    client_addr
                FROM pg_stat_activity
                WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                AND state != 'idle'
                AND pid != pg_backend_pid()
                ORDER BY duration DESC
            """))
            
            queries = []
            for row in result:
                queries.append({
                    "pid": row[0],
                    "duration": str(row[1]),
                    "query": row[2][:200] if row[2] else None,
                    "state": row[3],
                    "user": row[4],
                    "application": row[5],
                    "client_address": str(row[6]) if row[6] else None,
                })
            
            return queries
    
    async def get_vacuum_stats(self) -> List[Dict[str, Any]]:
        """Get vacuum and analyze statistics"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze,
                    vacuum_count,
                    autovacuum_count,
                    analyze_count,
                    autoanalyze_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_dead_tup DESC
            """))
            
            stats = []
            for row in result:
                stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "sequential_scans": row[2],
                    "sequential_reads": row[3],
                    "index_scans": row[4],
                    "index_fetches": row[5],
                    "live_tuples": row[6],
                    "dead_tuples": row[7],
                    "last_vacuum": str(row[8]) if row[8] else None,
                    "last_autovacuum": str(row[9]) if row[9] else None,
                    "last_analyze": str(row[10]) if row[10] else None,
                    "last_autoanalyze": str(row[11]) if row[11] else None,
                    "vacuum_count": row[12],
                    "autovacuum_count": row[13],
                    "analyze_count": row[14],
                    "autoanalyze_count": row[15],
                })
            
            return stats
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get comprehensive database health report"""
        logger.info("Generating comprehensive database health report...")
        
        report = {
            "timestamp": None,
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "metrics": {}
        }
        
        try:
            # Get all metrics
            report["metrics"]["connections"] = await self.get_connection_stats()
            report["metrics"]["database_size"] = await self.get_database_size()
            report["metrics"]["cache_hit_ratio"] = await self.get_cache_hit_ratio()
            report["metrics"]["tables"] = await self.get_table_sizes()
            report["metrics"]["indexes"] = await self.get_index_usage()
            report["metrics"]["slow_queries"] = await self.get_slow_queries()
            report["metrics"]["active_queries"] = await self.get_active_queries()
            report["metrics"]["locks"] = await self.get_locks()
            report["metrics"]["vacuum_stats"] = await self.get_vacuum_stats()
            report["metrics"]["replication"] = await self.get_replication_lag()
            
            # Analyze metrics for issues
            if report["metrics"]["connections"]["idle_in_transaction"] > 0:
                report["warnings"].append("Idle transactions detected")
                report["status"] = "warning"
            
            if report["metrics"]["cache_hit_ratio"]["hit_ratio"] < 95:
                report["warnings"].append("Cache hit ratio below 95%")
                report["status"] = "warning"
            
            if len(report["metrics"]["locks"]) > 0:
                report["warnings"].append(f"{len(report["metrics"]["locks"])} blocked locks detected")
                report["status"] = "warning"
            
            if len(report["metrics"]["active_queries"]) > 5:
                report["warnings"].append(f"{len(report["metrics"]["active_queries"])} long-running queries")
                report["status"] = "warning"
            
            # Check for unused indexes
            unused_indexes = [i for i in report["metrics"]["indexes"] if i["usage_status"] == "unused"]
            if len(unused_indexes) > 0:
                report["warnings"].append(f"{len(unused_indexes)} unused indexes detected")
            
            # Check for tables needing vacuum
            tables_needing_vacuum = [
                t for t in report["metrics"]["vacuum_stats"]
                if t["dead_tuples"] > t["live_tuples"] * 0.1
            ]
            if len(tables_needing_vacuum) > 0:
                report["warnings"].append(f"{len(tables_needing_vacuum)} tables may need vacuum")
            
            logger.info(f"Database health report generated: {report["status"]}")
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}", exc_info=True)
            report["status"] = "error"
            report["errors"].append(str(e))
        
        return report


# Global instance
db_monitor = DatabaseMonitor()