from enum import Enum


class NodeType(str, Enum):
    MINERAL = "mineral"
    COMPANY = "company"
    FACILITY = "facility"
    COUNTRY_REGION = "country_region"
    PRODUCT = "product"


class Layer(str, Enum):
    MATERIALS = "materials"
    CHIPS = "chips"
    POWER = "power"
    DATA_CENTERS = "data_centers"


class BottleneckType(str, Enum):
    CONCENTRATION = "concentration"
    VOLUME_DEMAND = "volume_demand"
    PHYSICAL = "physical"
    FINANCIAL = "financial"


class ChokepointTier(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    NONE = "none"


class EdgeType(str, Enum):
    MINES = "mines"
    REFINES = "refines"
    SUPPLIES = "supplies"
    INPUT_TO = "input_to"
    COMPONENT_OF = "component_of"
    OPERATES = "operates"
    LOCATED_IN = "located_in"
    SUBSTITUTES_FOR = "substitutes_for"


# Edge types that participate in cascade propagation (carry supply flow).
# Operates is included because operating a producer IS a form of supply —
# MP Materials operates Mountain Pass which mines Nd, so an event on MP
# Materials must propagate through Mountain Pass to Nd. Note: operates is
# NOT in SHARE_INTO_TARGET (see graph.py), so it does not double-count for
# inbound HHI at the operated node.
SUPPLY_EDGE_TYPES = {
    EdgeType.MINES,
    EdgeType.REFINES,
    EdgeType.SUPPLIES,
    EdgeType.INPUT_TO,
    EdgeType.COMPONENT_OF,
    EdgeType.OPERATES,
}


class Confidence(str, Enum):
    HARD = "hard"           # authoritative primary source (USGS, filings)
    ESTIMATE = "estimate"   # published range or industry estimate
    INFERENCE = "inference" # analyst reading (e.g. "signaling intent")


class RatingLabel(str, Enum):
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
