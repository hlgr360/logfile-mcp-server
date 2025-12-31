#!/usr/bin/env python3
"""
AI: Simple startup script for the web interface.

Creates a FastAPI app with default settings for development/demo purposes.
"""

import os
from pathlib import Path

from app.config import Settings
from app.web.routes import create_web_app

def create_demo_app():
    """AI: Create web app with demo settings."""
    # Use sample directories for demo
    base_dir = Path(__file__).parent
    
    settings = Settings(
        nexus_dir=str(base_dir / "sample_logs" / "nexus"),
        nginx_dir=str(base_dir / "sample_logs" / "nginx"),
        db_name="demo.db",
        nexus_pattern="*.log",
        nginx_pattern="*.log",
        web_port=8000,
        mcp_port=8001,
        enable_mcp_server=False
    )
    
    return create_web_app(settings)

# For uvicorn
app = create_demo_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
