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


def _glance_text_fragments(glance: dict) -> list[tuple[str, str]]:
    """Every user-facing string in a glance payload — the summary
    sentence, each supply line, the reach sentence, and every
    breadcrumb step's from/verb/to. Returned as (label, text) so an
    offender can be traced back to its field."""
    out: list[tuple[str, str]] = []
    if glance.get("summary"):
        out.append(("summary", glance["summary"]))
    for i, l in enumerate(glance.get("supply_lines") or []):
        out.append((f"supply_lines[{i}].text", l.get("text", "")))
    if glance.get("reach"):
        out.append(("reach", glance["reach"]))
    for pi, path in enumerate(glance.get("paths") or []):
        for si, step in enumerate(path):
            out.append((f"paths[{pi}][{si}].from", step.get("from", "")))
            out.append((f"paths[{pi}][{si}].verb", step.get("verb", "")))
            out.append((f"paths[{pi}][{si}].to",   step.get("to",   "")))
    return out


def test_glance_summary_present_and_clean_for_every_node(
    graph, narration_builder,
):
    """Pass I / I.1 — every node returns a `glance.summary` sentence
    that is non-empty, has no unfilled `{...}` placeholder, no
    double-space or edge-space artifact, and ends with a period.
    The summary is the one universal glance field; supply_lines /
    reach / paths render only where they apply."""
    offenders = []
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        assert "glance" in narr, f"{node.id}: no glance field"
        sentence = narr["glance"].get("summary")
        if not sentence or not sentence.strip():
            offenders.append((node.id, "empty"))
            continue
        if "{" in sentence or "}" in sentence:
            offenders.append((node.id, f"placeholder leak: {sentence!r}"))
        if "  " in sentence:
            offenders.append((node.id, f"double-space: {sentence!r}"))
        if sentence != sentence.strip():
            offenders.append((node.id, f"edge-space: {sentence!r}"))
        if not sentence.rstrip().endswith("."):
            offenders.append((node.id, f"no trailing period: {sentence!r}"))
    assert not offenders, offenders[:5]


def test_glance_no_placeholder_or_literal_s_paren_leaks(
    graph, narration_builder,
):
    """Pass I.1 AC5 — no `{...}` placeholder and no literal `(s)`
    pluralization token appears anywhere in the glance payload
    (summary / supply_lines / reach / paths). Pluralization is
    authored via singular/plural forms in narration.yaml so the
    rendered strip never reads `mineral(s)`."""
    offenders: list[tuple[str, str, str]] = []
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        for label, text in _glance_text_fragments(narr["glance"]):
            if not text:
                continue
            if "{" in text or "}" in text:
                offenders.append((node.id, label, f"placeholder leak: {text!r}"))
            if "(s)" in text.lower():
                offenders.append((node.id, label, f"literal '(s)': {text!r}"))
    assert not offenders, offenders[:5]


def test_glance_reach_downstream_count_matches_independent_bfs(
    graph, narration_builder,
):
    """Pass I.1 AC2 — glance.stats.downstream_nodes is computed on the
    backend over the REAL edge set (not rendered edges). This test
    pins it against an independent BFS over the graph's outbound
    supply-flow edges, so a future refactor that drifts the client's
    view-state walk into the strip's chip count is caught here.

    Chosen anchor: China. Its trail covers roughly half the graph and
    is the exemplar for the whole feature."""
    from collections import deque
    walk_types = {"mines", "refines", "supplies", "input_to", "component_of"}
    anchor_id = "country_region:china"
    reached: set[str] = set()
    queue: deque[str] = deque([anchor_id])
    while queue:
        cur = queue.popleft()
        for e in graph.out_edges(cur):
            if e.type.value not in walk_types:
                continue
            if e.target_id == anchor_id or e.target_id in reached:
                continue
            reached.add(e.target_id)
            queue.append(e.target_id)

    narr = narration_builder.build(anchor_id)
    stats = narr["glance"]["stats"]
    assert stats["downstream_nodes"] == len(reached), (
        f"glance.stats.downstream_nodes drift for {anchor_id}: "
        f"stats={stats['downstream_nodes']}, independent BFS={len(reached)}"
    )
    # China's downstream reach covers roughly half the graph — the
    # canonical demo for the whole strip. Pin the number so a scoring
    # or edge-set change here surfaces loudly.
    assert stats["downstream_nodes"] == 33, (
        f"China downstream_nodes changed: {stats['downstream_nodes']} "
        f"(previously 33). If the graph or the walk set changed, "
        f"update this pin deliberately."
    )
    # Chokepoints named in the reach sentence per AC1/AC2.
    assert "mineral:dysprosium" in stats["critical_reached"]
    assert "mineral:gallium" in stats["high_reached"]
    assert "company:tsmc" in stats["high_reached"]
    assert "Dysprosium" in narr["glance"]["reach"]


def test_glance_paths_seeded_from_distinct_first_hops(
    graph, narration_builder,
):
    """Pass I.1 AC3 — paths seed from N heaviest DISTINCT first-hop
    edges. Three near-identical dysprosium walks would fail this even
    if hops 2/3 differ, so we assert distinct first-hop targets
    across paths for any node with out-degree >= 2."""
    for node in graph.nodes.values():
        narr = narration_builder.build(node.id)
        paths = narr["glance"]["paths"]
        if len(paths) < 2:
            continue
        first_hop_targets = [p[0]["to"] for p in paths if p]
        assert len(first_hop_targets) == len(set(first_hop_targets)), (
            f"{node.id}: paths share a first-hop target: {first_hop_targets}"
        )


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
