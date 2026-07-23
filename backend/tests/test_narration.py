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


SEVERITY_WORDS = ("critical", "high", "moderate", "low")


def test_tier_word_in_why_title_matches_chokepoint_tier(graph, narration_builder):
    """Scored nodes only: the why-section title contains the tier word.
    Pass E — unscored nodes are handled by
    test_unscored_why_section_title_and_body_are_authored below; this
    test no longer skips them silently (that hid 42 panels)."""
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
            node.dynamic.baseline_tier.value
            if node.dynamic.baseline_tier
            else "none"
        )
        if tier == "unscored":
            continue  # covered explicitly by the unscored test below
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


def test_unscored_why_section_title_and_body_are_authored(graph, narration_builder):
    """Pass E — every unscored node's why-section renders authored copy:
      - title contains the authored unscored wording and NONE of the
        severity words {critical, high, moderate, low}
      - body is non-empty and names a missing axis (or generic fallback)
      - no {tier} placeholder and no literal 'unscored' token leak into
        any title or body (INV-4)
    """
    from app.schema.enums import ChokepointTier

    checked = 0
    for node in graph.nodes.values():
        if node.dynamic.baseline_tier != ChokepointTier.UNSCORED:
            continue
        checked += 1
        narr = narration_builder.build(node.id)
        why = next((s for s in narr["sections"] if s["key"] == "why_scores"), None)
        assert why is not None, (
            f"{node.id} unscored: no why_scores section rendered"
        )

        # Title contains authored wording (case-insensitive substring)
        title_lower = why["title"].lower()
        assert "why this isn't scored" in title_lower, (
            f"{node.id}: unscored title unexpected: {why['title']!r}"
        )
        # And none of the severity words
        for sev_word in SEVERITY_WORDS:
            assert sev_word not in title_lower, (
                f"{node.id}: unscored title contains severity word "
                f"{sev_word!r}: {why['title']!r}"
            )

        # Body is non-empty and names a reason (missing axis or generic).
        body = why["body"]
        assert body and body.strip(), f"{node.id}: unscored body empty"
        acceptable = [
            "no substitutability value on record",
            "no lead-time value on record",
            "required static axes for scoring are absent",  # generic fallback
        ]
        assert any(phrase in body for phrase in acceptable), (
            f"{node.id}: unscored body names no missing-axis reason: {body!r}"
        )

    # Pass E: 42 unscored. Pass H: NVIDIA + Quanta scored → 40.
    # Pass H.1 §4: Germany added → 41.
    assert checked == 41, (
        f"expected 41 unscored nodes to check (Pass H.1 §4 update: "
        f"+Germany), got {checked}. If the graph's scored/unscored "
        f"split changed, update this count deliberately (not silently)."
    )


def test_no_placeholder_or_unscored_token_leaks_into_any_rendered_text(
    graph, narration_builder,
):
    """INV-4: no `{tier}` placeholder and no literal `unscored` token
    appears in any rendered title or body across all 66 nodes."""
    offenders = []
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        for s in narr["sections"]:
            for field in ("title", "body"):
                text = s.get(field, "")
                if "{tier}" in text:
                    offenders.append((node.id, s["key"], field, "{tier} placeholder"))
                if "unscored" in text.lower():
                    offenders.append((node.id, s["key"], field, "literal 'unscored'"))
    assert not offenders, offenders[:5]


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
