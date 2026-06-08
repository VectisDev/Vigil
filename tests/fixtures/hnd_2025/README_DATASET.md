# Dataset: Honduras 2025 Presidential Election — CNE Snapshots
# Dataset: Elecciones Presidenciales Honduras 2025 — Snapshots CNE

**DOI:** *(pending Zenodo upload)*  
**Versión / Version:** 1.0  
**Fecha de creación / Created:** 2026-06-07  
**Licencia / License:** CC BY 4.0  

---

## Descripción / Description

Colección de 64 archivos JSON capturados del sistema de transmisión de resultados
electorales preliminares (TREP) del Consejo Nacional Electoral (CNE) de Honduras,
durante el escrutinio de las elecciones generales del 30 de noviembre de 2025.

Collection of 64 JSON files captured from the Preliminary Electoral Results
Transmission (TREP) system of Honduras's National Electoral Council (CNE),
during the count of the November 30, 2025 general elections.

---

## Cobertura / Coverage

| Campo | Valor |
|-------|-------|
| País / Country | Honduras |
| Elección / Election | Elecciones generales 2025 — nivel presidencial |
| Fuente / Source | CNE Honduras (datos públicos) |
| Período de captura | 2025-12-03 16:25 → 2025-12-10 17:03 |
| Capturas totales | 64 archivos JSON |
| Tamaño total | ~70 KB |
| Merkle root SHA-256 | `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780` |

---

## Estructura de archivos / File structure

```
HN.PRESIDENTE.00-TODOS.000-TODOS YYYY-MM-DD HH_MM_SS.json
```

Cada archivo contiene:
- `resultados`: votos por candidato y partido (nacional agregado)
- `estadisticas.totalizacion_actas`: actas totales y divulgadas
- `estadisticas.distribucion_votos`: válidos, nulos, blancos
- `estadisticas.estado_actas_divulgadas`: actas correctas e inconsistentes

---

## Integridad criptográfica / Cryptographic integrity

Los 64 archivos están anclados a Bitcoin blockchain via OpenTimestamps:

```bash
pip install opentimestamps-client
ots verify MERKLE_ROOT_HN2025.ots
```

Merkle root: `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`

---

## Uso / Usage

```bash
# Clonar el repositorio completo
git clone https://github.com/VectisDev/centinel.git
cd centinel

# Reproducir la auditoría forense completa
make reproduce-2025-audit

# Análisis de falsos positivos
PYTHONPATH=src python docs/research/run_fp_analysis.py
```

---

## Citación / Citation

```bibtex
@dataset{centinel_hnd2025,
  title     = {Honduras 2025 Presidential Election CNE Snapshots},
  author    = {CENTINEL Project},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {PENDING},
  url       = {https://github.com/VectisDev/centinel},
  license   = {CC BY 4.0},
  note      = {64 JSON snapshots from CNE Honduras TREP system,
               December 3-10 2025. Merkle root anchored to Bitcoin
               via OpenTimestamps: f17dbfe...}
}
```

---

## Neutralidad / Neutrality

Este dataset contiene datos públicos del CNE tal como fueron publicados.
Su análisis no implica ninguna afirmación de fraude electoral.
Ver: [DISCLAIMER.md](../../../../DISCLAIMER.md)

---

*CENTINEL — AGPL-3.0 · Datos: CC BY 4.0*
