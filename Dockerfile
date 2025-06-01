# --------------------------------------
# Stage 1: Build dependencies
# --------------------------------------
FROM python:3.9-slim AS builder

WORKDIR /install

# Install build dependencies if any (e.g., for psutil—psutil has wheels for most platforms)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------
# Stage 2: Final runtime image
# --------------------------------------
FROM python:3.9-slim

# Create a non-root user
RUN useradd --create-home --shell /bin/bash workeruser

# Create app directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy source code into /app/src
COPY src/ /app/src

# Set PYTHONPATH so that ‘worker’ package is found
ENV PYTHONPATH=/app/src

# Set environment variables defaults (can be overridden via Compose)
ENV DOCKER_SOCKET=/var/run/docker.sock \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    LOG_LEVEL=INFO

# Expose metrics port for Prometheus
EXPOSE 8000

# Switch to non-root user
USER workeruser

# Default command
CMD ["python3", "-m", "worker.main"]