from typing import Optional

from pydantic import BaseModel, Field

from .common import Coordinates, SourcedValue
from .enums import BottleneckType, ChokepointTier, Layer, NodeType


class StaticFields(BaseModel):
    """Slow-changing fields from the paper. Each is wrapped in SourcedValue
    so confidence and source are inseparable from the value."""

    scale: Optional[SourcedValue] = None            # value.value is a Scale dict
    substitutability: Optional[SourcedValue] = None # value.value in [0, 1]
    lead_time_years: Optional[SourcedValue] = None  # value.value is a number
    bottleneck_type: Optional[BottleneckType] = None
    financial_cushion: Optional[SourcedValue] = None  # value.value in [0, 1], companies only
    notes: Optional[str] = None
    # Optional per-node caveat rendered by the narration layer. Populate only
    # when a specific score is known to be misleading due to under-modelling
    # or a scoring artefact — otherwise leave null.
    modeling_caveat: Optional[str] = None


class DynamicFields(BaseModel):
    """Live fields owned by the terminal — never confuse with static."""

    price: Optional[float] = None
    price_ex_china: Optional[float] = None
    price_spread: Optional[float] = None
    market_cap: Optional[float] = None
    market_share: Optional[float] = None

    # Derived and cached — never hand-asserted.
    # Per-stage HHIs: stage name → HHI, for every edge type in
    # SUPPLY_EDGE_TYPES that has edges present on this node.
    # This is the single source of truth for per-stage concentration;
    # the mined_by_hhi / refined_by_hhi / supplied_by_hhi fields below
    # are convenience accessors that read from this dict.
    stage_hhis: Optional[dict[str, float]] = None
    # Convenience per-stage HHIs — None when the corresponding stage
    # has no edges here. Populated from stage_hhis; nothing downstream
    # reads them for computation, only for display / narration.
    mined_by_hhi: Optional[float] = None
    refined_by_hhi: Optional[float] = None
    supplied_by_hhi: Optional[float] = None
    # Per-category HHI within the `supplies` stage — {category: hhi}.
    # Only populated when the config's per-category flag is on and this
    # node has incoming supplies edges. `supplied_by_hhi` above is the
    # combined value that flows into inbound_hhi.
    supplies_per_category_hhi: Optional[dict[str, float]] = None
    # Categories with fewer than min_suppliers_for_concentration distinct
    # modelled suppliers — recorded here so the completeness backlog can
    # surface them. These categories do NOT contribute to the max combine.
    single_supplier_categories: Optional[list[str]] = None
    # True when EVERY supplies category on this node is single-supplier,
    # so the max combine returned no signal and supplies HHI fell back to
    # the aggregate reading. The narration layer can render this caveat.
    supplies_hhi_fallback_to_aggregate: bool = False
    # Same rule at the STAGE level (mines / refines / supplies / input_to /
    # component_of / operates) — a stage bucket with only one modelled
    # source cannot distinguish a real monopoly from an unmodelled market,
    # so it does not contribute to inbound_hhi. Recorded here for the
    # backlog. If EVERY stage on this node is single-supplier, inbound is
    # 0 and `all_stages_single_supplier` is True — the node explicitly
    # has no reliable inbound signal rather than a silent fallback.
    single_supplier_stages: Optional[list[str]] = None
    all_stages_single_supplier: bool = False
    # Ambiguity carried on BOTH tiers (spec §2). With no active events,
    # baseline_tier == current_tier and these agree; under events they
    # can differ if current_severity crosses into an unresolved band.
    tier_ambiguous: bool = False              # baseline-side
    tier_ambiguous_with: Optional[list[str]] = None
    current_tier_ambiguous: bool = False      # live-side
    current_tier_ambiguous_with: Optional[list[str]] = None
    # Axes that were absent when this node was scored. Names the axes
    # ("substitutability" and/or "lead_time_years"). Under the default
    # missing_static_axes.mode: `unscored`, the engine substitutes
    # nothing — severity is None and tier is UNSCORED. Under the legacy
    # modes `neutral` (missing term contributes 1.0) or `suppress`
    # (legacy 0.5 / 1.0 defaults), the engine substitutes and this
    # field records which axes were replaced. See docs/generated/
    # node_inventory.md for the current list.
    scored_on_default_axes: Optional[list[str]] = None
    # Legacy blended HHI — kept for inspection / before-after diffing.
    combined_hhi: Optional[float] = None
    inbound_hhi: Optional[float] = None               # combine of per-stage per scoring.yaml (default max)
    outbound_criticality: Optional[float] = None      # normalized [0,1] — captures ASML/TSMC-style upstream chokepoints
    concentration: Optional[float] = None             # combined value used in severity formula
    # STRUCTURAL — recomputed by refresh_all_derived from static axes +
    # concentration. Never moved by events. Threshold derivation, the
    # generated inventory, and every structural test read this.
    baseline_severity: Optional[float] = None
    baseline_tier: Optional[ChokepointTier] = None
    # LIVE — initialized to baseline_severity / baseline_tier by
    # refresh_all_derived; then updated by propagate_event for nodes
    # touched by an active event. With zero active events, current == baseline
    # everywhere. Written ONLY by cascade.propagate_event (INV-4).
    #   current_severity is None iff baseline_severity is None AND no
    #   scored-origin event has raised it — an unscored node whose
    #   current stays None is honest: an event does not fabricate a
    #   severity value from axes the node explicitly lacks.
    current_severity: Optional[float] = None
    current_tier: Optional[ChokepointTier] = None
    # True if any contribution to this node's current_severity came from
    # an event whose origin was unscored (no baseline). Attached now for
    # the news-ingestion pass to gate ranking; this pass only records it.
    current_severity_has_unscored_origin: bool = False
    derived_shares: Optional[dict] = None             # computed from edges

    recent_event_ids: list[str] = Field(default_factory=list)
    last_updated: Optional[str] = None


class Node(BaseModel):
    id: str
    type: NodeType
    name: str
    aliases: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=lambda: ["ai"])
    layer: Optional[Layer] = None
    sub_category: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    description: Optional[str] = None

    static: StaticFields = Field(default_factory=StaticFields)
    dynamic: DynamicFields = Field(default_factory=DynamicFields)
