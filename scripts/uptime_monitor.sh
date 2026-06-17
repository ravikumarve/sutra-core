#!/bin/bash
#
# SUTRA Uptime Monitoring Script
# Monitors service availability and sends alerts
#

set -e

# Configuration
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
LOG_FILE="/var/log/sutra/uptime_monitor.log"
CHECK_INTERVAL=60  # seconds
MAX_RETRIES=3
TIMEOUT=10  # seconds

# Services to monitor
SERVICES=(
    "http://localhost:8000/health/:SUTRA Application"
    "http://localhost:8000/health/database:Database Health"
    "http://localhost:8000/health/redis:Redis Health"
    "http://localhost:9091/-/healthy:Prometheus"
    "http://localhost:3000/api/health:Grafana"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success_msg() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Warning message
warning_msg() {
    log "${YELLOW}WARNING: $1${NC}"
}

# Send alert
send_alert() {
    local service_name="$1"
    local status="$2"
    local message="$3"
    
    if [ -n "${ALERT_WEBHOOK_URL}" ]; then
        local payload=$(cat <<EOF
{
    "service": "${service_name}",
    "status": "${status}",
    "message": "${message}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)
        
        curl -X POST -H "Content-Type: application/json" \
             -d "${payload}" \
             "${ALERT_WEBHOOK_URL}" \
             --max-time 5 \
             --silent \
             --show-error || warning_msg "Failed to send alert"
    fi
}

# Check service health
check_service() {
    local url="$1"
    local name="$2"
    local attempt=0
    local status_code=0
    
    while [ $attempt -lt $MAX_RETRIES ]; do
        status_code=$(curl -s -o /dev/null -w "%{http_code}" \
                          --max-time ${TIMEOUT} \
                          "${url}" || echo "000")
        
        if [ "${status_code}" = "200" ]; then
            success_msg "${name} is healthy (HTTP ${status_code})"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Attempt ${attempt}/${MAX_RETRIES} for ${name} (HTTP ${status_code})"
        sleep 2
    done
    
    # Service is down
    error_exit "${name} is unhealthy (HTTP ${status_code})"
    send_alert "${name}" "down" "Service returned HTTP ${status_code}"
    return 1
}

# Check database connectivity
check_database() {
    local attempt=0
    
    while [ $attempt -lt $MAX_RETRIES ]; do
        if docker exec sutra_postgres_prod pg_isready -U ${POSTGRES_USER:-sutra_user} -d ${POSTGRES_DB:-sutra_db} > /dev/null 2>&1; then
            success_msg "PostgreSQL database is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Attempt ${attempt}/${MAX_RETRIES} for PostgreSQL"
        sleep 2
    done
    
    error_exit "PostgreSQL database is not ready"
    send_alert "PostgreSQL" "down" "Database not ready after ${MAX_RETRIES} attempts"
    return 1
}

# Check Redis connectivity
check_redis() {
    local attempt=0
    
    while [ $attempt -lt $MAX_RETRIES ]; do
        if docker exec sutra_redis_prod redis-cli --raw incr ping > /dev/null 2>&1; then
            success_msg "Redis is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Attempt ${attempt}/${MAX_RETRIES} for Redis"
        sleep 2
    done
    
    error_exit "Redis is not ready"
    send_alert "Redis" "down" "Redis not ready after ${MAX_RETRIES} attempts"
    return 1
}

# Check disk space
check_disk_space() {
    local threshold=80
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "${usage}" -gt "${threshold}" ]; then
        warning_msg "Disk usage is ${usage}% (threshold: ${threshold}%)"
        send_alert "Disk Space" "warning" "Disk usage is ${usage}%"
        return 1
    fi
    
    success_msg "Disk usage is ${usage}% (below threshold)"
    return 0
}

# Check memory usage
check_memory_usage() {
    local threshold=80
    local usage=$(free | awk '/Mem/{printf("%.0f"), $3/$2*100}')
    
    if [ "${usage}" -gt "${threshold}" ]; then
        warning_msg "Memory usage is ${usage}% (threshold: ${threshold}%)"
        send_alert "Memory" "warning" "Memory usage is ${usage}%"
        return 1
    fi
    
    success_msg "Memory usage is ${usage}% (below threshold)"
    return 0
}

# Check CPU usage
check_cpu_usage() {
    local threshold=80
    local usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    
    if [ "${usage}" -gt "${threshold}" ]; then
        warning_msg "CPU usage is ${usage}% (threshold: ${threshold}%)"
        send_alert "CPU" "warning" "CPU usage is ${usage}%"
        return 1
    fi
    
    success_msg "CPU usage is ${usage}% (below threshold)"
    return 0
}

# Check container status
check_containers() {
    local containers=("sutra_app_prod" "sutra_postgres_prod" "sutra_redis_prod" "sutra_nginx_prod")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            error_exit "Container ${container} is not running"
            send_alert "Container ${container}" "down" "Container is not running"
            all_running=false
        fi
    done
    
    if [ "${all_running}" = true ]; then
        success_msg "All containers are running"
        return 0
    fi
    
    return 1
}

# Check backup status
check_backup_status() {
    local backup_dir="/var/backups/postgres"
    local max_age=86400  # 24 hours in seconds
    
    if [ ! -d "${backup_dir}" ]; then
        warning_msg "Backup directory does not exist"
        return 1
    fi
    
    local latest_backup=$(find "${backup_dir}" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
    
    if [ -z "${latest_backup}" ]; then
        warning_msg "No backup found"
        send_alert "Backup" "warning" "No backup found"
        return 1
    fi
    
    local backup_age=$(($(date +%s) - $(stat -c %Y "${latest_backup}")))
    
    if [ "${backup_age}" -gt "${max_age}" ]; then
        warning_msg "Latest backup is ${backup_age} seconds old (max: ${max_age})"
        send_alert "Backup" "warning" "Backup is ${backup_age} seconds old"
        return 1
    fi
    
    success_msg "Latest backup is ${backup_age} seconds old (within threshold)"
    return 0
}

# Run all checks
run_all_checks() {
    log "Starting uptime monitoring checks..."
    
    local failed=0
    
    # Check containers
    check_containers || failed=$((failed + 1))
    
    # Check database
    check_database || failed=$((failed + 1))
    
    # Check Redis
    check_redis || failed=$((failed + 1))
    
    # Check services
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r url name <<< "${service}"
        check_service "${url}" "${name}" || failed=$((failed + 1))
    done
    
    # Check system resources
    check_disk_space || failed=$((failed + 1))
    check_memory_usage || failed=$((failed + 1))
    check_cpu_usage || failed=$((failed + 1))
    
    # Check backup status
    check_backup_status || failed=$((failed + 1))
    
    if [ ${failed} -eq 0 ]; then
        success_msg "All uptime checks passed"
        return 0
    else
        error_exit "${failed} uptime checks failed"
        return 1
    fi
}

# Continuous monitoring
continuous_monitoring() {
    log "Starting continuous uptime monitoring (interval: ${CHECK_INTERVAL}s)..."
    
    while true; do
        run_all_checks
        sleep ${CHECK_INTERVAL}
    done
}

# Main script logic
case "${1:-check}" in
    check)
        run_all_checks
        ;;
    monitor)
        continuous_monitoring
        ;;
    *)
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  check    - Run all uptime checks once (default)"
        echo "  monitor  - Run continuous monitoring"
        exit 1
        ;;
esac

exit 0