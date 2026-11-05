# Threat model — summary / Modelo de amenaza — resumen

Resumen orientado a revisores y financiadores. El modelo formal completo, con
activos A1–A8 y actores, está en
[`docs/security/THREAT-MODEL.md`](security/THREAT-MODEL.md).

Summary for reviewers and funders. The full formal model, with assets A1–A8 and
threat actors, is in [`docs/security/THREAT-MODEL.md`](security/THREAT-MODEL.md).

## Premisa distintiva / Distinguishing premise

VIGIL sigue el linaje de Certificate Transparency (RFC 6962) con una inversión
fundamental: **la autoridad que publica es el adversario primario**, no un
intermediario de red. El sistema no pide confianza a la autoridad ni se la
concede.

VIGIL follows the Certificate Transparency (RFC 6962) lineage with one
fundamental inversion: **the publishing authority is the primary adversary**, not
a network intermediary. The system neither requests nor extends trust to the
authority.

## Capa de seguridad → amenaza mitigada

| Amenaza / Threat | Control en VIGIL / Control |
|---|---|
| Alteración silenciosa de capturas tras su publicación | Cadena SHA-256 encadenada + raíz Merkle + anclaje OpenTimestamps/Bitcoin |
| Operador único como punto de fallo o de coerción | Diseño sin intervención humana continua; federación de testigos; reconstrucción `k` de `n` sin que dos custodios basten |
| Panel de control atacado / robo de credenciales | Semillas de alta entropía (no contraseñas humanas); solo hashes en `web/access.json`; el token de escritura vive únicamente en memoria de página y nunca se persiste |
| Presión para suavizar hallazgos | AGPL-3.0 + verificación offline; umbrales pre-registrados y versionados en abierto, comprobables contra la fecha del hallazgo |
| Acusación de caja negra | Código abierto, fixtures reales incluidos, scripts de reproducción de un comando |
| Imputación de intención o de fraude | El motor emite observaciones descriptivas; los veredictos están prohibidos por `docs/legal/OPERATING-PRINCIPLES.md` §8 |
| Carga abusiva sobre la autoridad auditada | Techo de 480 peticiones/hora por host, estiramiento automático del intervalo, alcance limitado a 19 endpoints |
| Exposición del operador / doxxing | Publicación seudónima; mínimo PII en el repositorio; identidades de custodios sin divulgar |

## Lo que el modelo NO cubre / Out of scope

- Alteración ocurrida **antes** de la publicación oficial: VIGIL custodia lo
  publicado, no puede atestiguar lo no publicado.
- Fraude presencial en mesa, que no deja traza en el flujo de datos.
- Determinación de causa o intención: queda reservada a observadores
  calificados, tribunales y la opinión pública.
