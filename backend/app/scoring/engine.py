import math
from collections import defaultdict, deque
from typing import Optional

from ..graph import SupplyChainGraph
from ..schema import ChokepointTier, Node
from ..schema.enums import EdgeType, SUPPLY_EDGE_TYPES
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


def compute_stage_hhis(
    derived: Optional[dict], normalize: bool = True,
) -> tuple[dict[str, float], dict[str, int]]:
    """Compute per-stage HHIs for every edge type in SUPPLY_EDGE_TYPES that
    has edges present in `derived`. Returns ({stage: hhi}, {stage: n_sources}).

    Counts let the caller apply a stage-level `min_suppliers` gate — same
    rule as per-category HHI one level down (see spec §1). A single-source
    stage under `normalize: true` reads HHI 1.0 by construction, which
    cannot distinguish a real monopoly from unmodelled data.
    """
    if not derived:
        return {}, {}
    valid = {t.value for t in SUPPLY_EDGE_TYPES}
    hhis: dict[str, float] = {}
    counts: dict[str, int] = {}
    for stage_name, shares in derived.items():
        if stage_name not in valid or not shares:
            continue
        hhis[stage_name] = compute_hhi(shares, normalize=normalize)
        counts[stage_name] = len(shares)
    return hhis, counts


def compute_supplies_per_category(
    graph: SupplyChainGraph,
    node_id: str,
    normalize: bool = True,
) -> tuple[dict[str, float], dict[str, int]]:
    """Group the target's incoming `supplies` edges by `supply_category`
    and compute HHI per category. Returns (per_cat_hhi, supplier_counts).

    Edges with no `supply_category` land in a `general` sub-bucket. The
    supplier_counts dict lets the caller apply a `min_suppliers` gate
    (see `docs/category_validation_spec.md`) to distinguish a real
    monopoly from a category we simply haven't finished modelling."""
    buckets: dict[str, dict[str, float]] = defaultdict(dict)
    for edge in graph.in_edges(node_id, [EdgeType.SUPPLIES]):
        cat = edge.supply_category or "general"
        buckets[cat][edge.source_id] = edge.effective_weight()
    hhis = {cat: compute_hhi(shares, normalize=normalize)
            for cat, shares in buckets.items()}
    counts = {cat: len(shares) for cat, shares in buckets.items()}
    return hhis, counts


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

def _outbound_share_for(edge, share_field: str, fallback: bool) -> Optional[float]:
    """Which quantity to multiply along an outbound walk.

    output_share is "how much of the source's output goes to this target"
    — the correct quantity for downstream criticality ("how much of the
    supplier's output depends on this customer"). input_share was the
    legacy behaviour. See spec §2. Returns None when the edge should be
    skipped entirely (output_share requested, no fallback, edge null)."""
    if share_field == "input_share":
        return edge.effective_weight()
    # share_field == "output_share"
    if edge.output_share is not None:
        return edge.output_share
    if fallback:
        return edge.effective_weight()
    return None


def _outbound_criticality_raw(
    node_id: str,
    graph: SupplyChainGraph,
    decay: float,
    max_hops: int,
    min_influence: float,
    share_field: str = "input_share",
    fallback: bool = True,
    walk_counter: Optional[dict] = None,
) -> float:
    """Walks downstream from node_id, multiplying `share_field` on each hop.
    `walk_counter` (optional) accumulates {"output_share": n, "fallback": n,
    "skipped": n} for the fallback census in the report layer."""
    best_influence: dict[str, float] = {}
    queue: deque[tuple[str, float, int]] = deque([(node_id, 1.0, 0)])
    while queue:
        curr_id, running, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for edge in graph.downstream_supply_edges(curr_id):
            target_id = edge.target_id
            if target_id == node_id:
                continue
            share = _outbound_share_for(edge, share_field, fallback)
            if walk_counter is not None:
                if share_field == "output_share":
                    if edge.output_share is not None:
                        walk_counter["output_share"] = walk_counter.get("output_share", 0) + 1
                    elif fallback:
                        walk_counter["fallback"] = walk_counter.get("fallback", 0) + 1
                    else:
                        walk_counter["skipped"] = walk_counter.get("skipped", 0) + 1
                else:
                    walk_counter["input_share"] = walk_counter.get("input_share", 0) + 1
            if share is None:
                continue
            new_running = running * share
            new_depth = depth + 1
            influence = new_running * (decay ** new_depth)
            if influence <= min_influence:
                continue
            if influence > best_influence.get(target_id, 0.0):
                best_influence[target_id] = influence
                queue.append((target_id, new_running, new_depth))
    return math.sqrt(sum(v * v for v in best_influence.values()))


def compute_outbound_criticality_map(
    graph: SupplyChainGraph, config: ScoringConfig,
    walk_counter: Optional[dict] = None,
) -> dict[str, float]:
    """Compute normalized [0, 1] outbound criticality for every node.

    Normalization mode from config:
      `graph_max` — legacy: divide by the current graph's max raw outbound.
                    Relative; every node's normalized score depends on
                    every other node's raw value.
      `fixed`     — divide by a committed constant. Scores are comparable
                    across runs and graph edits. Clamped to 1.0 so a
                    future node exceeding the reference saturates rather
                    than breaks the [0, 1] contract.
    """
    decay = config.concentration_outbound_decay
    max_hops = config.concentration_outbound_max_hops
    min_influence = config.concentration_outbound_min_influence
    share_field = config.outbound_share_field
    fallback = config.outbound_fallback_to_input_share
    raw = {
        node_id: _outbound_criticality_raw(
            node_id, graph, decay, max_hops, min_influence,
            share_field=share_field, fallback=fallback,
            walk_counter=walk_counter,
        )
        for node_id in graph.nodes
    }
    mode = config.outbound_normalization_mode
    if mode == "fixed":
        ref = config.outbound_fixed_reference
        # First-run / unset — fall back to graph max so the derivation
        # step (`report --derive-fixed-reference`) can capture a value.
        if ref is None or ref <= 0.0:
            ref = max(raw.values()) if raw else 0.0
    else:  # graph_max
        ref = max(raw.values()) if raw else 0.0
    if ref <= 0.0:
        return {k: 0.0 for k in raw}
    return {k: min(1.0, v / ref) for k, v in raw.items()}


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


def compute_baseline_severity(node: Node, config: ScoringConfig) -> Optional[float]:
    """Uses the node's cached concentration (inbound+outbound combined).
    Called after refresh_all_derived has populated node.dynamic.concentration.
    Missing axes are resolved via axes_for_severity — see its docstring
    for the three modes.

    Returns None when the node is unscored (missing axes + mode=unscored).
    Callers set severity None and tier UNSCORED in that case.
    """
    conc = node.dynamic.concentration or 0.0
    sub, lt_norm, missing = axes_for_severity(node, config)
    node.dynamic.scored_on_default_axes = missing or None
    if sub is None or lt_norm is None:
        return None
    return compute_severity(conc, sub, lt_norm, config)


def _sourced_number(sv, default: float) -> float:
    if sv is None or sv.value is None:
        return default
    try:
        return float(sv.value)
    except (TypeError, ValueError):
        return default


def _axis_or_none(sv) -> Optional[float]:
    """Returns the axis value if present, else None (rather than a
    silent default). Callers decide how to handle absence based on
    config.missing_axes_mode."""
    if sv is None or sv.value is None:
        return None
    try:
        return float(sv.value)
    except (TypeError, ValueError):
        return None


# Anchor lead-time for `neutral` missing-axes mode: 25 years happens to
# normalize to 1.0 under the current log10_1p transform (log10(26)/log10(26)),
# which is the identity element of the multiplicative formula. If the
# normalization transform ever changes, this constant must move with it.
NEUTRAL_LEAD_TIME_ANCHOR_YEARS = 25.0


def axes_for_severity(
    node: Node,
    config: ScoringConfig,
    sub_delta: float = 0.0,
    lt_delta: float = 0.0,
) -> tuple[Optional[float], Optional[float], list[str]]:
    """Compute (substitutability_value, normalized_lead_time, missing_axes).

    Modes (config.missing_axes_mode):
      unscored — default. When ANY required axis is missing, returns
                 (None, None, missing). The caller (compute_baseline_severity
                 / cascade._event_severity_at_source) must treat that as
                 "refuse to score" — severity None, tier `unscored`.
      neutral  — a missing axis contributes 1.0 to the multiplicative
                 product (sub=0.0 → (1-sub)=1.0; lt_norm=1.0).
      suppress — legacy: missing axes use legacy_substitutability=0.5 and
                 legacy_lead_time_years=1.0 → 0.107 severity multiplier.

    Both engine.compute_baseline_severity and
    cascade._event_severity_at_source go through this helper — they must
    not diverge. See test_cascade_and_engine_use_identical_axis_handling.
    """
    mode = config.missing_axes_mode
    sub_raw = _axis_or_none(node.static.substitutability)
    lt_raw = _axis_or_none(node.static.lead_time_years)

    missing: list[str] = []
    if sub_raw is None:
        missing.append("substitutability")
    if lt_raw is None:
        missing.append("lead_time_years")

    if missing and mode == "unscored":
        return None, None, missing

    # Substitutability
    if sub_raw is not None:
        sub_base = sub_raw
    elif mode == "suppress":
        sub_base = config.missing_axes_legacy_substitutability
    else:  # neutral
        sub_base = 0.0
    sub_used = max(0.0, min(1.0, sub_base + sub_delta))

    # Lead time (raw years) → normalized
    if lt_raw is not None:
        lt_base_years = lt_raw
    elif mode == "suppress":
        lt_base_years = config.missing_axes_legacy_lead_time_years
    else:  # neutral — anchor at 25y so the neutral term is exactly 1.0
        lt_base_years = NEUTRAL_LEAD_TIME_ANCHOR_YEARS
    lt_years = max(0.0, lt_base_years + lt_delta)
    lt_norm = normalize_lead_time(lt_years, config.lead_time_normalization)

    return sub_used, lt_norm, missing


# --------------------------------------------------------------------------- #
# Chokepoint tier — derived, cached                                            #
# --------------------------------------------------------------------------- #

def derive_chokepoint_tier(
    baseline_severity: Optional[float], config: ScoringConfig,
) -> ChokepointTier:
    """None severity → UNSCORED (missing axes; distinct from NONE which
    is a scored value below the moderate threshold).

    Boundaries come from config.chokepoint_thresholds, which resolves to
    the derived thresholds.boundaries block written by Pass B. Not
    hard-coded here — every value is a function of the committed
    inventory + separation_factor. See
    docs/generated/threshold_analysis.md."""
    if baseline_severity is None:
        return ChokepointTier.UNSCORED
    t = config.chokepoint_thresholds
    if baseline_severity >= t["critical"]:
        return ChokepointTier.CRITICAL
    if baseline_severity >= t["high"]:
        return ChokepointTier.HIGH
    if baseline_severity >= t["moderate"]:
        return ChokepointTier.MODERATE
    return ChokepointTier.NONE


def _compute_tier_ambiguity(
    severity: Optional[float],
    tier_name: Optional[str],
    config: ScoringConfig,
) -> tuple[bool, Optional[list[str]]]:
    """A node is ambiguous when its severity sits inside a threshold-
    derivation unresolved band (§1.4). tier_ambiguous_with names the
    OTHER tier(s) the node plausibly belongs to — EXCLUDING its own
    derived tier. F4 fix (Pass C): matches the thresholds.py contract."""
    if severity is None:
        return False, None
    for band in config.threshold_unresolved_bands:
        lower = float(band.get("lower", 0.0))
        upper = float(band.get("upper", 1.0))
        if lower <= severity <= upper:
            others = [t for t in band.get("tiers", []) if t != tier_name]
            return True, others or None
    return False, None


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
    per_cat_enabled = config.supplies_per_category_enabled
    per_cat_combine = config.supplies_per_category_combine
    min_suppliers = config.supplies_min_suppliers_for_concentration
    stage_min_suppliers = config.stage_min_suppliers_for_concentration

    for node in graph.nodes.values():
        derived = node.dynamic.derived_shares

        # Single source of truth: per-stage HHIs across every SUPPLY_EDGE_TYPES
        # edge type with edges present. Never hardcoded.
        stage_hhis, stage_counts = compute_stage_hhis(derived, normalize=normalize)

        # Per-category split within `supplies` — replaces the aggregate
        # `supplies` HHI with a per-category combine (default max). Same
        # reasoning as per-stage HHI at the type level: a target is fragile
        # if ANY single category is single-sourced. See
        # `docs/per_category_supplies_report.md` and
        # `docs/category_validation_spec.md`.
        #
        # A category with < min_suppliers modelled suppliers cannot
        # distinguish real concentration from an unmodelled market, so it
        # does NOT contribute to the max. If every category on the node is
        # single-supplier, we fall back to the aggregate reading rather
        # than pretending we have signal.
        if per_cat_enabled and "supplies" in stage_hhis:
            per_cat, counts = compute_supplies_per_category(
                graph, node.id, normalize=normalize
            )
            single_supplier = sorted(c for c, n in counts.items() if n < min_suppliers)
            contributing = {c: h for c, h in per_cat.items()
                            if counts[c] >= min_suppliers}
            if contributing:
                if per_cat_combine == "max":
                    stage_hhis["supplies"] = max(contributing.values())
                else:  # weighted_sum — equal weight for now
                    stage_hhis["supplies"] = sum(contributing.values()) / len(contributing)
            # else: every category is single-supplier — leave the aggregate
            # value that compute_stage_hhis already put in stage_hhis["supplies"].
            node.dynamic.supplies_per_category_hhi = per_cat or None
            node.dynamic.single_supplier_categories = single_supplier or None
            node.dynamic.supplies_hhi_fallback_to_aggregate = bool(
                per_cat and not contributing
            )
        else:
            node.dynamic.supplies_per_category_hhi = None
            node.dynamic.single_supplier_categories = None
            node.dynamic.supplies_hhi_fallback_to_aggregate = False

        node.dynamic.stage_hhis = stage_hhis or None

        # Convenience accessors — read from stage_hhis, do not recompute.
        node.dynamic.mined_by_hhi    = stage_hhis.get("mines")
        node.dynamic.refined_by_hhi  = stage_hhis.get("refines")
        node.dynamic.supplied_by_hhi = stage_hhis.get("supplies")

        # Legacy blended value — kept purely for inspection / diffing.
        node.dynamic.combined_hhi = hhi_from_derived_shares(derived, normalize=normalize)

        # Stage-level min_suppliers gate — a single-source stage bucket
        # under normalize=true reads HHI 1.0 by construction (a single
        # share divided by its own sum is 1.0), which cannot distinguish
        # a real monopoly from unmodelled data. Same rule as per-category
        # HHI one level down. See spec §1.
        single_supplier_stages = sorted(
            s for s, n in stage_counts.items() if n < stage_min_suppliers
        )
        gated_stage_hhis = {
            s: h for s, h in stage_hhis.items()
            if stage_counts.get(s, 0) >= stage_min_suppliers
        }
        # Combine gated per-stage HHIs into inbound_hhi. When the yaml
        # opts out via an explicit stages list, honour it; otherwise use
        # everything present.
        if configured_stages is None:
            present = gated_stage_hhis
        else:
            present = {s: v for s, v in gated_stage_hhis.items()
                       if s in configured_stages}
        # If the node had stage buckets at all but every one is single-
        # supplier, we do NOT silently fall back to the aggregate — we
        # report the node as having no reliable inbound signal.
        node.dynamic.single_supplier_stages = single_supplier_stages or None
        node.dynamic.all_stages_single_supplier = bool(
            stage_hhis and not present
        )
        if node.dynamic.all_stages_single_supplier:
            inbound = 0.0
        else:
            inbound = combine_per_stage(present, config)

        outbound = outbound_map.get(node.id, 0.0)
        concentration = combine_concentration(inbound, outbound, config)

        node.dynamic.inbound_hhi = inbound
        node.dynamic.outbound_criticality = outbound
        node.dynamic.concentration = concentration

        # Pass D — STRUCTURAL fields. baseline_* is what the graph would
        # score with zero active events. Events must never move these
        # (INV-4). current_* is initialized to baseline_* here; cascade
        # updates current_* only for nodes touched by active events.
        baseline = compute_baseline_severity(node, config)
        node.dynamic.baseline_severity = baseline
        tier = derive_chokepoint_tier(baseline, config)
        node.dynamic.baseline_tier = tier
        tier_name = tier.value if tier else None
        amb, amb_with = _compute_tier_ambiguity(baseline, tier_name, config)
        node.dynamic.tier_ambiguous = amb
        node.dynamic.tier_ambiguous_with = amb_with

        # Initialize LIVE fields = baseline. Cascade may overwrite for
        # affected nodes (§3 step 3). No events → current == baseline
        # everywhere → T1 passes.
        node.dynamic.current_severity = baseline
        node.dynamic.current_tier = tier
        node.dynamic.current_tier_ambiguous = amb
        node.dynamic.current_tier_ambiguous_with = amb_with
        node.dynamic.current_severity_has_unscored_origin = False
