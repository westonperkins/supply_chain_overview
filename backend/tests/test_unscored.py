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
            assert n.dynamic.baseline_severity is None, (
                f"{n.id}: expected None severity, got {n.dynamic.baseline_severity}"
            )
            assert n.dynamic.baseline_tier == ChokepointTier.UNSCORED, (
                f"{n.id}: expected UNSCORED tier, got {n.dynamic.baseline_tier}"
            )


def test_no_unscored_node_appears_in_scored_tier_counts():
    """An unscored node must never surface in critical / high / moderate / none."""
    g = _score_with("unscored")
    scored_tiers = {"critical", "high", "moderate", "none"}
    offenders = []
    for n in g.nodes.values():
        if n.dynamic.baseline_severity is not None:
            continue
        tier = n.dynamic.baseline_tier
        if tier and tier.value in scored_tiers:
            offenders.append((n.id, tier.value))
    assert not offenders, offenders


def test_concentration_still_computes_for_unscored_nodes():
    """Only severity is withheld — concentration, HHI and derived shares
    continue to compute so the network structure remains inspectable."""
    g = _score_with("unscored")
    for n in g.nodes.values():
        if n.dynamic.baseline_tier != ChokepointTier.UNSCORED:
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
    tiered = sum(1 for n in g.nodes.values() if n.dynamic.baseline_tier)
    assert tiered == len(g.nodes)
    # No node should be UNSCORED under suppress
    unscored = [n.id for n in g.nodes.values()
                if n.dynamic.baseline_tier == ChokepointTier.UNSCORED]
    assert not unscored, unscored


def test_neutral_mode_still_reachable():
    g = _score_with("neutral")
    tiered = sum(1 for n in g.nodes.values() if n.dynamic.baseline_tier)
    assert tiered == len(g.nodes)
    unscored = [n.id for n in g.nodes.values()
                if n.dynamic.baseline_tier == ChokepointTier.UNSCORED]
    assert not unscored, unscored


def test_asml_is_rank_one_and_matches_fixed_reference():
    """`fixed_reference` is load-bearing AS THE GRAPH MAXIMUM. If ASML
    slips off rank 1 or another node reaches the reference, the ranking
    ties silently while a `rank <= 2` test would still pass. Guard with
    three tighter assertions:

      1. ASML is rank 1 exactly on raw outbound
      2. fixed_reference equals ASML's raw outbound (within tolerance)
      3. Zero nodes normalize to a clamped 1.0 — the reference is
         genuinely the max, not a value everything else caught up to
    """
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

    # (1) ASML is rank 1 exactly.
    assert ranked[0][0] == "company:asml", (
        f"ASML no longer rank 1 in raw outbound. Actual top-5: {ranked[:5]}"
    )

    # (2) fixed_reference matches ASML raw.
    ref = c.outbound_fixed_reference
    assert ref is not None, "fixed_reference not set in scoring.yaml"
    assert abs(ref - ranked[0][1]) < 1e-9, (
        f"fixed_reference={ref} does not match ASML raw={ranked[0][1]}. "
        f"Re-derive: `python backend/scripts/generate_inventory.py` then "
        f"update config/scoring.yaml."
    )

    # (3) Nothing else clamps at 1.0 — a tie would mean two nodes hit the
    # reference and the ranking is ambiguous.
    from app.scoring import refresh_all_derived
    refresh_all_derived(g, c)
    clamped_at_one = [
        n.name for n in g.nodes.values()
        if n.dynamic.outbound_criticality is not None
        and abs(n.dynamic.outbound_criticality - 1.0) < 1e-9
        and n.id != "company:asml"
    ]
    assert not clamped_at_one, (
        f"Nodes other than ASML clamp at outbound=1.0: {clamped_at_one}. "
        f"The fixed_reference is no longer the unique graph maximum."
    )
