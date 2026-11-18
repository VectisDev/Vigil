"""VIGIL se identifica ante lo que observa, y el cable lo respalda.

VIGIL identifies itself to what it observes, and the wire backs it up.

La premisa del proyecto es que no hace falta confiar en nadie: VIGIL no pide
permiso a la autoridad electoral para observar lo que esa autoridad publica.
Pero no pedir permiso no es lo mismo que esconderse, y la diferencia es justo
lo que separa este proyecto de un raspador cualquiera.

Hasta ahora esa diferencia vivía en el discurso y no en el código. El
capturador le preguntaba a robots.txt si `Vigil-Engine/1.0` podía entrar, y
después entraba sin presentar ese nombre: la sesión salía con la cabecera por
defecto de la librería. Pedir permiso con un nombre que no se usa no es
identificarse, y ninguna prueba lo detectaba porque no existía ninguna prueba
de robots.txt ni de la cabecera emitida.

Lo que fijan estas pruebas, por orden de importancia:

1. **El nombre que se consulta es el que viaja.** No por disciplina, sino
   porque es la misma constante — `vigil.identity.VIGIL_USER_AGENT`.
2. **Un `Disallow` dirigido a VIGIL detiene la captura de esa fuente.** Si un
   portal público decide excluir a un observador identificado, VIGIL para. Esa
   decisión queda documentada con fecha del lado del portal, que es
   exactamente el punto: la negativa es un hallazgo, no un obstáculo a sortear.
3. **Un robots.txt ausente o roto no bloquea nada.** Lo contrario permitiría
   cegar al observador borrando un archivo.
4. **La rotación de identidad no puede volver.** Había cuatro motores de
   rotación en el árbol y documentación que presumía de ellos. El candado del
   final falla si reaparece cualquiera.

English: the project's premise is that nobody needs to be trusted -- VIGIL
does not ask the electoral authority for permission to observe what that
authority publishes. But not asking permission is not the same as hiding, and
that difference is what separates this from an ordinary scraper. Until now the
difference lived in prose, not in code: the collector asked robots.txt about
`Vigil-Engine/1.0` and then fetched without presenting that name. These pin
that the name asked about is the name sent, that a Disallow aimed at VIGIL
stops the capture, that a missing robots.txt blocks nothing, and that identity
rotation cannot come back.
"""

from __future__ import annotations

import http.server
import json
import re
import socket
import threading
from pathlib import Path

import pytest
import requests

from vigil.identity import VIGIL_USER_AGENT, request_headers

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/VectisDev/Vigil"


# ── la identidad misma ────────────────────────────────────────────────────────


def test_the_name_asked_about_is_the_name_sent() -> None:
    """Preguntar por un nombre y entrar con otro no es identificarse."""
    import scripts.download_and_hash as capturador

    fuente = Path(capturador.__file__).read_text(encoding="utf-8")
    assert "rp.can_fetch(VIGIL_USER_AGENT" in fuente, (
        "robots.txt debe consultarse con la MISMA constante que viaja en la "
        "petición. Si se consulta con otra cadena, VIGIL pide permiso como "
        "alguien que luego no se presenta."
    )
    assert request_headers()["User-Agent"] == VIGIL_USER_AGENT


def test_the_identity_names_the_project_and_where_to_find_it() -> None:
    """Un rastreador que da la cara deja una vía de contacto."""
    assert "Vigil-Engine" in VIGIL_USER_AGENT
    assert REPO_URL in VIGIL_USER_AGENT, (
        "la identidad lleva la URL del repositorio para que quien reciba la "
        "petición pueda leer el código y escribirnos — y para que bloquearnos "
        "sea fácil, que es deliberado"
    )


def test_the_identity_does_not_impersonate_a_browser() -> None:
    """Fingir ser una persona con un navegador es lo contrario de esto."""
    for marca in ("Chrome/", "Safari/", "Firefox/", "Gecko/", "Windows NT", "Macintosh"):
        assert marca not in VIGIL_USER_AGENT, f"la identidad finge un navegador: {marca}"


def test_a_caller_cannot_replace_the_identity() -> None:
    """La identidad se escribe la última: ningún llamador la sustituye."""
    headers = request_headers({"User-Agent": "OtraCosa/9.9", "Accept": "text/csv"})
    assert headers["User-Agent"] == VIGIL_USER_AGENT
    assert headers["Accept"] == "text/csv", "lo demás sí debe poder ajustarse"


# ── lo que de verdad sale al cable ────────────────────────────────────────────


# `conftest.py` corta toda conexión de red en las pruebas, y hace bien: una
# suite que sale a internet no es reproducible. Pero estas pruebas necesitan
# medir qué cabecera llega de verdad a un servidor, y eso solo se puede ver
# hablando con uno. La salida es permitir el bucle local y nada más: se captura
# la función real antes de que el fixture global la sustituya, y se vuelve a
# poner envuelta en una guarda que rechaza cualquier destino que no sea esta
# misma máquina. El candado general sigue intacto fuera de aquí.
# English: conftest kills all network access in tests, rightly so. These tests
# need to see which header actually reaches a server, so they re-enable the
# loopback interface and nothing else.
_CONECTA = socket.socket.connect
_CREA_CONEXION = socket.create_connection
_BUCLE_LOCAL = {"127.0.0.1", "::1", "localhost"}


def _exige_bucle_local(direccion: object) -> None:
    host = direccion[0] if isinstance(direccion, tuple) else direccion
    if str(host) not in _BUCLE_LOCAL:
        raise RuntimeError("Network access is disabled during tests.")


@pytest.fixture
def portal(monkeypatch: pytest.MonkeyPatch):
    """Un portal de prueba que anota qué identidad recibe y sirve robots.txt."""

    def conecta(sock, direccion, *args, **kwargs):  # type: ignore[no-untyped-def]
        _exige_bucle_local(direccion)
        return _CONECTA(sock, direccion, *args, **kwargs)

    def crea_conexion(direccion, *args, **kwargs):  # type: ignore[no-untyped-def]
        _exige_bucle_local(direccion)
        return _CREA_CONEXION(direccion, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", conecta, raising=True)
    monkeypatch.setattr(socket, "create_connection", crea_conexion, raising=True)

    estado: dict[str, object] = {"robots": None, "recibidos": []}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:  # silencio
            pass

        def do_GET(self) -> None:  # noqa: N802 - lo nombra http.server
            if self.path == "/robots.txt":
                if estado["robots"] is None:
                    self.send_error(404)
                    return
                cuerpo = str(estado["robots"]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            estado["recibidos"].append(self.headers.get("User-Agent"))  # type: ignore[union-attr]
            cuerpo = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

    with socket.socket() as sonda:
        sonda.bind(("127.0.0.1", 0))
        puerto = sonda.getsockname()[1]
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    estado["base"] = f"http://127.0.0.1:{puerto}"
    try:
        yield estado
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_every_request_and_every_retry_carries_the_identity(portal) -> None:
    """La identidad vive en la sesión, así que no se pierde en un reintento."""
    sesion = requests.Session()
    sesion.headers.update(request_headers())
    for _ in range(3):
        sesion.get(f"{portal['base']}/datos", timeout=5)

    recibidos = set(portal["recibidos"])
    assert recibidos == {VIGIL_USER_AGENT}, (
        f"el portal recibió {recibidos}. Si una petición sale sin la identidad, "
        "o con otra, la afirmación «me identifico» deja de ser cierta justo "
        "donde se puede comprobar."
    )


def test_a_disallow_aimed_at_vigil_stops_the_capture(portal) -> None:
    """Si el portal nos excluye, paramos. Esa negativa es el hallazgo."""
    import scripts.download_and_hash as capturador

    capturador._ROBOTS_CACHE.clear()
    portal["robots"] = "User-agent: Vigil-Engine\nDisallow: /\n"
    assert capturador._check_robots_allowed(f"{portal['base']}/datos") is False


def test_a_disallow_aimed_at_someone_else_does_not_apply_to_us(portal) -> None:
    """Una regla para otro agente no nos ciega."""
    import scripts.download_and_hash as capturador

    capturador._ROBOTS_CACHE.clear()
    portal["robots"] = "User-agent: AlgunOtroBot\nDisallow: /\n"
    assert capturador._check_robots_allowed(f"{portal['base']}/datos") is True


def test_a_missing_robots_txt_does_not_block_the_capture(portal) -> None:
    """Lo contrario dejaría cegar al observador borrando un archivo."""
    import scripts.download_and_hash as capturador

    capturador._ROBOTS_CACHE.clear()
    portal["robots"] = None
    assert capturador._check_robots_allowed(f"{portal['base']}/datos") is True


# ── el candado: la rotación no puede volver ───────────────────────────────────

# Un navegador de verdad. Que VIGIL diga esto es suplantación, no identidad.
FINGE_NAVEGADOR = re.compile(r"Chrome/\d|Safari/\d|Firefox/\d|Gecko/\d|Mozilla/5\.0 \((Windows|Macintosh|X11)")

# Borrar la marca de automatización del navegador: ocultación activa.
OCULTA_AUTOMATIZACION = re.compile(r"navigator\.webdriver")

# Una lista de identidades es una lista de máscaras.
POOL_DE_IDENTIDADES = re.compile(r"user_agents?_(list|pool)\s*[:=]", re.IGNORECASE)

# Elegir cabecera al azar es exactamente lo que se quitó.
IDENTIDAD_AL_AZAR = re.compile(
    r"(random|secrets)\.choice\([^)]*(user_agent|referer|accept_language|headers)",
    re.IGNORECASE,
)

ARBOLES = ("src", "scripts", "vigil_engine")


def _fuentes():
    for arbol in ARBOLES:
        for ruta in sorted((REPO_ROOT / arbol).rglob("*.py")):
            if "__pycache__" in ruta.parts:
                continue
            yield ruta
    for nombre in ("advanced_security_config.yaml", "config.yaml"):
        ruta = REPO_ROOT / "command_center" / nombre
        if ruta.exists():
            yield ruta


@pytest.mark.parametrize(
    "patron,queja",
    [
        (FINGE_NAVEGADOR, "finge ser un navegador"),
        (OCULTA_AUTOMATIZACION, "oculta que es automatización"),
        (POOL_DE_IDENTIDADES, "declara un conjunto de identidades"),
        (IDENTIDAD_AL_AZAR, "elige una cabecera al azar"),
    ],
    ids=["navegador", "sigilo", "pool", "azar"],
)
def test_no_identity_rotation_comes_back(patron: re.Pattern[str], queja: str) -> None:
    """Se quitaron cuatro motores de rotación. Este candado impide el regreso.

    Ninguno defendía de nada: quince identidades que todas dicen `Centinel-*`
    caen con una sola regla, y seis proxies de centro de datos caen por ASN. Lo
    que sí hacían era contradecir la premisa del proyecto en su propio árbol.

    English: four rotation engines were removed. None of them defended against
    anything -- fifteen identities that all say `Centinel-*` fall to one rule,
    and six datacenter proxies fall by ASN. What they did do was contradict the
    project's premise inside its own tree.
    """
    culpables = []
    for ruta in _fuentes():
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if patron.search(linea):
                culpables.append(f"{ruta.relative_to(REPO_ROOT)}:{numero}")

    assert not culpables, (
        f"esto {queja}, y VIGIL audita identificándose: {culpables}. "
        "Si hace falta, el porqué está en docs/NO-EVASION.md."
    )
