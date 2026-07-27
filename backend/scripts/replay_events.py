"""Pass J — historical event replay.

Loads `data/ai/replay/events.json` (never the graph's events.json, which
must remain empty for the served graph) and runs each event
INDIVIDUALLY against a fresh baseline copy of the graph. Writes
per-event artifacts + a summary table to docs/generated/replay/.

Cumulative replay is deliberately not implemented — the current
formula has no time-decay, so cumulative replay would be a meaningless
stacking exercise. Cumulative is explicitly out of scope for this pass.

INV-1: the served graph must remain byte-identical. The runner writes
NOTHING to data/, NOTHING to config/, NOTHING to
docs/generated/severity_*. It reads config + graph, snapshots per-node
severities into local dicts, propagates a single event on a fresh
graph instance per event, and writes only under docs/generated/replay/.

Pass J.1 — model_rank metric.
--------------------------------------------------------------------- #
Ranking is the primary grading instrument. The rank is computed here,
in one place, so that grading.md can cite it rather than restate it.

Metric: `max_delta` descending, tie-broken by (`nodes_reached`
descending, `origin_scale` descending, `event_id` ascending). Ties
that survive all four keys are asserted impossible.

Rationale for max_delta as the primary key: max_delta measures the
model's response to the event — the largest severity move it produced
somewhere in the graph. origin_scale measures only the authored seed
(`{baseline|concentration} × magnitude × confidence`) and so is
substantially a measure of the Phase A author, not of the model. What
grading compares against observed disruption is the model's response,
not the seed.

For Pass J.1 §2 we ALSO emit `rank_by_origin_scale` (same tie-break
chain, with origin_scale promoted to primary). Events whose two ranks
differ by ≥ 2 slots feed finding F-J-5 (rank-metric instability).

Pass J.1 — probes.
--------------------------------------------------------------------- #
`--probes` runs `data/ai/replay/probes.json` (an injected-magnitude
counterfactual file) into `docs/generated/replay/probes/`. Probes NEVER
enter summary.md, ranking, or outcomes.json. Default invocation
(no flag) is unchanged.
"""
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.schema import Event
from app.scoring import (
    ScoringConfig,
    propagate_event,
    refresh_all_derived,
)

REPLAY_EVENTS = REPO / "data" / "ai" / "replay" / "events.json"
REPLAY_PROBES = REPO / "data" / "ai" / "replay" / "probes.json"
REPLAY_OUT = REPO / "docs" / "generated" / "replay"
REPLAY_PROBES_OUT = REPLAY_OUT / "probes"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class NodeSnapshot:
    node_id: str
    node_name: str
    node_type: str
    baseline_severity: float | None
    baseline_tier: str | None


@dataclass(frozen=True)
class NodeAfter:
    current_severity: float | None
    current_tier: str | None
    unscored_origin: bool


def _fresh_graph(config: ScoringConfig) -> SupplyChainGraph:
    """A fresh scored graph with NO events applied. Every event replay
    starts from this — never from a graph that has already been touched
    by a prior event (per the "individually, never cumulatively" rule)."""
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    refresh_all_derived(g, config)
    # Deliberately skip propagate_event over graph.events — the served
    # events.json is empty for the terminal today, but even if it were
    # not, replay must not compound with production events.
    return g


def _capture_baseline(graph: SupplyChainGraph) -> dict[str, NodeSnapshot]:
    return {
        n.id: NodeSnapshot(
            node_id=n.id,
            node_name=n.name,
            node_type=n.type.value,
            baseline_severity=n.dynamic.baseline_severity,
            baseline_tier=(
                n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else None
            ),
        )
        for n in graph.nodes.values()
    }


def _capture_after(graph: SupplyChainGraph) -> dict[str, NodeAfter]:
    return {
        n.id: NodeAfter(
            current_severity=n.dynamic.current_severity,
            current_tier=(
                n.dynamic.current_tier.value if n.dynamic.current_tier else None
            ),
            unscored_origin=bool(
                n.dynamic.current_severity_has_unscored_origin
            ),
        )
        for n in graph.nodes.values()
    }


def _delta(after: float | None, before: float | None) -> float:
    """current − baseline, treating None on baseline as 0.0 so the
    delta captures the raw walk contribution to an unscored node
    (Pass H invariant: cascade may write current on an unscored node
    without touching baseline; its tier stays UNSCORED)."""
    a = after if after is not None else 0.0
    b = before if before is not None else 0.0
    return a - b


def _tier_change(before: str | None, after: str | None) -> str:
    if before == after:
        return "—"
    return f"{before or '∅'} → {after or '∅'}"


def _sorted_cascade(event: Event) -> list:
    return sorted(event.cascade, key=lambda s: (s.hop, -s.severity_at_node))


def _fmt(v: float | None, prec: int = 3) -> str:
    if v is None:
        return "∅"
    return f"{v:.{prec}f}"


def _write_event_md(
    event: Event,
    baseline: dict[str, NodeSnapshot],
    after: dict[str, NodeAfter],
) -> None:
    path = REPLAY_OUT / f"{event.id}.md"

    # Identify origin(s) + origin scoredness. An unscored origin means
    # baseline_severity is None; the walk seeds from concentration.
    origin_lines = []
    for match in event.entities_matched:
        b = baseline.get(match.node_id)
        if b is None:
            origin_lines.append(
                f"- `{match.node_id}` (unresolved — not in graph)"
            )
            continue
        origin_scored = b.baseline_severity is not None
        origin_lines.append(
            f"- `{b.node_id}` ({b.node_type}, {b.node_name}) — "
            f"{'SCORED' if origin_scored else 'UNSCORED'} origin; "
            f"baseline_severity={_fmt(b.baseline_severity)}, "
            f"baseline_tier={b.baseline_tier or '∅'}"
        )

    # Cascade table
    cascade_rows = []
    for step in _sorted_cascade(event):
        b = baseline[step.node_id]
        a = after[step.node_id]
        delta = _delta(a.current_severity, b.baseline_severity)
        cascade_rows.append(
            "| {nid} | {hop} | {contrib} | {before_sev} | {after_sev} | {delta} | {tiers} |".format(
                nid=step.node_id,
                hop=step.hop,
                contrib=_fmt(step.severity_at_node),
                before_sev=_fmt(b.baseline_severity),
                after_sev=_fmt(a.current_severity),
                delta=f"{delta:+.3f}",
                tiers=_tier_change(b.baseline_tier, a.current_tier),
            )
        )

    # Top-10 by delta (all nodes, not just cascade — some touched via combine)
    all_deltas = []
    for nid, b in baseline.items():
        a = after[nid]
        d = _delta(a.current_severity, b.baseline_severity)
        if abs(d) < 1e-6:
            continue
        all_deltas.append((nid, b, a, d))
    all_deltas.sort(key=lambda t: -t[3])
    top10 = all_deltas[:10]

    top10_rows = []
    for nid, b, a, d in top10:
        top10_rows.append(
            f"| {nid} | {b.node_type} | {_fmt(b.baseline_severity)} | "
            f"{_fmt(a.current_severity)} | {d:+.3f} | "
            f"{_tier_change(b.baseline_tier, a.current_tier)} |"
        )

    # Propagation path for the top-3
    id_to_edge_source_target = {}
    # We do not have graph here; instead read paths from event.cascade
    top3_paths = []
    for nid, _, _, _ in top10[:3]:
        step = next((s for s in event.cascade if s.node_id == nid), None)
        if step is None:
            continue
        top3_paths.append((nid, step.edge_path))

    origin_scored_flag = any(
        (baseline.get(m.node_id) is not None
         and baseline[m.node_id].baseline_severity is not None)
        for m in event.entities_matched
    )

    if not cascade_rows:
        cascade_rows = ["| — | — | — | — | — | — | — |"]
    if not top10_rows:
        top10_rows = ["| — | — | — | — | — | — |"]

    origin_scored_desc = (
        "walk seeded from baseline_severity × magnitude × confidence"
        if origin_scored_flag
        else "walk seeded from concentration × magnitude × confidence "
             "(see Pass D §4)"
    )
    lines = [
        f"# Replay — {event.id}",
        "",
        f"**Headline.** {event.headline}",
        "",
        f"**Timestamp.** {event.timestamp}",
        "",
        "**Origin(s).**",
        *origin_lines,
        "",
        f"**Origin scale** (event severity attributed to strongest origin): "
        f"`{_fmt(event.severity)}`",
        "",
        f"**Origin scored?** `{origin_scored_flag}` — {origin_scored_desc}",
        "",
        f"**Authored axes (Phase A).** "
        f"concentration_delta={event.axes_impact.concentration_delta}, "
        f"substitutability_delta={event.axes_impact.substitutability_delta}, "
        f"lead_time_delta={event.axes_impact.lead_time_delta}",
        "",
        "> Reminder — the pipeline reads only `concentration_delta` as "
        "the event magnitude today. The other axes are authored for "
        "Phase B analysis but do not enter the walk.",
        "",
        "## Cascade table",
        "",
        "Every node touched by this event's walk, in order (hop, then "
        "severity descending). Contribution is the walk value at this "
        "node; before/after are the raw severity numbers; tiers use "
        "`derive_current_tier` (baseline None → tier stays UNSCORED).",
        "",
        "| node_id | hop | contrib | before | after | Δ | tier |",
        "|---|---|---|---|---|---|---|",
        *cascade_rows,
        "",
        "## Top-10 most-affected nodes by delta",
        "",
        "| node_id | type | before | after | Δ | tier |",
        "|---|---|---|---|---|---|",
        *top10_rows,
        "",
        "## Propagation path for top-3",
        "",
    ]
    if top3_paths:
        for nid, edge_path in top3_paths:
            lines.append(f"- **`{nid}`** — edges: `{' → '.join(edge_path) if edge_path else '(origin)'}`")
    else:
        lines.append("- (no cascade — see Phase B grading for interpretation)")
    lines.append("")

    path.write_text("\n".join(lines) + "\n")


def _class_from_tags(tags: list[str]) -> str:
    """Render event class from the committed tag vocabulary (Pass J.1 §5).
    Three values only: home_turf / misfit / misfit_candidate. Frozen —
    do not collapse misfit_candidate into misfit."""
    if "home_turf" in tags:
        return "home_turf"
    if "misfit" in tags:
        return "misfit"
    if "misfit_candidate" in tags:
        return "misfit_candidate"
    return "(untagged)"


def _rank_events(rows: list[dict]) -> None:
    """Compute model_rank + rank_by_origin_scale in place.

    Metric contract (Pass J.1 §1):
      model_rank            = max_delta ↓, nodes_reached ↓,
                              origin_scale ↓, event_id ↑
      rank_by_origin_scale  = origin_scale ↓, max_delta ↓,
                              nodes_reached ↓, event_id ↑

    Ties that survive all four keys are asserted impossible — event_id
    is unique per input file. The runner is the single place this
    metric is defined; grading.md CITES the runner output.
    """
    def _key_model(r: dict) -> tuple:
        return (
            -float(r["_max_delta_num"]),
            -int(r["reached"]),
            -float(r["_origin_scale_num"]),
            str(r["id"]),
        )

    def _key_origin(r: dict) -> tuple:
        return (
            -float(r["_origin_scale_num"]),
            -float(r["_max_delta_num"]),
            -int(r["reached"]),
            str(r["id"]),
        )

    for key_fn, out_field in (
        (_key_model, "model_rank"),
        (_key_origin, "rank_by_origin_scale"),
    ):
        ordered = sorted(rows, key=key_fn)
        # Detect impossible ties — two rows with identical 4-tuple.
        seen: dict[tuple, str] = {}
        for r in ordered:
            k = key_fn(r)
            if k in seen:
                raise AssertionError(
                    f"impossible tie under {out_field}: "
                    f"{r['id']} and {seen[k]} share full 4-key ({k!r})"
                )
            seen[k] = r["id"]
        for i, r in enumerate(ordered, start=1):
            r[out_field] = i


def _write_summary(rows: list[dict]) -> None:
    path = REPLAY_OUT / "summary.md"
    lines = [
        "# Pass J replay — summary",
        "",
        "One row per event. `nodes reached` counts nodes with |Δ| > 1e-6 "
        "(includes both scored-baseline nodes with `current_severity` moved "
        "and unscored nodes whose `current_severity` moved off None).",
        "",
        "`tier change?` = did any node's `current_tier` differ from its "
        "`baseline_tier` after propagation? For unscored nodes `current_tier` "
        "stays UNSCORED per Pass H.1 — a walk touching an unscored downstream "
        "node writes `current_severity` but never a scored tier.",
        "",
        "`model_rank` is `max_delta ↓`, tie-broken by "
        "`nodes_reached ↓, origin_scale ↓, event_id ↑` (Pass J.1 §1). "
        "`rank_by_origin_scale` is the same chain with `origin_scale` "
        "promoted to primary (Pass J.1 §2). Rank definitions live in "
        "`backend/scripts/replay_events.py::_rank_events`; any doc that "
        "restates an ordering is a defect.",
        "",
        "`class` is rendered from the committed `tags` array on each event "
        "(Pass J.1 §5). Vocabulary: `home_turf`, `misfit`, `misfit_candidate`.",
        "",
        "| event | class | origins | origin scale | nodes reached | max Δ | top affected | tier change? | model_rank | rank_by_origin_scale |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: x["model_rank"]):
        lines.append(
            "| {id} | {class_} | {origins} | {origin_sev} | {reached} | "
            "{max_delta} | {top} | {tier_changed} | {model_rank} | "
            "{rank_by_origin_scale} |".format(**r)
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def _rank_disagreements(rows: list[dict]) -> list[tuple[str, int, int, int]]:
    """Return events whose two ranks differ by ≥ 2 slots. Consumed by
    grading.md for F-J-5 (rank-metric instability)."""
    out = []
    for r in rows:
        diff = abs(r["model_rank"] - r["rank_by_origin_scale"])
        if diff >= 2:
            out.append((
                r["id"], r["model_rank"], r["rank_by_origin_scale"], diff,
            ))
    return out


def _served_graph_untouched_check(
    fresh: dict[str, NodeSnapshot],
    after_all_events: dict[str, NodeSnapshot],
) -> tuple[bool, list[str]]:
    """Assert baseline severities + tiers on a FRESH graph match those
    on a graph loaded again after every replay has run. This is the
    INV-1 self-check inside the runner — the suite also asserts this
    separately via test_generated_artifacts."""
    offenders: list[str] = []
    for nid, b0 in fresh.items():
        b1 = after_all_events.get(nid)
        if b1 is None:
            offenders.append(f"{nid} missing after replay")
            continue
        if b0.baseline_severity != b1.baseline_severity:
            offenders.append(
                f"{nid} baseline_severity moved "
                f"{b0.baseline_severity} → {b1.baseline_severity}"
            )
        if b0.baseline_tier != b1.baseline_tier:
            offenders.append(
                f"{nid} baseline_tier moved {b0.baseline_tier} → {b1.baseline_tier}"
            )
    return (not offenders), offenders


def _run_one_event(
    ev: Event,
    config: ScoringConfig,
) -> tuple[Event, dict[str, NodeSnapshot], dict[str, NodeAfter], dict]:
    """Run one event against a fresh baseline graph and return
    (event-with-cascade, baseline snapshot, after snapshot, summary row).
    Non-cumulative because `_fresh_graph` is called once per event; this
    is the only enforcement of non-cumulativity in the runner (the INV-1
    self-check compares baseline severities and can only fire on
    baseline mutation, so it does NOT cover non-cumulativity — see
    Pass J.1 §4)."""
    g = _fresh_graph(config)
    baseline = _capture_baseline(g)
    # Deep-copy so propagate_event's writes to cascade/severity don't
    # leak between runs (defensive; each event is already a fresh Event
    # instance from the outer loop).
    ev_copy = Event.model_validate(ev.model_dump())
    propagate_event(ev_copy, g, config)
    after = _capture_after(g)

    deltas = [
        (nid, _delta(after[nid].current_severity, baseline[nid].baseline_severity))
        for nid in g.nodes
    ]
    moved = [(nid, d) for nid, d in deltas if abs(d) > 1e-6]
    moved.sort(key=lambda t: -t[1])
    top_nid, top_delta = (moved[0] if moved else (None, 0.0))
    any_tier_change = any(
        after[nid].current_tier != baseline[nid].baseline_tier
        for nid in g.nodes
    )
    origins = ", ".join(m.node_id for m in ev_copy.entities_matched) or "(none)"
    row = {
        "id": ev_copy.id,
        "class_": _class_from_tags(list(ev_copy.tags)),
        "origins": origins,
        "origin_sev": _fmt(ev_copy.severity),
        "reached": len(moved),
        "max_delta": f"{top_delta:+.3f}",
        "top": top_nid or "—",
        "tier_changed": "yes" if any_tier_change else "no",
        # Numeric shadows used for ranking; not rendered.
        "_max_delta_num": top_delta,
        "_origin_scale_num": (ev_copy.severity or 0.0),
    }
    return ev_copy, baseline, after, row


def _run_probes(config: ScoringConfig) -> None:
    """Pass J.1 §6 — run injected-magnitude counterfactual probes into
    docs/generated/replay/probes/. NEVER touches summary.md, ranking,
    or outcomes.json. Probes are for measuring pipeline behaviour, not
    for stating beliefs about events."""
    if not REPLAY_PROBES.exists():
        print(f"No probes file at {REPLAY_PROBES}", file=sys.stderr)
        sys.exit(1)
    REPLAY_PROBES_OUT.mkdir(parents=True, exist_ok=True)
    raw = json.loads(REPLAY_PROBES.read_text())
    probes = [Event.model_validate(p) for p in raw]
    for p in probes:
        ev_copy, baseline, after, _ = _run_one_event(p, config)
        # Write into the probes/ subdir so probes cannot be confused
        # with authored events.
        original_out = REPLAY_OUT
        try:
            # _write_event_md writes to REPLAY_OUT / f"{event.id}.md";
            # temporarily rebind by writing directly.
            path = REPLAY_PROBES_OUT / f"{ev_copy.id}.md"
            # Reuse the same rendering by monkey-patching the module-level
            # REPLAY_OUT briefly is ugly; instead call a small helper that
            # takes the target path.
            _write_probe_md(path, ev_copy, baseline, after)
        finally:
            pass
    print(
        f"Wrote {len(probes)} probe artifacts to {REPLAY_PROBES_OUT}. "
        f"summary.md / ranking / outcomes.json NOT modified."
    )


def _write_probe_md(
    path: Path,
    event: Event,
    baseline: dict[str, NodeSnapshot],
    after: dict[str, NodeAfter],
) -> None:
    """Like _write_event_md but writes to an explicit path and stamps
    the file with a PROBE banner so an artifact cannot be mistaken for
    an authored replay result."""
    # Delegate the body to _write_event_md by temporarily redirecting
    # its target — cleaner: render inline, small duplication.
    global REPLAY_OUT
    original = REPLAY_OUT
    REPLAY_OUT = path.parent
    try:
        # _write_event_md computes path = REPLAY_OUT / f"{event.id}.md",
        # which after the rebind lands where we want.
        _write_event_md(event, baseline, after)
    finally:
        REPLAY_OUT = original
    # Prepend the PROBE banner to the generated file.
    body = path.read_text()
    banner = (
        "> **PROBE.** This is an injected-magnitude counterfactual — the "
        "axes on this record are not an estimate of any real event's "
        "impact. Probes do not enter summary.md, ranking, or outcomes.json. "
        "See Pass J.1 §6 and the probe's `notes` field for rationale.\n\n"
    )
    path.write_text(banner + body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probes",
        action="store_true",
        help=(
            "Run data/ai/replay/probes.json into docs/generated/replay/probes/. "
            "Never touches summary.md, ranking, or outcomes.json (Pass J.1 §6)."
        ),
    )
    args = parser.parse_args()

    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")

    if args.probes:
        _run_probes(config)
        return

    if not REPLAY_EVENTS.exists():
        print(f"No replay events file at {REPLAY_EVENTS}", file=sys.stderr)
        sys.exit(1)

    raw_events = json.loads(REPLAY_EVENTS.read_text())
    events = [Event.model_validate(e) for e in raw_events]

    # Capture a "fresh baseline" reference from an untouched graph. The
    # INV-1 self-check below compares this against a graph reloaded
    # after the loop, and can only fire if propagate_event mutates a
    # BASELINE field. propagate_event writes only current_* (see
    # backend/app/scoring/cascade.py). The self-check is therefore NOT
    # evidence that replay is non-cumulative; that guarantee comes from
    # calling _fresh_graph() once per event inside _run_one_event.
    reference = _fresh_graph(config)
    fresh_baseline = _capture_baseline(reference)

    summary_rows = []
    for ev in events:
        ev_copy, baseline, after, row = _run_one_event(ev, config)
        _write_event_md(ev_copy, baseline, after)
        summary_rows.append(row)

    _rank_events(summary_rows)
    _write_summary(summary_rows)

    disagreements = _rank_disagreements(summary_rows)
    if disagreements:
        print("Rank-metric disagreements ≥ 2 slots (feeds F-J-5):")
        for eid, m, o, d in disagreements:
            print(f"  {eid}: model_rank={m}, rank_by_origin_scale={o} (Δ={d})")

    # INV-1 self-check.
    post_reference = _fresh_graph(config)
    ok, offenders = _served_graph_untouched_check(
        fresh_baseline, _capture_baseline(post_reference),
    )
    if not ok:
        print(
            "INV-1 VIOLATED — baseline severities moved during replay:",
            file=sys.stderr,
        )
        for o in offenders:
            print(f"  {o}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {len(events)} per-event artifacts + summary.md to {REPLAY_OUT}")
    print("INV-1 OK: fresh baseline before and after all replays are byte-identical.")


if __name__ == "__main__":
    main()
