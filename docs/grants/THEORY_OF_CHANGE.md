# CENTINEL — Theory of Change + Results Framework
# Teoría del Cambio + Marco de Resultados

**Versión:** 1.0 · **Fecha:** 2026-06-07  
**Audiencia:** OTF · NDI · NED · Open Society · Carter Center · Revisores de grants  
**Alineación:** OECD-DAC · USAID MEL · OTF Internet Freedom Fund criteria

---

## 1. Problema / Problem Statement

En Honduras y Centroamérica, las autoridades electorales publican resultados que
los ciudadanos, periodistas y observadores deben aceptar **por confianza**. No existe
ningún mecanismo técnico independiente que permita verificar que los datos publicados
no fueron alterados después de su publicación, o que detecte patrones estadísticos
imposibles en tiempo real.

Esta asimetría de información tiene consecuencias directas: las crisis electorales de
Honduras en 2013, 2017 y los cuestionamientos de 2025 tenían en común la ausencia de
evidencia técnica verificable. Sin evidencia, las denuncias son tratadas como opiniones
políticas. Sin herramientas, los defensores no pueden proteger el proceso.

---

## 2. Theory of Change / Teoría del Cambio

```
INSUMOS          ACTIVIDADES              PRODUCTOS            EFECTOS           IMPACTO
─────────────    ─────────────────────   ─────────────────    ───────────────   ─────────────────
Datos públicos   Captura automática       64+ snapshots        Periodistas y     Mayor integridad
del CNE (JSON)   cada ≤5 minutos          encadenados con      observadores      electoral en
                                          SHA-256              tienen evidencia  Honduras 2029 y
Código AGPL-3.0  23 reglas forenses       criptográfica        técnica           toda Centroamérica
(abierto)        aplicadas en             verificable          verificable
                 tiempo real                                                     Reducción del
Costo cero       Anclaje Bitcoin          Alertas en tiempo    Disuasión:        espacio para
(GitHub free     via OpenTimestamps       real con niveles     manipuladores     manipulación de
tier)                                     de severidad         saben que hay     datos electorales
                 Guías para              calibrados           monitoreo         sin detección
                 observadores                                  independiente
                 internacionales          Reporte forense
                                          reproducible con
                 Validación               un solo comando
                 académica (UPNFM)
```

### Premisas / Assumptions

1. El CNE continuará publicando datos en formato JSON accesible públicamente.
2. Los actores con intención de manipulación evitarán hacerlo si saben que
   existe monitoreo independiente con evidencia verificable.
3. Los observadores internacionales adoptarán herramientas técnicas gratuitas
   si son suficientemente accesibles y documentadas.
4. La evidencia criptográficamente verificable tiene más peso que los informes
   cualitativos ante instituciones internacionales.

---

## 3. Results Framework / Marco de Resultados

### Nivel 1 — Outputs (Productos)

| # | Indicador | Línea base | Meta (12 meses) | Fuente de verificación |
|---|-----------|-----------|-----------------|----------------------|
| O1 | Snapshots capturados por elección | 64 (manual, HN 2025) | ≥ 2,000 (automatizado, ≤5 min) | Repositorio `centinel-data` |
| O2 | Reglas forenses activas y validadas | 23 (dev-v12) | 25+ con calibración departamental | `command_center/rules.yaml` |
| O3 | FP rate en datos limpios | 1.2% (Benford 2BL) | < 2% para todas las reglas CRITICAL | `docs/research/FALSE_POSITIVE_ANALYSIS.md` |
| O4 | Países con configuración activa | 1 (HN producción) + 5 configurados | 2 países con prueba de campo | `src/centinel/countries.py` |
| O5 | Documentación para observadores | 1 guía (v1.0) | Guías en ES/EN para 3 países | `docs/international_observers/` |
| O6 | Validación académica | Working paper borrador | Working paper con firma UPNFM | `docs/research/FALSE_POSITIVE_ANALYSIS.md` |

### Nivel 2 — Outcomes (Efectos inmediatos)

| # | Indicador | Línea base | Meta (12 meses) | Fuente |
|---|-----------|-----------|-----------------|--------|
| Oc1 | Periodistas/organizaciones que usan CENTINEL | 0 (no público) | ≥ 3 organizaciones de sociedad civil | Registros de uso, github forks |
| Oc2 | Misiones internacionales que conocen CENTINEL | 0 | ≥ 1 misión OEA o Carter Center briefeada | Comunicaciones, informes |
| Oc3 | Hallazgos forenses citados en informes externos | 0 | ≥ 1 cita en informe oficial de observación | Informes de misiones |
| Oc4 | Tiempo de detección de anomalías (vs. manual) | Semanas (post-electoral) | < 10 minutos (tiempo real) | Logs de alertas |
| Oc5 | Instancias independientes del swarm | 0 (single operator) | ≥ 3 forks activos en elección real | GitHub forks activos |

### Nivel 3 — Impact (Impacto)

| # | Indicador | Línea base | Meta (2029) | Supuesto |
|---|-----------|-----------|-------------|----------|
| I1 | Confianza pública en resultados electorales HN | Sin medir | Encuesta pre/post con mejora medible | Encuesta ciudadana |
| I2 | Cobertura de herramienta técnica en proceso HN 2029 | 0% | 100% del período de escrutinio | Logs de captura |
| I3 | Anomalías detectadas que reciben respuesta institucional | 0 | ≥ 1 anomalía con respuesta pública del CNE | Documentación pública |
| I4 | Adopción en otros países LATAM | 0 países en producción | 2 países en producción (GT o SV) | Field pilots |

---

## 4. Costo-efectividad / Cost-Effectiveness

| Comparación | Costo | Cobertura | Verificabilidad |
|-------------|-------|-----------|-----------------|
| Misión observación OEA | USD 200,000–500,000 / elección | Parcial (muestral) | Cualitativa |
| Misión EU EOM | USD 1,000,000–3,000,000 / elección | Parcial | Cualitativa |
| **CENTINEL (operación)** | **USD 0** | **100% datos publicados** | **Criptográfica** |
| CENTINEL (con grant validación) | USD 75,000 (una vez) | 100% + validación académica | Criptográfica + par |

**Ratio de eficiencia:** CENTINEL entrega cobertura 100% + verificabilidad criptográfica
a costo cero operativo. El grant solicitado es de validación y expansión, no de operación.

---

## 5. Gestión de riesgos / Risk Management

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| CNE cambia formato JSON | Media | Alto | Adaptadores por país en `countries.py`; arquitectura modular |
| CNE bloquea acceso | Alta | Alto | Swarm P2P federado; Tor fallback; gossip-first design |
| Instrumentalización política | Media | Crítico | AGPL-3.0; neutralidad en diseño; DISCLAIMER.md; academia |
| Credibilidad cuestionada | Baja | Alto | Validación UPNFM; calibración empírica; código abierto |
| Falta de adopción | Media | Medio | Guías para observadores; documentación accesible |

---

## 6. Alineación con criterios OTF / OTF Alignment

| Criterio OTF | Cómo lo cumple CENTINEL |
|--------------|------------------------|
| Fortalece internet freedom | Protege el acceso a datos electorales públicos contra supresión |
| Entornos autoritarios/represivos | Diseñado para Honduras; funciona donde el CNE podría bloquear acceso |
| Beneficia a defensores/periodistas | verify_chain.py: cualquier persona verifica sin infraestructura |
| Open source | AGPL-3.0; todo el código auditado; builds reproducibles |
| Zero cost | GitHub free tier; sin servidores; sin cuenta de terceros |
| Sostenibilidad | Costo cero = sostenible indefinidamente sin funding |

---

## 7. Indicadores de monitoreo interno / Internal Monitoring Indicators

Estos indicadores son medidos automáticamente por CENTINEL:

```yaml
# Medibles automáticamente en cada elección
technical_kpis:
  polling_success_rate: "% capturas exitosas / total intentos"
  chain_integrity_rate: "% snapshots con hash válido"
  alert_precision: "% alertas CRITICAL con anomalía confirmada"
  false_positive_rate: "% alertas en datos sin anomalía real"
  coverage_pct: "% período electoral con monitoreo activo"
  rule_execution_time_p95: "segundos por ciclo completo (target: <30s)"
```

---

*CENTINEL — AGPL-3.0 — docs/grants/THEORY_OF_CHANGE.md v1.0*  
*Para uso en propuestas OTF, NDI, NED, Open Society y Carter Center*
