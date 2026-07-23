"""Pass I Part 5 — coordinates audit.

Counts how many nodes carry populated `coordinates` (lat + lng) versus how
many don't, grouped by node type. No map is drawn; this is a data-quality
report that answers "if we ever drop a map into Level 0, how much of the
graph would even land somewhere?".

Runs read-only — never writes to data/ or docs/. Prints a table to stdout.
Included in the Pass I PDF report; not committed as a markdown artifact
per the project's PDF-only rule for reports.
"""
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph


def audit(graph: SupplyChainGraph) -> None:
    by_type: dict[str, list[str]] = defaultdict(list)
    populated_by_type: dict[str, list[str]] = defaultdict(list)

    for node in graph.nodes.values():
        by_type[node.type.value].append(node.id)
        if node.coordinates is not None:
            populated_by_type[node.type.value].append(node.id)

    total_nodes = sum(len(v) for v in by_type.values())
    total_pop = sum(len(v) for v in populated_by_type.values())

    print(f"Coordinates audit — {total_pop}/{total_nodes} nodes have populated (lat, lng).\n")
    print(f"{'node type':<20} {'populated':>10} {'total':>8} {'coverage':>10}")
    print("-" * 52)
    for t in sorted(by_type.keys()):
        n = len(by_type[t])
        p = len(populated_by_type[t])
        pct = 100 * p / n if n else 0
        print(f"{t:<20} {p:>10} {n:>8} {pct:>9.1f}%")
    print()

    # Per-type unpopulated node ids — surface exactly which entries
    # would fall off a map today.
    for t in sorted(by_type.keys()):
        missing = sorted(set(by_type[t]) - set(populated_by_type[t]))
        if not missing:
            continue
        print(f"[{t}] {len(missing)} without coordinates:")
        for nid in missing:
            print(f"  - {nid}")
        print()


if __name__ == "__main__":
    graph = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    audit(graph)
