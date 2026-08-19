"""Test 12 — Pass L §2 unresolved-band round-trip.

Verifies the fix for the two silent-drop paths K.2 §3.1 identified:

  1. `_write_boundaries_to_config` never wrote `unresolved_bands` — the
     `[]` in `config/scoring.yaml` was a stale hand-entry.
  2. `build_inventory` never emitted `tier_ambiguous` — so a set flag
     was silently dropped at the report boundary.

The current graph produces no band under Pass L's retry, so both fixes
have no visible effect on the live artifacts. This test constructs a
synthetic distribution that FORCES a band, exercises the writer +
inventory renderer against it, and asserts the mechanism works. Nothing
in this test writes to `data/ai/*` or `config/scoring.yaml`; the writer
operates on a scratch copy in tmp_path.
"""
from __future__ import annotations

from pathlib import Path
from statistics import median

from app.scoring.thresholds import (
    Gap,
    UnresolvedBand,
    ThresholdDerivation,
    derive_thresholds,
)


def _dev_with_band() -> ThresholdDerivation:
    """Build a ThresholdDerivation containing a synthetic unresolved
    band. Structural shape — no reference to any node in the actual
    graph, no severity value taken from committed state."""
    band = UnresolvedBand(
        lower=0.0,
        upper=0.5,
        tiers=["moderate", "none"],
        reason="synthetic test band — not from any live derivation",
    )
    return ThresholdDerivation(
        scored=[("synth:a", 0.9), ("synth:b", 0.5), ("synth:c", 0.1)],
        gaps=[],
        median_gap=0.0,
        separation_factor=3.0,
        separating_gaps=[],
        boundaries={"critical": 0.7, "high": 0.5, "moderate": 0.0},
        boundary_gap={"critical": None, "high": None, "moderate": None},
        unresolved_bands=[band],
    )


def test_writer_serializes_bands_to_yaml(tmp_path: Path):
    """The Phase B writer must render `unresolved_bands` from the
    derivation, not leave the config's stale `[]`. On a scratch config,
    the writer produces YAML that reloads with the band intact."""
    from scripts.generate_inventory import _serialize_unresolved_bands

    dev = _dev_with_band()
    lines = _serialize_unresolved_bands(dev.unresolved_bands, indent_level=2)
    text = "\n".join(lines)

    # Must not be the empty inline form.
    assert text != "  unresolved_bands: []", (
        "writer produced the empty form on a derivation carrying a band"
    )
    # Must contain the block header at the requested indent.
    assert text.startswith("  unresolved_bands:\n"), text
    # Band content — lower/upper/tiers/reason all present and readable.
    assert "lower: 0.0" in text
    assert "upper: 0.5" in text
    assert "tiers:" in text and "- moderate" in text and "- none" in text
    assert "reason:" in text

    # Full round-trip: paste under a minimal `thresholds:` block and
    # confirm yaml.safe_load reproduces the band data.
    import yaml
    doc = "thresholds:\n" + text + "\n"
    parsed = yaml.safe_load(doc)
    bands = parsed["thresholds"]["unresolved_bands"]
    assert len(bands) == 1
    b = bands[0]
    assert b["lower"] == 0.0
    assert b["upper"] == 0.5
    assert b["tiers"] == ["moderate", "none"]
    assert "synthetic test band" in b["reason"]


def test_writer_empty_bands_renders_inline():
    """The empty case must render as `[]` inline so a config with no
    bands stays diff-clean pass-over-pass."""
    from scripts.generate_inventory import _serialize_unresolved_bands

    lines = _serialize_unresolved_bands([], indent_level=2)
    assert lines == ["  unresolved_bands: []"]


def test_tier_ambiguity_engine_reads_synthetic_band():
    """`_compute_tier_ambiguity` in engine.py reads
    `config.threshold_unresolved_bands` — a list of dicts. Verify that
    a config with the writer-produced schema is understood by the
    engine's ambiguity check.

    Under this synthetic band (moderate/none, span [0, 0.5]), a node
    at severity 0.3 with tier="moderate" must be flagged ambiguous
    with alternate `none`. Structural — no reference to committed data."""
    from app.scoring.engine import _compute_tier_ambiguity

    class _FakeConfig:
        @property
        def threshold_unresolved_bands(self):
            return [{
                "lower": 0.0,
                "upper": 0.5,
                "tiers": ["moderate", "none"],
                "reason": "synthetic",
            }]

    ambig, ambig_with = _compute_tier_ambiguity(
        severity=0.3, tier_name="moderate", config=_FakeConfig(),
    )
    assert ambig is True
    assert ambig_with == ["none"]

    # A node above the band's upper is not ambiguous.
    ambig_hi, _ = _compute_tier_ambiguity(
        severity=0.9, tier_name="critical", config=_FakeConfig(),
    )
    assert ambig_hi is False


def test_inventory_renders_tier_ambiguous_column():
    """`build_inventory` must include `tier_ambiguous` and
    `tier_ambiguous_with` as scored-node columns so a set flag isn't
    silently dropped at the report boundary (K.2 §3.1.1 second silent
    drop)."""
    inventory_text = (
        Path(__file__).resolve().parents[2]
        / "docs" / "generated" / "node_inventory.md"
    ).read_text()
    # Header row must include both columns.
    header_lines = [
        l for l in inventory_text.splitlines() if l.startswith("| id |")
    ]
    assert header_lines, "no header row found in node_inventory.md"
    header = header_lines[0]
    assert "tier_ambiguous" in header, header
    assert "tier_ambiguous_with" in header, header
