[Español](#español) · [English](#english)

---

## Español

VIGIL combina **24 reglas estadísticas** (registradas en `src/centinel/core/rules/`) y **7 detectores forenses** de actas inconsistentes (`src/auditor/inconsistent_acts.py`). Ninguna regla decide sola: cada hallazgo es una señal para evaluación humana.

### Qué buscan las reglas

| Familia | Ejemplos | Técnica |
|---|---|---|
| Aritmética determinista | Sumas por mesa, participación imposible, emitidos mayores que inscritos | Validación exacta |
| Integridad de registros | Mesas que aparecen, desaparecen o cambian tras publicarse | Diferencia de conjuntos y huella SHA-256 por mesa |
| Distribución de dígitos | Ley de Benford, uniformidad del último dígito | χ² y MAD |
| Comportamiento en el tiempo | Saltos entre capturas, cambios de tendencia, velocidad de procesamiento, mesas tardías | Deltas en ventanas de tiempo |
| Comportamiento estadístico | Participación anómala, dispersión geográfica, correlación participación–voto, rachas | Z-score, coeficiente de variación, Pearson, Wald–Wolfowitz |
| Valores atípicos | Cambios porcentuales fuera de lo normal | Isolation Forest |

### Detectores forenses

Analizan el flujo de actas inconsistentes: inyección progresiva, velocidad de resolución imposible, beneficio asimétrico entre escrutinio especial y normal, retención y liberación masiva, Benford sobre el escrutinio especial y apagones de comunicación seguidos de cambios de tendencia.

### Calibración

Todos los umbrales se configuran en `config/prod/rules.yaml`. Los valores por defecto parten de convenciones estadísticas clásicas (p < 0,05 / 0,01 / 0,001, 3σ, umbral MAD de Nigrini) y de límites del dominio electoral, que deben ajustarse al sistema de cada país.

### Limitaciones, dichas con honestidad

- **Audita el dato publicado, no la papeleta.** Detecta manipulación del dato en línea, no del voto en la urna.
- **No prueba que el dato original sea correcto.** Si la autoridad publica un dato falso desde el primer momento, la cadena lo preserva pero no lo invalida; esa defensa corresponde al consenso entre testigos y a los detectores estadísticos.
- **Benford no aplica a todo.** Distribuciones acotadas pueden desviarse sin fraude; por eso la regla de Benford de primer dígito está limitada a severidad informativa y nunca actúa sola.
- **Reglas con memoria.** Algunas reglas necesitan varios ciclos de historial antes de ser fiables.

### Documentación completa

- [Metodología técnica](https://github.com/VectisDev/Vigil/blob/main/docs/research/METHODOLOGY.md)
- [Convenciones estadísticas](https://github.com/VectisDev/Vigil/blob/main/docs/stats/STATISTICAL_CONVENTIONS.md)
- [Análisis de falsos positivos (500 ejecuciones)](https://github.com/VectisDev/Vigil/blob/main/docs/research/FALSE_POSITIVE_ANALYSIS.md)

---

## English

VIGIL combines **24 statistical rules** (registered in `src/centinel/core/rules/`) and **7 forensic detectors** for inconsistent tally sheets (`src/auditor/inconsistent_acts.py`). No rule decides on its own: every finding is a signal for human evaluation.

### What the rules look for

| Family | Examples | Technique |
|---|---|---|
| Deterministic arithmetic | Per-table sums, impossible turnout, more ballots cast than registered voters | Exact validation |
| Record integrity | Tables that appear, disappear or change after publication | Set difference and per-table SHA-256 fingerprint |
| Digit distribution | Benford's law, last-digit uniformity | χ² and MAD |
| Behavior over time | Jumps between captures, trend shifts, processing speed, late tables | Deltas over time windows |
| Statistical behavior | Anomalous turnout, geographic dispersion, turnout–vote correlation, runs | Z-score, coefficient of variation, Pearson, Wald–Wolfowitz |
| Outliers | Unusual percentage changes | Isolation Forest |

### Forensic detectors

They analyze the flow of inconsistent tally sheets: progressive injection, impossible resolution speed, asymmetric benefit between special and regular scrutiny, hold-and-release, Benford on special scrutiny, and communication blackouts followed by trend shifts.

### Calibration

Every threshold is configurable in `config/prod/rules.yaml`. Defaults follow classic statistical conventions (p < 0.05 / 0.01 / 0.001, 3σ, Nigrini's MAD threshold) and electoral-domain limits, which must be tuned to each country's system.

### Limitations, stated honestly

- **It audits the published data, not the ballot.** It detects tampering with the online data, not with the vote in the box.
- **It does not prove the original data is correct.** If the authority publishes false data from the start, the chain preserves it without invalidating it; that defense belongs to witness consensus and the statistical detectors.
- **Benford does not apply everywhere.** Bounded distributions can deviate without fraud; that is why the first-digit Benford rule is capped at informational severity and never acts alone.
- **Stateful rules.** Some rules need several cycles of history before they are reliable.

### Full documentation

- [Technical methodology](https://github.com/VectisDev/Vigil/blob/main/docs/research/METHODOLOGY.md)
- [Statistical conventions](https://github.com/VectisDev/Vigil/blob/main/docs/stats/STATISTICAL_CONVENTIONS.md)
- [False positive analysis (500 runs)](https://github.com/VectisDev/Vigil/blob/main/docs/research/FALSE_POSITIVE_ANALYSIS.md)
