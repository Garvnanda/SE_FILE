"""Render start command: migration, secret-based bootstrap, then one API worker."""

import os
import subprocess
import sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
if os.environ.get("ENVIRONMENT") != "production":
    raise SystemExit("Render startup requires ENVIRONMENT=production")
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
subprocess.run([sys.executable, "scripts/seed_production.py"], check=True)
os.execv(
    sys.executable,
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "0.0.0.0",
        "--port",
        os.environ.get("PORT", "10000"),
        "--workers",
        "1",
        "--no-proxy-headers",
    ],
)
