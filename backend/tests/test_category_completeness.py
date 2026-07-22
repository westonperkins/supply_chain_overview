"""Test 12 — Category completeness.

Per-category HHI treats a category with only one modelled supplier as
incomplete data (see `docs/category_validation_spec.md` §2), because
HHI 1.0 by construction cannot distinguish a real monopoly from an
unmodelled market.

This test guarantees every single-supplier category surfaces in the
backlog so the completeness gap is tracked. Values themselves are
inspected in a written artefact — the test asserts only that they are
recorded, not their tier consequences (that's `test_paper_chokepoints`
and `test_tier_coherence`).
"""
from collections import defaultdict
from pathlib import Path

from app.schema.enums import EdgeType

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def _single_supplier_categories(graph):
    """Return {(node_id, node_name): [(category, single_supplier_id), …]}
    for every (target, supply_category) bucket with < 2 modelled suppliers."""
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for edge in graph.edges.values():
        if edge.type != EdgeType.SUPPLIES:
            continue
        cat = edge.supply_category or "general"
        buckets[(edge.target_id, cat)].append(edge.source_id)
    rows = defaultdict(list)
    for (tgt_id, cat), sources in buckets.items():
        if len(sources) < 2:
            node = graph.nodes[tgt_id]
            rows[(tgt_id, node.name)].append((cat, sources[0]))
    return dict(rows)


def _write_gaps(rows):
    path = _OUT / "category_gaps.txt"
    with path.open("w") as f:
        if not rows:
            f.write("no single-supplier categories — nothing in the backlog\n")
            return
        n_cats = sum(len(v) for v in rows.values())
        f.write(
            f"category-completeness backlog — {n_cats} single-supplier "
            f"category bucket(s) across {len(rows)} node(s)\n"
        )
        f.write(f"{'node':<38} {'category':<20} {'sole supplier':<30}\n")
        for (tgt_id, name), cats in sorted(rows.items()):
            for cat, src in sorted(cats):
                f.write(f"{name[:38]:<38} {cat:<20} {src:<30}\n")


def test_every_single_supplier_category_is_in_backlog(graph):
    """A single-supplier category must never contribute to concentration
    signal — it belongs in the completeness backlog, not in the tier."""
    rows = _single_supplier_categories(graph)
    _write_gaps(rows)

    # For every node that has ANY single-supplier categories, the engine
    # must have populated node.dynamic.single_supplier_categories with
    # exactly the same set. This closes the loop: whatever the data says
    # is single-supplier, the engine agrees is single-supplier.
    mismatches = []
    for (tgt_id, name), cats in rows.items():
        node = graph.nodes[tgt_id]
        engine_says = set(node.dynamic.single_supplier_categories or [])
        data_says = {c for c, _ in cats}
        if engine_says != data_says:
            mismatches.append((name, data_says - engine_says, engine_says - data_says))
    assert not mismatches, (
        f"{len(mismatches)} node(s) have engine/data mismatch on "
        f"single_supplier_categories: {mismatches[:3]}"
    )


def test_no_single_supplier_category_contributes_to_supplies_hhi(graph):
    """If a category has < 2 modelled suppliers, its per-category HHI must
    not be the value selected by the max combine — unless every category
    on the node is single-supplier, in which case supplies HHI falls back
    to the aggregate reading (flagged on node.dynamic)."""
    for node in graph.nodes.values():
        per_cat = node.dynamic.supplies_per_category_hhi
        single = set(node.dynamic.single_supplier_categories or [])
        if not per_cat or not single:
            continue
        if node.dynamic.supplies_hhi_fallback_to_aggregate:
            continue  # every category is single-supplier → aggregate is used
        multi = {c: h for c, h in per_cat.items() if c not in single}
        assert multi, (
            f"{node.name}: has single-supplier categories {single} and per_cat "
            f"HHIs {per_cat}, but no multi-supplier categories, yet did not "
            f"flag supplies_hhi_fallback_to_aggregate."
        )
        expected_max = max(multi.values())
        actual = node.dynamic.supplied_by_hhi
        # actual may be None if node has no supplies edges at all
        if actual is None:
            continue
        assert abs(actual - expected_max) < 1e-9, (
            f"{node.name}: supplied_by_hhi={actual} but expected "
            f"max of multi-supplier categories = {expected_max} "
            f"(single-supplier excluded: {single})"
        )
