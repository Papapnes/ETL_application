"""Start this checkout on an available local port, never reuse a stale server."""

import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def available_port(preferred=8501):
    for port in (preferred, 0):
        with socket.socket() as listener:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                listener.bind(("127.0.0.1", port))
                return listener.getsockname()[1]
            except OSError:
                if port == 0:
                    raise


def command(port):
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ROOT / "app.py"),
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--browser.serverAddress=127.0.0.1",
        f"--browser.serverPort={port}",
        "--server.headless=false",
        "--server.runOnSave=true",
    ]


def main():
    # Local-only launcher: cloud starts app.py directly and remains fail-closed.
    if not os.environ.get("DATAFLOW_DATABASE_URL") and not (ROOT / ".streamlit" / "secrets.toml").exists():
        os.environ.setdefault("DATAFLOW_DB_BACKEND", "sqlite")
    port = available_port()
    print(f"Application : {ROOT}", flush=True)
    if port != 8501:
        print("Le port habituel est occupe. Ouverture d'une nouvelle instance a jour.", flush=True)
    print(f"Adresse de cette instance : http://127.0.0.1:{port}", flush=True)
    print("Gardez cette fenetre ouverte. Ctrl+C pour arreter.", flush=True)
    try:
        return subprocess.call(command(port), cwd=ROOT)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
