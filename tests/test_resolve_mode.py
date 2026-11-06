"""El modo efectivo nunca se infiere del silencio.

The effective mode is never inferred from silence.

Estas pruebas fijan la regla que sustituye al marcador `ELECTION_CLOSED`: ante
cualquier ambigüedad el nodo cae a un modo que emite CERO peticiones, nunca a
uno que contacte una fuente ajena. El marcador anterior hacía lo contrario —su
ausencia significaba "sigue capturando"— y por eso cuatro colectores llevaban
meses disparando contra el portal de una elección ya concluida.

These tests pin the rule replacing the `ELECTION_CLOSED` marker: on any
ambiguity the node falls back to a mode issuing ZERO requests, never to one
that contacts someone else's server. The old marker did the opposite — its
absence meant "keep collecting" — which is why four collectors kept firing at
the portal of a concluded election.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".github" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from resolve_mode import load_config, resolve  # noqa: E402

NOW = datetime(2029, 11, 28, 12, 0, tzinfo=timezone.utc)


def _live(**overrides):
    """Configuración mínima que SÍ debería abrir LIVE."""
    config = {
        "mode": "LIVE",
        "source": {"active": True},
        "election": {
            "name": "Honduras General 2029",
            "window_start": (NOW - timedelta(days=2)).isoformat(),
            "window_end": (NOW + timedelta(days=2)).isoformat(),
        },
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------
# El camino feliz existe: si todo está en orden, LIVE abre.
# --------------------------------------------------------------------------


def test_live_opens_when_every_condition_holds():
    mode, reason = resolve(_live(), now=NOW)
    assert mode == "LIVE"
    assert "ventana abierta" in reason


# --------------------------------------------------------------------------
# Cada condición que falta degrada a ARMED, nunca a un LIVE parcial.
# --------------------------------------------------------------------------


def test_live_falls_back_when_source_not_active():
    """`mode: LIVE` por sí solo no basta: hay que habilitar la fuente aparte.

    English: `mode: LIVE` alone is not enough; the source must be enabled
    separately. Two deliberate acts, so a single careless edit cannot start
    sending requests to an electoral authority.
    """
    mode, reason = resolve(_live(source={"active": False}), now=NOW)
    assert mode == "ARMED"
    assert "source.active" in reason


def test_live_falls_back_before_the_window_opens():
    mode, reason = resolve(_live(), now=NOW - timedelta(days=30))
    assert mode == "ARMED"
    assert "abre el" in reason


def test_live_falls_back_after_the_window_closes():
    """Es el estado real del proyecto hoy: la elección de 2025 ya terminó."""
    mode, reason = resolve(_live(), now=NOW + timedelta(days=365))
    assert mode == "ARMED"
    assert "cerro el" in reason


def test_live_falls_back_without_window_dates():
    config = _live()
    config["election"]["window_start"] = None
    config["election"]["window_end"] = None
    mode, reason = resolve(config, now=NOW)
    assert mode == "ARMED"
    assert "sin fechas" in reason


@pytest.mark.parametrize("bad", ["2029-13-45", "mañana", "", 42])
def test_live_falls_back_on_unparseable_dates(bad):
    config = _live()
    config["election"]["window_start"] = bad
    mode, _ = resolve(config, now=NOW)
    assert mode == "ARMED"


# --------------------------------------------------------------------------
# Entradas inválidas o ausentes: siempre cero peticiones.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("declared", ["ACTIVO", "live!", "", "LIVE ", None, 7])
def test_invalid_declared_mode_never_resolves_to_live(declared):
    mode, _ = resolve({"mode": declared, "source": {"active": True}}, now=NOW)
    assert mode != "LIVE"


def test_live_with_whitespace_and_lowercase_is_accepted():
    """Un modo correcto escrito con descuido sigue siendo correcto."""
    config = _live(mode="  live  ")
    assert resolve(config, now=NOW)[0] == "LIVE"


def test_empty_config_resolves_to_replay():
    mode, _ = resolve({}, now=NOW)
    assert mode == "REPLAY"


def test_missing_file_resolves_to_replay(tmp_path):
    config = load_config(tmp_path / "no-existe.yaml")
    assert resolve(config, now=NOW)[0] == "REPLAY"


def test_unreadable_file_resolves_to_replay(tmp_path):
    """Un estado ilegible no debe habilitar la captura.

    English: an unreadable state file must never enable collection. The
    tempting alternative -- crash -- would also be wrong: a node that dies on
    a malformed file cannot report why its panel is empty.
    """
    broken = tmp_path / "mode.yaml"
    broken.write_text("mode: LIVE\n  : : esto no es yaml\n", encoding="utf-8")
    config = load_config(broken)
    assert resolve(config, now=NOW)[0] == "REPLAY"


# --------------------------------------------------------------------------
# El motivo siempre es legible: es lo que el panel muestra cuando no hay datos.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"mode": "ARMED", "election": {"name": "X"}},
        {"mode": "REPLAY", "replay": {"dataset": "tests/fixtures/hnd_2025"}},
        _live(source={"active": False}),
    ],
)
def test_reason_is_always_human_readable(config):
    _, reason = resolve(config, now=NOW)
    assert isinstance(reason, str) and len(reason) > 10


def test_the_shipped_config_resolves_to_replay():
    """El archivo real del repo no debe capturar nada por defecto."""
    config = load_config(REPO_ROOT / ".vigil" / "mode.yaml")
    mode, _ = resolve(config, now=NOW)
    assert mode == "REPLAY"
