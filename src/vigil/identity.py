"""How a fetch names itself. The default is one open string.

The version matches pyproject.toml. Stealth is not used to fetch a source.
"""

from __future__ import annotations

VERSION = "0.1.0"
REPOSITORY = "https://github.com/VectisDev/Vigil"
USER_AGENT = f"VIGIL/{VERSION} (+{REPOSITORY})"
STEALTH_FOR_SOURCE = False
