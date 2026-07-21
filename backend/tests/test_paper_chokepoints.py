"""Test 9 — Paper chokepoints. The strict exception to the "invariants,
not values" rule.

The paper identifies these seven as chokepoints. That the model puts each
in `critical` is the validation claim the terminal rests on. If any drops
below critical, whoever changed something needs to see this fail.

Asserts against baseline severity (== current_severity today; see the
schema gap in test_tier_coherence). If event deltas start moving current
severity around, add a baseline_severity field per the finding — DO NOT
weaken this test.
"""
PAPER_CHOKEPOINTS = [
    ("company:tsmc",                 "TSMC"),
    ("company:asml",                 "ASML"),
    ("mineral:gallium",              "gallium"),
    ("mineral:dysprosium",           "dysprosium"),
    ("product:hbm",                  "HBM"),
    ("product:cowos_packaging",      "CoWoS"),
    ("product:rf_power_semis",       "RF & Power Semiconductors"),
]


def test_every_paper_chokepoint_is_critical(graph):
    misses = []
    for node_id, name in PAPER_CHOKEPOINTS:
        node = graph.nodes.get(node_id)
        assert node is not None, f"paper chokepoint {node_id} ({name}) not in graph"
        tier = node.dynamic.chokepoint_tier
        tier_value = tier.value if tier else "none"
        if tier_value != "critical":
            misses.append((name, tier_value, node.dynamic.current_severity))
    assert not misses, (
        "paper chokepoints not landing in critical: "
        + "; ".join(f"{n}={t} (sev={s:.3f})" for n, t, s in misses)
    )
