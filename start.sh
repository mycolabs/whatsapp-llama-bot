#!/bin/bash
# Start script for Railway deployment
# This script ensures the application runs correctly with Gunicorn

set -e  # Exit on error

# Export PORT from Railway environment variable (defaults to 8080)
# Railway provides PORT automatically - must use plain $PORT without quotes
export PORT=${PORT:-8080}

# Change to app directory
cd /app || exit 1

# Export PYTHONPATH to ensure imports work correctly
export PYTHONPATH="${PYTHONPATH}:/app"

# Run Gunicorn using run.py as entry point
# Railway requires $PORT without quotes: -b 0.0.0.0:$PORT
exec gunicorn run:app \
    -b 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

