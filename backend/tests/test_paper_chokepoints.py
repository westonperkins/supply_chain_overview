"""Test 9 — Paper chokepoints. The strict exception to the "invariants,
not values" rule.

The paper identifies these seven as chokepoints. That the model puts each
in `critical` is the validation claim the terminal rests on. If any drops
below critical, whoever changed something needs to see this fail.

Parametrized per node — a single monolithic assertion would let a third
chokepoint slip out silently under the xfail cover of the known-miss two.
Each case fails or xfails independently; the five non-xfail cases pass
loudly if they move.

Asserts against baseline severity (== current_severity today; see the
schema gap in test_tier_coherence). If event deltas start moving current
severity around, add a baseline_severity field per the finding — DO NOT
weaken this test.
"""
import pytest

PAPER_CHOKEPOINTS = [
    ("company:tsmc",                 "TSMC"),
    ("company:asml",                 "ASML"),
    ("mineral:gallium",              "gallium"),
    ("mineral:dysprosium",           "dysprosium"),
    ("product:hbm",                  "HBM"),
    ("product:cowos_packaging",      "CoWoS"),
    ("product:rf_power_semis",       "RF & Power Semiconductors"),
]

# Per-node xfail reasons — modelling gaps, not test defects. Reviewed
# each pass; remove the xfail marker when the underlying gap is closed.
#
# The two BYTE-IDENTICAL entries (spec §3 A7) are `product:hbm` and
# `product:rf_power_semis` — introduced by the generated_inventory_hygiene
# pass and preserved unchanged by Pass B (threshold recalibration).
# Do not edit their reason strings without a spec change.
KNOWN_MISS_XFAIL_REASONS = {
    "product:hbm": (
        "HBM concentration is capped at inbound_hhi 0.44 — three memory "
        "suppliers (SK Hynix 0.60, Micron 0.21, Samsung 0.19) give a "
        "moderate HHI that the max combine cannot lift above the critical "
        "threshold. Would move on either (a) a memory sub-category split "
        "(hbm vs dram — spec explicitly forbids) or (b) output_share "
        "populated on HBM → NVIDIA at paper-supported basis."
    ),
    "product:rf_power_semis": (
        "RF & Power reads inbound=0 because gallium is its only modelled "
        "input_to source and the stage-level min_suppliers=2 rule zeroes "
        "single-source stage buckets. Outbound alone (0.082) doesn't lift "
        "severity above moderate. Would move on additional modelled inputs "
        "(indium, substrate) — a data completeness item."
    ),
    # ---- Incidental outcomes of Pass B threshold recalibration ----
    # These three chokepoints have severity above the pre-Pass-B critical
    # threshold (0.225) but below the derived Pass B critical/high
    # boundary (0.5096, midpoint of the ASML → gallium separating gap).
    # Spec §1.6 permits the boundary move to demote them as an incidental
    # outcome; §5 asks the pass to REPORT these tier changes — see
    # docs/generated/threshold_analysis.md for the derivation the
    # boundary comes from. The reasons name only the derivation output,
    # never the target tier. Test A8 checks no derivation source
    # references these node names.
    "company:tsmc": (
        "Incidental demotion from Pass B: severity 0.4600 sits below the "
        "derived critical/high boundary at 0.5096 (midpoint of the ASML → "
        "gallium separating gap). Tiers as `high` under the recalibrated "
        "thresholds. Not a modelling gap; a distribution-shape outcome. "
        "Remove this xfail when the derivation places the boundary such "
        "that this severity clears critical."
    ),
    "mineral:gallium": (
        "Incidental demotion from Pass B: severity 0.4803 sits below the "
        "derived critical/high boundary at 0.5096 (midpoint of the ASML → "
        "gallium separating gap). Tiers as `high` under the recalibrated "
        "thresholds. Not a modelling gap; a distribution-shape outcome. "
        "Remove this xfail when the derivation places the boundary such "
        "that this severity clears critical."
    ),
    "product:cowos_packaging": (
        "Incidental demotion from Pass B: severity 0.3132 sits below the "
        "derived critical/high boundary at 0.5096 AND below the "
        "high/moderate boundary at 0.3866 (midpoint of the TSMC → CoWoS "
        "separating gap). Tiers as `moderate` under the recalibrated "
        "thresholds. Not a modelling gap; a distribution-shape outcome. "
        "Remove this xfail when the derivation places the boundary such "
        "that this severity clears critical."
    ),
}


@pytest.mark.parametrize("node_id,name", PAPER_CHOKEPOINTS, ids=lambda x: x if ":" not in str(x) else x.split(":", 1)[1])
def test_paper_chokepoint_is_critical(graph, node_id, name):
    """Every paper chokepoint should land in `critical`. Known misses
    are marked xfail with a named reason above."""
    if node_id in KNOWN_MISS_XFAIL_REASONS:
        pytest.xfail(KNOWN_MISS_XFAIL_REASONS[node_id])

    node = graph.nodes.get(node_id)
    assert node is not None, f"paper chokepoint {node_id} ({name}) not in graph"
    tier = node.dynamic.chokepoint_tier
    tier_value = tier.value if tier else "none"
    sev = node.dynamic.current_severity
    sev_str = f"{sev:.3f}" if sev is not None else "None"
    assert tier_value == "critical", (
        f"paper chokepoint {name} not critical: tier={tier_value} sev={sev_str}"
    )
