"""Narration builder — assembles panel prose from templates in narration.yaml.

The load-bearing rule for this file: *no sentence is composed here*. Every
phrase, verb, and connector comes from the config. This file only:

  - looks up phrases via NarrationConfig
  - joins names / percentages according to config-defined layouts
  - walks the graph to gather sources / targets / cascade reach
  - substitutes into `{placeholder}` slots the templates already provide

If a change requires writing new prose in Python, that change is misplaced —
it belongs in narration.yaml.
"""

from collections import defaultdict, deque
from typing import Optional
import re

from ..graph import SupplyChainGraph
from ..schema import Edge, Node
from ..schema.enums import EdgeType, SUPPLY_EDGE_TYPES
from .config import NarrationConfig


# Edge types whose incoming direction describes "where a node comes from".
UPSTREAM_EDGE_TYPES: list[EdgeType] = [
    EdgeType.MINES,
    EdgeType.REFINES,
    EdgeType.SUPPLIES,
    EdgeType.INPUT_TO,
    EdgeType.COMPONENT_OF,
    EdgeType.OPERATES,
]

# Edge types whose outgoing direction describes "what a node feeds".
DOWNSTREAM_EDGE_TYPES: list[EdgeType] = [
    EdgeType.MINES,
    EdgeType.REFINES,
    EdgeType.SUPPLIES,
    EdgeType.INPUT_TO,
    EdgeType.COMPONENT_OF,
]


def _node_type_key(node: Node) -> str:
    """Maps schema node types to yaml section keys."""
    t = node.type.value
    if t == "country_region":
        return "country"
    return t  # mineral, company, product, facility


def _short_name(node: Node) -> str:
    """If a node's name is 'Long Form (ACRONYM)', return the acronym.
    Otherwise return the name unchanged. Applied to every mention so the
    prose is compact and the acronym-expansion pass can inject the
    long-form on first use per panel."""
    match = re.match(r"^(.+?)\s*\(([A-Z][A-Za-z0-9]*)\)\s*$", node.name)
    if match:
        return match.group(2)
    return node.name


def _pretty_sub_category(sub: Optional[str]) -> str:
    if not sub:
        return ""
    return sub.replace("_", " ")


def _sourced_number(sv, default: Optional[float] = None) -> Optional[float]:
    if sv is None or sv.value is None:
        return default
    try:
        return float(sv.value)
    except (TypeError, ValueError):
        return default


def _sourced_confidence(sv) -> str:
    if sv is None or sv.confidence is None:
        return "hard"
    return sv.confidence.value


def _join_names(names: list[str]) -> str:
    """Renders ['A', 'B', 'C'] as 'A, B and C'. Two → 'A and B'. One → 'A'."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f" and {names[-1]}"


class NarrationBuilder:
    def __init__(self, config: NarrationConfig, graph: SupplyChainGraph) -> None:
        self.config = config
        self.graph = graph

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def build(self, node_id: str) -> dict:
        node = self.graph.nodes.get(node_id)
        if node is None:
            raise KeyError(node_id)

        acronyms_used: dict[str, str] = {}
        type_key = _node_type_key(node)
        tier = self._tier_value(node)
        dominant_axis = self._dominant_axis(node)

        sections: list[dict] = []

        # Section 1: upstream ("where it comes from" / "what it buys" / ...)
        title = self.config.section_title(type_key, "where_from", tier)
        if title is not None:
            body = self._build_upstream(node, acronyms_used)
            if body:
                sections.append({"key": "where_from", "title": title, "body": body})

        # Section 2: downstream ("what it feeds" / "what it supplies" / ...)
        title = self.config.section_title(type_key, "what_feeds", tier)
        if title is not None:
            body = self._build_downstream(node, acronyms_used)
            if body:
                sections.append({"key": "what_feeds", "title": title, "body": body})

        # Section 3: why it scores
        title = self.config.section_title(type_key, "why_scores", tier)
        if title is not None:
            body = self._build_why_scores(node, dominant_axis, acronyms_used)
            if body:
                sections.append({"key": "why_scores", "title": title, "body": body})

        # Section 4: if it broke
        title = self.config.section_title(type_key, "if_broke", tier)
        if title is not None:
            body = self._build_if_broke(node)
            if body:
                sections.append({"key": "if_broke", "title": title, "body": body})

        # Scan all assembled sections for free-standing glossary acronyms and
        # inject expansion on first use — catches acronyms that appear in
        # prose without going through _name (e.g. CoWoS in TSMC's downstream).
        self._expand_free_standing_acronyms(sections, acronyms_used)

        # Caveats
        caveats = self._build_caveats(node)

        return {
            "node_id": node_id,
            "headline": {
                "name": node.name,
                "role": _pretty_sub_category(node.sub_category),
                "tier": self.config.tier_words.get(tier, tier),
            },
            "dominant_axis": dominant_axis,
            "sections": sections,
            "caveats": caveats,
            "acronyms": [
                {"term": k, "expansion": v} for k, v in acronyms_used.items()
            ],
        }

    # ------------------------------------------------------------------ #
    # Derived state helpers                                               #
    # ------------------------------------------------------------------ #

    def _tier_value(self, node: Node) -> str:
        if node.dynamic.chokepoint_tier is None:
            return "none"
        return node.dynamic.chokepoint_tier.value

    def _dominant_axis(self, node: Node) -> str:
        inbound = node.dynamic.inbound_hhi or 0.0
        outbound = node.dynamic.outbound_criticality or 0.0
        return "inbound" if inbound >= outbound else "outbound"

    # ------------------------------------------------------------------ #
    # Name formatting                                                     #
    # ------------------------------------------------------------------ #

    def _name(self, node: Node, acronyms_used: dict[str, str]) -> str:
        short = _short_name(node)
        if short in self.config.acronyms and short not in acronyms_used:
            expansion = self.config.acronyms[short]
            acronyms_used[short] = expansion
            return f"{short} ({expansion})"
        return short

    def _country_name(self, node: Node) -> str:
        # Countries are never acronyms — always return name.
        return node.name

    def _sources_with_shares(
        self,
        edges: list[Edge],
        acronyms_used: dict[str, str],
    ) -> str:
        """Format 'A (98.5%), B (1.0%) and C (0.5%)'. Top 3, then 'and others'.
        Largest first."""
        sorted_edges = sorted(edges, key=lambda e: -e.effective_weight())
        top = sorted_edges[:3]
        rendered = []
        for e in top:
            src = self.graph.nodes.get(e.source_id)
            if src is None:
                continue
            pct = e.effective_weight() * 100
            name = (
                self._country_name(src)
                if src.type.value == "country_region"
                else self._name(src, acronyms_used)
            )
            rendered.append(f"{name} ({pct:.{self.config.share_decimals}f}%)")
        if len(sorted_edges) > 3:
            # Top N as comma list + ", and others" — avoids "A, B and C and others".
            joined = ", ".join(rendered) + ", and others"
        else:
            joined = _join_names(rendered)
        return joined

    def _target_names(
        self,
        edges: list[Edge],
        acronyms_used: dict[str, str],
        limit: int = 3,
    ) -> tuple[str, list[str]]:
        """Returns ('A, B and C', [ids]) — top N targets by weight, largest first."""
        sorted_edges = sorted(edges, key=lambda e: -e.effective_weight())
        top = sorted_edges[:limit]
        ids: list[str] = []
        rendered: list[str] = []
        for e in top:
            tgt = self.graph.nodes.get(e.target_id)
            if tgt is None:
                continue
            ids.append(tgt.id)
            name = (
                self._country_name(tgt)
                if tgt.type.value == "country_region"
                else self._name(tgt, acronyms_used)
            )
            rendered.append(name)
        if len(sorted_edges) > limit:
            joined = ", ".join(rendered) + ", and others"
        else:
            joined = _join_names(rendered)
        return joined, ids

    # ------------------------------------------------------------------ #
    # Section 1 — upstream                                                #
    # ------------------------------------------------------------------ #

    def _build_upstream(self, node: Node, acronyms_used: dict[str, str]) -> Optional[str]:
        in_edges = self.graph.in_edges(node.id)
        if not in_edges:
            return None

        # Facility gets a compact two-part first section: operator + location.
        if node.type.value == "facility":
            return self._build_facility_upstream(node, acronyms_used)

        # Group incoming edges by type, in the paper's upstream order so mines
        # renders before refines etc.
        grouped: dict[EdgeType, list[Edge]] = defaultdict(list)
        for e in in_edges:
            grouped[e.type].append(e)

        sentences: list[str] = []
        for etype in UPSTREAM_EDGE_TYPES:
            edges = grouped.get(etype, [])
            if not edges:
                continue
            template = self.config.edge_template(etype.value, "upstream")
            if template is None:
                continue
            sentence = self._render_upstream_template(template, edges, acronyms_used)
            if sentence:
                sentences.append(sentence)
            if len(sentences) >= self.config.max_sentences:
                break

        if not sentences:
            return None
        return " ".join(sentences)

    def _build_facility_upstream(
        self,
        node: Node,
        acronyms_used: dict[str, str],
    ) -> Optional[str]:
        # Operator via inbound `operates` edge; location via outbound
        # `located_in` edge — these are the facility's structural context.
        operator_edges = [e for e in self.graph.in_edges(node.id) if e.type == EdgeType.OPERATES]
        location_edges = [e for e in self.graph.out_edges(node.id) if e.type == EdgeType.LOCATED_IN]

        parts: list[str] = []
        if operator_edges:
            template = self.config.edge_template("operates", "upstream") or ""
            src = self.graph.nodes.get(operator_edges[0].source_id)
            if src is not None:
                name = (
                    self._country_name(src)
                    if src.type.value == "country_region"
                    else self._name(src, acronyms_used)
                )
                parts.append(template.replace("{source}", name))
        if location_edges:
            template = self.config.edge_template("located_in", "upstream") or ""
            tgt = self.graph.nodes.get(location_edges[0].target_id)
            if tgt is not None:
                parts.append(template.replace("{source}", self._country_name(tgt)))

        if not parts:
            return None
        return " ".join(parts[: self.config.max_sentences])

    def _render_upstream_template(
        self,
        template: str,
        edges: list[Edge],
        acronyms_used: dict[str, str],
    ) -> Optional[str]:
        if "{sources_with_shares}" in template:
            body = self._sources_with_shares(edges, acronyms_used)
            if not body:
                return None
            return template.replace("{sources_with_shares}", body)
        if "{sources}" in template:
            names, _ = self._target_names(
                # reuse formatter — but we need SOURCE names not target names
                edges=[],
                acronyms_used=acronyms_used,
            )
            # Fallback path — should not be hit by any current template.
            top = sorted(edges, key=lambda e: -e.effective_weight())[:3]
            names_list: list[str] = []
            for e in top:
                src = self.graph.nodes.get(e.source_id)
                if src is None:
                    continue
                name = (
                    self._country_name(src)
                    if src.type.value == "country_region"
                    else self._name(src, acronyms_used)
                )
                names_list.append(name)
            return template.replace("{sources}", _join_names(names_list))
        if "{source}" in template:
            top = sorted(edges, key=lambda e: -e.effective_weight())
            if not top:
                return None
            src = self.graph.nodes.get(top[0].source_id)
            if src is None:
                return None
            name = (
                self._country_name(src)
                if src.type.value == "country_region"
                else self._name(src, acronyms_used)
            )
            return template.replace("{source}", name)
        return template

    # ------------------------------------------------------------------ #
    # Section 2 — downstream (chain up to 3 hops)                         #
    # ------------------------------------------------------------------ #

    def _build_downstream(self, node: Node, acronyms_used: dict[str, str]) -> Optional[str]:
        direct_edges = [
            e for e in self.graph.out_edges(node.id) if e.type in SUPPLY_EDGE_TYPES
        ]
        if not direct_edges:
            return None

        # Group by edge type so we can pick the strongest edge-type as the
        # anchor for the chain sentence.
        grouped: dict[EdgeType, list[Edge]] = defaultdict(list)
        for e in direct_edges:
            grouped[e.type].append(e)

        # Pick the edge type with the largest single edge weight — that's the
        # spine of the chain the user cares about.
        primary_type = max(
            grouped.keys(),
            key=lambda t: max((e.effective_weight() for e in grouped[t]), default=0.0),
        )
        primary_edges = grouped[primary_type]

        # First-hop sentence.
        template = self.config.edge_template(primary_type.value, "downstream")
        if template is None:
            return None

        first_hop_names, hop_ids = self._target_names(primary_edges, acronyms_used, limit=3)
        if not first_hop_names:
            return None
        first_sentence = template.replace("{targets}", first_hop_names).rstrip(".")

        # Additional hops.
        max_hops = self.config.chain_max_hops
        joiner = self.config.chain_joiner
        current_ids = hop_ids
        chained = first_sentence
        for _ in range(max_hops - 1):
            next_edges: dict[str, float] = {}
            for cid in current_ids:
                for e in self.graph.out_edges(cid):
                    if e.type not in SUPPLY_EDGE_TYPES:
                        continue
                    prev = next_edges.get(e.target_id, 0.0)
                    if e.effective_weight() > prev:
                        next_edges[e.target_id] = e.effective_weight()
            if not next_edges:
                break
            top_targets = sorted(next_edges.items(), key=lambda kv: -kv[1])[:3]
            names: list[str] = []
            for tid, _w in top_targets:
                tgt = self.graph.nodes.get(tid)
                if tgt is None:
                    continue
                name = (
                    self._country_name(tgt)
                    if tgt.type.value == "country_region"
                    else self._name(tgt, acronyms_used)
                )
                names.append(name)
            if not names:
                break
            chained += joiner + _join_names(names)
            current_ids = [tid for tid, _ in top_targets]

        sentences = [chained + "."]

        # If there's a second meaningful edge-type group, add a short second
        # sentence for it — capped at max_sentences.
        secondary_types = [t for t in grouped if t != primary_type]
        if secondary_types and len(sentences) < self.config.max_sentences:
            secondary_type = max(
                secondary_types,
                key=lambda t: max((e.effective_weight() for e in grouped[t]), default=0.0),
            )
            secondary_template = self.config.edge_template(
                secondary_type.value, "downstream"
            )
            if secondary_template is not None:
                names_str, _ = self._target_names(
                    grouped[secondary_type], acronyms_used, limit=3
                )
                if names_str:
                    sentences.append(secondary_template.replace("{targets}", names_str))

        return " ".join(sentences[: self.config.max_sentences])

    # ------------------------------------------------------------------ #
    # Section 3 — why it scores                                           #
    # ------------------------------------------------------------------ #

    def _build_why_scores(
        self,
        node: Node,
        dominant_axis: str,
        acronyms_used: dict[str, str],
    ) -> Optional[str]:
        parts: list[str] = []

        # Concentration clause — MUST branch on dominant_axis; that's the
        # single most important correctness requirement in the spec.
        if dominant_axis == "inbound":
            conc_value = node.dynamic.inbound_hhi or 0.0
            phrase = self.config.scale_phrase("concentration_inbound", conc_value)
        else:
            conc_value = node.dynamic.outbound_criticality or 0.0
            phrase = self.config.scale_phrase("concentration_outbound", conc_value)

        if phrase:
            parts.append(f"{phrase} ({conc_value:.2f} on a 0–1 scale)")

        # Substitutability clause.
        sub_value = _sourced_number(node.static.substitutability)
        if sub_value is not None:
            sub_phrase = self.config.scale_phrase("substitutability", sub_value)
            if sub_phrase:
                parts.append(sub_phrase)

        # Lead-time clause — hedged verb, not appended disclaimer.
        lt_value = _sourced_number(node.static.lead_time_years)
        if lt_value is not None:
            lt_phrase = self.config.scale_phrase("lead_time_years", lt_value)
            if lt_phrase:
                confidence = _sourced_confidence(node.static.lead_time_years)
                hedge = self.config.confidence_hedge(confidence)
                if hedge:
                    # Only lead-time phrases contain "would take " — insert
                    # the hedge immediately after so it modifies the timeframe.
                    if "would take " in lt_phrase:
                        lt_phrase = lt_phrase.replace(
                            "would take ", f"would take {hedge}"
                        )
                parts.append(lt_phrase)

        if not parts:
            return None

        # Sentence-cased final. Preserve grammar of each clause verbatim.
        first = parts[0][0].upper() + parts[0][1:]
        if len(parts) == 1:
            return first + "."
        if len(parts) == 2:
            return f"{first}, and {parts[1]}."
        return f"{first}, {parts[1]}, and {parts[2]}."

    # ------------------------------------------------------------------ #
    # Section 4 — if it broke                                             #
    # ------------------------------------------------------------------ #

    def _build_if_broke(self, node: Node) -> Optional[str]:
        # BFS downstream through supply edges only.
        reachable: set[str] = set()
        queue: deque[str] = deque([node.id])
        while queue:
            cur = queue.popleft()
            for e in self.graph.out_edges(cur):
                if e.type not in SUPPLY_EDGE_TYPES:
                    continue
                if e.target_id in reachable or e.target_id == node.id:
                    continue
                reachable.add(e.target_id)
                queue.append(e.target_id)

        if not reachable:
            return None

        critical = 0
        for rid in reachable:
            target = self.graph.nodes.get(rid)
            if target is None:
                continue
            tier = target.dynamic.chokepoint_tier
            if tier is not None and tier.value == "critical":
                critical += 1

        n = len(reachable)
        node_word = "node" if n == 1 else "nodes"
        base = f"{n} {node_word} downstream would be affected"
        if critical > 0:
            crit_word = "critical" if critical == 1 else "critical"
            base += f", {critical} of them {crit_word}"
        return base + "."

    # ------------------------------------------------------------------ #
    # Caveats                                                              #
    # ------------------------------------------------------------------ #

    def _build_caveats(self, node: Node) -> list[str]:
        caveats: list[str] = []
        if node.static.modeling_caveat:
            caveats.append(node.static.modeling_caveat)
        return caveats

    # ------------------------------------------------------------------ #
    # Acronym expansion sweep                                             #
    # ------------------------------------------------------------------ #

    def _expand_free_standing_acronyms(
        self,
        sections: list[dict],
        acronyms_used: dict[str, str],
    ) -> None:
        for term, expansion in self.config.acronyms.items():
            if term in acronyms_used:
                continue
            # Whole-word match. Skip when:
            #   - already inside / preceded by parens
            #   - immediately followed by "(" (someone else's expansion)
            #   - followed by another Capitalised word (part of a compound
            #     name like "CoWoS Advanced Packaging" — expanding mid-phrase
            #     reads as an interruption).
            pattern = re.compile(
                r"(?<![A-Za-z0-9(])"
                + re.escape(term)
                + r"(?![A-Za-z0-9])(?!\s*\()(?!\s+[A-Z])"
            )
            for s in sections:
                m = pattern.search(s["body"])
                if m:
                    s["body"] = (
                        s["body"][: m.end()]
                        + f" ({expansion})"
                        + s["body"][m.end():]
                    )
                    acronyms_used[term] = expansion
                    break
