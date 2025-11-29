# Dockerfile for WhatsApp Llama 4 Bot
# This file defines the container image for Railway deployment

# Use Python 3.11 slim image for smaller size and better performance
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (if needed for audio/image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
# Copy all files maintaining the package structure
# This preserves relative imports (from .webhook_utils)
COPY . .

# Make start script executable
RUN chmod +x start.sh || true

# Expose port 8080 (Railway standard, but can be overridden via PORT env var)
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8080}/health')" || exit 1

# Run using start script for better flexibility
# Railway provides PORT environment variable automatically
CMD ["./start.sh"]

