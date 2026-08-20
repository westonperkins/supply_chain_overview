"""Pass Y — Cascade walk semantics (CW-0/CW-2/CW-1) and fanout FO-1c.

Measurement only; ships nothing. Drives three cascade-walk semantics and
four fanout candidates through the real engine primitives, in-process.
No config, edge, node, authored axis, matched entity, or cascade.py is
edited. Committed severities/tiers stay byte-identical.

Cascade semantics
-----------------
  CW-0  current committed. First-encounter-wins: a per-origin `visited`
        set is marked on first arrival and never cleared, so within one
        origin's walk the first path to a node wins and later/stronger
        arrivals are discarded before their value is computed. This is a
        faithful copy of cascade.propagate_event, validated node-for-node.
  CW-2  parallel-edge fix only. Before expanding a node, collapse its
        outbound supply edges so each distinct target keeps only its
        greatest-resolved-share edge (tie -> edge id asc, ties reported).
        Visited set otherwise unchanged — longer-path suppression remains.
  CW-1  full max-of-paths (engine semantics). No visited set; update a
        node only on strict improvement and re-enqueue only when improved;
        bounded by max_hops. The one supply-edge cycle (arm<->arm_core_ip)
        terminates because decay*share<1 and the 1e-6 floor.

Fanout (hop-0 scoping of a COUNTRY origin's outbound edges)
----------------------------------------------------------
  FO-0   no scoping.
  FO-1a  subject scoping, permissive fallback (unscoped when no subject).
  FO-1b  subject scoping, strict fallback (null when no subject).
  FO-1c  FO-1b, but the strict fallback fires only when the country origin
         has MORE THAN ONE distinct outbound target; single/zero-target
         countries seed normally (Y11 fixes the rule text).

Seeding (MA-0, MA-1) imported from Pass W so it cannot diverge.
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
from app.schema.enums import SUPPLY_EDGE_TYPES
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived
from app.scoring.engine import _outbound_share_for, derive_current_tier

from pass_w_measure import _origin_seed, _cushion, _combine, _spearman

REPLAY_EVENTS = REPO / "data" / "ai" / "replay" / "events.json"
REPLAY_PROBES = REPO / "data" / "ai" / "replay" / "probes.json"
OUTCOMES = REPO / "data" / "ai" / "replay" / "outcomes.json"

CASCADES = ["CW-0", "CW-2", "CW-1"]
FANOUTS = ["FO-0", "FO-1a", "FO-1b", "FO-1c"]

SUBJECT_MINERAL = {
    "J-2025-04-china-rees": "mineral:dysprosium",
    "J-2024-12-china-gallium": "mineral:gallium",
}


def _is_country(nid: str) -> bool:
    return nid.startswith("country_region:")


def _share(edge, config):
    return _outbound_share_for(edge, config.cascade_share_field,
                               config.cascade_fallback_to_input_share)


def _collapse_parallel(edges, config):
    """CW-2: keep, per distinct target, the edge with the greatest resolved
    share. Tie -> edge id ascending (reported)."""
    by_t = {}
    ties = []
    for e in edges:
        s = _share(e, config)
        if s is None:
            continue
        if e.target_id not in by_t:
            by_t[e.target_id] = e
        else:
            cur = by_t[e.target_id]
            cs = _share(cur, config)
            if s > cs:
                by_t[e.target_id] = e
            elif s == cs:
                keep = min((cur, e), key=lambda x: x.id)
                ties.append({"target": e.target_id,
                             "edges": sorted([cur.id, e.id]), "share": s,
                             "kept": keep.id})
                by_t[e.target_id] = keep
    return list(by_t.values()), ties


def _country_targets(origin, graph):
    return {e.target_id for e in graph.downstream_supply_edges(origin.id)}


def _hop0_edges(fo, origin, graph, matched_ids):
    """(edges_to_follow, scoped, nulled) for a COUNTRY origin at hop 0."""
    all_edges = graph.downstream_supply_edges(origin.id)
    if fo == "FO-0":
        return all_edges, False, False
    if fo == "FO-1c" and len(_country_targets(origin, graph)) <= 1:
        # Single- or zero-target country: no fanout to prevent; seed normally.
        return all_edges, False, False
    scoped = [e for e in all_edges if e.target_id in matched_ids]
    if scoped:
        return scoped, True, False
    if fo == "FO-1a":
        return all_edges, False, False        # permissive fallback
    return [], True, True                     # FO-1b / FO-1c strict null


def _walk_visited(graph, config, mode, best, origin_id, seed, start_edges, ties):
    decay, max_hops = config.cascade_decay, config.cascade_max_hops
    q = deque([(origin_id, seed, [], 0, start_edges)])
    visited = {origin_id}
    while q:
        nid, sev, path, hop, edges = q.popleft()
        if hop >= max_hops:
            continue
        if mode == "CW-2":
            edges, t = _collapse_parallel(edges, config)
            ties.extend(t)
        for e in edges:
            tgt = graph.nodes.get(e.target_id)
            if tgt is None or e.target_id in visited:
                continue
            s = _share(e, config)
            if s is None:
                continue
            down = sev * decay * s * (1.0 - _cushion(tgt))
            if down <= 1e-6:
                continue
            npath = path + [e.id]
            if tgt.id not in best or down > best[tgt.id][0]:
                best[tgt.id] = (down, npath, hop + 1)
            visited.add(tgt.id)
            q.append((tgt.id, down, npath, hop + 1,
                      graph.downstream_supply_edges(tgt.id)))


def _walk_maxpath(graph, config, best, origin_id, seed, start_edges):
    decay, max_hops = config.cascade_decay, config.cascade_max_hops
    q = deque([(origin_id, seed, [], 0, start_edges)])
    while q:
        nid, sev, path, hop, edges = q.popleft()
        if hop >= max_hops:
            continue
        for e in edges:
            tgt = graph.nodes.get(e.target_id)
            if tgt is None:
                continue
            s = _share(e, config)
            if s is None:
                continue
            down = sev * decay * s * (1.0 - _cushion(tgt))
            if down <= 1e-6:
                continue
            npath = path + [e.id]
            if tgt.id not in best or down > best[tgt.id][0]:
                best[tgt.id] = (down, npath, hop + 1)
                q.append((tgt.id, down, npath, hop + 1,
                          graph.downstream_supply_edges(tgt.id)))


def _propagate(event, graph, config, cascade_mode, fo, seeding):
    matched_ids = {m.node_id for m in event.entities_matched}
    best = {}
    nulls = []
    ties = []
    for match in event.entities_matched:
        origin = graph.nodes.get(match.node_id)
        if origin is None:
            continue
        seed = _origin_seed(seeding, origin, event.axes_impact, match.confidence, config)
        if origin.id not in best or seed > best[origin.id][0]:
            best[origin.id] = (seed, [], 0)
        if _is_country(origin.id):
            start_edges, scoped, nulled = _hop0_edges(fo, origin, graph, matched_ids)
            if nulled:
                nulls.append(origin.id)
        else:
            start_edges = graph.downstream_supply_edges(origin.id)
        if cascade_mode in ("CW-0", "CW-2"):
            _walk_visited(graph, config, cascade_mode, best, origin.id, seed, start_edges, ties)
        else:
            _walk_maxpath(graph, config, best, origin.id, seed, start_edges)

    combine = config.events_combine
    results = {}
    max_source = 0.0
    for nid, (contribution, path, hop) in best.items():
        node = graph.nodes[nid]
        base = node.dynamic.baseline_severity
        max_source = max(max_source, contribution)
        if base is None and hop == 0:
            results[nid] = {"current": None, "base": None, "delta": 0.0,
                            "contribution": contribution, "hop": hop, "path": path}
            continue
        current = base if base is not None else 0.0
        new_current = _combine(current, contribution, combine)
        delta = new_current - (base if base is not None else 0.0)
        results[nid] = {"current": new_current, "base": base, "delta": delta,
                        "contribution": contribution, "hop": hop, "path": path}
    return {"nodes": results, "origin_scale": max_source,
            "nulls": nulls, "ties": ties}


def _downstream_of(graph, root, target):
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


def _metrics(event, graph, config, cascade_mode, fo, seeding):
    prop = _propagate(event, graph, config, cascade_mode, fo, seeding)
    nodes = prop["nodes"]
    moved = [(nid, r["delta"]) for nid, r in nodes.items() if abs(r["delta"]) > 1e-6]
    moved.sort(key=lambda t: -t[1])
    top_nid, top_delta = (moved[0] if moved else (None, 0.0))
    tier_changes = 0
    for nid, r in nodes.items():
        if r["base"] is None or r["current"] is None:
            continue
        if derive_current_tier(r["base"], r["base"], config) != \
           derive_current_tier(r["base"], r["current"], config):
            tier_changes += 1
    subj = SUBJECT_MINERAL.get(event.id)
    if subj is None or top_nid is None:
        subj_bin = None
    else:
        subj_bin = (top_nid == subj) or _downstream_of(graph, subj, top_nid)
    origin_contrib = max((nodes[m.node_id]["contribution"]
                          for m in event.entities_matched if m.node_id in nodes),
                         default=0.0)
    return {
        "id": event.id, "cascade": cascade_mode, "fo": fo, "seeding": seeding,
        "nodes_reached": len(moved), "max_delta": top_delta,
        "max_delta_node": top_nid,
        "top5": [{"node": nid, "delta": d} for nid, d in moved[:5]],
        "tier_changes": tier_changes, "origin_scale": prop["origin_scale"],
        "subject": subj, "subject_binary": subj_bin, "nulls": prop["nulls"],
        "ties": prop["ties"],
        "node_detail": {nid: {"contribution": r["contribution"], "delta": r["delta"],
                              "hop": r["hop"], "path": r["path"]}
                        for nid, r in nodes.items()},
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


def _validate_cw0(events, config):
    def _d(cur, base):
        c = cur if cur is not None else (base if base is not None else 0.0)
        return c - (base if base is not None else 0.0)
    mism = []
    for ev in events:
        g = _fresh(config)
        evc = Event.model_validate(ev.model_dump())
        propagate_event(evc, g, config)
        real = {n.id: _d(n.dynamic.current_severity, n.dynamic.baseline_severity)
                for n in g.nodes.values()}
        g2 = _fresh(config)
        prop = _propagate(evc, g2, config, "CW-0", "FO-0", "MA-0")
        mine = {nid: r["delta"] for nid, r in prop["nodes"].items()}
        for nid in set(real) | set(mine):
            if abs(real.get(nid, 0.0) - mine.get(nid, 0.0)) > 1e-12:
                mism.append((ev.id, nid, real.get(nid), mine.get(nid)))
    return mism


def _parallel_census(graph, config):
    from collections import defaultdict
    pairs = defaultdict(list)
    for e in graph.edges.values():
        if e.type in SUPPLY_EDGE_TYPES:
            pairs[(e.source_id, e.target_id)].append(e)
    out = []
    for (s, t), es in sorted(pairs.items()):
        if len(es) < 2:
            continue
        ordered = [e for e in graph.out_edges(s)
                   if e.target_id == t and e.type in SUPPLY_EDGE_TYPES]
        taken = ordered[0]
        shares = {e.id: _share(e, config) for e in ordered}
        mx = max(shares.values())
        tk = shares[taken.id]
        out.append({"source": s, "target": t,
                    "edges": [e.id for e in ordered],
                    "taken": taken.id, "taken_share": tk, "max_share": mx,
                    "ratio": (mx / tk) if tk else None,
                    "loss": mx > tk + 1e-12})
    return out


def _country_classification(graph):
    rows = []
    for nid in sorted(n for n in graph.nodes if _is_country(n)):
        targets = _country_targets(graph.nodes[nid], graph)
        rows.append({"country": nid, "n_distinct_targets": len(targets),
                     "targets": sorted(targets),
                     "fo1c_class": ("seed_normally" if len(targets) <= 1 else "scoped")})
    return rows


def main():
    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e) for e in json.loads(REPLAY_EVENTS.read_text())]
    probes = [Event.model_validate(p) for p in json.loads(REPLAY_PROBES.read_text())]
    outcomes = {o["id"]: o["magnitude_ordinal"]
                for o in json.loads(OUTCOMES.read_text())["outcomes"]}

    validation = _validate_cw0(events, config)

    gref = _fresh(config)
    census = _parallel_census(gref, config)
    classification = _country_classification(gref)

    # Block A — cascade semantics, FO-0, both seedings.
    block_a = {}
    for seeding in ["MA-0", "MA-1"]:
        for cw in CASCADES:
            rows = [_metrics(ev, _fresh(config), config, cw, "FO-0", seeding) for ev in events]
            _rank(rows)
            block_a[f"{cw}|{seeding}"] = rows

    # Block B — fanout at CW-0, both seedings.
    block_b = {}
    spearman_b = {}
    for seeding in ["MA-0", "MA-1"]:
        for fo in FANOUTS:
            rows = [_metrics(ev, _fresh(config), config, "CW-0", fo, seeding) for ev in events]
            _rank(rows)
            block_b[f"{fo}|{seeding}"] = rows
            mr = {r["id"]: r["model_rank"] for r in rows}
            spearman_b[f"{fo}|{seeding}"] = _spearman(mr, outcomes)

    # Block C — recommended FO (FO-1c) under CW-2 and CW-1 at MA-1.
    block_c = {}
    for cw in ["CW-0", "CW-2", "CW-1"]:
        rows = [_metrics(ev, _fresh(config), config, cw, "FO-1c", "MA-1") for ev in events]
        _rank(rows)
        block_c[f"FO-1c|{cw}|MA-1"] = rows

    # Probes under each FO at CW-0.
    probe_matrix = {}
    for fo in FANOUTS:
        for p in probes:
            m = _metrics(p, _fresh(config), config, "CW-0", fo, "MA-0")
            probe_matrix[f"{p.id}|{fo}"] = {k: v for k, v in m.items()
                                            if k not in ("node_detail", "top5", "ties")}

    def _strip(rows):
        return [{k: v for k, v in r.items() if k not in ("ties",)} for r in rows]

    facts = {
        "cw0_validation_mismatches": validation,
        "parallel_census": census,
        "country_classification": classification,
        "observed_ordinal": outcomes,
        "block_a_cascade": {k: _strip(v) for k, v in block_a.items()},
        "block_b_fanout": {k: _strip(v) for k, v in block_b.items()},
        "spearman_block_b": spearman_b,
        "block_c_interaction": {k: _strip(v) for k, v in block_c.items()},
        "probe_matrix": probe_matrix,
    }
    (REPO / "docs" / "generated" / "pass_y_facts.json").write_text(
        json.dumps(facts, indent=2, default=str) + "\n")
    n_loss = sum(1 for c in census if c["loss"])
    print("wrote pass_y_facts.json")
    print("CW-0 validation mismatches:", len(validation))
    print("parallel pairs:", len(census), "lossy:", n_loss)
    for seeding in ["MA-0", "MA-1"]:
        print(f"-- {seeding} ρ (Block B) --")
        for fo in FANOUTS:
            print(f"   {fo}: ρ={spearman_b[f'{fo}|{seeding}']:+.4f}")
    _write_markdown(facts)


def _write_markdown(facts):
    L = ["# Cascade semantics & fanout candidates — Pass Y (measurement only)", "",
         f"_Generated by `backend/scripts/pass_y_measure.py`. In-process; nothing "
         f"committed. CW-0 validated vs real engine: "
         f"**{len(facts['cw0_validation_mismatches'])} mismatches**._", ""]
    L.append("## Parallel-edge census (lossy pairs)")
    L.append("")
    L.append("| source | target | takes | share | max | ratio |")
    L.append("|---|---|---|---:|---:|---:|")
    for c in facts["parallel_census"]:
        if c["loss"]:
            L.append(f"| {c['source']} | {c['target']} | {c['taken'].split(':')[-1]} | "
                     f"{c['taken_share']:.4f} | {c['max_share']:.4f} | {c['ratio']:.6f} |")
    L.append("")
    for block, title in [("block_b_fanout", "Block B — fanout at CW-0"),
                         ("block_a_cascade", "Block A — cascade at FO-0")]:
        L.append(f"## {title}")
        L.append("")
        for key, rows in facts[block].items():
            L.append(f"### {key}")
            L.append("")
            L.append("| rank | event | reached | max Δ | max Δ node | subject? | nulls |")
            L.append("|---:|---|---:|---:|---|:--:|---|")
            for r in sorted(rows, key=lambda r: r["model_rank"]):
                sb = r["subject_binary"]
                sbs = "—" if sb is None else ("yes" if sb else "NO")
                L.append(f"| {r['model_rank']} | {r['id'].replace('J-','')} | "
                         f"{r['nodes_reached']} | {r['max_delta']:.6f} | "
                         f"{r['max_delta_node']} | {sbs} | {','.join(r['nulls']) or '—'} |")
            L.append("")
    (REPO / "docs" / "generated" / "cascade_fanout_candidates.md").write_text("\n".join(L) + "\n")
    print("wrote cascade_fanout_candidates.md")


if __name__ == "__main__":
    main()
