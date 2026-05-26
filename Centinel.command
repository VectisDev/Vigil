#!/usr/bin/env bash
# Centinel — doble clic en Finder para abrir / double-click in Finder to open
# macOS: chmod +x Centinel.command  (ya hecho / already done)

cd "$(dirname "$0")"

# ── Find Python 3.10+ ─────────────────────────────────────────────────────────
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        VER=$("$candidate" -c 'import sys; print(sys.version_info[:2] >= (3,10))' 2>/dev/null)
        if [ "$VER" = "True" ]; then
            PY="$candidate"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    osascript -e 'display dialog "Python 3.10 o superior no encontrado.\n\nDescárgalo desde:\nhttps://www.python.org/downloads/\n\nPython 3.10 or higher not found.\n\nDownload it from:\nhttps://www.python.org/downloads/" buttons {"Abrir python.org"} default button 1' >/dev/null 2>&1
    open "https://www.python.org/downloads/"
    exit 1
fi

# ── Launch ────────────────────────────────────────────────────────────────────
"$PY" scripts/launch.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Centinel encontró un error. / Centinel encountered an error."
    echo "Presiona Enter para cerrar. / Press Enter to close."
    read -r
fi
