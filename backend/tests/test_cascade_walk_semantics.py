"""Pass Z §6 — pin the CASCADE walk's semantics.

`test_outbound_walk_semantics.py` pins the ENGINE walk
(`_outbound_criticality_raw`). Pass Y found the two walks had silently
diverged — the engine did max-of-paths, the cascade did
first-encounter-wins — with only one pinned. This file closes that
asymmetry for `cascade.propagate_event`.

Guards 1–4 are INTENT-pinned (synthetic graphs / structural assertions,
written against the target semantics, not observed output). Guard 5 is
VALUE-pinned (a regression on a committed number, labelled as such).
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
REPO = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import json

from app.graph import SupplyChainGraph
from app.schema import Event
from app.schema.node import Node, StaticFields, DynamicFields
from app.schema.edge import Edge
from app.schema.enums import NodeType, EdgeType
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event

FIX = Path(__file__).parent / "fixtures"


def _cfg():
    return ScoringConfig.load(FIX / "scoring.yaml")


def _node(nid, baseline=None, conc=None):
    n = Node(id=nid, type=NodeType.PRODUCT, name=nid, aliases=[],
             domains=["ai"], description="t",
             static=StaticFields(), dynamic=DynamicFields())
    n.dynamic.baseline_severity = baseline
    n.dynamic.concentration = conc
    return n


def _edge(eid, s, t, share):
    return Edge(id=eid, source_id=s, target_id=t, type=EdgeType.SUPPLIES,
                static={}, input_share=share)


def _seed_event(origin_id):
    """An event whose only matched entity is `origin_id`, concentration
    delta 1.0, confidence 1.0. For an unscored origin at concentration 0
    the seed is (conc' − conc) × conf = 1.0 — a clean unit seed."""
    return Event.model_validate({
        "id": "T", "timestamp": "2024-01-01T00:00:00Z", "headline": "t",
        "entities_matched": [{"node_id": origin_id, "confidence": 1.0,
                              "match_type": "name"}],
        "axes_impact": {"concentration_delta": 1.0},
    })


def _contrib(event, node_id):
    for s in event.cascade:
        if s.node_id == node_id:
            return s.severity_at_node, s.edge_path, s.hop
    return None


# --- Guard 1: max-of-paths, parallel edge + longer path (INTENT) -----------

def test_max_of_paths_beats_weaker_parallel_edge():
    """A → B via a WEAK edge (0.2, first in file order) and a STRONG edge
    (0.9, second). Max-of-paths must record B via the strong edge; the
    pre-Pass-Z first-encounter walk recorded the weak one."""
    cfg = _cfg()
    g = SupplyChainGraph()
    g.nodes["mineral:a"] = _node("mineral:a", conc=0.0)   # unscored origin
    g.nodes["product:b"] = _node("product:b")
    g.edges["e:a-weak-b"] = _edge("e:a-weak-b", "mineral:a", "product:b", 0.2)
    g.edges["e:a-strong-b"] = _edge("e:a-strong-b", "mineral:a", "product:b", 0.9)
    g._reindex()
    ev = propagate_event(_seed_event("mineral:a"), g, cfg)
    contrib, path, hop = _contrib(ev, "product:b")
    # seed 1.0 × decay 0.6 × 0.9 = 0.54 via the strong edge.
    assert path == ["e:a-strong-b"], path
    assert abs(contrib - 1.0 * cfg.cascade_decay * 0.9) < 1e-12, contrib


def test_max_of_paths_beats_weaker_direct_via_longer_path():
    """A → D direct (0.1, first) is beaten by A → C → D (0.9, 0.9). The
    first-encounter walk marked D visited on the direct edge and never
    saw the stronger two-hop path."""
    cfg = _cfg()
    g = SupplyChainGraph()
    g.nodes["mineral:a"] = _node("mineral:a", conc=0.0)
    g.nodes["product:c"] = _node("product:c")
    g.nodes["product:d"] = _node("product:d")
    g.edges["e:a-d"] = _edge("e:a-d", "mineral:a", "product:d", 0.1)   # weak direct, first
    g.edges["e:a-c"] = _edge("e:a-c", "mineral:a", "product:c", 0.9)
    g.edges["e:c-d"] = _edge("e:c-d", "product:c", "product:d", 0.9)
    g._reindex()
    ev = propagate_event(_seed_event("mineral:a"), g, cfg)
    contrib, path, hop = _contrib(ev, "product:d")
    dk = cfg.cascade_decay
    expected = 1.0 * dk * 0.9 * dk * 0.9    # via C
    assert path == ["e:a-c", "e:c-d"], path
    assert hop == 2, hop
    assert abs(contrib - expected) < 1e-12, (contrib, expected)


# --- Guard 2: termination on a cycle (INTENT) ------------------------------

def test_walk_terminates_on_cycle_and_respects_max_hops():
    """A ↔ B cycle. With no visited set, termination relies on
    strict-improvement + decay<1 + the 1e-6 floor + max_hops. The call
    must return and no cascade step may exceed max_hops."""
    cfg = _cfg()
    g = SupplyChainGraph()
    g.nodes["mineral:a"] = _node("mineral:a", conc=0.0)
    g.nodes["product:b"] = _node("product:b")
    g.edges["e:a-b"] = _edge("e:a-b", "mineral:a", "product:b", 0.9)
    g.edges["e:b-a"] = _edge("e:b-a", "product:b", "mineral:a", 0.9)
    g._reindex()
    ev = propagate_event(_seed_event("mineral:a"), g, cfg)   # must return
    assert all(s.hop <= cfg.cascade_max_hops for s in ev.cascade)


def test_real_graph_arm_cycle_terminates():
    """The committed AI graph's one supply-edge cycle (arm ↔ arm_core_ip)
    must not hang the walk. Drive an event that reaches it (copper →
    tsmc → arm → arm_core_ip) and assert bounded hops."""
    cfg = _cfg()
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    refresh_all_derived(g, cfg)
    ev = Event.model_validate({
        "id": "T", "timestamp": "2024-01-01T00:00:00Z", "headline": "t",
        "entities_matched": [{"node_id": "mineral:copper", "confidence": 1.0,
                              "match_type": "name"}],
        "axes_impact": {"concentration_delta": 0.5},
    })
    ev = propagate_event(ev, g, cfg)
    assert all(s.hop <= cfg.cascade_max_hops for s in ev.cascade)


# --- Guard 3: origin-hop invariant (expectation 12) ------------------------

def test_unscored_origins_stay_none_and_hop_zero():
    """The invariant that MATTERS (Pass Z §4.1 / expectation 12, corrected).

    The spec's expectation 12 — "every matched origin retains hop 0" — is
    FALSE under max-of-paths across multiple origins: a SCORED origin can
    be reached more strongly from another origin (e.g. china-gallium's
    `mineral:gallium` is recorded at hop 1 via `e:china-mines-gallium`,
    0.1773, which beats gallium's own seed 0.0421). That is correct
    attribution and harmless — hop 0 vs 1 does not change how a scored
    node accumulates.

    The invariant that is load-bearing (the `is_origin = hop == 0` gate
    that keeps an UNSCORED origin's current_severity None) DOES hold:
    country origins have no inbound supply edges, so nothing can overwrite
    them to hop > 0. This test pins that: every unscored matched origin
    stays None and hop 0. A future edge that fed a country would break
    this and must be caught here."""
    cfg = _cfg()
    events = json.loads((REPO / "data" / "ai" / "replay" / "events.json").read_text())
    for raw in events:
        g = SupplyChainGraph.from_dir(FIX, domain="ai")
        refresh_all_derived(g, cfg)
        ev = propagate_event(Event.model_validate(raw), g, cfg)
        by_id = {s.node_id: s for s in ev.cascade}
        for m in ev.entities_matched:
            node = g.nodes.get(m.node_id)
            if node is None or node.dynamic.baseline_severity is not None:
                continue  # only unscored origins
            assert node.dynamic.current_severity is None, (raw["id"], m.node_id)
            if m.node_id in by_id:
                assert by_id[m.node_id].hop == 0, (raw["id"], m.node_id, by_id[m.node_id].hop)


def test_single_origin_self_return_does_not_overwrite_seed():
    """The §4.1 concern proper: a walk returning to its OWN origin cannot
    improve the seed (contributions strictly decrease). On a lone origin
    with a self-cycle, the origin keeps hop 0 and its seed contribution."""
    cfg = _cfg()
    g = SupplyChainGraph()
    g.nodes["mineral:a"] = _node("mineral:a", conc=0.0)
    g.nodes["product:b"] = _node("product:b")
    g.edges["e:a-b"] = _edge("e:a-b", "mineral:a", "product:b", 0.9)
    g.edges["e:b-a"] = _edge("e:b-a", "product:b", "mineral:a", 0.9)
    g._reindex()
    ev = propagate_event(_seed_event("mineral:a"), g, cfg)
    origin_step = next(s for s in ev.cascade if s.node_id == "mineral:a")
    assert origin_step.hop == 0, origin_step
    assert abs(origin_step.severity_at_node - 1.0) < 1e-12, origin_step  # the unit seed


# --- Guard 4: FO-1a permissive fallback (INTENT) ---------------------------

def test_fo1a_country_with_no_subject_seeds_unscoped():
    """kachin-kia matches country origins (kachin, myanmar) and NO mineral
    subject. Under FO-1a the country origins must fall back to the full
    unscoped edge set (not record a null): the event still reaches its
    downstream minerals."""
    cfg = _cfg()
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    refresh_all_derived(g, cfg)
    events = {e["id"]: e for e in
              json.loads((REPO / "data" / "ai" / "replay" / "events.json").read_text())}
    ev = propagate_event(Event.model_validate(events["J-2024-10-kachin-kia"]), g, cfg)
    reached = {s.node_id for s in ev.cascade}
    # kachin mines dysprosium; the permissive fallback must let the walk
    # cross into dysprosium (and beyond) rather than nulling the origin.
    assert "mineral:dysprosium" in reached, sorted(reached)


# --- Guard 5: china-rees regression (VALUE-pinned) -------------------------

def test_china_rees_regression_value_pinned():
    """VALUE-pinned (Pass Z §6.5): the shipped china-rees walk reaches 7
    nodes with dysprosium as max-Δ node and Δ 0.09109554353960558. This
    pins an observed committed value, not intended semantics — update it
    only with an authorizing spec."""
    cfg = _cfg()
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    refresh_all_derived(g, cfg)
    events = {e["id"]: e for e in
              json.loads((REPO / "data" / "ai" / "replay" / "events.json").read_text())}
    ev = propagate_event(Event.model_validate(events["J-2025-04-china-rees"]), g, cfg)
    deltas = []
    for n in g.nodes.values():
        cur, base = n.dynamic.current_severity, n.dynamic.baseline_severity
        cv = cur if cur is not None else (base if base is not None else 0.0)
        d = cv - (base if base is not None else 0.0)
        if abs(d) > 1e-6:
            deltas.append((n.id, d))
    deltas.sort(key=lambda t: -t[1])
    assert len(deltas) == 7, [d[0] for d in deltas]
    assert deltas[0][0] == "mineral:dysprosium", deltas[0]
    assert abs(deltas[0][1] - 0.09109554353960558) < 1e-15, deltas[0][1]
