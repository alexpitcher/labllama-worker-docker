# LabLlama Worker Docker

A containerized worker service for distributed Docker monitoring and system metrics collection. This worker automatically registers with a LabLlama bot and provides real-time health monitoring, metrics collection, and safe command execution capabilities.

## Features

- **Auto Registration**: Automatically registers with LabLlama bot on startup
- **Health Monitoring**: Continuous heartbeat and health status reporting
- **System Metrics**: Real-time CPU, memory, disk, and network monitoring
- **Docker Metrics**: Container status and resource usage monitoring
- **Safe Command Execution**: Controlled execution of debugging commands
- **Log Collection**: Access to worker application logs
- **Event Monitoring**: Docker event tracking and reporting

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd labllama-worker-docker

# Start the worker
docker-compose up -d

# View logs
docker-compose logs -f
```

### Using Docker

```bash
# Pull the pre-built image
docker pull ghcr.io/alexpitcher/labllama-worker-docker

# Run the container
docker run -d \
  --name labllama-worker \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e LABLLAMA_BOT_URL=http://your-bot-url:8000 \
  ghcr.io/alexpitcher/labllama-worker-docker
```

## Configuration

Configure the worker using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LABLLAMA_BOT_URL` | `http://localhost:8000` | URL of the LabLlama bot to register with |
| `WORKER_PORT` | `8080` | Port for the worker API server |
| `WORKER_HOST` | `0.0.0.0` | Host interface to bind to |
| `WORKER_HOST_ID` | Auto-generated | Unique identifier for this worker |
| `HEARTBEAT_INTERVAL` | `30` | Heartbeat interval in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## API Endpoints

The worker exposes several REST API endpoints:

### Health & Status
- `GET /health` - Health check with service status
- `GET /info` - Worker information and capabilities

### Metrics & Monitoring  
- `GET /metrics` - System metrics (CPU, memory, disk, network)
- `GET /containers` - Docker container information and metrics
- `GET /events?since=1h` - Recent Docker events

### Command Execution
- `POST /execute` - Execute safe debugging commands
- `GET /execute/commands` - List available commands

### Logs
- `GET /logs?lines=100` - Retrieve worker application logs

## Architecture

```
┌─────────────────┐    Registration    ┌─────────────────┐
│   LabLlama Bot  │←─────────────────────│ LabLlama Worker │
│                 │                     │                 │
│  - Manages      │    Heartbeat       │  - Collects     │  
│    Workers      │←─────────────────────│    Metrics     │
│  - Aggregates   │                     │  - Monitors     │
│    Data         │    API Requests    │    Docker       │
│                 │─────────────────────→│  - Executes    │
└─────────────────┘                     │    Commands     │
                                        └─────────────────┘
```

## Development

### Requirements
- Python 3.11+
- Docker & Docker Compose
- Access to Docker socket

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LABLLAMA_BOT_URL=http://localhost:8000
export WORKER_PORT=8080

# Run the worker
python worker_main.py
```

### Testing

```bash
# Run tests
pytest

# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8080/metrics
curl http://localhost:8080/containers
```

## Deployment

### Production Deployment

Use the production Docker Compose file:

```bash
docker-compose -f compose.prod.yml up -d
```

### Kubernetes

Deploy using the provided Kubernetes manifests (if available) or create your own deployment configuration.

## Monitoring

The worker provides comprehensive monitoring capabilities:

- **System Metrics**: CPU usage, memory consumption, disk space, network I/O
- **Docker Metrics**: Container status, resource usage, health checks
- **Application Logs**: Structured logging with configurable levels
- **Health Checks**: Built-in health endpoint for container orchestration

## Security

- **Safe Command Execution**: Only whitelisted commands can be executed
- **Read-only Docker Socket**: Docker socket is mounted read-only
- **Network Isolation**: Runs in isolated Docker network
- **No Root Access**: Runs as non-root user inside container

## Troubleshooting

### Common Issues

1. **Worker not registering with bot**
   - Check `LABLLAMA_BOT_URL` environment variable
   - Ensure bot is running and accessible
   - Check network connectivity

2. **Docker metrics unavailable**
   - Verify Docker socket is mounted: `/var/run/docker.sock:/var/run/docker.sock:ro`
   - Check Docker daemon is running

3. **Health check failing**
   - Check container logs: `docker logs labllama-worker`
   - Verify port 8080 is accessible
   - Check system resources

### Logs

View worker logs:
```bash
# Docker Compose
docker-compose logs -f labllama-worker

# Docker
docker logs -f labllama-worker

# Local files
tail -f logs/worker.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license information here]
