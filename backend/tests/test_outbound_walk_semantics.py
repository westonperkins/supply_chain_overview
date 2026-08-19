"""Pass T §4 — permanent test pinning the outbound walk's max-of-paths
semantic.

The walk in `backend/app/scoring/engine.py::_outbound_criticality_raw`
uses `best_influence[target_id]` per destination, updated only when a
new path yields a STRICTLY GREATER influence than the previous best.
It is not sum-of-paths; it is max-of-paths, with a per-hop decay
penalty applied to each candidate influence.

Pass R claimed the max-path rule as a mechanism for a null result on
TSMC's raw outbound; Pass R.1 didn't dispute it; Pass S retracted the
claim after review because it was asserted from a null result rather
than measured. Pass T measured it on a synthetic sub-graph and
confirmed the semantic. This test pins that finding so a future engine
change to sum-of-paths (or anything else) fails visibly with an
attribution to the walk's contract, not a downstream mystery.

Also asserts the corollary that fell out of the Pass S clamp-suppression
retraction: a strong direct edge A→D suppresses an indirect path
A→B→D entirely while the decay-adjusted indirect influence is less
than the direct. Raising w_bd within that regime changes nothing.
"""

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig
from app.scoring.engine import _outbound_criticality_raw
from app.schema.edge import Edge
from app.schema.enums import EdgeType
from app.schema.node import Node, StaticFields, DynamicFields, NodeType


def _mkgraph(w_direct: float, w_ab: float, w_bd: float) -> SupplyChainGraph:
    """A→D at w_direct, A→B at w_ab, B→D at w_bd."""
    g = SupplyChainGraph()
    for nid in ("test:A", "test:B", "test:D"):
        g.nodes[nid] = Node(
            id=nid, type=NodeType.COMPANY, name=nid,
            aliases=[], domains=["ai"], layer=None, sub_category=None,
            description="test", static=StaticFields(),
            dynamic=DynamicFields(),
        )
    edges_def = [
        ("test:e-ad", "test:A", "test:D", w_direct),
        ("test:e-ab", "test:A", "test:B", w_ab),
        ("test:e-bd", "test:B", "test:D", w_bd),
    ]
    for eid, s, t, w in edges_def:
        g.edges[eid] = Edge(
            id=eid, source_id=s, target_id=t,
            type=EdgeType.SUPPLIES, static={}, input_share=w,
            output_share=None, supply_category="foundry_wafers",
        )
    g._reindex()
    return g


def _walk_params():
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    return {
        "decay": c.concentration_outbound_decay,
        "max_hops": c.concentration_outbound_max_hops,
        "min_influence": c.concentration_outbound_min_influence,
        "share_field": c.outbound_share_field,
        "fallback": c.outbound_fallback_to_input_share,
    }


def test_walk_uses_max_of_paths_not_sum():
    """A's raw outbound must NOT rise while w_bd sweeps within a range
    where the direct A→D edge still dominates the indirect A→B→D path.

    Parameters chosen so w_bd = 0.317… is the decay-adjusted crossover
    (w_direct / (w_ab × decay)). Below that, A_raw is constant at
    `sqrt((w_direct × decay)² + (w_ab × decay)²)`. Above, it rises.
    """
    params = _walk_params()
    w_direct = 0.20
    w_ab = 0.90
    # Well below the crossover.
    below_sweep = [0.05, 0.10, 0.20, 0.30]
    values_below = [
        _outbound_criticality_raw("test:A", _mkgraph(w_direct, w_ab, w_bd), **params)
        for w_bd in below_sweep
    ]
    # All four should be identical (max is set by the direct edge).
    assert len(set(round(v, 12) for v in values_below)) == 1, (
        f"A_raw should be flat while indirect < direct; got {values_below}"
    )
    # Expected constant: sqrt((w_direct × decay)² + (w_ab × decay)²)
    decay = params["decay"]
    expected = math.sqrt(
        (w_direct * decay) ** 2 + (w_ab * decay) ** 2
    )
    assert abs(values_below[0] - expected) < 1e-10, (
        f"below-crossover value {values_below[0]} != expected {expected}"
    )


def test_walk_rises_when_indirect_beats_direct():
    """Above the decay-adjusted crossover, A_raw must rise strictly
    with w_bd — the indirect path now sets the best_influence for D."""
    params = _walk_params()
    w_direct = 0.20
    w_ab = 0.90
    above_sweep = [0.40, 0.50, 0.70, 0.90]
    values = [
        _outbound_criticality_raw("test:A", _mkgraph(w_direct, w_ab, w_bd), **params)
        for w_bd in above_sweep
    ]
    for i in range(len(values) - 1):
        assert values[i + 1] > values[i], (
            f"A_raw should rise strictly above crossover; got {values}"
        )


def test_walk_crossover_step_is_upward():
    """At the crossover boundary the value must step up, not down.
    Guards against a future refactor that flips the strict-inequality
    comparison in the walk (which would silently invert the semantic)."""
    params = _walk_params()
    w_direct = 0.20
    w_ab = 0.90
    below = _outbound_criticality_raw(
        "test:A", _mkgraph(w_direct, w_ab, 0.30), **params,
    )
    above = _outbound_criticality_raw(
        "test:A", _mkgraph(w_direct, w_ab, 0.40), **params,
    )
    assert above > below, (
        f"crossover step should be upward; got below={below}, above={above}"
    )
