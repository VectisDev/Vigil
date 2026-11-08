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


def override_key_id(text: str | None) -> str:
    if not text:
        return ""
    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return ""
    if not isinstance(loaded, dict):
        return ""
    return str(loaded.get("key_id") or "").strip()


def apply_pace(
    requests_per_hour: float,
    interval_seconds: float,
    burst: float,
    override_text: str | None,
    signed: bool,
    key_active: bool = False,
) -> tuple[float, float, float]:
    """Return the pace a node may use.

    Inside the lock, the numbers pass through. Past the lock, they pass
    only when the statement is present, the commit is signed, and the
    named ops key id is active.
    """
    if within_lock(requests_per_hour, interval_seconds, burst):
        return (float(requests_per_hour), float(interval_seconds), float(burst))
    if override_text and statement_present(override_text) and signed and key_active and override_key_id(override_text):
        return (float(requests_per_hour), float(interval_seconds), float(burst))
    return clamp(requests_per_hour, interval_seconds, burst)


def override_is_refused(text: str | None, signed: bool, key_active: bool = False) -> bool:
    """True when a file claims a faster pace, or an ops action, without a signed active key id."""
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
    names_an_action = bool(str(loaded.get("action") or "").strip())
    past = not within_lock(*pace)
    if not past and not names_an_action:
        return False
    kid = str(loaded.get("key_id") or "").strip()
    if past:
        return not (statement_present(text) and signed and key_active and bool(kid))
    return not (signed and key_active and bool(kid))


def commit_has_signature(commit_text: str) -> bool:
    return "\ngpgsig " in f"\n{commit_text}" or commit_text.startswith("gpgsig ")


def override_files(root: Path) -> list[Path]:
    """Files that can carry a pace override.

    The root file is ``rate_override.yml``. A fork may also put one YAML
    file per acceptance under ``audit/ceiling-unlock/``.
    """
    found: list[Path] = []
    primary = root / "rate_override.yml"
    if primary.is_file():
        found.append(primary)
    folder = root / "audit" / "ceiling-unlock"
    if folder.is_dir():
        found.extend(sorted(path for path in folder.glob("*.yml") if path.is_file()))
    return found


def read_override(root: Path) -> str | None:
    files = override_files(root)
    if not files:
        return None
    return files[0].read_text(encoding="utf-8")


def github_verified(rel: str) -> bool:
    """True only when GitHub reports verification.verified for the commit that last touched ``rel``."""
    import os

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo or not rel:
        return False
    env = {**os.environ, "GH_TOKEN": token}
    listed = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits?path={rel}&per_page=1", "--jq", ".[0].sha"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    sha = listed.stdout.strip()
    if listed.returncode != 0 or not sha or sha == "null":
        return False
    asked = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.verification.verified"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return asked.returncode == 0 and asked.stdout.strip() == "true"


def verified_override_text(root: Path, key_active) -> tuple[bool, str | None]:
    """Return ``(ok, text)``.

    ``ok`` is false when a file tries to pass the lock without a GitHub-verified
    commit, the responsibility line, and an active key id. ``text`` is the
    accepted file that goes past the lock, or None when the ceiling stays.
    """
    chosen: str | None = None
    for path in override_files(root):
        text = path.read_text(encoding="utf-8")
        if not override_is_refused(text, False, False):
            continue
        rel = path.relative_to(root).as_posix()
        active = bool(key_active(override_key_id(text)))
        if override_is_refused(text, github_verified(rel), key_active=active):
            return False, None
        chosen = text
    return True, chosen


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
