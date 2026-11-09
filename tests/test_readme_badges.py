"""Las insignias del README dicen algo cierto, y el rojo queda reservado.

The README badges state something true, and red stays reserved.

Las cuatro insignias eran imágenes estáticas de shields.io con el color escrito
a mano. La de CI decía `badge/CI-main-D7262E`: un rectángulo rojo fijo que no
consultaba nada. En un README de GitHub una insignia roja de CI significa una
sola cosa —la rama está rota— así que la cabecera del proyecto anunciaba un
fallo permanente que no existía, y una verdadera habría sido indistinguible.

Dos invariantes, y la segunda es la que importa:

1. La insignia de CI apunta al punto final de estado del propio GitHub, que se
   pone verde o rojo según la última ejecución real. Es de primera mano: no
   pasa por un tercero que pueda limitar la tasa o caerse, y para un proyecto
   cuya premisa es no tener que confiar en intermediarios eso no es un detalle.
2. Ninguna insignia estática se pinta del rojo de marca. El rojo sirve para
   avisar; si decora, deja de avisar.

English: all four badges were static shields.io images with the colour written
by hand, and the CI one was a fixed red rectangle that queried nothing. In a
GitHub README a red CI badge means exactly one thing -- the branch is broken --
so the project header announced a permanent failure that did not exist, and a
real one would have been indistinguishable. These pin that the CI badge is
GitHub's own live status endpoint, and that no static badge wears the brand red.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
READMES = ("README.md", "README.en.md")

# El rojo de marca. Una insignia que lo lleve se lee como una alarma.
ROJO_DE_MARCA = re.compile(r"D7262E", re.IGNORECASE)

# `img.shields.io/badge/...` es el generador ESTÁTICO: lo que va en la URL es
# lo que se dibuja. Cualquier otra ruta de shields consulta algo.
SHIELDS_ESTATICA = re.compile(r"img\.shields\.io/badge/")

# El punto final de estado de GitHub Actions.
INSIGNIA_VIVA = re.compile(r"github\.com/[^/\s\"]+/[^/\s\"]+/actions/workflows/([^/\s\"]+)/badge\.svg")

IMAGEN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC = re.compile(r"src=\"([^\"]+)\"")


def _cabecera(nombre: str) -> str:
    """El bloque de insignias: lo que hay antes del primer encabezado `##`."""
    texto = (REPO_ROOT / nombre).read_text(encoding="utf-8")
    corte = texto.find("\n## ")
    return texto if corte < 0 else texto[:corte]


def _insignias(nombre: str) -> list[str]:
    fuentes = []
    for etiqueta in IMAGEN.findall(_cabecera(nombre)):
        encontrado = SRC.search(etiqueta)
        if not encontrado:
            continue
        fuente = encontrado.group(1)
        if "shields.io" in fuente or "badge.svg" in fuente:
            fuentes.append(fuente)
    return fuentes


@pytest.mark.parametrize("nombre", READMES)
def test_la_insignia_de_ci_consulta_el_estado_real(nombre: str) -> None:
    """Una insignia de CI que no consulta nada es una afirmación sin respaldo."""
    fuentes = _insignias(nombre)
    vivas = [f for f in fuentes if INSIGNIA_VIVA.search(f)]
    assert vivas, (
        f"{nombre} no lleva ninguna insignia de estado real. Una imagen estática "
        "de shields.io con el color escrito a mano no mide la rama: dice siempre "
        "lo mismo, y en rojo anuncia un fallo que puede no existir."
    )
    for fuente in vivas:
        assert not SHIELDS_ESTATICA.search(fuente), f"{nombre}: {fuente} sigue siendo estática"


@pytest.mark.parametrize("nombre", READMES)
def test_la_insignia_de_ci_nombra_un_flujo_que_corre_en_main(nombre: str) -> None:
    """Si el flujo no se dispara en `main`, la insignia sale «no status»."""
    for fuente in _insignias(nombre):
        encontrado = INSIGNIA_VIVA.search(fuente)
        if not encontrado:
            continue
        archivo = REPO_ROOT / ".github" / "workflows" / encontrado.group(1)
        assert archivo.exists(), f"{nombre}: la insignia nombra {archivo.name}, que no existe"

        flujo = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        # `on` sin comillas es el booleano True en YAML 1.1.
        disparadores = flujo.get("on", flujo.get(True, {})) or {}
        ramas = (disparadores.get("push") or {}).get("branches") or []
        assert "main" in ramas, f"{archivo.name} no se dispara al empujar a main: la insignia no mediría nada"

        assert "?branch=main" in fuente, f"{nombre}: la insignia no fija la rama, así que mostraría cualquiera"


@pytest.mark.parametrize("nombre", READMES)
def test_ninguna_insignia_estatica_usa_el_rojo_de_aviso(nombre: str) -> None:
    """El rojo avisa. Si además decora, deja de avisar."""
    pintadas = [f for f in _insignias(nombre) if SHIELDS_ESTATICA.search(f) and ROJO_DE_MARCA.search(f)]
    assert not pintadas, (
        f"{nombre}: estas insignias estáticas llevan el rojo de marca y no pueden "
        f"cambiar de estado, así que avisan de nada: {pintadas}. El rojo queda para "
        "la insignia de CI, que es la única que se pone roja por un motivo."
    )


def test_los_dos_readmes_llevan_la_misma_fila() -> None:
    """Un lector en inglés no debe ver un estado distinto del que ve uno en español."""
    conteos = {nombre: len(_insignias(nombre)) for nombre in READMES}
    assert len(set(conteos.values())) == 1, f"las cabeceras no coinciden: {conteos}"

    flujos = set()
    for nombre in READMES:
        for fuente in _insignias(nombre):
            encontrado = INSIGNIA_VIVA.search(fuente)
            if encontrado:
                flujos.add(encontrado.group(1))
    assert len(flujos) == 1, f"cada README mide un flujo distinto: {flujos}"
