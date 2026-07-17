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


class DynamicFields(BaseModel):
    """Live fields owned by the terminal — never confuse with static."""

    price: Optional[float] = None
    price_ex_china: Optional[float] = None
    price_spread: Optional[float] = None
    market_cap: Optional[float] = None
    market_share: Optional[float] = None

    # Derived and cached — never hand-asserted.
    inbound_hhi: Optional[float] = None               # HHI on incoming supplier shares
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
