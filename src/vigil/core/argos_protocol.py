"""
PROTOCOLO ARGOS — CINCO CAPAS DE DEFENSA DEL VIGIL
(ARGOS PROTOCOL — FIVE DEFENSE LAYERS OF VIGIL)

Sistema de protección multi-capa del Protocolo ARGOS.
(Multi-layer protection system of the ARGOS Protocol.)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class ArgosLayer(Enum):
    """
    Capas del Protocolo ARGOS numeradas y localizadas.
    (Numbered and localized ARGOS Protocol layers.)
    """

    # 🐦 Cuervo: Memoria distribuida de testimonios
    CORVID = (
        "🐦",
        "Cuervo",
        "Memoria de Cuervo",
        "Gossip distribuido: testigos confirman hechos entre sí",
    )

    # 🦑 Pulpo: Cifrado de tránsito
    CEPHALOPOD = (
        "🦑",
        "Pulpo",
        "Tinta de Pulpo",
        "Cifrado ChaCha20Poly1305: oculta tráfico entre testigos",
    )

    # Aqui estaba la capa «Venado (Evasion)»: jitter y capturas senuelo.
    # Nunca existio en el codigo y el panel la reportaba como ACTIVA. VIGIL
    # audita identificandose y no publica capturas falsas: una sola, puesta a
    # proposito, desacreditaria a todas las demas. Ver `docs/NO-EVASION.md`.
    # English: the «Venado (Evasion)» layer -- jitter and decoy snapshots --
    # lived here. It never existed in code and the panel reported it ACTIVE.

    # 🦎 Lagartija: Auto-regeneración
    REGENERATION = (
        "🦎",
        "Lagartija",
        "Regeneración de Lagartija",
        "Sync nightly con mirrors: detección + restauración de compromiso",
    )

    # ⚔️ Tejón: Congelación + recuperación
    KILL_SWITCH = (
        "⚔️",
        "Tejón",
        "Defensa de Tejón",
        "Freeze instantáneo + exponential backoff: respuesta a ataque activo",
    )

    @property
    def emoji(self) -> str:
        return self.value[0]

    @property
    def name_es(self) -> str:
        return self.value[1]

    @property
    def title_es(self) -> str:
        return self.value[2]

    @property
    def description_es(self) -> str:
        return self.value[3]


# Backward-compatibility alias — callers still using AnimalDefense won't break.
# ponytail: remove once all callers import ArgosLayer directly.
AnimalDefense = ArgosLayer


@dataclass
class DefenseStatus:
    """
    Estado operacional de una capa del Protocolo ARGOS.
    (Operational status of an ARGOS Protocol layer.)
    """

    defense: ArgosLayer
    enabled: bool
    last_check_ts: float
    last_alert: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializar a diccionario."""
        return {
            "emoji": self.defense.emoji,
            "name_es": self.defense.name_es,
            "title_es": self.defense.title_es,
            "enabled": self.enabled,
            "last_check_ts": self.last_check_ts,
            "last_alert": self.last_alert,
            "metrics": self.metrics,
        }


# Mapeo de capas del Protocolo ARGOS para acceso rápido
ALL_DEFENSES = {
    "corvid": ArgosLayer.CORVID,
    "cephalopod": ArgosLayer.CEPHALOPOD,
    "regeneration": ArgosLayer.REGENERATION,
    "kill_switch": ArgosLayer.KILL_SWITCH,
}
