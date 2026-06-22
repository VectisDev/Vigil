#!/usr/bin/env bash
# One-command bootstrap: dependencies -> preflight -> (optional) serve.
#
# Collapses the only remaining friction step ("install the deps") into a
# single command that ends in a plain-language GO / NO-GO verdict. A local
# election observer with no Python background runs ONE line and learns,
# before election day, whether the deployment is safe to run.
#
# Usage:
#   ./scripts/bootstrap.sh                 # install + preflight only
#   ./scripts/bootstrap.sh --serve         # also start the public API
#   CENTINEL_MODE=election ./scripts/bootstrap.sh --serve
#
# Exit codes: 0 ready (or serving), 1 preflight BLOCKED, 2 setup failure.
# Non-destructive: never deletes, never overwrites config, never forces.
#
# Bilingüe: arranque de un solo comando. Instala dependencias, corre la
# autoauditoría previa y (opcional) levanta la API pública. Termina con un
# veredicto claro GO / NO-GO para un observador sin conocimientos de Python.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVE=0
for arg in "$@"; do
  case "$arg" in
    --serve) SERVE=1 ;;
    -h|--help)
      sed -n '2,/^set -uo/{/^set -uo/!s/^# \{0,1\}//p}' "$0"
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s (use --help)\n' "$arg" >&2
      exit 2
      ;;
  esac
done

CENTINEL_MODE="${CENTINEL_MODE:-maintenance}"
export CENTINEL_MODE
HOST="${CENTINEL_HOST:-0.0.0.0}"
PORT="${CENTINEL_PORT:-8000}"

print_step() { printf '\n=== %s ===\n' "$1"; }
print_ok()   { printf '  [OK]    %s\n' "$1"; }
print_warn() { printf '  [WARN]  %s\n' "$1"; }
print_fail() { printf '  [FAIL]  %s\n' "$1"; }

# --- 1. Python version gate (pyproject requires >=3.10) -------------------
print_step "Python"
if ! command -v python3 >/dev/null 2>&1; then
  print_fail "python3 not found. Install Python >=3.10 first."
  exit 2
fi
PYV="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,10) else 1)'; then
  print_fail "Python $PYV detected; Centinel needs >=3.10."
  exit 2
fi
print_ok "Python $PYV"

# --- 2. Dependencies: prefer Poetry, fall back to pip --------------------
print_step "Dependencies / Dependencias"
RUN_PREFIX=()
if command -v poetry >/dev/null 2>&1; then
  print_ok "Poetry found — installing (main deps only)"
  if poetry install --only main --no-interaction --no-ansi; then
    RUN_PREFIX=(poetry run)
  else
    print_fail "poetry install failed. Re-run after fixing the error above."
    exit 2
  fi
else
  print_warn "Poetry not found — using pip into a local virtualenv"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv || { print_fail "venv creation failed"; exit 2; }
  fi
  # shellcheck disable=SC1091
  . .venv/bin/activate
  REQ="requirements-prod.txt"
  [ -f "$REQ" ] || REQ="requirements.txt"
  if ! python3 -m pip install --quiet --upgrade pip; then
    print_fail "pip self-upgrade failed"; exit 2
  fi
  if python3 -m pip install --quiet -r "$REQ"; then
    print_ok "Installed from $REQ into .venv"
  else
    print_fail "pip install -r $REQ failed."
    exit 2
  fi
fi

# Ensure the package is importable whether installed or run from source.
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

# --- 3. Preflight self-audit (the GO / NO-GO gate) ----------------------
print_step "Preflight / Autoauditoría (centinel doctor)"
printf '  mode: %s\n' "$CENTINEL_MODE"
set +e
"${RUN_PREFIX[@]}" python3 -m centinel.cli doctor --mode "$CENTINEL_MODE"
DOCTOR_RC=$?
set -e 2>/dev/null || true

if [ "$DOCTOR_RC" -eq 1 ]; then
  print_fail "Preflight BLOCKED. Fix the [STOP] items above before running"
  print_fail "an election. Server NOT started. / Servidor NO iniciado."
  exit 1
elif [ "$DOCTOR_RC" -ne 0 ]; then
  print_fail "doctor exited with code $DOCTOR_RC (unexpected). Aborting."
  exit 2
fi
print_ok "Preflight passed — deployment is safe to run."

# --- 4. Optional: start the public API ----------------------------------
if [ "$SERVE" -eq 0 ]; then
  printf '\nReady. Start the API with:\n'
  printf '  ./scripts/bootstrap.sh --serve\n'
  printf 'Listo. Levanta la API con el comando de arriba.\n'
  exit 0
fi

print_step "Serving / Sirviendo"
printf '  http://%s:%s  (Ctrl-C to stop / para detener)\n' "$HOST" "$PORT"
exec "${RUN_PREFIX[@]}" python3 -m uvicorn centinel.api.main:app \
  --host "$HOST" --port "$PORT"
