# SUTRA Core - Production Security Hardening Guide

**Version:** 1.0.0  
**Last Updated:** 2026-04-27  
**Purpose:** Comprehensive security hardening for production deployment

---

## Table of Contents

1. [Infrastructure Security](#infrastructure-security)
2. [Application Security](#application-security)
3. [Database Security](#database-security)
4. [Network Security](#network-security)
5. [Secrets Management](#secrets-management)
6. [Monitoring & Logging](#monitoring--logging)
7. [Incident Response](#incident-response)
8. [Compliance & Auditing](#compliance--auditing)

---

## Infrastructure Security

### 1. Server Hardening

#### Operating System Security
- ✅ **Keep OS Updated:** Regular security patches and updates
  ```bash
  # Ubuntu/Debian
  sudo apt update && sudo apt upgrade -y
  
  # CentOS/RHEL
  sudo yum update -y
  ```

- ✅ **Disable Unnecessary Services:** Remove unused services and ports
  ```bash
  # List all services
  sudo systemctl list-units --type=service --state=running
  
  # Disable unnecessary services
  sudo systemctl disable <service-name>
  sudo systemctl stop <service-name>
  ```

- ✅ **Configure Firewall:** Use UFW or iptables
  ```bash
  # Ubuntu/Debian - UFW
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow ssh
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  
  # CentOS/RHEL - firewalld
  sudo firewall-cmd --set-default-zone=public
  sudo firewall-cmd --permanent --add-service=ssh
  sudo firewall-cmd --permanent --add-service=http
  sudo firewall-cmd --permanent --add-service=https
  sudo firewall-cmd --reload
  ```

- ✅ **Secure SSH Configuration:** Harden SSH access
  ```bash
  # Edit /etc/ssh/sshd_config
  sudo nano /etc/ssh/sshd_config
  
  # Recommended settings:
  Port 22222  # Change from default 22
  PermitRootLogin no
  PasswordAuthentication no
  PubkeyAuthentication yes
  MaxAuthTries 3
  ClientAliveInterval 300
  ClientAliveCountMax 2
  
  # Restart SSH
  sudo systemctl restart sshd
  ```

#### User Management
- ✅ **Create Dedicated Service User:** Run application as non-root user
  ```bash
  # Create sutra user
  sudo useradd -r -s /bin/false sutra
  
  # Add to docker group
  sudo usermod -aG docker sutra
  ```

- ✅ **Implement Sudo Policies:** Restrict sudo access
  ```bash
  # Edit sudoers file
  sudo visudo
  
  # Add specific rules
  sutra ALL=(ALL) NOPASSWD:/usr/bin/docker
  ```

#### File System Security
- ✅ **Set Proper Permissions:** Restrict file access
  ```bash
  # Application directory
  sudo chown -R sutra:sutra /opt/sutra
  sudo chmod -R 750 /opt/sutra
  
  # Configuration files
  sudo chmod 600 /opt/sutra/.env.production
  
  # Logs directory
  sudo chmod 750 /var/log/sutra
  ```

- ✅ **Enable Disk Encryption:** Encrypt sensitive data
  ```bash
  # Use LUKS for disk encryption
  sudo cryptsetup -y -v luksFormat /dev/sdb1
  ```

### 2. Docker Security

#### Container Hardening
- ✅ **Use Non-Root Containers:** Run containers as non-root user
  ```dockerfile
  # Dockerfile
  USER sutra
  ```

- ✅ **Limit Container Capabilities:** Drop unnecessary capabilities
  ```yaml
  # docker-compose.yml
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE
  ```

- ✅ **Implement Resource Limits:** Prevent resource exhaustion
  ```yaml
  # docker-compose.yml
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
  ```

- ✅ **Use Read-Only File System:** Prevent runtime modifications
  ```yaml
  # docker-compose.yml
  read_only: true
  tmpfs:
    - /tmp
  ```

#### Image Security
- ✅ **Use Official Base Images:** Prefer official images
  ```dockerfile
  FROM python:3.11-slim
  ```

- ✅ **Scan Images for Vulnerabilities:** Regular security scanning
  ```bash
  # Trivy scan
  trivy image sutra/core:latest
  
  # Docker scan
  docker scan sutra/core:latest
  ```

- ✅ **Minimize Image Size:** Reduce attack surface
  ```dockerfile
  # Multi-stage build
  FROM python:3.11-slim as builder
  # ... build steps ...
  
  FROM python:3.11-slim
  COPY --from=builder /app /app
  ```

#### Docker Daemon Security
- ✅ **Secure Docker Daemon:** Restrict Docker API access
  ```bash
  # Edit /etc/docker/daemon.json
  {
    "hosts": ["unix:///var/run/docker.sock"],
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    },
    "icc": false,
    "userland-proxy": false
  }
  
  # Restart Docker
  sudo systemctl restart docker
  ```

---

## Application Security

### 1. Authentication & Authorization

#### JWT Security
- ✅ **Use Strong Secrets:** Generate cryptographically secure secrets
  ```bash
  python scripts/generate_production_secrets.py
  ```

- ✅ **Implement Token Expiration:** Set appropriate token lifetimes
  ```python
  # Access token: 30 minutes
  # Refresh token: 7 days
  ```

- ✅ **Token Refresh Mechanism:** Implement secure token refresh
  ```python
  # Use refresh tokens to obtain new access tokens
  ```

#### Password Security
- ✅ **Strong Password Requirements:** Enforce password complexity
  ```python
  # Minimum 12 characters
  # At least one uppercase, one lowercase, one number, one special character
  ```

- ✅ **Secure Password Storage:** Use bcrypt with proper work factor
  ```python
  # bcrypt with cost factor 12
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  ```

- ✅ **Password Rotation:** Implement password expiration
  ```python
  # Require password change every 90 days
  ```

### 2. Input Validation & Sanitization

#### Input Validation
- ✅ **Validate All Inputs:** Never trust user input
  ```python
  # Use Pydantic for validation
  class UserInput(BaseModel):
      name: str = Field(..., min_length=1, max_length=100)
      email: EmailStr
      phone: str = Field(..., regex=r'^\+?[1-9]\d{1,14}$')
  ```

- ✅ **Sanitize Output:** Prevent XSS attacks
  ```python
  # Escape HTML output
  from html import escape
  safe_output = escape(user_input)
  ```

#### SQL Injection Prevention
- ✅ **Use Parameterized Queries:** Never concatenate SQL
  ```python
  # Good: Parameterized query
  await session.execute(
      "SELECT * FROM users WHERE id = :user_id",
      {"user_id": user_id}
  )
  
  # Bad: String concatenation
  await session.execute(f"SELECT * FROM users WHERE id = {user_id}")
  ```

### 3. Encryption & Data Protection

#### Data Encryption
- ✅ **Encrypt Sensitive Data:** Use AES-256 encryption
  ```python
  # EncryptionManager with Fernet
  encrypted_data = encryption_manager.encrypt(sensitive_data)
  ```

- ✅ **Encrypt in Transit:** Use TLS/SSL for all connections
  ```nginx
  # Nginx SSL configuration
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  ```

- ✅ **Encrypt at Rest:** Encrypt database backups
  ```bash
  # Encrypt backup file
  gpg --symmetric --cipher-algo AES256 backup.sql
  ```

#### Key Management
- ✅ **Secure Key Storage:** Use secrets manager
  ```bash
  # AWS Secrets Manager
  aws secretsmanager get-secret-value --secret-id sutra/production
  
  # HashiCorp Vault
  vault kv get -field=encryption_key sutra/production
  ```

- ✅ **Key Rotation:** Regular key rotation
  ```python
  # Rotate encryption keys every 90 days
  ```

### 4. Rate Limiting & DDoS Protection

#### Rate Limiting
- ✅ **Implement Rate Limiting:** Prevent API abuse
  ```python
  # Rate limiting middleware
  RATE_LIMIT_REQUESTS=100
  RATE_LIMIT_PERIOD=60
  ```

- ✅ **Per-User Rate Limits:** Individual user limits
  ```python
  # Different limits for different user roles
  admin: 1000 requests/hour
  user: 100 requests/hour
  ```

#### DDoS Protection
- ✅ **Use CDN/Proxy:** Cloudflare, AWS CloudFront
  ```yaml
  # Cloudflare configuration
  - Enable DDoS protection
  - Enable rate limiting
  - Enable bot protection
  ```

- ✅ **Implement Circuit Breakers:** Prevent cascading failures
  ```python
  # Circuit breaker pattern
  from circuitbreaker import circuit
  
  @circuit(failure_threshold=5, recovery_timeout=60)
  async def external_api_call():
      # External API call
      pass
  ```

---

## Database Security

### 1. PostgreSQL Security

#### Connection Security
- ✅ **Require SSL:** Encrypt database connections
  ```python
  # Database URL with SSL
  DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
  ```

- ✅ **Use Strong Passwords:** Generate secure database passwords
  ```bash
  python scripts/generate_production_secrets.py
  ```

- ✅ **Limit Network Access:** Restrict database access
  ```bash
  # pg_hba.conf
  host    sutra_db    sutra_user    10.0.0.0/8    scram-sha-256
  ```

#### User & Role Management
- ✅ **Principle of Least Privilege:** Minimal required permissions
  ```sql
  -- Create application user with limited permissions
  CREATE USER sutra_app WITH PASSWORD 'secure_password';
  GRANT CONNECT ON DATABASE sutra_db TO sutra_app;
  GRANT USAGE ON SCHEMA public TO sutra_app;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sutra_app;
  ```

- ✅ **Separate Roles:** Different roles for different purposes
  ```sql
  -- Read-only role
  CREATE ROLE sutra_readonly;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO sutra_readonly;
  
  -- Admin role
  CREATE ROLE sutra_admin;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sutra_admin;
  ```

#### Data Security
- ✅ **Row-Level Security:** Implement tenant isolation
  ```sql
  -- Enable RLS
  ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
  
  -- Create policy
  CREATE POLICY tenant_isolation ON tenants
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
  ```

- ✅ **Encrypt Sensitive Columns:** Use pgcrypto
  ```sql
  -- Enable pgcrypto
  CREATE EXTENSION pgcrypto;
  
  -- Encrypt sensitive data
  INSERT INTO sensitive_data (encrypted_field)
  VALUES (pgp_sym_encrypt('sensitive_data', 'encryption_key'));
  ```

### 2. Backup Security

#### Backup Encryption
- ✅ **Encrypt Backups:** Encrypt all backup files
  ```bash
  # Encrypt backup
  gpg --symmetric --cipher-algo AES256 backup.sql
  
  # Decrypt backup
  gpg --decrypt backup.sql.gpg > backup.sql
  ```

- ✅ **Secure Backup Storage:** Store backups securely
  ```bash
  # Upload to encrypted S3 bucket
  aws s3 cp backup.sql s3://encrypted-backup-bucket/sutra/
  ```

#### Backup Access Control
- ✅ **Restrict Backup Access:** Limit who can access backups
  ```bash
  # Set proper permissions
  chmod 600 /var/backups/sutra/*.sql
  chown sutra:sutra /var/backups/sutra/*.sql
  ```

---

## Network Security

### 1. SSL/TLS Configuration

#### Certificate Management
- ✅ **Use Valid Certificates:** Obtain SSL certificates
  ```bash
  # Let's Encrypt
  certbot certonly --webroot -w /var/www/html -d api.sutra.com
  ```

- ✅ **Auto-Renew Certificates:** Set up automatic renewal
  ```bash
  # Certbot auto-renewal
  certbot renew --quiet
  ```

#### SSL Configuration
- ✅ **Strong SSL Configuration:** Use modern SSL settings
  ```nginx
  # Nginx SSL configuration
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
  ssl_prefer_server_ciphers off;
  ssl_session_cache shared:SSL:10m;
  ssl_session_timeout 10m;
  ```

### 2. Network Segmentation

#### Firewall Rules
- ✅ **Implement Network Segmentation:** Separate network zones
  ```bash
  # Create separate network for database
  docker network create --driver bridge sutra-db-network
  
  # Create separate network for application
  docker network create --driver bridge sutra-app-network
  ```

- ✅ **Restrict Inter-Container Communication:** Limit container communication
  ```yaml
  # docker-compose.yml
  networks:
    default:
      internal: true
  ```

---

## Secrets Management

### 1. Secrets Storage

#### Environment Variables
- ✅ **Use Environment Variables:** Store secrets in environment
  ```bash
  # .env.production
  ENCRYPTION_KEY=your_encryption_key
  SECRET_KEY=your_secret_key
  ```

- ✅ **Restrict File Permissions:** Secure .env files
  ```bash
  chmod 600 .env.production
  ```

#### Secrets Manager
- ✅ **Use Secrets Manager:** AWS Secrets Manager, HashiCorp Vault
  ```bash
  # AWS Secrets Manager
  aws secretsmanager create-secret \
    --name sutra/production \
    --secret-string '{"ENCRYPTION_KEY":"key","SECRET_KEY":"secret"}'
  
  # HashiCorp Vault
  vault kv put sutra/production ENCRYPTION_KEY=key SECRET_KEY=secret
  ```

### 2. Secrets Rotation

#### Automated Rotation
- ✅ **Implement Key Rotation:** Regular secret rotation
  ```python
  # Rotate encryption keys every 90 days
  # Rotate JWT secrets every 90 days
  # Rotate database passwords every 90 days
  ```

- ✅ **Monitor Rotation:** Track secret rotation
  ```python
  # Log all secret rotation events
  logger.info(f"Secret rotated: {secret_name}")
  ```

---

## Monitoring & Logging

### 1. Security Monitoring

#### Intrusion Detection
- ✅ **Implement IDS:** Use intrusion detection systems
  ```bash
  # OSSEC
  sudo apt install ossec-hids-server
  
  # Fail2Ban
  sudo apt install fail2ban
  ```

- ✅ **Monitor Suspicious Activity:** Alert on suspicious behavior
  ```python
  # Monitor for failed login attempts
  if failed_login_attempts > 5:
      send_security_alert("Multiple failed login attempts")
  ```

### 2. Logging

#### Security Logging
- ✅ **Log Security Events:** Comprehensive security logging
  ```python
  # Log all authentication events
  logger.info(f"User login: {user_id} from {ip_address}")
  
  # Log all authorization failures
  logger.warning(f"Authorization failed: {user_id} attempted to access {resource}")
  ```

- ✅ **Centralized Logging:** Use centralized log management
  ```bash
  # ELK Stack
  # Splunk
  # CloudWatch Logs
  ```

#### Log Protection
- ✅ **Protect Log Files:** Secure log storage
  ```bash
  # Set proper permissions
  chmod 640 /var/log/sutra/*.log
  chown sutra:adm /var/log/sutra/*.log
  ```

- ✅ **Log Rotation:** Prevent log disk exhaustion
  ```bash
  # Logrotate configuration
  /var/log/sutra/*.log {
      daily
      rotate 30
      compress
      delaycompress
      notifempty
      create 0640 sutra adm
  }
  ```

---

## Incident Response

### 1. Incident Response Plan

#### Preparation
- ✅ **Create Incident Response Team:** Define roles and responsibilities
- ✅ **Establish Communication Channels:** Set up alerting and notification
- ✅ **Document Procedures:** Create runbooks for common incidents

#### Detection & Analysis
- ✅ **Implement Monitoring:** Comprehensive security monitoring
- ✅ **Establish Baselines:** Normal behavior baselines
- ✅ **Set Up Alerts:** Automated alerting for security events

#### Containment & Eradication
- ✅ **Isolate Affected Systems:** Prevent spread of incident
- ✅ **Preserve Evidence:** Collect and preserve forensic evidence
- ✅ **Remove Threats:** Eliminate the root cause

#### Recovery
- ✅ **Restore Systems:** Restore from clean backups
- ✅ **Verify Integrity:** Ensure systems are clean
- ✅ **Monitor for Recurrence:** Continued monitoring

#### Post-Incident Activity
- ✅ **Conduct Post-Mortem:** Learn from the incident
- ✅ **Update Procedures:** Improve response procedures
- ✅ **Communicate Findings:** Share lessons learned

---

## Compliance & Auditing

### 1. Compliance Requirements

#### Data Protection
- ✅ **GDPR Compliance:** Implement GDPR requirements
- ✅ **Data Retention:** Implement data retention policies
- ✅ **Data Deletion:** Secure data deletion procedures

#### Financial Compliance
- ✅ **PCI DSS:** If handling payment data
- ✅ **GST Compliance:** Indian GST requirements
- ✅ **Audit Trails:** Comprehensive audit logging

### 2. Auditing

#### Security Audits
- ✅ **Regular Security Audits:** Periodic security assessments
- ✅ **Penetration Testing:** Regular penetration testing
- ✅ **Vulnerability Scanning:** Continuous vulnerability scanning

#### Compliance Audits
- ✅ **Compliance Reviews:** Regular compliance reviews
- ✅ **Documentation:** Maintain compliance documentation
- ✅ **Reporting:** Generate compliance reports

---

## Security Checklist

### Pre-Deployment
- [ ] All security patches applied
- [ ] Firewall configured correctly
- [ ] SSL/TLS certificates valid
- [ ] Secrets generated and stored securely
- [ ] Database backups encrypted
- [ ] Monitoring and alerting configured
- [ ] Incident response plan in place
- [ ] Security audit completed

### Post-Deployment
- [ ] Continuous monitoring enabled
- [ ] Log rotation configured
- [ ] Backup procedures tested
- [ ] Security alerts configured
- [ ] Performance monitoring active
- [ ] Uptime monitoring configured
- [ ] Regular security scans scheduled
- [ ] Incident response tested

---

## Conclusion

This security hardening guide provides comprehensive security measures for production deployment. Regular security reviews and updates are essential to maintain a secure production environment.

**Remember:** Security is an ongoing process, not a one-time setup.

---

**Document Owner:** Security Team  
**Last Reviewed:** 2026-04-27  
**Next Review:** 2026-07-27
