"""
Niveles de severidad compartidos para todas las reglas de VIGIL.
Shared severity levels for all VIGIL rules.
"""

from enum import Enum


class Severity(Enum):
    """Alert severity levels aligned with the VIGIL rules engine."""
    NOMINAL = "NOMINAL"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
