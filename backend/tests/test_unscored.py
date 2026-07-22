"""Test 16 — Unscored nodes.

Guards the `unscored` third mode for missing_static_axes.
Spec: docs/scoring_honesty_fixes_spec.md §1.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.schema.enums import ChokepointTier

FIX = Path(__file__).parent / "fixtures"


def _score_with(axes_mode):
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    c = ScoringConfig.load(FIX / "scoring.yaml")
    c.raw["missing_static_axes"]["mode"] = axes_mode
    refresh_all_derived(g, c)
    for e in g.events.values():
        propagate_event(e, g, c)
    return g


def test_unscored_default_produces_none_severity_and_unscored_tier():
    g = _score_with("unscored")
    for n in g.nodes.values():
        sub_missing = n.static.substitutability is None or n.static.substitutability.value is None
        lt_missing = n.static.lead_time_years is None or n.static.lead_time_years.value is None
        if sub_missing or lt_missing:
            assert n.dynamic.current_severity is None, (
                f"{n.id}: expected None severity, got {n.dynamic.current_severity}"
            )
            assert n.dynamic.chokepoint_tier == ChokepointTier.UNSCORED, (
                f"{n.id}: expected UNSCORED tier, got {n.dynamic.chokepoint_tier}"
            )


def test_no_unscored_node_appears_in_scored_tier_counts():
    """An unscored node must never surface in critical / high / moderate / none."""
    g = _score_with("unscored")
    scored_tiers = {"critical", "high", "moderate", "none"}
    offenders = []
    for n in g.nodes.values():
        if n.dynamic.current_severity is not None:
            continue
        tier = n.dynamic.chokepoint_tier
        if tier and tier.value in scored_tiers:
            offenders.append((n.id, tier.value))
    assert not offenders, offenders


def test_concentration_still_computes_for_unscored_nodes():
    """Only severity is withheld — concentration, HHI and derived shares
    continue to compute so the network structure remains inspectable."""
    g = _score_with("unscored")
    for n in g.nodes.values():
        if n.dynamic.chokepoint_tier != ChokepointTier.UNSCORED:
            continue
        # concentration is the "combine of inbound + outbound"; must not
        # be forced to None because the node is unscored.
        assert n.dynamic.concentration is not None, (
            f"{n.id}: concentration should compute even for unscored nodes"
        )
        assert n.dynamic.outbound_criticality is not None, (
            f"{n.id}: outbound_criticality should compute for unscored nodes"
        )


def test_scored_on_default_axes_names_missing_axes():
    g = _score_with("unscored")
    for n in g.nodes.values():
        sub_missing = n.static.substitutability is None or n.static.substitutability.value is None
        lt_missing = n.static.lead_time_years is None or n.static.lead_time_years.value is None
        expected = []
        if sub_missing:
            expected.append("substitutability")
        if lt_missing:
            expected.append("lead_time_years")
        actual = n.dynamic.scored_on_default_axes or []
        assert actual == expected, (n.id, expected, actual)


def test_suppress_mode_still_reachable():
    g = _score_with("suppress")
    tiered = sum(1 for n in g.nodes.values() if n.dynamic.chokepoint_tier)
    assert tiered == len(g.nodes)
    # No node should be UNSCORED under suppress
    unscored = [n.id for n in g.nodes.values()
                if n.dynamic.chokepoint_tier == ChokepointTier.UNSCORED]
    assert not unscored, unscored


def test_neutral_mode_still_reachable():
    g = _score_with("neutral")
    tiered = sum(1 for n in g.nodes.values() if n.dynamic.chokepoint_tier)
    assert tiered == len(g.nodes)
    unscored = [n.id for n in g.nodes.values()
                if n.dynamic.chokepoint_tier == ChokepointTier.UNSCORED]
    assert not unscored, unscored


def test_asml_ranks_at_or_near_top_of_raw_outbound():
    """Sanity: under uniform input_share, ASML's raw outbound is at or
    near the graph max. The wrong-quantity contamination that put KLA
    above ASML in the previous pass is closed."""
    from app.scoring.engine import _outbound_criticality_raw
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    c = ScoringConfig.load(FIX / "scoring.yaml")
    decay = c.concentration_outbound_decay
    max_hops = c.concentration_outbound_max_hops
    min_influence = c.concentration_outbound_min_influence
    share_field = c.outbound_share_field
    fallback = c.outbound_fallback_to_input_share

    raw = {
        nid: _outbound_criticality_raw(
            nid, g, decay, max_hops, min_influence,
            share_field=share_field, fallback=fallback,
        )
        for nid in g.nodes
    }
    ranked = sorted(raw.items(), key=lambda kv: -kv[1])
    asml_rank = next(i for i, (nid, _) in enumerate(ranked) if nid == "company:asml")
    assert asml_rank <= 2, (
        f"ASML now ranks #{asml_rank + 1} in raw outbound; expected top 3. "
        f"Top-5: {ranked[:5]}"
    )
