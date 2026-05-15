"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/centinel/cli.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - main
  - bloque_main

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `src/centinel/cli.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - main
  - bloque_main

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Cli Module
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



import json
from typing import Optional

import typer

app = typer.Typer(help="Centinel Engine CLI")


@app.callback()
def main() -> None:
    """Interfaz de línea de comandos de Centinel.

    English: Centinel command line interface.
    """


@app.command()
def doctor(
    mode: Optional[str] = typer.Option(
        None,
        "--mode",
        help="Override CENTINEL_MODE for this check (maintenance|monitoring|election).",
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON instead of text."
    ),
) -> None:
    """Preflight self-audit. Exits non-zero if the active mode is BLOCKED.

    English: Verify the security posture the active CENTINEL_MODE
    promises is actually satisfied before running an election.
    """
    from .core.doctor import BLOCKED, format_report, run_doctor

    report = run_doctor(mode)
    if as_json:
        typer.echo(
            json.dumps(
                {
                    "profile": report.profile.as_dict(),
                    "overall": report.overall,
                    "election_ready": report.election_ready,
                    "checks": [
                        {
                            "name": c.name,
                            "status": c.status,
                            "detail": c.detail,
                            "remedy": c.remedy,
                        }
                        for c in report.checks
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        typer.echo(format_report(report))
    if report.overall == BLOCKED:
        raise typer.Exit(code=1)


@app.command()
def profile(
    mode: Optional[str] = typer.Option(
        None, "--mode", help="Override CENTINEL_MODE for this resolution."
    ),
) -> None:
    """Show the security posture derived from the active CENTINEL_MODE.

    English: Print which security switches the current mode implies,
    without mutating anything.
    """
    from .core.profiles import resolve_profile

    resolved = resolve_profile(mode)
    typer.echo(json.dumps(resolved.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
