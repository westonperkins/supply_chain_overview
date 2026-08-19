"""Pass O §5 — synthetic tests for the diff generator's per-row cause
classifier and for the arm_core_ip replay fixture (the pass's acceptance
test).

The classifier must distinguish:
  - non-zero severity delta → RESCALE / STRUCTURAL (existing paths)
  - zero severity delta + tier changed + snapshot has boundaries that
    differ from current                              → BOUNDARY
  - zero severity delta + tier changed + snapshot has no boundaries
    (the pre-Pass-O shape)                           → BOUNDARY (unverified)
  - zero severity delta + tier changed + boundaries equal              → UNEXPLAINED
    (should not happen; classifier must not silently
     absorb it into any BOUNDARY bucket).

Pass N Phase A shipped a zero-delta tier change on `arm_core_ip` that
the diff generator called `STRUCTURAL` because it had no boundaries in
the snapshot to compare against. This pass makes that class of
misattribution structurally impossible; the arm_core_ip replay fixture
is the acceptance test that Pass N Phase A's transition now classifies
as BOUNDARY, not as movement.
"""

from types import SimpleNamespace

from app.reporting import build_severity_diff
from app.schema.enums import ChokepointTier


# ---- test stubs -----------------------------------------------------------
#
# The classifier reads:
#   - graph.nodes[nid].dynamic.baseline_severity
#   - graph.nodes[nid].dynamic.baseline_tier          (Enum-like, .value)
#   - config.outbound_fixed_reference                 (optional)
#   - config.chokepoint_thresholds                    (dict)
#   - config.inbound_per_stage_method                 (str)
#   - config.inbound_per_stage_eps                    (float, optional)
#
# Everything else on Node / ScoringConfig is untouched. SimpleNamespace
# stubs are honest to that surface and much lighter than round-tripping
# the schema through the loader.


def _node(node_id, severity, tier):
    """Build a graph-node stub with just the fields the classifier reads."""
    return SimpleNamespace(
        id=node_id,
        dynamic=SimpleNamespace(
            baseline_severity=severity,
            baseline_tier=(
                None if tier == "none" and severity is None
                else ChokepointTier(tier)
            ),
        ),
    )


def _graph(nodes: dict):
    # The classifier reads both `graph.nodes[nid]` and `n.id for n in
    # graph.nodes.values()` — the second form requires each node stub
    # to carry an id. Set it from the dict key to keep test bodies
    # readable.
    for nid, node in nodes.items():
        node.id = nid
    return SimpleNamespace(nodes=nodes)


def _config(
    boundaries: dict,
    method: str = "noisy_or",
    eps: float = 0.01,
    fixed_reference: float = 1.0,
):
    """Config stub — carries only the fields the classifier reads."""
    return SimpleNamespace(
        chokepoint_thresholds=boundaries,
        inbound_per_stage_method=method,
        inbound_per_stage_eps=eps,
        outbound_fixed_reference=fixed_reference,
    )


def _row_for(diff_md: str, node_id: str) -> str:
    for line in diff_md.split("\n"):
        if line.startswith(f"| {node_id} |"):
            return line
    raise AssertionError(f"{node_id} row missing from diff:\n{diff_md}")


# ---------------------------------------------------------------------------
# §1.2 BOUNDARY cause — the base contract
# ---------------------------------------------------------------------------


def test_zero_delta_plus_boundary_move_classifies_BOUNDARY():
    """Node severity does not move; the boundary moves past it. The
    classifier must credit the boundary, not attribute the tier change
    to structural or rescale movement."""
    snap = {
        "captured_at_pass": "synth_pre",
        "fixed_reference": 1.0,
        "boundaries": {"critical": 0.55, "high": 0.42, "moderate": 0.14},
        "aggregator_method": "noisy_or",
        "nodes": {
            "n:x": {
                "severity": 0.1512, "tier": "moderate",
                "concentration": 0.4582, "inbound_hhi": 0.0,
                "outbound_criticality": 0.4582,
            },
        },
    }
    graph = _graph({"n:x": _node("n:x", 0.1512, "none")})
    cfg = _config(boundaries={"critical": 0.55, "high": 0.42, "moderate": 0.18})
    diff = build_severity_diff(snap, graph, config=cfg)

    row = _row_for(diff, "n:x")
    assert "| BOUNDARY |" in row, row
    assert "STRUCTURAL" not in row and "RESCALE" not in row, row


def test_zero_delta_plus_no_snapshot_boundaries_classifies_BOUNDARY_unverified():
    """Snapshot pre-dates §1.1's boundary capture. Zero-delta tier
    change is *sound* to attribute to boundary movement but the
    snapshot has no evidence to verify against — classifier must say
    so rather than assert a verified BOUNDARY."""
    snap = {
        "captured_at_pass": "synth_old",
        "fixed_reference": 1.0,
        # NO boundaries key on purpose — this is the pre-Pass-O shape.
        "nodes": {
            "n:x": {
                "severity": 0.1512, "tier": "moderate",
                "concentration": 0.4582, "inbound_hhi": 0.0,
                "outbound_criticality": 0.4582,
            },
        },
    }
    graph = _graph({"n:x": _node("n:x", 0.1512, "none")})
    cfg = _config(boundaries={"critical": 0.55, "high": 0.42, "moderate": 0.18})
    diff = build_severity_diff(snap, graph, config=cfg)

    row = _row_for(diff, "n:x")
    assert "BOUNDARY (unverified)" in row, row


def test_zero_delta_plus_boundaries_equal_classifies_UNEXPLAINED():
    """A zero-delta tier change with unchanged boundaries should not
    occur — but if the classifier ever sees one, it must not silently
    call it BOUNDARY. A load-bearing invariant: the classifier records
    ignorance rather than manufacture a cause."""
    snap = {
        "captured_at_pass": "synth_equal",
        "fixed_reference": 1.0,
        "boundaries": {"critical": 0.55, "high": 0.42, "moderate": 0.18},
        "aggregator_method": "noisy_or",
        "nodes": {
            "n:x": {
                "severity": 0.1512, "tier": "moderate",
                "concentration": 0.4582, "inbound_hhi": 0.0,
                "outbound_criticality": 0.4582,
            },
        },
    }
    graph = _graph({"n:x": _node("n:x", 0.1512, "none")})
    cfg = _config(boundaries={"critical": 0.55, "high": 0.42, "moderate": 0.18})
    diff = build_severity_diff(snap, graph, config=cfg)

    row = _row_for(diff, "n:x")
    assert "UNEXPLAINED" in row, row


def test_boundary_cause_appears_in_summary_counts():
    """The summary block must expose BOUNDARY as its own count under
    tier changes — Pass N Phase A had 12 tier changes but the summary
    only exposed RESCALE/STRUCTURAL, hiding boundary movement."""
    snap = {
        "captured_at_pass": "synth_summary",
        "fixed_reference": 1.0,
        "boundaries": {"critical": 0.55, "high": 0.42, "moderate": 0.14},
        "aggregator_method": "noisy_or",
        "nodes": {
            "n:a": {"severity": 0.1512, "tier": "moderate",
                    "concentration": 0.45, "inbound_hhi": 0.0,
                    "outbound_criticality": 0.45},
            "n:b": {"severity": 0.1600, "tier": "moderate",
                    "concentration": 0.48, "inbound_hhi": 0.0,
                    "outbound_criticality": 0.48},
        },
    }
    graph = _graph({
        "n:a": _node("n:a", 0.1512, "none"),
        "n:b": _node("n:b", 0.1600, "none"),
    })
    cfg = _config(boundaries={"critical": 0.55, "high": 0.42, "moderate": 0.17})
    diff = build_severity_diff(snap, graph, config=cfg)

    assert "BOUNDARY" in diff
    assert "boundary moved" in diff.lower()
    # The classifier saw two zero-delta tier changes, both boundary-caused.
    assert "BOUNDARY** (zero severity delta, tier moved because boundary moved): 2" in diff, diff


# ---------------------------------------------------------------------------
# §5(5) — arm_core_ip replay fixture (acceptance test)
# ---------------------------------------------------------------------------


def test_arm_core_ip_replay_pass_l_to_phase_a_classifies_BOUNDARY():
    """The pass's acceptance test.

    Pass N Phase A committed a tier change on arm_core_ip that Pass N.1
    proved was boundary-caused: severity was 0.1511933805 both before
    and after; the moderate boundary moved 0.1367 → 0.1771 across the
    node's severity, so tier fell moderate → none. The diff generator
    of the time classified this as STRUCTURAL because it had no way to
    see boundary movement.

    Replay the transition against the post-O classifier. Snapshot
    carries a pass_l-shape (boundaries at 0.1367); current graph is
    post-Phase-A (boundaries at 0.1771, same severity). Classification
    must be BOUNDARY, not STRUCTURAL."""
    snap = {
        "captured_at_pass": "pass_l_replay_fixture",
        "fixed_reference": 1.6711394969476698,
        # Pass L boundaries (moderate at 0.1367). Values reconstructed
        # from Pass N.1 §1 evidence; only `moderate` is load-bearing
        # for this replay.
        "boundaries": {
            "critical": 0.5178454839188712,
            "high": 0.41368488092014066,
            "moderate": 0.1367,
        },
        "aggregator_method": "noisy_or",
        "nodes": {
            "product:arm_core_ip": {
                "severity": 0.15119338054081047,
                "tier": "moderate",
                "concentration": 0.45821127051538846,
                "inbound_hhi": 0.0,
                "outbound_criticality": 0.45821127051538846,
            },
        },
    }
    graph = _graph({
        "product:arm_core_ip": _node(
            "product:arm_core_ip", 0.15119338054081047, "none",
        ),
    })
    cfg = _config(
        boundaries={
            "critical": 0.5178454839188712,
            "high": 0.41368488092014066,
            "moderate": 0.17711108045794494,
        },
        method="noisy_or",
        fixed_reference=1.6711394969476698,
    )
    diff = build_severity_diff(snap, graph, config=cfg)

    row = _row_for(diff, "product:arm_core_ip")
    assert "| BOUNDARY |" in row, row
    # Sanity: no severity delta reported (byte-identical).
    assert "+0.0000000000" in row, row
    # Sanity: cause must NOT be misattributed to STRUCTURAL or RESCALE.
    assert "STRUCTURAL" not in row and "RESCALE" not in row, row
