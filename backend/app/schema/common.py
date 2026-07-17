from typing import Any, Optional

from pydantic import BaseModel, Field

from .enums import Confidence


class Coordinates(BaseModel):
    lat: float
    lng: float


class Scale(BaseModel):
    """Structured magnitude — value + unit — so scale can be compared numerically."""
    value: float
    unit: str  # e.g. "t/yr", "GW", "USD", "GPUs"


class SourcedValue(BaseModel):
    """Wraps a static value with its confidence + source note.

    Lets the terminal distinguish a hard USGS number from an analyst inference.
    """
    value: Any
    confidence: Confidence = Confidence.ESTIMATE
    source_note: Optional[str] = None
