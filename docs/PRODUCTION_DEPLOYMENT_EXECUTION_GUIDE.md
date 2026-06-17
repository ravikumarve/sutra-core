# SUTRA Core - Production Deployment Execution Guide

**Version:** 1.0.0  
**Last Updated:** 2026-04-27  
**Purpose:** Step-by-step production deployment execution

---

## Prerequisites

### Infrastructure Requirements
- ✅ Production server(s) with minimum specifications:
  - 4 vCPU / 8GB RAM (recommended)
  - 100GB SSD storage
  - Ubuntu 22.04 LTS or similar
- ✅ PostgreSQL 15 database server
- ✅ Redis 7 server
- ✅ SSL/TLS certificates
- ✅ Domain name configured (e.g., api.sutra.com)
- ✅ DNS records pointing to production server

### Software Requirements
- ✅ Docker 24.0+
- ✅ Docker Compose 2.20+
- ✅ Python 3.11+
- ✅ Git
- ✅ Nginx (for reverse proxy)
- ✅ Certbot (for SSL certificates)

### Access Requirements
- ✅ SSH access to production server
- ✅ Database admin access
- ✅ Redis admin access
- ✅ Meta WhatsApp Cloud API credentials
- ✅ OpenAI API key (for Whisper)
- ✅ Gemini API key (for agent reasoning)
- ✅ Groq API key (optional, for fallback)

---

## Phase 1: Server Preparation

### 1.1 System Updates
```bash
# Connect to production server
ssh user@production-server

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    docker.io \
    docker-compose \
    python3 \
    python3-pip \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    curl \
    wget \
    vim

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
docker-compose --version
```

### 1.2 Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status
```

### 1.3 Create Application Directory
```bash
# Create application directory
sudo mkdir -p /opt/sutra
sudo chown $USER:$USER /opt/sutra
cd /opt/sutra

# Create necessary subdirectories
mkdir -p logs backups scripts
```

### 1.4 Clone Repository
```bash
# Clone repository (replace with your actual repository)
cd /opt/sutra
git clone https://github.com/your-org/sutra-core.git .

# Or copy files from development environment
# scp -r /path/to/sutra/* user@production-server:/opt/sutra/
```

---

## Phase 2: Secrets Generation

### 2.1 Generate Production Secrets
```bash
cd /opt/sutra

# Generate production secrets
python3 scripts/generate_production_secrets.py

# This will create .env.production file with secure secrets
```

### 2.2 Configure Environment Variables
```bash
# Edit the generated .env.production file
nano .env.production

# Update the following values with your actual credentials:
# - DATABASE_URL (with your production database credentials)
# - REDIS_URL (with your production Redis credentials)
# - META_APP_ID (from Meta Developer Portal)
# - META_APP_SECRET (from Meta Developer Portal)
# - META_PHONE_NUMBER_ID (from Meta Developer Portal)
# - META_ACCESS_TOKEN (from Meta Developer Portal)
# - META_WEBHOOK_URL (your production webhook URL)
# - OPENAI_API_KEY (from OpenAI Platform)
# - GEMINI_API_KEY (from Google AI Studio)
# - GROQ_API_KEY (from Groq Console - optional)
# - CORS_ORIGINS (your production frontend domains)

# Save and exit
```

### 2.3 Secure Environment File
```bash
# Set restrictive permissions
chmod 600 .env.production

# Verify permissions
ls -la .env.production
```

---

## Phase 3: SSL Certificate Setup

### 3.1 Obtain SSL Certificate
```bash
# Configure Nginx for SSL
sudo nano /etc/nginx/sites-available/sutra

# Add the following configuration:
server {
    listen 80;
    server_name api.sutra.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/sutra /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Obtain SSL certificate
sudo certbot --nginx -d api.sutra.com

# Follow the prompts to complete certificate setup
```

### 3.2 Verify SSL Certificate
```bash
# Test SSL configuration
curl -I https://api.sutra.com

# Check certificate details
openssl s_client -connect api.sutra.com:443 -servername api.sutra.com
```

---

## Phase 4: Database Setup

### 4.1 Create Database User and Database
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Execute the following SQL commands:
CREATE USER sutra_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE sutra_db OWNER sutra_user;
GRANT ALL PRIVILEGES ON DATABASE sutra_db TO sutra_user;
\q

# Update .env.production with the database credentials
nano .env.production
# Update DATABASE_URL with the actual credentials
```

### 4.2 Test Database Connection
```bash
# Test database connection
cd /opt/sutra
docker-compose -f docker-compose.prod.yml run --rm app python -c "
from src.db.connection import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"
```

---

## Phase 5: Redis Setup

### 5.1 Configure Redis
```bash
# If using external Redis, ensure it's accessible
# If using Docker Compose Redis, it will be configured automatically

# Test Redis connection
docker-compose -f docker-compose.prod.yml run --rm app python -c "
import redis.asyncio as redis
import asyncio
async def check():
    client = await redis.from_url('redis://localhost:6379')
    print(await client.ping())
    await client.close()
asyncio.run(check())
"
```

---

## Phase 6: Application Deployment

### 6.1 Build Docker Images
```bash
cd /opt/sutra

# Build production images
docker-compose -f docker-compose.prod.yml build --no-cache

# This may take several minutes
```

### 6.2 Run Database Migrations
```bash
# Start database container
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Verify migrations
docker-compose -f docker-compose.prod.yml exec app alembic current
```

### 6.3 Start Application
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check application logs
docker-compose -f docker-compose.prod.yml logs -f app
```

### 6.4 Verify Deployment
```bash
# Wait for services to start
sleep 30

# Check health endpoint
curl https://api.sutra.com/health/

# Check detailed health
curl https://api.sutra.com/health/detailed

# Expected output:
# {
#   "status": "healthy",
#   "checks": {
#     "application": {"healthy": true, "message": "Application is healthy"},
#     "database": {"healthy": true, "message": "Database is healthy"},
#     "redis": {"healthy": true, "message": "Redis is healthy"},
#     "agents": {"healthy": true, "message": "Agents are healthy"}
#   }
# }
```

---

## Phase 7: Monitoring Setup

### 7.1 Start Monitoring Services
```bash
cd /opt/sutra

# Start Prometheus and Grafana
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Wait for services to start
sleep 10

# Check monitoring services
docker-compose -f docker-compose.prod.yml ps prometheus grafana
```

### 7.2 Configure Grafana
```bash
# Access Grafana
# URL: http://monitoring.sutra.com (or your monitoring domain)
# Default credentials: admin/admin

# 1. Login to Grafana
# 2. Change default password
# 3. Add Prometheus data source
#    - URL: http://prometheus:9090
#    - Access: Server (default)
# 4. Import dashboards from /docs/grafana-dashboards/
# 5. Configure alert notifications
```

### 7.3 Verify Monitoring
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics
curl http://localhost:8000/metrics
```

---

## Phase 8: Backup Setup

### 8.1 Configure Automated Backups
```bash
# Create backup directory
sudo mkdir -p /var/backups/sutra/{database,application,volumes,config}
sudo chown $USER:$USER /var/backups/sutra

# Make backup scripts executable
chmod +x scripts/backup_database.sh
chmod +x scripts/backup_application.sh
chmod +x scripts/restore_database.sh
chmod +x scripts/restore_application.sh

# Test backup script
bash scripts/backup_database.sh

# Verify backup
ls -lh /var/backups/sutra/database/
```

### 8.2 Schedule Automated Backups
```bash
# Add cron jobs for automated backups
crontab -e

# Add the following lines:
# Daily database backup at 2:00 AM
0 2 * * * cd /opt/sutra && bash scripts/backup_database.sh >> /var/log/sutra/backup.log 2>&1

# Weekly application backup on Sunday at 3:00 AM
0 3 * * 0 cd /opt/sutra && bash scripts/backup_application.sh >> /var/log/sutra/backup.log 2>&1

# Save and exit
```

### 8.3 Configure Cloud Storage (Optional)
```bash
# Install AWS CLI (if using S3)
sudo apt install -y awscli

# Configure AWS credentials
aws configure

# Test S3 upload
aws s3 ls s3://your-backup-bucket

# Add S3 sync to backup script
# Edit scripts/backup_database.sh to include S3 upload
```

---

## Phase 9: Webhook Configuration

### 9.1 Configure Meta Webhook
```bash
# Get your webhook URL
WEBHOOK_URL="https://api.sutra.com/api/v1/webhooks/whatsapp"

# Update Meta webhook configuration
# Go to Meta Developer Portal: https://developers.facebook.com/apps/

# 1. Select your app
# 2. Go to WhatsApp > Configuration
# 3. Set Webhook URL to: https://api.sutra.com/api/v1/webhooks/whatsapp
# 4. Set Verify Token to: (value from .env.production META_VERIFY_TOKEN)
# 5. Subscribe to webhook events:
#    - messages
#    - message_status
# 6. Verify webhook
```

### 9.2 Test Webhook
```bash
# Test webhook endpoint
curl -X POST https://api.sutra.com/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "123456789",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {
            "phone_number_id": "987654321",
            "display_phone_number": "+919876543210"
          },
          "messages": [{
            "id": "msg_123",
            "from": "919876543210",
            "type": "text",
            "timestamp": "1700000000",
            "text": {
              "body": "Hello, I want to order 2 shirts"
            }
          }]
        },
        "field": "messages"
      }]
    }]
  }'

# Check application logs
docker-compose -f docker-compose.prod.yml logs app | tail -50
```

---

## Phase 10: Final Verification

### 10.1 Health Check
```bash
# Comprehensive health check
curl https://api.sutra.com/health/detailed

# Verify all components are healthy
# Expected output should show all checks as "healthy": true
```

### 10.2 Functionality Test
```bash
# Test API endpoints
curl https://api.sutra.com/

# Test metrics endpoint
curl https://api.sutra.com/metrics

# Test authentication (if applicable)
curl -X POST https://api.sutra.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "password": "test_password"}'
```

### 10.3 Performance Test
```bash
# Test response time
time curl https://api.sutra.com/health/

# Load test (optional)
# Install Apache Bench
sudo apt install -y apache2-utils

# Run load test
ab -n 1000 -c 10 https://api.sutra.com/health/
```

### 10.4 Security Test
```bash
# Test SSL configuration
openssl s_client -connect api.sutra.com:443 -servername api.sutra.com

# Test security headers
curl -I https://api.sutra.com/

# Check for common vulnerabilities
# (Optional) Run security scanner
# nmap -sV api.sutra.com
```

---

## Phase 11: Monitoring and Alerting

### 11.1 Verify Monitoring
```bash
# Check Prometheus
curl http://localhost:9090/api/v1/targets

# Check Grafana
# Access: http://monitoring.sutra.com
# Login and verify dashboards are displaying data

# Check application metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

### 11.2 Configure Alerts
```bash
# Access Alertmanager
# URL: http://localhost:9093

# Verify alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Test alert notification
# Trigger a test alert and verify notification is received
```

### 11.3 Set Up Log Aggregation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/sutra

# Add the following:
/opt/sutra/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 sutra sutra
    sharedscripts
    postrotate
        docker-compose -f /opt/sutra/docker-compose.prod.yml restart app
    endscript
}

# Test log rotation
sudo logrotate -f /etc/logrotate.d/sutra
```

---

## Phase 12: Documentation and Handoff

### 12.1 Update Documentation
```bash
# Document deployment details
nano /opt/sutra/DEPLOYMENT_NOTES.md

# Add:
# - Deployment date and time
# - Server details
# - Database connection details
# - Redis connection details
# - SSL certificate details
# - Any issues encountered and resolutions
# - Configuration changes made
```

### 12.2 Create Runbook
```bash
# Copy runbooks to accessible location
cp docs/PRODUCTION_RUNBOOKS.md /opt/sutra/
cp docs/PRODUCTION_BACKUP_PROCEDURES.md /opt/sutra/
cp docs/PRODUCTION_SECURITY_HARDENING.md /opt/sutra/

# Make runbooks accessible to operations team
sudo chown -R sutra:sutra /opt/sutra/*.md
```

### 12.3 Team Handoff
```bash
# Schedule handover meeting with operations team
# Provide:
# - Access credentials
# - Documentation location
# - Monitoring dashboards
# - Alert configuration
# - Emergency contacts
# - Runbooks location
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Container won't start
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs app

# Check for port conflicts
sudo netstat -tulpn | grep :8000

# Restart container
docker-compose -f docker-compose.prod.yml restart app
```

#### Issue: Database connection failed
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker-compose -f docker-compose.prod.yml exec app python -c "
from src.db.connection import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"
```

#### Issue: Redis connection failed
```bash
# Check Redis is running
docker-compose -f docker-compose.prod.yml ps redis

# Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli PING
```

#### Issue: SSL certificate error
```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Restart Nginx
sudo systemctl restart nginx
```

#### Issue: High memory usage
```bash
# Check memory usage
free -h
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Scale down if needed
docker-compose -f docker-compose.prod.yml up -d --scale app=2
```

---

## Post-Deployment Checklist

### Immediate (First 24 Hours)
- [ ] Monitor system performance closely
- [ ] Verify all monitoring alerts are working
- [ ] Check backup procedures are running
- [ ] Review security logs for any issues
- [ ] Test disaster recovery procedures
- [ ] Verify webhook is receiving messages
- [ ] Check agent coordination is working
- [ ] Monitor database performance

### Short-term (First Week)
- [ ] Conduct security audit
- [ ] Performance optimization
- [ ] Load testing
- [ ] User acceptance testing
- [ ] Documentation updates
- [ ] Team training
- [ ] Incident response testing
- [ ] Backup verification

### Long-term (First Month)
- [ ] Regular security reviews
- [ ] Performance tuning
- [ ] Capacity planning
- [ ] Disaster recovery testing
- [ ] Process optimization
- [ ] Cost optimization
- [ ] Feature enhancements
- [ ] User feedback collection

---

## Emergency Contacts

### Technical Team
- **DevOps Lead:** [Name] - [Phone] - [Email]
- **Database Admin:** [Name] - [Phone] - [Email]
- **Security Lead:** [Name] - [Phone] - [Email]

### External Services
- **Meta Support:** https://developers.facebook.com/support/
- **OpenAI Support:** https://help.openai.com/
- **Cloud Provider:** [Provider Support]

### Escalation Procedures
1. **Level 1:** Contact DevOps Lead
2. **Level 2:** Contact CTO
3. **Level 3:** Activate incident response team

---

## Conclusion

This deployment execution guide provides comprehensive step-by-step instructions for deploying the SUTRA Core system to production. Follow each phase carefully and verify each step before proceeding to the next phase.

**Remember:** Production deployment requires careful planning, testing, and monitoring. Always have a rollback plan ready and ensure proper backups are in place before making any changes.

---

**Document Owner:** DevOps Team  
**Last Updated:** 2026-04-27  
**Next Review:** 2026-07-27
