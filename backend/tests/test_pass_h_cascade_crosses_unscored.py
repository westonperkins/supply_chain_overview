"""Pass H — cascade apply layer must not drop walk contributions on
unscored downstream nodes.

Pass H investigation established two things:

1. The BFS walk itself was correct — it visited every downstream node
   regardless of scored / unscored status (values in the cascade
   output confirmed).
2. The APPLY step silently dropped contributions on unscored nodes
   (`if baseline is None: continue`), so downstream branches that
   crossed an unscored intermediate had `current_severity` stay
   None even though the walk had computed a real value.

Fix: apply loop now accumulates the walk value on unscored downstream
nodes (anchored at 0.0), while preserving the Pass D §4 origin rule
(unscored ORIGIN's current stays None). Pass H.1 then further
constrained the derived tier — see test_current_tier_stays_unscored
below and derive_current_tier in engine.py.

Recorded graph finding: **the AI graph today contains no path of the
form scored → unscored → scored.** All unscored downstream nodes
(hyperscalers, AI labs, most facilities) sit at the terminal end of
their supply chains — there's no scored node further downstream.
This test therefore uses an unscored downstream node (Broadcom) as
the evidence that the apply fix works; a truly synthetic
scored→unscored→scored chain would need a fixture graph, which is
not built here.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.graph import SupplyChainGraph
from app.schema import AxesImpact, EntityMatch, Event
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event

FIXTURES = Path(__file__).parent / "fixtures"


def _event(node_id: str, magnitude: float) -> Event:
    return Event(
        id=f"pass_h:{node_id}",
        timestamp="2026-07-22T00:00:00Z",
        headline=f"cascade test on {node_id}",
        summary=None,
        entities_matched=[EntityMatch(node_id=node_id, confidence=1.0, match_type="test")],
        axes_impact=AxesImpact(
            concentration_delta=magnitude,
            substitutability_delta=0.0,
            lead_time_delta=0.0,
        ),
        severity=None,
        cascade=[],
        tags=[],
        notes=None,
    )


def test_unscored_downstream_node_receives_applied_walk_value():
    """Pass H apply fix — Broadcom (baseline_severity is None, sits
    downstream of gallium via RF & Power Semis) receives a non-null
    current_severity after a gallium event. Pre-Pass-H this was
    silently None because the apply loop skipped unscored nodes."""
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)

    broadcom = g.nodes["company:broadcom"]
    assert broadcom.dynamic.baseline_severity is None, (
        "test premise: Broadcom is unscored (baseline_severity=None)"
    )

    propagate_event(_event("mineral:gallium", magnitude=0.5), g, c)

    assert broadcom.dynamic.current_severity is not None, (
        f"Broadcom (unscored downstream) has current_severity=None. "
        f"The walk reached it — visible in the cascade output — but "
        f"the apply layer discarded the value. This is the Pass H "
        f"apply-layer defect."
    )
    assert broadcom.dynamic.current_severity > 0.0, (
        f"Broadcom current_severity should be a positive walk value, "
        f"got {broadcom.dynamic.current_severity}"
    )


def test_scored_downstream_of_unscored_intermediate_still_gets_hit():
    """Non-regression check on scored downstream — per Pass H Q1/Q2,
    scored downstream was always applied correctly (walk traversal
    was never broken; only apply on unscored was). Vertiv (scored,
    downstream of gallium via RF & Power) rises above baseline.

    NOT evidence of the apply fix itself — this passed before Pass H
    too. Kept as a guard against a regression that would break the
    already-correct scored-path behaviour."""
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)

    vertiv = g.nodes["company:vertiv"]
    baseline = vertiv.dynamic.baseline_severity
    assert baseline is not None, "test premise: Vertiv is scored"

    propagate_event(_event("mineral:gallium", magnitude=0.5), g, c)

    assert vertiv.dynamic.current_severity > baseline, (
        f"Vertiv current should have risen above baseline ({baseline}), "
        f"got {vertiv.dynamic.current_severity}"
    )


def test_unscored_origin_still_stays_none_after_pass_h():
    """Regression guard: Pass H changed downstream unscored behaviour
    but MUST preserve the Pass D §4 origin rule — an unscored ORIGIN's
    current stays None (no fabrication for the directly-hit node)."""
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)

    mp = g.nodes["facility:mountain_pass"]
    assert mp.dynamic.baseline_severity is None

    propagate_event(_event("facility:mountain_pass", magnitude=0.8), g, c)

    assert mp.dynamic.current_severity is None, (
        f"unscored ORIGIN's current_severity was fabricated: "
        f"{mp.dynamic.current_severity}. Pass D §4 principle violated."
    )


def test_current_tier_stays_unscored_when_baseline_is_none():
    """Pass H.1 Part 1 — a node with baseline_severity=None must have
    current_tier=UNSCORED after any event propagation, even when the
    Pass H apply fix wrote a non-null current_severity via propagation.

    Rationale: tier boundaries are distribution-anchored on the
    BASELINE severity distribution (Pass B/C). Applying them to a
    bare event contribution buckets against thresholds calibrated
    for structural severity. Two different quantities.
    """
    from app.schema.enums import ChokepointTier

    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)

    propagate_event(_event("mineral:gallium", magnitude=0.5), g, c)

    offenders = []
    for n in g.nodes.values():
        if n.dynamic.baseline_severity is not None:
            continue
        if n.dynamic.current_tier != ChokepointTier.UNSCORED:
            offenders.append((
                n.id,
                n.dynamic.current_severity,
                n.dynamic.current_tier.value if n.dynamic.current_tier else None,
            ))

    assert not offenders, (
        f"{len(offenders)} unscored node(s) carry a scored current_tier "
        f"after a real event. Pass H.1 rule violated: derive_current_tier "
        f"must return UNSCORED whenever baseline_severity is None. "
        f"Offenders (first 3): {offenders[:3]}"
    )
