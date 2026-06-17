#!/bin/bash
# ============================================
# SUTRA Core - Production Deployment Script
# ============================================
# This script handles the complete production deployment process
# ============================================

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# ============================================
# CONFIGURATION
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/sutra/deployment.log"
BACKUP_DIR="/var/backups/sutra"
DEPLOYMENT_USER="sutra"
DEPLOYMENT_HOST="production.sutra.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# LOGGING FUNCTIONS
# ============================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# ============================================
# PRE-DEPLOYMENT CHECKS
# ============================================

pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if .env.production exists
    if [ ! -f "$PROJECT_DIR/.env.production" ]; then
        log_error ".env.production file not found!"
        log_error "Please create it using: python scripts/generate_production_secrets.py"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed!"
        exit 1
    fi
    
    # Check if we have enough disk space
    available_space=$(df -BG "$PROJECT_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log_warning "Low disk space: ${available_space}GB available"
    fi
    
    log_success "Pre-deployment checks passed"
}

# ============================================
# BACKUP FUNCTIONS
# ============================================

backup_database() {
    log "Creating database backup..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename
    backup_file="$BACKUP_DIR/sutra_db_$(date +%Y%m%d_%H%M%S).sql"
    
    # Run backup script
    bash "$SCRIPT_DIR/backup_database.sh"
    
    log_success "Database backup completed: $backup_file"
}

backup_application() {
    log "Creating application backup..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename
    backup_file="$BACKUP_DIR/sutra_app_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # Create application backup
    tar -czf "$backup_file" \
        -C "$PROJECT_DIR" \
        src/ \
        alembic.ini \
        requirements.txt \
        Dockerfile \
        docker-compose.prod.yml
    
    log_success "Application backup completed: $backup_file"
}

# ============================================
# DEPLOYMENT FUNCTIONS
# ============================================

build_docker_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build production images
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log_success "Docker images built successfully"
}

stop_current_deployment() {
    log "Stopping current deployment..."
    
    cd "$PROJECT_DIR"
    
    # Stop current containers
    docker-compose -f docker-compose.prod.yml down
    
    log_success "Current deployment stopped"
}

start_new_deployment() {
    log "Starting new deployment..."
    
    cd "$PROJECT_DIR"
    
    # Start new containers
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "New deployment started"
}

run_database_migrations() {
    log "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head
    
    log_success "Database migrations completed"
}

# ============================================
# HEALTH CHECKS
# ============================================

health_check() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=0
    local health_url="http://localhost:8000/health/"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 5
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

detailed_health_check() {
    log "Running detailed health checks..."
    
    # Check application health
    if curl -f -s "http://localhost:8000/health/" > /dev/null 2>&1; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
        return 1
    fi
    
    # Check database health
    if curl -f -s "http://localhost:8000/health/database" > /dev/null 2>&1; then
        log_success "Database health check passed"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check Redis health
    if curl -f -s "http://localhost:8000/health/redis" > /dev/null 2>&1; then
        log_success "Redis health check passed"
    else
        log_error "Redis health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# ============================================
# ROLLBACK FUNCTIONS
# ============================================

rollback() {
    log_error "Deployment failed, initiating rollback..."
    
    cd "$PROJECT_DIR"
    
    # Stop current deployment
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup (if available)
    if [ -f "$BACKUP_DIR/sutra_db_latest.sql" ]; then
        log "Restoring database from backup..."
        bash "$SCRIPT_DIR/restore_database.sh" "$BACKUP_DIR/sutra_db_latest.sql"
    fi
    
    # Start previous deployment (if available)
    # This would need to be implemented based on your rollback strategy
    
    log_error "Rollback completed"
    exit 1
}

# ============================================
# CLEANUP FUNCTIONS
# ============================================

cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "sutra_*.sql" -mtime +7 -delete
    find "$BACKUP_DIR" -name "sutra_*.tar.gz" -mtime +7 -delete
    
    log_success "Old backups cleaned up"
}

cleanup_docker_images() {
    log "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old images (keep last 5)
    docker images --format '{{.ID}} {{.CreatedAt}}' | \
        grep sutra | \
        sort -k2 -r | \
        tail -n +6 | \
        awk '{print $1}' | \
        xargs -r docker rmi
    
    log_success "Old Docker images cleaned up"
}

# ============================================
# NOTIFICATION FUNCTIONS
# ============================================

send_notification() {
    local status=$1
    local message=$2
    
    log "Sending deployment notification: $status"
    
    # Send Slack notification (if configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"SUTRA Deployment $status: $message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Send email notification (if configured)
    # This would need to be implemented based on your email setup
}

# ============================================
# MAIN DEPLOYMENT FUNCTION
# ============================================

main() {
    log "=========================================="
    log "SUTRA Core - Production Deployment"
    log "=========================================="
    log "Starting deployment at $(date)"
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Create backups
    backup_database
    backup_application
    
    # Build new images
    build_docker_images
    
    # Stop current deployment
    stop_current_deployment
    
    # Start new deployment
    start_new_deployment
    
    # Run database migrations
    run_database_migrations
    
    # Health checks
    if ! health_check; then
        rollback
    fi
    
    # Detailed health checks
    if ! detailed_health_check; then
        rollback
    fi
    
    # Cleanup
    cleanup_old_backups
    cleanup_docker_images
    
    # Send success notification
    send_notification "SUCCESS" "Deployment completed successfully"
    
    log_success "=========================================="
    log_success "Deployment completed successfully!"
    log_success "=========================================="
    log "Deployment finished at $(date)"
}

# ============================================
# SCRIPT EXECUTION
# ============================================

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warning "Running as root is not recommended"
fi

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Run main function
main 2>&1 | tee -a "$LOG_FILE"
