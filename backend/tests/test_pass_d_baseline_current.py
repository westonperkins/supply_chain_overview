"""Pass D — baseline vs current severity split, cascade neutral-leak fix.

T1  no-event identity                — current == baseline everywhere with no events
T2  baseline equals prior current    — INV-1 (fresh baseline matches Pass C snapshot)
T3  thresholds ignore events         — INV-3 (boundaries invariant under an event)
T4  unscored origin emits no fabricated severity — the leak fix
T5  scored origin raises current, leaves baseline
T7  events write current only        — INV-4 (baseline immovable)

(T6 lives in test_paper_chokepoints.py — the assertion was retargeted
from current_severity to baseline_severity there.)
"""
import copy
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import pytest

from app.graph import SupplyChainGraph
from app.schema import AxesImpact, EntityMatch, Event
from app.schema.enums import ChokepointTier
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.thresholds import derive_thresholds

REPO = BACKEND.parent
FIXTURES = Path(__file__).parent / "fixtures"


def _fresh():
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)
    return g, c


def _synthetic_event(node_id: str, magnitude: float) -> Event:
    """Build a mock event that our propagator can consume.
    magnitude comes from axes.concentration_delta per config default."""
    return Event(
        id=f"synth:{node_id}",
        timestamp="2026-07-22T00:00:00Z",
        headline=f"synthetic event on {node_id}",
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


# ---------------------------------------------------------------------
# T1 — no-event identity
# ---------------------------------------------------------------------

def test_no_event_current_equals_baseline_everywhere():
    """T1 (spec §5). With no active events, current == baseline for every
    node, exactly. Applies to severity AND tier.
    """
    g, _ = _fresh()  # refresh_all_derived only; no propagate_event calls
    for n in g.nodes.values():
        assert n.dynamic.current_severity == n.dynamic.baseline_severity, (
            f"{n.id}: current_severity={n.dynamic.current_severity} "
            f"!= baseline_severity={n.dynamic.baseline_severity}"
        )
        assert n.dynamic.current_tier == n.dynamic.baseline_tier, (
            f"{n.id}: current_tier={n.dynamic.current_tier} "
            f"!= baseline_tier={n.dynamic.baseline_tier}"
        )


# ---------------------------------------------------------------------
# T2 — baseline equals prior current (INV-1)
# ---------------------------------------------------------------------

def test_baseline_severity_equals_prior_pass_current_bit_for_bit():
    """T2 (INV-1). New baseline_severity == Pass C snapshot's per-node
    severity bit-for-bit. Fails naming any node that moved."""
    g, _ = _fresh()
    snap = json.loads(
        (REPO / "docs" / "generated" / "severity_snapshot.json").read_text()
    )
    label = snap.get("captured_at_pass")
    for nid, entry in snap["nodes"].items():
        node = g.nodes[nid]
        prior_sev = entry.get("severity")
        new_base = node.dynamic.baseline_severity
        if prior_sev is None and new_base is None:
            continue
        assert prior_sev == new_base, (
            f"{nid}: Pass C snapshot severity {prior_sev!r} != new "
            f"baseline_severity {new_base!r}. INV-1 says the schema "
            f"split must not move any structural value. Snapshot label: "
            f"{label!r}."
        )


# ---------------------------------------------------------------------
# T3 — thresholds ignore events (INV-3)
# ---------------------------------------------------------------------

def test_threshold_derivation_ignores_events():
    """T3 (INV-3). Derive boundaries with an event active and assert they
    are identical to boundaries derived with no events. Events must not
    move a boundary."""
    g, c = _fresh()
    baseline_only = [
        (nid, n.dynamic.baseline_severity) for nid, n in g.nodes.items()
    ]
    d_no_event = derive_thresholds(baseline_only, c.threshold_separation_factor)

    # Fire an event; assert derivation from BASELINE is unchanged.
    ev = _synthetic_event("company:tsmc", magnitude=0.5)
    propagate_event(ev, g, c)
    baseline_after_event = [
        (nid, n.dynamic.baseline_severity) for nid, n in g.nodes.items()
    ]
    d_with_event = derive_thresholds(baseline_after_event, c.threshold_separation_factor)

    assert d_no_event.boundaries == d_with_event.boundaries, (
        f"threshold boundaries moved under an active event. "
        f"before={d_no_event.boundaries} after={d_with_event.boundaries}. "
        f"INV-3 violated — an event moved a tier boundary."
    )


# ---------------------------------------------------------------------
# T4 — unscored origin does NOT fabricate severity (the leak fix)
# ---------------------------------------------------------------------

def test_event_on_unscored_origin_stays_none_and_propagates_downstream():
    """T4 (spec §4). Fire an event at an unscored node; assert:
      - its current_severity stays None (not ~0.9 as the pre-fix code emitted)
      - its current_tier stays UNSCORED
      - at least one downstream scored node's current_severity rose
      - that downstream node's current_severity_has_unscored_origin is True.
    """
    g, c = _fresh()

    # Mountain Pass is unscored (facility, missing static axes) AND has
    # a downstream mines-edge to neodymium (a scored mineral) so the
    # test can verify propagation reaches a scored downstream node.
    origin_id = "facility:mountain_pass"
    origin = g.nodes[origin_id]
    assert origin.dynamic.baseline_severity is None, (
        f"expected {origin_id} to be unscored (test premise). Pick a "
        f"different unscored origin if this assertion fires."
    )
    baseline_downstream_snapshot = {
        nid: n.dynamic.baseline_severity for nid, n in g.nodes.items()
    }

    ev = _synthetic_event(origin_id, magnitude=0.8)
    propagate_event(ev, g, c)

    # Origin's own current stays None; tier stays UNSCORED.
    assert origin.dynamic.current_severity is None, (
        f"leak: unscored origin's current_severity fabricated as "
        f"{origin.dynamic.current_severity}. Expected None."
    )
    assert origin.dynamic.current_tier == ChokepointTier.UNSCORED

    # At least one downstream SCORED node's current_severity moved up.
    risers = [
        nid for nid, n in g.nodes.items()
        if n.dynamic.baseline_severity is not None
        and n.dynamic.current_severity is not None
        and n.dynamic.current_severity > baseline_downstream_snapshot[nid]
    ]
    assert risers, (
        f"unscored-origin event did not propagate to any downstream "
        f"scored node. concentration-based propagation is broken."
    )

    # Every riser downstream of the unscored origin should be flagged.
    tagged = [
        nid for nid in risers
        if g.nodes[nid].dynamic.current_severity_has_unscored_origin
    ]
    assert tagged, (
        f"downstream risers {risers[:3]} are not flagged with "
        f"current_severity_has_unscored_origin — provenance tag missing."
    )


# ---------------------------------------------------------------------
# T5 — scored origin raises current, leaves baseline
# ---------------------------------------------------------------------

def test_event_on_scored_origin_raises_current_but_not_baseline():
    """T5. Fire an event at a scored node; assert:
      - current_severity > baseline_severity at the origin
      - baseline_severity unchanged
      - current_severity ≤ 1.0
    """
    g, c = _fresh()
    origin_id = "company:tsmc"
    origin = g.nodes[origin_id]
    assert origin.dynamic.baseline_severity is not None
    baseline_before = origin.dynamic.baseline_severity

    ev = _synthetic_event(origin_id, magnitude=0.5)
    propagate_event(ev, g, c)

    assert origin.dynamic.baseline_severity == baseline_before, (
        f"baseline_severity moved under an event: {baseline_before} → "
        f"{origin.dynamic.baseline_severity}. INV-4 violated."
    )
    assert origin.dynamic.current_severity is not None
    assert origin.dynamic.current_severity > baseline_before, (
        f"scored origin's current_severity did not rise above baseline: "
        f"baseline={baseline_before}, current={origin.dynamic.current_severity}"
    )
    assert origin.dynamic.current_severity <= 1.0 + 1e-9, (
        f"current_severity {origin.dynamic.current_severity} exceeds 1.0"
    )


# ---------------------------------------------------------------------
# T7 — events write current only (INV-4)
# ---------------------------------------------------------------------

def test_event_propagation_writes_current_only_not_baseline():
    """T7 (INV-4). After propagation, no node's baseline_severity or
    baseline_tier differs from the pre-event snapshot."""
    g, c = _fresh()
    before_baseline = {
        nid: (n.dynamic.baseline_severity, n.dynamic.baseline_tier)
        for nid, n in g.nodes.items()
    }
    # Fire multiple events at scored + unscored origins.
    for oid, mag in [
        ("company:tsmc", 0.5),
        ("company:nvidia", 0.6),  # unscored
        ("company:asml", 0.4),
    ]:
        ev = _synthetic_event(oid, magnitude=mag)
        propagate_event(ev, g, c)

    for nid, n in g.nodes.items():
        prev_sev, prev_tier = before_baseline[nid]
        assert n.dynamic.baseline_severity == prev_sev, (
            f"{nid}: baseline_severity moved under events. "
            f"before={prev_sev} after={n.dynamic.baseline_severity}"
        )
        assert n.dynamic.baseline_tier == prev_tier, (
            f"{nid}: baseline_tier moved under events. "
            f"before={prev_tier} after={n.dynamic.baseline_tier}"
        )
