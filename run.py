"""Start Kaaval with one command:   python run.py

Starts the API (port 8000) and the web app (port 5173) together, opens the
chat in your browser, and stops both when you press Ctrl+C.
Run it from the project root with the virtual environment active.
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
WINDOWS = os.name == "nt"


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if WINDOWS:  # also stop the child processes npm starts
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.terminate()


def main() -> int:
    if not (ROOT / ".env").exists():
        (ROOT / ".env").write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example (mock mode, no keys needed).")

    if not (FRONTEND / "node_modules").exists():
        print("First run: installing frontend packages (about a minute)...")
        subprocess.run("npm install", cwd=FRONTEND, shell=True, check=True)

    print("Starting Kaaval...  (press Ctrl+C to stop)")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"], cwd=ROOT
    )
    frontend = subprocess.Popen("npm run dev", cwd=FRONTEND, shell=True)

    time.sleep(4)
    print("\n  Customer chat:    http://localhost:5173")
    print("  Owner dashboard:  http://localhost:5173/#/owner\n")
    webbrowser.open("http://localhost:5173")

    try:
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
        print("One of the servers stopped; shutting down the other.")
    except KeyboardInterrupt:
        print("\nStopping Kaaval...")
    finally:
        stop(backend)
        stop(frontend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
