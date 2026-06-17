# SUTRA Core — DevOps Automator Review

**Status**: DevOps Review Complete
**Author**: DevOps Automator
**Last Updated**: 2026-04-26
**Version**: 1.0
**Review Type**: Deployment and Infrastructure Review

---

## Executive Summary

### Overall Infrastructure Assessment

**Risk Level**: ⚠️ **MODERATE-HIGH RISK**

The SUTRA Core architecture presents significant DevOps challenges due to the aggressive resource constraints (2 vCPU / 2GB RAM) combined with high availability requirements (>99.9% uptime) and CPU-intensive workloads (Whisper transcription). While the architectural decisions are sound for the target deployment, several critical gaps must be addressed before production deployment.

**Key Findings**:
- ✅ **Strengths**: Well-defined multi-tenancy architecture, appropriate technology stack for constraints, clear performance targets
- ⚠️ **Critical Gaps**: No containerization strategy, missing CI/CD pipeline, inadequate monitoring strategy, insufficient backup procedures
- ❌ **Blockers**: High availability target (>99.9%) is unrealistic on single VPS without redundancy, no disaster recovery testing procedures

**Recommendation**: **DO NOT PROCEED TO PRODUCTION** until all Critical and High severity issues are addressed. The current architecture is suitable for MVP/alpha deployment but requires significant hardening for production with financial data.

---

## 3. CI/CD Pipeline Architecture (Continued)

### 3.1 Automated Testing Pipeline (Continued)

#### 3.1.1 GitHub Actions Workflow (Continued)

```yaml
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-mock

      - name: Run E2E tests
        env:
          DATABASE_URL: postgresql://sutra_user:sutra_password@localhost:5432/sutra_test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/e2e/ -v --cov=src --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: e2e
          name: codecov-umbrella

  # Build Docker Images
  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [lint, security, unit-tests, integration-tests, e2e-tests]
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push backend image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/backend:latest
            ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/frontend:latest
            ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.sutra.example.com
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to staging server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/sutra
            docker-compose -f docker-compose.staging.yml pull
            docker-compose -f docker-compose.staging.yml up -d
            docker-compose -f docker-compose.staging.yml ps

      - name: Run smoke tests
        run: |
          curl -f https://staging.sutra.example.com/health || exit 1

  # Deploy to Production
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://api.sutra.example.com
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_SSH_KEY }}
          script: |
            cd /opt/sutra
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml ps

      - name: Run smoke tests
        run: |
          curl -f https://api.sutra.example.com/health || exit 1

      - name: Notify deployment success
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment successful'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3.2 Security Scanning Integration

#### 3.2.1 Automated Security Pipeline

```yaml
# .github/workflows/security.yml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  # Dependency Scanning
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Snyk security scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload Snyk results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: snyk.sarif

  # Container Scanning
  container-scan:
    name: Container Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker build -t sutra-backend:latest ./backend
          docker build -t sutra-frontend:latest ./frontend

      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'sutra-backend:latest'
          format: 'sarif'
          output: 'trivy-backend.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-backend.sarif'

  # Static Application Security Testing (SAST)
  sast:
    name: Static Application Security Testing
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Semgrep SAST
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/owasp-top-ten
            p/cwe-top-25
            p/python
          publish: true

  # Secrets Scanning
  secrets-scan:
    name: Secrets Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

### 3.3 Deployment Automation

#### 3.3.1 Zero-Downtime Deployment Strategy

**Blue-Green Deployment**:

```bash
#!/bin/bash
# deploy-blue-green.sh

set -e

# Configuration
BLUE_PORT=8000
GREEN_PORT=8001
HEALTH_CHECK_URL="http://localhost:${PORT}/health"
HEALTH_CHECK_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5

# Determine which environment is currently active
if curl -f "http://localhost:${BLUE_PORT}/health" > /dev/null 2>&1; then
    CURRENT="blue"
    NEW="green"
    NEW_PORT=$GREEN_PORT
else
    CURRENT="green"
    NEW="blue"
    NEW_PORT=$BLUE_PORT
fi

echo "Current environment: $CURRENT"
echo "New environment: $NEW"

# Pull new images
docker-compose -f docker-compose.${NEW}.yml pull

# Start new environment
docker-compose -f docker-compose.${NEW}.yml up -d

# Wait for health check
echo "Waiting for health check..."
START_TIME=$(date +%s)
while true; do
    if curl -f "http://localhost:${NEW_PORT}/health" > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -ge $HEALTH_CHECK_TIMEOUT ]; then
        echo "Health check timeout after ${HEALTH_CHECK_TIMEOUT}s"
        echo "Rolling back..."
        docker-compose -f docker-compose.${NEW}.yml down
        exit 1
    fi
    
    echo "Health check failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
    sleep $HEALTH_CHECK_INTERVAL
done

# Switch traffic
echo "Switching traffic to $NEW environment..."
# Update Nginx configuration
sed -i "s/upstream backend {.*}/upstream backend { server localhost:${NEW_PORT}; }/" /etc/nginx/conf.d/backend.conf
nginx -s reload

# Wait for traffic to switch
sleep 10

# Stop old environment
echo "Stopping old environment..."
docker-compose -f docker-compose.${CURRENT}.yml down

echo "Deployment successful! New environment: $NEW"
```

**Rollback Automation**:

```bash
#!/bin/bash
# rollback.sh

set -e

# Configuration
BLUE_PORT=8000
GREEN_PORT=8001

# Determine which environment is currently active
if curl -f "http://localhost:${BLUE_PORT}/health" > /dev/null 2>&1; then
    CURRENT="blue"
    ROLLBACK="green"
    ROLLBACK_PORT=$GREEN_PORT
else
    CURRENT="green"
    ROLLBACK="blue"
    ROLLBACK_PORT=$BLUE_PORT
fi

echo "Current environment: $CURRENT"
echo "Rolling back to: $ROLLBACK"

# Start rollback environment
docker-compose -f docker-compose.${ROLLBACK}.yml up -d

# Wait for health check
echo "Waiting for health check..."
for i in {1..12}; do
    if curl -f "http://localhost:${ROLLBACK_PORT}/health" > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    echo "Health check failed, retrying..."
    sleep 5
done

# Switch traffic
echo "Switching traffic to $ROLLBACK environment..."
sed -i "s/upstream backend {.*}/upstream backend { server localhost:${ROLLBACK_PORT}; }/" /etc/nginx/conf.d/backend.conf
nginx -s reload

# Stop failed environment
echo "Stopping failed environment..."
docker-compose -f docker-compose.${CURRENT}.yml down

echo "Rollback successful! Current environment: $ROLLBACK"
```

---

## 4. Monitoring and Alerting Strategy

### 4.1 Application Performance Monitoring

#### 4.1.1 Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'sutra-production'
    environment: 'production'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "alert_rules.yml"

scrape_configs:
  # FastAPI Backend
  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Next.js Dashboard
  - job_name: 'nextjs'
    static_configs:
      - targets: ['nextjs:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 10s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

  # Node Exporter (System Metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # cAdvisor (Container Metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
```

#### 4.1.2 Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: application.rules
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          service: fastapi
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second for {{ $labels.instance }}"

      # High Response Time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
          service: fastapi
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds for {{ $labels.instance }}"

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
          service: containers
        annotations:
          summary: "High memory usage detected"
          description: "Container {{ $labels.name }} is using {{ $value | humanizePercentage }} of memory limit"

      # High CPU Usage
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
          service: containers
        annotations:
          summary: "High CPU usage detected"
          description: "Container {{ $labels.name }} is using {{ $value | humanizePercentage }} of CPU limit"

  - name: database.rules
    rules:
      # High Database Connections
      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends{datname="sutra_db"} > 40
        for: 5m
        labels:
          severity: warning
          service: postgres
        annotations:
          summary: "High database connections"
          description: "Database has {{ $value }} connections (limit: 50)"

      # Slow Database Queries
      - alert: SlowDatabaseQueries
        expr: rate(pg_stat_statements_mean_time_ms[5m]) > 100
        for: 5m
        labels:
          severity: warning
          service: postgres
        annotations:
          summary: "Slow database queries detected"
          description: "Average query time is {{ $value }}ms"

  - name: infrastructure.rules
    rules:
      # High Disk Usage
      - alert: HighDiskUsage
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 5m
        labels:
          severity: critical
          service: infrastructure
        annotations:
          summary: "High disk usage detected"
          description: "Disk usage is {{ $value | humanizePercentage }} for {{ $labels.instance }}"

      # High Load Average
      - alert: HighLoadAverage
        expr: node_load1 > 2.0
        for: 5m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "High load average detected"
          description: "1-minute load average is {{ $value }} for {{ $labels.instance }}"

      # High Memory Usage
      - alert: HighSystemMemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
          service: infrastructure
        annotations:
          summary: "High system memory usage detected"
          description: "Available memory is {{ $value | humanizePercentage }} for {{ $labels.instance }}"
```

### 4.2 Infrastructure Monitoring

#### 4.2.1 Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "SUTRA Core - Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{status}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"sutra_db\"}",
            "legendFormat": "Connections"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Container Resource Usage",
        "targets": [
          {
            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes",
            "legendFormat": "{{name}} Memory"
          },
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m])",
            "legendFormat": "{{name}} CPU"
          }
        ],
        "type": "graph"
      },
      {
        "title": "System Resources",
        "targets": [
          {
            "expr": "node_load1",
            "legendFormat": "Load Average"
          },
          {
            "expr": "(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "Memory Available %"
          },
          {
            "expr": "(node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100",
            "legendFormat": "Disk Available %"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### 4.3 Log Aggregation

#### 4.3.1 ELK Stack Configuration

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - logging_network

  logstash:
    image: logstash:8.8.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    networks:
      - logging_network
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.8.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    networks:
      - logging_network
    depends_on:
      - elasticsearch

  filebeat:
    image: elastic/filebeat:8.8.0
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - logging_network
    depends_on:
      - logstash

networks:
  logging_network:
    driver: bridge

volumes:
  elasticsearch_data:
```

---

## 5. Backup and Disaster Recovery

### 5.1 Automated Backup Strategy

#### 5.1.1 Backup Automation Script

```bash
#!/bin/bash
# backup.sh

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
S3_BUCKET="s3://sutra-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p ${BACKUP_DIR}/${DATE}

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec postgres pg_dump -U sutra_user sutra_db | gzip > ${BACKUP_DIR}/${DATE}/postgres_${DATE}.sql.gz

# Redis backup
echo "Backing up Redis..."
docker exec redis redis-cli --rdb /data/dump.rdb
docker cp redis:/data/dump.rdb ${BACKUP_DIR}/${DATE}/redis_${DATE}.rdb

# Application data backup
echo "Backing up application data..."
tar -czf ${BACKUP_DIR}/${DATE}/app_data_${DATE}.tar.gz /opt/sutra/data

# Upload to S3
echo "Uploading to S3..."
aws s3 sync ${BACKUP_DIR}/${DATE} ${S3_BUCKET}/${DATE}

# Cleanup old backups
echo "Cleaning up old backups..."
find ${BACKUP_DIR} -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;

# Verify backup
echo "Verifying backup..."
if [ -f ${BACKUP_DIR}/${DATE}/postgres_${DATE}.sql.gz ] && \
   [ -f ${BACKUP_DIR}/${DATE}/redis_${DATE}.rdb ] && \
   [ -f ${BACKUP_DIR}/${DATE}/app_data_${DATE}.tar.gz ]; then
    echo "Backup completed successfully!"
    echo "Backup location: ${BACKUP_DIR}/${DATE}"
else
    echo "Backup verification failed!"
    exit 1
fi
```

#### 5.1.2 Automated Backup Schedule

```bash
# Add to crontab
# Daily backup at 2 AM
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /opt/scripts/full_backup.sh >> /var/log/backup.log 2>&1

# Hourly incremental backup
0 * * * * /opt/scripts/incremental_backup.sh >> /var/log/backup.log 2>&1
```

### 5.2 Disaster Recovery Testing

#### 5.2.1 Restore Testing Script

```bash
#!/bin/bash
# test-restore.sh

set -e

# Configuration
BACKUP_DATE=$1
TEST_DIR="/tmp/restore_test_${BACKUP_DATE}"
POSTGRES_TEST_DB="sutra_restore_test"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20260426_020000"
    exit 1
fi

# Create test directory
mkdir -p ${TEST_DIR}

# Download backup from S3
echo "Downloading backup from S3..."
aws s3 sync s3://sutra-backups/${BACKUP_DATE} ${TEST_DIR}

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
docker exec postgres createdb -U sutra_user ${POSTGRES_TEST_DB}
gunzip -c ${TEST_DIR}/postgres_${BACKUP_DATE}.sql.gz | docker exec -i postgres psql -U sutra_user -d ${POSTGRES_TEST_DB}

# Restore Redis
echo "Restoring Redis..."
docker cp ${TEST_DIR}/redis_${BACKUP_DATE}.rdb redis:/data/dump.rdb
docker restart redis

# Restore application data
echo "Restoring application data..."
tar -xzf ${TEST_DIR}/app_data_${BACKUP_DATE}.tar.gz -C ${TEST_DIR}

# Verify restore
echo "Verifying restore..."
docker exec postgres psql -U sutra_user -d ${POSTGRES_TEST_DB} -c "SELECT COUNT(*) FROM template.customers;"

# Cleanup
echo "Cleaning up..."
docker exec postgres dropdb -U sutra_user ${POSTGRES_TEST_DB}
rm -rf ${TEST_DIR}

echo "Restore test completed successfully!"
```

### 5.3 Recovery Time Objectives

| Component | RTO | RPO | Backup Frequency | Retention |
|-----------|-----|-----|------------------|-----------|
| PostgreSQL | 4 hours | 1 hour | Daily + Hourly WAL | 30 days |
| Redis | 1 hour | 15 minutes | Hourly | 7 days |
| Application Data | 4 hours | 1 hour | Daily | 30 days |
| Configuration | 1 hour | 1 hour | Per change | 90 days |

---

## 6. Scaling Strategy

### 6.1 Horizontal Scaling

#### 6.1.1 Auto-Scaling Configuration

```yaml
# docker-compose.autoscale.yml
version: '3.8'

services:
  fastapi:
    image: ghcr.io/sutra/backend:latest
    deploy:
      mode: replicated
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - fastapi
```

### 6.2 Vertical Scaling

#### 6.2.1 Resource Optimization

**Current Resource Constraints**: 2 vCPU / 2GB RAM
**Recommended Minimum**: 4 vCPU / 4GB RAM
**Optimal Configuration**: 8 vCPU / 8GB RAM

**Scaling Triggers**:
- CPU utilization > 80% for 5 minutes
- Memory utilization > 90% for 5 minutes
- Response time > 500ms for 95th percentile
- Error rate > 1% for 5 minutes

---

## 7. Infrastructure Security

### 7.1 Container Security Hardening

#### 7.1.1 Security Configuration

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  fastapi:
    image: ghcr.io/sutra/backend:latest
    security_opt:
      - no-new-privileges:true
      - seccomp:./seccomp-profile.json
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    user: "1000:1000"
    networks:
      - sutra_network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### 7.2 Network Security

#### 7.2.1 Firewall Configuration

```bash
# UFW Firewall Rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Docker internal communication
sudo ufw allow from 172.28.0.0/16

# Enable firewall
sudo ufw enable
```

---

## 8. Risk Assessment

### 8.1 Infrastructure Risks

| Risk ID | Risk Description | Likelihood | Impact | Risk Score | Mitigation |
|---------|------------------|------------|--------|------------|------------|
| INF-001 | Resource exhaustion on 2 vCPU / 2GB RAM | High | Critical | 20 | Upgrade to 4 vCPU / 4GB RAM |
| INF-002 | Single VPS failure causing downtime | Medium | Critical | 15 | Implement active-passive failover |
| INF-003 | Whisper CPU blocking other processes | High | High | 16 | Implement CPU isolation with cgroups |
| INF-004 | Database performance degradation | Medium | High | 12 | Implement connection pooling and indexing |
| INF-005 | Backup failure causing data loss | Low | Critical | 10 | Implement backup verification and testing |
| INF-006 | Security vulnerability in containers | Medium | High | 12 | Implement container security scanning |
| INF-007 | Deployment failure causing downtime | Medium | High | 12 | Implement blue-green deployment |
| INF-008 | Monitoring gap preventing issue detection | Medium | Medium | 8 | Implement comprehensive monitoring |

---

## 9. Implementation Priority Roadmap

### Phase 0: Critical Infrastructure Foundation (Weeks 1-2)
**Must Complete Before Production Deployment**

1. **Containerization** (P0)
   - Implement Docker Compose multi-container architecture
   - Create optimized Docker images with multi-stage builds
   - Configure resource limits for 2 vCPU / 2GB RAM
   - Implement container security hardening

2. **CI/CD Pipeline** (P0)
   - Set up GitHub Actions for automated testing
   - Implement security scanning integration
   - Create deployment automation
   - Add rollback procedures

3. **Monitoring and Alerting** (P0)
   - Implement Prometheus for metrics collection
   - Set up Grafana dashboards
   - Configure alert rules and notifications
   - Add log aggregation with ELK stack

4. **Backup and Recovery** (P0)
   - Implement automated backup strategy
   - Set up disaster recovery procedures
   - Create restore testing automation
   - Configure backup verification

---

### Phase 1: Infrastructure Optimization (Weeks 3-4)
**Must Complete Before Production Launch**

1. **Performance Optimization** (P1)
   - Implement CPU isolation with cgroups
   - Optimize memory usage
   - Configure disk I/O optimization
   - Tune network parameters

2. **High Availability** (P1)
   - Implement active-passive failover
   - Set up load balancing
   - Configure health checks
   - Add automatic recovery

3. **Security Hardening** (P1)
   - Implement network security
   - Configure firewall rules
   - Add secrets management
   - Set up security monitoring

---

## Final DevOps Assessment

### DevOps Posture Summary

**Current DevOps Maturity**: **MODERATE-HIGH RISK**

**Strengths**:
- ✅ Clear performance targets and requirements
- ✅ Appropriate technology stack for constraints
- ✅ Well-defined multi-tenancy architecture

**Critical Gaps**:
- ❌ No containerization strategy defined
- ❌ No CI/CD pipeline implemented
- ❌ No monitoring and alerting strategy
- ❌ No backup and disaster recovery procedures
- ❌ High availability target unrealistic on single VPS

**Recommendation**: **DO NOT PROCEED TO PRODUCTION** until all Critical (P0) and High (P1) DevOps issues are addressed.

---

### DevOps Approval Criteria

**Before Production Deployment, Must Have**:

✅ **Critical DevOps Controls (P0)**:
- [ ] Docker Compose multi-container architecture operational
- [ ] CI/CD pipeline with automated testing and deployment
- [ ] Monitoring and alerting with Prometheus and Grafana
- [ ] Automated backup and disaster recovery procedures
- [ ] Container security scanning and hardening

✅ **High Priority DevOps Controls (P1)**:
- [ ] Performance optimization for CPU-only deployment
- [ ] High availability with active-passive failover
- [ ] Security hardening with network security
- [ ] Blue-green deployment with rollback automation
- [ ] Comprehensive monitoring and alerting

✅ **DevOps Testing**:
- [ ] Load testing for target throughput completed
- [ ] Disaster recovery testing verified
- [ ] Backup and restore testing completed
- [ ] Security scanning operational
- [ ] Performance monitoring active

---

### Next Steps

1. **Immediate Action (This Week)**:
   - Implement Docker Compose containerization
   - Set up CI/CD pipeline with GitHub Actions
   - Configure monitoring with Prometheus and Grafana
   - Implement automated backup strategy

2. **Short Term (Next 2 Weeks)**:
   - Optimize performance for CPU-only deployment
   - Implement high availability with failover
   - Complete security hardening
   - Set up blue-green deployment

3. **Medium Term (Next 4 Weeks)**:
   - Complete infrastructure optimization
   - Implement comprehensive monitoring
   - Finalize disaster recovery procedures
   - Complete security compliance

4. **Long Term (Ongoing)**:
   - Maintain monitoring and alerting
   - Regular security scanning
   - Continuous performance optimization
   - Ongoing capacity planning

---

## Conclusion

The SUTRA Core DevOps infrastructure requires **significant implementation** before production deployment. The aggressive resource constraints (2 vCPU / 2GB RAM) combined with high availability requirements (>99.9% uptime) create substantial challenges that must be addressed through comprehensive automation and optimization.

**DevOps Automator Recommendation**: **HALT PRODUCTION DEPLOYMENT** until all Critical (P0) and High (P1) DevOps issues are remediated and verified through comprehensive testing.

**Estimated DevOps Implementation Timeline**: **4-6 weeks** for full infrastructure automation and hardening.

**DevOps Confidence Level**: **MODERATE (60%)** — Clear requirements but significant implementation work required.

---

**DevOps Automator Review Complete**
**Next Steps**: Comprehensive technical review complete - ready for implementation planning
**Timeline**: DevOps implementation must begin immediately
**Confidence**: **MODERATE (60%)** — Critical DevOps gaps identified but implementation path clear