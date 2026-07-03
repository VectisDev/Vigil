# 20260703 — Pasada de minimización "ponytail" en web/ops

2026-07-03

Le pedí a Claude que le echara un vistazo a `DietrichGebert/ponytail`, un plugin que le mete
disciplina a un agente de IA para que no escriba código de más: antes de agregar algo, que se
pregunte si hace falta, si ya existe, si lo resuelve el stdlib, si cabe en una línea. La idea
era usar esa misma lógica sobre Vigil para recortar grasa sin perder capacidades.

Primer hallazgo importante: no se puede instalar el plugin dentro de una sesión de agente
remoto (`/plugin install` es un comando de la CLI interactiva, no algo invocable desde acá).
Así que en vez de instalarlo, aplicamos la misma filosofía a mano — auditoría + refactor,
como si fuera `/ponytail-audit`.

Segundo hallazgo: el repo es mucho más grande de lo que documenta el CLAUDE.md por sí solo.
Ahí solo se detalla `web/ops/`, pero hay ~36k líneas de Python en `src/centinel` (motor
forense, criptografía, custodia de evidencia) y otras ~16k en `scripts/`. Intentar una pasada
de minimización a ciegas sobre esa capa es peligroso — un cambio mal calibrado en
`hashchain.py` o `rules_engine.py` puede romper garantías que necesitamos para que
observadores internacionales confíen en el sistema. Dividimos el trabajo en dos fases: refactor
real en `web/ops/`, solo auditoría (sin tocar código) en el núcleo forense/criptográfico.

## Lo que se recortó en `web/ops/`

Un escaneo cruzado de nombres de función contra todos los call sites en los 5 archivos JS +
el HTML encontró 8 funciones completamente huérfanas (cero llamadores, ni siquiera desde
`onclick=` en el HTML):

- `_b64e` (helper de base64 encode que quedó del lado de encriptar, pero el flujo real solo
  usa `_b64d` para desencriptar)
- `copyLog`, `downloadTxt`, `_logTxtContent` (un mini-subsistema de descarga de logs en texto
  plano, reemplazado en algún momento por `downloadPdf` sin que nadie borrara el anterior)
- `doEmergencia` (wrapper de una línea sobre `openEmergencyModal`, sin ningún caller)
- `getEndpointUrl`, `syncText` (helpers de configuración que dejaron de usarse)
- `requestPat` (una versión basada en Promise de abrir el modal de PAT, superada por el
  banner `#pat-onboarding` — el modal `#pat-modal` sigue en el DOM y `confirmPat`/
  `closePatModal` siguen conectados por `onclick`, así que no toqué esa parte; queda anotado
  para revisar si el modal en sí también es vestigial)

También en `ops.css` había dos cosas muertas:
un bloque `body.light-mode{...}` de 17 líneas que los propios comentarios del JS dicen que
fue reemplazado por el sistema `[data-theme]`, y un comentario roto (un `/*` que nunca cerraba
antes del siguiente `/*`, tragándose silenciosamente la etiqueta "DEV MODE VISIBILITY").

En total: ~4 funciones JS "raíz" que arrastraron 2 más en cascada al quedar huérfanas, más 20
líneas de CSS muerto. Verifiqué con Chromium headless que el panel sigue cargando sin errores
de consola (`pageerror`) tras los cambios — el auth screen renderiza igual que antes.

## Lo que se encontró pero no se tocó

En `src/centinel/core/blockchain.py` hay un módulo de 53 líneas que se auto-documenta como
DEPRECATED (violaba el principio de Costo Cero) y no tiene un solo llamador en todo el repo —
candidato limpio para borrar, pero queda fuera de esta sesión.

Más interesante: encontré funciones `sha256_file`/`merkle_root` duplicadas entre
`evidence_bundle.py` y `verify_evidence_bundle.py`. Mi primer instinto fue "esto hay que
fusionarlo", pero pensándolo mejor esa duplicación es intencional — es el mismo patrón que
`verify_chain.py`: un verificador independiente que un observador de la OEA puede auditar sin
depender del mismo código que generó la evidencia. Fusionarlo rompería el propósito de tener
una verificación independiente. Quedó documentado en
`docs/audits/audit-20260703-CoreDeadCodeFindings.md`, junto con otro par de duplicaciones
entre `bootstrap.py` y `validate_hashes.py` que sí parecen candidatas reales a consolidar en
una sesión futura dedicada a `scripts/`.

## Notas para la próxima

- `scripts/` (16k líneas, ~30 archivos) quedó sin tocar más allá de la revisión de
  duplicados — vale la pena una sesión dedicada.
- El resto de `web/` (`monitor`, `lab`, `verifier`, `replay`, etc.) tampoco se exploró en
  detalle esta vez.
- `blockchain.py` y el modal `#pat-modal`/`requestPat` (ahora sin su punto de entrada) son
  los dos candidatos de mayor confianza para la próxima pasada.
