#!/usr/bin/env python3
"""
Auto-server launcher for AI Proxy Core
Allows the HTML client to start/stop the server
"""
import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def start_server(api_key=None):
    """Start the AI Proxy Core server with the given API key"""
    if api_key:
        os.environ['GEMINI_API_KEY'] = api_key
    
    # Import and run the FastAPI app
    import uvicorn
    from main import app
    
    print(f"Starting server with API key: {api_key[:10]}..." if api_key else "Starting server...")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Proxy Core Auto-Server")
    parser.add_argument("--api-key", help="Gemini API key", default=os.environ.get("GEMINI_API_KEY"))
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Warning: No GEMINI_API_KEY provided. WebSocket connections will fail.")
    
    start_server(args.api_key)