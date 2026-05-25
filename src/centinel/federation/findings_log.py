"""
FederationAnomalyLog — ring buffer thread-safe de hallazgos electorales cross-nodo.

Almacena FindingPayload recibidos de otros nodos (y los propios emitidos) con
deduplicación por finding_id, consulta por severidad/regla y persistencia JSONL.
"""
from __future__ import annotations

import json
import logging
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from centinel.federation.gossip import FindingPayload

logger = logging.getLogger("centinel.federation.findings_log")

_BROADCAST_SEVERITIES = {"HIGH", "CRITICAL"}


class FederationAnomalyLog:
    """Ring buffer de hallazgos electorales cross-nodo.

    Persiste en logs/federation_anomalies.jsonl para auditoría post-elección.
    Acepta finding_type "rule_violation" y "anomaly".
    """

    ACCEPTED_TYPES = {"rule_violation", "anomaly"}

    def __init__(
        self,
        max_findings: int = 500,
        log_path: Optional[Path] = None,
    ) -> None:
        self._max = max_findings
        self._log_path = log_path
        self._store: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.Lock()
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, finding: "FindingPayload", source: str = "remote") -> bool:
        """Añade hallazgo al ring buffer. Retorna True si es nuevo (no dedup).

        Args:
            finding: FindingPayload firmado y verificado.
            source: "local" (emitido por este nodo) | "remote" (recibido de peer).
        """
        if finding.finding_type not in self.ACCEPTED_TYPES:
            return False
        if finding.severity not in _BROADCAST_SEVERITIES:
            return False

        with self._lock:
            if finding.finding_id in self._store:
                return False  # dedup

            entry = finding.to_dict()
            entry["_source"] = source
            entry["_received_utc"] = datetime.now(timezone.utc).isoformat()

            self._store[finding.finding_id] = entry

            # Evict oldest when over capacity
            while len(self._store) > self._max:
                self._store.popitem(last=False)

            if self._log_path:
                self._append_jsonl(entry)

        logger.info(
            "federation_anomaly_added finding_id=%s rule=%s severity=%s source=%s",
            finding.finding_id,
            finding.rule_key,
            finding.severity,
            source,
        )
        return True

    def query(
        self,
        since_utc: Optional[str] = None,
        severity: Optional[str] = None,
        rule_key: Optional[str] = None,
        node_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Consulta hallazgos con filtros opcionales, más recientes primero."""
        with self._lock:
            items = list(self._store.values())

        # Más recientes primero
        items.sort(key=lambda x: x.get("timestamp_utc", ""), reverse=True)

        if since_utc:
            items = [i for i in items if i.get("timestamp_utc", "") >= since_utc]
        if severity:
            items = [i for i in items if i.get("severity") == severity.upper()]
        if rule_key:
            items = [i for i in items if i.get("rule_key") == rule_key]
        if node_id:
            items = [i for i in items if i.get("node_id") == node_id]

        return items[:limit]

    def stats(self) -> dict:
        """Resumen de hallazgos almacenados."""
        with self._lock:
            items = list(self._store.values())
        by_severity: dict[str, int] = {}
        by_rule: dict[str, int] = {}
        by_node: dict[str, int] = {}
        for item in items:
            sev = item.get("severity", "UNKNOWN")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            rule = item.get("rule_key", "unknown")
            by_rule[rule] = by_rule.get(rule, 0) + 1
            nid = item.get("node_id", "unknown")
            by_node[nid] = by_node.get(nid, 0) + 1
        return {
            "total": len(items),
            "by_severity": by_severity,
            "by_rule": by_rule,
            "by_node": by_node,
        }

    def _append_jsonl(self, entry: dict) -> None:
        try:
            with self._log_path.open("a", encoding="utf-8") as fh:  # type: ignore[union-attr]
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("federation_anomaly_log_write_error error=%s", exc)
