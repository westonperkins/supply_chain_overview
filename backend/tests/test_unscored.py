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


# Pass K.1 §5 — frozen scale-constant literal for `fixed_reference`.
# Restored from Pass H honesty-fixes pass; will not move without an
# explicit spec authorization and a full re-baseline of committed
# snapshots. Guarded by test_fixed_reference_is_frozen below.
_FROZEN_FIXED_REFERENCE = 1.6711394969476698


def test_asml_is_rank_one_in_raw_outbound():
    """Pass K.1 §5 rewrite — ASML remaining #1 in raw outbound is a
    structural claim about the graph, not a claim about `fixed_reference`.
    The two were coupled in Pass K by an "assert fixed_reference == ASML
    raw" check; that check was the exact re-derivation defect §2 Option A
    exists to prevent. It is deleted here.

    What survives: ASML is the load-bearing outbound-side node in the
    graph; if it slips off rank 1 or another node ties, the ranking is
    silently ambiguous. Guard that structural fact independently."""
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

    assert ranked[0][0] == "company:asml", (
        f"ASML no longer rank 1 in raw outbound. Actual top-5: {ranked[:5]}"
    )


def test_fixed_reference_is_frozen():
    """Pass K.1 §5 — `fixed_reference` is a scale constant.

    Its value being able to move UNOBSERVED was the Pass K defect (§2).
    This test pins the literal so any future drift fails loudly at the
    config level. Do NOT update the literal to "match the graph" — that
    is `graph_max` mode wearing `fixed`'s name, and the whole point of
    Option A is to prevent that.

    A legitimate change to this constant requires:
      1. an explicit spec authorization stating why
      2. a full re-baseline of every committed severity snapshot
      3. updating this literal in the SAME commit as the config change
    See `config/scoring.yaml` comment on the constant for detail.
    """
    c = ScoringConfig.load(FIX / "scoring.yaml")
    ref = c.outbound_fixed_reference
    assert ref == _FROZEN_FIXED_REFERENCE, (
        f"`fixed_reference` moved from the frozen literal "
        f"{_FROZEN_FIXED_REFERENCE!r} to {ref!r}. If the change is "
        f"authorized by a spec, update _FROZEN_FIXED_REFERENCE in the "
        f"same commit and cite the spec. Do not update the constant "
        f"alone — the defect this test catches is silent drift, not the "
        f"value itself."
    )
