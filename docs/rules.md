# Reglas Técnicas – Sentinel

## [ES] Español

### R-01 Integridad de Conteo Acumulado
Los votos acumulados nunca pueden disminuir entre snapshots consecutivos.

### R-02 Monotonicidad Temporal
Los timestamps deben avanzar o mantenerse, nunca retroceder.

### R-03 Consistencia Aritmética
La suma de votos por candidato debe coincidir con el total válido.

### R-04 Variación Atípica
Incrementos abruptos fuera de desviación histórica se registran como eventos.

### R-05 Reescritura Implícita
Cambio de valores sin aumento de actas se registra.

### R-06 Variación Relativa de Votos
Cambios porcentuales entre snapshots que superen un umbral configurable se registran como anomalías.

### R-07 Saltos en % Escrutado
Incrementos o decrementos abruptos en el porcentaje escrutado se registran como eventos.

### R-08 Discrepancias Mesas/Votos/Blancos/Nulos
Cuando el esquema lo permite, se detectan inconsistencias entre actas/mesas y el desglose de votos, blancos y nulos.

---

## [EN] English

### R-01 Accumulated Counting Integrity
Accumulated votes must never decrease between consecutive snapshots.

### R-02 Temporal Monotonicity
Timestamps must move forward or remain stable.

### R-03 Arithmetic Consistency
Sum of candidate votes must match valid votes.

### R-04 Atypical Variation
Abrupt increases outside historical deviation are logged as events.

### R-05 Implicit Rewrite
Value changes without act increase are logged.

### R-06 Relative Vote Variation
Percentage changes between snapshots above a configurable threshold are logged as anomalies.

### R-07 Scrutiny Percentage Jumps
Abrupt increases or decreases in scrutiny percentage are logged as events.

### R-08 Tables/Votes/Blank/Null Discrepancies
When the schema allows, inconsistencies between tables/actas and the vote breakdown (valid, blank, null) are detected.
