#!/bin/bash
#
# SUTRA Database Backup Script
# Automated daily backup with verification
#
# Usage: ./scripts/backup_database.sh [tenant_id]
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_PATH:-/var/backups/sutra}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/var/log/sutra/backup.log"

# Database configuration (from environment)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DATABASE_URL##*/}"
DB_USER="${DATABASE_URL%%:*}"
DB_PASSWORD="${DATABASE_URL#*:}"

# Tenant ID (optional, for tenant-specific backups)
TENANT_ID="${1:-}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    error_exit "pg_dump is not installed. Please install postgresql-client."
fi

# Set PGPASSWORD for pg_dump
export PGPASSWORD="${DB_PASSWORD}"

# Generate backup filename
if [ -n "${TENANT_ID}" ]; then
    BACKUP_FILE="${BACKUP_DIR}/tenant_${TENANT_ID}_${TIMESTAMP}.sql.gz"
    log "Starting tenant-specific backup for tenant: ${TENANT_ID}"
else
    BACKUP_FILE="${BACKUP_DIR}/full_backup_${TIMESTAMP}.sql.gz"
    log "Starting full database backup"
fi

# Perform backup
log "Backup file: ${BACKUP_FILE}"

if [ -n "${TENANT_ID}" ]; then
    # Tenant-specific backup (filter by tenant_id)
    pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --table="tenants" \
        --table="users" \
        --table="inventory" \
        --table="customers" \
        --table="orders" \
        --table="order_items" \
        --table="credit_ledger" \
        --table="audit_log" \
        --table="webhook_events" \
        --no-owner --no-acl | \
        grep -E "(^CREATE TABLE|^INSERT INTO|^COPY|tenant_${TENANT_ID})" | \
        gzip > "${BACKUP_FILE}" || error_exit "Backup failed"
else
    # Full database backup
    pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --no-owner --no-acl | gzip > "${BACKUP_FILE}" || error_exit "Backup failed"
fi

# Verify backup
log "Verifying backup..."
if gzip -t "${BACKUP_FILE}"; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "Backup verified successfully. Size: ${BACKUP_SIZE}"
else
    error_exit "Backup verification failed"
fi

# Calculate checksum
CHECKSUM=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
log "Backup checksum: ${CHECKSUM}"

# Create backup metadata
METADATA_FILE="${BACKUP_FILE}.metadata"
cat > "${METADATA_FILE}" << EOF
backup_file: ${BACKUP_FILE}
timestamp: ${TIMESTAMP}
tenant_id: ${TENANT_ID}
checksum: ${CHECKSUM}
size: ${BACKUP_SIZE}
database: ${DB_NAME}
host: ${DB_HOST}
port: ${DB_PORT}
EOF

# Clean old backups
log "Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "*.metadata" -mtime +${RETENTION_DAYS} -delete

# Log completion
log "Backup completed successfully"
log "Backup file: ${BACKUP_FILE}"
log "Metadata file: ${METADATA_FILE}"

# Exit successfully
exit 0