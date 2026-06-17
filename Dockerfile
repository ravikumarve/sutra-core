# Multi-stage Dockerfile for SUTRA Core
# Optimized for production deployment

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

ARG BUILD_DATE
ARG VCS_REF

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install project with its dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --user --no-cache-dir ".[prod]"

# ============================================
# Stage 2: Production Image
# ============================================
FROM python:3.12-slim AS production

LABEL maintainer="SUTRA Team" \
      org.opencontainers.image.title="SUTRA Core" \
      org.opencontainers.image.description="AI-powered WhatsApp ERP for India's 63 million MSMEs" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="SUTRA"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r sutra && useradd -r -g sutra sutra

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy runtime config only (source is in the wheel)
COPY alembic.ini .
COPY .env.example .env

# Create data dirs
RUN mkdir -p /app/logs /app/tmp /app/backups && \
    chown -R sutra:sutra /app

USER sutra

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
