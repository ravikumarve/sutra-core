# SUTRA Core - Disaster Recovery Runbook

## 📋 Overview

This document provides comprehensive procedures for disaster recovery and business continuity for SUTRA Core. It covers backup strategies, recovery procedures, and incident response protocols.

**Last Updated:** 2026-04-26  
**Version:** 1.0  
**Owner:** DevOps Team

---

## 🎯 Recovery Objectives

### Recovery Time Objective (RTO)
- **Critical Systems:** 4 hours
- **Non-Critical Systems:** 24 hours

### Recovery Point Objective (RPO)
- **Database:** 1 hour (daily backups + WAL archiving)
- **Application Code:** 0 hours (Git repository)
- **Configuration:** 0 hours (Git repository + environment variables)

### Availability Targets
- **Production:** >99.9% (8.76 hours downtime/year)
- **Staging:** >99.5% (43.8 hours downtime/year)

---

## 🗄️ Backup Strategy

### 1. Database Backups

#### Automated Daily Backups
- **Schedule:** Daily at 2:00 AM UTC
- **Retention:** 30 days
- **Location:** `/var/backups/sutra/`
- **Compression:** gzip
- **Encryption:** At rest (filesystem encryption)

#### Backup Types
1. **Full Database Backup**
   - All tables and data
   - Run daily
   - File: `full_backup_YYYYMMDD_HHMMSS.sql.gz`

2. **Tenant-Specific Backup**
   - Single tenant data
   - Run on demand
   - File: `tenant_{tenant_id}_YYYYMMDD_HHMMSS.sql.gz`

3. **Schema-Only Backup**
   - Database structure only
   - Run weekly
   - File: `schema_backup_YYYYMMDD_HHMMSS.sql.gz`

#### Backup Verification
- **Automated:** Daily verification after backup
- **Manual:** Weekly full verification
- **Tests:** Integrity, checksum, restore test

### 2. Application Backups

#### Code Repository
- **Location:** GitHub (private)
- **Branches:** main, develop, feature/*
- **Backup:** GitHub provides backup
- **Frequency:** Every commit

#### Configuration Backups
- **Location:** Git repository (encrypted)
- **Files:** `.env`, config files
- **Frequency:** Every change
- **Encryption:** GPG encryption

#### Asset Backups
- **Location:** S3-compatible storage
- **Files:** User uploads, static files
- **Frequency:** Daily
- **Retention:** 90 days

---

## 🚨 Incident Response Procedures

### Severity Levels

#### P0 - Critical (Immediate Response)
- **Definition:** Complete system outage, data loss, security breach
- **Response Time:** 15 minutes
- **Resolution Time:** 4 hours
- **Escalation:** CTO, CEO

#### P1 - High (Urgent Response)
- **Definition:** Major functionality broken, significant performance degradation
- **Response Time:** 30 minutes
- **Resolution Time:** 8 hours
- **Escalation:** Engineering Lead

#### P2 - Medium (Normal Response)
- **Definition:** Minor functionality issues, moderate performance impact
- **Response Time:** 2 hours
- **Resolution Time**: 24 hours
- **Escalation:** Team Lead

#### P3 - Low (Scheduled Response)
- **Definition:** Cosmetic issues, minor bugs
- **Response Time:** 1 business day
- **Resolution Time**: 1 week
- **Escalation:** None

### Incident Response Flow

#### 1. Detection
- **Monitoring:** Prometheus alerts
- **Logs:** ELK stack
- **Users:** Support tickets
- **Automated:** Health checks

#### 2. Assessment
- **Impact:** Affected users, systems, data
- **Severity:** Assign P0-P3 level
- **Scope:** Determine incident boundaries
- **Timeline:** Estimate resolution time

#### 3. Containment
- **Isolation:** Separate affected systems
- **Mitigation:** Implement temporary fixes
- **Communication:** Notify stakeholders
- **Documentation:** Start incident log

#### 4. Resolution
- **Root Cause:** Identify underlying issue
- **Fix:** Implement permanent solution
- **Testing:** Verify fix works
- **Deployment:** Deploy to production

#### 5. Recovery
- **Restore:** Recover lost data if needed
- **Verify:** Confirm system is operational
- **Monitor:** Watch for recurrence
- **Close:** Document and close incident

---

## 🔄 Recovery Procedures

### Scenario 1: Database Corruption

#### Symptoms
- Database queries failing
- Error messages about corruption
- Inconsistent data

#### Recovery Steps

1. **Assess Damage**
   ```bash
   # Check database status
   psql -h localhost -U sutra_user -d sutra_db -c "SELECT version();"
   
   # Check table integrity
   psql -h localhost -U sutra_user -d sutra_db -c "SELECT * FROM pg_stat_database;"
   ```

2. **Stop Application**
   ```bash
   # Stop application to prevent further damage
   sudo systemctl stop sutra
   ```

3. **Identify Corruption**
   ```bash
   # Check for corrupted tables
   psql -h localhost -U sutra_user -d sutra_db -c "
   SELECT schemaname, tablename 
   FROM pg_tables 
   WHERE schemaname = 'public';
   "
   ```

4. **Restore from Backup**
   ```bash
   # Find latest good backup
   ls -lt /var/backups/sutra/full_backup_*.sql.gz | head -1
   
   # Restore database
   ./scripts/restore_database.sh /var/backups/sutra/full_backup_YYYYMMDD_HHMMSS.sql.gz
   ```

5. **Verify Restore**
   ```bash
   # Verify backup before restore
   ./scripts/verify_backup.sh /var/backups/sutra/full_backup_YYYYMMDD_HHMMSS.sql.gz
   
   # Check restored data
   psql -h localhost -U sutra_user -d sutra_db -c "SELECT COUNT(*) FROM tenants;"
   ```

6. **Restart Application**
   ```bash
   # Start application
   sudo systemctl start sutra
   
   # Verify application is running
   curl http://localhost:8000/health
   ```

7. **Monitor**
   - Watch for errors
   - Monitor performance
   - Check data consistency

#### Estimated Time: 2-4 hours

---

### Scenario 2: Complete Server Failure

#### Symptoms
- Server not responding
- No SSH access
- Hardware failure indicators

#### Recovery Steps

1. **Assess Situation**
   - Check server status
   - Contact hosting provider
   - Determine failure type

2. **Provision New Server**
   - Spin up new VPS
   - Install dependencies
   - Configure network

3. **Restore from Backup**
   ```bash
   # Copy backups from storage
   rsync -avz backup-server:/var/backups/sutra/ /var/backups/sutra/
   
   # Restore database
   ./scripts/restore_database.sh /var/backups/sutra/full_backup_YYYYMMDD_HHMMSS.sql.gz
   ```

4. **Deploy Application**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/sutra.git
   cd sutra
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run migrations
   alembic upgrade head
   
   # Start application
   sudo systemctl start sutra
   ```

5. **Update DNS**
   - Update A record
   - Wait for propagation
   - Verify DNS resolution

6. **Verify Operations**
   - Test all endpoints
   - Check database connectivity
   - Verify Redis connection
   - Test WhatsApp integration

7. **Monitor**
   - Watch for errors
   - Monitor performance
   - Check all integrations

#### Estimated Time: 4-8 hours

---

### Scenario 3: Data Loss (Accidental Deletion)

#### Symptoms
- Missing records
- Incorrect data
- User reports of lost data

#### Recovery Steps

1. **Identify Lost Data**
   - Determine what was lost
   - Identify time of loss
   - Find affected tables

2. **Stop Application**
   ```bash
   # Stop to prevent further data loss
   sudo systemctl stop sutra
   ```

3. **Point-in-Time Recovery**
   ```bash
   # Find backup before data loss
   ls -lt /var/backups/sutra/full_backup_*.sql.gz
   
   # Restore to temporary database
   ./scripts/restore_database.sh /var/backups/sutra/full_backup_YYYYMMDD_HHMMSS.sql.gz
   
   # Extract lost data
   psql -h localhost -U sutra_user -d sutra_db_restore -c "
   COPY (SELECT * FROM orders WHERE order_date < 'loss_timestamp') 
   TO STDOUT WITH CSV HEADER;
   " > lost_data.csv
   ```

4. **Restore Lost Data**
   ```bash
   # Import lost data
   psql -h localhost -U sutra_user -d sutra_db -c "
   COPY orders FROM STDIN WITH CSV HEADER;
   " < lost_data.csv
   ```

5. **Verify Data**
   - Check data integrity
   - Verify relationships
   - Confirm with users

6. **Restart Application**
   ```bash
   sudo systemctl start sutra
   ```

#### Estimated Time: 1-2 hours

---

### Scenario 4: Security Breach

#### Symptoms
- Unauthorized access
- Suspicious activity
- Data exfiltration indicators

#### Recovery Steps

1. **Contain Incident**
   ```bash
   # Immediately stop all services
   sudo systemctl stop sutra
   sudo systemctl stop redis
   sudo systemctl stop postgresql
   ```

2. **Assess Damage**
   - Review logs
   - Check for unauthorized changes
   - Identify compromised accounts
   - Determine data exposure

3. **Secure Systems**
   ```bash
   # Change all passwords
   # Rotate API keys
   # Revoke compromised tokens
   # Update firewall rules
   ```

4. **Restore from Clean Backup**
   ```bash
   # Find backup before breach
   # Verify backup integrity
   # Restore to clean state
   ./scripts/restore_database.sh /var/backups/sutra/full_backup_YYYYMMDD_HHMMSS.sql.gz
   ```

5. **Patch Vulnerabilities**
   - Update all dependencies
   - Apply security patches
   - Review and harden configuration

6. **Monitor**
   - Watch for suspicious activity
   - Review access logs
   - Monitor system performance

7. **Communicate**
   - Notify affected users
   - Report to authorities if required
   - Document incident

#### Estimated Time: 8-24 hours

---

## 🧪 Testing Procedures

### Monthly Backup Testing

#### Test Checklist
- [ ] Verify latest backup integrity
- [ ] Test restore to temporary database
- [ ] Verify restored data
- [ ] Check application functionality
- [ ] Document test results

#### Test Script
```bash
#!/bin/bash
# Monthly backup test script

# Get latest backup
LATEST_BACKUP=$(ls -t /var/backups/sutra/full_backup_*.sql.gz | head -1)

# Verify backup
./scripts/verify_backup.sh "${LATEST_BACKUP}"

# Test restore
./scripts/restore_database.sh "${LATEST_BACKUP}"

# Verify restored data
psql -h localhost -U sutra_user -d sutra_db -c "SELECT COUNT(*) FROM tenants;"

# Document results
echo "Backup test completed: $(date)" >> /var/log/sutra/backup_tests.log
```

### Quarterly Disaster Recovery Drill

#### Drill Objectives
- Test complete recovery procedures
- Verify RTO/RPO targets
- Identify gaps in procedures
- Train team members

#### Drill Scenarios
1. Complete server failure
2. Database corruption
3. Security breach
4. Data center outage

#### Drill Evaluation
- Document lessons learned
- Update procedures as needed
- Schedule follow-up training

---

## 📞 Contact Information

### Primary Contacts
- **DevOps Lead:** devops@sutra.com
- **Engineering Lead:** engineering@sutra.com
- **CTO:** cto@sutra.com

### Emergency Contacts
- **24/7 Support:** support@sutra.com
- **Hosting Provider:** [Provider Contact]
- **Security Team:** security@sutra.com

### External Services
- **GitHub:** https://github.com/your-org/sutra
- **Hosting Provider:** [Provider Portal]
- **Monitoring:** [Monitoring Dashboard]

---

## 📚 Related Documentation

- [Backup Script Documentation](scripts/backup_database.sh)
- [Restore Script Documentation](scripts/restore_database.sh)
- [Verification Script Documentation](scripts/verify_backup.sh)
- [Database Security Documentation](src/db/security.py)
- [Monitoring Documentation](docs/MONITORING.md)
- [Security Documentation](docs/SECURITY.md)

---

## 🔄 Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-04-26 | 1.0 | Initial version | DevOps Team |

---

**Document Status:** ✅ Active  
**Next Review:** 2026-07-26  
**Approved By:** DevOps Lead