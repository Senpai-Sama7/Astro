# ASTRO - Autonomous Agent Ecosystem
# Production Dockerfile for containerized deployment

FROM python:3.11-slim

LABEL maintainer="ASTRO Team"
LABEL description="ASTRO Autonomous Agent Ecosystem"
LABEL version="2.0.0"

# Security: Run as non-root user
RUN groupadd -r astro && useradd -r -g astro astro

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY web/ ./web/

# Create workspace directory
RUN mkdir -p workspace logs && chown -R astro:astro /app

# Switch to non-root user
USER astro

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ASTRO_ENV=production

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run API server
CMD ["python", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
