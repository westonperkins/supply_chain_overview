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
    # Axes that were absent when this node was scored — the engine
    # substituted its missing-axes-mode default (neutral: 1.0 term;
    # suppress: legacy legacy_substitutability / legacy_lead_time_years).
    # Names the axes ("substitutability" and/or "lead_time_years").
    # See docs/scoring_correctness_fixes_spec.md §1.
    scored_on_default_axes: Optional[list[str]] = None
    # Legacy blended HHI — kept for inspection / before-after diffing.
    combined_hhi: Optional[float] = None
    inbound_hhi: Optional[float] = None               # combine of per-stage per scoring.yaml (default max)
    outbound_criticality: Optional[float] = None      # normalized [0,1] — captures ASML/TSMC-style upstream chokepoints
    concentration: Optional[float] = None             # combined value used in severity formula
    current_severity: Optional[float] = None
    chokepoint_tier: Optional[ChokepointTier] = None
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
