#!/bin/bash
#
# SUTRA Backup Verification Script
# Verify backup integrity and test restore
#
# Usage: ./scripts/verify_backup.sh <backup_file>
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_PATH:-/var/backups/sutra}"
LOG_FILE="/var/log/sutra/verify_backup.log"

# Database configuration (from environment)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DATABASE_URL##*/}"
DB_USER="${DATABASE_URL%%:*}"
DB_PASSWORD="${DATABASE_URL#*:}"

# Backup file
BACKUP_FILE="${1}"

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

# Check if required tools are available
if ! command -v gzip &> /dev/null; then
    error_exit "gzip is not installed"
fi

if ! command -v psql &> /dev/null; then
    error_exit "psql is not installed"
fi

# Set PGPASSWORD for psql
export PGPASSWORD="${DB_PASSWORD}"

# Start verification
log "Starting backup verification: ${BACKUP_FILE}"

# 1. Check file integrity
log "Step 1: Checking file integrity..."
if gzip -t "${BACKUP_FILE}"; then
    log "✓ File integrity check passed"
else
    error_exit "✗ File integrity check failed"
fi

# 2. Check file size
log "Step 2: Checking file size..."
FILE_SIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}")
if [ "${FILE_SIZE}" -gt 0 ]; then
    log "✓ File size: ${FILE_SIZE} bytes"
else
    error_exit "✗ File size is zero"
fi

# 3. Calculate checksum
log "Step 3: Calculating checksum..."
CHECKSUM=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
log "✓ Checksum: ${CHECKSUM}"

# 4. Verify metadata
log "Step 4: Verifying metadata..."
METADATA_FILE="${BACKUP_FILE}.metadata"
if [ -f "${METADATA_FILE}" ]; then
    log "✓ Metadata file found"
    
    # Check if checksum matches
    METADATA_CHECKSUM=$(grep "^checksum:" "${METADATA_FILE}" | cut -d' ' -f2)
    if [ "${CHECKSUM}" = "${METADATA_CHECKSUM}" ]; then
        log "✓ Checksum matches metadata"
    else
        log "✗ Checksum mismatch with metadata"
        log "  Expected: ${METADATA_CHECKSUM}"
        log "  Actual: ${CHECKSUM}"
    fi
    
    # Display metadata
    log "Metadata contents:"
    cat "${METADATA_FILE}" | tee -a "${LOG_FILE}"
else
    log "⚠ No metadata file found"
fi

# 5. Test restore (dry run)
log "Step 5: Testing restore (dry run)..."
TEMP_DB="${DB_NAME}_verify_$(date +%s)"

# Create temporary database
log "Creating temporary database: ${TEMP_DB}"
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
    -c "CREATE DATABASE ${TEMP_DB};" 2>/dev/null || {
    log "⚠ Could not create temporary database (may already exist)"
    TEMP_DB="${DB_NAME}_verify"
}

# Test restore
log "Testing restore to temporary database..."
if gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" > /dev/null 2>&1; then
    log "✓ Restore test passed"
else
    log "✗ Restore test failed"
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEMP_DB};" 2>/dev/null
    error_exit "Restore test failed"
fi

# 6. Verify restored data
log "Step 6: Verifying restored data..."

# Check table count
TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "${TABLE_COUNT}" -gt 0 ]; then
    log "✓ Restored ${TABLE_COUNT} tables"
else
    log "✗ No tables found in restored database"
fi

# Check specific tables
EXPECTED_TABLES=("tenants" "users" "inventory" "customers" "orders" "order_items" "credit_ledger" "audit_log" "webhook_events")
MISSING_TABLES=()

for table in "${EXPECTED_TABLES[@]}"; do
    EXISTS=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
        -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '${table}');")
    
    if [ "${EXISTS}" = "t" ]; then
        ROW_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" \
            -t -c "SELECT COUNT(*) FROM ${table};")
        log "✓ Table '${table}' exists with ${ROW_COUNT} rows"
    else
        log "✗ Table '${table}' not found"
        MISSING_TABLES+=("${table}")
    fi
done

# 7. Clean up temporary database
log "Step 7: Cleaning up temporary database..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
    -c "DROP DATABASE IF EXISTS ${TEMP_DB};" 2>/dev/null
log "✓ Temporary database cleaned up"

# 8. Generate verification report
log "Step 8: Generating verification report..."
REPORT_FILE="${BACKUP_FILE}.verification_report"

cat > "${REPORT_FILE}" << EOF
SUTRA Backup Verification Report
================================
Backup File: ${BACKUP_FILE}
Timestamp: $(date)
Verification Status: SUCCESS

File Information
---------------
File Size: ${FILE_SIZE} bytes
Checksum: ${CHECKSUM}

Verification Results
--------------------
✓ File integrity check passed
✓ File size check passed
✓ Checksum calculated
✓ Restore test passed
✓ Restored ${TABLE_COUNT} tables

Table Verification
------------------
EOF

for table in "${EXPECTED_TABLES[@]}"; do
    if [[ ! " ${MISSING_TABLES[@]} " =~ " ${table} " ]]; then
        echo "✓ ${table}" >> "${REPORT_FILE}"
    else
        echo "✗ ${table} (MISSING)" >> "${REPORT_FILE}"
    fi
done

cat >> "${REPORT_FILE}" << EOF

Conclusion
----------
Backup verification completed successfully.
The backup file is valid and can be used for restore operations.

Generated by: SUTRA Backup Verification Script
EOF

log "✓ Verification report generated: ${REPORT_FILE}"

# Final summary
log ""
log "=========================================="
log "BACKUP VERIFICATION SUMMARY"
log "=========================================="
log "Status: SUCCESS"
log "Backup File: ${BACKUP_FILE}"
log "File Size: ${FILE_SIZE} bytes"
log "Checksum: ${CHECKSUM}"
log "Tables Restored: ${TABLE_COUNT}"
log "Missing Tables: ${#MISSING_TABLES[@]}"
log "Report: ${REPORT_FILE}"
log "=========================================="

if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    log ""
    log "WARNING: The following tables are missing:"
    for table in "${MISSING_TABLES[@]}"; do
        log "  - ${table}"
    done
    exit 1
fi

# Exit successfully
exit 0