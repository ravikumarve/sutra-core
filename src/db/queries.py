"""
Database Query Optimization
Provides query caching, optimization, and performance monitoring
"""
import json
import logging
import time
from typing import Optional, Dict, Any, List, TypeVar, Generic
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryCache:
    """
    Simple in-memory query result cache
    For production, consider using Redis or Memcached
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, query: str, params: tuple) -> str:
        """Generate cache key from query and parameters"""
        return f"{hash(query)}:{hash(str(params))}"
    
    def get(self, query: str, params: tuple) -> Optional[Any]:
        """Get cached result"""
        key = self._generate_key(query, params)
        
        if key in self.cache:
            result, expiry = self.cache[key]
            
            # Check if cache entry is still valid
            if datetime.utcnow() < expiry:
                self.hits += 1
                logger.debug(f"Cache hit: {key}")
                return result
            else:
                # Remove expired entry
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, query: str, params: tuple, result: Any, ttl: Optional[int] = None) -> None:
        """Cache query result"""
        key = self._generate_key(query, params)
        expiry = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
        self.cache[key] = (result, expiry)
        logger.debug(f"Cache set: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Query cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "size": len(self.cache)
        }


# Global query cache instance
query_cache = QueryCache()


def cached_query(ttl: int = 300):
    """
    Decorator for caching query results
    
    Args:
        ttl: Time to live in seconds (default: 300 seconds = 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args))}:{hash(str(kwargs))}"
            
            # Try to get from cache
            cached_result = query_cache.get(cache_key, ())
            if cached_result is not None:
                return cached_result
            
            # Execute query
            result = await func(*args, **kwargs)
            
            # Cache result
            query_cache.set(cache_key, (), result, ttl)
            
            return result
        return wrapper
    return decorator


class QueryOptimizer:
    """
    Database query optimization utilities
    """
    
    @staticmethod
    def optimize_user_query(tenant_id: str, phone_number: str) -> Select:
        """
        Optimized user query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            phone_number: User phone number
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import User
        
        # Use composite index (tenant_id, phone_number)
        return select(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.phone_number == phone_number
            )
        )
    
    @staticmethod
    def optimize_tenant_query(tenant_id: str) -> Select:
        """
        Optimized tenant query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import Tenant
        
        # Use primary key index
        return select(Tenant).where(Tenant.id == tenant_id)
    
    @staticmethod
    def optimize_inventory_query(
        tenant_id: str,
        category: Optional[str] = None,
        low_stock: bool = False
    ) -> Select:
        """
        Optimized inventory query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            category: Optional category filter
            low_stock: Filter for low stock items
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import Inventory
        
        conditions = [Inventory.tenant_id == tenant_id]
        
        if category:
            conditions.append(Inventory.category == category)
        
        if low_stock:
            conditions.append(
                and_(
                    Inventory.quantity <= Inventory.min_stock_level,
                    Inventory.is_active == True
                )
            )
        
        # Use composite index (tenant_id, category) if category is specified
        return select(Inventory).where(and_(*conditions))
    
    @staticmethod
    def optimize_order_query(
        tenant_id: str,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Select:
        """
        Optimized order query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            customer_id: Optional customer filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import Order
        
        conditions = [Order.tenant_id == tenant_id]
        
        if customer_id:
            conditions.append(Order.customer_id == customer_id)
        
        if status:
            conditions.append(Order.status == status)
        
        if date_from:
            conditions.append(Order.order_date >= date_from)
        
        if date_to:
            conditions.append(Order.order_date <= date_to)
        
        # Use composite index (tenant_id, order_date) for date range queries
        return select(Order).where(and_(*conditions))
    
    @staticmethod
    def optimize_customer_query(
        tenant_id: str,
        phone_number: Optional[str] = None,
        active_only: bool = True
    ) -> Select:
        """
        Optimized customer query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            phone_number: Optional phone number filter
            active_only: Filter for active customers only
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import Customer
        
        conditions = [Customer.tenant_id == tenant_id]
        
        if phone_number:
            # Use composite index (tenant_id, phone_number)
            conditions.append(Customer.phone_number == phone_number)
        
        if active_only:
            conditions.append(Customer.is_active == True)
        
        return select(Customer).where(and_(*conditions))
    
    @staticmethod
    def optimize_credit_ledger_query(
        tenant_id: str,
        customer_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Select:
        """
        Optimized credit ledger query with proper indexing
        
        Args:
            tenant_id: Tenant ID
            customer_id: Optional customer filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Optimized SQLAlchemy query
        """
        from src.db.models import CreditLedger
        
        conditions = [CreditLedger.tenant_id == tenant_id]
        
        if customer_id:
            conditions.append(CreditLedger.customer_id == customer_id)
        
        if date_from:
            conditions.append(CreditLedger.transaction_date >= date_from)
        
        if date_to:
            conditions.append(CreditLedger.transaction_date <= date_to)
        
        # Use composite index (tenant_id, customer_id, transaction_date)
        return select(CreditLedger).where(and_(*conditions))


class QueryPerformanceMonitor:
    """
    Monitor and log query performance
    """
    
    def __init__(self):
        self.slow_queries: List[Dict[str, Any]] = []
        self.slow_query_threshold_ms = 100  # 100ms threshold
    
    def log_query(
        self,
        query: str,
        duration_ms: float,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log query performance
        
        Args:
            query: SQL query
            duration_ms: Query execution time in milliseconds
            params: Query parameters
        """
        if duration_ms > self.slow_query_threshold_ms:
            self.slow_queries.append({
                "query": query[:500],  # Truncate long queries
                "duration_ms": duration_ms,
                "params": params,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms - {query[:200]}... "
                f"Params: {params}"
            )
        else:
            logger.debug(f"Query executed: {duration_ms:.2f}ms - {query[:100]}...")
    
    def get_slow_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get slow queries
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of slow queries
        """
        return self.slow_queries[-limit:]
    
    def clear_slow_queries(self) -> None:
        """Clear slow query log"""
        self.slow_queries.clear()
        logger.info("Slow query log cleared")


# Global query performance monitor instance
query_monitor = QueryPerformanceMonitor()


async def execute_optimized_query(
    session: AsyncSession,
    query: Select,
    use_cache: bool = False,
    cache_ttl: int = 300
) -> Any:
    """
    Execute optimized query with optional caching
    
    Args:
        session: Database session
        query: SQLAlchemy query
        use_cache: Whether to use query cache
        cache_ttl: Cache time to live in seconds
        
    Returns:
        Query result
    """
    start_time = time.time()
    
    try:
        # Convert query to string for caching
        query_str = str(query)
        
        # Check cache if enabled
        if use_cache:
            cached_result = query_cache.get(query_str, ())
            if cached_result is not None:
                return cached_result
        
        # Execute query
        result = await session.execute(query)
        scalar_result = result.scalar_one_or_none()
        
        # Cache result if enabled
        if use_cache and scalar_result is not None:
            query_cache.set(query_str, (), scalar_result, cache_ttl)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        query_monitor.log_query(query_str, duration_ms)
        
        return scalar_result
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


async def execute_optimized_query_list(
    session: AsyncSession,
    query: Select,
    use_cache: bool = False,
    cache_ttl: int = 300
) -> List[Any]:
    """
    Execute optimized query that returns a list
    
    Args:
        session: Database session
        query: SQLAlchemy query
        use_cache: Whether to use query cache
        cache_ttl: Cache time to live in seconds
        
    Returns:
        Query result list
    """
    start_time = time.time()
    
    try:
        # Convert query to string for caching
        query_str = str(query)
        
        # Check cache if enabled
        if use_cache:
            cached_result = query_cache.get(query_str, ())
            if cached_result is not None:
                return cached_result
        
        # Execute query
        result = await session.execute(query)
        scalar_result = result.scalars().all()
        
        # Cache result if enabled
        if use_cache and scalar_result:
            query_cache.set(query_str, (), scalar_result, cache_ttl)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        query_monitor.log_query(query_str, duration_ms)
        
        return scalar_result
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


def get_query_performance_stats() -> Dict[str, Any]:
    """
    Get query performance statistics
    
    Returns:
        Dictionary with performance statistics
    """
    return {
        "cache_stats": query_cache.get_stats(),
        "slow_queries": len(query_monitor.slow_queries),
        "slow_query_threshold_ms": query_monitor.slow_query_threshold_ms
    }
