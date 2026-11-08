"""Freedom with visible responsibility.

Vigil does not forbid a faster pace. The default stays respectful.
A faster pace is applied only after a public signed commit accepts
the consequences. The signature is a key, not a legal name.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

MAX_REQUESTS_PER_HOUR = 480
MIN_INTERVAL_SECONDS = 1.0
MAX_BURST = 8

STATEMENTS = (
    "I accept full responsibility for the consequences of requests above the respectful pace, including load on the source comparable to a denial of service.",
    "Acepto toda la responsabilidad por las consecuencias de peticiones por encima del ritmo respetuoso, incluida una carga sobre la fuente comparable a una denegación de servicio.",
)


def within_lock(requests_per_hour: float, interval_seconds: float, burst: float) -> bool:
    return (
        float(requests_per_hour) <= MAX_REQUESTS_PER_HOUR
        and float(interval_seconds) >= MIN_INTERVAL_SECONDS
        and float(burst) <= MAX_BURST
    )


def clamp(requests_per_hour: float, interval_seconds: float, burst: float) -> tuple[float, float, float]:
    return (
        min(float(requests_per_hour), MAX_REQUESTS_PER_HOUR),
        max(float(interval_seconds), MIN_INTERVAL_SECONDS),
        min(float(burst), MAX_BURST),
    )


def statement_present(text: str) -> bool:
    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return False
    if not isinstance(loaded, dict):
        return False
    value = str(loaded.get("responsibility", "")).strip()
    return value in STATEMENTS


def apply_pace(
    requests_per_hour: float,
    interval_seconds: float,
    burst: float,
    override_text: str | None,
    signed: bool,
) -> tuple[float, float, float]:
    """Return the pace a node may use.

    Inside the lock, the numbers pass through. Past the lock, they pass
    only when the statement is present and the commit is signed.
    """
    if within_lock(requests_per_hour, interval_seconds, burst):
        return (float(requests_per_hour), float(interval_seconds), float(burst))
    if override_text and statement_present(override_text) and signed:
        return (float(requests_per_hour), float(interval_seconds), float(burst))
    return clamp(requests_per_hour, interval_seconds, burst)


def override_is_refused(text: str | None, signed: bool) -> bool:
    """True when a file tries to go past the lock without a signed acceptance."""
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return True
    if not isinstance(loaded, dict):
        return True
    pace = (
        float(loaded.get("max_requests_per_hour", MAX_REQUESTS_PER_HOUR)),
        float(loaded.get("min_interval_seconds", MIN_INTERVAL_SECONDS)),
        float(loaded.get("max_burst", MAX_BURST)),
    )
    if within_lock(*pace):
        return False
    return not (statement_present(text) and signed)


def commit_has_signature(commit_text: str) -> bool:
    return "\ngpgsig " in f"\n{commit_text}" or commit_text.startswith("gpgsig ")


def read_override(root: Path) -> str | None:
    path = root / "rate_override.yml"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def git_override_is_signed(root: Path) -> bool:
    """True when the latest commit that touched rate_override.yml carries a signature."""
    path = root / "rate_override.yml"
    if not path.is_file():
        return False
    listed = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "rate_override.yml"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    sha = listed.stdout.strip()
    if not sha:
        return False
    shown = subprocess.run(
        ["git", "cat-file", "commit", sha],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return shown.returncode == 0 and commit_has_signature(shown.stdout)
