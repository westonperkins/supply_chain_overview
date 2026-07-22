"""Test 13 — Stage-level completeness.

Same rule as per-category HHI one level up: a stage bucket with fewer
than min_suppliers modelled sources cannot distinguish a real monopoly
from unmodelled data. See docs/outbound_output_share_report.md §1 and
config/scoring.yaml (concentration.inbound.per_stage.min_suppliers_for_concentration).
"""
from collections import defaultdict
from pathlib import Path

from app.graph.graph import SHARE_INTO_TARGET

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def _single_supplier_stages(graph):
    """{(target_id, stage_name): [source_id]} where the stage bucket has
    fewer than 2 modelled sources."""
    # Match the scoring engine's read: derived_shares only tracks
    # SHARE_INTO_TARGET types (mines / refines / supplies / input_to /
    # component_of). `operates` is a SUPPLY_EDGE_TYPE for cascade purposes
    # but never enters the target's share map, so it can't be single-
    # supplier "in the HHI sense."
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    share_types = {t.value for t in SHARE_INTO_TARGET}
    for edge in graph.edges.values():
        if edge.type.value not in share_types:
            continue
        buckets[(edge.target_id, edge.type.value)].append(edge.source_id)
    return {k: v for k, v in buckets.items() if len(v) < 2}


def _write_gaps(rows, graph):
    path = _OUT / "single_supplier_stages.txt"
    with path.open("w") as f:
        if not rows:
            f.write("no single-supplier stages — nothing in the backlog\n")
            return
        f.write(f"stage-level completeness backlog — {len(rows)} single-\n"
                f"supplier stage bucket(s)\n")
        f.write(f"{'node':<38} {'stage':<14} {'sole source':<30}\n")
        for (tgt_id, stage), sources in sorted(rows.items()):
            name = graph.nodes[tgt_id].name if tgt_id in graph.nodes else tgt_id
            f.write(f"{name[:38]:<38} {stage:<14} {sources[0]:<30}\n")


def test_every_single_supplier_stage_is_in_backlog(graph):
    """Every stage bucket with < 2 sources must be recorded on the node's
    dynamic.single_supplier_stages and written to the backlog."""
    rows = _single_supplier_stages(graph)
    _write_gaps(rows, graph)

    mismatches = []
    by_node: dict[str, set[str]] = defaultdict(set)
    for (tgt_id, stage), _ in rows.items():
        by_node[tgt_id].add(stage)
    for tgt_id, stages_from_data in by_node.items():
        node = graph.nodes[tgt_id]
        engine_says = set(node.dynamic.single_supplier_stages or [])
        if engine_says != stages_from_data:
            mismatches.append(
                (node.name, stages_from_data - engine_says, engine_says - stages_from_data)
            )
    assert not mismatches, (
        f"{len(mismatches)} node(s) with engine/data mismatch on "
        f"single_supplier_stages: {mismatches[:3]}"
    )


def test_no_single_supplier_stage_bucket_contributes(graph):
    """A stage with < 2 sources must not contribute to inbound_hhi. When
    ALL stages on a node are single-supplier, inbound_hhi is 0 and the
    node is flagged (`all_stages_single_supplier`)."""
    for node in graph.nodes.values():
        single = set(node.dynamic.single_supplier_stages or [])
        stage_hhis = node.dynamic.stage_hhis or {}
        if not single or not stage_hhis:
            continue
        multi_stages = {s: h for s, h in stage_hhis.items() if s not in single}
        if node.dynamic.all_stages_single_supplier:
            assert (node.dynamic.inbound_hhi or 0.0) == 0.0, (
                f"{node.name}: all_stages_single_supplier flagged but "
                f"inbound_hhi = {node.dynamic.inbound_hhi}"
            )
            continue
        # There are multi-supplier stages — inbound must come from them.
        expected_max = max(multi_stages.values())
        actual = node.dynamic.inbound_hhi or 0.0
        assert abs(actual - expected_max) < 1e-9, (
            f"{node.name}: inbound_hhi={actual} but max of multi-supplier "
            f"stages = {expected_max} (single excluded: {single})"
        )
