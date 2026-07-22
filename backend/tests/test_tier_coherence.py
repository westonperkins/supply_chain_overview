"""Test 5 — Tier/severity coherence.

For every node: baseline_tier == derive_chokepoint_tier(baseline_severity).
And current_tier == derive_chokepoint_tier(current_severity).

Pass D closed the schema gap this test used to record: the two tiers
are now separate fields (baseline_ and current_), and with no active
events they must be equal. See T1 in test_pass_d_baseline_current.
"""
from pathlib import Path

from app.scoring import derive_chokepoint_tier

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def _tier_value(tier):
    return tier.value if tier else "none"


def test_baseline_tier_matches_derive_from_baseline_severity(graph, config):
    mismatches = []
    for node in graph.nodes.values():
        expected = derive_chokepoint_tier(node.dynamic.baseline_severity, config).value
        actual = _tier_value(node.dynamic.baseline_tier)
        if expected != actual:
            mismatches.append(
                (node.id, node.dynamic.baseline_severity, expected, actual)
            )
    _OUT.joinpath("schema_gap.txt").write_text(
        "Pass D closed the baseline vs current severity split.\n"
        "This test no longer needs to record the schema gap.\n"
    )
    assert not mismatches, mismatches[:5]


def test_current_tier_matches_derive_from_current_severity(graph, config):
    mismatches = []
    for node in graph.nodes.values():
        expected = derive_chokepoint_tier(node.dynamic.current_severity, config).value
        actual = _tier_value(node.dynamic.current_tier)
        if expected != actual:
            mismatches.append(
                (node.id, node.dynamic.current_severity, expected, actual)
            )
    assert not mismatches, mismatches[:5]
