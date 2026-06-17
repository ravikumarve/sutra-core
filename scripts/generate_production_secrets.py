#!/usr/bin/env python3
"""
Generate Secure Encryption Key for Production
Generates a cryptographically secure encryption key for production use
"""

import secrets
import base64
import hashlib
import os
from pathlib import Path


def generate_encryption_key():
    """
    Generate a cryptographically secure encryption key for production
    
    Returns:
        str: Base64 encoded encryption key
    """
    # Generate 32 bytes (256 bits) of random data
    key = secrets.token_bytes(32)
    
    # Encode as base64 for safe storage in environment variables
    encoded_key = base64.urlsafe_b64encode(key).decode('utf-8')
    
    return encoded_key


def generate_jwt_secret():
    """
    Generate a secure JWT secret for production
    
    Returns:
        str: Base64 encoded JWT secret
    """
    # Generate 64 bytes (512 bits) of random data for JWT secret
    secret = secrets.token_bytes(64)
    
    # Encode as base64 for safe storage in environment variables
    encoded_secret = base64.urlsafe_b64encode(secret).decode('utf-8')
    
    return encoded_secret


def generate_webhook_verify_token():
    """
    Generate a secure webhook verify token for production
    
    Returns:
        str: Random verify token
    """
    # Generate 32-byte random token
    token = secrets.token_urlsafe(32)
    
    return token


def generate_database_password():
    """
    Generate a secure database password for production
    
    Returns:
        str: Secure database password
    """
    # Generate 32-byte random password
    password = secrets.token_urlsafe(32)
    
    return password


def generate_redis_password():
    """
    Generate a secure Redis password for production
    
    Returns:
        str: Secure Redis password
    """
    # Generate 32-byte random password
    password = secrets.token_urlsafe(32)
    
    return password


def save_to_env_file(output_path: str = ".env.production"):
    """
    Generate all production secrets and save to .env.production file
    
    Args:
        output_path: Path to save the .env.production file
    """
    secrets_dict = {
        # Encryption
        "ENCRYPTION_KEY": generate_encryption_key(),
        
        # JWT
        "SECRET_KEY": generate_jwt_secret(),
        
        # Webhook
        "META_VERIFY_TOKEN": generate_webhook_verify_token(),
        
        # Database
        "DATABASE_PASSWORD": generate_database_password(),
        
        # Redis
        "REDIS_PASSWORD": generate_redis_password(),
    }
    
    # Create .env.production file
    env_content = """# ============================================
# SUTRA Core - Production Environment
# ============================================
# IMPORTANT: Keep this file secure and never commit to version control
# Generated: {timestamp}
# ============================================

# Application
APP_NAME=SUTRA Core
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# ============================================
# SECURITY SECRETS (GENERATED)
# ============================================

# Encryption Key (AES-256)
ENCRYPTION_KEY={encryption_key}

# JWT Secret
SECRET_KEY={secret_key}

# Webhook Verify Token
META_VERIFY_TOKEN={verify_token}

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Database URL (update with your production database details)
DATABASE_URL=postgresql://sutra_user:{database_password}@localhost:5432/sutra_db

# Database Pool Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# ============================================
# REDIS CONFIGURATION
# ============================================

# Redis URL (update with your production Redis details)
REDIS_URL=redis://:{redis_password}@localhost:6379/0

# Redis Pool Settings
REDIS_POOL_SIZE=20
REDIS_STREAM_MAX_LEN=10000

# ============================================
# META WHATSAPP CLOUD API
# ============================================

# Meta App Configuration (update with your production credentials)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_PHONE_NUMBER_ID=your_meta_phone_number_id
META_ACCESS_TOKEN=your_meta_access_token
META_WEBHOOK_URL=https://api.sutra.com/api/v1/webhooks/whatsapp

# ============================================
# LLM API CONFIGURATION
# ============================================

# OpenAI API Key (for Whisper STT)
OPENAI_API_KEY=your_openai_api_key

# Gemini API Key (for agent reasoning)
GEMINI_API_KEY=your_gemini_api_key

# Groq API Key (fallback / fast inference)
GROQ_API_KEY=your_groq_api_key

# ============================================
# MULTI-TENANCY
# ============================================

DEFAULT_TENANT_ID=default
TENANT_ISOLATION_ENABLED=true

# ============================================
# GST CONFIGURATION
# ============================================

DEFAULT_GST_STATE_CODE=24

# ============================================
# RATE LIMITING
# ============================================

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# ============================================
# MONITORING
# ============================================

MONITORING_ENABLED=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# ============================================
# BACKUP CONFIGURATION
# ============================================

BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/var/backups/sutra

# ============================================
# ALERTS
# ============================================

RESTOCK_THRESHOLD_UNITS=10
UDHAAR_ALERT_DAYS=30

# ============================================
# PERFORMANCE
# ============================================

MAX_REQUEST_SIZE=10485760
MAX_WEBHOOK_RETRIES=3
WEBHOOK_TIMEOUT=30

# ============================================
# CORS CONFIGURATION
# ============================================

# Update with your production frontend domains
CORS_ORIGINS=["https://dashboard.sutra.com","https://api.sutra.com"]

# ============================================
# TESTING
# ============================================

TEST_MODE=false
""".format(
        timestamp=__import__('datetime').datetime.now().isoformat(),
        encryption_key=secrets_dict["ENCRYPTION_KEY"],
        secret_key=secrets_dict["SECRET_KEY"],
        verify_token=secrets_dict["META_VERIFY_TOKEN"],
        database_password=secrets_dict["DATABASE_PASSWORD"],
        redis_password=secrets_dict["REDIS_PASSWORD"],
    )
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(env_content)
    
    # Set restrictive permissions
    os.chmod(output_path, 0o600)
    
    print(f"✅ Production secrets generated and saved to: {output_path}")
    print(f"🔒 File permissions set to: 600 (read/write for owner only)")
    print(f"\n⚠️  IMPORTANT SECURITY NOTES:")
    print(f"   1. Keep this file secure and never commit to version control")
    print(f"   2. Store this file in a secure location (e.g., vault, secrets manager)")
    print(f"   3. Update the placeholder values with your actual production credentials")
    print(f"   4. Distribute secrets securely to your production servers")
    print(f"   5. Rotate secrets regularly (recommended: every 90 days)")


def print_secrets():
    """
    Print generated secrets to console (for manual setup)
    """
    print("=" * 80)
    print("🔐 PRODUCTION SECRETS GENERATION")
    print("=" * 80)
    print()
    
    print("📋 Generated Secrets:")
    print("-" * 80)
    print(f"ENCRYPTION_KEY:        {generate_encryption_key()}")
    print(f"SECRET_KEY:            {generate_jwt_secret()}")
    print(f"META_VERIFY_TOKEN:     {generate_webhook_verify_token()}")
    print(f"DATABASE_PASSWORD:     {generate_database_password()}")
    print(f"REDIS_PASSWORD:        {generate_redis_password()}")
    print("-" * 80)
    print()
    
    print("⚠️  SECURITY WARNINGS:")
    print("-" * 80)
    print("1. Store these secrets securely (e.g., AWS Secrets Manager, HashiCorp Vault)")
    print("2. Never commit secrets to version control")
    print("3. Use environment-specific secrets (dev/staging/prod)")
    print("4. Rotate secrets regularly (recommended: every 90 days)")
    print("5. Use strong, unique secrets for each environment")
    print("-" * 80)
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate secure encryption keys and secrets for production"
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".env.production",
        help="Output file path (default: .env.production)"
    )
    parser.add_argument(
        "--print-only",
        "-p",
        action="store_true",
        help="Only print secrets to console (don't create file)"
    )
    
    args = parser.parse_args()
    
    if args.print_only:
        print_secrets()
    else:
        save_to_env_file(args.output)
