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
        signal the section is omitted for this type.

        Pass E — when tier == 'unscored', a dedicated per-section title from
        the `unscored.section_titles` block is used. It never runs through
        the {tier} → tier_words substitution that would otherwise resolve to
        the literal token `unscored` or a severity word (INV-4)."""
        if tier == "unscored":
            override = self.raw.get("unscored", {}).get("section_titles", {}).get(section_key)
            if override is not None:
                return override
            # No override for this (unscored, section) — fall through so
            # sections we haven't authored for (where_from / what_feeds /
            # if_broke) still render normally.

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

    def unscored_body(self) -> dict:
        """The authored body pieces for the unscored `why` section (Pass E).
        See config/narration.yaml `unscored.body`."""
        return self.raw.get("unscored", {}).get("body", {})

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

    # ---------- glance strip (Pass I) --------------------------------------

    def glance_summary(self, node_type_key: str) -> dict:
        """Returns the raw glance_summary block for a node type (mineral /
        company / product / facility / country) — or an empty dict if
        none is authored. The builder assembles the sentence from these
        pieces exactly as it does for `unscored.body`, so no prose text
        lives in Python."""
        return self.raw.get("glance_summary", {}).get(node_type_key, {})

    def edge_glance_verb(self, edge_type: str) -> str:
        """Compact verb for the heaviest-path breadcrumb. Falls back to
        the edge type token so a missing entry never renders as blank."""
        return self.raw.get("edge_glance_verb", {}).get(edge_type, edge_type)
