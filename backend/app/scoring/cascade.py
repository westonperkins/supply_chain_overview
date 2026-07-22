from collections import deque
from typing import Optional

from ..graph import SupplyChainGraph
from ..schema import (
    AxesImpact,
    CascadeStep,
    Event,
    Node,
    NodeType,
)
from .config import ScoringConfig
from .engine import (
    _outbound_share_for,
    _sourced_number,
    compute_severity,
    normalize_lead_time,
)


def _cushion(node: Node) -> float:
    """Look up the downstream node's financial cushion in [0, 1].

    v0 uses a manually-set static field per company. Missing/non-company
    nodes default to 0 (no cushion), so cascade dampening is conservative.
    """
    if node.type != NodeType.COMPANY:
        return 0.0
    return _sourced_number(node.static.financial_cushion, default=0.0)


def _event_severity_at_source(node: Node, axes: AxesImpact, config: ScoringConfig) -> float:
    """Severity at the directly-hit node, combining its cached baseline
    concentration (inbound + outbound combined) with the event-specific deltas."""
    conc_base = node.dynamic.concentration or 0.0
    conc = max(0.0, min(1.0, conc_base + axes.concentration_delta))

    sub_base = _sourced_number(node.static.substitutability, default=0.5)
    sub = max(0.0, min(1.0, sub_base + axes.substitutability_delta))

    lt_years = max(0.0, _sourced_number(node.static.lead_time_years, default=1.0)
                        + axes.lead_time_delta)
    lt = normalize_lead_time(lt_years, config.lead_time_normalization)

    return compute_severity(conc, sub, lt, config)


def propagate_event(event: Event, graph: SupplyChainGraph, config: ScoringConfig) -> Event:
    """Walk supply edges downstream from each matched entity. Records the
    full path per hop so the UI can render *why* a company was hit.

    Returns the same Event with severity and cascade populated (mutates
    a copy is unnecessary — we set fields on the passed-in object).
    """
    decay = config.cascade_decay
    max_hops = config.cascade_max_hops
    share_field = config.cascade_share_field
    fallback = config.cascade_fallback_to_input_share

    # Best severity seen at each node across all origins/paths, and the path
    # that achieved it (for inspectability).
    best: dict[str, CascadeStep] = {}
    max_source_severity = 0.0

    for match in event.entities_matched:
        origin = graph.nodes.get(match.node_id)
        if origin is None:
            continue

        origin_sev = _event_severity_at_source(origin, event.axes_impact, config) * match.confidence
        max_source_severity = max(max_source_severity, origin_sev)

        step = CascadeStep(node_id=origin.id, hop=0, severity_at_node=origin_sev, edge_path=[])
        prev = best.get(origin.id)
        if prev is None or origin_sev > prev.severity_at_node:
            best[origin.id] = step

        # BFS downstream.
        queue: deque[tuple[str, float, list[str], int]] = deque()
        queue.append((origin.id, origin_sev, [], 0))

        visited_on_this_origin: set[str] = {origin.id}

        while queue:
            node_id, sev, path, hop = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in graph.downstream_supply_edges(node_id):
                target = graph.nodes.get(edge.target_id)
                if target is None or edge.target_id in visited_on_this_origin:
                    continue
                cushion = _cushion(target)
                share = _outbound_share_for(edge, share_field, fallback)
                if share is None:
                    continue
                # Downstream severity = source_severity * decay * share * (1 - cushion)
                downstream_sev = sev * decay * share * (1.0 - cushion)
                if downstream_sev <= 1e-6:
                    continue

                new_path = path + [edge.id]
                candidate = CascadeStep(
                    node_id=target.id,
                    hop=hop + 1,
                    severity_at_node=downstream_sev,
                    edge_path=new_path,
                )
                prev = best.get(target.id)
                if prev is None or downstream_sev > prev.severity_at_node:
                    best[target.id] = candidate

                visited_on_this_origin.add(target.id)
                queue.append((target.id, downstream_sev, new_path, hop + 1))

    # Sort cascade by hop, then severity desc for stable UI rendering.
    cascade = sorted(best.values(), key=lambda s: (s.hop, -s.severity_at_node))
    event.cascade = cascade
    event.severity = max_source_severity
    return event
