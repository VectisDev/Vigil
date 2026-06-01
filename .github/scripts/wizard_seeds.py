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
import hashlib, secrets, json, os, sys
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
if access_path.exists():
    try:
        existing = json.loads(access_path.read_text())
        if existing.get("seeds") and len(existing["seeds"]) == 12:
            print("Seeds already exist — skipping generation.")
            Path("/tmp/centinel-seeds.txt").write_text(  # nosec B108 - ephemeral GitHub Actions runner; path used to pass output between steps
                "Seeds ya configurados en una ejecución anterior.\n"
                "Usa el panel OPS para regenerarlos si es necesario.\n"
            )
            sys.exit(0)
    except Exception:
        pass

ADJECTIVES = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
    "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey", "xray",
    "yankee", "zulu", "amber", "azure", "black", "blue", "cedar", "coral",
    "crimson", "cyan", "dusk", "ember", "frost", "gold", "green", "ivory",
]
NOUNS = [
    "anchor", "arrow", "badge", "bolt", "bridge", "canyon", "cloud", "comet",
    "crown", "crystal", "dawn", "eagle", "falcon", "flame", "forest", "glacier",
    "harbor", "hawk", "island", "jaguar", "keystone", "lance", "lantern", "marble",
    "meteor", "mirror", "moon", "mountain", "nova", "oak", "orbit", "pearl",
    "phoenix", "pine", "prism", "quartz", "raven", "reef", "ridge", "river",
    "rocket", "sage", "shadow", "shield", "signal", "silver", "solar", "spark",
    "spire", "star", "storm", "summit", "sword", "thorn", "tide", "tiger",
    "torch", "tower", "trail", "vault", "viper", "vista", "wave", "wolf",
]

LABELS = list("ABCDEFGHIJKL")
seeds = [
    f"{secrets.choice(ADJECTIVES)}-{secrets.choice(NOUNS)}-{secrets.randbelow(10000):04d}"
    for _ in range(12)
]
hashes = {
    f"S1-{LABELS[i]}": hashlib.pbkdf2_hmac("sha256", s.encode(), SALT.encode(), ITERS).hex()
    for i, s in enumerate(seeds)
}

access_path.parent.mkdir(parents=True, exist_ok=True)
access_path.write_text(json.dumps({
    "version":      1,
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
    "  CENTINEL — SEEDS DE ACCESO AL PANEL OPS",
    "=" * 62,
    f"  País:      {COUNTRY}",
    f"  Generado:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    f"  Panel OPS: {pages_url}ops/",
    "",
    "  ⚠ CONFIDENCIAL — Guarda este archivo FUERA DE LÍNEA.",
    "    El sistema solo almacena los hashes PBKDF2-SHA256 (600K iter).",
    "    Si pierdes estos seeds, regenera desde el panel OPS.",
    "    Este archivo EXPIRA en 24 horas (artifact de GitHub Actions).",
    "",
    "-" * 62,
    "  12 SEEDS DE ALTA ENTROPÍA:",
    "-" * 62,
    "",
]
for i, (label, s) in enumerate(zip([f"S1-{l}" for l in LABELS], seeds), 1):
    lines.append(f"  {label}:  {s}")
lines += [
    "",
    "=" * 62,
    f"  Panel público:     {pages_url}",
    f"  Panel OPS:         {pages_url}ops/",
    f"  Run de origen:     {run_url}",
    "=" * 62,
]
Path("/tmp/centinel-seeds.txt").write_text("\n".join(lines) + "\n")  # nosec B108 - ephemeral GitHub Actions runner; path used to pass output between steps
print("Seeds file written to /tmp/centinel-seeds.txt")
