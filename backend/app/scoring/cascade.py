"""Event propagation — walks supply edges downstream from each matched
entity and updates every touched node's `current_severity`. Pass D
rewrite:

  - Writes ONLY to `current_*` fields (INV-4). Never `baseline_*`.
  - Origin's own severity is derived from its BASELINE (for scored
    origins) or from CONCENTRATION (for unscored origins). NEVER by
    substituting sub=0/lt=1.0 into the severity formula — that was the
    Pass C-deferred neutral leak; see spec §4.
  - Contributions combine via config `events.combine` (default noisy_or).
  - Every downstream contribution inherits an `origin_scored` flag; any
    node touched by an unscored-origin contribution sets
    `current_severity_has_unscored_origin = True`. This attaches the
    provenance the news-ingestion pass will gate ranking on.
"""
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
    axes_for_severity,
    compute_severity,
    derive_chokepoint_tier,
    normalize_lead_time,
    _compute_tier_ambiguity,
)


def _cushion(node: Node) -> float:
    """Look up the downstream node's financial cushion in [0, 1].

    v0 uses a manually-set static field per company. Missing/non-company
    nodes default to 0 (no cushion), so cascade dampening is conservative.
    """
    if node.type != NodeType.COMPANY:
        return 0.0
    return _sourced_number(node.static.financial_cushion, default=0.0)


def _event_magnitude(axes: AxesImpact, config: ScoringConfig) -> float:
    """Read the event's magnitude ∈ [0,1] from the AxesImpact per config
    `events.magnitude_source`. Default source is `axes.concentration_delta`
    clipped to [0,1] — the primary quantity events convey today. When a
    future Event schema adds an explicit `magnitude` field, change the
    config path, not the code."""
    src = config.events_magnitude_source
    if src == "axes.concentration_delta":
        return max(0.0, min(1.0, axes.concentration_delta))
    if src == "axes.substitutability_delta":
        return max(0.0, min(1.0, abs(axes.substitutability_delta)))
    # Fallback — treat as no magnitude
    return 0.0


def _combine(current: float, contribution: float, method: str) -> float:
    """Combine an incoming event contribution into a node's current
    severity per config `events.combine`. noisy_or is bounded [0,1] and
    monotonic — cannot push current below its previous value."""
    c = max(0.0, min(1.0, contribution))
    if method == "noisy_or":
        return 1.0 - (1.0 - current) * (1.0 - c)
    if method == "max":
        return max(current, c)
    if method == "add_clamp":
        return min(1.0, current + c)
    raise ValueError(f"unknown events.combine method: {method}")


def _event_source_scale(
    origin: Node,
    magnitude: float,
    confidence: float,
) -> tuple[float, bool]:
    """Return (source_scale, origin_scored). Pass D §4:

      - SCORED origin (baseline_severity is not None): source_scale =
        baseline_severity × magnitude × confidence. Event effect at the
        origin is derived from a real structural severity.
      - UNSCORED origin (baseline_severity is None): source_scale =
        concentration × magnitude × confidence. The origin's own
        current_severity stays None (caller enforces); downstream
        propagation is seeded by concentration — a real number, unlike
        the fabricated severity the old code emitted.
    """
    baseline = origin.dynamic.baseline_severity
    if baseline is not None:
        return baseline * magnitude * confidence, True
    conc = origin.dynamic.concentration or 0.0
    return conc * magnitude * confidence, False


def propagate_event(event: Event, graph: SupplyChainGraph, config: ScoringConfig) -> Event:
    """Walk supply edges downstream from each matched entity. Updates
    node.dynamic.current_severity + current_tier for every touched node.

    Multi-path handling: per event, each downstream node's contribution
    is the BEST (max) path from any origin (existing behaviour). That
    single per-event contribution is then combined into the node's
    current_severity via `events.combine` (default noisy_or). Multiple
    events applied in sequence each combine into current the same way.

    Returns the passed-in event with cascade and severity populated (the
    UI reads these; not equivalent to node.dynamic writes).
    """
    decay = config.cascade_decay
    max_hops = config.cascade_max_hops
    share_field = config.cascade_share_field
    fallback = config.cascade_fallback_to_input_share
    combine_method = config.events_combine
    magnitude = _event_magnitude(event.axes_impact, config)

    # Best (per-event) contribution per node, with origin_scored flag.
    best_contribution: dict[str, tuple[float, bool, list[str], int]] = {}

    for match in event.entities_matched:
        origin = graph.nodes.get(match.node_id)
        if origin is None:
            continue

        source_scale, origin_scored = _event_source_scale(
            origin, magnitude, match.confidence,
        )
        # Origin's own contribution — recorded whether scored or not so
        # cascade metadata is complete. Actual write to current_severity
        # is gated below by "baseline is not None" (unscored stays None).
        prev = best_contribution.get(origin.id)
        if prev is None or source_scale > prev[0]:
            best_contribution[origin.id] = (source_scale, origin_scored, [], 0)

        # BFS downstream, tracking max-path contribution per node.
        queue: deque[tuple[str, float, list[str], int]] = deque()
        queue.append((origin.id, source_scale, [], 0))
        visited_on_this_origin: set[str] = {origin.id}

        while queue:
            node_id, sev, path, hop = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in graph.downstream_supply_edges(node_id):
                target = graph.nodes.get(edge.target_id)
                if target is None or edge.target_id in visited_on_this_origin:
                    continue
                share = _outbound_share_for(edge, share_field, fallback)
                if share is None:
                    continue
                cushion = _cushion(target)
                downstream = sev * decay * share * (1.0 - cushion)
                if downstream <= 1e-6:
                    continue
                new_path = path + [edge.id]
                prev = best_contribution.get(target.id)
                if prev is None or downstream > prev[0]:
                    best_contribution[target.id] = (
                        downstream, origin_scored, new_path, hop + 1,
                    )
                visited_on_this_origin.add(target.id)
                queue.append((target.id, downstream, new_path, hop + 1))

    # Apply contributions to each touched node's current_severity.
    # Unscored downstream nodes (baseline is None) do NOT accumulate a
    # current_severity — an event does not fabricate severity from
    # absent axes (§4). Their current_severity stays None.
    max_source_severity = 0.0
    for node_id, (contribution, origin_scored, _, _) in best_contribution.items():
        node = graph.nodes[node_id]
        max_source_severity = max(max_source_severity, contribution)
        if node.dynamic.baseline_severity is None:
            # Unscored node: no baseline to combine with. Skip.
            continue
        current = node.dynamic.current_severity
        if current is None:
            # Should not happen (engine initializes current = baseline
            # for scored nodes) but be defensive.
            current = node.dynamic.baseline_severity
        new_current = _combine(current, contribution, combine_method)
        node.dynamic.current_severity = new_current
        if not origin_scored:
            node.dynamic.current_severity_has_unscored_origin = True
        # Re-derive current_tier + ambiguity from new current_severity.
        new_tier = derive_chokepoint_tier(new_current, config)
        node.dynamic.current_tier = new_tier
        tier_name = new_tier.value if new_tier else None
        amb, amb_with = _compute_tier_ambiguity(new_current, tier_name, config)
        node.dynamic.current_tier_ambiguous = amb
        node.dynamic.current_tier_ambiguous_with = amb_with

    # Build the CascadeStep list for the event object (UI/inspection).
    cascade = sorted(
        (
            CascadeStep(
                node_id=nid, hop=hop, severity_at_node=contrib,
                edge_path=path,
            )
            for nid, (contrib, _, path, hop) in best_contribution.items()
        ),
        key=lambda s: (s.hop, -s.severity_at_node),
    )
    event.cascade = cascade
    event.severity = max_source_severity
    return event
