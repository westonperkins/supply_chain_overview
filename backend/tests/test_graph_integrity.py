"""Test 8 — Graph integrity."""
from collections import Counter


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
