#!/usr/bin/env python3 
"""
ListSync Web UI API Server Startup Script
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import psutil
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "api_requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_listsync_data():
    """Check if ListSync data directory exists"""
    data_dir = Path("data")
    db_file = data_dir / "list_sync.db"
    
    if not data_dir.exists():
        print("❌ Data directory not found. Please run ListSync first to create the database.")
        return False
    
    if not db_file.exists():
        print("❌ ListSync database not found. Please run ListSync first to create the database.")
        return False
    
    print(f"✅ Found ListSync database: {db_file} ({db_file.stat().st_size} bytes)")
    return True

def check_listsync_process():
    """Check if ListSync is running"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    if ('list_sync' in cmdline_str or 'listsync' in cmdline_str) and 'python' in cmdline_str:
                        if 'api_server.py' not in cmdline_str:
                            print(f"✅ Found ListSync process: PID {proc.info['pid']}")
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print("⚠️  ListSync process not found. The API will work but sync status may be inaccurate.")
        return True  # Don't block API startup
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return True  # Don't block API startup

def main():
    print("🚀 Starting ListSync Web UI API Server...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check ListSync data
    if not check_listsync_data():
        sys.exit(1)
    
    # Check ListSync process (warning only)
    check_listsync_process()
    
    print("\n📊 Starting API server...")
    print("🔗 API documentation: http://localhost:4222/docs")
    print("🔗 Health check: http://localhost:4222/api/system/health")
    print("🔗 Dashboard: http://localhost:3222 (when Next.js is running)")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the API server
    try:
        import uvicorn
        # Disable reload in Docker/production (causes issues with file watching)
        is_docker = os.environ.get("RUNNING_IN_DOCKER", "false").lower() == "true"
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=4222,
            reload=not is_docker,  # Only reload in development, not in Docker
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 