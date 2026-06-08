# Datos Departamentales Sintéticos — HN 2025
# Synthetic Departmental Data — HN 2025

**Tipo:** SINTÉTICO — generado a partir de totales nacionales reales  
**Fecha:** 2026-06-07 · **Seed:** 2025 (reproducible)

## Por qué sintético / Why synthetic

El CNE de Honduras publica datos a nivel nacional durante las elecciones.
Los JSONs departamentales reales no estaban disponibles durante las capturas
manuales de diciembre 2025, y el API del CNE 2025 ya está offline.

Estos archivos distribuyen los totales nacionales entre los 18 departamentos
usando pesos del padrón electoral real y variación departamental gaussiana (σ=1.5pp).

## Uso / Usage

**Solo para:** calibración de R6 (CV geográfico), tests de integración, demos.  
**No usar para:** análisis forense real, comunicaciones públicas, grants.

## Validación R6 — Coeficiente de Variación

| Métrica | Valor | Umbral dev-v10 | Estado |
|---------|-------|---------------|--------|
| CV share líder | 0.0191 | critical=0.45 | ✅ No dispara |
| CV turnout | 0.0289 | — | ✅ Normal |

**Conclusión:** `critical_cv=0.45` es defensible — datos normales de HN producen CV~0.02.

## Reproducir / Reproduce

```bash
PYTHONPATH=src python scripts/generate_synthetic_dept_data.py
```
