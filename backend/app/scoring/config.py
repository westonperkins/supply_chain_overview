from pathlib import Path
from typing import Any, Optional

import yaml


class ScoringConfig:
    """Wraps scoring.yaml. All formula / weight / threshold access goes
    through here — code never hardcodes these values."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw

    @classmethod
    def load(cls, path: Path) -> "ScoringConfig":
        with path.open() as f:
            cfg = cls(yaml.safe_load(f))
        cfg._validate()
        return cfg

    def _validate(self) -> None:
        """Fail loudly at load if config references an edge type that isn't a
        supply edge — the whole point of listing stages is deliberate opt-out,
        so a typo or renamed edge type must surface immediately, not silently
        no-op the way the previous defect did."""
        # Import here to avoid a circular dep at module load.
        from ..schema.enums import SUPPLY_EDGE_TYPES

        stages = (
            self.raw.get("concentration", {})
            .get("inbound", {})
            .get("per_stage", {})
            .get("stages")
        )
        if stages is None:
            return
        valid = {t.value for t in SUPPLY_EDGE_TYPES}
        unknown = [s for s in stages if s not in valid]
        if unknown:
            raise ValueError(
                f"scoring.yaml: concentration.inbound.per_stage.stages contains "
                f"unknown edge types {unknown}. Valid options: {sorted(valid)}."
            )

    @property
    def formula(self) -> str:
        return self.raw["formula"]

    @property
    def weights(self) -> dict[str, float]:
        return self.raw["weights"]

    @property
    def concentration_inbound_method(self) -> str:
        return self.raw["concentration"]["inbound"]["method"]

    # ---------------- Per-stage inbound HHI ---------------- #

    @property
    def inbound_per_stage_stages(self) -> Optional[list[str]]:
        """Optional restriction — when None, use every stage in
        SUPPLY_EDGE_TYPES that has edges present on the node. Listing stages
        here is an opt-OUT of edge types, not the default set."""
        stages = (
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("stages")
        )
        return list(stages) if stages else None

    @property
    def inbound_per_stage_normalize(self) -> bool:
        """When true (legacy), per-stage HHI divides each share by the
        stage's sum before squaring, so a bucket summing to 0.08 reads
        as 1.00 — incompleteness disappears. When false, HHI is the sum
        of squared raw shares, so incomplete buckets self-report."""
        return bool(
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("normalize", True)
        )

    @property
    def inbound_per_stage_combine(self) -> str:
        return (
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("combine", "max")
        )

    @property
    def stage_min_suppliers_for_concentration(self) -> int:
        """Minimum distinct sources a stage bucket must have before it
        contributes to the combine. See yaml comment + spec §1."""
        return int(
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("min_suppliers_for_concentration", 2)
        )

    @property
    def inbound_per_stage_weights(self) -> dict[str, float]:
        return dict(
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("weights", {})
        )

    # ---------------- Per-category supplies HHI ---------------- #

    @property
    def supplies_per_category_enabled(self) -> bool:
        """When true (default), the `supplies` stage's HHI is computed by
        grouping in-edges by `supply_category` first, computing HHI per
        category, then combining via `supplies_per_category_combine`.
        When false, `supplies` HHI reads the aggregate bucket."""
        return bool(
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("supplies", {})
            .get("per_category", {})
            .get("enabled", True)
        )

    @property
    def supplies_per_category_combine(self) -> str:
        return (
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("supplies", {})
            .get("per_category", {})
            .get("combine", "max")
        )

    @property
    def supplies_min_suppliers_for_concentration(self) -> int:
        """Minimum number of distinct modelled suppliers a per-category bucket
        must have before it can contribute a concentration signal. Default 2
        — a single-supplier category cannot distinguish a real monopoly from
        an unmodelled market."""
        return int(
            self.raw["concentration"]["inbound"]
            .get("per_stage", {})
            .get("supplies", {})
            .get("per_category", {})
            .get("min_suppliers_for_concentration", 2)
        )

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
    def outbound_share_field(self) -> str:
        """Which edge field the outbound walk multiplies at each hop —
        `output_share` (correct quantity) or `input_share` (legacy)."""
        return self.raw["concentration"]["outbound"].get(
            "share_field", "output_share"
        )

    @property
    def outbound_fallback_to_input_share(self) -> bool:
        return bool(self.raw["concentration"]["outbound"].get(
            "fallback_to_input_share", True
        ))

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
    def cascade_share_field(self) -> str:
        return self.raw["cascade"].get("share_field", "output_share")

    @property
    def cascade_fallback_to_input_share(self) -> bool:
        return bool(self.raw["cascade"].get("fallback_to_input_share", True))

    @property
    def financial_cushion_proxy(self) -> str:
        return self.raw["cascade"]["financial_cushion_proxy"]

    @property
    def rating_thresholds(self) -> dict[str, float]:
        return self.raw["rating"]["thresholds"]
