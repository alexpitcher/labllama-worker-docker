# LabLlama Worker - Quick Start Guide

## TL;DR - Deploy in 2 Minutes

### For docker-01 (10.204.1.1):
```bash
# SSH to docker-01
ssh server@10.204.1.1

# One-command deployment
docker run -d --name labllama-worker \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e LABLLAMA_BOT_URL=http://YOUR_BOT_IP:8000 \
  -e WORKER_HOST_ID=docker-01 \
  --restart unless-stopped \
  15pitchera/labllama-worker-docker:latest

# Test it works
curl http://localhost:8080/health
```

### Using Docker Compose (Recommended):
```bash
# 1. Create docker-compose.yml
wget https://your-repo/docker-compose.production.yml -O docker-compose.yml

# 2. Edit YOUR_BOT_IP in the file
sed -i 's/YOUR_BOT_IP/10.204.1.100/g' docker-compose.yml

# 3. Start worker
docker compose up -d

# 4. Verify
curl http://localhost:8080/health
```

## What You Get

✅ **System Monitoring**: CPU, memory, disk metrics every 30s  
✅ **Container Monitoring**: All Docker containers with live stats  
✅ **Remote Debugging**: Safe command execution for troubleshooting  
✅ **Bot Integration**: Auto-registers with LabLlama Phase 1 bot  
✅ **Health Monitoring**: Self-healing with restart policies  

## API Endpoints

Test these on your worker:

```bash
# Health check
curl http://10.204.1.1:8080/health

# System metrics  
curl http://10.204.1.1:8080/metrics

# Container list
curl http://10.204.1.1:8080/containers

# Available debug commands
curl http://10.204.1.1:8080/execute/commands

# Execute a safe command
curl -X POST http://10.204.1.1:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "system_uptime", "params": {}}'
```

## Management Commands

```bash
# Container status
docker ps | grep labllama-worker

# Live logs  
docker logs -f labllama-worker

# Restart worker
docker restart labllama-worker

# Update to latest
docker pull 15pitchera/labllama-worker-docker:latest
docker restart labllama-worker

# Stop worker
docker stop labllama-worker
docker rm labllama-worker
```

## Integration with LabLlama Bot

Once your Phase 1 bot has HTTP API (Step 1B), the worker will:

1. **Auto-register** on startup
2. **Send heartbeats** every 30s  
3. **Provide metrics** for `/system docker-01` commands
4. **Execute debugging** commands from LLM investigations

## Troubleshooting

**Worker won't start:**
```bash
# Check Docker socket
ls -la /var/run/docker.sock

# Check port conflicts  
netstat -tlnp | grep :8080

# Check container logs
docker logs labllama-worker
```

**Can't reach bot:**
```bash
# Test bot connectivity
curl http://YOUR_BOT_IP:8000/health

# Check worker config
docker exec labllama-worker env | grep LABLLAMA_BOT_URL
```

**No metrics:**
```bash
# Test endpoints individually
curl http://localhost:8080/health
curl http://localhost:8080/metrics  
curl http://localhost:8080/containers
```

For full documentation, see the complete LabLlama Worker v2.0 Documentation.