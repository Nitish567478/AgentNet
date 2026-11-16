"""
AgentNet: Application Launcher
Starts the FastAPI server hosting REST APIs and the Interactive Web Dashboard.
Automatically cleans up stale lingering processes on the port.
"""

import sys
import os
import subprocess
import uvicorn
from app.config import settings


def free_port(port: int):
    """Frees the port if a stale process is lingering on Windows."""
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            for line in out.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    if pid != str(os.getpid()):
                        print(f"[Launcher] Port {port} held by stale PID {pid}. Cleaning up...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        except Exception:
            pass


if __name__ == "__main__":
    import traceback
    import threading
    import time

    free_port(settings.APP_PORT)
    print("=" * 65)
    print("  Starting AgentNet: Social Network for AI Agents")
    print(f"  Web Dashboard:  http://{settings.APP_HOST}:{settings.APP_PORT}")
    print(f"  Interactive API: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print("=" * 65, flush=True)

    # Background heartbeat thread to keep connection alive and active
    def heartbeat():
        while True:
            time.sleep(25)
            print(f"[AgentNet Server] Active & Listening on http://{settings.APP_HOST}:{settings.APP_PORT}", flush=True)

    t = threading.Thread(target=heartbeat, daemon=True)
    t.start()

    try:
        uvicorn.run(
            "app.main:app",
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            reload=False,
            log_level="info"
        )
    except BaseException as e:
        print(f"[Launcher CAUGHT {type(e).__name__}] {e}", flush=True)
        traceback.print_exc()
        raise
