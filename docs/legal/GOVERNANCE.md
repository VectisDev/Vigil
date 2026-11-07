# Governance Document — VIGIL
## Documento de Gobernanza

**Version:** 1.1 | **Date:** 2026-05-18 | **Status:** Active

---

## Español

### Propósito

Este documento define quién controla el proyecto VIGIL, cómo se toman las
decisiones, la política de conflicto de intereses, y cómo se incorporan nuevos
contribuyentes. Es un requisito estándar de organizaciones como NDI, Carter Center y EU EOM
para cualquier solicitud de grant.

---

### Estructura de Decisión

#### Rol de Mantenedor Principal

El mantenedor principal es responsable de:

- Decisiones de arquitectura técnica del núcleo criptográfico y estadístico
- Aprobación de contribuciones que afecten la cadena de hashes o las reglas estadísticas
- La divulgación de vulnerabilidades, por los dos canales de `.github/SECURITY.md`

**Criterio de selección:** Competencia técnica demostrable en criptografía aplicada,
estadística electoral y sistemas distribuidos. Sin afiliación a partido político o
candidatura electoral activa en los países donde el sistema opera.

No hay comité técnico, ni consejo, ni segundo mantenedor. La revisión académica se busca y ninguna institución la ha firmado.

---

### Política de Conflicto de Intereses

#### Prohibiciones absolutas

Los mantenedores y contribuyentes del proyecto NO pueden:

1. **Usar VIGIL para favorecer a un candidato o partido específico**
   — el sistema es 100% agnóstico a candidatos y partidos
2. **Integrar nombres de candidatos reales en código, tests o documentación**
   — usar siempre placeholders neutros ("Candidato A", "Partido X")
3. **Compartir datos electorales privados** obtenidos para validación técnica con terceros
   sin autorización escrita explícita
4. **Recibir remuneración de partidos políticos o candidatos** simultáneamente a trabajar
   en el proyecto
5. **Publicar una causa o un responsable** a partir de una señal del software. El repositorio no tiene una entidad legal que autorice ese texto.

#### Declaración requerida

Todo mantenedor y contribuyente con acceso al repositorio principal debe declarar:

- Si tiene afiliación activa con algún partido político o candidato en los países donde
  opera el sistema
- Si tiene relación contractual con el CNE u órgano electoral equivalente
- Cualquier conflicto potencial que pudiera afectar la imparcialidad del sistema

#### Proceso de divulgación

Si el mantenedor identifica un conflicto de intereses:
1. Escribirlo en el repositorio, en este archivo o en el informe del caso
2. No mezclar ese conflicto con una lectura de los datos
3. No hay un comité que pueda apartar a otra persona: solo está VectisDev

---

### Proceso de Contribución

#### Para contribuciones de código

1. Fork del repositorio → rama de feature → Pull Request
2. El PR debe pasar CI (tests, linting, type checking)
3. Revisión por al menos 1 mantenedor
4. Para cambios en reglas estadísticas o núcleo criptográfico: revisión por un
   revisor técnico independiente (ninguna institución está comprometida a la fecha)

#### Para contribuciones de documentación

1. Las traducciones y mejoras de documentación son bienvenidas sin revisión técnica formal
2. Los cambios en METHODOLOGY.md, THEORY_OF_CHANGE.md e INCIDENT_RESPONSE.md requieren
   revisión del mantenedor principal

#### Para reporte de seguridad

Ver `.github/SECURITY.md`. No publicar un fallo de seguridad en un issue. El contacto es vectisdev26@proton.me o el aviso privado de GitHub.

---

### Política de Divulgación Responsable

Si el sistema muestra una anomalía durante un proceso electoral real:

1. El mantenedor copia la evidencia antes de reiniciar nada
2. No hay un segundo revisor en este repositorio
3. El texto público describe el archivo guardado y enlaza `docs/evidence/HN2025.md` cuando habla de 2025
4. No se notifica a una misión ni a un medio en nombre de una entidad que no existe
5. No se nombra una causa ni un responsable

Una lectura publicada antes de mirar los bytes daña el registro.

---

### Licenciamiento y Uso

**Licencia principal:** AGPL-3.0

Todo código del proyecto está bajo AGPL-3.0, lo que requiere que cualquier modificación
sea publicada como código abierto. Esto garantiza que no puede existir una versión privada
del sistema con capacidades adicionales o reducidas sin transparencia.

No hay una licencia especial aparte de la AGPL-3.0. Una administración que adapte el código publica las modificaciones, como cualquier otra persona.

---

### Quién cobra

Quien solicita es el mantenedor, una persona, con identidad pública VectisDev.
El nombre legal se da solo al financiador al contratar y no está en este
repositorio. OTF financia a personas. NLnet paga a la persona después de cada
hito. No hace falta un patrocinador fiscal. Uno puede considerarse más
adelante. No hay ninguno. No hay supervisor académico. No se afirma una
relación con ninguna universidad.

---

### Historial de Revisiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2025-05-17 | Documento inicial |

---

## English

### Who is paid

The applicant is the individual maintainer. The public identity is VectisDev. The legal name is given only to the funder at contracting and is not in this repository. OTF funds individuals. NLnet pays an individual after each milestone. No fiscal sponsor is needed. One may be considered later. None is in place. There is no academic supervisor and no university relationship.

### Purpose

This document defines who controls the VIGIL project, how decisions are made,
the conflict of interest policy, and how new contributors are incorporated. It is a
standard requirement for organizations such as NDI, Carter Center, and EU EOM for any
grant application.

---

### Conflict of Interest Policy

**Absolute prohibitions** — maintainers and contributors may NOT:

1. Use VIGIL to favor a specific candidate or party
2. Include real candidate names in code, tests, or documentation
3. Share private electoral data obtained for technical validation with third parties
4. Receive remuneration from political parties or candidates while working on the project
5. Publish a cause or a responsible party from a software signal. This repository has no legal entity that clears that text.

**Required disclosure:** All maintainers with access to the main repository must declare
any active affiliation with political parties or candidates in countries where the system
operates.

---

### Responsible Disclosure Policy

If a stored series looks wrong during a real election:

1. The maintainer copies the evidence before restarting anything
2. There is no second reviewer in this repository
3. Public text describes the stored file
4. No mission and no newsroom is contacted in the name of an entity that does not exist
5. No cause and no responsible party is named

---

### Licensing

**Primary license:** AGPL-3.0

All project code is under AGPL-3.0, requiring any modifications to be published as open
source. This ensures no private version of the system can exist with additional or reduced
capabilities without transparency.

---

*Last revision: 2025-05-17*
*See also: [THEORY_OF_CHANGE.md](THEORY_OF_CHANGE.md) | CODE_OF_CONDUCT.md | SECURITY.md*
