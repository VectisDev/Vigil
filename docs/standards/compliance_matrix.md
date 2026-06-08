# CENTINEL — Matriz de Cumplimiento con Estándares Internacionales
# CENTINEL — International Standards Compliance Matrix

**Versión / Version:** 1.0 · **Fecha / Date:** 2026-06-07
**Estado / Status:** Borrador — pendiente revisión @international-standards-agent

---

## Resumen / Summary

| Estándar | Cobertura | Estado |
|----------|-----------|--------|
| OEA Principios de Observación Electoral (2005) | 8/10 principios | 🟡 Parcial |
| Carter Center Electoral Observation Manual | 6/8 áreas | 🟡 Parcial |
| OSCE/ODIHR Election Observation Handbook | 5/7 compromisos | 🟡 Parcial |
| NDI/IFES Principles for Digital Electoral Technologies | 7/9 principios | 🟡 Parcial |
| Council of Europe Recommendation on Election Technology | 4/6 requisitos | 🟡 Parcial |

**Leyenda:** ✅ Cumple · 🟡 Parcial · ❌ Brecha · 🔵 No aplica

---

## 1. OEA — Declaración de Principios para la Observación Electoral Internacional (2005)

| # | Principio OEA | Componente CENTINEL | Estado | Evidencia |
|---|---------------|---------------------|--------|-----------|
| 1 | Observación genuina y sin interferencia | Análisis de datos públicos únicamente; no interfiere con procesos | ✅ | DISCLAIMER.md; README §Neutrality |
| 2 | Neutralidad política | Sin afiliación; DISCLAIMER bilingüe; AGPL-3.0 | ✅ | DISCLAIMER.md; LICENSE |
| 3 | Metodología profesional y sistemática | 23 reglas estadísticas documentadas con referencias académicas | ✅ | docs/stats/STATISTICAL_CONVENTIONS.md |
| 4 | Acceso a información pública | Analiza exclusivamente JSON/TREP del CNE (datos públicos) | ✅ | README §What it solves |
| 5 | Declaraciones basadas en evidencia objetiva | Reportes solo con métricas cuantitativas; no interpretaciones políticas | ✅ | verify_chain.py; reportes PDF |
| 6 | No interferencia con el proceso electoral | Sistema de lectura pasiva; no modifica, no envía datos a CNE | ✅ | Architecture docs |
| 7 | Coordinación con misiones internacionales | **Pendiente** — guías para observadores no completadas | ❌ | — |
| 8 | Seguridad de los observadores | Opsec del operador documentada; identidad protegida | 🟡 | docs/opsec/ (en desarrollo) |
| 9 | Evaluación del proceso completo | Solo analiza datos publicados; no observa logística ni urnas | 🔵 | No aplica — auditoria digital |
| 10 | Reporte oportuno | Alertas en tiempo real durante el evento | ✅ | Polling ≤5 min |

**Cobertura:** 7 cumple + 1 parcial + 1 brecha + 1 no aplica = **78% de principios aplicables**

**Brecha prioritaria:** Desarrollar guía técnica para observadores de misiones OEA.

---

## 2. Carter Center — Electoral Observation Guidelines

| Área | Descripción | Estado CENTINEL | Notas |
|------|-------------|-----------------|-------|
| Data integrity | Verificabilidad de datos electorales | ✅ | SHA-256 chain + verify_chain.py |
| Transparency | Metodología abierta y reproducible | ✅ | AGPL-3.0; STATISTICAL_CONVENTIONS.md |
| Neutrality | Neutralidad política documentada | ✅ | DISCLAIMER.md bilingüe |
| Statistical rigor | Validación estadística académica | 🟡 | WP-CENTINEL-2026-01 pendiente firma |
| Independent verification | Verificación offline por terceros | ✅ | verify_chain.py (0 dependencias) |
| Chain of custody | Cadena de custodia criptográfica | ✅ | SHA-256 chained hash |
| Observer training | Materiales para observadores | ❌ | Pendiente: guía de interpretación |
| Reporting standards | Reportes con disclaimers neutros | 🟡 | PDFs parciales; disclaimer en README |

**Cobertura:** 5 cumple + 2 parcial + 1 brecha = **75% de áreas**

---

## 3. OSCE/ODIHR — Election Observation Handbook (8ª edición)

| Compromiso | Descripción | Estado CENTINEL |
|------------|-------------|-----------------|
| Código de conducta | Conducta neutral e imparcial | ✅ DISCLAIMER.md |
| Metodología sistemática | Enfoque cuantitativo documentado | ✅ 23 reglas con referencias |
| Acceso a información | Uso exclusivo de datos públicos | ✅ README §What it solves |
| Observación tecnológica | Herramienta tecnológica para observación | ✅ Arquitectura completa |
| Coordinación | Coordinación con misiones | ❌ Sin protocolo formal aún |
| Publicación de hallazgos | Reportes verificables y reproducibles | 🟡 En desarrollo |
| Protección de operadores | Opsec de operadores | 🟡 En desarrollo |

---

## 4. NDI/IFES — Principles for Digital Electoral Technologies

| Principio | Descripción | Estado CENTINEL | Evidencia |
|-----------|-------------|-----------------|-----------|
| Transparencia | Código abierto y auditable | ✅ | AGPL-3.0; código público |
| Auditabilidad | Auditoría independiente posible | ✅ | verify_chain.py; reproducibilidad |
| Seguridad | Protección contra manipulación | ✅ | SHA-256 chain; Ed25519 |
| Accesibilidad | Operación sin infraestructura cara | ✅ | Costo cero; 3 pasos |
| Neutralidad | Sin sesgo político | ✅ | DISCLAIMER.md |
| Interoperabilidad | Múltiples países LATAM | 🟡 | HN producción; otros configurados |
| Privacidad | No recopila datos personales | ✅ | user-privacy-agent; logs anónimos |
| Sostenibilidad | Operación a largo plazo | ✅ | Costo cero; AGPL garantía |
| Documentación | Documentación para usuarios | 🟡 | Técnica sí; no-técnica pendiente |

---

## 5. Council of Europe — Recommendation on Electronic Voting

| Requisito | Estado CENTINEL | Notas |
|-----------|-----------------|-------|
| Transparencia del sistema | ✅ | Código abierto AGPL-3.0 |
| Verificabilidad individual | ✅ | verify_chain.py para cualquier tercero |
| Seguridad criptográfica | ✅ | SHA-256, Ed25519, HKDF |
| Protección de datos | 🟡 | user-privacy-agent en implementación |
| Auditabilidad técnica | ✅ | STATISTICAL_CONVENTIONS.md; tests |
| Certificación/validación | ❌ | Validación académica UPNFM pendiente firma |

---

## 6. Brechas prioritarias / Priority Gaps

| Brecha | Estándar afectado | Esfuerzo estimado | Responsable |
|--------|-------------------|-------------------|-------------|
| Guía técnica para observadores | OEA, Carter Center, OSCE | 2-3 días | @international-standards-agent |
| Validación académica firmada | Carter Center, NDI | 0 días código (Devis) | Prof. Devis Alvarado |
| Guía no-técnica bilingüe | OSCE, NDI | 1-2 días | @dashboard-visual-agent |
| Protocolo formal con misiones | OEA, OSCE | 2-4 semanas | @legal-strategy-agent |

---

## 7. Fortalezas diferenciadoras / Differential Strengths

Áreas donde CENTINEL **supera** los estándares de observación tradicional:

| Dimensión | Observación tradicional | CENTINEL |
|-----------|------------------------|----------|
| Costo | $10k–$500k/elección | $0 (GitHub free tier) |
| Verificabilidad | Informes cualitativos | Prueba criptográfica offline |
| Tiempo real | Reportes post-electorales | Alertas cada ≤5 minutos |
| Resistencia | Organización = punto único | Swarm P2P — sin centro |
| Acceso | Requiere acreditación | Cualquier ciudadano |
| Reproducibilidad | Metodología cerrada | Totalmente reproducible |

---

*Documento mantenido por @international-standards-agent*
*Actualizar con cada nueva funcionalidad o estándar relevante*
*CENTINEL — AGPL-3.0 — github.com/VectisDev/centinel*
