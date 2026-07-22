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


def _write_boundaries_to_config(derivation):
    """F3 fix (Pass C): the config boundary block is a RENDERING of the
    derivation output, never a parallel hand-entry. This rewrites the
    three float values in place, preserving comments and every other
    line of scoring.yaml so the diff is minimal and reviewable."""
    yaml_path = REPO / "config" / "scoring.yaml"
    text = yaml_path.read_text()
    lines = text.split("\n")

    out = []
    inside_boundaries = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("boundaries:"):
            inside_boundaries = True
            out.append(line)
            continue
        if inside_boundaries:
            # An unindented (or top-level) sibling ends the block.
            if line and not line.startswith(" "):
                inside_boundaries = False
                out.append(line)
                continue
            # Rewrite the three boundary lines with derivation values.
            for name in ("critical", "high", "moderate"):
                prefix = f"    {name}:"
                if stripped.startswith(f"{name}:"):
                    indent = line[: len(line) - len(line.lstrip())]
                    out.append(f"{indent}{name}: {derivation.boundaries[name]!r}")
                    break
            else:
                out.append(line)
                continue
        else:
            out.append(line)
    yaml_path.write_text("\n".join(out))

    # Also mirror to the fixture so H1 identity stays clean.
    fx = REPO / "backend" / "tests" / "fixtures" / "scoring.yaml"
    fx.write_text(yaml_path.read_text())


def main():
    # First pass: score to get severities (independent of tier boundaries).
    g, c = score()

    # Derive from committed severities.
    severities = [(nid, n.dynamic.baseline_severity) for nid, n in g.nodes.items()]
    derivation = derive_thresholds(severities, c.threshold_separation_factor)

    # F3: write derived boundaries into config so config IS the rendering
    # of the derivation. Then re-score so tiers reflect the freshly
    # written boundaries.
    _write_boundaries_to_config(derivation)
    g, c = score()

    inventory = build_inventory(g, c)
    (GENERATED / "node_inventory.md").write_text(inventory)

    scored_count = sum(1 for _, s in severities if s is not None)
    unscored_count = len(severities) - scored_count
    analysis = build_threshold_analysis(
        derivation, inventory, scored_count, unscored_count,
        chokepoint_landing=_chokepoint_landing(g),
    )
    (GENERATED / "threshold_analysis.md").write_text(analysis)

    snapshot = _load_snapshot_or_first_run(g)
    diff = build_severity_diff(snapshot, g)
    (GENERATED / "severity_diff.md").write_text(diff)

    print("Wrote:")
    print(f"  {GENERATED / 'node_inventory.md'}")
    print(f"  {GENERATED / 'threshold_analysis.md'}")
    print(f"  {GENERATED / 'severity_snapshot.json'} (unchanged unless first run)")
    print(f"  {GENERATED / 'severity_diff.md'}")


# F2.b — paper-chokepoint tier-landing table lives in the reporting layer.
# The seven ids live here (reporting), NOT in the derivation module —
# A8 still holds: no derivation-path source file references them.
PAPER_CHOKEPOINT_IDS = [
    ("company:tsmc", "TSMC"),
    ("company:asml", "ASML"),
    ("mineral:gallium", "gallium"),
    ("mineral:dysprosium", "dysprosium"),
    ("product:hbm", "HBM"),
    ("product:cowos_packaging", "CoWoS"),
    ("product:rf_power_semis", "RF & Power Semis"),
]


def _chokepoint_landing(graph):
    rows = []
    for nid, name in PAPER_CHOKEPOINT_IDS:
        n = graph.nodes.get(nid)
        if n is None:
            continue
        sev = n.dynamic.baseline_severity
        tier = n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else "none"
        rows.append((name, nid, sev, tier))
    return rows


if __name__ == "__main__":
    main()
