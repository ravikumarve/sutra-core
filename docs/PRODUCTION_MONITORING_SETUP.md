# SUTRA Core - Production Monitoring Setup

**Version:** 1.0.0  
**Last Updated:** 2026-04-27  
**Purpose:** Comprehensive monitoring setup for production deployment

---

## Table of Contents

1. [Monitoring Architecture](#monitoring-architecture)
2. [Application Monitoring](#application-monitoring)
3. [Database Monitoring](#database-monitoring)
4. [Redis Monitoring](#redis-monitoring)
5. [System Monitoring](#system-monitoring)
6. [Security Monitoring](#security-monitoring)
7. [Alerting Configuration](#alerting-configuration)
8. [Dashboard Setup](#dashboard-setup)

---

## Monitoring Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     SUTRA Core System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │  PostgreSQL  │  │    Redis     │      │
│  │   Application│  │   Database   │  │    Cache     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│                    ┌──────▼──────┐                            │
│                    │  Prometheus  │                            │
│                    │   Metrics    │                            │
│                    └──────┬──────┘                            │
│                           │                                   │
│                    ┌──────▼──────┐                            │
│                    │   Grafana   │                            │
│                    │  Dashboards  │                            │
│                    └──────┬──────┘                            │
│                           │                                   │
│                    ┌──────▼──────┐                            │
│                    │  Alertmanager│                           │
│                    │   Alerts     │                            │
│                    └─────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Application Metrics** → Prometheus (scraping)
2. **Database Metrics** → PostgreSQL Exporter → Prometheus
3. **Redis Metrics** → Redis Exporter → Prometheus
4. **System Metrics** → Node Exporter → Prometheus
5. **Prometheus** → Grafana (visualization)
6. **Prometheus** → Alertmanager (alerting)

---

## Application Monitoring

### 1. Application Metrics

#### FastAPI Metrics
```python
# src/api/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Request counter
request_counter = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Active connections gauge
active_connections = Gauge(
    'active_connections',
    'Active database connections'
)

# Agent message counter
agent_message_counter = Counter(
    'agent_messages_total',
    'Total agent messages',
    ['agent_type', 'message_type', 'status']
)

# Agent processing duration
agent_processing_duration = Histogram(
    'agent_processing_duration_seconds',
    'Agent processing duration',
    ['agent_type']
)
```

#### Middleware Implementation
```python
# src/main.py
from src.api.middleware.metrics import (
    request_counter,
    request_duration,
    active_connections
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for each request"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    request_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### 2. Business Metrics

#### Custom Business Metrics
```python
# src/monitoring/business_metrics.py
from prometheus_client import Counter, Gauge, Histogram

# Order metrics
order_counter = Counter(
    'orders_total',
    'Total orders',
    ['tenant_id', 'status', 'payment_method']
)

order_amount = Histogram(
    'order_amount',
    'Order amount distribution',
    ['tenant_id']
)

# Customer metrics
customer_counter = Counter(
    'customers_total',
    'Total customers',
    ['tenant_id']
)

# Credit metrics
credit_ledger_amount = Gauge(
    'credit_ledger_amount',
    'Total credit ledger amount',
    ['tenant_id']
)

# Inventory metrics
inventory_level = Gauge(
    'inventory_level',
    'Current inventory level',
    ['tenant_id', 'product_id']
)

# WhatsApp metrics
whatsapp_message_counter = Counter(
    'whatsapp_messages_total',
    'Total WhatsApp messages',
    ['tenant_id', 'direction', 'status']
)
```

### 3. Health Checks

#### Comprehensive Health Checks
```python
# src/api/routes/health.py
from fastapi import APIRouter, HTTPException
from prometheus_client import Gauge
import time

router = APIRouter()

# Health status gauge
health_status = Gauge(
    'health_status',
    'Health status (1=healthy, 0=unhealthy)',
    ['component']
)

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check"""
    health_status.labels(component="application").set(1)
    
    checks = {
        "application": await check_application_health(),
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "agents": await check_agents_health()
    }
    
    overall_status = all(check["healthy"] for check in checks.values())
    
    return {
        "status": "healthy" if overall_status else "unhealthy",
        "checks": checks,
        "timestamp": time.time()
    }

async def check_application_health():
    """Check application health"""
    try:
        # Check if application is responsive
        return {"healthy": True, "message": "Application is healthy"}
    except Exception as e:
        health_status.labels(component="application").set(0)
        return {"healthy": False, "message": str(e)}

async def check_database_health():
    """Check database health"""
    try:
        from src.db.connection import check_database_health
        result = await check_database_health()
        health_status.labels(component="database").set(1 if result["status"] == "healthy" else 0)
        return result
    except Exception as e:
        health_status.labels(component="database").set(0)
        return {"healthy": False, "message": str(e)}

async def check_redis_health():
    """Check Redis health"""
    try:
        import redis.asyncio as redis
        redis_client = await redis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.close()
        health_status.labels(component="redis").set(1)
        return {"healthy": True, "message": "Redis is healthy"}
    except Exception as e:
        health_status.labels(component="redis").set(0)
        return {"healthy": False, "message": str(e)}

async def check_agents_health():
    """Check agents health"""
    try:
        from src.agents.coordinator import agent_coordinator
        status = agent_coordinator.get_status()
        health_status.labels(component="agents").set(1 if status["is_running"] else 0)
        return {
            "healthy": status["is_running"],
            "message": "Agents are healthy" if status["is_running"] else "Agents are not running"
        }
    except Exception as e:
        health_status.labels(component="agents").set(0)
        return {"healthy": False, "message": str(e)}
```

---

## Database Monitoring

### 1. PostgreSQL Metrics

#### PostgreSQL Exporter Setup
```yaml
# docker-compose.yml
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      - DATA_SOURCE_NAME=postgresql://sutra_user:password@postgres:5432/sutra_db?sslmode=disable
    ports:
      - "9187:9187"
    depends_on:
      - postgres
```

#### Key Database Metrics
- **Connection Metrics:** Active connections, idle connections
- **Query Performance:** Query duration, slow queries
- **Table Statistics:** Row counts, table sizes
- **Index Usage:** Index hit ratio, unused indexes
- **Lock Metrics:** Lock waits, deadlocks
- **Replication Metrics:** Replication lag (if applicable)

### 2. Database Performance Monitoring

#### Slow Query Logging
```python
# src/db/monitoring.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query start time"""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query duration"""
    total = time.time() - context._query_start_time
    
    # Log slow queries (>100ms)
    if total > 0.1:
        logger.warning(
            f"Slow query detected: {total:.3f}s - {statement[:200]}... "
            f"Params: {parameters}"
        )
```

---

## Redis Monitoring

### 1. Redis Metrics

#### Redis Exporter Setup
```yaml
# docker-compose.yml
services:
  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      - REDIS_ADDR=redis://redis:6379
    ports:
      - "9121:9121"
    depends_on:
      - redis
```

#### Key Redis Metrics
- **Connection Metrics:** Connected clients, rejected connections
- **Memory Metrics:** Used memory, memory fragmentation
- **Performance Metrics:** Commands per second, hit ratio
- **Key Metrics:** Total keys, expired keys
- **Persistence Metrics:** RDB/AOF status, last save time

---

## System Monitoring

### 1. System Metrics

#### Node Exporter Setup
```yaml
# docker-compose.yml
services:
  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
```

#### Key System Metrics
- **CPU Metrics:** CPU usage, load average, CPU time
- **Memory Metrics:** Memory usage, swap usage, cache
- **Disk Metrics:** Disk usage, disk I/O, disk latency
- **Network Metrics:** Network traffic, network errors
- **File System Metrics:** File system usage, inode usage

---

## Security Monitoring

### 1. Security Metrics

#### Security Event Metrics
```python
# src/monitoring/security_metrics.py
from prometheus_client import Counter, Gauge

# Authentication metrics
auth_attempts = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success, failure
)

failed_logins = Counter(
    'failed_logins_total',
    'Total failed login attempts',
    ['user_id', 'ip_address']
)

# Authorization metrics
authorization_failures = Counter(
    'authorization_failures_total',
    'Total authorization failures',
    ['user_id', 'resource', 'action']
)

# Rate limiting metrics
rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit violations',
    ['endpoint', 'user_id']
)

# Webhook metrics
webhook_failures = Counter(
    'webhook_failures_total',
    'Total webhook failures',
    ['webhook_type', 'error_type']
)

# Security alerts
security_alerts = Counter(
    'security_alerts_total',
    'Total security alerts',
    ['alert_type', 'severity']
)
```

### 2. Intrusion Detection

#### Security Event Monitoring
```python
# src/monitoring/intrusion_detection.py
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class IntrusionDetector:
    """Detects potential security intrusions"""
    
    def __init__(self):
        self.failed_login_attempts = defaultdict(int)
        self.suspicious_ips = set()
        self.rate_violations = defaultdict(int)
    
    def check_failed_logins(self, user_id: str, ip_address: str):
        """Check for failed login attempts"""
        self.failed_login_attempts[user_id] += 1
        
        # Alert if more than 5 failed attempts
        if self.failed_login_attempts[user_id] > 5:
            logger.warning(
                f"Multiple failed login attempts: user={user_id}, "
                f"attempts={self.failed_login_attempts[user_id]}"
            )
            self.suspicious_ips.add(ip_address)
    
    def check_rate_limiting(self, endpoint: str, user_id: str):
        """Check for rate limit violations"""
        self.rate_violations[(endpoint, user_id)] += 1
        
        # Alert if more than 10 violations
        if self.rate_violations[(endpoint, user_id)] > 10:
            logger.warning(
                f"Excessive rate limit violations: endpoint={endpoint}, "
                f"user={user_id}, violations={self.rate_violations[(endpoint, user_id)]}"
            )
    
    def check_suspicious_activity(self, user_id: str, activity: str):
        """Check for suspicious activity patterns"""
        # Implement suspicious activity detection logic
        pass

# Global intrusion detector
intrusion_detector = IntrusionDetector()
```

---

## Alerting Configuration

### 1. Prometheus Alerting Rules

#### Alert Rules Configuration
```yaml
# docker/prometheus/alerts.yml
groups:
  - name: sutra_alerts
    interval: 30s
    rules:
      # Application alerts
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }} seconds"
      
      - alert: ServiceDown
        expr: up{job="sutra"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Service {{ $labels.instance }} is down"
      
      # Database alerts
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count > pg_settings_max_connections * 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
          description: "Database connection pool is {{ $value }}% full"
      
      - alert: SlowDatabaseQueries
        expr: rate(pg_stat_statements_mean_time_ms[5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "Average query time is {{ $value }}ms"
      
      # Redis alerts
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis instance {{ $labels.instance }} is down"
      
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is {{ $value }}%"
      
      # System alerts
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
      
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
      
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low"
          description: "Disk space is {{ $value }}% available"
      
      # Security alerts
      - alert: HighFailedLoginRate
        expr: rate(auth_attempts_total{status="failure"}[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High failed login rate"
          description: "Failed login rate is {{ $value }} attempts/min"
      
      - alert: HighRateLimitViolations
        expr: rate(rate_limit_exceeded_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit violations"
          description: "Rate limit violations are {{ $value }} violations/min"
```

### 2. Alertmanager Configuration

#### Alertmanager Setup
```yaml
# docker/prometheus/alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true
    
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#sutra-alerts'
        send_resolved: true
  
  - name: 'critical-alerts'
    slack_configs:
      - channel: '#sutra-critical'
        send_resolved: true
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'warning-alerts'
    slack_configs:
      - channel: '#sutra-warnings'
        send_resolved: true
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## Dashboard Setup

### 1. Grafana Dashboards

#### Main Dashboard Configuration
```json
{
  "dashboard": {
    "title": "SUTRA Core - Main Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "Errors"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "title": "Redis Memory Usage",
        "targets": [
          {
            "expr": "redis_memory_used_bytes / 1024 / 1024 / 1024",
            "legendFormat": "GB"
          }
        ]
      },
      {
        "title": "System CPU Usage",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "System Memory Usage",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  }
}
```

### 2. Dashboard Import

#### Import Dashboards
```bash
# Import main dashboard
curl -X POST \
  http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-dashboards/main-dashboard.json

# Import database dashboard
curl -X POST \
  http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-dashboards/database-dashboard.json

# Import system dashboard
curl -X POST \
  http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-dashboards/system-dashboard.json
```

---

## Monitoring Checklist

### Pre-Deployment
- [ ] Prometheus configured and running
- [ ] Grafana configured and dashboards imported
- [ ] Alertmanager configured and notifications tested
- [ ] All exporters running (PostgreSQL, Redis, Node)
- [ ] Application metrics endpoint accessible
- [ ] Health checks implemented and tested
- [ ] Alert rules configured and tested
- [ ] Notification channels configured

### Post-Deployment
- [ ] Verify metrics collection
- [ ] Verify dashboards display data
- [ ] Test alert notifications
- [ ] Monitor system performance
- [ ] Review alert thresholds
- [ ] Adjust monitoring as needed
- [ ] Document monitoring procedures
- [ ] Train team on monitoring tools

---

## Conclusion

This monitoring setup provides comprehensive visibility into the SUTRA Core system. Regular monitoring and alert adjustments are essential for maintaining optimal system performance and reliability.

**Remember:** Monitoring is only valuable if you act on the data it provides.

---

**Document Owner:** DevOps Team  
**Last Reviewed:** 2026-04-27  
**Next Review:** 2026-07-27
