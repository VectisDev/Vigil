# Fondo para la Libertad en Internet de OTF — nota conceptual

Borrador para el formulario en línea. Este archivo no es una solicitud presentada.

Revisado el 7 de noviembre de 2026 contra las páginas del fondo:

- Preguntas de la nota: [Apéndice I](https://docs.opentech.fund/otf-application-guidebook/appendix-i-concept-note-guide). Esa página no publica un límite de palabras para estas respuestas. Los límites del [apéndice II](https://docs.opentech.fund/otf-application-guidebook/appendix-ii-proposal-guide) valen solo si OTF pide una propuesta completa.
- Rango de montos: [Internet Freedom Fund](https://www.opentech.fund/funds/internet-freedom-fund/). Los premios pueden ir de 10.000 a 900.000 USD y hasta 24 meses. OTF dice que el pedido ideal está entre 50.000 y 200.000 USD por 6 a 12 meses. Este pedido es **75.000 USD por 12 meses**, dentro de ese rango.
- El pago es por entregables, en USD. El contrato se firma con quien solicita ([página del fondo](https://www.opentech.fund/funds/internet-freedom-fund/)). OTF financia a personas y también a proyectos ([nota del foro, 6 de abril de 2018](https://we.opentech.fund/t/does-otf-support-projects-individuals-or-both/894)). OTF no financia conectividad, TIC para el desarrollo, ni incidencia de política, como tales.
- Las notas conceptuales se aceptan de forma continua ([guía](https://docs.opentech.fund/otf-application-guidebook/our-funds-and-fellowships/internet-freedom-fund)). Este archivo no fija una fecha de envío.

Categoría en el formulario: **Desarrollo tecnológico** (una sola, como pide el formulario). No es un encuentro, así que la pregunta de fecha de inicio no aplica.

Cada encabezado de abajo corresponde a un campo. Las rutas son archivos de este repositorio.

---

## Título del proyecto

VIGIL — una copia comprobable de un canal público de resultados

## Describa su proyecto en 1–3 oraciones.

El proyecto guarda una copia de resultados legibles por máquina que un portal oficial ya publica, para que un periodista pueda ver después si esos bytes siguen igual y si siquiera se intentó una descarga. Los beneficiarios principales son periodistas y observadores electorales de Centroamérica que pueden clonar un repositorio público, empezando por el JSON de Honduras 2025 que ya está aquí. La comprobación sin red es `make replay-offline`, descrita en `docs/VERIFY.md`.

## ¿Qué problema abordará su proyecto?

Un portal oficial puede publicar un JSON y luego reemplazarlo, o dejar de responder, y quien no guardó la primera respuesta no tiene con qué comparar. Eso es una asimetría de información. Esta nota no dice quién, si alguien, cambió un conteo.

Lo que este repositorio tiene son 64 archivos JSON guardados a mano del Consejo Nacional Electoral de Honduras después de la elección del 30 de noviembre de 2025 (`docs/evidence/HN2025.md`, `tests/fixtures/hnd_2025/`). `verify/verify_chain.py` sale en 1 en ese directorio: 63 archivos no tienen `previous_hash`. No son una cadena de hashes. Una raíz Merkle de esos bytes está comprometida y `make replay-offline` la recalcula (`Makefile`, `Dockerfile.demo`). Los huecos entre nombres de archivo no son caídas medidas, porque no se guardó un registro de intentos.

El cambio que paga este fondo es más estrecho: un registro que distinga "nadie preguntó" de "preguntamos y el portal no contestó" (`tests/fixtures/fetch_logs/`, `scripts/export_static_snapshot.py`). Sin esa distinción, un archivo que falta se narra fácil como una caída. Si el problema sigue igual, la única copia del canal es la página que el portal muestra hoy.

## Si se financia, ¿qué forma tomará?

Desarrollo tecnológico. El producto son mejoras a un programa ya publicado bajo AGPL-3.0 (`LICENSE`, `pyproject.toml`), no un artículo como producto principal, no un curso y no un evento. No es un proyecto de conectividad, ni de TIC para el desarrollo, ni de incidencia de política, que OTF lista fuera de su mandato.

## Panorama breve de las actividades.

Una persona mantiene el repositorio, con el nombre VectisDev (`docs/operations/BUS_FACTOR.md`). No hay un revisor estadístico contratado (`docs/legal/GOVERNANCE.md`).

**Objetivo 1.** Un tercero comprueba la muestra guardada sin el mantenedor.

- Actividad: mantener obligatorios los jobs `replay-offline` y `demo-image` (`.github/workflows/ci.yml`, `Dockerfile.demo`).
- Actividad: el mantenedor ejecuta una vez el workflow de release (`docs/operations/RELEASE.md`). Este repositorio no ha creado esa etiqueta.
- Quién: VectisDev.
- Entregable: un release de GitHub con tarball, SBOM CycloneDX, `SHA256SUMS` y firma sin clave de largo plazo.
- Cuándo: meses 1–3.

**Objetivo 2.** El texto público no se adelanta a los archivos.

- Actividad: dejar `docs/evidence/HN2025.md` como la única ficha de la muestra de 2025, y `tests/test_claim_guard.py` en CI.
- Quién: VectisDev.
- Entregable: esa prueba sigue en verde durante los 12 meses.
- Cuándo: meses 1–12.

**Objetivo 3.** "Caída" significa un intento de descarga fallido y anotado.

- Actividad: usar la regla que ya existe: `reachable` queda desconocido si no hay un intento registrado (`scripts/export_static_snapshot.py`). No se reetiquetará la muestra de 2025.
- Quién: VectisDev.
- Entregable: un registro de intentos de la próxima ventana en que la herramienta apunte a un portal en vivo, o una nota de una página que diga que esa ventana no ocurrió.
- Cuándo: meses 3–12.

**Objetivo 4.** Un lector externo de la heurística de 10 por minuto, o un alto.

- El 10 es `DEFAULT_MAX_RESOLUTION_RATE` en `src/auditor/inconsistent_acts.py`. No está calibrado con otra elección. Honduras 2013, 2017 y 2021 no están en el árbol (`docs/research/HISTORICAL_CALIBRATION.md`). Las reglas CRITICAL están en `promotion: exploratory` hasta que exista un fixture fuera de la muestra de 2025 (`command_center/rules.yaml`, `tests/test_rule_promotion_gate.py`).
- Actividad: contratar a un lector que no sea el mantenedor, o escribir que el contrato no se hizo. Puede confirmar el resultado negativo o añadir `tests/fixtures/promotion/<regla>.json`.
- Quién: un revisor aún no contratado, pagado con la línea de abajo. VectisDev no califica su propia heurística.
- Entregable: un memo corto en `docs/research/`, o el fixture externo.
- Cuándo: meses 2–8.

**Objetivo 5.** Instrucciones en español que no agregan números.

- Actividad: una página en español cuyo único comando es el de `docs/VERIFY.md`.
- Quién: VectisDev.
- Entregable: esa página.
- Cuándo: meses 4–9.

## ¿Existen proyectos similares? ¿En qué se diferencia o complementa?

Certificate Transparency (RFC 6962) es la idea de que un lector posterior no tiene que confiar en la copia actual de quien publica. OpenTimestamps compromete un resumen en Bitcoin. Este proyecto usa esa forma sobre un canal JSON público y añade un registro de intentos. No observa mesas de votación y no reemplaza una misión de observación.

Los archivos de 2025 muestran el límite de la idea cuando la cadena no se escribió en el momento: el verificador falla, a propósito (`docs/VERIFY.md`). No hay un acuerdo de colaboración con ninguna misión ni redacción. No se afirma ninguno.

## ¿Cuánto tiempo estima que tomarán las actividades?

12 meses.

## ¿Cuánto financiamiento estima que necesitará? (en dólares de EE. UU.)

75.000 USD. Es el único total del repositorio (`docs/grants/BUDGET_NARRATIVE.md`). No hay viajes ni conferencias. Quien solicita es el mantenedor, una persona. La identidad pública es VectisDev. El nombre legal se da solo al financiador al contratar y no está en este archivo. No hace falta un patrocinador fiscal. Uno puede considerarse más adelante. No hay ninguno. NLnet, si se usa, paga a la persona directo después de cada hito y no exige una entidad legal ([preguntas de NLnet](https://nlnet.nl/core/faq/)).

| Entregable | USD |
|---|---|
| Lector estadístico externo, aún no contratado, o un alto escrito si el contrato no se hace. La ausencia de series 2013–2021 ya está escrita. | 22.000 |
| Un release de software firmado (tarball, SBOM CycloneDX, `SHA256SUMS`, firma sin clave de largo plazo). El workflow existe; la etiqueta no. | 15.000 |
| Definición de caída como intento fallido, usada en una ventana en vivo posterior. La muestra de 2025 no se reclasifica. | 10.000 |
| Página en español que repite `docs/VERIFY.md` y no añade números | 12.000 |
| Notas de un segundo portal público, solo trabajo de escritorio | 8.000 |
| Coordinación y contingencia, 12 meses | 8.000 |
| **Total** | **75.000** |

No hay servidores de nube en esta tabla. Mantener el repositorio es tiempo del mantenedor, no un segundo presupuesto (`docs/operations/BUS_FACTOR.md`).

## ¿Quién se beneficiaría?

Periodistas y observadores electorales que ya leen un canal público de resultados y pueden clonar un repositorio git. No hicimos un estudio de usuarios, y no decimos que la herramienta beneficia a todo el mundo. El usuario concreto de hoy es quien comprueba los 64 archivos de Honduras con `docs/VERIFY.md`. Un usuario posterior es quien apunte el mismo registro de intentos a otro portal JSON público.

## ¿Dónde están los usuarios o audiencias previstos?

América Latina y el Caribe, en la lista regional M49 de Naciones Unidas a la que OTF dice estar pasando. El primer canal es el JSON presidencial público de Honduras. El lugar de residencia del mantenedor no está dicho en este repositorio.

## ¿Cuál es su nombre?

VectisDev

El formulario permite un seudónimo. Esa es la identidad pública (`CITATION.cff`). El nombre legal se divulga solo al financiador al contratar y no se escribe en este repositorio.

## ¿Qué correo debemos usar para contactarle?

vectisdev26@proton.me

Es la dirección en `.github/SECURITY.md`, `CITATION.cff` y `pyproject.toml`.

## ¿Por qué usted y su equipo son las personas adecuadas?

El repositorio es la evidencia, no un currículum. Un tercero puede correr `make replay-offline` (`docs/VERIFY.md`). El CI de la rama por defecto incluye ese job y una imagen de contenedor fijada (`.github/workflows/ci.yml`, `Dockerfile.demo`). El merge que llevó esa imagen a la rama por defecto es el pull request 796; el CI de ese merge salió en verde (ejecución 42423340598 de GitHub Actions).

Hay un solo mantenedor y ningún socio universitario (`docs/operations/BUS_FACTOR.md`, `docs/legal/GOVERNANCE.md`). Quien solicita es esa persona. OTF puede contratar con una persona. No hace falta un patrocinador fiscal. Uno puede considerarse más adelante. No hay ninguno.

## Fecha de inicio propuesta

No aplica. OTF pregunta esto solo para encuentros comunitarios, y solo para una fecha al menos 90 días después del envío. Este proyecto es desarrollo tecnológico.
