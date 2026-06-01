# Documentacion Matematica de Centinel / Centinel Mathematical Documentation

Referencia tecnica de los metodos estadisticos, formulas y umbrales utilizados
por las reglas de deteccion de Centinel Engine y el modulo forense de actas
inconsistentes.

Technical reference for the statistical methods, formulas, and thresholds used
by Centinel Engine detection rules and the inconsistent-acts forensic module.

---

## Indice / Index

| # | Archivo / File | Tema / Topic | Reglas fuente / Source rules |
|---|----------------|--------------|------------------------------|
| 1 | [benford-analysis.md](benford-analysis.md) | Ley de Benford (primer digito) / Benford's First Digit Law | `benford_first_digit_rule.py`, `benford_law_rule.py`, `granular_anomaly_rule.py` |
| 2 | [irreversibility.md](irreversibility.md) | Irreversibilidad estadistica / Statistical irreversibility | `irreversibility_rule.py` |
| 3 | [trend-shifts.md](trend-shifts.md) | Deteccion de cambios de tendencia / Trend shift detection | `trend_shift_rule.py`, `snapshot_jump_rule.py`, `granular_anomaly_rule.py` |
| 4 | [participation-anomalies.md](participation-anomalies.md) | Anomalias de participacion / Participation anomalies | `participation_anomaly_rule.py`, `participation_anomaly_advanced_rule.py`, `turnout_impossible_rule.py`, `null_blank_rule.py` |
| 5 | [statistical-tests.md](statistical-tests.md) | Pruebas estadisticas clasicas / Classical statistical tests | `runs_test_rule.py`, `last_digit_uniformity_rule.py`, `large_numbers_rule.py`, `correlation_participation_vote_rule.py`, `inconsistency_rate_rule.py` |
| 6 | [velocity-processing.md](velocity-processing.md) | Velocidad de procesamiento / Processing speed anomalies | `processing_speed_rule.py` |
| 7 | [inconsistent-acts.md](inconsistent-acts.md) | Deteccion forense de actas inconsistentes / Forensic inconsistent-acts detection | `src/auditor/inconsistent_acts.py` |
| 8 | [geographic-correlation.md](geographic-correlation.md) | Dispersion geografica y correlacion / Geographic dispersion and correlation | `geographic_dispersion_rule.py`, `correlation_participation_vote_rule.py` |
| 9 | [ml-outliers.md](ml-outliers.md) | Deteccion de outliers con ML / ML-based outlier detection | `ml_outliers_rule.py` |

---

## Reglas aritmeticas y de integridad / Arithmetic and integrity rules

Las siguientes reglas aplican chequeos deterministas (no estadisticos) y no
requieren documentacion matematica separada:

- `basic_diff_rule.py` -- Consistencia aritmetica basica entre snapshots.
- `table_consistency_rule.py` -- Validos + nulos + blancos vs total por mesa.
- `mesa_impossibility_rule.py` -- Imposibilidades aritmeticas por registro JSON.
- `mesa_reconciliation_rule.py` -- Mutacion de registros entre publicaciones.
- `mesas_diff_rule.py` -- Mesas duplicadas o desaparecidas entre snapshots.
- `late_mesa_rule.py` -- Aparicion tardia de registros en el JSON.

---

## Convenciones / Conventions

- Las formulas usan notacion LaTeX: en linea con `$...$`, en bloque con `$$...$$`.
- Cada seccion documenta: formula, hipotesis nula/alternativa, umbrales por defecto,
  sensibilidad/especificidad, falsos positivos posibles, y referencia al archivo fuente.
- Los encabezados son bilingues (ES/EN).
