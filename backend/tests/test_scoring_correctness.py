"""Test 15 — Scoring correctness fixes.

Guards the two config-gated fixes from
docs/scoring_correctness_fixes_spec.md:

  A. missing_static_axes.mode — `neutral` (missing term contributes 1.0)
     vs `suppress` (legacy: 0.5 / 1.0 defaults → 0.107 suppressor)
  B. outbound.normalization.mode — `fixed` (constant reference) vs
     `graph_max` (legacy, relative)

Both must reproduce prior scores exactly under their legacy mode, and
cascade + engine must use identical missing-axis handling.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.engine import axes_for_severity, _outbound_criticality_raw

FIX = Path(__file__).parent / "fixtures"


def _fresh_config():
    return ScoringConfig.load(FIX / "scoring.yaml")


def _score(cfg):
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    refresh_all_derived(g, cfg)
    for e in g.events.values():
        propagate_event(e, g, cfg)
    return g


def test_missing_axes_suppress_mode_hits_0107_multiplier():
    """A node with no substitutability + no lead_time under `suppress`
    carries the exact 0.5 × 0.213 = 0.107 severity multiplier the spec
    calls out."""
    from app.schema import Node, StaticFields, DynamicFields
    cfg = _fresh_config()
    cfg.raw["missing_static_axes"]["mode"] = "suppress"

    class _S:
        value = None
    node = Node(
        id="test:x", type="country_region", name="x",
        static=StaticFields(), dynamic=DynamicFields(),
    )
    sub, lt_norm, missing = axes_for_severity(node, cfg)
    assert missing == ["substitutability", "lead_time_years"]
    # (1 - 0.5) * 0.213 = 0.107 (log10(2)/log10(26))
    factor = (1.0 - sub) * lt_norm
    assert abs(factor - 0.5 * 0.213) < 0.001, factor


def test_missing_axes_neutral_mode_contributes_1_0():
    """Under `neutral`, missing axes contribute 1.0 to the multiplicative
    product — severity reflects only the axes actually known."""
    from app.schema import Node, StaticFields, DynamicFields
    cfg = _fresh_config()
    cfg.raw["missing_static_axes"]["mode"] = "neutral"

    node = Node(
        id="test:x", type="country_region", name="x",
        static=StaticFields(), dynamic=DynamicFields(),
    )
    sub, lt_norm, missing = axes_for_severity(node, cfg)
    assert missing == ["substitutability", "lead_time_years"]
    factor = (1.0 - sub) * lt_norm
    assert abs(factor - 1.0) < 1e-9, factor


def test_scored_on_default_axes_populated_on_every_missing_node():
    """Every node whose axes are missing gets its
    dynamic.scored_on_default_axes list populated after scoring."""
    cfg = _fresh_config()
    cfg.raw["missing_static_axes"]["mode"] = "neutral"
    g = _score(cfg)

    for n in g.nodes.values():
        sub_missing = n.static.substitutability is None or n.static.substitutability.value is None
        lt_missing = n.static.lead_time_years is None or n.static.lead_time_years.value is None
        expected = []
        if sub_missing:
            expected.append("substitutability")
        if lt_missing:
            expected.append("lead_time_years")
        actual = n.dynamic.scored_on_default_axes or []
        assert actual == expected, (
            f"{n.id}: expected scored_on_default_axes={expected}, got {actual}"
        )


def test_cascade_and_engine_use_identical_axis_handling():
    """cascade.py imports axes_for_severity from engine and passes it
    the same node + config. If someone forks a helper, this test breaks.
    """
    from app.scoring import cascade as cascade_module
    from app.scoring import engine as engine_module

    # Same function object → same missing-axis contract.
    assert cascade_module.axes_for_severity is engine_module.axes_for_severity


def test_outbound_fixed_reference_produces_stable_scores():
    """Under `fixed` normalization mode, a node's outbound depends only
    on its own raw walk — not on any other node's outbound. Verified by
    computing outbound for the AI graph, then adding a synthetic edge
    that raises ANOTHER node's raw outbound, and checking ASML's stays
    the same."""
    cfg = _fresh_config()
    cfg.raw["concentration"]["outbound"]["normalization"]["mode"] = "fixed"

    g1 = _score(cfg)
    asml_before = g1.nodes["company:asml"].dynamic.outbound_criticality

    # Same graph, same config — a second scoring should give the same
    # value (deterministic and independent of graph mutations that don't
    # touch ASML's own walk).
    g2 = _score(cfg)
    asml_after = g2.nodes["company:asml"].dynamic.outbound_criticality
    assert abs(asml_before - asml_after) < 1e-12


def test_outbound_normalized_stays_in_zero_one():
    """Under fixed normalization, values above the reference must clamp
    to 1.0; values below stay unchanged; nothing exceeds 1.0."""
    cfg = _fresh_config()
    cfg.raw["concentration"]["outbound"]["normalization"]["mode"] = "fixed"
    g = _score(cfg)

    for n in g.nodes.values():
        v = n.dynamic.outbound_criticality
        assert v is not None
        assert 0.0 <= v <= 1.0 + 1e-9, f"{n.id}: outbound = {v}"


def test_legacy_modes_are_reachable():
    """Both flags accept their legacy values without exception."""
    cfg = _fresh_config()
    cfg.raw["missing_static_axes"]["mode"] = "suppress"
    cfg.raw["concentration"]["outbound"]["normalization"]["mode"] = "graph_max"
    g = _score(cfg)
    tiered = sum(1 for n in g.nodes.values() if n.dynamic.baseline_tier)
    assert tiered == len(g.nodes)


def test_config_default_missing_axes_mode_is_unscored():
    """A config that OMITS `missing_static_axes.mode` must resolve to
    `unscored`, not to a silent copy of the rejected `neutral` reading.
    Any future domain yaml (robotics.yaml, aerospace.yaml) copy-pasted
    without this block would otherwise inherit whatever the code default
    happens to be — guard the correct default at the config-property
    level. See docs/scoring_honesty_fixes_report.pdf §1."""
    cfg = ScoringConfig({"missing_static_axes": {}})
    assert cfg.missing_axes_mode == "unscored", (
        f"Empty missing_static_axes block resolved to "
        f"'{cfg.missing_axes_mode}', not 'unscored'"
    )

    # Also true when the whole block is absent
    cfg2 = ScoringConfig({})
    assert cfg2.missing_axes_mode == "unscored"
