"""Deprecated alias for :mod:`vigil_engine` (the package was renamed with the project).

``import centinel_engine`` and ``from centinel_engine.x import ...`` keep working:
every ``centinel_engine.*`` module resolves to the same module object as
``vigil_engine.*``. Update imports to ``vigil_engine``; this alias will be removed
in a future major release.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import warnings

_OLD, _NEW = "centinel_engine", "vigil_engine"


class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Resolve ``centinel_engine.x`` to the already-importable ``vigil_engine.x``."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(_OLD + "."):
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return importlib.import_module(_NEW + spec.name[len(_OLD):])

    def exec_module(self, module):
        """The target module is already executed by its own import."""


warnings.warn(
    "The 'centinel_engine' package was renamed to 'vigil_engine'; please update your imports.",
    DeprecationWarning,
    stacklevel=2,
)
if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())
sys.modules[__name__] = importlib.import_module(_NEW)
