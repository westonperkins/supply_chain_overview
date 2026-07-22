"""Test 3 — Structural: no silent zeros.

No node with at least one inbound supply edge may have inbound_hhi == 0
*unless* the stage-level min_suppliers rule has explicitly zeroed it —
in which case dynamic.all_stages_single_supplier is set. The rule change
is deliberate ("if every stage is single-supplier, no reliable signal,
report the node rather than fall back silently" — see spec §1 of
docs/outbound_output_share_spec.md). Silent zeros are still forbidden.
"""
from .helpers import SHARE_STAGES


def test_no_node_with_inbound_supply_reads_zero(graph):
    offenders = []
    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares or {}
        has_inbound = any(
            k in SHARE_STAGES and v for k, v in derived.items()
        )
        if not has_inbound:
            continue
        if (node.dynamic.inbound_hhi or 0.0) != 0.0:
            continue
        # Zero is allowed ONLY when the engine has flagged the node as
        # having every stage single-supplier — that is an explicit,
        # inspectable state, not a silent zero.
        if node.dynamic.all_stages_single_supplier:
            continue
        offenders.append(node.id)
    assert not offenders, (
        f"{len(offenders)} node(s) with inbound supply edges but "
        f"inbound_hhi == 0 without all_stages_single_supplier flag: "
        f"{offenders}"
    )
