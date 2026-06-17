# SUTRA Core - Quick Start Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2026-04-27  
**Purpose:** Rapid deployment guide for experienced users

---

## Prerequisites

- ✅ Server with Docker and Docker Compose installed
- ✅ PostgreSQL 15 database
- ✅ Redis 7 server
- ✅ SSL/TLS certificates
- ✅ Domain name configured
- ✅ Meta WhatsApp Cloud API credentials
- ✅ OpenAI API key
- ✅ Gemini API key

---

## 5-Minute Deployment

### Step 1: Clone and Configure
```bash
# Clone repository
git clone https://github.com/your-org/sutra-core.git
cd sutra-core

# Generate secrets
python3 scripts/generate_production_secrets.py

# Edit configuration
nano .env.production
# Update: DATABASE_URL, REDIS_URL, META_*, OPENAI_API_KEY, GEMINI_API_KEY
```

### Step 2: Deploy
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

# Verify deployment
curl https://api.sutra.com/health/
```

### Step 3: Configure Monitoring
```bash
# Start monitoring
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Access Grafana
# URL: http://monitoring.sutra.com
# Default: admin/admin
```

### Step 4: Setup Backups
```bash
# Create backup directory
mkdir -p /var/backups/sutra

# Test backup
bash scripts/backup_database.sh

# Schedule backups
crontab -e
# Add: 0 2 * * * cd /opt/sutra && bash scripts/backup_database.sh
```

---

## Detailed Deployment

For comprehensive deployment instructions, see:
- [Production Deployment Execution Guide](PRODUCTION_DEPLOYMENT_EXECUTION_GUIDE.md)
- [Production Deployment Checklist](PRODUCTION_DEPLOYMENT_CHECKLIST.md)

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml restart app
```

**Database connection failed:**
```bash
docker-compose -f docker-compose.prod.yml exec app python -c "
from src.db.connection import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"
```

**Redis connection failed:**
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli PING
```

**High memory usage:**
```bash
docker stats
docker-compose -f docker-compose.prod.yml restart
```

---

## Support

For detailed support, see:
- [Production Runbooks](PRODUCTION_RUNBOOKS.md)
- [Production Security Hardening](PRODUCTION_SECURITY_HARDENING.md)
- [Production Monitoring Setup](PRODUCTION_MONITORING_SETUP.md)
- [Production Backup Procedures](PRODUCTION_BACKUP_PROCEDURES.md)

---

## Next Steps

1. Configure Meta webhook
2. Test WhatsApp integration
3. Set up monitoring alerts
4. Configure backup schedules
5. Review security settings
6. Test disaster recovery

---

**Document Owner:** DevOps Team  
**Last Updated:** 2026-04-27
