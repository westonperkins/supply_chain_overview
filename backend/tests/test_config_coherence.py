"""Test 6 — Config/schema coherence, both directions.

- Every stage named in scoring.yaml must exist in SUPPLY_EDGE_TYPES.
  (Also covered by the load-time validation added with per-stage HHI —
  this test reasserts it against the fixture yaml.)
- Every edge `type` present in edges.json must exist in the edge type
  enum. A typo'd edge type currently vanishes from scoring without error.
"""
import json
from pathlib import Path

from app.schema.enums import EdgeType, SUPPLY_EDGE_TYPES


def test_yaml_stages_are_valid_supply_edge_types(config):
    stages = config.inbound_per_stage_stages
    if stages is None:
        return  # default (all supply types) — nothing to validate
    valid = {t.value for t in SUPPLY_EDGE_TYPES}
    unknown = [s for s in stages if s not in valid]
    assert not unknown, f"yaml stages contain unknown edge types: {unknown}"


def test_every_edge_type_in_edges_json_exists_in_enum(fixtures_dir):
    with (fixtures_dir / "ai" / "edges.json").open() as f:
        edges = json.load(f)
    valid = {t.value for t in EdgeType}
    seen = {e["type"] for e in edges}
    unknown = sorted(seen - valid)
    assert not unknown, (
        f"edges.json contains edge types not in the schema enum: {unknown}. "
        f"Valid: {sorted(valid)}"
    )
