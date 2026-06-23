# Security Policy — Vigil

> NIST SP 800-53 PL-1 / ISO/IEC 27005 §7. Última actualización: 2026-06-23.
> Este documento es la política de seguridad operativa del sistema Vigil.

## Propósito y alcance

Vigil es un sistema de observación electoral ciudadano de código abierto para Honduras. Esta política cubre todos los componentes: pipeline de captura de datos, cadena de custodia criptográfica, interfaces web públicas, y operaciones de los testigos de integridad.

**Principio fundamental**: Vigil opera exclusivamente sobre fuentes de datos públicas del CNE. No captura, procesa ni almacena datos personales. Su misión es la verificación criptográfica de integridad de datos electorales públicos.

## Principios de seguridad

| Principio | Implementación |
|---|---|
| **Integridad por diseño** | SHA-256 encadenado en cada snapshot; no repudio via Ed25519 + Bitcoin OTS |
| **Zero Trust** | PBKDF2 para acceso a panel `/ops/`; sin backend; sin cookies de sesión permanentes |
| **Mínimo privilegio** | El sistema solo lee datos públicos; no escribe al CNE ni a ningún sistema externo |
| **Trazabilidad completa** | Cada acción sobre datos queda registrada en el hash chain |
| **Transparencia** | Todo el código es público en GitHub; metodología documentada públicamente |
| **Zero Cost / Zero Dependency** | Sin servidores propios; sin servicios de pago; sin dependencias de terceros con acceso a datos |

## Controles de acceso

| Recurso | Control | Implementación |
|---|---|---|
| Panel `/ops/` | Autenticación PBKDF2 con sal aleatoria | `web/ops/index.html` AUTH IIFE |
| Hash chain | Solo lectura pública; escritura solo por pipeline autorizado | `src/centinel/core/hashchain.py` |
| Claves Ed25519 | Almacenamiento fuera de línea; nunca en el repositorio | `docs/operations/WITNESS-SETUP-DETAILED.md` |
| Backups cifrados | AES-256-GCM; clave derivada de passphrase operador | `centinel_engine/secure_backup.py` |

## Gestión de incidentes

| Tipo de incidente | Respuesta inmediata | Escalación |
|---|---|---|
| Hash chain rota (detección de tamper) | Activar kill-switch; preservar estado actual; publicar alerta | Notificar a testigos de integridad |
| Clave Ed25519 comprometida | Revocar y regenerar; re-firmar cadena desde último punto verificado | Coordinación con testigos externos |
| Endpoint CNE cambiado silenciosamente | Endpoint healer intenta auto-recuperación; alerta si falla | Revisión manual de configuración |
| Takedown de GitHub Pages | Activar mirror nodes; publicar en IPFS | Notificar a observadores registrados |
| Identificación del operador | Protocolo OSINT: ver `docs/legal/OPERATING-PRINCIPLES.md` | N/A — protocolo operativo |

## Prohibiciones explícitas

1. **No almacenar PII**: ningún dato personal identificable en código, logs, reportes, ni artefactos.
2. **No modificar snapshots consolidados**: los snapshots una vez encadenados son inmutables por política.
3. **No usar servicios de pago**: Zero Cost mandate permanente — ver `docs/COST_ELIMINATION_ROADMAP.md`.
4. **No publicar claves privadas**: las claves Ed25519 y passphrases de backup nunca van al repositorio.
5. **No bypasear TLS**: todas las conexiones al CNE usan TLS con cert pinning.

## Revisión de esta política

Esta política debe revisarse:
- Antes de cada observación electoral activa.
- Después de cualquier incidente de seguridad.
- Cuando se incorporen nuevas funcionalidades que afecten la superficie de ataque.

---
*Ver también: `docs/legal/OPERATING-PRINCIPLES.md`, `docs/compliance/RISK_REGISTER.md`, `COMPLIANCE.md`.*
