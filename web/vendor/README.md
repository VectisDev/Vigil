# Dependencias alojadas en el repositorio

Las bibliotecas de terceros viven aquí y no en un CDN.

Un `<script src="https://cdn...">` en el panel significa que un tercero puede
ver la IP de cada visitante y, si ese tercero se ve comprometido o cambia el
archivo, ejecutar código en el origen del panel. Para un proyecto cuya premisa
es que cualquiera pueda verificar lo que corre, una dependencia que puede
cambiar bajo los pies sin dejar rastro en el repositorio es lo contrario de
verificable.

Alojarlas aquí también hace que el panel funcione sin conexión, que es el caso
de uso de un verificador.

## Contenido

| Archivo | Versión | Origen | Licencia |
|---|---|---|---|
| `js-yaml-4.1.0.min.js` | 4.1.0 | paquete npm `js-yaml` | MIT (`js-yaml-4.1.0.LICENSE`) |

Para actualizar: `npm pack js-yaml@<version>`, copiar `dist/js-yaml.min.js` y
la licencia, y cambiar la referencia en `web/ops/index.html`.

---

# Repository-hosted dependencies

Third-party libraries live here rather than on a CDN.

A `<script src="https://cdn...">` lets a third party see every visitor's IP
and, if compromised, run code in the panel's origin. For a project whose
premise is that anyone can verify what runs, a dependency that can change
underfoot without a trace in the repository is the opposite of verifiable.

Hosting them here also makes the panel work offline, which is a verifier's
use case.
