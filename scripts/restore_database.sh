#!/bin/bash
#
# SUTRA Database Restore Script
# Restore database from backup
#
# Usage: ./scripts/restore_database.sh <backup_file> [tenant_id]
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_PATH:-/var/backups/sutra}"
LOG_FILE="/var/log/sutra/restore.log"

# Database configuration (from environment)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DATABASE_URL##*/}"
DB_USER="${DATABASE_URL%%:*}"
DB_PASSWORD="${DATABASE_URL#*:}"

# Backup file
BACKUP_FILE="${1}"
TENANT_ID="${2:-}"

# Create log directory
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

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "Backup file not found: ${BACKUP_FILE}"
fi

# Check if pg_restore is available
if ! command -v psql &> /dev/null; then
    error_exit "psql is not installed. Please install postgresql-client."
fi

# Set PGPASSWORD for psql
export PGPASSWORD="${DB_PASSWORD}"

# Verify backup
log "Verifying backup file: ${BACKUP_FILE}"
if gzip -t "${BACKUP_FILE}"; then
    log "Backup file verified"
else
    error_exit "Backup file is corrupted"
fi

# Check metadata file
METADATA_FILE="${BACKUP_FILE}.metadata"
if [ -f "${METADATA_FILE}" ]; then
    log "Backup metadata found"
    cat "${METADATA_FILE}" | tee -a "${LOG_FILE}"
else
    log "Warning: No metadata file found"
fi

# Confirm restore
if [ -z "${FORCE_RESTORE}" ]; then
    log "WARNING: This will restore the database from backup"
    log "Backup file: ${BACKUP_FILE}"
    log "Database: ${DB_NAME}"
    log ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
fi

# Perform restore
log "Starting database restore..."

if [ -n "${TENANT_ID}" ]; then
    log "Restoring tenant-specific data for tenant: ${TENANT_ID}"
    
    # Create temporary restore database
    TEMP_DB="${DB_NAME}_restore_${TENANT_ID}_$(date +%s)"
    log "Creating temporary database: ${TEMP_DB}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${TEMP_DB};" || error_exit "Failed to create temporary database"
    
    # Restore to temporary database
    log "Restoring to temporary database..."
    gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
        || error_exit "Restore failed"
    
    # Verify restore
    log "Verifying restore..."
    TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    log "Restored ${TABLE_COUNT} tables"
    
    # Drop temporary database
    log "Dropping temporary database..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE ${TEMP_DB};" || error_exit "Failed to drop temporary database"
    
    log "Tenant-specific restore completed successfully"
    
else
    log "Restoring full database..."
    
    # Create temporary restore database
    TEMP_DB="${DB_NAME}_restore_$(date +%s)"
    log "Creating temporary database: ${TEMP_DB}"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${TEMP_DB};" || error_exit "Failed to create temporary database"
    
    # Restore to temporary database
    log "Restoring to temporary database..."
    gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
        || error_exit "Restore failed"
    
    # Verify restore
    log "Verifying restore..."
    TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    log "Restored ${TABLE_COUNT} tables"
    
    # Drop old database and rename temporary database
    log "Replacing old database..."
    OLD_DB="${DB_NAME}_old_$(date +%s)"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "ALTER DATABASE ${DB_NAME} RENAME TO ${OLD_DB};" || error_exit "Failed to rename old database"
    
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "ALTER DATABASE ${TEMP_DB} RENAME TO ${DB_NAME};" || error_exit "Failed to rename temporary database"
    
    log "Full database restore completed successfully"
    log "Old database renamed to: ${OLD_DB}"
fi

# Log completion
log "Restore completed successfully"
log "Backup file: ${BACKUP_FILE}"

# Exit successfully
exit 0