# SUTRA Core - Production Runbooks

**Version:** 1.0.0  
**Last Updated:** 2026-04-27  
**Purpose:** Operational runbooks for production deployment

---

## Table of Contents

1. [Application Runbooks](#application-runbooks)
2. [Database Runbooks](#database-runbooks)
3. [Redis Runbooks](#redis-runbooks)
4. [Security Runbooks](#security-runbooks)
5. [Monitoring Runbooks](#monitoring-runbooks)
6. [Emergency Procedures](#emergency-procedures)

---

## Application Runbooks

### 1. Application Deployment

#### Deploy New Version
```bash
# 1. Create backup
cd /opt/sutra
bash scripts/backup_database.sh
bash scripts/backup_application.sh

# 2. Pull latest code
git pull origin main

# 3. Build new images
docker-compose -f docker-compose.prod.yml build

# 4. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 5. Start new deployment
docker-compose -f docker-compose.prod.yml up -d

# 6. Run database migrations
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

# 7. Health check
sleep 30
curl -f http://localhost:8000/health/

# 8. Verify deployment
curl -f http://localhost:8000/health/detailed
```

#### Rollback Deployment
```bash
# 1. Stop current deployment
cd /opt/sutra
docker-compose -f docker-compose.prod.yml down

# 2. Restore from backup
bash scripts/restore_database.sh sutra_db_YYYYMMDD_HHMMSS.sql.gz.gpg
bash scripts/restore_application.sh sutra_app_YYYYMMDD_HHMMSS.tar.gz

# 3. Start previous version
git checkout <previous-commit-hash>
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify rollback
curl -f http://localhost:8000/health/
```

### 2. Application Troubleshooting

#### Application Not Starting
```bash
# 1. Check container status
docker-compose -f docker-compose.prod.yml ps

# 2. Check container logs
docker-compose -f docker-compose.prod.yml logs app

# 3. Check for resource issues
docker stats

# 4. Check configuration
docker-compose -f docker-compose.prod.yml config

# 5. Restart application
docker-compose -f docker-compose.prod.yml restart app
```

#### High Error Rate
```bash
# 1. Check error logs
docker-compose -f docker-compose.prod.yml logs app | grep ERROR

# 2. Check application metrics
curl http://localhost:8000/metrics

# 3. Check database connectivity
docker-compose -f docker-compose.prod.yml exec app python -c "
from src.db.connection import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"

# 4. Check Redis connectivity
docker-compose -f docker-compose.prod.yml exec app python -c "
import redis.asyncio as redis
import asyncio
async def check():
    client = await redis.from_url('redis://localhost:6379')
    print(await client.ping())
    await client.close()
asyncio.run(check())
"

# 5. Restart application if needed
docker-compose -f docker-compose.prod.yml restart app
```

#### High Latency
```bash
# 1. Check response times
curl -w "@curl-format.txt" http://localhost:8000/health/

# 2. Check database query performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# 3. Check system resources
top
htop

# 4. Check database connections
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT count(*) FROM pg_stat_activity;
"

# 5. Scale application if needed
docker-compose -f docker-compose.prod.yml up -d --scale app=4
```

---

## Database Runbooks

### 1. Database Maintenance

#### Database Backup
```bash
# 1. Create backup
cd /opt/sutra
bash scripts/backup_database.sh

# 2. Verify backup
ls -lh /var/backups/sutra/database/

# 3. Test restore (optional)
bash scripts/restore_database.sh <backup-file>
```

#### Database Restore
```bash
# 1. Stop application
cd /opt/sutra
docker-compose -f docker-compose.prod.yml stop app

# 2. Restore database
bash scripts/restore_database.sh sutra_db_YYYYMMDD_HHMMSS.sql.gz.gpg

# 3. Start application
docker-compose -f docker-compose.prod.yml start app

# 4. Verify restore
curl -f http://localhost:8000/health/database
```

#### Database Migration
```bash
# 1. Create backup
bash scripts/backup_database.sh

# 2. Run migrations
cd /opt/sutra
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

# 3. Verify migration
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT version FROM alembic_version;
"

# 4. Test application
curl -f http://localhost:8000/health/
```

#### Database Rollback
```bash
# 1. Check current version
cd /opt/sutra
docker-compose -f docker-compose.prod.yml exec app alembic current

# 2. Rollback to specific version
docker-compose -f docker-compose.prod.yml exec -T app alembic downgrade <revision>

# 3. Verify rollback
docker-compose -f docker-compose.prod.yml exec app alembic current

# 4. Test application
curl -f http://localhost:8000/health/
```

### 2. Database Troubleshooting

#### Database Connection Issues
```bash
# 1. Check database status
docker-compose -f docker-compose.prod.yml ps postgres

# 2. Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# 3. Test database connectivity
docker-compose -f docker-compose.prod.yml exec app python -c "
from src.db.connection import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"

# 4. Check connection pool
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT count(*) FROM pg_stat_activity;
"

# 5. Restart database if needed
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Slow Database Queries
```bash
# 1. Identify slow queries
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# 2. Check query execution plan
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
EXPLAIN ANALYZE <your-query>;
"

# 3. Check index usage
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
"

# 4. Analyze tables
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
ANALYZE;
"

# 5. Reindex if needed
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
REINDEX DATABASE sutra_db;
"
```

#### Database Lock Issues
```bash
# 1. Check for locks
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT pid, usename, pg_blocking_pids(pid) as blocked_by,
       query as blocked_query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
"

# 2. Check long-running transactions
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"

# 3. Terminate blocking session (if necessary)
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT pg_terminate_backend(<pid>);
"
```

---

## Redis Runbooks

### 1. Redis Maintenance

#### Redis Backup
```bash
# 1. Create backup
cd /opt/sutra
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# 2. Verify backup
docker-compose -f docker-compose.prod.yml exec redis redis-cli LASTSAVE

# 3. Copy backup file
docker cp sutra_redis_1:/data/dump.rdb /var/backups/sutra/redis/
```

#### Redis Restore
```bash
# 1. Stop Redis
cd /opt/sutra
docker-compose -f docker-compose.prod.yml stop redis

# 2. Restore backup
docker cp /var/backups/sutra/redis/dump.rdb sutra_redis_1:/data/dump.rdb

# 3. Start Redis
docker-compose -f docker-compose.prod.yml start redis

# 4. Verify restore
docker-compose -f docker-compose.prod.yml exec redis redis-cli PING
```

#### Redis Flush
```bash
# ⚠️ WARNING: This will delete all data!
# 1. Backup first
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# 2. Flush all data
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# 3. Verify
docker-compose -f docker-compose.prod.yml exec redis redis-cli DBSIZE
```

### 2. Redis Troubleshooting

#### Redis Connection Issues
```bash
# 1. Check Redis status
docker-compose -f docker-compose.prod.yml ps redis

# 2. Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis

# 3. Test Redis connectivity
docker-compose -f docker-compose.prod.yml exec app python -c "
import redis.asyncio as redis
import asyncio
async def check():
    client = await redis.from_url('redis://localhost:6379')
    print(await client.ping())
    await client.close()
asyncio.run(check())
"

# 4. Check Redis memory
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory

# 5. Restart Redis if needed
docker-compose -f docker-compose.prod.yml restart redis
```

#### High Memory Usage
```bash
# 1. Check memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory

# 2. Check key count
docker-compose -f docker-compose.prod.yml exec redis redis-cli DBSIZE

# 3. Find large keys
docker-compose -f docker-compose.prod.yml exec redis redis-cli --bigkeys

# 4. Check memory per key
docker-compose -f docker-compose.prod.yml exec redis redis-cli MEMORY USAGE <key>

# 5. Delete old keys if needed
docker-compose -f docker-compose.prod.yml exec redis redis-cli --scan --pattern "<pattern>" | xargs redis-cli DEL
```

#### Redis Performance Issues
```bash
# 1. Check Redis stats
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO stats

# 2. Check slow log
docker-compose -f docker-compose.prod.yml exec redis redis-cli SLOWLOG GET 10

# 3. Check client connections
docker-compose -f docker-compose.prod.yml exec redis redis-cli CLIENT LIST

# 4. Monitor commands
docker-compose -f docker-compose.prod.yml exec redis redis-cli MONITOR

# 5. Restart Redis if needed
docker-compose -f docker-compose.prod.yml restart redis
```

---

## Security Runbooks

### 1. Security Incidents

#### Suspicious Login Activity
```bash
# 1. Check failed login attempts
docker-compose -f docker-compose.prod.yml logs app | grep "Failed login"

# 2. Check authentication logs
docker-compose -f docker-compose.prod.yml logs app | grep "auth"

# 3. Block suspicious IP
# Add to firewall rules
sudo ufw deny from <suspicious-ip>

# 4. Review user accounts
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT id, email, last_login_at FROM users ORDER BY last_login_at DESC LIMIT 20;
"

# 5. Reset compromised passwords
docker-compose -f docker-compose.prod.yml exec app python -c "
from src.security.auth import auth_manager
print(auth_manager.hash_password('new_secure_password'))
"
```

#### Data Breach Response
```bash
# 1. Immediately stop affected services
docker-compose -f docker-compose.prod.yml stop

# 2. Preserve evidence
docker-compose -f docker-compose.prod.yml logs app > /tmp/security_incident.log
docker cp sutra_app_1:/app/logs /tmp/security_logs/

# 3. Change all secrets
python scripts/generate_production_secrets.py

# 4. Review access logs
docker-compose -f docker-compose.prod.yml logs nginx | grep <suspicious-ip>

# 5. Notify security team
# Send alert to security team
```

#### Malware Detection
```bash
# 1. Scan system for malware
sudo clamscan -r /opt/sutra

# 2. Check for suspicious processes
ps aux | grep <suspicious-process>

# 3. Check network connections
netstat -tulpn | grep <suspicious-port>

# 4. Isolate affected system
# Disconnect from network if necessary

# 5. Restore from clean backup
bash scripts/restore_database.sh <clean-backup>
bash scripts/restore_application.sh <clean-backup>
```

### 2. Security Maintenance

#### Secret Rotation
```bash
# 1. Generate new secrets
python scripts/generate_production_secrets.py

# 2. Update .env.production
nano .env.production

# 3. Restart application
cd /opt/sutra
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify new secrets
curl -f http://localhost:8000/health/

# 5. Document rotation
echo "$(date): Secret rotation completed" >> /var/log/sutra/security.log
```

#### SSL Certificate Renewal
```bash
# 1. Check certificate expiry
openssl x509 -in /etc/ssl/certs/sutra.crt -noout -dates

# 2. Renew certificate
sudo certbot renew --quiet

# 3. Reload nginx
sudo systemctl reload nginx

# 4. Verify new certificate
curl -I https://api.sutra.com

# 5. Test SSL configuration
openssl s_client -connect api.sutra.com:443 -servername api.sutra.com
```

---

## Monitoring Runbooks

### 1. Alert Response

#### High CPU Usage Alert
```bash
# 1. Check CPU usage
top
htop

# 2. Identify high CPU processes
ps aux --sort=-%cpu | head -20

# 3. Check application metrics
curl http://localhost:8000/metrics

# 4. Scale application if needed
docker-compose -f docker-compose.prod.yml up -d --scale app=4

# 5. Optimize if needed
# Review code for optimization opportunities
```

#### High Memory Usage Alert
```bash
# 1. Check memory usage
free -h
top

# 2. Identify high memory processes
ps aux --sort=-%mem | head -20

# 3. Check application memory
docker stats

# 4. Restart application if needed
docker-compose -f docker-compose.prod.yml restart app

# 5. Increase memory limits if needed
# Update docker-compose.prod.yml
```

#### Disk Space Alert
```bash
# 1. Check disk usage
df -h

# 2. Find large files
find /opt/sutra -type f -size +1G -exec ls -lh {} \;

# 3. Clean up old logs
find /var/log/sutra -name "*.log" -mtime +30 -delete

# 4. Clean up Docker resources
docker system prune -a

# 5. Expand disk if needed
# Contact infrastructure team
```

### 2. Performance Tuning

#### Database Performance Tuning
```bash
# 1. Check database performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT * FROM pg_stat_activity WHERE state = 'active';
"

# 2. Optimize queries
# Review slow query log

# 3. Update statistics
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
ANALYZE;
VACUUM ANALYZE;
"

# 4. Reindex if needed
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
REINDEX DATABASE sutra_db;
"

# 5. Tune configuration
# Edit postgresql.conf
```

#### Application Performance Tuning
```bash
# 1. Check application performance
curl -w "@curl-format.txt" http://localhost:8000/health/

# 2. Profile application
# Use profiling tools

# 3. Optimize code
# Review and optimize slow code paths

# 4. Scale horizontally
docker-compose -f docker-compose.prod.yml up -d --scale app=4

# 5. Enable caching
# Review caching strategy
```

---

## Emergency Procedures

### 1. System Outage

#### Complete System Failure
```bash
# 1. Assess the situation
# Check all services status
docker-compose -f docker-compose.prod.yml ps

# 2. Identify root cause
# Check logs
docker-compose -f docker-compose.prod.yml logs

# 3. Implement temporary fix
# Restart services if needed
docker-compose -f docker-compose.prod.yml restart

# 4. Restore from backup if needed
bash scripts/restore_database.sh <latest-backup>
bash scripts/restore_application.sh <latest-backup>

# 5. Monitor system
# Watch logs and metrics
```

#### Database Failure
```bash
# 1. Stop application
docker-compose -f docker-compose.prod.yml stop app

# 2. Assess database status
docker-compose -f docker-compose.prod.yml ps postgres
docker-compose -f docker-compose.prod.yml logs postgres

# 3. Restore from backup
bash scripts/restore_database.sh <latest-backup>

# 4. Start application
docker-compose -f docker-compose.prod.yml start app

# 5. Verify system
curl -f http://localhost:8000/health/
```

#### Application Failure
```bash
# 1. Check application status
docker-compose -f docker-compose.prod.yml ps app
docker-compose -f docker-compose.prod.yml logs app

# 2. Restart application
docker-compose -f docker-compose.prod.yml restart app

# 3. If restart fails, rollback
bash scripts/restore_application.sh <previous-backup>

# 4. Verify system
curl -f http://localhost:8000/health/

# 5. Monitor for issues
docker-compose -f docker-compose.prod.yml logs -f app
```

### 2. Data Loss

#### Accidental Data Deletion
```bash
# 1. STOP! Do not make any changes
# 2. Assess the damage
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT COUNT(*) FROM <affected-table>;
"

# 3. Restore from backup
bash scripts/restore_database.sh <backup-before-deletion>

# 4. Verify restore
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT COUNT(*) FROM <affected-table>;
"

# 5. Implement safeguards
# Add additional checks and validations
```

#### Data Corruption
```bash
# 1. Identify corrupted data
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT * FROM <affected-table> WHERE <condition>;
"

# 2. Restore from backup
bash scripts/restore_database.sh <last-known-good-backup>

# 3. Verify data integrity
docker-compose -f docker-compose.prod.yml exec postgres psql -U sutra_user -d sutra_db -c "
SELECT COUNT(*) FROM <affected-table>;
"

# 4. Investigate root cause
# Check logs for errors

# 5. Implement prevention
# Add data validation checks
```

---

## Runbook Maintenance

### Regular Updates
- [ ] Review and update runbooks monthly
- [ ] Add new procedures as needed
- [ ] Remove outdated procedures
- [ ] Test critical procedures quarterly
- [ ] Train team on runbooks

### Documentation
- [ ] Document all incidents
- [ ] Update runbooks based on incidents
- [ ] Share lessons learned
- [ ] Maintain change log
- [ ] Keep runbooks version controlled

---

## Conclusion

These runbooks provide comprehensive operational procedures for the SUTRA Core system. Regular testing and updates are essential to ensure effective incident response and system maintenance.

**Remember:** Runbooks are living documents that should be continuously improved based on operational experience.

---

**Document Owner:** Operations Team  
**Last Reviewed:** 2026-04-27  
**Next Review:** 2026-07-27
