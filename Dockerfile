# Pediatric Handoff PHI Remover
# HIPAA-compliant local transcription with PHI de-identification
#
# Build: docker build -t phi-remover .
# Run:   docker run -p 8000:8000 phi-remover

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (via pip URL to avoid version resolution issues)
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

# Copy application code
COPY app/ ./app/
COPY static/ ./static/

# Create directories for logs and temp files
RUN mkdir -p /app/logs /tmp/handoff-transcriber \
    && chown -R appuser:appuser /app /tmp/handoff-transcriber

# Copy model preload script
COPY scripts/preload_models.py ./scripts/

# Preload models during build (optional, increases image size but faster startup)
# Uncomment the following line to preload whisper model during build:
# RUN python scripts/preload_models.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default environment variables (can be overridden at runtime)
ENV WHISPER_MODEL=medium.en \
    DEBUG=false \
    CORS_ORIGINS=http://localhost:8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
