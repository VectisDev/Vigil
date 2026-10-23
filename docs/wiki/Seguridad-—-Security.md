[Español](#español) · [English](#english)

---

## Español

### Reportar una vulnerabilidad

Repórtala **en privado** desde la pestaña [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new). No abras un *issue* público para fallos de seguridad. El objetivo es responder en 48 horas y publicar una corrección o mitigación en 7 días para fallos críticos. Contacto alternativo: security@vectis.dev.

### Cómo se protege la evidencia

- **Integridad:** cada captura se hashea con SHA-256 y se enlaza a la anterior; alterar cualquier dato pasado rompe la cadena de forma detectable.
- **Tiempo:** las raíces de Merkle se anclan a Bitcoin con OpenTimestamps, de modo que nadie puede retrodatar la evidencia.
- **Autoría:** testigos y operadores firman con Ed25519.
- **Copias de seguridad:** cifradas con Fernet y claves derivadas con HKDF-SHA256.

### Qué hay (y qué no) en el repositorio

- No hay secretos, credenciales ni claves privadas en el código.
- El panel, la administración y el visor son HTML estático servido desde GitHub Pages.
- `web/access.json` solo contiene hashes de las claves de acceso del panel, nunca las claves.
- Cada cambio pasa por CodeQL, análisis de calidad, Dependabot y escaneo de secretos.

### Documentación completa

- [Política de seguridad](https://github.com/VectisDev/Vigil/blob/main/SECURITY.md)
- [Revisión de seguridad y modelo de amenazas](https://github.com/VectisDev/Vigil/blob/main/docs/security/SECURITY-REVIEW.md)
- [Modelos de amenaza en la arquitectura](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARCHITECTURE.md)

---

## English

### Reporting a vulnerability

Report it **privately** from the [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new) tab. Do not open a public issue for security bugs. The goal is to acknowledge within 48 hours and publish a fix or mitigation within 7 days for critical issues. Alternative contact: security@vectis.dev.

### How the evidence is protected

- **Integrity:** every capture is hashed with SHA-256 and linked to the previous one; altering any past data breaks the chain detectably.
- **Time:** Merkle roots are anchored to Bitcoin through OpenTimestamps, so nobody can backdate the evidence.
- **Authorship:** witnesses and operators sign with Ed25519.
- **Backups:** encrypted with Fernet, with keys derived through HKDF-SHA256.

### What is (and is not) in the repository

- There are no secrets, credentials or private keys in the code.
- The panel, admin and replay viewer are static HTML served from GitHub Pages.
- `web/access.json` holds only hashes of the panel access keys, never the keys themselves.
- Every change goes through CodeQL, code quality analysis, Dependabot and secret scanning.

### Full documentation

- [Security policy](https://github.com/VectisDev/Vigil/blob/main/SECURITY.md)
- [Security review and threat model](https://github.com/VectisDev/Vigil/blob/main/docs/security/SECURITY-REVIEW.md)
- [Threat models in the architecture](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARCHITECTURE.md)
