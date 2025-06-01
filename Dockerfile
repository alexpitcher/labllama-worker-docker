# Stage 1: Builder with dependencies
FROM python:3.9-slim AS builder

# Install build dependencies (if any C extensions required—none needed here)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

# Create a non-root user
RUN useradd --create-home --shell /bin/bash workeruser

WORKDIR /app

# Copy the installed packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy source code
COPY src/ /app/src
COPY setup.cfg .  # for linting configuration, though not needed at runtime

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    DOCKER_SOCKET=/var/run/docker.sock

# Switch to non-root user
USER workeruser

# Expose metrics port
EXPOSE 8000

# Entrypoint
CMD ["python3", "-m", "worker.main"]