from pathlib import Path
from typing import Any

import yaml


class ScoringConfig:
    """Wraps scoring.yaml. All formula / weight / threshold access goes
    through here — code never hardcodes these values."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw

    @classmethod
    def load(cls, path: Path) -> "ScoringConfig":
        with path.open() as f:
            return cls(yaml.safe_load(f))

    @property
    def formula(self) -> str:
        return self.raw["formula"]

    @property
    def weights(self) -> dict[str, float]:
        return self.raw["weights"]

    @property
    def concentration_inbound_method(self) -> str:
        return self.raw["concentration"]["inbound"]["method"]

    @property
    def concentration_outbound_decay(self) -> float:
        return float(self.raw["concentration"]["outbound"]["decay_per_hop"])

    @property
    def concentration_outbound_max_hops(self) -> int:
        return int(self.raw["concentration"]["outbound"]["max_hops"])

    @property
    def concentration_outbound_min_influence(self) -> float:
        return float(self.raw["concentration"]["outbound"]["min_influence"])

    @property
    def concentration_combine_method(self) -> str:
        return self.raw["concentration"]["combine"]["method"]

    @property
    def concentration_inbound_weight(self) -> float:
        return float(self.raw["concentration"]["combine"]["inbound_weight"])

    @property
    def concentration_outbound_weight(self) -> float:
        return float(self.raw["concentration"]["combine"]["outbound_weight"])

    @property
    def lead_time_normalization(self) -> str:
        return self.raw.get("lead_time", {}).get("normalization", "identity")

    @property
    def chokepoint_thresholds(self) -> dict[str, float]:
        return self.raw["chokepoint_thresholds"]

    @property
    def cascade_decay(self) -> float:
        return float(self.raw["cascade"]["decay_per_hop"])

    @property
    def cascade_max_hops(self) -> int:
        return int(self.raw["cascade"].get("max_hops", 6))

    @property
    def financial_cushion_proxy(self) -> str:
        return self.raw["cascade"]["financial_cushion_proxy"]

    @property
    def rating_thresholds(self) -> dict[str, float]:
        return self.raw["rating"]["thresholds"]
