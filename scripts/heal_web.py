#!/usr/bin/env python3
"""
Healer autónomo para la web de GitHub Pages.

Verifica que los archivos críticos de web/ estén presentes y bien formados.
Si falta alguno o está corrupto, lo restaura desde la última versión en git.
Se puede invocar manualmente o mediante el workflow heal-web.yml.

Uso:
    python scripts/heal_web.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

# Lo que el sitio publicado carga de verdad, y nada mas.
#
# Esta lista vigilaba cinco archivos que el panel v4 dejo de cargar
# —`ops.css`, `ops-panel.js`, `ops-monitor.js`, `ops-command.js` y
# `vigil-log.js`— y NO vigilaba ninguno de los que si carga. El healer
# protegia lo muerto y dejaba lo vivo sin red: si `ops-v4.js` hubiera
# desaparecido, nadie se habria enterado hasta abrir la pagina.
#
# Quien anada un archivo al panel tiene que anadirlo aqui tambien;
# `tests/test_heal_web_watches_what_is_served.py` falla si no lo hace.
#
# English: what the published site actually loads, and nothing else. This
# list guarded five files the v4 panel stopped loading and guarded none of
# the ones it does load -- the healer protected the dead and left the live
# without a net.
CRITICAL_FILES = [
    "web/index.html",
    "web/access.json",
    "web/config.js",
    "web/replay/index.html",
    "web/verifier/index.html",
    "web/lab/index.html",
    "web/monitor/index.html",
    "web/shared/vigil-theme.js",
    "web/shared/vigil-theme.css",
    "web/shared/brand-header.css",
    "web/shared/tokens.css",
    "web/shared/vigil-nav.css",
    "web/ops/index.html",
    "web/ops/ops-v4.css",
    "web/ops/js/ops-core.js",
    "web/ops/js/ops-tabs.js",
    "web/ops/js/ops-v4.js",
    "web/ops/data/s3_mirror_status.json",
    ".github/workflows/pages.yml",
]

JSON_FILES = [
    "web/access.json",
]


def _git_restore(path: str) -> bool:
    """Restore a file from HEAD."""
    try:
        subprocess.run(
            ["git", "checkout", "HEAD", "--", path],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _check_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except (json.JSONDecodeError, OSError):
        return False


def run(dry_run: bool = False) -> int:
    healed = 0
    errors = 0

    print(f"\n{BOLD}VIGIL Web Healer{RESET}")
    print(f"{'─'*50}")

    for rel in CRITICAL_FILES:
        p = REPO_ROOT / rel
        ok = True
        reason = ""

        if not p.exists():
            ok = False
            reason = "MISSING"
        elif rel in JSON_FILES and not _check_json(p):
            ok = False
            reason = "INVALID JSON"

        if ok:
            print(f"  {GREEN}✓{RESET}  {rel}")
            continue

        print(f"  {RED}✗{RESET}  {rel}  [{reason}]")
        if not dry_run:
            if _git_restore(rel):
                print(f"       {CYAN}→ restored from HEAD{RESET}")
                healed += 1
            else:
                print(f"       {RED}→ RESTORE FAILED{RESET}")
                errors += 1
        else:
            print(f"       {CYAN}→ would restore (dry-run){RESET}")

    print(f"\n{'─'*50}")
    if dry_run:
        print("  Dry-run mode — no changes made.")
    else:
        print(f"  Healed: {healed}  |  Errors: {errors}")

    return 0 if errors == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="VIGIL web healer")
    parser.add_argument("--dry-run", action="store_true", help="Only report, don't fix")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
