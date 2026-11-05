"""Utilidades estadísticas compartidas / shared statistical utilities."""

from .multiple_testing import benjamini_hochberg, bonferroni

__all__ = ["benjamini_hochberg", "bonferroni"]
