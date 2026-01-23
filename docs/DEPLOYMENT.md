# Deployment Guide

This guide covers deploying the Pediatric Handoff PHI Remover in various environments.

## Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/Joshausha/pediatric-handoff-phi-remover.git
cd pediatric-handoff-phi-remover

# Build and run with Docker Compose
docker compose up -d

# View logs
docker compose logs -f

# Access at http://localhost:8000
```

## System Requirements

### Minimum
- **CPU**: 4 cores
- **RAM**: 4 GB
- **Storage**: 10 GB (includes model cache)
- **OS**: Linux, macOS, or Windows with Docker

### Recommended (for faster transcription)
- **CPU**: 8+ cores
- **RAM**: 8 GB
- **Storage**: 20 GB
- **GPU**: NVIDIA GPU with CUDA (optional, 5-10x faster)

## Deployment Options

### Option 1: Docker (Recommended)

Docker provides isolation, reproducibility, and easy updates.

```bash
# Build the image
docker build -t phi-remover .

# Run the container
docker run -d \
  --name phi-remover \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -e CORS_ORIGINS="http://your-hospital.local:8000" \
  phi-remover
```

### Option 2: Docker Compose

Best for production with persistent configuration:

```bash
# Copy and customize the compose file
cp docker-compose.yml docker-compose.prod.yml

# Edit environment variables
nano docker-compose.prod.yml

# Start
docker compose -f docker-compose.prod.yml up -d
```

### Option 3: Direct Python (Development Only)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

All settings can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `medium.en` | Whisper model size (tiny.en, base.en, small.en, medium.en, large-v3) |
| `WHISPER_DEVICE` | `cpu` | Compute device (cpu, cuda) |
| `DEBUG` | `false` | Enable debug logging |
| `CORS_ORIGINS` | `http://localhost:8000` | Comma-separated allowed origins |
| `RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window |
| `MAX_AUDIO_SIZE_MB` | `50` | Maximum upload size |
| `ENABLE_AUDIT_LOGGING` | `true` | Enable HIPAA audit logs |
| `AUDIT_LOG_FILE` | `logs/audit.log` | Audit log path |

### CORS Configuration for Hospital Networks

For hospital deployment, set `CORS_ORIGINS` to your specific hostnames:

```bash
CORS_ORIGINS="http://handoff.pediatrics.hospital.local,https://handoff.pediatrics.hospital.local"
```

## GPU Acceleration (Optional)

For NVIDIA GPUs with CUDA support:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update docker-compose.yml:
```yaml
services:
  phi-remover:
    environment:
      - WHISPER_DEVICE=cuda
      - WHISPER_COMPUTE_TYPE=float16
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

3. Rebuild and restart:
```bash
docker compose up -d --build
```

## Health Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "whisper_model": "medium.en",
  "whisper_loaded": true,
  "presidio_loaded": true
}
```

### Docker Health Check

The container includes automatic health checks. View status:

```bash
docker inspect phi-remover --format='{{.State.Health.Status}}'
```

## Audit Logs

Audit logs are HIPAA-compliant (no PHI) and stored in `logs/audit.log`.

Sample log entry:
```json
{
  "timestamp": "2026-01-22T15:30:00.000Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "transcription_complete",
  "file_size_bytes": 5242880,
  "audio_duration_seconds": 120.5,
  "phi_entities_removed": 15,
  "phi_by_type": {"PERSON": 8, "DATE_TIME": 4, "ROOM": 3},
  "processing_time_seconds": 45.2,
  "success": true
}
```

## Security Considerations

### Network Isolation

- Deploy on an isolated hospital network segment
- Use a reverse proxy (nginx) for TLS termination
- Firewall rules to restrict access to authorized workstations

### Data Flow

1. Audio recorded in browser (never leaves device during recording)
2. Audio uploaded to local server (within hospital network)
3. Transcription happens locally (no external API calls)
4. PHI removed before display
5. No persistent storage of audio or transcripts (memory only)

### Audit Compliance

- All processing events logged (without PHI)
- Logs include hashed client IPs for correlation
- Configurable log retention via standard log rotation

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs phi-remover
```

Common issues:
- Insufficient memory (increase Docker memory limit)
- Port 8000 already in use (change port mapping)
- Missing environment variables

### Slow transcription

- Use `medium.en` instead of `large-v3` for faster processing
- Add GPU acceleration if available
- Check CPU usage - may need more cores

### Rate limit errors

Increase limits in environment:
```bash
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
```

## Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build

# Or pull pre-built image (when available)
docker pull ghcr.io/joshausha/pediatric-handoff-phi-remover:latest
docker compose up -d
```
