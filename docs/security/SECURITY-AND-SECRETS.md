# Seguridad y gestión de secretos | Security and Secrets Management

## Español

### Propósito
Define prácticas de seguridad para VIGIL, incluyendo manejo de secretos, cifrado, logging seguro y backups. Complementa [README](../README.md) y [docs/SECRETS_BACKUP.md](SECRETS_BACKUP.md).

### Gestión de secretos
- Los tokens, claves privadas y contraseñas no se commitean. Cifrarlos y subir el archivo sigue siendo un secreto en git.
- Los secretos de GitHub Actions viven en la configuración del repositorio, no en el árbol.
- `scripts/encrypt_secrets.py` sirve para un archivo local. Este repositorio no guarda una clave de Arbitrum ni una clave de firma, cifrada o no.
- Contacto de seguridad: vectisdev26@proton.me y el aviso privado de GitHub. Ver `.github/SECURITY.md`.

### Cifrado y protección de datos
- **Hashing criptográfico:** snapshots y diffs se protegen con hashes encadenados para integridad.
- **No almacenar datos personales:** únicamente datos públicos agregados.
- **Principio de mínimo privilegio:** limitar acceso a secretos solo a procesos necesarios.

### Logging seguro
- **Evitar datos sensibles:** no registrar llaves ni secretos en logs.
- **Logs rotativos:** habilitar rotación para reducir exposición y consumo.
- **Trazabilidad técnica:** registrar hashes, métricas agregadas y metadatos relevantes.

### Backups y resguardo
- **Procedimientos de respaldo:** seguir la guía de [SECRETS_BACKUP.md](SECRETS_BACKUP.md).
- **Separación de medios:** almacenar copias cifradas en ubicaciones distintas.
- **Pruebas periódicas de restauración:** validar que los respaldos funcionen.

### Auditoría y cumplimiento
- **Escaneos de vulnerabilidades:** ejecutar `make scan-security` (requiere GitHub CLI).
- **Revisión de configuraciones:** verificar que los secretos estén fuera del control de versiones.
- **Trazabilidad reproducible:** alinear con la metodología en [METHODOLOGY.md](METHODOLOGY.md).

### Enlaces relacionados
- [README](../README.md)
- [METHODOLOGY.md](METHODOLOGY.md)
- [LEGAL-AND-OPERATIONAL-BOUNDARIES.md](LEGAL-AND-OPERATIONAL-BOUNDARIES.md)
- [OPERATIONAL-FLOW-AND-CADENCE.md](OPERATIONAL-FLOW-AND-CADENCE.md)
- [SECRETS_BACKUP.md](SECRETS_BACKUP.md)

---

## English

### Purpose
Defines security practices for VIGIL, including secrets handling, encryption, safe logging, and backups. It complements the [README](../README.md) and [docs/SECRETS_BACKUP.md](SECRETS_BACKUP.md).

### Secrets management
- Tokens, private keys, and passwords are not committed. Encrypting them and uploading the file is still a secret in git.
- GitHub Actions secrets live in repository settings, not in the tree.
- `scripts/encrypt_secrets.py` is for a local file. This repository does not store an Arbitrum key or a signing key, encrypted or otherwise.
- Security contact: vectisdev26@proton.me and GitHub private vulnerability reporting. See `.github/SECURITY.md`.

### Encryption and data protection
- **Cryptographic hashing:** snapshots and diffs are protected with chained hashes for integrity.
- **No personal data storage:** only aggregated public data.
- **Principle of least privilege:** limit secret access to required processes only.

### Safe logging
- **Avoid sensitive data:** do not log keys or secrets.
- **Rotating logs:** enable rotation to reduce exposure and storage overhead.
- **Technical traceability:** record hashes, aggregate metrics, and relevant metadata.

### Backups and safekeeping
- **Backup procedures:** follow [SECRETS_BACKUP.md](SECRETS_BACKUP.md).
- **Media separation:** store encrypted copies in distinct locations.
- **Periodic restore tests:** validate that backups are usable.

### Auditing and compliance
- **Vulnerability scans:** run `make scan-security` (requires GitHub CLI).
- **Configuration review:** ensure secrets remain out of version control.
- **Reproducible traceability:** align with [METHODOLOGY.md](METHODOLOGY.md).

### Related links
- [README](../README.md)
- [METHODOLOGY.md](METHODOLOGY.md)
- [LEGAL-AND-OPERATIONAL-BOUNDARIES.md](LEGAL-AND-OPERATIONAL-BOUNDARIES.md)
- [OPERATIONAL-FLOW-AND-CADENCE.md](OPERATIONAL-FLOW-AND-CADENCE.md)
- [SECRETS_BACKUP.md](SECRETS_BACKUP.md)
