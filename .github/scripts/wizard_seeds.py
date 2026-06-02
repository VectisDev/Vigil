#!/usr/bin/env python3
"""
Wizard step: generate seeds, write web/access.json, write plaintext seeds
to /tmp/centinel-seeds.txt for the GitHub Actions artifact.

Called by setup-wizard.yml. Environment variables:
  CENTINEL_COUNTRY  — country code (HN, GT, ...)
  REPO_OWNER        — GitHub username
  REPO_NAME         — repository name
  GITHUB_RUN_ID     — Actions run ID (for artifact URL in the seeds file)
"""
import hashlib, secrets, json, os, sys, base64
from datetime import datetime, timezone
from pathlib import Path

SALT    = "centinel-admin-salt-v1"
ITERS   = 600_000
COUNTRY = os.environ.get("CENTINEL_COUNTRY", "HN")
OWNER   = os.environ.get("REPO_OWNER", "")
REPO    = os.environ.get("REPO_NAME", "")
RUN_ID  = os.environ.get("GITHUB_RUN_ID", "")

access_path = Path("web/access.json")

# Don't regenerate if valid seeds already exist
if access_path.exists() and os.environ.get("FORCE_REGENERATE") != "true":
    try:
        existing = json.loads(access_path.read_text())
        if existing.get("seeds") and len(existing["seeds"]) >= 12:
            print("Seeds already exist — skipping generation.")
            Path("/tmp/centinel-seeds.txt").write_text(  # nosec B108 - ephemeral GitHub Actions runner; path used to pass output between steps
                "Seeds ya configurados en una ejecución anterior.\n"
                "Usa el panel OPS para regenerarlos si es necesario.\n"
            )
            sys.exit(0)
    except Exception:
        pass

def generate_base64_seed(entropy_bytes=18):
    """Generate a base64-style 24-character seed with high entropy."""
    random_bytes = secrets.token_bytes(entropy_bytes)
    b64_encoded = base64.urlsafe_b64encode(random_bytes).decode('ascii')
    return b64_encoded[:24]

NUM_SEEDS = 12
seeds = [generate_base64_seed() for _ in range(NUM_SEEDS)]
hashes = [
    hashlib.pbkdf2_hmac("sha256", s.encode(), SALT.encode(), ITERS).hex()
    for s in seeds
]

access_path.parent.mkdir(parents=True, exist_ok=True)
access_path.write_text(json.dumps({
    "version":      2,
    "algo":         "PBKDF2-SHA256",
    "iterations":   ITERS,
    "salt":         SALT,
    "seeds":        hashes,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "country":      COUNTRY,
}, indent=2))
print(f"web/access.json written with {len(seeds)} seeds")

pages_url = f"https://{OWNER}.github.io/{REPO}/"
run_url   = f"https://github.com/{OWNER}/{REPO}/actions/runs/{RUN_ID}"

lines = [
    "=" * 62,
    "  CENTINEL — CLAVES DE ACCESO AL PANEL OPS",
    "=" * 62,
    f"  País:      {COUNTRY}",
    f"  Generado:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    f"  Panel OPS: {pages_url}ops/",
    "",
    "  CONFIDENCIAL — Guarda este archivo FUERA DE LINEA.",
    "    El sistema solo almacena los hashes PBKDF2-SHA256 (600K iter).",
    "    Si pierdes estas claves, regenera desde el panel OPS.",
    "    Este archivo EXPIRA en 24 horas (artifact de GitHub Actions).",
    "",
    "-" * 62,
    f"  {NUM_SEEDS} CLAVES DE ACCESO:",
    "-" * 62,
    "",
]
for i, s in enumerate(seeds, 1):
    lines.append(f"  Clave {i:2d}:  {s}")
lines += [
    "",
    "=" * 62,
    f"  Panel publico:     {pages_url}",
    f"  Panel OPS:         {pages_url}ops/",
    f"  Run de origen:     {run_url}",
    "=" * 62,
]
Path("/tmp/centinel-seeds.txt").write_text("\n".join(lines) + "\n")  # nosec B108 - ephemeral GitHub Actions runner; path used to pass output between steps
print("Seeds file written to /tmp/centinel-seeds.txt")
