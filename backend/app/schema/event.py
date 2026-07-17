from typing import Optional

from pydantic import BaseModel, Field


class EventSource(BaseModel):
    url: Optional[str] = None
    publisher: Optional[str] = None


class EntityMatch(BaseModel):
    node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    match_type: str  # "name" | "alias" | "place"


class AxesImpact(BaseModel):
    """Event-specific perturbation of the three severity axes.

    Interpreted as deltas layered on top of the affected node's static values.
    Positive concentration_delta = the event increases concentration risk, etc.
    """
    concentration_delta: float = 0.0
    substitutability_delta: float = 0.0
    lead_time_delta: float = 0.0


class CascadeStep(BaseModel):
    """One hop in the propagation path — inspectable, per the brief."""
    node_id: str
    hop: int
    severity_at_node: float
    edge_path: list[str] = Field(default_factory=list)  # ordered edge IDs from origin to here


class Event(BaseModel):
    id: str
    timestamp: str
    source: EventSource = Field(default_factory=EventSource)
    headline: str
    summary: Optional[str] = None

    entities_matched: list[EntityMatch] = Field(default_factory=list)
    axes_impact: AxesImpact = Field(default_factory=AxesImpact)

    # Computed at scoring time.
    severity: Optional[float] = None
    cascade: list[CascadeStep] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
