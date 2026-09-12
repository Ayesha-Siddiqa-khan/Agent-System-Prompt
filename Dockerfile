# ==============================================================================
# Stage 1: Build Dependencies
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies if native C-extensions are compiled
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create isolated Python virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# Stage 2: Hardened Production Runtime
# ==============================================================================
FROM python:3.11-slim AS runner

LABEL org.opencontainers.image.title="cloud-native-service" \
      org.opencontainers.image.description="Hardened cloud-native FastAPI microservice" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Ensure minimal base OS packages and remove package cache
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create dedicated non-root user and group with UID/GID 10001
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /nonexistent appuser

# Copy isolated virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Configure runtime environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HOST=0.0.0.0

# Copy application source files
COPY --chown=appuser:appgroup src/ /app/src/

# Enforce non-root execution
USER 10001:10001

# Expose microservice port
EXPOSE 8080

# Hardened healthcheck probe using native standard library (eliminates curl/wget attack surface)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')" || exit 1

# Launch microservice
ENTRYPOINT ["uvicorn", "src.app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
