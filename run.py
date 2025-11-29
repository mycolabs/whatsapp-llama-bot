#!/usr/bin/env python3
"""
Railway deployment entry point
This script ensures the FastAPI app runs correctly with Gunicorn.

webhook_main.py now handles both relative and absolute imports,
so we can import it directly.
"""
import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the app from webhook_main
# webhook_main.py handles import fallback automatically
from webhook_main import app

# Export app for Gunicorn
if __name__ == "__main__":
    # This allows running directly with: python run.py
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
