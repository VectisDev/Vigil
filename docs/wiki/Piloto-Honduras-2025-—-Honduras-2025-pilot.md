[Español](#español) · [English](#english)

---

## Español

> **Transparencia metodológica.** Es un **análisis forense retroactivo**, no una auditoría en vivo. Se hizo sobre 64 archivos JSON del Consejo Nacional Electoral (CNE) descargados manualmente el **4 de diciembre de 2025**, después de la elección del 30 de noviembre. Esos archivos no traen `previous_hash`: `verify_chain.py` debe reportar 63 huérfanos y salir en 1. Lo que sí está comprometido es la raíz Merkle de esos bytes, calculada después, no una custodia continua durante el conteo. La captura continua en vivo es el objetivo para Honduras 2029.

### Qué detectó el motor

| Hallazgo | Detalle |
|---|---|
| Apagón de comunicación de 13 horas | 3 dic 22:00 → 4 dic 11:06, sin datos publicados durante la noche; cambio de tendencia de −0,504 puntos |
| Tasa de resolución sobre el umbral pre-registrado | 2.346 actas inconsistentes resueltas a 39,15 actas/min (umbral operativo: 10/min; no es un límite físico medido en campo) |
| Estancamiento prolongado | 17 eventos en que el conteo de actas inconsistentes quedó congelado 8 o más ciclos seguidos |
| Patrón de inyección progresiva | 6 ciclos seguidos de deltas bajos con más de 1.000 actas inconsistentes pendientes |
| Interrupciones de comunicación | 41, incluidos 6 apagones nocturnos de más de 10 horas |

**VIGIL no acusa a ninguna parte.** Son observaciones sobre datos públicos, para que observadores calificados las evalúen.

### Compruébalo tú

```bash
make replay-offline
# verify_chain sale en 1: 63 huérfanos. La raíz Merkle debe coincidir.
```

- Datos crudos: `tests/fixtures/hnd_2025/` · [conjunto de datos en Zenodo (DOI 10.5281/zenodo.20598892)](https://zenodo.org/records/20598892)
- Anclaje a Bitcoin: `tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots`
- Script forense: `scripts/forensic_hnd_2025.py`
- [Informe interactivo en el panel](https://vectisdev.github.io/Vigil/reports/hnd_2025.html)

---

## English

> **Methodological transparency.** This is a **retroactive forensic analysis**, not a live audit. It was run on 64 JSON files from Honduras' National Electoral Council (CNE), downloaded manually on **December 4, 2025**, after the November 30 election. Those files have no `previous_hash`: `verify_chain.py` must report 63 orphans and exit 1. What is committed is the Merkle root of those bytes, computed afterwards, not continuous custody during the count. Continuous live capture is the target for Honduras 2029.

### What the engine detected

| Finding | Detail |
|---|---|
| 13-hour communication blackout | Dec 3 22:00 → Dec 4 11:06, no data published overnight; −0.504 point trend shift |
| Resolution rate above the pre-registered threshold | 2,346 inconsistent tally sheets resolved at 39.15 per minute (operational threshold: 10/min; not a field-measured physical limit) |
| Prolonged stagnation | 17 events where the inconsistent count froze for 8+ consecutive cycles |
| Progressive injection pattern | 6 consecutive low-delta cycles with over 1,000 inconsistent sheets pending |
| Communication gaps | 41, including 6 overnight blackouts longer than 10 hours |

**VIGIL does not accuse any party.** These are observations on public data, for qualified observers to evaluate.

### Check it yourself

```bash
make replay-offline
# verify_chain exits 1: 63 orphans. The Merkle root must match.
```

- Raw data: `tests/fixtures/hnd_2025/` · [dataset on Zenodo (DOI 10.5281/zenodo.20598892)](https://zenodo.org/records/20598892)
- Bitcoin anchor: `tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots`
- Forensic script: `scripts/forensic_hnd_2025.py`
- [Interactive report on the panel](https://vectisdev.github.io/Vigil/reports/hnd_2025.html)
