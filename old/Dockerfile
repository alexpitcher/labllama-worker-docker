########################################
# Stage 1: Build dependencies
########################################
FROM python:3.9-slim AS builder

WORKDIR /install

# Install build dependencies (e.g., gcc for any C‐extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

########################################
# Stage 2: Runtime image
########################################
FROM python:3.9-slim

# 1. Create a non‐root user
RUN useradd --create-home --shell /bin/bash workeruser

# 2. Set working directory (for finalCMD and volume purposes)
WORKDIR /app

# 3. Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 4. Copy application source code (for pip editable install / Compose mount)
COPY src/ /app/src

# 5. Install the `worker` package in editable mode so it’s in site-packages
WORKDIR /app/src
RUN pip install --no-cache-dir -e .

# 6. Prepend /app/src to PYTHONPATH so Python finds worker/ if editing in-place
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# 7. Return to /app to keep consistency with Compose mount
WORKDIR /app

# 8. Default environment variables (override via docker-compose if needed)
ENV REDIS_HOST="redis" \
    REDIS_PORT="6379" \
    LOG_LEVEL="INFO"

# 9. Switch to non‐root user
USER workeruser

# 10. Expose Prometheus metrics port
EXPOSE 8000

# 11. Entrypoint (shell form preserves environment variables)
#     `bash -lc` ensures login shell behavior, loading PYTHONPATH
CMD bash -lc "python3 -m worker.main"