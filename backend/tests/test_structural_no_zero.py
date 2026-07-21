"""Test 3 — Structural: no silent zeros.

No node with at least one inbound supply edge may have inbound_hhi == 0.
This is the assertion that would have caught the stage-list defect
(input_to and component_of missing from stages) without needing anyone to
notice a symptom.
"""
from .helpers import SHARE_STAGES


def test_no_node_with_inbound_supply_reads_zero(graph):
    offenders = []
    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares or {}
        has_inbound = any(
            k in SHARE_STAGES and v for k, v in derived.items()
        )
        if has_inbound and (node.dynamic.inbound_hhi or 0.0) == 0.0:
            offenders.append(node.id)
    assert not offenders, (
        f"{len(offenders)} node(s) with inbound supply edges but "
        f"inbound_hhi == 0: {offenders}"
    )
