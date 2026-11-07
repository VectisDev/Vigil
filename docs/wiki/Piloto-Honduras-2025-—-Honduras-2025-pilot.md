[Español](#español) · [English](#english)

---

## Español

> **Transparencia metodológica.** Es un análisis retroactivo de 64 archivos JSON del CNE, guardados a mano entre el 3 y el 10 de diciembre de 2025. No es una auditoría en vivo. La ficha única está en [`docs/evidence/HN2025.md`](https://github.com/VectisDev/Vigil/blob/main/docs/evidence/HN2025.md). Esos archivos no traen `previous_hash`: `verify_chain.py` sale en 1 con 63 huérfanos. La raíz Merkle compromete esos bytes; no es custodia continua. Los huecos entre nombres de archivo no son una medición de que el portal estuviera caído.

### Qué hay en la serie guardada

| Observación | Detalle |
|---|---|
| Intervalo largo sin archivo guardado | 3 dic 22:00 → 4 dic 11:06 entre dos archivos; diferencia de share −0,504 puntos. No hay registro de intentos de descarga |
| Tasa entre dos archivos | 2.346 actas inconsistentes menos en 60 minutos (39,15/min), cerca de 3.9× la heurística de 10/min. No es un estudio pre-registrado |
| Conteo de inconsistentes quieto | 17 tramos en que ese conteo no se movió durante 8 ciclos o más |
| Deltas pequeños | 6 ciclos con delta bajo y más de 1.000 actas inconsistentes todavía en el archivo |
| Intervalos largos | 41 intervalos entre archivos, 7 de ellos de más de 10 horas, sin prueba de caída del portal |

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

> **Methodological transparency.** This is a retrospective look at 64 CNE JSON files saved by hand from 3 to 10 December 2025. It is not a live audit. The single card is [`docs/evidence/HN2025.md`](https://github.com/VectisDev/Vigil/blob/main/docs/evidence/HN2025.md). Those files have no `previous_hash`: `verify_chain.py` exits 1 with 63 orphans. The Merkle root commits those bytes; it is not continuous custody. Gaps between filenames are not a measurement that the portal was down.

### What the stored series shows

| Observation | Detail |
|---|---|
| Long interval with no stored file | 3 Dec 22:00 → 4 Dec 11:06 between two files; share difference −0.504 points. No fetch log |
| Rate between two files | 2,346 fewer inconsistent tally sheets in 60 minutes (39.15/min), about 3.9× the heuristic of 10/min. Not a pre-registered study |
| Inconsistent count unmoved | 17 stretches where that count did not move for 8 or more cycles |
| Small deltas | 6 cycles with a low delta and more than 1,000 inconsistent tally sheets still in the file |
| Long intervals | 41 intervals between files, 7 of them longer than 10 hours, with no proof the portal was down |

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
