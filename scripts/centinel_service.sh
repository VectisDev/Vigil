#!/usr/bin/env bash
# Deprecated name kept for existing automation: VIGIL was formerly CENTINEL.
exec "$(dirname "$(readlink -f "$0")")/vigil_service.sh" "$@"
