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

def compute_hhi(shares: dict[str, float], normalize: bool = True) -> float:
    """Herfindahl-Hirschman Index.

    When `normalize=True` (legacy behaviour), shares are divided by their
    sum before squaring, so a bucket summing to 0.08 reads as HHI 1.00 —
    incompleteness is discarded.

    When `normalize=False`, HHI is the sum of squared RAW shares. An
    incomplete bucket is dampened in exact proportion to its shortfall;
    no tuning parameter, no threshold. If the shares sum above 1.0 (i.e.
    the edge-type semantics are not "target's input share"), HHI can
    exceed 1.0 — that value is left un-clamped so the semantic mismatch
    surfaces rather than being hidden. See the audit in
    `docs/edge_weight_semantics_report.md`.
    """
    if not shares:
        return 0.0
    if normalize:
        total = sum(shares.values())
        if total <= 0:
            return 0.0
        return sum((v / total) ** 2 for v in shares.values())
    return sum(v * v for v in shares.values())


def hhi_from_derived_shares(derived: Optional[dict], normalize: bool = True) -> float:
    """Legacy blended HHI — kept so before/after is inspectable on the node
    as `combined_hhi`. NOT the inbound_hhi used in scoring anymore.

    Merges every stage into one supplier map via strongest-bucket-per-source,
    which dilutes the mining signal for minerals whose mining and refining
    have different concentration profiles (see per_stage_hhi below).
    """
    if not derived:
        return 0.0
    combined: dict[str, float] = {}
    for _edge_type, sources in derived.items():
        for src, weight in sources.items():
            if weight > combined.get(src, 0.0):
                combined[src] = weight
    return compute_hhi(combined, normalize=normalize)


def per_stage_hhi(derived: Optional[dict], stage: str, normalize: bool = True) -> Optional[float]:
    """HHI of one stage in isolation. Returns None when the stage has no
    edges on this node (so we can distinguish 'not applicable' from 'zero')."""
    if not derived:
        return None
    stage_shares = derived.get(stage)
    if not stage_shares:
        return None
    return compute_hhi(stage_shares, normalize=normalize)


def compute_stage_hhis(derived: Optional[dict], normalize: bool = True) -> dict[str, float]:
    """Compute per-stage HHIs for every edge type in SUPPLY_EDGE_TYPES that
    has edges present in `derived`. Returns {} when nothing applies.

    This is deliberately data-driven: the stage set is not hardcoded, so
    adding a new SUPPLY_EDGE_TYPES member automatically flows through. The
    previous defect (hardcoded three-stage triple in Python that yaml
    couldn't override) cannot recur under this shape."""
    if not derived:
        return {}
    valid = {t.value for t in SUPPLY_EDGE_TYPES}
    out: dict[str, float] = {}
    for stage_name, shares in derived.items():
        if stage_name not in valid or not shares:
            continue
        out[stage_name] = compute_hhi(shares, normalize=normalize)
    return out


def combine_per_stage(values: dict[str, float], config: ScoringConfig) -> float:
    """Combines the present per-stage HHIs according to config.

    Default 'max' preserves the intent of the per-stage split: a mineral is
    fragile if EITHER stage is concentrated. Averaging reintroduces the
    dilution this fix exists to remove."""
    if not values:
        return 0.0
    method = config.inbound_per_stage_combine
    if method == "max":
        return max(values.values())
    if method == "weighted_sum":
        weights = config.inbound_per_stage_weights
        total_w = 0.0
        total_v = 0.0
        for stage, v in values.items():
            w = weights.get(stage, 1.0)
            total_v += v * w
            total_w += w
        return (total_v / total_w) if total_w > 0 else 0.0
    raise ValueError(f"unknown per_stage combine method: {method}")


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
      2. stage_hhis  (per-stage HHI for every edge type present in
         SUPPLY_EDGE_TYPES — not a hardcoded set), plus convenience
         accessors mined_by_hhi / refined_by_hhi / supplied_by_hhi and
         the legacy blended combined_hhi
      3. inbound_hhi     (combine of stage_hhis values per config;
         default = max over all present stages; optional stages
         restriction in yaml opts OUT of edge types)
      4. outbound_criticality  (walk downstream, then normalize by graph max)
      5. concentration   (combine inbound + outbound per config)
      6. current_severity, chokepoint_tier  (from concentration + static axes)
    """
    graph.refresh_derived_shares()

    outbound_map = compute_outbound_criticality_map(graph, config)
    configured_stages = config.inbound_per_stage_stages  # None → use all
    normalize = config.inbound_per_stage_normalize

    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares

        # Single source of truth: per-stage HHIs across every SUPPLY_EDGE_TYPES
        # edge type with edges present. Never hardcoded.
        stage_hhis = compute_stage_hhis(derived, normalize=normalize)
        node.dynamic.stage_hhis = stage_hhis or None

        # Convenience accessors — read from stage_hhis, do not recompute.
        node.dynamic.mined_by_hhi    = stage_hhis.get("mines")
        node.dynamic.refined_by_hhi  = stage_hhis.get("refines")
        node.dynamic.supplied_by_hhi = stage_hhis.get("supplies")

        # Legacy blended value — kept purely for inspection / diffing.
        node.dynamic.combined_hhi = hhi_from_derived_shares(derived, normalize=normalize)

        # Combine present per-stage HHIs into inbound_hhi. When the yaml
        # opts out via an explicit stages list, honour it; otherwise use
        # everything present. This is the fix for the previous defect,
        # where the code hardcoded {mines, refines, supplies} in Python
        # so listing more in yaml silently did nothing.
        if configured_stages is None:
            present = stage_hhis
        else:
            present = {s: v for s, v in stage_hhis.items() if s in configured_stages}
        inbound = combine_per_stage(present, config)

        outbound = outbound_map.get(node.id, 0.0)
        concentration = combine_concentration(inbound, outbound, config)

        node.dynamic.inbound_hhi = inbound
        node.dynamic.outbound_criticality = outbound
        node.dynamic.concentration = concentration

        baseline = compute_baseline_severity(node, config)
        node.dynamic.current_severity = baseline
        node.dynamic.chokepoint_tier = derive_chokepoint_tier(baseline, config)
