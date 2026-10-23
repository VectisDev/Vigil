# Nombres heredados de CENTINEL / Legacy CENTINEL names

> **ES:** El proyecto se llamó CENTINEL antes de llamarse VIGIL. Este documento lista lo que conserva el nombre anterior **a propósito** y los alias que mantienen la compatibilidad.
>
> **EN:** The project was named CENTINEL before it became VIGIL. This document lists what keeps the former name **on purpose**, and the aliases that keep things compatible.

---

## 1. Constantes del protocolo (no cambian nunca) / Protocol constants (never change)

Forman parte de los hashes, las firmas y las claves. Cambiarlas invalidaría evidencia ya generada, incluida la cadena de Honduras 2025 anclada en Bitcoin. Cada una lleva un comentario en el código que remite a este documento.

They feed hashes, signatures and keys. Changing them would invalidate evidence that already exists, including the Honduras 2025 chain anchored to Bitcoin. Each carries a code comment pointing here.

| Constante / Constant | Dónde / Where | Uso / Use |
|---|---|---|
| `centinel-hashchain-v1` | `src/vigil/core/hashchain.py` | Separación de dominio de la cadena de hashes / Hash-chain domain separation |
| `centinel-chain-v1` | `src/vigil/download.py` | Encadenado de capturas / Snapshot chaining |
| `centinel-anchor-v1` | `src/vigil/core/anchoring_payload.py` | Raíz anclada con OpenTimestamps / OpenTimestamps-anchored root |
| `CENTINEL-ASYNC-POLLER-GENESIS-2026` | `src/vigil/core/poller_async.py` | Bloque génesis del poller / Poller genesis block |
| `centinel-checkpoint` | `src/vigil/checkpointing.py` | `info` de HKDF para checkpoints cifrados / HKDF `info` for encrypted checkpoints |
| `centinel-admin-salt-v1` | `src/vigil/seed_pdf.py`, `scripts/setup_wizard.py` | Sal de las claves del panel (formato v1) / Panel key salt (v1 format) |
| `centinel-log-v1` | `scripts/logging_utils.py`, `reports/report_generator.py` | Esquema de la evidencia exportada / Exported evidence schema |
| `-----BEGIN/END CENTINEL SHAMIR SHARE-----` | `src/vigil/core/crypto/centinel_share_format.py` | Marcas de las acciones de clave ya entregadas / Markers of key shares already handed out |

## 2. Nombres persistidos o externos / Persisted or external names

Se conservan porque ya existen fuera del código: en instalaciones, repositorios o servicios.

Kept because they already exist outside the code: in installations, repositories or services.

| Nombre / Name | Motivo / Reason |
|---|---|
| `.centinel-setup.json` | Marca que una instalación está configurada; cambiarla haría que el asistente la tratara como nueva / Marks an installation as configured; renaming it would make the wizard treat it as new |
| Sección `centinel:` de la configuración / `centinel:` config section | Presente en configuraciones guardadas / Present in saved configurations |
| Repositorio `centinel-data` / repository | Repositorio de datos existente / Existing data repository |
| `codeberg.org/VectisDev/centinel`, `peers-{país}.centinel.vectisdev.com` | Espejo y DNS de la federación existentes / Existing mirror and federation DNS |
| `/centinel-backups` (Dropbox) | Carpeta con copias existentes / Folder with existing backups |
| `web/downloads/centinel_observer_pack.zip` | URL de descarga publicada / Published download URL |
| `contracts/CentinelAnchor.sol` | Artefacto para la cadena de bloques / On-chain artifact |
| `scripts/centinel_key_ceremony.py`, `centinel_key_reconstruct.py` | Nombres citados en los procedimientos de custodia / Names quoted in custody procedures |
| Claves internas del navegador (`centinel_admin_*`) y nombres de eventos de log / Browser storage keys and log event names | Internos; cambiarlos cerraría sesiones o rompería filtros sin aportar nada / Internal; renaming would end sessions or break filters for no gain |
| Documentos históricos / Historical documents | Auditorías, diario de desarrollo, preprint, whitepaper v1, registro de espejos y CHANGELOG / Audits, dev diary, preprint, whitepaper v1, mirror log and CHANGELOG |

## 3. Alias de compatibilidad / Compatibility aliases

| Antes / Before | Ahora / Now | Cómo se resuelve / How it resolves |
|---|---|---|
| `import centinel`, `centinel.*` | `vigil`, `vigil.*` | El alias devuelve el **mismo** módulo; avisa con `DeprecationWarning` / The alias returns the **same** module; warns with `DeprecationWarning` |
| `import centinel_engine` | `vigil_engine` | Igual / Same |
| Comando / command `centinel` | `vigil` | Ambos ejecutan `vigil.cli:main` / Both run `vigil.cli:main` |
| `CENTINEL_<X>` | `VIGIL_<X>` | Se lee `VIGIL_<X>`; si no existe, `CENTINEL_<X>`. Si existen ambos, gana `VIGIL_<X>`. Los valores por defecto del perfil de seguridad nunca pisan un `CENTINEL_<X>` explícito / `VIGIL_<X>` is read first, then `CENTINEL_<X>`. If both exist, `VIGIL_<X>` wins. Security-profile defaults never override an explicit `CENTINEL_<X>` |
| Secreto / secret `CENTINEL_NTFY_TOPIC` | `VIGIL_NTFY_TOPIC` | El workflow acepta cualquiera / The workflow accepts either |
| Cabecera / header `X-Centinel-Key` | `X-Vigil-Key` | La API acepta ambas / The API accepts both |
| `window.CENTINEL_API_BASE` | `window.VIGIL_API_BASE` | `web/config.js` copia el valor antiguo si falta el nuevo / `web/config.js` copies the old value when the new one is missing |
| `CentinelSettings` | `VigilSettings` | Alias de la misma clase / Alias of the same class |
| `launchers/Centinel.sh`, `.command`, `.bat`, `scripts/centinel_service.sh` | `Vigil.*`, `scripts/vigil_service.sh` | Envoltorios que llaman al nuevo / Wrappers calling the new one |
| `centinel_engine/.env` | `vigil_engine/.env` | Se sigue usando el antiguo si ya existe / The old file is still used if it exists |

Los alias se retirarán en una versión mayor futura, anunciándolo en el CHANGELOG. Las constantes del protocolo no se retiran: cambiar una exigiría una versión nueva del protocolo (`-v2`) que conviva con la anterior.

Aliases will be removed in a future major release, announced in the CHANGELOG. Protocol constants are never removed: changing one would require a new protocol version (`-v2`) living alongside the old one.
