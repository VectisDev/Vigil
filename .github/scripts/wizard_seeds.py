#!/usr/bin/env python3
"""
Wizard step: generate seeds and write their SHA-256 hashes to web/access.json.

The plaintext seeds are written only to /tmp/centinel-seeds.txt (mode 0600).
This script does not print them. The Regenerate Admin Seeds workflow may
upload that file as an artifact kept for one day.

Helper for fork self-configuration. Environment variables:
  CENTINEL_COUNTRY  — country code (HN, GT, ...)
  REPO_OWNER        — GitHub username
  REPO_NAME         — repository name
  GITHUB_RUN_ID     — Actions run ID (for artifact URL in the seeds file)
"""
import hashlib, secrets, json, os, sys, base64
from datetime import datetime, timezone
from pathlib import Path

# The regenerate workflow uploads this exact path. Do not print the file.
SEEDS_PATH = Path("/tmp/centinel-seeds.txt")  # nosec B108 - artifact path, created mode 0600


def write_seeds_file(text: str) -> None:
    """Escribe el archivo de claves solo legible por su dueno (0600).

    English: write the key file readable by its owner only (0600). The mode is
    applied at creation, not afterwards, so there is no window in which the
    file exists with wider permissions.
    """
    SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(SEEDS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)


COUNTRY = os.environ.get("VIGIL_COUNTRY", os.environ.get("CENTINEL_COUNTRY", "HN"))
OWNER = os.environ.get("REPO_OWNER", "")
REPO = os.environ.get("REPO_NAME", "")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "")

access_path = Path("web/access.json")

# Don't regenerate if valid seeds already exist
if access_path.exists() and os.environ.get("FORCE_REGENERATE") != "true":
    try:
        existing = json.loads(access_path.read_text())
        if existing.get("seeds") and len(existing["seeds"]) >= 12:
            print("Seeds already exist — skipping generation.")
            write_seeds_file(
                "Seeds ya configurados en una ejecución anterior.\n"
                "Usa el panel OPS para regenerarlos si es necesario.\n"
            )
            sys.exit(0)
    except Exception:
        # Unreadable or missing seed state just means a first run: generate seeds below.
        pass


def generate_base64_seed(entropy_bytes=18):
    """Generate a base64-style 24-character seed with high entropy."""
    random_bytes = secrets.token_bytes(entropy_bytes)
    b64_encoded = base64.urlsafe_b64encode(random_bytes).decode("ascii")
    return b64_encoded[:24]


NUM_SEEDS = 12
seeds = [generate_base64_seed() for _ in range(NUM_SEEDS)]
hashes = [hashlib.sha256(s.encode()).hexdigest() for s in seeds]

access_path.parent.mkdir(parents=True, exist_ok=True)
access_path.write_text(
    json.dumps(
        {
            "version": 3,
            "method": "SHA-256",
            "seeds": hashes,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "country": COUNTRY,
        },
        indent=2,
    )
)
print(f"web/access.json written with {len(seeds)} seeds")

pages_url = f"https://{OWNER}.github.io/{REPO}/"
run_url = f"https://github.com/{OWNER}/{REPO}/actions/runs/{RUN_ID}"

lines = [
    "=" * 62,
    "  VIGIL — CLAVES DE ACCESO AL PANEL OPS",
    "=" * 62,
    f"  País:      {COUNTRY}",
    f"  Generado:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    f"  Panel OPS: {pages_url}ops/",
    "",
    "  CONFIDENCIAL — Guarda este archivo FUERA DE LINEA.",
    "    El sistema solo almacena los hashes SHA-256.",
    "    Si pierdes estas claves, regenera desde el panel OPS.",
    "    Este archivo solo existe en el runner y se destruye con el job.",
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
write_seeds_file("\n".join(lines) + "\n")
print("Key file written. This script does not print the keys.")
