from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
import json

from ..schema import Event


class IngestionSource(ABC):
    """Swappable seam for event sources. Everything downstream of ingestion
    (scoring, cascade, UI) is developed against MockIngestionSource until
    the schema is proven end-to-end; then a real source (GDELT, NewsAPI,
    etc.) is dropped in behind this same interface."""

    @abstractmethod
    def fetch(self) -> Iterable[Event]:
        ...


class MockIngestionSource(IngestionSource):
    """Reads hand-authored events from a JSON file — the only ingestion
    source until steps 1-5 of the build order are locked."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self) -> list[Event]:
        with self.path.open() as f:
            return [Event(**raw) for raw in json.load(f)]
