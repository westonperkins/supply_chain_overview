from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Pass V §2.1 — every event/probe model forbids unknown keys. Before
# Pass V, Event had no model_config, so Pydantic v2 defaulted to
# extra="ignore": an unknown key in the event JSON was silently
# discarded by model_validate. That is the exact failure mode the
# unresolved-entity register exists to end, one level up — an authored
# `entities_unresolved` predating schema support would have vanished
# without error. The §2.1 extra-key sweep confirmed all 7 replay events,
# both probes, and the reference-events fixture are clean, so the freeze
# is applied here. An unknown key now raises ValidationError.
_FORBID_EXTRA = ConfigDict(extra="forbid")


class EventSource(BaseModel):
    model_config = _FORBID_EXTRA

    url: Optional[str] = None
    publisher: Optional[str] = None


class EntityMatch(BaseModel):
    model_config = _FORBID_EXTRA

    node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    match_type: str  # "name" | "alias" | "place"


class UnresolvedEntity(BaseModel):
    """Pass V §2 — an entity a source named that authoring could not
    resolve to a graph node, recorded at authoring time.

    This is NOT a match: nothing in `propagate_event` or the scoring
    path reads this field (guarded by
    test_unresolved_not_read_by_scoring). It is a durable record so the
    unresolved-entity register can aggregate it and a human can decide
    whether it warrants a new node, an alias, or nothing.

    `reason` vocabulary — FROZEN, four values (bare str with the
    vocabulary here, matching the `match_type` precedent rather than an
    enum):
      - `no_node`       — the graph has no node for this entity at all.
      - `alias_unknown` — a modelled node exists, but the source's name
                          for it is not in that node's `aliases`.
      - `ambiguous`     — the mention could resolve to more than one node.
      - `out_of_domain` — a real entity deliberately outside the AI
                          graph's scope.

    `candidate_node_id` is a HYPOTHESIS, never a match. Nothing reads it
    into the walk; it lets a human reviewing the register see what the
    author suspected. If it names a node that exists, that is a strong
    `alias_unknown` signal and the register surfaces it.
    """

    model_config = _FORBID_EXTRA

    mention: str                          # the entity as the source named it
    reason: str                           # see vocabulary above
    candidate_node_id: Optional[str] = None  # author's guess, if any — NOT a match
    notes: Optional[str] = None


class AxesImpact(BaseModel):
    """Event-specific perturbation of the three severity axes.

    Interpreted as deltas layered on top of the affected node's static values.
    Positive concentration_delta = the event increases concentration risk, etc.
    """

    model_config = _FORBID_EXTRA

    concentration_delta: float = 0.0
    substitutability_delta: float = 0.0
    lead_time_delta: float = 0.0


class CascadeStep(BaseModel):
    """One hop in the propagation path — inspectable, per the brief."""

    model_config = _FORBID_EXTRA

    node_id: str
    hop: int
    severity_at_node: float
    edge_path: list[str] = Field(default_factory=list)  # ordered edge IDs from origin to here


class Event(BaseModel):
    model_config = _FORBID_EXTRA

    id: str
    timestamp: str
    source: EventSource = Field(default_factory=EventSource)
    headline: str
    summary: Optional[str] = None

    entities_matched: list[EntityMatch] = Field(default_factory=list)
    # Pass V §2 — entities the source named that authoring could not
    # resolve to a graph node. Authored deliberately; never read by the
    # scoring path. Feeds the unresolved-entity register.
    entities_unresolved: list[UnresolvedEntity] = Field(default_factory=list)
    axes_impact: AxesImpact = Field(default_factory=AxesImpact)

    # Computed at scoring time.
    severity: Optional[float] = None
    cascade: list[CascadeStep] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
