"""Deprecated alias for :mod:`vigil` (the package was renamed with the project).

``import centinel`` and ``from centinel.core import ...`` keep working: every
``centinel.*`` module resolves to the same module object as ``vigil.*``, so
state, monkeypatching and ``isinstance`` checks are shared. Update imports to
``vigil``; this alias will be removed in a future major release.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import warnings

_OLD, _NEW = "centinel", "vigil"


class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Resolve ``centinel.x.y`` to the already-importable ``vigil.x.y``."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(_OLD + "."):
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return importlib.import_module(_NEW + spec.name[len(_OLD):])

    def exec_module(self, module):
        """The target module is already executed by its own import."""


warnings.warn(
    "The 'centinel' package was renamed to 'vigil'; please update your imports.",
    DeprecationWarning,
    stacklevel=2,
)
if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())
sys.modules[__name__] = importlib.import_module(_NEW)
