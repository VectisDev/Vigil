"""La identidad con la que VIGIL se presenta ante lo que observa.

The identity VIGIL presents to what it observes.

VIGIL audita sin pedir permiso, pero no se esconde. Esa es la diferencia con
las herramientas que trabajan desde dentro de la autoridad electoral: no
necesitamos que nadie diga que sí, y aun así decimos quiénes somos.

Esa postura solo vale si el cable la respalda. Antes de este módulo no lo
hacía: `scripts/download_and_hash.py` le preguntaba a robots.txt si
`Vigil-Engine/1.0` podía entrar, y luego entraba sin presentar ese nombre ni
ningún otro —salía la cabecera por defecto de la librería—. Pedir permiso con
un nombre que no se usa no es identificarse.

Por eso la constante vive aquí y en un solo sitio: lo que se le pregunta a
robots.txt y lo que viaja en la petición son, por construcción, la misma
cadena. No es disciplina del programador, es que no hay dos valores que puedan
divergir.

La cadena incluye la URL del repositorio porque es la convención de un
rastreador que da la cara: quien reciba la petición puede ver qué es esto,
leer el código y escribir si algo le molesta. Y hace el bloqueo más fácil, que
es deliberado — ver `docs/NO-EVASION.md`.

English: VIGIL audits without asking permission, but it does not hide. That
stance only holds if the wire backs it, and before this module it did not: the
collector asked robots.txt whether `Vigil-Engine/1.0` could fetch a URL and
then fetched without presenting that name or any other. Asking permission
under a name you never use is not identifying yourself. The constant lives
here, in one place, so the name asked about and the name sent cannot diverge.
It carries the repository URL by convention, so whoever receives the request
can read the code and write to us -- and so that blocking us is easy, which is
deliberate. See `docs/NO-EVASION.md`.
"""

from __future__ import annotations

# El nombre, la version y el contacto. Un solo valor, un solo sitio.
# English: the name, the version and the contact. One value, one place.
VIGIL_USER_AGENT = "Vigil-Engine/1.0 (+https://github.com/VectisDev/Vigil)"


def request_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Las cabeceras de toda peticion que VIGIL hace hacia fuera.

    `extra` permite anadir lo que una fuente concreta necesite (un `Accept`
    distinto, por ejemplo) sin poder sustituir la identidad: el User-Agent se
    escribe despues, asi que gana siempre. Un llamador no puede, ni por
    descuido ni a proposito, salir con otro nombre.

    English: `extra` lets a caller add what a given source needs without being
    able to replace the identity -- the User-Agent is written last, so it
    always wins. No caller can go out under another name, by accident or
    otherwise.
    """
    headers = {"Accept": "application/json"}
    if extra:
        headers.update(extra)
    headers["User-Agent"] = VIGIL_USER_AGENT
    return headers
