"""
FederationAttackLog — ring buffer thread-safe de ataques dirigidos al swarm.

Solo persiste ataques a paths Centinel-específicos o DoS sostenido — filtra el
ruido de scans genéricos de internet que no son relevantes para los demás nodos.
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

logger = logging.getLogger("centinel.federation.attack_log")

# Paths que solo existen en un nodo Centinel — un ataque a estos es
# intencional, no un scan aleatorio de internet.
_SWARM_PATHS: frozenset[str] = frozenset({
    "/api/swarm/",
    "/api/swarm/attest",
    "/api/swarm/finding",
    "/api/swarm/anomalies",
    "/api/swarm/attacks",
    "/api/swarm/status",
    "/api/swarm/connect",
    "/hashchain/verify",
    "/api/health",
    "/api/summaries",
    "/api/national-snapshot",
    "/api/departments/status",
    "/live",
})

# Frecuencia de requests que indica DoS sostenido independientemente del path
_DOS_FREQUENCY_THRESHOLD = 50


class FederationAttackLog:
    """Ring buffer de ataques coordinados/dirigidos al swarm de vigilancia.

    Un ataque es "dirigido" si apunta a paths Centinel-específicos o
    supera el umbral de DoS sostenido. El ruido de scans genéricos de
    internet (wp-login, .env, etc.) se descarta.
    """

    ACCEPTED_TYPE = "swarm_attack"

    def __init__(
        self,
        max_findings: int = 300,
        log_path: Optional[Path] = None,
        dos_frequency_threshold: int = _DOS_FREQUENCY_THRESHOLD,
    ) -> None:
        self._max = max_findings
        self._log_path = log_path
        self._dos_threshold = dos_frequency_threshold
        self._store: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.Lock()
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def is_swarm_targeted(self, event: dict) -> bool:
        """True si el ataque apunta a paths de Centinel o es DoS sostenido.

        Filtra scans genéricos de internet (wp-login, /admin, etc.) que no
        son relevantes para los demás nodos de la red de vigilancia.
        """
        route = event.get("route", "")
        frequency = int(event.get("frequency_count", 0))

        # Path-based: cualquier path exclusivo de Centinel
        if any(route == p or route.startswith(p) for p in _SWARM_PATHS):
            return True

        # DoS sostenido: alta frecuencia independientemente del path
        if frequency >= self._dos_threshold:
            return True

        return False

    def add(self, finding: "FindingPayload", source: str = "remote") -> bool:
        """Añade ataque al ring buffer. Retorna True si es nuevo (no dedup).

        Args:
            finding: FindingPayload con finding_type="swarm_attack".
            source: "local" | "remote".
        """
        if finding.finding_type != self.ACCEPTED_TYPE:
            return False

        with self._lock:
            if finding.finding_id in self._store:
                return False

            entry = finding.to_dict()
            entry["_source"] = source
            entry["_received_utc"] = datetime.now(timezone.utc).isoformat()

            self._store[finding.finding_id] = entry

            while len(self._store) > self._max:
                self._store.popitem(last=False)

            if self._log_path:
                self._append_jsonl(entry)

        logger.info(
            "federation_attack_added finding_id=%s rule=%s severity=%s source=%s",
            finding.finding_id,
            finding.rule_key,
            finding.severity,
            source,
        )
        return True

    def query(
        self,
        since_utc: Optional[str] = None,
        node_id: Optional[str] = None,
        rule_key: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Consulta ataques con filtros opcionales, más recientes primero."""
        with self._lock:
            items = list(self._store.values())

        items.sort(key=lambda x: x.get("timestamp_utc", ""), reverse=True)

        if since_utc:
            items = [i for i in items if i.get("timestamp_utc", "") >= since_utc]
        if node_id:
            items = [i for i in items if i.get("node_id") == node_id]
        if rule_key:
            items = [i for i in items if i.get("rule_key") == rule_key]

        return items[:limit]

    def stats(self) -> dict:
        """Resumen de ataques almacenados."""
        with self._lock:
            items = list(self._store.values())
        by_node: dict[str, int] = {}
        by_rule: dict[str, int] = {}
        for item in items:
            nid = item.get("node_id", "unknown")
            by_node[nid] = by_node.get(nid, 0) + 1
            rule = item.get("rule_key", "unknown")
            by_rule[rule] = by_rule.get(rule, 0) + 1
        return {
            "total": len(items),
            "by_node": by_node,
            "by_rule": by_rule,
        }

    def _append_jsonl(self, entry: dict) -> None:
        try:
            with self._log_path.open("a", encoding="utf-8") as fh:  # type: ignore[union-attr]
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("federation_attack_log_write_error error=%s", exc)
