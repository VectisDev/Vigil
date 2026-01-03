# Security Policy

This project is dedicated to transparent and verifiable monitoring of public electoral data. Security is paramount to ensure data integrity and prevent manipulation. We welcome responsible disclosures.

## Supported Versions
The project is in preparation for 2029 elections. Current versions use Python 3.11 and fixed library dependencies (see requirements.txt). Only the main branch is supported.

## Reporting a Vulnerability
If you discover a security vulnerability in the code, scripts, or workflow:
- **Do not open a public issue** for sensitive matters to avoid exploitation.
- Email details to letha.kevin3513@carpecool.fr (include "Security Report" in the subject).
- Include: Description, reproduction steps, potential impact, and suggested fix.
- We will acknowledge receipt within 48 hours and work on a fix, crediting you if desired (anonymous OK).

## Vulnerability Management
- **Dependencies**: Scanned via GitHub Dependabot (enabled). Fixed versions in requirements.txt.
- **Code Scanning**: GitHub CodeQL enabled for static analysis (Settings → Security → Code scanning → Set up CodeQL).
- **Branch Protection**: Main branch requires pull request reviews (no direct pushes).
- **Script Integrity**: All scripts hashed in hashes/scripts_hashes.md. Verify with `sha256sum`.
- **Data Integrity**: SHA-256 chaining in snapshots (immutable record).
- **Known Risks**: Potential geo-blocks from CNE – fallback to proxies in docs/proxy.md.

Contributions must follow secure practices (signed commits recommended). For questions, open an issue.

Last updated: January 3, 2026

---

# Política de Seguridad

Este proyecto está dedicado al monitoreo transparente y verificable de datos electorales públicos. La seguridad es paramount para garantizar la integridad de los datos y prevenir manipulaciones. Damos la bienvenida a divulgaciones responsables.

## Versiones Soportadas
El proyecto está en preparación para las elecciones de 2029. Las versiones actuales usan Python 3.11 y dependencias fijas (ver requirements.txt). Solo la rama main es soportada.

## Reportar una Vulnerabilidad
Si descubre una vulnerabilidad de seguridad en el código, scripts o workflow:
- **No abra un issue público** para asuntos sensibles para evitar explotación.
- Envía detalles por email a letha.kevin3513@carpecool.fr (incluya "Security Report" en el asunto).
- Incluya: Descripción, pasos de reproducción, impacto potencial y fix sugerido.
- Reconoceremos recepción en 48 horas y trabajaremos en un fix, acreditándote si lo deseas (anónimo OK).

## Gestión de Vulnerabilidades
- **Dependencias**: Escaneadas vía GitHub Dependabot (habilitado). Versiones fijas en requirements.txt.
- **Escaneo de Código**: GitHub CodeQL habilitado para análisis estático (Settings → Security → Code scanning → Set up CodeQL).
- **Protección de Rama**: Rama main requiere revisiones de pull requests (no pushes directos).
- **Integridad de Scripts**: Todos los scripts hasheados en hashes/scripts_hashes.md. Verifique con `sha256sum`.
- **Integridad de Datos**: Encadenamiento SHA-256 en snapshots (registro inmutable).
- **Riesgos Conocidos**: Posibles geo-bloqueos del CNE – fallback a proxies en docs/proxy.md.

Las contribuciones deben seguir prácticas seguras (commits firmados recomendados). Para preguntas, abra un issue.

Última actualización: 3 de enero de 2026
