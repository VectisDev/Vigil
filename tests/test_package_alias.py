"""Backward compatibility of the pre-rename package names (centinel -> vigil)."""

from __future__ import annotations

import importlib
import sys

import pytest


def test_centinel_alias_resolves_to_vigil_modules():
    sys.modules.pop("centinel", None)  # re-run the shim so its warning is observable
    with pytest.warns(DeprecationWarning):
        centinel = importlib.import_module("centinel")
    vigil = importlib.import_module("vigil")
    assert centinel is vigil

    old = importlib.import_module("centinel.paths")
    new = importlib.import_module("vigil.paths")
    assert old is new


def test_centinel_alias_supports_from_imports():
    from centinel.paths import iter_all_hashes
    from vigil.paths import iter_all_hashes as current

    assert iter_all_hashes is current


def test_centinel_engine_alias_resolves_to_vigil_engine():
    sys.modules.pop("centinel_engine", None)
    with pytest.warns(DeprecationWarning):
        old_pkg = importlib.import_module("centinel_engine")
    assert old_pkg is importlib.import_module("vigil_engine")
    assert importlib.import_module("centinel_engine.hash_chain") is importlib.import_module("vigil_engine.hash_chain")
