"""
Niveles de severidad compartidos para todas las reglas de CENTINEL.
Shared severity levels for all CENTINEL rules.
"""

from enum import Enum


class Severity(Enum):
    """Alert severity levels aligned with the CENTINEL rules engine."""
    NOMINAL = "NOMINAL"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
