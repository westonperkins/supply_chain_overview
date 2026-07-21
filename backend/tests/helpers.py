"""Pure helpers reused across tests and the report script.

Each returns raw data structures. Formatting lives elsewhere so tests can
assert against numbers while `run_report.py` prints them.
"""
from collections import defaultdict
from copy import deepcopy
from typing import Any

from app.graph import SupplyChainGraph
from app.scoring import (
    ScoringConfig,
    compute_outbound_criticality_map,
    refresh_all_derived,
)
from app.schema.enums import SUPPLY_EDGE_TYPES


# The edge types that produce shares into a node. Excludes `operates`
# (ownership, not a share into the target's supply base).
SHARE_STAGES = {
    "mines",
    "refines",
    "supplies",
    "input_to",
    "component_of",
}


def collect_share_shortfalls(graph: SupplyChainGraph, threshold: float = 0.95) -> list[dict]:
    """Every stage bucket on every node whose weights sum below `threshold`.

    A bucket summing to 0.47 produces a confident HHI from incomplete data —
    this is exactly how copper read refined_by_hhi = 1.0 from a single
    China edge. Sorted worst first.
    """
    rows: list[dict] = []
    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares or {}
        for stage_name, sources in derived.items():
            if stage_name not in SHARE_STAGES:
                continue
            total = sum(sources.values())
            if total < threshold:
                rows.append(
                    {
                        "node_id": node.id,
                        "node_name": node.name,
                        "stage": stage_name,
                        "sum": total,
                        "n_edges": len(sources),
                        "shortfall": 1.0 - total,
                    }
                )
    return sorted(rows, key=lambda r: -r["shortfall"])


def collect_thin_buckets(graph: SupplyChainGraph) -> list[dict]:
    """Every (node, stage) pair with exactly one edge — HHI is 1.0 by
    construction, so under `combine: max` that bucket wins unless another
    stage matches. Reports whether this bucket determined the node's
    inbound_hhi."""
    rows: list[dict] = []
    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares or {}
        stage_hhis = node.dynamic.stage_hhis or {}
        inbound = node.dynamic.inbound_hhi or 0.0
        for stage_name, sources in derived.items():
            if stage_name not in SHARE_STAGES:
                continue
            if len(sources) != 1:
                continue
            bucket_hhi = stage_hhis.get(stage_name, 0.0)
            won_max = abs(bucket_hhi - inbound) < 1e-9 and inbound > 0
            rows.append(
                {
                    "node_id": node.id,
                    "node_name": node.name,
                    "stage": stage_name,
                    "bucket_hhi": bucket_hhi,
                    "inbound_hhi": inbound,
                    "won_max": won_max,
                }
            )
    return rows


def snapshot_derived(graph: SupplyChainGraph) -> dict[str, dict[str, Any]]:
    """Deep-copies every node.dynamic field into a plain dict so we can
    diff after a second refresh."""
    snap: dict[str, dict[str, Any]] = {}
    for node in graph.nodes.values():
        d = node.dynamic
        snap[node.id] = {
            "stage_hhis": deepcopy(d.stage_hhis),
            "mined_by_hhi": d.mined_by_hhi,
            "refined_by_hhi": d.refined_by_hhi,
            "supplied_by_hhi": d.supplied_by_hhi,
            "combined_hhi": d.combined_hhi,
            "inbound_hhi": d.inbound_hhi,
            "outbound_criticality": d.outbound_criticality,
            "concentration": d.concentration,
            "current_severity": d.current_severity,
            "chokepoint_tier": (
                d.chokepoint_tier.value if d.chokepoint_tier else None
            ),
            "derived_shares": deepcopy(d.derived_shares),
        }
    return snap


def outbound_sensitivity_probe(
    graph: SupplyChainGraph, config: ScoringConfig
) -> dict[str, Any]:
    """Recompute outbound_criticality with the single highest-outbound node
    excluded from the normalization max. Return the number of tier changes.

    Rationale: outbound criticality normalizes to the graph max, so any
    single node's raw score can drag every other score. When robotics
    lands in the same graph, AI tiers may move for a non-AI reason.
    """
    from app.scoring.engine import (
        derive_chokepoint_tier,
        combine_concentration,
        compute_baseline_severity,
    )

    # Baseline outbound criticality map on the full graph.
    baseline_out = compute_outbound_criticality_map(graph, config)
    top_id, top_val = max(baseline_out.items(), key=lambda kv: kv[1])

    # Recompute the raw values without normalization, then normalize by the
    # SECOND-highest value.
    from app.scoring.engine import _outbound_criticality_raw

    decay = config.concentration_outbound_decay
    max_hops = config.concentration_outbound_max_hops
    min_influence = config.concentration_outbound_min_influence
    raw = {
        n_id: _outbound_criticality_raw(n_id, graph, decay, max_hops, min_influence)
        for n_id in graph.nodes
    }
    raw_top = raw[top_id]
    # New max: the highest raw among all others.
    new_max = max(v for k, v in raw.items() if k != top_id and v > 0)
    if new_max <= 0:
        new_max = 1.0
    perturbed = {k: (v / new_max if k != top_id else 0.0) for k, v in raw.items()}

    # Recompute severities + tiers using the perturbed outbound values.
    original_tiers: dict[str, str] = {}
    perturbed_tiers: dict[str, str] = {}
    for node in graph.nodes.values():
        inbound = node.dynamic.inbound_hhi or 0.0
        orig_out = baseline_out.get(node.id, 0.0)
        pert_out = perturbed.get(node.id, 0.0)

        orig_conc = combine_concentration(inbound, orig_out, config)
        pert_conc = combine_concentration(inbound, pert_out, config)

        original_dynamic = node.dynamic.concentration
        # Temporarily set concentration for baseline severity computation.
        node.dynamic.concentration = orig_conc
        orig_sev = compute_baseline_severity(node, config)
        node.dynamic.concentration = pert_conc
        pert_sev = compute_baseline_severity(node, config)
        # Restore.
        node.dynamic.concentration = original_dynamic

        original_tiers[node.id] = derive_chokepoint_tier(orig_sev, config).value
        perturbed_tiers[node.id] = derive_chokepoint_tier(pert_sev, config).value

    changed = [
        (nid, original_tiers[nid], perturbed_tiers[nid])
        for nid in graph.nodes
        if original_tiers[nid] != perturbed_tiers[nid]
    ]
    return {
        "removed_node_id": top_id,
        "removed_node_name": graph.nodes[top_id].name,
        "removed_original_score": top_val,
        "n_changed_tiers": len(changed),
        "changed": changed,
    }
