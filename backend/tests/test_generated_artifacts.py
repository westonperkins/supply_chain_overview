"""Test 17 — Generated artifact staleness guards.

Every number the next three passes argue about lives in a file that
code wrote. These tests enforce that the committed files match what
the code produces — the drift this pass exists to close cannot recur
without failing here.

Guards:
  - node_inventory.md regenerates byte-for-byte from the current state
  - severity_diff.md regenerates byte-for-byte from snapshot vs current
  - severity_snapshot.json covers every graph node and vice versa
"""
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.graph import SupplyChainGraph
from app.reporting import build_inventory, build_severity_diff, snapshot_severity
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived

REPO = BACKEND.parent
FIXTURES = Path(__file__).parent / "fixtures"
GENERATED = REPO / "docs" / "generated"


def _score_from_fixtures():
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    c = ScoringConfig.load(FIXTURES / "scoring.yaml")
    refresh_all_derived(g, c)
    for e in g.events.values():
        propagate_event(e, g, c)
    return g, c


def test_node_inventory_matches_committed_file():
    """Regenerate the inventory in memory and byte-compare. Without
    this guard the file drifts from the code and the next pass argues
    against a stale table — the same failure this pass exists to close.
    """
    g, c = _score_from_fixtures()
    generated = build_inventory(g, c)
    committed = (GENERATED / "node_inventory.md").read_text()
    assert generated == committed, (
        "docs/generated/node_inventory.md is out of sync with the code.\n"
        "Regenerate: `python backend/scripts/generate_inventory.py`"
    )


def test_severity_diff_matches_committed_file():
    """Regenerate the diff against the committed snapshot and byte-compare."""
    g, _ = _score_from_fixtures()
    snapshot = json.loads((GENERATED / "severity_snapshot.json").read_text())
    generated = build_severity_diff(snapshot, g)
    committed = (GENERATED / "severity_diff.md").read_text()
    assert generated == committed, (
        "docs/generated/severity_diff.md is out of sync.\n"
        "Regenerate: `python backend/scripts/generate_inventory.py`"
    )


def test_severity_snapshot_covers_every_node():
    """Snapshot membership must match graph membership exactly — a
    missing node in the snapshot would silently drop from the diff."""
    g, _ = _score_from_fixtures()
    snapshot = json.loads((GENERATED / "severity_snapshot.json").read_text())
    graph_ids = {n.id for n in g.nodes.values()}
    snap_ids = set(snapshot.keys())
    assert graph_ids == snap_ids, (
        f"snapshot / graph membership mismatch. "
        f"only in graph: {graph_ids - snap_ids}; "
        f"only in snapshot: {snap_ids - graph_ids}"
    )


def test_inventory_sections_sum_to_full_graph():
    """Section A count + Section B count = total nodes. No node appears
    in both; none missing from either."""
    g, c = _score_from_fixtures()
    inventory = build_inventory(g, c)

    # Section A rows have severity in the 4th column; Section B rows are
    # under `## B.`. Simplest structural check: count table rows in each.
    lines = inventory.split("\n")
    in_a = False
    in_b = False
    a_rows = 0
    b_rows = 0
    for line in lines:
        if line.startswith("## A."):
            in_a, in_b = True, False
            continue
        if line.startswith("## B."):
            in_a, in_b = False, True
            continue
        if line.startswith("## C."):
            in_a, in_b = False, False
            continue
        if in_a and line.startswith("| ") and not line.startswith("| id ") \
                and not line.startswith("|---"):
            a_rows += 1
        if in_b and line.startswith("| ") and not line.startswith("| id ") \
                and not line.startswith("|---"):
            b_rows += 1

    scored = sum(1 for n in g.nodes.values() if n.dynamic.current_severity is not None)
    unscored = sum(1 for n in g.nodes.values() if n.dynamic.current_severity is None)
    assert a_rows == scored, f"Section A: {a_rows} rows vs {scored} scored"
    assert b_rows == unscored, f"Section B: {b_rows} rows vs {unscored} unscored"
    assert a_rows + b_rows == len(g.nodes), (
        f"A + B = {a_rows + b_rows} ≠ {len(g.nodes)} nodes"
    )


def test_snapshot_severity_returns_all_five_keys_per_node():
    g, _ = _score_from_fixtures()
    snap = snapshot_severity(g)
    required = {"severity", "tier", "concentration", "inbound_hhi", "outbound_criticality"}
    for nid, entry in snap.items():
        assert required.issubset(entry.keys()), (nid, entry.keys())
