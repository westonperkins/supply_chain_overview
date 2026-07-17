import math
from collections import deque
from typing import Optional

from ..graph import SupplyChainGraph
from ..schema import ChokepointTier, Node
from ..schema.enums import SUPPLY_EDGE_TYPES
from .config import ScoringConfig


# --------------------------------------------------------------------------- #
# Inbound concentration — HHI                                                 #
# --------------------------------------------------------------------------- #

def compute_hhi(shares: dict[str, float]) -> float:
    """Herfindahl-Hirschman Index, normalized to [0, 1]."""
    if not shares:
        return 0.0
    total = sum(shares.values())
    if total <= 0:
        return 0.0
    normed = [v / total for v in shares.values()]
    return sum(v * v for v in normed)


def hhi_from_derived_shares(derived: Optional[dict]) -> float:
    """Combine share buckets across edge types into a single supply-share map,
    then compute HHI. Uses the strongest bucket per source to avoid double
    counting a supplier that both mines AND refines a mineral."""
    if not derived:
        return 0.0
    combined: dict[str, float] = {}
    for _edge_type, sources in derived.items():
        for src, weight in sources.items():
            if weight > combined.get(src, 0.0):
                combined[src] = weight
    return compute_hhi(combined)


# --------------------------------------------------------------------------- #
# Outbound criticality — the ASML/TSMC axis                                    #
# --------------------------------------------------------------------------- #
#
# For each node N, walks the downstream supply subgraph and tracks the best
# influence(N -> D) = product of edge weights along the max-product path,
# multiplied by decay^depth. The final score is the root-sum-square across
# reachable downstream nodes: sqrt(sum(influence^2)).
#
# Interpretation: "how much of the downstream graph is single-sourced from N."
# ASML, TSMC, HBM, CoWoS will score high; leaf nodes (data centers, minerals
# that go nowhere in AI) score low. Values are then normalized to graph max so
# the returned scale is [0, 1].
#

def _outbound_criticality_raw(
    node_id: str,
    graph: SupplyChainGraph,
    decay: float,
    max_hops: int,
    min_influence: float,
) -> float:
    best_influence: dict[str, float] = {}
    # (curr_id, running_weight_product, depth)
    queue: deque[tuple[str, float, int]] = deque([(node_id, 1.0, 0)])
    while queue:
        curr_id, running, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for edge in graph.downstream_supply_edges(curr_id):
            target_id = edge.target_id
            if target_id == node_id:
                continue  # never loop back onto origin
            new_running = running * edge.effective_weight()
            new_depth = depth + 1
            influence = new_running * (decay ** new_depth)
            if influence <= min_influence:
                continue
            if influence > best_influence.get(target_id, 0.0):
                best_influence[target_id] = influence
                queue.append((target_id, new_running, new_depth))
    return math.sqrt(sum(v * v for v in best_influence.values()))


def compute_outbound_criticality_map(graph: SupplyChainGraph, config: ScoringConfig) -> dict[str, float]:
    """Compute normalized [0, 1] outbound criticality for every node."""
    decay = config.concentration_outbound_decay
    max_hops = config.concentration_outbound_max_hops
    min_influence = config.concentration_outbound_min_influence
    raw = {
        node_id: _outbound_criticality_raw(node_id, graph, decay, max_hops, min_influence)
        for node_id in graph.nodes
    }
    max_raw = max(raw.values()) if raw else 0.0
    if max_raw <= 0.0:
        return {k: 0.0 for k in raw}
    return {k: v / max_raw for k, v in raw.items()}


# --------------------------------------------------------------------------- #
# Combine inbound + outbound → concentration                                   #
# --------------------------------------------------------------------------- #

def combine_concentration(inbound: float, outbound: float, config: ScoringConfig) -> float:
    method = config.concentration_combine_method
    if method == "max":
        return max(inbound, outbound)
    if method == "weighted_sum":
        wi = config.concentration_inbound_weight
        wo = config.concentration_outbound_weight
        total = wi + wo
        if total <= 0:
            return 0.0
        return (wi * inbound + wo * outbound) / total
    raise ValueError(f"unknown concentration combine method: {method}")


# --------------------------------------------------------------------------- #
# Lead time normalization                                                      #
# --------------------------------------------------------------------------- #

def normalize_lead_time(years: float, method: str) -> float:
    if method == "identity":
        return years
    if method == "log10_1p":
        return math.log10(years + 1) / math.log10(26.0)
    raise ValueError(f"unknown lead_time normalization: {method}")


# --------------------------------------------------------------------------- #
# Severity formula                                                             #
# --------------------------------------------------------------------------- #

def _safe_eval(expr: str, ns: dict[str, float]) -> float:
    return float(eval(expr, {"__builtins__": {}}, ns))


def compute_severity(
    concentration: float,
    substitutability: float,
    lead_time: float,
    config: ScoringConfig,
) -> float:
    w = config.weights
    ns = {
        "concentration": concentration * w["concentration"],
        "substitutability": min(1.0, max(0.0, substitutability * w["substitutability"])),
        "lead_time": lead_time * w["lead_time"],
    }
    return _safe_eval(config.formula, ns)


def compute_baseline_severity(node: Node, config: ScoringConfig) -> float:
    """Uses the node's cached concentration (inbound+outbound combined).
    Called after refresh_all_derived has populated node.dynamic.concentration."""
    conc = node.dynamic.concentration or 0.0
    sub = _sourced_number(node.static.substitutability, default=0.5)
    lt_raw = _sourced_number(node.static.lead_time_years, default=1.0)
    lt = normalize_lead_time(lt_raw, config.lead_time_normalization)
    return compute_severity(conc, sub, lt, config)


def _sourced_number(sv, default: float) -> float:
    if sv is None or sv.value is None:
        return default
    try:
        return float(sv.value)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Chokepoint tier — derived, cached                                            #
# --------------------------------------------------------------------------- #

def derive_chokepoint_tier(baseline_severity: float, config: ScoringConfig) -> ChokepointTier:
    t = config.chokepoint_thresholds
    if baseline_severity >= t["critical"]:
        return ChokepointTier.CRITICAL
    if baseline_severity >= t["high"]:
        return ChokepointTier.HIGH
    if baseline_severity >= t["moderate"]:
        return ChokepointTier.MODERATE
    return ChokepointTier.NONE


# --------------------------------------------------------------------------- #
# Whole-graph refresh                                                          #
# --------------------------------------------------------------------------- #

def refresh_all_derived(graph: SupplyChainGraph, config: ScoringConfig) -> None:
    """Recompute every derived field on every node.

    Order matters:
      1. derived_shares  (from edges)
      2. inbound_hhi     (from derived_shares)
      3. outbound_criticality  (walk downstream, then normalize by graph max)
      4. concentration   (combine inbound + outbound per config)
      5. current_severity, chokepoint_tier  (from concentration + static axes)
    """
    graph.refresh_derived_shares()

    outbound_map = compute_outbound_criticality_map(graph, config)

    for node in graph.nodes.values():
        inbound = hhi_from_derived_shares(node.dynamic.derived_shares)
        outbound = outbound_map.get(node.id, 0.0)
        concentration = combine_concentration(inbound, outbound, config)

        node.dynamic.inbound_hhi = inbound
        node.dynamic.outbound_criticality = outbound
        node.dynamic.concentration = concentration

        baseline = compute_baseline_severity(node, config)
        node.dynamic.current_severity = baseline
        node.dynamic.chokepoint_tier = derive_chokepoint_tier(baseline, config)
