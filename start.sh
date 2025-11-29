#!/bin/bash
# Start script for Railway deployment
# This script ensures the application runs correctly with Gunicorn

set -e  # Exit on error

# Get port from Railway environment variable (defaults to 8080)
PORT=${PORT:-8080}

# Change to app directory
cd /app || exit 1

# Export PYTHONPATH to ensure imports work correctly
export PYTHONPATH="${PYTHONPATH}:/app"

# Run Gunicorn using run.py as entry point
# run.py handles the module imports correctly
exec gunicorn run:app \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

