#!/usr/bin/env bash
# Centinel — doble clic en el gestor de archivos / double-click in file manager
# Linux: chmod +x Centinel.sh  (ya hecho / already done)

cd "$(dirname "$(readlink -f "$0")")"

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
    # Try to show a GUI dialog if available
    MSG="Python 3.10 o superior no encontrado.\n\nInstálalo con:\n  sudo apt install python3  (Ubuntu/Debian)\n  sudo dnf install python3  (Fedora)\n\nPython 3.10 or higher not found.\nInstall it with the command above."
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --text="$MSG" 2>/dev/null
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$MSG" 2>/dev/null
    else
        echo -e "$MSG"
        echo ""
        echo "Presiona Enter para cerrar. / Press Enter to close."
        read -r
    fi
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
