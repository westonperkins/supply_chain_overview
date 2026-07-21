from typing import Optional

from pydantic import BaseModel, Field, computed_field

from .enums import Confidence, EdgeType


class EdgeStatic(BaseModel):
    notes: Optional[str] = None
    since_year: Optional[int] = None
    confidence: Confidence = Confidence.ESTIMATE
    source_note: Optional[str] = None


class EdgeDynamic(BaseModel):
    current_input_share: Optional[float] = None  # observed override for input_share
    last_updated: Optional[str] = None


class Edge(BaseModel):
    """A directed weighted edge between two graph nodes.

    Two distinct fields carry two distinct quantities. This split resolves the
    audit finding in `docs/edge_weight_semantics_report.md`, where one
    `weight` field was holding three different things (share of target supply,
    share of source output, criticality of dependency).

    `input_share`   : the source's share of the target's supply of the thing
                      modelled by the edge type. Answers "how single-sourced
                      is the buyer?" Consumed by inbound HHI. Per-target sums
                      across one edge type should approach 1.0.
    `output_share`  : the target's share of the SOURCE'S output. Answers "how
                      captive is the supplier?" Consumed by customer-
                      concentration measures (and by cascade later, as its own
                      task). Optional — populate only where the paper
                      quantifies it.

    Cascade and outbound criticality continue reading input_share for now;
    switching them to output_share is deliberately a separate change.
    """

    id: str
    source_id: str
    target_id: str
    type: EdgeType
    input_share: float = Field(gt=0.0, le=1.0)
    output_share: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    domains: list[str] = Field(default_factory=lambda: ["ai"])

    static: EdgeStatic = Field(default_factory=EdgeStatic)
    dynamic: EdgeDynamic = Field(default_factory=EdgeDynamic)

    def effective_input_share(self) -> float:
        """Prefer dynamic override when observed; fall back to static."""
        if self.dynamic.current_input_share is not None:
            return self.dynamic.current_input_share
        return self.input_share

    # Backwards-compat alias — the previous method name still works but
    # returns input_share explicitly now.
    def effective_weight(self) -> float:
        return self.effective_input_share()

    # Backwards-compat alias exposed on serialization + attribute access so
    # frontend clients that read `edge.weight` continue working without a
    # code change during this transition. Removed once the frontend switches
    # to `input_share` directly.
    @computed_field
    @property
    def weight(self) -> float:
        return self.input_share
