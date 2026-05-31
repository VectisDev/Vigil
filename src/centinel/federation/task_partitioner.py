"""
Deterministic task partitioner for Centinel Swarm (max 12 nodes).

With N active nodes sorted by arrival_order, CNE sources are distributed by:
    source[i] → node at slot_index (i % N)

This is a pure function of (sources, active_node_list) — no coordination
needed. When nodes drop, survivors automatically cover orphaned sources on
the next scrape cycle without any message exchange.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

MAX_SWARM_NODES = 12

# Honduras CNE data sources: national aggregate + 18 departmental endpoints.
HN_SOURCES: list[str] = [
    "NACIONAL",
    "01_atl",    # Atlántida
    "02_col",    # Colón
    "03_com",    # Comayagua
    "04_cop",    # Copán
    "05_cor",    # Cortés
    "06_ch",     # Choluteca
    "07_ep",     # El Paraíso
    "08_fm",     # Francisco Morazán
    "09_gr",     # Gracias a Dios
    "10_in",     # Intibucá
    "11_iz",     # Islas de la Bahía
    "12_la_paz", # La Paz
    "13_le",     # Lempira
    "14_oc",     # Ocotepeque
    "15_ol",     # Olancho
    "16_sb",     # Santa Bárbara
    "17_val",    # Valle
    "18_yoro",   # Yoro
]


@dataclass(frozen=True)
class TaskSlice:
    """The subset of CNE sources assigned to one node."""
    node_id: str
    arrival_order: int
    sources: tuple[str, ...]

    @property
    def source_count(self) -> int:
        return len(self.sources)


class TaskPartitioner:
    """Assigns CNE sources to active swarm nodes deterministically."""

    def __init__(self, sources: Optional[list[str]] = None) -> None:
        self._sources = list(sources or HN_SOURCES)

    def assign(self, nodes: list[tuple[str, int]]) -> list[TaskSlice]:
        """
        Compute one TaskSlice per active node.

        nodes: list of (node_id, arrival_order) for currently active nodes.
        The arrival_order determines slot rank — the list itself can arrive in
        any order; assignment is stable and deterministic regardless.

        With N nodes:
          node at slot 0 → sources at indices 0, N, 2N, …
          node at slot 1 → sources at indices 1, N+1, 2N+1, …
          …
        """
        if not nodes:
            return []
        sorted_nodes = sorted(nodes, key=lambda x: x[1])  # by arrival_order
        n = len(sorted_nodes)
        slices = []
        for slot, (node_id, arrival_order) in enumerate(sorted_nodes):
            assigned = tuple(
                src for i, src in enumerate(self._sources) if i % n == slot
            )
            slices.append(TaskSlice(
                node_id=node_id,
                arrival_order=arrival_order,
                sources=assigned,
            ))
        return slices

    def get_sources_for(
        self,
        my_node_id: str,
        active_nodes: list[tuple[str, int]],
    ) -> list[str]:
        """Return the sources this node should scrape given current active swarm.

        Falls back to all sources if this node_id isn't in the active list
        (solo mode — cover everything rather than miss anything).
        """
        for sl in self.assign(active_nodes):
            if sl.node_id == my_node_id:
                return list(sl.sources)
        return list(self._sources)

    def assignment_summary(self, nodes: list[tuple[str, int]]) -> list[dict]:
        """Return a JSON-serialisable summary of the current assignment."""
        return [
            {
                "node_id": sl.node_id,
                "arrival_order": sl.arrival_order,
                "sources": list(sl.sources),
                "source_count": sl.source_count,
            }
            for sl in self.assign(nodes)
        ]
