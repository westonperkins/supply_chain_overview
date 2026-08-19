"""Pass Q §6 — mechanical artifact writer.

Emits `docs/generated/pass_q_facts.json` from measurable state so the
Pass Q report can QUOTE the artifact rather than recall it from memory.
Prose narration of numbers is the failure surface hit repeatedly in
prior reports (mistyped baselines, fabricated causal explanations,
asserted precision without derivation). This script is the ground
truth; the report reads from it.

Sources:
  - "before" edges: `git show HEAD:data/ai/edges.json` — the last
    committed state; reproducible from git alone.
  - "before" node metrics: `docs/generated/severity_snapshot.json` —
    still `pass_n_d4a` at Pass Q open (Passes O + P did not roll the
    snapshot forward).
  - "after" everything: current working tree, scored in-process.

Full float precision throughout; rounding belongs in the report.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event


PASS_Q_EDGE_IDS = [
    "e:gev-supplies-constellation",
    "e:gev-supplies-duke",
    "e:gev-supplies-nextera",
    "e:gev-supplies-citadel",
    "e:nextera-supplies-citadel",
    "e:quanta-supplies-duke",
    "e:quanta-supplies-nextera",
    "e:siemens-supplies-constellation",
    "e:siemens-supplies-duke",
    "e:siemens-supplies-nextera",
    "e:siemens-supplies-citadel",
    "e:vertiv-supplies-citadel",
    "e:vertiv-supplies-vantage",
]

PASS_Q_NODES_PRIMARY = [
    "company:ge_vernova",
    "company:siemens_energy",
    "company:quanta_services",
    "company:vertiv",
    "company:nextera_energy",
    "company:constellation_energy",
    "company:duke_energy",
    "facility:the_citadel",
    "facility:vantage_frontier",
]

CAVEAT_CHECK_NODES = [
    "company:ge_vernova",
    "company:siemens_energy",
    "company:quanta_services",
]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8")


def _head_edge_lookup() -> dict:
    """Parse edges.json at HEAD and return {edge_id: edge_dict}."""
    text = _git("show", "HEAD:data/ai/edges.json")
    return {e["id"]: e for e in json.loads(text)}


def _bucket_sum(
    edges_by_id: dict, target: str, category: str, current_edges: list,
) -> float:
    """Sum input_share across every edge into `target` under `category`.
    Used to check the K.2.1 §2.3 collision claim (bucket sums crossing
    1.0 under noisy-OR are honest, not defects)."""
    total = 0.0
    # current_edges may be a graph.edges dict OR a list of dicts.
    if isinstance(current_edges, dict):
        it = current_edges.values()
    else:
        it = current_edges
    for e in it:
        if getattr(e, "target_id", None) == target or (
            isinstance(e, dict) and e.get("target_id") == target
        ):
            if getattr(e, "supply_category", None) == category or (
                isinstance(e, dict) and e.get("supply_category") == category
            ):
                v = getattr(e, "input_share", None)
                if v is None and isinstance(e, dict):
                    v = e.get("input_share")
                if v is not None:
                    total += float(v)
    return total


def _bucket_members(
    edges_dict_list: list, target: str, category: str,
) -> list[str]:
    members = []
    for e in edges_dict_list:
        if e.get("target_id") == target and e.get("supply_category") == category:
            members.append(e.get("source_id"))
    return sorted(members)


def _commit_shape() -> tuple[str, dict]:
    """Return (shape, {'pass_o': sha_or_null, 'pass_p': sha_or_null})."""
    log = _git("log", "--oneline", "-20").strip().splitlines()
    pass_o = next(
        (line.split()[0] for line in log if "Pass O" in line and "N.1" not in line),
        None,
    )
    pass_p = next(
        (line.split()[0] for line in log if "Pass P" in line), None,
    )
    if pass_o and pass_p:
        return "two", {"pass_o": pass_o, "pass_p": pass_p}
    if pass_o == pass_p and pass_o is not None:
        return "one", {"pass_o": pass_o, "pass_p": pass_p}
    return "other", {"pass_o": pass_o, "pass_p": pass_p}


def main() -> None:
    head_sha = _git("rev-parse", "HEAD").strip()
    shape, shape_shas = _commit_shape()

    # Score BEFORE: from pass_n_d4a snapshot on disk (which still
    # represents Pass Q open — Passes O and P did not roll forward).
    snap = json.load(
        open(REPO / "docs" / "generated" / "severity_snapshot.json")
    )
    before_nodes = snap["nodes"]

    # HEAD edges lookup.
    head_edges_by_id = _head_edge_lookup()
    head_edges_list = list(head_edges_by_id.values())

    # Score AFTER: current working tree.
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for ev in g.events.values():
        propagate_event(ev, g, c)
    current_edges_list = [
        e for e in json.load(open(REPO / "data" / "ai" / "edges.json"))
    ]

    # -------- per-edge before/after --------
    edges_facts = []
    for eid in PASS_Q_EDGE_IDS:
        e_before = head_edges_by_id.get(eid)
        e_after_graph = g.edges.get(eid)
        e_after_json = next(
            (e for e in current_edges_list if e.get("id") == eid), None,
        )
        if e_before is None or e_after_json is None:
            edges_facts.append({"id": eid, "error": "missing"})
            continue
        before_val = e_before.get("input_share")
        after_val = e_after_json.get("input_share")
        source = e_before.get("source_id")
        target = e_before.get("target_id")
        category = e_before.get("supply_category")
        # bucket sums measured on both sides
        bucket_before = _bucket_sum(head_edges_by_id, target, category, head_edges_list)
        bucket_after = _bucket_sum({}, target, category, current_edges_list)
        members = _bucket_members(current_edges_list, target, category)
        sole = (len(members) == 1)
        # status
        note_after = (e_after_json.get("static") or {}).get("source_note", "")
        note_before = (e_before.get("static") or {}).get("source_note", "")
        if before_val != after_val:
            status = "reauthored_value"
        elif note_after != note_before:
            status = "reauthored_note_only"
        else:
            status = "undeterminable"
        confidence = (
            (e_after_json.get("static") or {}).get("confidence")
            or "unknown"
        )
        edges_facts.append({
            "id": eid,
            "source": source,
            "target": target,
            "supply_category": category,
            "input_share_before": before_val,
            "input_share_after": after_val,
            "status": status,
            "confidence": confidence,
            "bucket_members": members,
            "bucket_sum_before": bucket_before,
            "bucket_sum_after": bucket_after,
            "sole_supplier_bucket": sole,
        })

    # -------- per-node before/after --------
    nodes_facts = []
    all_involved_ids = set(PASS_Q_NODES_PRIMARY)
    # Add any node whose metrics moved so the artifact records the
    # cascade footprint honestly (spec §7 stop-condition sweep needs
    # this readable in one place).
    for nid, n in g.nodes.items():
        sev_a = n.dynamic.baseline_severity
        sev_b = before_nodes.get(nid, {}).get("severity")
        inb_a = n.dynamic.inbound_hhi
        inb_b = before_nodes.get(nid, {}).get("inbound_hhi")
        out_a = n.dynamic.outbound_criticality
        out_b = before_nodes.get(nid, {}).get("outbound_criticality")
        conc_a = n.dynamic.concentration
        conc_b = before_nodes.get(nid, {}).get("concentration")
        tier_a = (
            n.dynamic.baseline_tier.value
            if n.dynamic.baseline_tier is not None else "unscored"
        )
        tier_b = before_nodes.get(nid, {}).get("tier", "unscored")
        moved = any(
            (a != b) for a, b in (
                (sev_a, sev_b), (inb_a, inb_b), (out_a, out_b),
                (conc_a, conc_b),
            )
        ) or tier_a != tier_b
        if moved or nid in all_involved_ids:
            all_involved_ids.add(nid)

    for nid in sorted(all_involved_ids):
        n = g.nodes.get(nid)
        if n is None:
            continue
        b = before_nodes.get(nid, {})
        sev_a = n.dynamic.baseline_severity
        inb_a = n.dynamic.inbound_hhi
        out_a = n.dynamic.outbound_criticality
        conc_a = n.dynamic.concentration
        tier_a = (
            n.dynamic.baseline_tier.value
            if n.dynamic.baseline_tier is not None else "unscored"
        )
        dom_axis = lambda i, o: "inbound" if (i or 0) >= (o or 0) else "outbound"
        nodes_facts.append({
            "id": nid,
            "in_primary_touched_set": nid in PASS_Q_NODES_PRIMARY,
            "inbound_hhi_before": b.get("inbound_hhi"),
            "inbound_hhi_after": inb_a,
            "outbound_before": b.get("outbound_criticality"),
            "outbound_after": out_a,
            "concentration_before": b.get("concentration"),
            "concentration_after": conc_a,
            "dominant_axis_before": dom_axis(
                b.get("inbound_hhi"), b.get("outbound_criticality"),
            ),
            "dominant_axis_after": dom_axis(inb_a, out_a),
            "severity_before": b.get("severity"),
            "severity_after": sev_a,
            "tier_before": b.get("tier", "unscored"),
            "tier_after": tier_a,
        })

    # -------- caveat check (§5) --------
    caveat_facts = []
    for nid in CAVEAT_CHECK_NODES:
        n = g.nodes[nid]
        b = before_nodes[nid]
        inb_a = n.dynamic.inbound_hhi
        out_a = n.dynamic.outbound_criticality
        inb_b = b["inbound_hhi"]
        out_b = b["outbound_criticality"]
        if inb_a != inb_b:
            branch = "C"
            reason = "inbound_hhi moved — stop condition (spec §5 branch C)"
        elif (inb_a or 0) >= (out_a or 0):
            branch = "A"
            reason = "inbound_hhi unchanged AND inbound still the dominant axis"
        else:
            branch = "B"
            reason = "inbound_hhi unchanged BUT outbound now ≥ inbound; caveat is scope-stale"
        caveat_facts.append({
            "id": nid,
            "branch": branch,
            "reason": reason,
            "inbound_hhi_before": inb_b,
            "inbound_hhi_after": inb_a,
            "outbound_before": out_b,
            "outbound_after": out_a,
        })

    # -------- suite --------
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "backend/tests/", "-q", "--tb=no"],
            cwd=REPO, capture_output=True, text=True, timeout=180,
        )
        tail = r.stdout.strip().splitlines()[-1] if r.stdout else ""
        # e.g. "110 passed in 0.66s"
        import re
        m = re.match(r"^(\d+)\s+passed", tail)
        passed = int(m.group(1)) if m else 0
        failed_m = re.search(r"(\d+)\s+failed", tail)
        failed = int(failed_m.group(1)) if failed_m else 0
        xfail_m = re.search(r"(\d+)\s+xfailed?", tail)
        xfail = int(xfail_m.group(1)) if xfail_m else 0
        suite = {"passed": passed, "failed": failed, "xfail": xfail, "tail": tail}
    except Exception as exc:
        suite = {"error": str(exc)}

    # -------- output --------
    out = {
        "head_sha_at_open": head_sha,
        "commit_shape_o_p": shape,
        "commit_shas_o_p": shape_shas,
        "graph": {
            "nodes": len(g.nodes),
            "edges": len(g.edges),
            "scored": sum(
                1 for n in g.nodes.values()
                if n.dynamic.baseline_severity is not None
            ),
        },
        "boundaries": dict(c.chokepoint_thresholds),
        "threshold_mode": c.threshold_mode,
        "fixed_reference": c.outbound_fixed_reference,
        "aggregator": {
            "method": c.inbound_per_stage_method,
            "eps": c.inbound_per_stage_eps,
        },
        "edges": edges_facts,
        "nodes_touched": nodes_facts,
        "caveat_check": caveat_facts,
        "suite": suite,
    }
    out_path = REPO / "docs" / "generated" / "pass_q_facts.json"
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
