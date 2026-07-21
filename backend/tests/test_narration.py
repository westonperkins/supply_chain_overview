"""Test 10 — Narration invariants.

These are structural. Specific words in narration copy are not asserted
here — those live in narration.yaml and would move under any template
tuning. The tests below are what has to hold no matter how the templates
read.
"""
import re


def test_every_node_returns_a_narration(graph, narration_builder):
    for node_id in graph.nodes:
        narration_builder.build(node_id)


def test_no_section_body_is_empty_or_dangling(graph, narration_builder):
    dangling_suffixes = (
        " and",
        " which supply",
        " and others,",  # dangling if it's the terminal text
    )
    offenders = []
    for node_id in graph.nodes:
        narr = narration_builder.build(node_id)
        for s in narr["sections"]:
            body = s["body"].strip()
            if not body:
                offenders.append((node_id, s["key"], "empty"))
                continue
            body_trimmed = body.rstrip(".").rstrip()
            for suf in dangling_suffixes:
                if body_trimmed.endswith(suf.rstrip(".").rstrip()):
                    offenders.append((node_id, s["key"], f"dangling: …{suf}"))
    assert not offenders, offenders[:5]


def test_tier_word_in_why_title_matches_chokepoint_tier(graph, narration_builder):
    tier_words = {
        "critical": "critical",
        "high": "high",
        "moderate": "moderate",
        "none": "low",
    }
    mismatches = []
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        tier = (
            node.dynamic.chokepoint_tier.value
            if node.dynamic.chokepoint_tier
            else "none"
        )
        expected_word = tier_words[tier]
        for s in narr["sections"]:
            if s["key"] != "why_scores":
                continue
            title = s["title"].lower()
            # country panels use "why it matters" — accept as valid override.
            if "why it matters" in title:
                break
            if expected_word not in title:
                mismatches.append((node.id, tier, s["title"]))
    assert not mismatches, mismatches[:5]


def test_modeling_caveats_render(graph, narration_builder):
    for node in graph.nodes.values():
        if not node.static.modeling_caveat:
            continue
        narr = narration_builder.build(node.id)
        assert node.static.modeling_caveat in narr["caveats"], (
            f"{node.id}: modeling_caveat not rendered in narration caveats"
        )


def test_prose_percentages_match_edge_weights_to_one_decimal(graph, narration_builder):
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        # Every edge touching this node — either as source or target.
        touching = {
            round(e.weight * 100, 1)
            for e in graph.edges.values()
            if e.source_id == node.id or e.target_id == node.id
        }
        for s in narr["sections"]:
            for m in re.finditer(r"\(([\d.]+)%\)", s["body"]):
                pct = float(m.group(1))
                assert pct in touching, (
                    f"{node.id}: {pct}% in prose does not match any edge weight "
                    f"touching this node; expected one of {sorted(touching)}"
                )
