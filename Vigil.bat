@echo off
title Vigil — Auditoría Electoral
cd /d "%~dp0"

REM ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python no encontrado / Python not found
    echo.
    echo  Por favor instala Python 3.11 o superior desde:
    echo  Please install Python 3.11 or higher from:
    echo.
    echo    https://www.python.org/downloads/
    echo.
    echo  Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM ── Launch ────────────────────────────────────────────────────────────────
python scripts\launch.py
if %errorlevel% neq 0 (
    echo.
    echo  Vigil encontro un error. Revisa el mensaje de arriba.
    echo  Vigil encountered an error. Check the message above.
    echo.
    pause
)
