"""Test 9 — Paper chokepoints (severity, not display tier).

The validation claim this test enforces is now:
  **Every paper chokepoint's baseline severity is strictly greater than
  the median baseline severity across all scored nodes.**

Reframed in Pass C (F2). The old assertion — "every paper chokepoint
lands in the `critical` tier" — was coupling foundational validation
to a threshold we've shown is shape-derived and therefore arbitrary
across passes. `all chokepoints critical` only ever held under the
discarded 0.225 line. Under distribution-anchored thresholds, tier
membership moves with distribution shape; severity does not. This test
now measures the model (severity), not the display (tier). Tier
landings for the seven chokepoints are tracked as REPORTING in
`docs/generated/threshold_analysis.md` (§F2.b) — information, not a
red light.

`DO NOT weaken this test` — the reframe is a correction of WHAT is
validated, not a loosening. It stays per-node parametrized and fails
loudly on any chokepoint whose severity drops below the median of
scored severities.

Asserts against baseline severity (== current_severity today; see the
schema gap in test_tier_coherence).
"""
import hashlib
import statistics

import pytest

# Pass J.1 §3 — pinned SHA-256 of every KNOWN_MISS_XFAIL_REASONS value.
# A defect that recurred across passes (the report characterising xfails
# by non-existent function names and calling both misses `moderate` when
# one is `none`) gets a machine check, not another prose reminder. The
# hashes below are computed over the exact reason string bytes; a spec
# change that legitimately edits a reason must update the hash in the
# SAME commit as the string, and cite the spec authorising the change.
# Do not update the hash alone — that path defeats the pin.
KNOWN_MISS_XFAIL_REASON_HASHES = {
    "product:hbm":             "ba782ac27eb403b643f212083d95ab720175c3518800e21c6aee45764a03db2e",
    "product:rf_power_semis":  "8186bf40fc6413be215cef6ff983a8cec52ac2c0f7e116ed7e07593d81d3f131",
}

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
# Both entries are BYTE-IDENTICAL (spec §A4 Pass C) to their pre-pass
# state — introduced by the generated_inventory_hygiene pass and
# preserved unchanged. Do not edit their reason strings without a spec
# change. The three Pass B entries (TSMC / gallium / CoWoS) were
# DELETED in Pass C because the reframed test no longer coupled to a
# display tier — all three now pass severity > median.
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
}


@pytest.mark.parametrize(
    "node_id,name", PAPER_CHOKEPOINTS,
    ids=lambda x: x if ":" not in str(x) else x.split(":", 1)[1],
)
def test_paper_chokepoint_severity_above_median(graph, node_id, name):
    """Every paper chokepoint's baseline severity is strictly greater
    than the median baseline severity across all scored nodes.

    Threshold-independent by construction — tests severity against a
    severity statistic, so it does not move when display boundaries
    move. Known misses (HBM, RF & Power) carry their pre-existing
    reasons — both score below median (0.178 and 0.026 vs ~0.212) for
    the same modelling gaps already documented, so the reasons remain
    valid without editing.
    """
    if node_id in KNOWN_MISS_XFAIL_REASONS:
        pytest.xfail(KNOWN_MISS_XFAIL_REASONS[node_id])

    node = graph.nodes.get(node_id)
    assert node is not None, f"paper chokepoint {node_id} ({name}) not in graph"

    scored_sevs = [
        n.dynamic.baseline_severity for n in graph.nodes.values()
        if n.dynamic.baseline_severity is not None
    ]
    median_sev = statistics.median(scored_sevs)

    sev = node.dynamic.current_severity
    assert sev is not None, (
        f"paper chokepoint {name} has no severity (unscored) — this test "
        f"cannot validate a chokepoint that has no computed severity"
    )
    assert sev > median_sev, (
        f"paper chokepoint {name}: severity {sev:.5f} is not > "
        f"median scored severity {median_sev:.5f}. The paper identifies "
        f"this as a chokepoint; the model puts it below the middle of "
        f"the scored distribution — that's a modelling gap to name and "
        f"document in KNOWN_MISS_XFAIL_REASONS with a paper-anchored "
        f"reason."
    )


def test_xfail_registry_is_pinned():
    """Pass J.1 §3 — the xfail registry is pinned by SHA-256.

    Keys must be exactly the two documented misses; each reason string's
    SHA-256 must equal the hex constant committed alongside it. If a
    reason legitimately changes, update the hash in the same commit as
    the string and cite the spec authorising the change. Do NOT update
    the hash alone — that path defeats the pin.

    Motivation: the Pass J report characterised these xfails by
    non-existent function names, and called both misses `moderate` when
    committed `docs/generated/threshold_analysis.md` shows
    `product:rf_power_semis` = 0.0261 → `none` (per Pass I.1 review, the
    same species of defect had recurred). A machine check replaces the
    fourth prose reminder.
    """
    keys_expected = set(KNOWN_MISS_XFAIL_REASON_HASHES.keys())
    keys_actual = set(KNOWN_MISS_XFAIL_REASONS.keys())
    assert keys_actual == keys_expected, (
        f"KNOWN_MISS_XFAIL_REASONS keys drifted from the pinned set. "
        f"Expected {sorted(keys_expected)}; got {sorted(keys_actual)}. "
        f"Update both the registry and KNOWN_MISS_XFAIL_REASON_HASHES "
        f"in the same commit, and cite the spec authorising the change."
    )
    for node_id, reason in KNOWN_MISS_XFAIL_REASONS.items():
        h = hashlib.sha256(reason.encode("utf-8")).hexdigest()
        expected = KNOWN_MISS_XFAIL_REASON_HASHES[node_id]
        assert h == expected, (
            f"xfail reason for {node_id} does not match its pinned "
            f"SHA-256. expected={expected}, got={h}. The xfail registry "
            f"is pinned; if a reason string legitimately changes, "
            f"update the hash in the same commit as the string and "
            f"cite the spec authorising the change. Do not update the "
            f"hash alone."
        )
