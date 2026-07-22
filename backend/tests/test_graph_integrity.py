"""Test 8 — Graph integrity."""
from collections import Counter, defaultdict


def test_no_edge_references_unknown_node(graph):
    node_ids = set(graph.nodes)
    dangling = []
    for e in graph.edges.values():
        if e.source_id not in node_ids:
            dangling.append((e.id, "source", e.source_id))
        if e.target_id not in node_ids:
            dangling.append((e.id, "target", e.target_id))
    assert not dangling, dangling[:5]


def test_no_duplicate_edge_ids(graph):
    counts = Counter(e.id for e in graph.edges.values())
    dupes = [(eid, n) for eid, n in counts.items() if n > 1]
    assert not dupes, dupes


def test_no_self_edges(graph):
    self_edges = [e.id for e in graph.edges.values() if e.source_id == e.target_id]
    assert not self_edges, self_edges


def test_every_node_has_at_least_one_edge(graph):
    edged_ids: set[str] = set()
    for e in graph.edges.values():
        edged_ids.add(e.source_id)
        edged_ids.add(e.target_id)
    isolated = [n.id for n in graph.nodes.values() if n.id not in edged_ids]
    assert not isolated, isolated


def test_no_input_share_bucket_exceeds_one(graph):
    """No per-target, per-edge-type input_share bucket sums above 1.0.

    Scoped to edge types with target-input-share semantics: the members
    of SUPPLY_EDGE_TYPES. `located_in` is deliberately excluded — it's
    a categorical set-membership relation, not a share (verified: it's
    not in SUPPLY_EDGE_TYPES, so scoring never treats it as one).

    For `supplies` specifically, the invariant applies PER CATEGORY once
    per-category HHI is on — see test_no_per_category_supplies_exceeds_one.
    The aggregate bucket may exceed 1.0 when categories don't compete.
    """
    from app.schema.enums import SUPPLY_EDGE_TYPES
    share_types = {t.value for t in SUPPLY_EDGE_TYPES} - {"supplies"}
    sums: dict[tuple[str, str], float] = defaultdict(float)
    for e in graph.edges.values():
        if e.type.value not in share_types:
            continue
        sums[(e.target_id, e.type.value)] += e.input_share
    over = sorted(
        ((k, v) for k, v in sums.items() if v > 1.0 + 1e-9),
        key=lambda kv: -kv[1],
    )
    assert not over, f"{len(over)} bucket(s) exceed 1.0: {over[:5]}"


def test_no_per_category_supplies_bucket_exceeds_one(graph):
    """Per-category invariant: no (target, supply_category) supplies bucket
    exceeds 1.0. Under per-category semantics this is the invariant that
    matters — the aggregate supplies bucket may legitimately exceed 1.0
    when a target buys from multiple non-competing categories.
    """
    sums: dict[tuple[str, str], float] = defaultdict(float)
    for e in graph.edges.values():
        if e.type.value != "supplies":
            continue
        cat = e.supply_category or "general"
        sums[(e.target_id, cat)] += e.input_share
    over = sorted(
        ((k, v) for k, v in sums.items() if v > 1.0 + 1e-9),
        key=lambda kv: -kv[1],
    )
    assert not over, f"{len(over)} per-category bucket(s) exceed 1.0: {over[:5]}"


def test_gallium_mined_by_hhi_unchanged(graph):
    """Regression guard — this pass touches supplies only. Gallium's mining
    concentration comes from mines edges on the mineral node and MUST NOT
    move. Locks the paper §1A anchor across future refactors."""
    ga = graph.nodes["mineral:gallium"]
    hhi = ga.dynamic.mined_by_hhi
    assert hhi is not None, "gallium mined_by_hhi should be populated"
    assert hhi > 0.94, f"gallium mined_by_hhi regressed: {hhi}"


def test_output_share_has_provenance(graph):
    """Every populated output_share carries its own confidence + note.

    The model_validator on Edge enforces this at load time; this test
    documents the contract at the test-suite level and would catch a
    regression if the validator were ever softened.
    """
    missing: list[tuple[str, str]] = []
    for e in graph.edges.values():
        if e.output_share is None:
            continue
        if e.static.output_share_confidence is None:
            missing.append((e.id, "confidence"))
        if not e.static.output_share_source_note:
            missing.append((e.id, "source_note"))
    assert not missing, missing
