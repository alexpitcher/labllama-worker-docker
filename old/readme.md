# Python Docker Worker

## Overview
This project implements a Phase 2 Docker-based worker that:
- Listens to Docker container lifecycle events.
- Polls container metrics every 30 seconds.
- Sends heartbeats to Redis for liveness checks.
- Batches error alerts to Discord.

## Project Structure

my-worker-project/
├── src/worker/
│   ├── config.py
│   ├── logger.py
│   ├── event_listener.py
│   ├── metrics_collector.py
│   ├── discord_batcher.py
│   └── main.py
├── tests/
│   ├── test_event_listener.py
│   └── test_metrics_collector.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── Dockerfile
├── requirements.txt
├── setup.cfg
└── README.md

## Prerequisites
1. Docker installed on the host.
2. Python 3.9 environment (for local development).
3. Redis (for heartbeat).
4. Discord webhook URL (if batching alerts).

## Local Development
```bash
# Clone repository
git clone https://github.com/yourusername/my-worker-project.git
cd my-worker-project

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HOST_ID="$(hostname)-worker"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export API_KEY="test-api-key"
export METRICS_URL="http://localhost:5000/api/metrics/batch"

# Run unit tests
pytest

# Run worker locally (requires local Docker & Redis)
python -m worker.main

Building and Running in Docker

# Build image
docker build -t my-worker-app:latest .

# Run container (mount Docker socket read-only)
docker run -d \
  --name worker1 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e HOST_ID="$(hostname)-worker" \
  -e REDIS_HOST="redis.local" \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." \
  -e API_KEY="real-api-key" \
  -e METRICS_URL="http://server.local/api/metrics/batch" \
  my-worker-app:latest

CI/CD

This repository uses GitHub Actions for:
	•	Linting (flake8).
	•	Type checking (mypy).
	•	Unit testing (pytest).
	•	Docker image build on pushes to main.

Configuration

All configuration is handled via environment variables. See src/worker/config.py for the complete list and defaults.

License

MIT License

