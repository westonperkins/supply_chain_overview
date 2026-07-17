from typing import Optional

from pydantic import BaseModel, Field

from .enums import Confidence, EdgeType


class EdgeStatic(BaseModel):
    notes: Optional[str] = None
    since_year: Optional[int] = None
    confidence: Confidence = Confidence.ESTIMATE
    source_note: Optional[str] = None


class EdgeDynamic(BaseModel):
    current_weight: Optional[float] = None  # if the weight has been observed to change
    last_updated: Optional[str] = None


class Edge(BaseModel):
    id: str
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = Field(ge=0.0, le=1.0)
    domains: list[str] = Field(default_factory=lambda: ["ai"])

    static: EdgeStatic = Field(default_factory=EdgeStatic)
    dynamic: EdgeDynamic = Field(default_factory=EdgeDynamic)

    def effective_weight(self) -> float:
        """Prefer dynamic weight when observed; fall back to static."""
        if self.dynamic.current_weight is not None:
            return self.dynamic.current_weight
        return self.weight
