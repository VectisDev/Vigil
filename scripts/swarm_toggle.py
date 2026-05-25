"""
Toggle Centinel swarm mode without editing .env or restarting.

ES: Conecta o desconecta el nodo del enjambre con un solo comando.
    Llama a los endpoints existentes del API y persiste CENTINEL_AUTOCONNECT
    en centinel_engine/.env para que el ajuste sobreviva reinicios.

EN: Connect or disconnect the node from the swarm with a single command.
    Calls the existing API endpoints and persists CENTINEL_AUTOCONNECT in
    centinel_engine/.env so the setting survives restarts.

Usage:
    python scripts/swarm_toggle.py join                     # joins local swarm
    python scripts/swarm_toggle.py leave                    # leaves local swarm
    python scripts/swarm_toggle.py status                   # show swarm status
    python scripts/swarm_toggle.py join --url http://host:8080 --my-url https://public-ip:8080
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests

_DEFAULT_API = "http://localhost:8080"
_ENV_PATH = Path("centinel_engine") / ".env"


def _update_env(key: str, value: str) -> None:
    """ES: Actualiza o añade KEY=VALUE en centinel_engine/.env preservando el resto.
    EN: Updates or appends KEY=VALUE in centinel_engine/.env preserving other entries."""
    if not _ENV_PATH.exists():
        _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ENV_PATH.write_text(f"{key}={value}\n", encoding="utf-8")
        return

    text = _ENV_PATH.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)
    if pattern.search(text):
        text = pattern.sub(f"{key}={value}", text)
    else:
        text = text.rstrip("\n") + f"\n{key}={value}\n"
    _ENV_PATH.write_text(text, encoding="utf-8")


def join(api_url: str = _DEFAULT_API, my_url: str | None = None) -> None:
    """ES: Une el nodo al enjambre y persiste CENTINEL_AUTOCONNECT=1.
    EN: Joins the swarm and persists CENTINEL_AUTOCONNECT=1."""
    body: dict = {}
    if my_url:
        body["my_url"] = my_url
    try:
        resp = requests.post(f"{api_url}/api/swarm/connect", json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: No se puede conectar a {api_url} — ¿está el servidor corriendo?")
        print(f"ERROR: Cannot connect to {api_url} — is the server running?")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    _update_env("CENTINEL_AUTOCONNECT", "1")
    print(f"Joined swarm: node_id={data.get('node_id')} country={data.get('country_code')} status={data.get('status')}")
    print(f"Persisted CENTINEL_AUTOCONNECT=1 in {_ENV_PATH}")


def leave(api_url: str = _DEFAULT_API) -> None:
    """ES: Desconecta el nodo del enjambre y persiste CENTINEL_AUTOCONNECT=0.
    EN: Disconnects from the swarm and persists CENTINEL_AUTOCONNECT=0."""
    try:
        resp = requests.post(f"{api_url}/api/swarm/disconnect", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: No se puede conectar a {api_url} — ¿está el servidor corriendo?")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    _update_env("CENTINEL_AUTOCONNECT", "0")
    print(f"Left swarm: node_id={data.get('node_id')} status={data.get('status')}")
    print(f"Persisted CENTINEL_AUTOCONNECT=0 in {_ENV_PATH}")


def status(api_url: str = _DEFAULT_API) -> None:
    """ES: Muestra el estado actual del enjambre. EN: Shows current swarm state."""
    try:
        resp = requests.get(f"{api_url}/api/swarm/status", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: No se puede conectar a {api_url}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Toggle Centinel swarm mode (join/leave/status)",
    )
    parser.add_argument("action", choices=["join", "leave", "status"])
    parser.add_argument(
        "--url",
        default=_DEFAULT_API,
        help=f"API server URL (default: {_DEFAULT_API})",
    )
    parser.add_argument(
        "--my-url",
        default=None,
        dest="my_url",
        help="Public URL of this node (needed to receive incoming gossip)",
    )
    args = parser.parse_args()

    if args.action == "join":
        join(args.url, args.my_url)
    elif args.action == "leave":
        leave(args.url)
    else:
        status(args.url)
