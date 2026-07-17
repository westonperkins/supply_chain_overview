from collections import defaultdict
from pathlib import Path
import json
from typing import Iterable, Optional

from ..schema import (
    Edge,
    EdgeType,
    Event,
    Node,
    NodeType,
)
from ..schema.enums import SUPPLY_EDGE_TYPES


# Edges whose direction represents the FLOW of shares INTO the target node
# (i.e. the target's supplier mix). Used to derive the target's share map.
SHARE_INTO_TARGET = {
    EdgeType.MINES,       # country supplies mineral
    EdgeType.REFINES,     # country supplies refined mineral
    EdgeType.SUPPLIES,    # company supplies company
    EdgeType.INPUT_TO,    # mineral/product feeds company
    EdgeType.COMPONENT_OF,# product feeds product/company
}


class SupplyChainGraph:
    """In-memory supply-chain graph. Nodes and edges are the single source of
    truth; per-node share maps are DERIVED from edges (structural change B)."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.events: dict[str, Event] = {}

        # Adjacency indexes, rebuilt when data loads.
        self._out: dict[str, list[str]] = defaultdict(list)  # source -> [edge_id]
        self._in: dict[str, list[str]] = defaultdict(list)   # target -> [edge_id]

    # ---- loading ----------------------------------------------------------

    @classmethod
    def from_dir(cls, data_dir: Path, domain: str = "ai") -> "SupplyChainGraph":
        g = cls()
        with (data_dir / domain / "nodes.json").open() as f:
            for raw in json.load(f):
                node = Node(**raw)
                g.nodes[node.id] = node
        with (data_dir / domain / "edges.json").open() as f:
            for raw in json.load(f):
                edge = Edge(**raw)
                g.edges[edge.id] = edge
        with (data_dir / domain / "events.json").open() as f:
            for raw in json.load(f):
                event = Event(**raw)
                g.events[event.id] = event
        g._reindex()
        return g

    def _reindex(self) -> None:
        self._out.clear()
        self._in.clear()
        for edge in self.edges.values():
            self._out[edge.source_id].append(edge.id)
            self._in[edge.target_id].append(edge.id)

    # ---- basic queries ----------------------------------------------------

    def in_edges(self, node_id: str, types: Optional[Iterable[EdgeType]] = None) -> list[Edge]:
        allowed = set(types) if types else None
        return [
            self.edges[eid]
            for eid in self._in.get(node_id, [])
            if allowed is None or self.edges[eid].type in allowed
        ]

    def out_edges(self, node_id: str, types: Optional[Iterable[EdgeType]] = None) -> list[Edge]:
        allowed = set(types) if types else None
        return [
            self.edges[eid]
            for eid in self._out.get(node_id, [])
            if allowed is None or self.edges[eid].type in allowed
        ]

    def downstream_supply_edges(self, node_id: str) -> list[Edge]:
        """Edges leaving this node along supply-flow direction — used for cascade."""
        return self.out_edges(node_id, SUPPLY_EDGE_TYPES)

    # ---- derived shares (structural change B) -----------------------------

    def derived_shares(self, node_id: str) -> dict:
        """Compute the node's incoming-supplier share map from edges.

        Returns a dict keyed by edge type, each mapping source_id -> weight.
        The edge IS the source of truth; the shares map is regenerated here
        so it can never drift out of sync with the graph.
        """
        buckets: dict[str, dict[str, float]] = defaultdict(dict)
        for edge in self.in_edges(node_id, SHARE_INTO_TARGET):
            buckets[edge.type.value][edge.source_id] = edge.effective_weight()
        return dict(buckets)

    def refresh_derived_shares(self) -> None:
        """Cache derived_shares onto each node's dynamic block."""
        for node in self.nodes.values():
            node.dynamic.derived_shares = self.derived_shares(node.id) or None
