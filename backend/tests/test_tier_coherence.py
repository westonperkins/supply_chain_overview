"""Test 5 — Tier/severity coherence.

For every node: chokepoint_tier == derive_chokepoint_tier(baseline_severity).

Baseline severity is the node's static axes with no event delta applied.
scoring.yaml states thresholds apply to baseline severity, but the schema
today has only current_severity, which compute_baseline_severity writes
into. They are the same value until event ingestion arrives.

The schema gap is reported in _out/schema_gap.txt as a finding — this task
does not fix it, per scope.
"""
from pathlib import Path

from app.scoring import derive_chokepoint_tier

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def test_tier_matches_derive_from_current_severity(graph, config):
    mismatches = []
    for node in graph.nodes.values():
        expected = derive_chokepoint_tier(node.dynamic.current_severity or 0.0, config).value
        actual = (
            node.dynamic.chokepoint_tier.value if node.dynamic.chokepoint_tier else "none"
        )
        if expected != actual:
            mismatches.append(
                (node.id, node.dynamic.current_severity, expected, actual)
            )
    # Also record the schema gap as an artefact.
    gap_path = _OUT / "schema_gap.txt"
    gap_path.write_text(
        "FINDING — baseline vs current severity.\n"
        "\n"
        "scoring.yaml specifies chokepoint tier thresholds are applied to\n"
        "BASELINE severity — the node's static axes with no event delta.\n"
        "The schema today has only one field, `current_severity`, which\n"
        "`compute_baseline_severity` writes into. They are the same value\n"
        "today, so this test cannot distinguish them.\n"
        "\n"
        "Once event ingestion applies AxesImpact deltas, current_severity\n"
        "will drift with the news, and tiers derived from it will drift\n"
        "with the news too. Resolve before wiring live ingestion:\n"
        "  - add `baseline_severity` alongside `current_severity` on\n"
        "    DynamicFields\n"
        "  - `refresh_all_derived` writes baseline\n"
        "  - `propagate_event` writes current per-event, without touching\n"
        "    tier\n"
        "  - tier derived from baseline only\n"
    )
    assert not mismatches, mismatches[:5]
