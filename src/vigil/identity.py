"""How a fetch names itself. One string, including the public key id.

The version matches pyproject.toml. The key id is the public id of the
operator key (the audit's S0N slot). This repository has no issued key,
so the default id is ``unset``. An operator sets ``VIGIL_KEY_ID`` to the
fingerprint they handed out. Stealth is not used to fetch a source.
"""

from __future__ import annotations

import os

VERSION = "0.1.0"
REPOSITORY = "https://github.com/VectisDev/Vigil"
STEALTH_FOR_SOURCE = False


def user_agent(key_id: str | None = None) -> str:
    """The only User-Agent. ``key_id`` is a public id, never the secret."""
    if key_id is None:
        key_id = os.environ.get("VIGIL_KEY_ID", "")
    ident = str(key_id).strip() or "unset"
    return f"Vigil/{VERSION} (+{REPOSITORY}; key:{ident})"


USER_AGENT = user_agent()
