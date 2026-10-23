# Piloto Honduras 2025 — Honduras 2025 pilot

[Español](#español) · [English](#english)

---

## Español

> **Transparencia metodológica.** Es un **análisis forense retroactivo**, no una auditoría en vivo. Se hizo sobre 64 archivos JSON del Consejo Nacional Electoral (CNE) descargados manualmente el **4 de diciembre de 2025**, después de la elección del 30 de noviembre. La cadena criptográfica se construyó a posteriori: demuestra la capacidad de detección del motor con datos reales, pero no es evidencia observacional del proceso en vivo. La captura continua en vivo es el objetivo para Honduras 2029.

### Qué detectó el motor

| Hallazgo | Detalle |
|---|---|
| Apagón de comunicación de 13 horas | 3 dic 22:00 → 4 dic 11:06, sin datos publicados durante la noche; cambio de tendencia de −0,504 puntos |
| Tasa de resolución físicamente improbable | 2.346 actas inconsistentes resueltas a 39,15 actas/min (umbral: 10/min) |
| Estancamiento prolongado | 17 eventos en que el conteo de actas inconsistentes quedó congelado 8 o más ciclos seguidos |
| Patrón de inyección progresiva | 6 ciclos seguidos de deltas bajos con más de 1.000 actas inconsistentes pendientes |
| Interrupciones de comunicación | 41, incluidos 6 apagones nocturnos de más de 10 horas |

**VIGIL no afirma fraude.** Son anomalías estadísticas sobre datos públicos, para que observadores calificados, tribunales y la ciudadanía las evalúen.

### Compruébalo tú

```bash
make reproduce-2025-audit
python verify/verify_chain.py tests/fixtures/hnd_2025/
```

- Datos crudos: `tests/fixtures/hnd_2025/` · [conjunto de datos en Zenodo (DOI 10.5281/zenodo.20598892)](https://zenodo.org/records/20598892)
- Anclaje a Bitcoin: `tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots`
- Script forense: `scripts/forensic_hnd_2025.py`
- [Informe interactivo en el panel](https://vectisdev.github.io/Vigil/reports/hnd_2025.html)

---

## English

> **Methodological transparency.** This is a **retroactive forensic analysis**, not a live audit. It was run on 64 JSON files from Honduras' National Electoral Council (CNE), downloaded manually on **December 4, 2025**, after the November 30 election. The cryptographic chain was built after the fact: it shows the engine's detection capability on real data, but it is not observational evidence of the live process. Continuous live capture is the target for Honduras 2029.

### What the engine detected

| Finding | Detail |
|---|---|
| 13-hour communication blackout | Dec 3 22:00 → Dec 4 11:06, no data published overnight; −0.504 point trend shift |
| Physically implausible resolution rate | 2,346 inconsistent tally sheets resolved at 39.15 per minute (threshold: 10/min) |
| Prolonged stagnation | 17 events where the inconsistent count froze for 8+ consecutive cycles |
| Progressive injection pattern | 6 consecutive low-delta cycles with over 1,000 inconsistent sheets pending |
| Communication gaps | 41, including 6 overnight blackouts longer than 10 hours |

**VIGIL does not assert fraud.** These are statistical anomalies in public data, for qualified observers, courts and the public to evaluate.

### Check it yourself

```bash
make reproduce-2025-audit
python verify/verify_chain.py tests/fixtures/hnd_2025/
```

- Raw data: `tests/fixtures/hnd_2025/` · [dataset on Zenodo (DOI 10.5281/zenodo.20598892)](https://zenodo.org/records/20598892)
- Bitcoin anchor: `tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots`
- Forensic script: `scripts/forensic_hnd_2025.py`
- [Interactive report on the panel](https://vectisdev.github.io/Vigil/reports/hnd_2025.html)
