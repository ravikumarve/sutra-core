#!/bin/bash
#
# SUTRA Deployment Script
# Automated deployment for production and staging
#

set -e

# Configuration
DEPLOYMENT_ENV="${1:-production}"
COMPOSE_FILE="docker-compose.${DEPLOYMENT_ENV}.yml"
BACKUP_DIR="/var/backups/sutra"
LOG_FILE="/var/log/sutra/deploy.log"

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

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        error_exit "Please run as root"
    fi
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    
    success_msg "Docker and Docker Compose are installed"
}

# Check if environment file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        error_exit ".env file not found. Please create it from .env.example"
    fi
    
    success_msg "Environment file found"
}

# Create backup before deployment
create_backup() {
    log "Creating backup before deployment..."
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    
    # Backup database
    if [ -f "./scripts/backup_database.sh" ]; then
        ./scripts/backup_database.sh
        success_msg "Database backup created"
    else
        warning_msg "Backup script not found, skipping backup"
    fi
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    
    docker-compose -f "${COMPOSE_FILE}" pull
    
    success_msg "Docker images pulled successfully"
}

# Stop services
stop_services() {
    log "Stopping services..."
    
    docker-compose -f "${COMPOSE_FILE}" down
    
    success_msg "Services stopped"
}

# Start services
start_services() {
    log "Starting services..."
    
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    success_msg "Services started"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations
    docker-compose -f "${COMPOSE_FILE}" exec -T app alembic upgrade head
    
    success_msg "Database migrations completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
            success_msg "Health check passed"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 5
    done
    
    error_exit "Health check failed after $max_attempts attempts"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check if all services are running
    docker-compose -f "${COMPOSE_FILE}" ps
    
    # Check application health
    if curl -f http://localhost:8000/health/database/detailed > /dev/null 2>&1; then
        success_msg "Application is healthy"
    else
        error_exit "Application health check failed"
    fi
    
    success_msg "Deployment verified successfully"
}

# Rollback on failure
rollback() {
    log "Rolling back deployment..."
    
    # Stop current deployment
    docker-compose -f "${COMPOSE_FILE}" down
    
    # Restore from backup if available
    if [ -f "${BACKUP_DIR}/latest_backup.sql.gz" ]; then
        log "Restoring from backup..."
        ./scripts/restore_database.sh "${BACKUP_DIR}/latest_backup.sql.gz"
    fi
    
    # Start previous version
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    success_msg "Rollback completed"
}

# Main deployment function
deploy() {
    log "Starting deployment to ${DEPLOYMENT_ENV}..."
    
    # Pre-deployment checks
    check_root
    check_docker
    check_env_file
    
    # Create backup
    create_backup
    
    # Pull latest images
    pull_images
    
    # Stop services
    stop_services
    
    # Start services
    start_services
    
    # Run migrations
    run_migrations
    
    # Health check
    health_check
    
    # Verify deployment
    verify_deployment
    
    success_msg "Deployment to ${DEPLOYMENT_ENV} completed successfully"
}

# Cleanup old images
cleanup() {
    log "Cleaning up old Docker images..."
    
    docker image prune -af
    
    success_msg "Cleanup completed"
}

# Show logs
show_logs() {
    log "Showing logs..."
    
    docker-compose -f "${COMPOSE_FILE}" logs -f --tail=100
}

# Main script logic
case "${2:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    cleanup)
        cleanup
        ;;
    logs)
        show_logs
        ;;
    status)
        docker-compose -f "${COMPOSE_FILE}" ps
        ;;
    *)
        echo "Usage: $0 <environment> <command>"
        echo ""
        echo "Environments:"
        echo "  production  - Production deployment"
        echo "  staging     - Staging deployment"
        echo ""
        echo "Commands:"
        echo "  deploy      - Deploy application (default)"
        echo "  rollback    - Rollback to previous version"
        echo "  cleanup     - Clean up old Docker images"
        echo "  logs        - Show application logs"
        echo "  status      - Show service status"
        exit 1
        ;;
esac

exit 0