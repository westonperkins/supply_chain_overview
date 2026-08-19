"""Test 16 — Unscored nodes.

Guards the `unscored` third mode for missing_static_axes.
Spec: docs/scoring_honesty_fixes_spec.md §1.
"""
import sys
from pathlib import Path

import pytest
import yaml

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.schema.enums import ChokepointTier

FIX = Path(__file__).parent / "fixtures"
REPO = BACKEND.parent


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
# Will not move without an explicit spec authorization and a full
# re-baseline of committed snapshots. Guarded by
# test_fixed_reference_is_frozen below.
#
# Pass U (FR-C, re-baseline Phase B) — authorizing spec. The constant
# moved from ASML's honesty-fixes raw outbound (1.6711394969476698) to
# a declared-arbitrary headroom value of 2.5, chosen above the current
# graph maximum raw outbound (mineral:copper, 2.0447548854281186) so
# nothing clamps and near-term growth does not re-clamp. This is the
# first invocation of this test's docstring clause permitting an
# authorized change. See config/scoring.yaml's fixed_reference comment
# block and docs/generated/replay/pass_u_report.pdf §3.
_FROZEN_FIXED_REFERENCE = 2.5


def test_top_outbound_anchor_is_expected_node():
    """Pass K.1 §5 rewrite — the load-bearing outbound-side node in the
    graph is asserted structurally so that if the ranking becomes
    silently ambiguous (rank-1 tie, unexpected node dislodges the
    anchor) the test fires.

    Pass K.1 originally asserted `ranked[0] == asml`. Pass R
    re-authored `copper → {tsmc, sk_hynix, micron, samsung,
    ge_vernova, siemens_energy}` from cost-basis (0.06-0.40) to
    dependency-basis (0.95 — copper damascene interconnects are a
    function-halt for leading-edge fabs; HV transformer + generator
    windings are copper-dominant for the power OEMs). The natural
    consequence: copper's raw outbound (2.04) now exceeds ASML's
    (1.77). Copper is the new rank-1 anchor.

    This is a structural claim change, not a defect. The re-baseline
    pass pre-approved in Pass P.5.2 will need to reconsider what
    `fixed_reference` normalises against (currently frozen at ASML's
    Pass K raw value 1.6711…). That decision is out of scope for the
    copper data pass and out of scope for this test — this test only
    records the current structural fact.

    The invariant survives: exactly one node is rank 1, no ties.
    Updates to the expected anchor need a matching update to this
    test in the same commit, citing the authorizing spec."""
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

    # Pass R — anchor moved from ASML to copper. Anchor changes go
    # here plus a ledger entry in docs/generated/replay/grading.md.
    expected_anchor = "mineral:copper"
    assert ranked[0][0] == expected_anchor, (
        f"{expected_anchor} no longer rank 1 in raw outbound. Actual "
        f"top-5: {ranked[:5]}. If the anchor genuinely moved, update "
        f"this test and record the change in grading.md; do not silently "
        f"accommodate."
    )
    # No tie at rank 1 — an ambiguous ranking is a structural defect.
    assert ranked[0][1] > ranked[1][1], (
        f"rank-1 tie in raw outbound: {ranked[:2]}"
    )


def _assert_fixed_reference_frozen(ref: float) -> None:
    """Raises AssertionError if `ref` differs from the frozen literal.

    Pass U §4 — extracted from `test_fixed_reference_is_frozen` so a
    proof-of-guard test can exercise the failure branch without editing
    any scoring.yaml on disk. Mirrors the shape `test_thresholds_frozen`
    already uses for the boundaries guard (`_assert_frozen`); before
    Pass U the boundaries guard proved itself and this one never did."""
    assert ref == _FROZEN_FIXED_REFERENCE, (
        f"`fixed_reference` moved from the frozen literal "
        f"{_FROZEN_FIXED_REFERENCE!r} to {ref!r}. If the change is "
        f"authorized by a spec, update _FROZEN_FIXED_REFERENCE in the "
        f"same commit and cite the spec. Do not update the constant "
        f"alone — the defect this test catches is silent drift, not the "
        f"value itself."
    )


def _load_fixed_reference(scoring_yaml: Path) -> float:
    """Read `fixed_reference` straight from a scoring.yaml on disk."""
    raw = yaml.safe_load(scoring_yaml.read_text())
    return raw["concentration"]["outbound"]["normalization"]["fixed_reference"]


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
    _assert_fixed_reference_frozen(c.outbound_fixed_reference)


def test_config_fixed_reference_is_frozen():
    """Pass U §4 — guard the COMMITTED config, not only the fixture.

    Gap this closes: `test_fixed_reference_is_frozen` above reads
    `FIX / scoring.yaml` (the test fixture). Since Pass K.1 froze the
    constant, nothing had ever asserted that `config/scoring.yaml` — the
    file the engine and the generator actually load — carries the frozen
    value. The two were kept in sync by hand; if the real config drifted
    while the fixture stayed put, the freeze stayed green. This reads the
    repo config directly."""
    ref = _load_fixed_reference(REPO / "config" / "scoring.yaml")
    _assert_fixed_reference_frozen(ref)


def test_config_and_fixture_fixed_reference_agree():
    """Pass U §4 — the sync itself is now checked, not assumed.

    `test_fixtures_and_data_are_content_identical` asserts whole-file
    identity, but that guard lives in a different module and compares
    entire files; this one pins the specific invariant Pass K.1 cares
    about (the two `fixed_reference` values agree) so a drift is
    reported against the constant by name."""
    repo_ref = _load_fixed_reference(REPO / "config" / "scoring.yaml")
    fix_ref = _load_fixed_reference(FIX / "scoring.yaml")
    assert repo_ref == fix_ref, (
        f"`fixed_reference` differs between config/scoring.yaml "
        f"({repo_ref!r}) and backend/tests/fixtures/scoring.yaml "
        f"({fix_ref!r}). The fixture must mirror the committed config; "
        f"update both in the same commit."
    )


def test_guard_actually_fails_when_fixed_reference_drifts():
    """Pass U §4 proof-of-guard (spec §4.6: prove it, don't assert it).

    Feed `_assert_fixed_reference_frozen` a drifted value. If the guard
    silently accepts it the whole freeze is theatre. The boundaries
    guard has had this proof since Pass P (`_assert_frozen`); the
    `fixed_reference` guard never did until Pass U."""
    drifted = _FROZEN_FIXED_REFERENCE + 1e-9
    with pytest.raises(AssertionError) as exc_info:
        _assert_fixed_reference_frozen(drifted)
    msg = str(exc_info.value)
    assert "fixed_reference" in msg
    assert "spec" in msg
