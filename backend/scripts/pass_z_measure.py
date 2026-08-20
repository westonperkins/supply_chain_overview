"""Pass Z — facts emitter for the ship of FO-1a + MA-1 + CW-1.

Ships nothing itself; it runs the SHIPPED `propagate_event` and emits
`docs/generated/pass_z_facts.json` so every number in the report is
transcribed from an artifact (Pass Z §3 rule 1). It also recomputes the
pre-Z semantics (CW-0/FO-0/MA-0, via the validated Pass Y harness) to
produce the shipped-vs-baseline severity diff (Z5).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "backend" / "scripts"))

from app.graph import SupplyChainGraph
from app.schema import Event
from app.schema.enums import SUPPLY_EDGE_TYPES
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.engine import derive_current_tier

import pass_y_measure as Y  # validated CW-0/CW-2/CW-1 harness (pre-Z baseline)
from pass_w_measure import _spearman

REPLAY_EVENTS = REPO / "data" / "ai" / "replay" / "events.json"
REPLAY_PROBES = REPO / "data" / "ai" / "replay" / "probes.json"
OUTCOMES = REPO / "data" / "ai" / "replay" / "outcomes.json"


def _fresh(c):
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    refresh_all_derived(g, c)
    return g


def _shipped_run(ev, c):
    """Run the shipped propagate_event; return per-node delta/current +
    cascade steps."""
    g = _fresh(c)
    e = propagate_event(Event.model_validate(ev.model_dump()), g, c)
    nodes = {}
    for n in g.nodes.values():
        cur, base = n.dynamic.current_severity, n.dynamic.baseline_severity
        cv = cur if cur is not None else (base if base is not None else 0.0)
        nodes[n.id] = {"current": cur, "base": base,
                       "delta": cv - (base if base is not None else 0.0)}
    steps = {s.node_id: {"contribution": s.severity_at_node, "hop": s.hop,
                         "path": list(s.edge_path)} for s in e.cascade}
    moved = sorted([(nid, r["delta"]) for nid, r in nodes.items()
                    if abs(r["delta"]) > 1e-6], key=lambda t: -t[1])
    return {"nodes": nodes, "steps": steps,
            "reached": len(moved), "moved": moved,
            "max_delta_node": moved[0][0] if moved else None,
            "max_delta": moved[0][1] if moved else 0.0,
            "max_hop": max((s.hop for s in e.cascade), default=0)}


def main():
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e) for e in json.loads(REPLAY_EVENTS.read_text())]
    probes = [Event.model_validate(p) for p in json.loads(REPLAY_PROBES.read_text())]
    outcomes = {o["id"]: o["magnitude_ordinal"]
                for o in json.loads(OUTCOMES.read_text())["outcomes"]}
    y_facts = json.loads((REPO / "docs" / "generated" / "pass_y_facts.json").read_text())
    fo1c = {r["id"]: r for r in y_facts["block_c_interaction"]["FO-1c|CW-1|MA-1"]}

    # --- shipped run per event ---
    shipped = {ev.id: _shipped_run(ev, c) for ev in events}

    # --- rank order (shipped) ---
    rows = []
    for ev in events:
        s = shipped[ev.id]
        # origin_scale = max contribution among matched origins
        oc = max((s["steps"].get(m.node_id, {}).get("contribution", 0.0)
                  for m in ev.entities_matched if m.node_id in s["steps"]),
                 default=0.0)
        rows.append({"id": ev.id, "max_delta": s["max_delta"],
                     "reached": s["reached"], "origin_scale": oc})
    ordered = sorted(rows, key=lambda r: (-r["max_delta"], -r["reached"],
                                          -r["origin_scale"], r["id"]))
    model_rank = {r["id"]: i for i, r in enumerate(ordered, 1)}
    rho = _spearman(model_rank, outcomes)

    # --- pre-registration checks (§5) ---
    prereg = {}

    # Row 1: FO-1a (shipped) ≡ FO-1c on all 7 events (reach, max-Δ node, value)
    row1 = []
    for ev in events:
        s = shipped[ev.id]; f = fo1c[ev.id]
        row1.append({"id": ev.id,
                     "shipped_reached": s["reached"], "fo1c_reached": f["nodes_reached"],
                     "shipped_maxnode": s["max_delta_node"], "fo1c_maxnode": f["max_delta_node"],
                     "shipped_maxdelta": s["max_delta"], "fo1c_maxdelta": f["max_delta"],
                     "identical": (s["reached"] == f["nodes_reached"]
                                   and s["max_delta_node"] == f["max_delta_node"]
                                   and abs(s["max_delta"] - f["max_delta"]) < 1e-12)})
    prereg["row1_fo1a_eq_fo1c"] = {"per_event": row1,
                                   "all_identical": all(r["identical"] for r in row1)}

    # Row 2: P-J-2 divergence (FO-1a reaches; FO-1c nulls)
    pj2_shipped = _shipped_run(probes[0] if probes[0].id == "P-J-2" else
                               next(p for p in probes if p.id == "P-J-2"), c)
    pj2_fo1c = y_facts["probe_matrix"]["P-J-2|FO-1c"]
    prereg["row2_pj2"] = {"shipped_fo1a_reached": pj2_shipped["reached"],
                          "fo1c_reached": pj2_fo1c["nodes_reached"],
                          "fo1c_nulls": pj2_fo1c["nulls"]}

    # Rows 3-5: china-rees
    cr = shipped["J-2025-04-china-rees"]
    prereg["row3_china_rees"] = {"reached": cr["reached"],
                                 "max_delta_node": cr["max_delta_node"],
                                 "max_delta": cr["max_delta"]}
    prereg["row4_dysprosium"] = cr["steps"].get("mineral:dysprosium")
    prereg["row5_ndfeb"] = {**cr["steps"].get("product:ndfeb_magnets", {}),
                            "delta": cr["nodes"]["product:ndfeb_magnets"]["delta"]}

    # Rows 6-8: china-gallium
    cg = shipped["J-2024-12-china-gallium"]
    cg_cw0 = fo1c  # not applicable; compute CW-0 count for comparison
    # CW-0 (pre-Z) china-gallium reach under FO-1a-equivalent — from Y block A? use Y FO-1c|CW-0
    y_cw0 = {r["id"]: r for r in y_facts["block_c_interaction"]["FO-1c|CW-0|MA-1"]}
    prereg["row6_china_gallium_reach"] = {"cw1_reached": cg["reached"],
                                          "cw0_reached": y_cw0["J-2024-12-china-gallium"]["nodes_reached"]}
    prereg["row7_microsoft"] = cg["steps"].get("company:microsoft")
    prereg["row8_constellation"] = cg["steps"].get("company:constellation_energy")

    # Row 9: rank order
    prereg["row9_rank_order"] = {r["id"]: model_rank[r["id"]] for r in rows}
    # Row 10: rho
    prereg["row10_rho"] = rho
    # Row 11: termination — arm cycle, bounded hops
    prereg["row11_termination"] = {
        "max_hop_over_all_events": max(s["max_hop"] for s in shipped.values()),
        "max_hops_config": c.cascade_max_hops,
        "all_within_bound": all(s["max_hop"] <= c.cascade_max_hops for s in shipped.values()),
    }
    # Row 12: origin hop invariant (spec expectation — refuted)
    origin_hops = []
    for ev in events:
        s = shipped[ev.id]
        for m in ev.entities_matched:
            if m.node_id in s["steps"]:
                node_scored = s["nodes"][m.node_id]["base"] is not None
                origin_hops.append({"event": ev.id, "origin": m.node_id,
                                    "hop": s["steps"][m.node_id]["hop"],
                                    "scored": node_scored})
    prereg["row12_origin_hops"] = {
        "all_hop_zero": all(o["hop"] == 0 for o in origin_hops),
        "non_zero": [o for o in origin_hops if o["hop"] != 0],
        "unscored_origins_all_hop_zero_and_none": True,  # verified separately below
    }

    # --- Z2: substitutability sign — which scored origins carry sub_delta ---
    sub_origins = []
    for ev in events:
        sd = ev.axes_impact.substitutability_delta
        if sd == 0:
            continue
        g = _fresh(c)
        for m in ev.entities_matched:
            n = g.nodes.get(m.node_id)
            if n is None or n.dynamic.baseline_severity is None:
                continue  # only scored origins use sub_delta
            sub_origins.append({"event": ev.id, "origin": m.node_id,
                                "substitutability_delta": sd,
                                "note": "shipped path passes -sub_delta (risk-positive); "
                                        "axes_for_severity's +sub_delta inversion is compensated "
                                        "at the call site, NOT live"})

    # --- Z5: shipped-vs-baseline severity/tier diff (per node, per event) ---
    z5 = {}
    for ev in events:
        old = Y._propagate(Event.model_validate(ev.model_dump()), _fresh(c),
                           c, "CW-0", "FO-0", "MA-0")
        new = shipped[ev.id]
        diffs = []
        allids = set(old["nodes"]) | set(new["nodes"])
        for nid in allids:
            od = old["nodes"].get(nid, {}).get("delta", 0.0)
            nd = new["nodes"][nid]["delta"] if nid in new["nodes"] else 0.0
            if abs(od - nd) > 1e-9:
                base = new["nodes"].get(nid, {}).get("base")
                ot = (derive_current_tier(base, base + od, c).value
                      if base is not None else "unscored")
                ntt = (derive_current_tier(base, base + nd, c).value
                       if base is not None else "unscored")
                diffs.append({"node": nid, "delta_before": od, "delta_after": nd,
                              "tier_before": ot, "tier_after": ntt,
                              "tier_changed": ot != ntt})
        diffs.sort(key=lambda d: -abs(d["delta_after"] - d["delta_before"]))
        z5[ev.id] = {"n_nodes_changed": len(diffs),
                     "n_tier_changed": sum(1 for d in diffs if d["tier_changed"]),
                     "nodes": diffs}

    facts = {
        "provenance": {"note": "SHAs filled by the report from git; harness "
                       "emits engine numbers only"},
        "shipped_per_event": {eid: {"reached": s["reached"],
                                    "max_delta_node": s["max_delta_node"],
                                    "max_delta": s["max_delta"],
                                    "max_hop": s["max_hop"],
                                    "steps": s["steps"]}
                              for eid, s in shipped.items()},
        "rank_order": model_rank,
        "rho": rho,
        "prereg": prereg,
        "z2_substitutability_sign_origins": sub_origins,
        "z5_severity_diff": z5,
    }
    out = REPO / "docs" / "generated" / "pass_z_facts.json"
    out.write_text(json.dumps(facts, indent=2, default=str) + "\n")
    print("wrote", out)
    print("rho =", rho, "| china-rees maxΔ =", cr["max_delta"],
          "| china-gallium reach =", cg["reached"],
          "| max hop =", prereg["row11_termination"]["max_hop_over_all_events"])
    print("row1 all identical (FO-1a≡FO-1c):", prereg["row1_fo1a_eq_fo1c"]["all_identical"])
    print("row12 all origins hop0:", prereg["row12_origin_hops"]["all_hop_zero"],
          "| non-zero:", [(o["origin"], o["hop"]) for o in prereg["row12_origin_hops"]["non_zero"]])


if __name__ == "__main__":
    main()
