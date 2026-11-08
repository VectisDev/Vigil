"""The approved audit fixes stay true."""

from __future__ import annotations

import re
from pathlib import Path

from vigil.identity import USER_AGENT, user_agent
from vigil.pace import github_verified, override_files
from vigil.swarm.governance import faulty_bound, quorum_size
from vigil.swarm.rooms import CODE_LENGTH, code_grants_trust, expiry, generate_room_code, is_current

ROOT = Path(__file__).resolve().parents[1]
BANNED_HOSTS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "unpkg.com",
    "ajax.googleapis.com",
)
ALLOWED_HOSTS = {"github.com", "vectisdev.github.io", "www.w3.org"}


def test_custom_mode_cannot_pass_the_ceiling() -> None:
    from vigil_engine.rate_limiter import HARD_CEILING_MIN_INTERVAL, TokenBucketRateLimiter

    assert HARD_CEILING_MIN_INTERVAL == 1.0
    limiter = TokenBucketRateLimiter(enforce_ceiling=True)
    limiter.reconfigure(mode="custom", max_requests_per_hour=9000, min_interval=0.1, burst=100)
    assert limiter.max_requests_per_hour <= 480
    assert limiter.min_interval >= 1.0
    assert limiter.burst <= 8
    source = (ROOT / "vigil_engine" / "rate_limiter.py").read_text(encoding="utf-8")
    assert 'self._mode != "custom"' not in source
    assert "random.uniform(0.0, 3.2)" not in source


def test_an_unverified_override_does_not_open_the_ceiling() -> None:
    assert github_verified("rate_override.yml") is False
    assert override_files(ROOT) == []
    text = (ROOT / "scripts" / "check_rate_override.py").read_text(encoding="utf-8")
    assert "verification.verified" in text
    for name in ("poller-A.yml", "poller-B.yml", "scheduler.yml", "pipeline.yml", "audit.yml"):
        workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "scripts/check_rate_override.py" in workflow


def test_one_user_agent_names_the_key_id() -> None:
    assert USER_AGENT == "Vigil/0.1.0 (+https://github.com/VectisDev/Vigil; key:unset)"
    assert user_agent("S0N") == "Vigil/0.1.0 (+https://github.com/VectisDev/Vigil; key:S0N)"
    collector = (ROOT / "scripts" / "collector.py").read_text(encoding="utf-8")
    assert "random.choice(user_agents)" not in collector
    headers = (ROOT / "scripts" / "download_and_hash.py").read_text(encoding="utf-8")
    assert "Referer" not in headers
    proxies = (ROOT / "config" / "prod" / "proxies.yaml").read_text(encoding="utf-8")
    assert "proxies: []" in proxies
    assert "socks5" not in proxies
    assert "httpbin.org" not in proxies


def test_room_codes_are_generated_and_do_not_grant_trust() -> None:
    code = generate_room_code()
    assert len(code) >= 12
    assert len(code) == CODE_LENGTH
    assert code_grants_trust() is False
    opened = expiry(1000.0, ttl=10)
    assert is_current(opened, 1009.0) is True
    assert is_current(opened, 1010.0) is False
    route = (ROOT / "src" / "vigil" / "api" / "routes" / "swarm.py").read_text(encoding="utf-8")
    assert "authorize_sala_url" not in route
    assert "4-32 hex" not in route
    assert quorum_size(12) >= 2 * faulty_bound(12) + 1


def test_public_pages_do_not_load_an_external_domain() -> None:
    web = ROOT / "web"
    problems: list[str] = []
    resource = re.compile(
        r"""<(?:script|link)\b[^>]*(?:src|href)=["']https?://([^/"']+)""",
        re.IGNORECASE,
    )
    for path in web.rglob("*"):
        if path.suffix.lower() not in {".html", ".js", ".css", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for banned in BANNED_HOSTS:
            if banned in lowered:
                problems.append(f"{path.relative_to(ROOT)}: {banned}")
        for match in resource.finditer(text):
            name = match.group(1).split(":")[0].lower()
            if name not in ALLOWED_HOSTS:
                problems.append(f"{path.relative_to(ROOT)}: {name}")
    assert problems == []


def test_the_public_site_does_not_keep_a_key() -> None:
    web = ROOT / "web"
    for path in web.rglob("*"):
        if path.suffix.lower() not in {".html", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "centinel_admin_key" not in text
        assert "sessionStorage" not in text
        assert "#key" not in text
    policy = (ROOT / ".github" / "SECURITY.md").read_text(encoding="utf-8")
    assert "d32970cf1" in policy
    assert "invalid" in policy
    assert "not a security boundary" in policy
