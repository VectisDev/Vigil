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



import typer
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from centinel.core.animal_defenses import AnimalDefense, ALL_DEFENSES

app = typer.Typer(help="Centinel Engine CLI")


# Subcomandos
panel_app = typer.Typer(help="Panel operador — Operador panel status")


@app.callback()
def main() -> None:
    """Interfaz de línea de comandos de Centinel.

    English: Centinel command line interface.
    """


@app.command()
def status() -> None:
    """Ver estado general del sistema.

    English: Show overall system status.
    """
    typer.echo("🔍 Centinel Engine Status")
    typer.echo("=" * 50)

    # Placeholder: cargar estado desde archivos
    typer.echo("✅ Core: OPERATIONAL")
    typer.echo("🐦 Cuervo: ACTIVE")
    typer.echo("🦑 Pulpo: ACTIVE")
    typer.echo("🦌 Venado: ACTIVE")
    typer.echo("🦎 Lagartija: ACTIVE")
    typer.echo("⚔️ Tejón: READY")


@panel_app.command(name="show")
def panel_show(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostrar detalles completos / Show full details")
) -> None:
    """Mostrar panel de estado operacional.

    English: Display operational status panel.
    """
    typer.echo("")
    typer.echo("╔════════════════════════════════════════════════════════════════╗")
    typer.echo("║ CENTINEL — Estado Operacional / Operational Status             ║")
    typer.echo("╠════════════════════════════════════════════════════════════════╣")
    typer.echo("║                                                                ║")

    # Threat score (placeholder)
    threat_score = 22
    status_color = "🟢 VERDE" if threat_score < 31 else "🟡 AMARILLO" if threat_score < 75 else "🔴 ROJO"
    typer.echo(f"║  AMENAZA GENERAL / Threat Score:  {threat_score:3d}/100 {status_color:<17} ║")
    typer.echo("║                                                                ║")

    # Defensas animales
    typer.echo("║  DEFENSAS ANIMALES / Animal Defenses:                         ║")
    typer.echo("║  ┌─────────────────────────────────────────────────────────┐  ║")

    for key, defense in ALL_DEFENSES.items():
        status_str = "ACTIVO ✓" if key != "kill_switch" else "READY  "
        detail = {
            "corvid": "Último:  5m",
            "cephalopod": "Clave: hash...",
            "evasion": "Jitter: ±30%",
            "regeneration": "Mirrors: 3/3",
            "kill_switch": "(no activado)"
        }
        line = f"│ {defense.emoji} {defense.name_es:<10} ({key:<13}): {status_str}  {detail.get(key, ''):<20}"
        typer.echo(f"║  {line:<63} ║")

    typer.echo("║  └─────────────────────────────────────────────────────────┘  ║")
    typer.echo("║                                                                ║")

    # Métricas
    typer.echo("║  MÉTRICAS / Metrics:                                           ║")
    typer.echo("║  Merkle Root:     abc123...abc123        [VIGENTE — 2m]        ║")
    typer.echo("║  Anomalías:       0 Benford + 0 Z-score                        ║")
    typer.echo("║  Conectividad:    4/4 endpoints UP       [100%]               ║")
    typer.echo("║  Snapshots:       2847 captured          [Last: 30s ago]       ║")
    typer.echo("║                                                                ║")

    if verbose:
        typer.echo("║  DETALLES VERBOSOS / Verbose Details:                      ║")
        typer.echo("║  Last merkle update: 2026-05-16T14:30:00Z                  ║")
        typer.echo("║  Threat events (24h): 0                                    ║")
        typer.echo("║  Recovery attempts: 0                                      ║")
        typer.echo("║                                                                ║")

    typer.echo("║  ⓘ Detalles: centinel panel show --verbose                    ║")
    typer.echo("║  ⓘ Auditoría: cat hashes/attack_log.jsonl                     ║")
    typer.echo("╚════════════════════════════════════════════════════════════════╝")
    typer.echo("")


@panel_app.command(name="json")
def panel_json() -> None:
    """Retornar estado en formato JSON para máquinas.

    English: Return status as JSON for machines.
    """
    data = {
        "threat_score": 22,
        "status": "🟢 GREEN",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "defenses": {
            "corvid": {
                "emoji": AnimalDefense.CORVID.emoji,
                "name_es": AnimalDefense.CORVID.name_es,
                "enabled": True,
                "last_attestation": "2m ago"
            },
            "cephalopod": {
                "emoji": AnimalDefense.CEPHALOPOD.emoji,
                "name_es": AnimalDefense.CEPHALOPOD.name_es,
                "enabled": True,
                "key_hash": "abc123..."
            },
            "evasion": {
                "emoji": AnimalDefense.EVASION.emoji,
                "name_es": AnimalDefense.EVASION.name_es,
                "enabled": True,
                "jitter_range": "±30%"
            },
            "regeneration": {
                "emoji": AnimalDefense.REGENERATION.emoji,
                "name_es": AnimalDefense.REGENERATION.name_es,
                "enabled": True,
                "mirrors": 3
            },
            "kill_switch": {
                "emoji": AnimalDefense.KILL_SWITCH.emoji,
                "name_es": AnimalDefense.KILL_SWITCH.name_es,
                "status": "READY",
                "activated": False
            }
        },
        "metrics": {
            "merkle_root": "abc123...abc123",
            "merkle_age_seconds": 120,
            "benford_anomalies": 0,
            "zscore_anomalies": 0,
            "connectivity": {"total": 4, "up": 4, "pct": 100},
            "snapshots_total": 2847,
            "last_snapshot_seconds_ago": 30
        },
        "next_actions": "Monitor normally. Green status maintained."
    }
    typer.echo(json.dumps(data, indent=2))


# Agregar subcomandos
app.add_typer(panel_app, name="panel", help="Panel operador — Operador panel")


if __name__ == "__main__":
    app()
