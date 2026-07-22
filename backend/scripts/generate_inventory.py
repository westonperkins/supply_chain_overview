"""Command that regenerates the three docs/generated/ artifacts:

  - node_inventory.md    (regenerated every run)
  - severity_snapshot.json  (captured once, then edited only when
                             scoring changes deliberately)
  - severity_diff.md     (regenerated every run — compares the snapshot
                          to the current state)

Usage from repo root:
    python backend/scripts/generate_inventory.py

Staleness guards in backend/tests/test_generated_artifacts.py enforce
that the committed files match what the code produces.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.reporting import build_inventory, build_severity_diff, snapshot_severity
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event


GENERATED = REPO / "docs" / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)


def score():
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for e in g.events.values():
        propagate_event(e, g, c)
    return g, c


def _write_snapshot_if_missing(g):
    """First-run behaviour: capture severity to a JSON so the diff file
    has something to compare against. On subsequent runs the snapshot is
    treated as authoritative and updated only when the pass author says
    scoring moved deliberately."""
    path = GENERATED / "severity_snapshot.json"
    if path.exists():
        return json.loads(path.read_text())
    snap = snapshot_severity(g)
    path.write_text(json.dumps(snap, indent=2, default=str) + "\n")
    return snap


def main():
    g, c = score()

    inventory = build_inventory(g, c)
    (GENERATED / "node_inventory.md").write_text(inventory)

    snapshot = _write_snapshot_if_missing(g)
    diff = build_severity_diff(snapshot, g)
    (GENERATED / "severity_diff.md").write_text(diff)

    print(f"Wrote:")
    print(f"  {GENERATED / 'node_inventory.md'}")
    print(f"  {GENERATED / 'severity_snapshot.json'}")
    print(f"  {GENERATED / 'severity_diff.md'}")


if __name__ == "__main__":
    main()
