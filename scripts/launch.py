#!/usr/bin/env python3
"""
Centinel Launcher — doble clic para abrir en el navegador.

Abre Centinel en tu navegador con un solo doble clic.
No se necesita abrir ninguna terminal.

Works like Jupyter Notebook: starts the server in background
and opens the browser to the correct page (setup wizard on
first run, dashboard on return).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("CENTINEL_PORT", "7474"))
HOST = "127.0.0.1"
SETUP_MARKER = REPO_ROOT / ".centinel-setup.json"
VENV_DIR = REPO_ROOT / ".venv"
MAX_WAIT_SECONDS = 30


# ── helpers ────────────────────────────────────────────────────────────────────

def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _wait_for_server(host: str, port: int, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_port_open(host, port):
            return True
        time.sleep(0.4)
    return False


def _run(*args: str, **kw) -> "subprocess.CompletedProcess[bytes]":
    return subprocess.run(list(args), check=True, **kw)


# ── dependency bootstrap ───────────────────────────────────────────────────────

def _venv_python() -> Path:
    """Path to the venv Python binary."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _ensure_deps() -> Path:
    """
    Make sure a virtualenv with all deps exists.
    Returns the path to the Python executable to use.

    - If we ARE already running inside a venv: trust it and return sys.executable.
    - If .venv/ exists and has the marker: return venv Python.
    - Otherwise: create .venv + pip-install, then re-exec with venv Python.
    """
    marker = VENV_DIR / ".centinel-ready"

    # Already inside a venv (e.g. developer, or second run after re-exec)
    if sys.prefix != sys.base_prefix:
        return Path(sys.executable)

    # Venv ready from a previous run
    if marker.exists() and _venv_python().exists():
        return _venv_python()

    print("Instalando dependencias por primera vez (puede tomar 1-2 min)…")
    print("Installing dependencies for the first time (may take 1-2 min)…")

    # Create venv
    if not VENV_DIR.exists():
        _run(sys.executable, "-m", "venv", str(VENV_DIR))

    vpy = _venv_python()

    # Upgrade pip silently
    _run(str(vpy), "-m", "pip", "install", "--quiet", "--upgrade", "pip")

    # Install production requirements
    req_file = REPO_ROOT / "requirements-prod.txt"
    if not req_file.exists():
        req_file = REPO_ROOT / "requirements.txt"

    _run(str(vpy), "-m", "pip", "install", "--quiet", "-r", str(req_file))

    # Install the package itself in editable mode so `vigil.*` is importable
    _run(str(vpy), "-m", "pip", "install", "--quiet", "-e", str(REPO_ROOT))

    marker.touch()
    print("Dependencias instaladas correctamente. / Dependencies installed OK.")
    return vpy


# ── server ─────────────────────────────────────────────────────────────────────

def _start_server(python: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault("CENTINEL_PORT", str(PORT))
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    cmd = [
        str(python), "-m", "uvicorn",
        "vigil.api.main:app",
        "--host", HOST,
        "--port", str(PORT),
        "--log-level", "warning",
    ]

    return subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Iniciando Centinel… / Starting Centinel…")

    # Bootstrap deps (no-op if already ready)
    try:
        python = _ensure_deps()
    except subprocess.CalledProcessError as exc:
        print(f"\nError instalando dependencias: {exc}")
        print("Asegúrate de tener Python ≥3.10 instalado y conexión a internet.")
        print("Make sure Python ≥3.10 is installed and you have internet access.")
        _pause_on_windows()
        sys.exit(1)

    # If we need to re-exec with venv Python, do it now
    if Path(sys.executable).resolve() != python.resolve():
        env = os.environ.copy()
        env.setdefault("CENTINEL_PORT", str(PORT))
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        os.execve(str(python), [str(python), str(Path(__file__).resolve())], env)
        # os.execve replaces the current process — nothing below runs

    # If the server is already running, don't start it again
    server_process = None
    if not _is_port_open(HOST, PORT):
        server_process = _start_server(Path(sys.executable))

    print(f"Esperando servidor… / Waiting for server on :{PORT}…", end="", flush=True)
    if not _wait_for_server(HOST, PORT, MAX_WAIT_SECONDS):
        print("\nError: el servidor no respondió a tiempo. / Server did not respond in time.")
        if server_process:
            server_process.terminate()
        _pause_on_windows()
        sys.exit(1)
    print(" listo / ready.")

    # First run → setup wizard; returning user → dashboard
    page = "/setup/" if not SETUP_MARKER.exists() else "/"
    url = f"http://{HOST}:{PORT}{page}"

    print(f"Abriendo Centinel en tu navegador… / Opening Centinel in your browser…")
    webbrowser.open(url)

    # Keep the process alive as long as we own the server
    if server_process:
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\nCerrando Centinel… / Closing Centinel…")
            server_process.terminate()


def _pause_on_windows() -> None:
    if sys.platform == "win32":
        input("\nPresiona Enter para cerrar… / Press Enter to close…")


if __name__ == "__main__":
    main()
