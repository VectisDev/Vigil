#!/usr/bin/env python3
"""
Centinel Launcher — abre el navegador automáticamente.

El usuario hace doble clic (o ejecuta este script) y Centinel
se abre en su navegador sin necesidad de escribir ninguna URL.

Funciona como Jupyter Notebook: inicia el servidor en background
y abre el navegador al destino correcto.
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
MAX_WAIT_SECONDS = 20


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
        time.sleep(0.3)
    return False


def _start_server() -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault("CENTINEL_PORT", str(PORT))

    cmd = [
        sys.executable, "-m", "uvicorn",
        "centinel.api.main:app",
        "--host", HOST,
        "--port", str(PORT),
        "--log-level", "warning",
    ]

    return subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    print("Iniciando Centinel…")

    # Si el servidor ya está corriendo, no lo arranques de nuevo
    server_process = None
    if not _is_port_open(HOST, PORT):
        server_process = _start_server()

    print(f"Esperando servidor en :{PORT}…", end="", flush=True)
    if not _wait_for_server(HOST, PORT, MAX_WAIT_SECONDS):
        print("\nError: el servidor no respondió a tiempo.")
        if server_process:
            server_process.terminate()
        sys.exit(1)
    print(" listo.")

    # Primera vez (sin setup) → wizard; ya configurado → dashboard
    page = "/setup/" if not SETUP_MARKER.exists() else "/"
    url = f"http://{HOST}:{PORT}{page}"

    print(f"Abriendo Centinel en tu navegador…")
    webbrowser.open(url)

    # Mantener el proceso vivo si somos los dueños del servidor
    if server_process:
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\nCerrando Centinel…")
            server_process.terminate()


if __name__ == "__main__":
    main()
