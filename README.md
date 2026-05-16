# Centinel

[![License](https://img.shields.io/badge/License-AGPL--3.0-blue)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-499%20passing-success)

**Infraestructura de auditoría electoral verificable, sin confianza institucional.**

Centinel permite que cualquier ciudadano verifique de forma independiente la
integridad de los datos electorales publicados por una autoridad, sin necesidad
de confiar en esa autoridad, sin infraestructura dedicada y sin coste operativo.

> *Independent, trustless election-integrity verification. A single operator can
> audit a national election from a laptop — no institutional dependency, no
> dedicated infrastructure, zero operating cost.*

---

## Qué resuelve

Las autoridades electorales publican resultados que la ciudadanía debe aceptar
por confianza. Centinel elimina esa confianza requerida: captura los datos
publicados, los encadena criptográficamente y permite que cualquier tercero
verifique —de forma reproducible y offline— que no fueron alterados después de
su publicación.

| Propiedad | Garantía |
|---|---|
| **Reproducibilidad** | Cadena SHA-256 + raíz de Merkle, verificable offline por cualquiera |
| **Independencia** | El operador no necesita permiso ni cooperación de la autoridad |
| **Resiliencia** | Federación P2P; ningún punto único de fallo o captura |
| **Inmutabilidad temporal** | Anclaje en Bitcoin vía OpenTimestamps, sin coste |
| **Neutralidad** | Reporta hechos verificables. No interpreta intención política |

---

## Operación

```bash
poetry install

centinel panel show          # Estado del sistema
centinel snapshot            # Captura y verificación puntual
centinel cron --interval 30s # Captura continua automática
```

Un operador, una máquina. Sin servidores dedicados, sin coordinación institucional.

---

## Arquitectura de defensa

Centinel aplica defensa en profundidad: cada capa mitiga una clase distinta de
amenaza a la integridad o disponibilidad de la auditoría.

| Capa | Función | Amenaza mitigada |
|---|---|---|
| Atestación distribuida | Confirmación cruzada entre testigos | Testigo único comprometido |
| Cifrado en tránsito | ChaCha20-Poly1305 | Interceptación / MITM |
| Temporización no determinista | Jitter en la captura | Predicción y bloqueo selectivo |
| Auto-regeneración | Resincronización desde réplicas | Manipulación local del estado |
| Interruptor de seguridad | Congelación ante ataque activo | Compromiso en tiempo real |

→ [Especificación de defensas](docs/ANIMAL-DEFENSES-ES.md) ·
[Arquitectura y teoremas T1–T4](docs/ARCHITECTURE.md)

---

## Estado de validación

| Eje | Estado |
|---|---|
| Auditoría criptográfica (teoremas T1–T4) | Completa — verificable en el código |
| Suite de pruebas | 499 / 499 |
| Validación académica independiente | En curso (UPNFM, Honduras) |
| Piloto con datos reales | Pendiente (2–3 municipios) |

Versión **0.1 — pre-piloto.** Núcleo criptográfico estable; pendiente prueba de
campo y dictamen académico independiente.

---

## Documentación

| Documento | Audiencia |
|---|---|
| [QUICKSTART.md](docs/QUICKSTART.md) | Operadores — primeros pasos |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Revisores técnicos — diseño y teoremas |
| [SECURITY-REVIEW.md](docs/SECURITY-REVIEW.md) | Auditores — modelo de amenazas |
| [METHODOLOGY.md](docs/METHODOLOGY.md) | Académicos — fundamento metodológico |
| [OPERATOR-RUNBOOKS.md](docs/OPERATOR-RUNBOOKS.md) | Operadores — procedimientos |
| [LEGAL-AND-OPERATIONAL-BOUNDARIES.md](docs/LEGAL-AND-OPERATIONAL-BOUNDARIES.md) | Marco legal y límites operativos |

---

## Licencia

**GNU AGPL-3.0.** Software libre, auditable y de redistribución garantizada:
cualquier derivado debe permanecer abierto. Esta licencia es deliberada —
asegura que Centinel no pueda ser capturado, cerrado ni privatizado por ningún
actor, público o privado.

---

**Centinel** · Auditoría electoral como derecho ciudadano, no como privilegio
institucional · `userf8a2c4`
