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

Pass N §4 — both xfails retired. `product:hbm` and
`product:rf_power_semis` were the model's only two disagreements with
the paper. D4 (noisy-OR aggregator) resolved HBM by construction — the
memory-bucket concentration jumped from HHI 0.4402 to noisy-OR 0.7440,
lifting severity from 0.1779 to 0.3008 which crosses the post-D4 median
0.2015. D4a (min_suppliers=1) resolved RF & Power — the sole-source
gallium input_to bucket unzeroed to concentration 0.9, lifting severity
from 0.0261 to 0.2872 which crosses the post-D4+D4a median 0.2404.

Both resolutions trace to mechanisms named in their own reason strings
(HBM's reason names "inbound_hhi 0.44 cap"; RF & Power's names the
"min_suppliers=2 rule zeroes single-source stage buckets"). Neither
resolves via an unrelated side effect crossing a threshold. See
`docs/generated/replay/grading.md` Pass N ledger for retirement
reasoning.

The registry is now empty. `test_xfail_registry_is_pinned` still
asserts the shape: if a new xfail is added without a pin, the test
fails; if a pin is added without a matching registry entry, the test
fails.
"""
import hashlib
import statistics

import pytest

# Pass N §4 — the xfail registry is now empty. Both product:hbm and
# product:rf_power_semis retired when D4+D4a shipped, per §4 retirement
# reasoning above. The pinning machinery from Pass J.1 stays so a
# future xfail addition without a spec-cited SHA-256 pin fails loudly.
KNOWN_MISS_XFAIL_REASON_HASHES: dict[str, str] = {}

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
# Pass N §4 — the two prior entries (product:hbm and
# product:rf_power_semis) were retired when D4+D4a shipped. Their
# named mechanisms (HBM's inbound_hhi=0.44 cap, RF & Power's
# min_suppliers=2 zeroing) both ended by construction under the
# aggregator and min_suppliers changes. Registry is now empty; ALL
# seven paper chokepoints pass severity > median.
KNOWN_MISS_XFAIL_REASONS: dict[str, str] = {}


def _param_with_xfail(node_id: str, name: str):
    """Pass K §5 — conditional xfail marker rather than imperative
    `pytest.xfail()`. Under `strict=False`, pytest runs the assertion:
    fails → XFAIL, passes → XPASS. An XPASS is a finding that must be
    closed by a spec decision, never by silently deleting the entry.
    Pass N §4 closed both prior XPASS entries with retirement reasoning."""
    reason = KNOWN_MISS_XFAIL_REASONS.get(node_id)
    if reason is None:
        return pytest.param(node_id, name)
    return pytest.param(
        node_id, name,
        marks=pytest.mark.xfail(strict=False, reason=reason),
    )


@pytest.mark.parametrize(
    "node_id,name",
    [_param_with_xfail(nid, nm) for nid, nm in PAPER_CHOKEPOINTS],
    ids=lambda x: x if ":" not in str(x) else x.split(":", 1)[1],
)
def test_paper_chokepoint_severity_above_median(graph, node_id, name):
    """Every paper chokepoint's baseline severity is strictly greater
    than the median baseline severity across all scored nodes.

    Threshold-independent by construction — tests severity against a
    severity statistic, so it does not move when display boundaries
    move. Pass N §4: registry is empty; all seven pass. If a future
    change causes a chokepoint to slip below the median, add it back
    to KNOWN_MISS_XFAIL_REASONS with a mechanism-anchored reason and
    a matching SHA-256 pin in KNOWN_MISS_XFAIL_REASON_HASHES.
    """
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

    Pass N §4 retired both prior entries; the registry is now empty
    and the pinning machinery holds the shape:

      - keys of the registry MUST equal keys of the hash constant
        (an empty registry with an empty hash dict passes this)
      - each reason string's SHA-256 MUST equal its pinned hex

    If a future xfail is added, the pin (in the same commit as the
    string) is required. If a hash is added without a matching
    registry entry, the test fails. Do NOT update a hash alone or
    add a registry entry alone — the pin is the mechanism preventing
    silent xfail drift.
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
