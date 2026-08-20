"""Pass X — Country-origin fanout, Phase A: measurement only.

Measures five country-origin scoping candidates (FO-0..FO-3), each under
BOTH MA-0 and MA-1 seeding, through the real engine, in-process. Commits
nothing. No config, edge, node, authored axis, or matched entity changes.

The mechanism (Pass X §0, verified): a `country_region` origin's only
outbound supply edges are `mines`/`refines` into minerals, so an event
matching a country seeds a walk into every mineral that country touches
and everything downstream. `country_region:china` carries 10 such edges;
`china-rees` (a dysprosium licence) therefore lights gallium, neodymium,
indium, and copper as well as dysprosium.

Candidates (hop-0 scoping of a COUNTRY origin's outbound edges)
---------------------------------------------------------------
  FO-0   status quo. No scoping.
  FO-1a  subject scoping, PERMISSIVE fallback. Follow only country edges
         whose target is also in entities_matched; if none, fall back to
         the full unscoped set.
  FO-1b  subject scoping, STRICT fallback. Same, but if no matched entity
         is a valid target the country origin seeds NOTHING (recorded as
         an unscoped-country-origin null).
  FO-2   place-origin suppression. If the event matches >=1 non-country
         entity, drop country origins entirely.
  FO-3   per-edge event scoping via a hypothetical author-named field.
         The field does not exist in the committed corpus; the honest
         authoring is "the subject minerals", i.e. the matched minerals,
         with a strict null when none is named — mechanically identical
         to FO-1b on this corpus (the point of X9).

Seeding (from Pass W, imported so it cannot diverge)
----------------------------------------------------
  MA-0   origin contribution = (baseline | concentration) x magnitude x
         confidence; magnitude = concentration_delta.
  MA-1   origin contribution = perturbation difference (severity'-baseline
         for scored, conc'-conc for unscored) x confidence.

FO-0 + MA-0 is validated node-for-node against the real propagate_event.
"""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "backend" / "scripts"))

from app.graph import SupplyChainGraph
from app.schema import Event
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived
from app.scoring.engine import _outbound_share_for, derive_current_tier

# Reuse Pass W's validated primitives so seeding cannot diverge.
from pass_w_measure import (
    _origin_seed, _cushion, _combine, _perturbed_conc, _node_perturbation,
    _spearman,
)

REPLAY_EVENTS = REPO / "data" / "ai" / "replay" / "events.json"
REPLAY_PROBES = REPO / "data" / "ai" / "replay" / "probes.json"
OUTCOMES = REPO / "data" / "ai" / "replay" / "outcomes.json"

CANDIDATES = ["FO-0", "FO-1a", "FO-1b", "FO-2", "FO-3"]
SEEDINGS = ["MA-0", "MA-1"]


def _is_country(nid: str) -> bool:
    return nid.startswith("country_region:")


def _hop0_edges(candidate, origin, graph, matched_ids):
    """Return (edges_to_follow, scoped_flag) for a COUNTRY origin at hop 0.
    scoped_flag records whether subject scoping actually narrowed the set."""
    all_edges = graph.downstream_supply_edges(origin.id)
    if candidate in ("FO-0", "FO-2"):
        return all_edges, False
    # FO-1a / FO-1b / FO-3 — scope to matched targets.
    scoped = [e for e in all_edges if e.target_id in matched_ids]
    if scoped:
        return scoped, True
    # No matched entity is a valid target — fallback branch.
    if candidate == "FO-1a":
        return all_edges, False            # permissive: unscoped
    return [], True                        # FO-1b / FO-3: strict null


def _propagate(event, graph, config, candidate, seeding):
    decay = config.cascade_decay
    max_hops = config.cascade_max_hops
    share_field = config.cascade_share_field
    fallback = config.cascade_fallback_to_input_share
    combine_method = config.events_combine
    matched_ids = {m.node_id for m in event.entities_matched}
    has_non_country = any(not _is_country(m.node_id) for m in event.entities_matched
                          if m.node_id in graph.nodes)

    best: dict[str, tuple] = {}
    hop0_edge_ids: list[str] = []
    unscoped_country_nulls: list[str] = []

    for match in event.entities_matched:
        origin = graph.nodes.get(match.node_id)
        if origin is None:
            continue
        is_country = _is_country(origin.id)
        # FO-2: drop country origins when a specific entity is present.
        if candidate == "FO-2" and is_country and has_non_country:
            continue

        seed = _origin_seed(seeding, origin, event.axes_impact, match.confidence, config)
        if origin.id not in best or seed > best[origin.id][0]:
            best[origin.id] = (seed, [], 0)

        # Determine which of the origin's own outbound edges to follow.
        if is_country:
            start_edges, scoped = _hop0_edges(candidate, origin, graph, matched_ids)
            if not start_edges and scoped and candidate in ("FO-1b", "FO-3"):
                unscoped_country_nulls.append(origin.id)
        else:
            start_edges = graph.downstream_supply_edges(origin.id)

        # BFS. Expand the origin using `start_edges` (already filtered for a
        # country origin at hop 0); all deeper hops expand normally.
        queue = deque()
        queue.append((origin.id, seed, [], 0, start_edges))
        visited = {origin.id}
        while queue:
            nid, sev, path, hop, edges = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in edges:
                tgt = graph.nodes.get(edge.target_id)
                if tgt is None or edge.target_id in visited:
                    continue
                share = _outbound_share_for(edge, share_field, fallback)
                if share is None:
                    continue
                factor = decay * share * (1.0 - _cushion(tgt))
                downstream = sev * factor
                if downstream <= 1e-6:
                    continue
                if hop == 0:
                    hop0_edge_ids.append(edge.id)
                new_path = path + [edge.id]
                if tgt.id not in best or downstream > best[tgt.id][0]:
                    best[tgt.id] = (downstream, new_path, hop + 1)
                visited.add(tgt.id)
                queue.append((tgt.id, downstream, new_path, hop + 1,
                              graph.downstream_supply_edges(tgt.id)))

    # Apply contributions -> current, exactly like cascade.py.
    results = {}
    max_source = 0.0
    for nid, (contribution, path, hop) in best.items():
        node = graph.nodes[nid]
        base = node.dynamic.baseline_severity
        max_source = max(max_source, contribution)
        if base is None and hop == 0:
            results[nid] = {"current": None, "base": None, "delta": 0.0,
                            "contribution": contribution, "hop": hop}
            continue
        current = base if base is not None else 0.0
        new_current = _combine(current, contribution, combine_method)
        delta = new_current - (base if base is not None else 0.0)
        results[nid] = {"current": new_current, "base": base, "delta": delta,
                        "contribution": contribution, "hop": hop}
    return {"nodes": results, "origin_scale": max_source,
            "hop0_edges": hop0_edge_ids,
            "unscoped_country_nulls": unscoped_country_nulls}


SUBJECT_MINERAL = {  # the event's named subject mineral (for the subject binary)
    "J-2025-04-china-rees": "mineral:dysprosium",
    "J-2024-12-china-gallium": "mineral:gallium",
}


def _downstream_of(graph, root, target):
    """True if `target` is reachable downstream of `root` via supply edges."""
    seen = {root}
    q = deque([root])
    while q:
        nid = q.popleft()
        for e in graph.downstream_supply_edges(nid):
            if e.target_id == target:
                return True
            if e.target_id not in seen:
                seen.add(e.target_id)
                q.append(e.target_id)
    return False


def _metrics(event, graph, config, candidate, seeding):
    prop = _propagate(event, graph, config, candidate, seeding)
    nodes = prop["nodes"]
    moved = [(nid, r["delta"]) for nid, r in nodes.items() if abs(r["delta"]) > 1e-6]
    moved.sort(key=lambda t: -t[1])
    top_nid, top_delta = (moved[0] if moved else (None, 0.0))
    top5 = [{"node": nid, "delta": d} for nid, d in moved[:5]]
    tier_changes = 0
    for nid, r in nodes.items():
        if r["base"] is None or r["current"] is None:
            continue
        if derive_current_tier(r["base"], r["base"], config) != \
           derive_current_tier(r["base"], r["current"], config):
            tier_changes += 1
    subj = SUBJECT_MINERAL.get(event.id)
    if subj is None or top_nid is None:
        subject_binary = None
    else:
        subject_binary = (top_nid == subj) or _downstream_of(graph, subj, top_nid)
    return {
        "id": event.id, "seeding": seeding, "candidate": candidate,
        "hop0_edges": prop["hop0_edges"], "n_hop0_edges": len(prop["hop0_edges"]),
        "nodes_reached": len(moved), "max_delta": top_delta,
        "max_delta_node": top_nid, "top5": top5, "tier_changes": tier_changes,
        "origin_scale": prop["origin_scale"],
        "subject": subj, "subject_binary_is_subject_or_downstream": subject_binary,
        "unscoped_country_nulls": prop["unscoped_country_nulls"],
    }


def _rank(rows):
    ordered = sorted(rows, key=lambda r: (
        -r["max_delta"], -r["nodes_reached"], -r["origin_scale"], r["id"]))
    for i, r in enumerate(ordered, 1):
        r["model_rank"] = i


def _fresh(config):
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    refresh_all_derived(g, config)
    return g


def _validate_fo0_ma0(events, config):
    def _delta(cur, base):
        c = cur if cur is not None else (base if base is not None else 0.0)
        return c - (base if base is not None else 0.0)
    mism = []
    for ev in events:
        g = _fresh(config)
        ev_copy = Event.model_validate(ev.model_dump())
        propagate_event(ev_copy, g, config)
        real = {n.id: _delta(n.dynamic.current_severity, n.dynamic.baseline_severity)
                for n in g.nodes.values()}
        g2 = _fresh(config)
        prop = _propagate(ev_copy, g2, config, "FO-0", "MA-0")
        mine = {nid: r["delta"] for nid, r in prop["nodes"].items()}
        for nid in set(real) | set(mine):
            if abs(real.get(nid, 0.0) - mine.get(nid, 0.0)) > 1e-12:
                mism.append((ev.id, nid, real.get(nid), mine.get(nid)))
    return mism


def main():
    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e) for e in json.loads(REPLAY_EVENTS.read_text())]
    probes = [Event.model_validate(p) for p in json.loads(REPLAY_PROBES.read_text())]
    outcomes = {o["id"]: o["magnitude_ordinal"]
                for o in json.loads(OUTCOMES.read_text())["outcomes"]}

    validation = _validate_fo0_ma0(events, config)

    # events x candidate x seeding
    matrix = {}
    spearman = {}
    displacement = {}
    for seeding in SEEDINGS:
        for cand in CANDIDATES:
            rows = []
            for ev in events:
                rows.append(_metrics(ev, _fresh(config), config, cand, seeding))
            _rank(rows)
            matrix[f"{cand}|{seeding}"] = rows
            mr = {r["id"]: r["model_rank"] for r in rows}
            spearman[f"{cand}|{seeding}"] = _spearman(mr, outcomes)
            displacement[f"{cand}|{seeding}"] = {
                r["id"]: mr[r["id"]] - outcomes[r["id"]] for r in rows}

    # probes x candidate x seeding
    probe_matrix = {}
    for seeding in SEEDINGS:
        for cand in CANDIDATES:
            for p in probes:
                m = _metrics(p, _fresh(config), config, cand, seeding)
                probe_matrix[f"{p.id}|{cand}|{seeding}"] = {
                    k: v for k, v in m.items() if k != "model_rank"}

    # §1 / X7 — unscored-origin seeding under MA-0 and MA-1.
    unscored_seeding = []
    for ev in events:
        g = _fresh(config)
        for m in ev.entities_matched:
            node = g.nodes.get(m.node_id)
            if node is None or node.dynamic.baseline_severity is not None:
                continue  # only unscored origins
            conc = node.dynamic.concentration or 0.0
            ax = ev.axes_impact
            mag = max(0.0, min(1.0, ax.concentration_delta))
            ma0 = conc * mag * m.confidence
            cp = _perturbed_conc(conc, ax.concentration_delta, False)
            ma1 = (cp - conc) * m.confidence
            unscored_seeding.append({
                "event": ev.id, "origin": m.node_id, "concentration": conc,
                "confidence": m.confidence, "concentration_delta": ax.concentration_delta,
                "ma0_seed": ma0, "ma0_formula": "concentration x concentration_delta x confidence",
                "ma1_seed": ma1, "ma1_formula": "(conc' - conc) x confidence  [a concentration difference]",
            })

    facts = {
        "candidates": CANDIDATES, "seedings": SEEDINGS,
        "fo0_ma0_validation_mismatches": validation,
        "observed_ordinal": outcomes,
        "matrix": matrix, "spearman": spearman, "rank_displacement": displacement,
        "probe_matrix": probe_matrix,
        "unscored_origin_seeding": unscored_seeding,
    }
    (REPO / "docs" / "generated" / "pass_x_facts.json").write_text(
        json.dumps(facts, indent=2, default=str) + "\n")
    print("wrote pass_x_facts.json")
    print("FO-0+MA-0 validation mismatches:", len(validation))
    _write_markdown(matrix, spearman, probe_matrix, outcomes, facts)


def _write_markdown(matrix, spearman, probe_matrix, outcomes, facts):
    short = {"J-2024-04-taiwan-quake": "taiwan", "J-2024-09-asml-export": "asml",
             "J-2024-10-kachin-kia": "kachin", "J-2024-11-hynix-hbm": "HBM",
             "J-2024-12-china-gallium": "gallium", "J-2025-04-china-rees": "china-rees",
             "J-2025-10-nexperia": "nexperia"}
    L = ["# Country-origin fanout candidates — Pass X (measurement only)", "",
         "_Generated by `backend/scripts/pass_x_measure.py`. In-process; nothing "
         "committed. FO-0+MA-0 validated vs real engine: "
         f"**{len(facts['fo0_ma0_validation_mismatches'])} mismatches**._", ""]
    for seeding in SEEDINGS:
        L.append(f"## Seeding: {seeding}")
        L.append("")
        for cand in CANDIDATES:
            rows = sorted(matrix[f"{cand}|{seeding}"], key=lambda r: r["model_rank"])
            L.append(f"### {cand} + {seeding}  (ρ={spearman[f'{cand}|{seeding}']:+.4f})")
            L.append("")
            L.append("| rank | event | hop0 edges | reached | max Δ | max Δ node | "
                     "subject? | tier chg | observed |")
            L.append("|---:|---|---:|---:|---:|---|:--:|---:|---:|")
            for r in rows:
                sb = r["subject_binary_is_subject_or_downstream"]
                sbs = "—" if sb is None else ("yes" if sb else "NO")
                L.append(f"| {r['model_rank']} | {short[r['id']]} | {r['n_hop0_edges']} | "
                         f"{r['nodes_reached']} | {r['max_delta']:.6f} | "
                         f"{r['max_delta_node']} | {sbs} | {r['tier_changes']} | "
                         f"{outcomes[r['id']]} |")
            L.append("")
    (REPO / "docs" / "generated" / "fanout_candidates.md").write_text("\n".join(L) + "\n")
    print("wrote fanout_candidates.md")


if __name__ == "__main__":
    main()
