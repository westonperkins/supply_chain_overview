"""Pass W — Multi-axis event intake, Phase A: measurement only.

Drives five candidate designs (MA-0..MA-3) for reading an event's
`AxesImpact` through the REAL scoring engine, in-process, and reports.
NOTHING is committed to scoring; no config or authored axis is edited.

Candidates
----------
  MA-0  status quo. magnitude = concentration_delta; origin contribution
        = (baseline | concentration) x magnitude x confidence; scalar
        walk downstream.
  MA-1  axis perturbation at origin, scalar propagation. At the origin,
        recompute severity under perturbed axes and take the DIFFERENCE
        from baseline as the contribution; propagate that scalar.
  MA-1b MA-1 with headroom-relative concentration:
        conc' = conc + concentration_delta * (1 - conc).
  MA-2  MA-1 origin, but every downstream node is ALSO re-scored under
        the event's axis deltas applied to ITS OWN axes, attenuated by
        the max-path walk factor. Measured to be rejected on evidence.
  MA-3  combined scalar magnitude: widen only _event_magnitude to
        noisy_or(concentration_delta, |sub_delta|, norm(lt_delta)).

Conventions resolved before any candidate runs (Pass W §2)
----------------------------------------------------------
  * Substitutability sign: RISK-POSITIVE. A positive substitutability_delta
    means the event makes substitution HARDER (more risk), matching the
    AxesImpact docstring and all seven authored events. Since the engine's
    `axes_for_severity` computes `sub_base + sub_delta`, risk-positive is
    applied by passing `-substitutability_delta` to it, so the used
    substitutability falls and (1 - sub) rises. (§0.2)
  * lead_time_delta unit: YEARS. `axes_for_severity` does
    `lt_base_years + lt_delta`; checked coherent against all seven events. (§0.3)

The MA-0 path here is validated to reproduce the real engine's
`propagate_event` node-for-node before any candidate is trusted.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.schema import AxesImpact, Event
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived
from app.scoring.engine import (
    axes_for_severity,
    compute_severity,
    derive_current_tier,
    normalize_lead_time,
    _outbound_share_for,
    _sourced_number,
)
from app.schema.node import NodeType

REPLAY_EVENTS = REPO / "data" / "ai" / "replay" / "events.json"
OUTCOMES = REPO / "data" / "ai" / "replay" / "outcomes.json"

CANDIDATES = ["MA-0", "MA-1", "MA-1b", "MA-2", "MA-3"]
SIGN_CONVENTION = "risk_positive"
LEAD_TIME_UNIT = "years"


# --------------------------------------------------------------------------- #
# Engine-faithful helpers (mirror cascade.py exactly).                          #
# --------------------------------------------------------------------------- #

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _cushion(node) -> float:
    if node.type != NodeType.COMPANY:
        return 0.0
    return _sourced_number(node.static.financial_cushion, default=0.0)


def _combine(current: float, contribution: float, method: str) -> float:
    c = _clamp01(contribution)
    if method == "noisy_or":
        return 1.0 - (1.0 - current) * (1.0 - c)
    if method == "max":
        return max(current, c)
    if method == "add_clamp":
        return min(1.0, current + c)
    raise ValueError(method)


def _noisy_or_scalar(vals: list[float]) -> float:
    acc = 0.0
    for v in vals:
        acc = 1.0 - (1.0 - acc) * (1.0 - _clamp01(v))
    return acc


# --------------------------------------------------------------------------- #
# Perturbation primitives.                                                      #
# --------------------------------------------------------------------------- #

def _perturbed_conc(conc: float, cd: float, headroom: bool) -> float:
    cp = conc + cd * (1.0 - conc) if headroom else conc + cd
    return _clamp01(cp)


def _perturbed_severity(node, config, cd, sd, ld, headroom):
    """Return (severity_or_None, conc_prime). Risk-positive: subtract sd."""
    conc = node.dynamic.concentration or 0.0
    cp = _perturbed_conc(conc, cd, headroom)
    sub, lt_norm, _ = axes_for_severity(node, config, sub_delta=-sd, lt_delta=ld)
    if sub is None or lt_norm is None:
        return None, cp
    return compute_severity(cp, sub, lt_norm, config), cp


def _node_perturbation(node, config, cd, sd, ld, headroom):
    """The event-effect at a single node: (perturbed - baseline) for a
    scored node, or (conc' - conc) for an unscored one. Used as the origin
    seed (MA-1/1b) and as the per-node re-score (MA-2)."""
    conc = node.dynamic.concentration or 0.0
    base = node.dynamic.baseline_severity
    sevp, cp = _perturbed_severity(node, config, cd, sd, ld, headroom)
    if base is not None and sevp is not None:
        return sevp - base
    return cp - conc


def _origin_seed(candidate, origin, axes: AxesImpact, conf, config):
    conc = origin.dynamic.concentration or 0.0
    base = origin.dynamic.baseline_severity
    cd, sd, ld = (axes.concentration_delta, axes.substitutability_delta,
                  axes.lead_time_delta)
    if candidate == "MA-0":
        mag = _clamp01(cd)
        return (base if base is not None else conc) * mag * conf
    if candidate == "MA-3":
        lt_norm_delta = normalize_lead_time(max(0.0, ld), config.lead_time_normalization)
        mag = _noisy_or_scalar([_clamp01(cd), _clamp01(abs(sd)), lt_norm_delta])
        return (base if base is not None else conc) * mag * conf
    # MA-1 / MA-1b / MA-2 origin: perturbation difference.
    headroom = candidate == "MA-1b"
    return _node_perturbation(origin, config, cd, sd, ld, headroom) * conf


# --------------------------------------------------------------------------- #
# Propagation (faithful copy of cascade.propagate_event's BFS), parametrized   #
# by candidate seed. MA-2 additionally re-scores downstream nodes.              #
# --------------------------------------------------------------------------- #

def _propagate(event: Event, graph: SupplyChainGraph, config: ScoringConfig,
               candidate: str) -> dict:
    decay = config.cascade_decay
    max_hops = config.cascade_max_hops
    share_field = config.cascade_share_field
    fallback = config.cascade_fallback_to_input_share
    combine_method = config.events_combine
    axes = event.axes_impact
    cd, sd, ld = axes.concentration_delta, axes.substitutability_delta, axes.lead_time_delta
    headroom = candidate == "MA-1b"

    # best_contribution[node] = (contribution, path, hop)
    best: dict[str, tuple[float, list, int]] = {}
    # best_atten[node] = max path attenuation from any origin (MA-2).
    best_atten: dict[str, float] = {}

    for match in event.entities_matched:
        origin = graph.nodes.get(match.node_id)
        if origin is None:
            continue
        seed = _origin_seed(candidate, origin, axes, match.confidence, config)

        # Origin record.
        if origin.id not in best or seed > best[origin.id][0]:
            best[origin.id] = (seed, [], 0)
        if origin.id not in best_atten or 1.0 > best_atten[origin.id]:
            best_atten[origin.id] = 1.0

        # BFS downstream: scalar `sev` propagates to reach nodes; `atten`
        # tracks the product of decay*share*(1-cushion) (for MA-2).
        queue = deque()
        queue.append((origin.id, seed, 1.0, [], 0))
        visited = {origin.id}
        while queue:
            nid, sev, atten, path, hop = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in graph.downstream_supply_edges(nid):
                tgt = graph.nodes.get(edge.target_id)
                if tgt is None or edge.target_id in visited:
                    continue
                share = _outbound_share_for(edge, share_field, fallback)
                if share is None:
                    continue
                factor = decay * share * (1.0 - _cushion(tgt))
                downstream = sev * factor
                atten_child = atten * factor
                if downstream <= 1e-6:
                    continue
                new_path = path + [edge.id]
                if tgt.id not in best or downstream > best[tgt.id][0]:
                    best[tgt.id] = (downstream, new_path, hop + 1)
                if tgt.id not in best_atten or atten_child > best_atten[tgt.id]:
                    best_atten[tgt.id] = atten_child
                visited.add(tgt.id)
                queue.append((tgt.id, downstream, atten_child, new_path, hop + 1))

    # MA-2: replace each node's contribution with (its own re-score) x
    # (best attenuation to it). Origins keep their own perturbation seed.
    if candidate == "MA-2":
        for nid in list(best):
            node = graph.nodes[nid]
            pert = _node_perturbation(node, config, cd, sd, ld, headroom)
            atten = best_atten.get(nid, 0.0)
            contribution = pert * atten
            _, path, hop = best[nid]
            best[nid] = (contribution, path, hop)

    # Apply contributions -> current_severity, exactly like cascade.py.
    results = {}
    max_source = 0.0
    for nid, (contribution, path, hop) in best.items():
        node = graph.nodes[nid]
        base = node.dynamic.baseline_severity
        max_source = max(max_source, contribution)
        is_origin = hop == 0
        if base is None and is_origin:
            results[nid] = {"current": None, "base": None, "delta": 0.0,
                            "contribution": contribution, "hop": hop}
            continue
        if base is None:
            current = 0.0
        else:
            current = base
        new_current = _combine(current, contribution, combine_method)
        delta = new_current - (base if base is not None else 0.0)
        results[nid] = {"current": new_current, "base": base, "delta": delta,
                        "contribution": contribution, "hop": hop}
    return {"nodes": results, "origin_scale": max_source}


# --------------------------------------------------------------------------- #
# Per-event / per-candidate metrics + ranking.                                  #
# --------------------------------------------------------------------------- #

def _event_metrics(event, graph, config, candidate) -> dict:
    prop = _propagate(event, graph, config, candidate)
    nodes = prop["nodes"]
    moved = [(nid, r["delta"]) for nid, r in nodes.items() if abs(r["delta"]) > 1e-6]
    moved.sort(key=lambda t: -t[1])
    top_nid, top_delta = (moved[0] if moved else (None, 0.0))
    tier_changes = 0
    for nid, r in nodes.items():
        if r["base"] is None or r["current"] is None:
            continue
        bt = derive_current_tier(r["base"], r["base"], config)
        ct = derive_current_tier(r["base"], r["current"], config)
        if bt != ct:
            tier_changes += 1
    # origin contribution = max contribution among matched origins (hop 0)
    origin_contrib = max(
        (nodes[m.node_id]["contribution"]
         for m in event.entities_matched if m.node_id in nodes),
        default=0.0,
    )
    return {
        "id": event.id,
        "origin_contribution": origin_contrib,
        "nodes_reached": len(moved),
        "max_delta": top_delta,
        "max_delta_node": top_nid,
        "tier_changes": tier_changes,
        "origin_scale": prop["origin_scale"],
        "nodes": nodes,
    }


def _rank(rows: list[dict]) -> None:
    """model_rank = max_delta desc, tie (nodes_reached desc, origin_scale
    desc, id asc) — identical to replay_events._rank_events."""
    ordered = sorted(rows, key=lambda r: (
        -r["max_delta"], -r["nodes_reached"], -r["origin_scale"], r["id"]))
    for i, r in enumerate(ordered, 1):
        r["model_rank"] = i


def _spearman(rank_a: dict, rank_b: dict) -> float:
    ids = sorted(set(rank_a) & set(rank_b))
    n = len(ids)
    d2 = sum((rank_a[i] - rank_b[i]) ** 2 for i in ids)
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def _validate_ma0(events, config):
    """MA-0 through this harness must match the real engine node-for-node.

    Compared on the DELTA (current - baseline), not absolute current: the
    real engine initializes every scored node's current_severity to its
    baseline (so an untouched node reads current==baseline, delta 0),
    whereas this harness records only moved nodes. Comparing deltas makes
    an untouched node read 0 on both sides."""
    def _delta(current, base):
        c = current if current is not None else (base if base is not None else 0.0)
        b = base if base is not None else 0.0
        return c - b

    mism = []
    for ev in events:
        g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
        refresh_all_derived(g, config)
        ev_copy = Event.model_validate(ev.model_dump())
        propagate_event(ev_copy, g, config)
        real = {n.id: _delta(n.dynamic.current_severity, n.dynamic.baseline_severity)
                for n in g.nodes.values()}
        g2 = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
        refresh_all_derived(g2, config)
        prop = _propagate(ev_copy, g2, config, "MA-0")
        mine = {nid: r["delta"] for nid, r in prop["nodes"].items()}
        for nid in set(real) | set(mine):
            a, b = real.get(nid, 0.0), mine.get(nid, 0.0)
            if abs(a - b) > 1e-12:
                mism.append((ev.id, nid, a, b))
    return mism


def main() -> None:
    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e) for e in json.loads(REPLAY_EVENTS.read_text())]
    outcomes = {o["id"]: o["magnitude_ordinal"]
                for o in json.loads(OUTCOMES.read_text())["outcomes"]}

    validation_mismatches = _validate_ma0(events, config)

    per_candidate = {}
    for cand in CANDIDATES:
        rows = []
        for ev in events:
            g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
            refresh_all_derived(g, config)
            rows.append(_event_metrics(ev, g, config, cand))
        _rank(rows)
        per_candidate[cand] = rows

    # Spearman vs observed ordinal.
    observed_rank = dict(outcomes)  # ordinal 1..7, 1 = biggest
    spearman = {}
    displacement = {}
    for cand, rows in per_candidate.items():
        model_rank = {r["id"]: r["model_rank"] for r in rows}
        spearman[cand] = _spearman(model_rank, observed_rank)
        displacement[cand] = {
            r["id"]: model_rank[r["id"]] - observed_rank[r["id"]] for r in rows}

    # Saturation table (per event, origins only).
    saturation = []
    for ev in events:
        g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
        refresh_all_derived(g, config)
        ax = ev.axes_impact
        for m in ev.entities_matched:
            node = g.nodes.get(m.node_id)
            if node is None:
                continue
            conc = node.dynamic.concentration or 0.0
            cp_flat = _perturbed_conc(conc, ax.concentration_delta, False)
            cp_head = _perturbed_conc(conc, ax.concentration_delta, True)
            saturation.append({
                "event": ev.id, "node": m.node_id,
                "concentration": conc, "concentration_delta": ax.concentration_delta,
                "conc_after_flat": cp_flat,
                "effective_move_flat": cp_flat - conc,
                "lost_to_clamp_flat": max(0.0, (conc + ax.concentration_delta) - 1.0),
                "conc_after_headroom": cp_head,
                "effective_move_headroom": cp_head - conc,
            })

    facts = {
        "conventions": {"substitutability_sign": SIGN_CONVENTION,
                        "lead_time_delta_unit": LEAD_TIME_UNIT},
        "ma0_validation_mismatches": validation_mismatches,
        "observed_ordinal": outcomes,
        "candidates": {
            cand: [{k: v for k, v in r.items() if k != "nodes"} for r in rows]
            for cand, rows in per_candidate.items()
        },
        "spearman": spearman,
        "rank_displacement": displacement,
        "saturation": saturation,
        # HBM traced under every candidate (origins detail).
        "hbm_trace": {
            cand: next(
                ({"event": r["id"], "origin_contribution": r["origin_contribution"],
                  "max_delta": r["max_delta"], "max_delta_node": r["max_delta_node"],
                  "nodes_reached": r["nodes_reached"], "model_rank": r["model_rank"],
                  "origins": {
                      m.node_id: r["nodes"].get(m.node_id, {}).get("contribution")
                      for e in events if e.id == "J-2024-11-hynix-hbm"
                      for m in e.entities_matched}}
                 for r in rows if r["id"] == "J-2024-11-hynix-hbm"), None)
            for cand, rows in per_candidate.items()
        },
    }
    (REPO / "docs" / "generated" / "pass_w_facts.json").write_text(
        json.dumps(facts, indent=2, default=str) + "\n")
    print("wrote pass_w_facts.json")
    print("MA-0 validation mismatches:", len(validation_mismatches))
    for cand in CANDIDATES:
        ranks = {r["id"]: r["model_rank"] for r in per_candidate[cand]}
        hbm = ranks["J-2024-11-hynix-hbm"]
        print(f"  {cand}: rho={spearman[cand]:+.4f}  HBM_rank={hbm}")
    _write_markdown(per_candidate, spearman, displacement, outcomes, facts)


def _write_markdown(per_candidate, spearman, displacement, outcomes, facts):
    L = ["# Multi-axis candidate comparison — Pass W (measurement only)", "",
         "_Generated by `backend/scripts/pass_w_measure.py`. In-process; "
         "nothing committed to scoring. Substitutability sign: risk-positive. "
         "lead_time_delta unit: years._", ""]
    L.append(f"MA-0 harness validation vs real engine: "
             f"**{len(facts['ma0_validation_mismatches'])} mismatches** "
             f"(0 = harness faithful).")
    L.append("")
    L.append("## Observed ordinal (outcomes.json, 1 = biggest observed)")
    L.append("")
    L.append("| event | observed ordinal |")
    L.append("|---|---|")
    for eid, o in sorted(outcomes.items(), key=lambda kv: kv[1]):
        L.append(f"| {eid} | {o} |")
    L.append("")
    for cand in CANDIDATES:
        rows = sorted(per_candidate[cand], key=lambda r: r["model_rank"])
        L.append(f"## {cand}  (Spearman ρ vs observed = {spearman[cand]:+.4f})")
        L.append("")
        L.append("| event | origin contrib | nodes reached | max Δ | max Δ node | "
                 "tier chg | model_rank | observed | displacement |")
        L.append("|---|---:|---:|---:|---|---:|---:|---:|---:|")
        for r in rows:
            disp = displacement[cand][r["id"]]
            L.append(f"| {r['id']} | {r['origin_contribution']:.6f} | "
                     f"{r['nodes_reached']} | {r['max_delta']:.6f} | "
                     f"{r['max_delta_node']} | {r['tier_changes']} | "
                     f"{r['model_rank']} | {outcomes[r['id']]} | {disp:+d} |")
        L.append("")
    (REPO / "docs" / "generated" / "multi_axis_candidates.md").write_text("\n".join(L) + "\n")
    print("wrote multi_axis_candidates.md")


if __name__ == "__main__":
    main()
