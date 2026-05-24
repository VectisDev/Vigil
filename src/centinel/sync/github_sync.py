"""
GitHub sync — publishes snapshot records and alerts to the gh-pages data directory.

Pushes lightweight JSON files to the web/data/ directory via the GitHub Contents API.
Failures are always non-fatal: local SQLite remains the source of truth.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_REPO   = os.getenv("GITHUB_REPOSITORY", "VectisDev/centinel")
_TOKEN  = os.getenv("GITHUB_TOKEN", "")
_BRANCH = os.getenv("GITHUB_PAGES_BRANCH", "main")
_API    = f"https://api.github.com/repos/{_REPO}"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_file_sha(path: str) -> Optional[str]:
    try:
        import urllib.request
        req = urllib.request.Request(f"{_API}/contents/{path}?ref={_BRANCH}", headers=_headers())
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())["sha"]
    except Exception:
        return None


def _put_file(path: str, content_str: str, message: str) -> bool:
    if not _TOKEN:
        logger.debug("github_sync: no token, skipping push")
        return False
    try:
        import urllib.request
        sha = _get_file_sha(path)
        payload: Dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content_str.encode()).decode(),
            "branch": _BRANCH,
        }
        if sha:
            payload["sha"] = sha
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{_API}/contents/{path}",
            data=data,
            headers={**_headers(), "Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        return True
    except Exception as exc:
        logger.warning("github_sync_put_failed", path=path, error=str(exc))
        return False


def push_snapshot(
    captured_at: str,
    chain_hash: str,
    merkle_root: str,
    chain_length: int = 0,
    dept_code: Optional[str] = None,
    ots_proof_b64: Optional[str] = None,
    anomaly_flag: bool = False,
    alert_state: str = "normal",
    raw_meta: Optional[Dict] = None,
) -> bool:
    """Append snapshot record to web/data/latest_snapshot.json."""
    record = {
        "captured_at": captured_at,
        "chain_hash": chain_hash,
        "merkle_root": merkle_root,
        "chain_length": chain_length,
        "anomaly_flag": anomaly_flag,
        "alert_state": alert_state,
    }
    if dept_code:
        record["dept_code"] = dept_code
    if ots_proof_b64:
        record["ots_proof_b64"] = ots_proof_b64
    if raw_meta:
        record["raw_meta"] = raw_meta

    ok = _put_file(
        "web/data/latest_snapshot.json",
        json.dumps(record, indent=2),
        f"data: snapshot {chain_hash[:12]} [{alert_state}]",
    )
    if ok:
        logger.info("github_snapshot_pushed", hash=chain_hash[:16])
    return ok


def push_alert(
    created_at: str,
    severity: str,
    description: str,
    rule_id: Optional[str] = None,
    kind: Optional[str] = None,
    dept_code: Optional[str] = None,
) -> bool:
    """Append alert to web/data/alerts.json (last 100 kept)."""
    alert = {
        "created_at": created_at,
        "severity": severity,
        "description": description,
    }
    if rule_id:
        alert["rule_id"] = rule_id
    if kind:
        alert["kind"] = kind
    if dept_code:
        alert["dept_code"] = dept_code

    ok = _put_file(
        "web/data/latest_alert.json",
        json.dumps(alert, indent=2),
        f"data: alert {severity} — {description[:60]}",
    )
    if ok:
        logger.info("github_alert_pushed", severity=severity)
    return ok


def is_configured() -> bool:
    """Return True if GITHUB_TOKEN is set."""
    return bool(_TOKEN)
