"""Peer URL validation that keeps gossip from being used for SSRF."""

from __future__ import annotations

import pytest

from vigil.federation.gossip import _peer_url_allowed, _sl


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000",  # several nodes on one machine
        "http://192.168.1.20:8000",  # LAN swarm
        "https://10.0.0.5",
    ],
)
async def test_allows_loopback_and_private_peers(url):
    assert await _peer_url_allowed(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data",  # cloud metadata (link-local)
        "http://[fe80::1]:8000",  # IPv6 link-local
        "http://0.0.0.0:8000",  # unspecified
        "http://224.0.0.1",  # multicast
        "ftp://192.168.1.20",  # not http(s)
        "http://user:pass@192.168.1.20",  # embedded credentials
        "http://:8000",  # no host
        "not a url",
    ],
)
async def test_rejects_dangerous_peer_urls(url):
    assert await _peer_url_allowed(url) is False


def test_log_sanitizer_neutralizes_line_breaks():
    assert _sl("node\nFAKE log line\r") == "node\\nFAKE log line\\r"
