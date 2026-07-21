from pathlib import Path
from typing import Any, Optional

import yaml


class NarrationConfig:
    """Wraps config/narration.yaml. Every phrasing decision is a lookup here —
    if a phrase is being built in Python, it belongs in this file instead."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw

    @classmethod
    def load(cls, path: Path) -> "NarrationConfig":
        with path.open() as f:
            return cls(yaml.safe_load(f))

    # ---------- word-scales ------------------------------------------------

    def scale_phrase(self, scale_name: str, value: float) -> Optional[str]:
        scale = self.raw["scales"].get(scale_name)
        if not scale:
            return None
        # Scale entries are ordered high→low; first entry with min ≤ value wins.
        for entry in scale:
            if value >= entry["min"]:
                return entry["phrase"]
        return scale[-1]["phrase"]

    # ---------- edge templates ---------------------------------------------

    def edge_template(self, edge_type: str, direction: str) -> Optional[str]:
        return self.raw.get("edges", {}).get(edge_type, {}).get(direction)

    # ---------- section titles ---------------------------------------------

    def section_title(
        self,
        node_type_key: str,
        section_key: str,
        tier: str,
    ) -> Optional[str]:
        """Returns the section title for the given (type, section), or None to
        signal the section is omitted for this type."""
        type_map = self.raw["sections"].get(node_type_key, {})
        default_map = self.raw["sections"]["default"]

        # Explicit override wins; explicit None means omit.
        if section_key in type_map:
            title = type_map[section_key]
            if title is None:
                return None
        else:
            title = default_map.get(section_key)
            if title is None:
                return None

        tier_word = self.tier_words.get(tier, tier)
        return title.replace("{tier}", tier_word)

    @property
    def tier_words(self) -> dict[str, str]:
        return self.raw["tier_words"]

    # ---------- confidence hedges ------------------------------------------

    def confidence_hedge(self, confidence: str) -> str:
        hedges = self.raw["confidence_hedges"]
        return hedges.get(confidence, "")

    # ---------- limits ------------------------------------------------------

    @property
    def share_decimals(self) -> int:
        return int(self.raw["limits"]["share_decimal_places"])

    @property
    def max_sentences(self) -> int:
        return int(self.raw["limits"]["max_sentences_per_section"])

    # ---------- chain -------------------------------------------------------

    @property
    def chain_max_hops(self) -> int:
        return int(self.raw["chain"]["max_hops"])

    @property
    def chain_joiner(self) -> str:
        return self.raw["chain"]["joiner"]

    # ---------- acronyms ----------------------------------------------------

    @property
    def acronyms(self) -> dict[str, str]:
        return self.raw.get("acronyms", {})

    # ---------- disclaimers -------------------------------------------------

    @property
    def company_rating_disclaimer(self) -> str:
        text = self.raw.get("disclaimers", {}).get("company_rating", "")
        return " ".join(text.split())  # collapse YAML line folding
