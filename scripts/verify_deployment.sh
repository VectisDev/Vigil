#!/usr/bin/env bash
# Verify a running Centinel demo deployment in under 60 seconds.
#
# Probes the public audit surface — no authentication required — and confirms
# the system is reachable, the hash chain is internally consistent, and the
# timeline endpoint responds. Exit 0 on success, 1 on any failure.
#
# Usage:
#   ./scripts/verify_deployment.sh                # localhost:8000
#   BASE_URL=https://centinel.example.org ./scripts/verify_deployment.sh
#
# Bilingüe: verifica un despliegue demo en menos de 60s consultando endpoints
# publicos sin autenticacion.

set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-90}"
CURL_OPTS=(--silent --show-error --max-time 10)

pass=0
fail=0

print_step() { printf '\n=== %s ===\n' "$1"; }
print_ok()   { printf '  [OK]    %s\n' "$1"; pass=$((pass + 1)); }
print_fail() { printf '  [FAIL]  %s\n' "$1"; fail=$((fail + 1)); }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Required command missing: %s\n' "$1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

print_step "Waiting for $BASE_URL to become reachable"
elapsed=0
while [ "$elapsed" -lt "$MAX_WAIT_SECONDS" ]; do
  if curl "${CURL_OPTS[@]}" --fail "$BASE_URL/audit/health" >/dev/null 2>&1; then
    print_ok "Server reachable after ${elapsed}s"
    break
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done
if [ "$elapsed" -ge "$MAX_WAIT_SECONDS" ]; then
  print_fail "Server unreachable after ${MAX_WAIT_SECONDS}s — aborting"
  exit 1
fi

print_step "Probing /audit/health"
HEALTH_BODY=$(curl "${CURL_OPTS[@]}" "$BASE_URL/audit/health" || true)
if [ -z "$HEALTH_BODY" ]; then
  print_fail "/audit/health returned empty body"
else
  STATUS=$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read()).get("status",""))' <<<"$HEALTH_BODY" 2>/dev/null || echo "")
  if [ "$STATUS" = "ok" ]; then
    print_ok "/audit/health status=ok"
  else
    print_fail "/audit/health unexpected status: $STATUS"
  fi
  NOAUTH=$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read()).get("no_auth_required",""))' <<<"$HEALTH_BODY" 2>/dev/null || echo "")
  if [ "$NOAUTH" = "True" ]; then
    print_ok "/audit/health advertises no_auth_required=true"
  else
    print_fail "/audit/health missing no_auth_required flag"
  fi
fi

print_step "Probing /audit/chain/verify"
CHAIN_BODY=$(curl "${CURL_OPTS[@]}" "$BASE_URL/audit/chain/verify" || true)
if [ -z "$CHAIN_BODY" ]; then
  print_fail "/audit/chain/verify returned empty body"
else
  VALID=$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read()).get("valid",""))' <<<"$CHAIN_BODY" 2>/dev/null || echo "")
  COUNT=$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read()).get("count",""))' <<<"$CHAIN_BODY" 2>/dev/null || echo "")
  if [ "$VALID" = "True" ]; then
    print_ok "/audit/chain/verify valid=true count=$COUNT"
  else
    print_fail "/audit/chain/verify invalid — count=$COUNT body=$CHAIN_BODY"
  fi
fi

print_step "Probing /audit/timeline"
TL_BODY=$(curl "${CURL_OPTS[@]}" "$BASE_URL/audit/timeline?limit=5" || true)
if [ -z "$TL_BODY" ]; then
  print_fail "/audit/timeline returned empty body"
else
  TOTAL=$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read()).get("total",""))' <<<"$TL_BODY" 2>/dev/null || echo "")
  if [ -n "$TOTAL" ]; then
    print_ok "/audit/timeline reachable — total=$TOTAL"
  else
    print_fail "/audit/timeline malformed response"
  fi
fi

print_step "Summary"
printf 'Checks passed: %d\n' "$pass"
printf 'Checks failed: %d\n' "$fail"
if [ "$fail" -gt 0 ]; then
  printf '\nDeployment verification FAILED.\n'
  exit 1
fi
printf '\nCentinel deployment healthy. Ready for audit verification.\n'
printf 'API docs:  %s/docs\n' "$BASE_URL"
printf 'Audit:     %s/audit/health\n' "$BASE_URL"
exit 0
