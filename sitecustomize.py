"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `sitecustomize.py`.
Este módulo forma parte de VIGIL y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - (sin componentes de nivel de módulo / no top-level components)

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `sitecustomize.py`.
This module is part of VIGIL and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - (sin componentes de nivel de módulo / no top-level components)

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Sitecustomize Module
# AUTO-DOC-INDEX
#
# ES: Índice rápido
#   1) Propósito del módulo
#   2) Componentes principales
#   3) Puntos de extensión
#
# EN: Quick index
#   1) Module purpose
#   2) Main components
#   3) Extension points
#
# Secciones / Sections:
#   - Configuración / Configuration
#   - Lógica principal / Core logic
#   - Integraciones / Integrations


from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"
PARENT_ROOT = REPO_ROOT.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
# No se elimina REPO_ROOT: pyproject.toml ya declara vigil_engine, scripts y
# command_center como paquetes, asi que quitarlo solo rompia los entrypoints de
# produccion mientras conftest.py lo reinsertaba para las pruebas.
# REPO_ROOT is no longer removed: pyproject.toml now declares vigil_engine,
# scripts and command_center as packages, so removing it only broke the
# production entrypoints while conftest.py re-inserted it for tests.
if str(PARENT_ROOT) in sys.path:
    sys.path.remove(str(PARENT_ROOT))
