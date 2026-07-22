"""Command that regenerates the docs/generated/ artifacts:

  - node_inventory.md       (regenerated every run)
  - threshold_analysis.md   (regenerated every run — Pass B)
  - severity_snapshot.json  (never overwritten by this script; the pass
                             author edits it explicitly when scoring
                             changes deliberately)
  - severity_diff.md        (regenerated every run against the snapshot)

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
from app.reporting import (
    build_inventory,
    build_severity_diff,
    build_threshold_analysis,
    snapshot_severity,
)
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.thresholds import derive_thresholds

GENERATED = REPO / "docs" / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

# Current pass name used for the snapshot label whenever the snapshot
# is captured for the first time. Do not update this to a NEW pass name
# unless you are intentionally rebasing the diff onto post-pass state.
CURRENT_PASS_NAME = "generated_inventory_hygiene"


def score():
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for e in g.events.values():
        propagate_event(e, g, c)
    return g, c


def _load_snapshot_or_first_run(g):
    """Never overwrite the snapshot from this script — the pass author
    updates it explicitly by editing the JSON when scoring deliberately
    moves. First-run behaviour: emit an empty labelled snapshot so the
    diff header can say "first-run" plainly."""
    path = GENERATED / "severity_snapshot.json"
    if path.exists():
        return json.loads(path.read_text())
    # First-run capture
    snap = snapshot_severity(g, captured_at_pass=CURRENT_PASS_NAME)
    path.write_text(json.dumps(snap, indent=2, default=str) + "\n")
    return snap


def main():
    g, c = score()

    inventory = build_inventory(g, c)
    (GENERATED / "node_inventory.md").write_text(inventory)

    # Threshold analysis — reads the same graph state.
    severities = [(nid, n.dynamic.current_severity) for nid, n in g.nodes.items()]
    derivation = derive_thresholds(severities, c.threshold_separation_factor)
    scored_count = sum(1 for _, s in severities if s is not None)
    unscored_count = len(severities) - scored_count
    analysis = build_threshold_analysis(derivation, inventory, scored_count, unscored_count)
    (GENERATED / "threshold_analysis.md").write_text(analysis)

    snapshot = _load_snapshot_or_first_run(g)
    diff = build_severity_diff(snapshot, g)
    (GENERATED / "severity_diff.md").write_text(diff)

    print("Wrote:")
    print(f"  {GENERATED / 'node_inventory.md'}")
    print(f"  {GENERATED / 'threshold_analysis.md'}")
    print(f"  {GENERATED / 'severity_snapshot.json'} (unchanged unless first run)")
    print(f"  {GENERATED / 'severity_diff.md'}")


if __name__ == "__main__":
    main()
