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

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

import yaml

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event


# Pass Q.1 §2 — regex used by the caveat-number audit. Same one as the
# guard test test_modeling_caveat_numbers_are_current.
_CAVEAT_DECIMAL_RE = re.compile(
    r"(?<![\d.])(\d+\.\d+)(?!\s*[%xX])(?![\d.])"
)
_CAVEAT_TOLERANCE = 0.05


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

# Pass R — the 8 copper→X edges.
PASS_R_EDGE_IDS = [
    "e:copper-input-tsmc",
    "e:copper-input-sk_hynix",
    "e:copper-input-micron",
    "e:copper-input-samsung",
    "e:copper-input-siemens",
    "e:copper-input-ge_vernova",
    "e:copper-input-quanta",
    "e:copper-input-vertiv",
]

PASS_R_NODES_PRIMARY = [
    "mineral:copper",
    "company:tsmc",
    "company:sk_hynix",
    "company:micron",
    "company:samsung",
    "company:siemens_energy",
    "company:ge_vernova",
    "company:quanta_services",
    "company:vertiv",
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
    _unused, target: str, category, current_edges: list,
) -> float:
    """Sum input_share across every edge into `target` whose
    supply_category equals `category`.

    `category=None` matches ONLY edges with no supply_category
    (e.g. `input_to`) — NOT "any bucket". Pass R.1 §1 correction:
    the prior implementation used
    `getattr(e, "supply_category", None) == category or ...` on a
    list of dicts, and since a dict does not have `supply_category`
    as an *attribute* (only as a *key*), `getattr` returned its
    default `None` for every dict edge. When the caller passed
    `category=None` (correct for `input_to`), the `None == None`
    short-circuit fired on every edge into the target regardless
    of its actual `supply_category` key. This inflated the four
    `copper → fab` input_to bucket sums by summing every supplies-
    stage edge into the fab as well (e.g. TSMC's `bucket_sum_after`
    was reported as 5.18 rather than 0.95).

    Fix: normalize each edge to a single access path per iteration
    (attribute for objects, key for dicts) and drop the `or`-branch
    entirely. `_bucket_members` was already correct; the two now
    agree.
    """
    total = 0.0
    if isinstance(current_edges, dict):
        it = current_edges.values()
    else:
        it = current_edges
    for e in it:
        if isinstance(e, dict):
            e_target = e.get("target_id")
            e_cat = e.get("supply_category")
            e_share = e.get("input_share")
        else:
            e_target = getattr(e, "target_id", None)
            e_cat = getattr(e, "supply_category", None)
            e_share = getattr(e, "input_share", None)
        if e_target != target:
            continue
        if e_cat != category:
            continue
        if e_share is not None:
            total += float(e_share)
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
    """Return (shape, {'pass_o': sha_or_null, 'pass_p': sha_or_null}).

    Pass R §7 correction — prior implementation had two bugs:
      (a) `if pass_o and pass_p: return "two"` fired BEFORE the
          equality check, so a squashed commit (same SHA matching
          both "Pass O" and "Pass P" tokens) was misreported as
          two commits rather than one. The `"one"` branch was
          therefore unreachable.
      (b) The colon-less token `"Pass O"` matches any commit
          message containing that substring; using `"Pass O:"`
          (the actual title prefix) is safer against future
          commit-message variations.
    Equality is now checked first; a matching SHA is a squashed
    commit ("one") regardless of how many lines it appears on.
    """
    log = _git("log", "--oneline", "-20").strip().splitlines()
    pass_o = next(
        (line.split()[0] for line in log
         if "Pass O:" in line and "N.1" not in line),
        None,
    )
    pass_p = next(
        (line.split()[0] for line in log if "Pass P:" in line), None,
    )
    if pass_o and pass_p:
        if pass_o == pass_p:
            return "one", {"pass_o": pass_o, "pass_p": pass_p}
        return "two", {"pass_o": pass_o, "pass_p": pass_p}
    return "other", {"pass_o": pass_o, "pass_p": pass_p}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--output-name", default="pass_q_facts.json",
        help=(
            "Filename under docs/generated/ for the artifact "
            "(default: pass_q_facts.json). Use `pass_q1_facts.json` for "
            "Pass Q.1 and so on for subsequent correction passes."
        ),
    )
    parser.add_argument(
        "--pass-tag", default="q", choices=["q", "q1", "r"],
        help=(
            "Which pass's edge + node sets to track in the artifact. "
            "Pass Q's 13 power-cluster edges (`q`, `q1`) or Pass R's 8 "
            "copper edges (`r`). Determines PASS_*_EDGE_IDS + "
            "PASS_*_NODES_PRIMARY used in the per-edge and nodes_touched "
            "sections. Default: q for backwards compatibility."
        ),
    )
    args = parser.parse_args()

    if args.pass_tag == "r":
        edge_ids = PASS_R_EDGE_IDS
        primary_nodes = PASS_R_NODES_PRIMARY
    else:
        edge_ids = PASS_Q_EDGE_IDS
        primary_nodes = PASS_Q_NODES_PRIMARY

    head_sha = _git("rev-parse", "HEAD").strip()
    shape, shape_shas = _commit_shape()

    # Score BEFORE: `git show HEAD:docs/generated/severity_snapshot.json`
    # is the reproducible-from-git-alone reference; reading the on-disk
    # snapshot risks reading a post-run roll-forward (Pass R rolls the
    # snapshot forward before this artifact is written).
    snap = json.loads(_git("show", "HEAD:docs/generated/severity_snapshot.json"))
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
    for eid in edge_ids:
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
    all_involved_ids = set(primary_nodes)
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
            "in_primary_touched_set": nid in primary_nodes,
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

    # -------- caveat number audit (Pass Q.1 §2) --------
    # Runs the same branch-D check as
    # `test_modeling_caveat_numbers_are_current`, but produces a per-
    # node record in the artifact instead of an assertion. The test is
    # authoritative for pass/fail; this block gives the artifact a
    # readable summary.
    narr_raw = yaml.safe_load(
        (REPO / "config" / "narration.yaml").read_text()
    ) or {}
    caveats_cfg = narr_raw.get("modeling_caveats", {})
    # Pass R §7 — also read the HEAD-committed narration + nodes so
    # `asserted_numbers_before` can be populated (Q.1 open item).
    head_narr = yaml.safe_load(
        _git("show", "HEAD:config/narration.yaml")
    ) or {}
    head_caveats_cfg = head_narr.get("modeling_caveats", {})
    head_nodes = {
        n["id"]: n for n in json.loads(_git("show", "HEAD:data/ai/nodes.json"))
    }
    caveat_audit = []
    for nid, node in g.nodes.items():
        raw_cav = node.static.modeling_caveat
        if not raw_cav:
            continue
        # Pass R §7 — local shape variable renamed to avoid shadowing
        # `shape` from `_commit_shape()`; that shadowing sent "literal"
        # into the Q.1 artifact's `commit_shape_o_p` field.
        if raw_cav.startswith("caveat:"):
            text = " ".join(
                (caveats_cfg.get(raw_cav[len('caveat:'):], "")).split()
            )
            caveat_shape = "key"
        else:
            text = raw_cav
            caveat_shape = "literal"
        numbers = [
            float(m) for m in _CAVEAT_DECIMAL_RE.findall(text)
            if 0.0 <= float(m) <= 1.0
        ]
        # `asserted_numbers_before` — decimals in the HEAD-committed
        # caveat prose, resolved the same way. Lets the artifact
        # DEMONSTRATE branch-D detection rather than only report a
        # clean post-fix state.
        head_static = (head_nodes.get(nid) or {}).get("static") or {}
        head_cav = head_static.get("modeling_caveat")
        if head_cav:
            if head_cav.startswith("caveat:"):
                head_text = " ".join(
                    (head_caveats_cfg.get(head_cav[len('caveat:'):], "")).split()
                )
            else:
                head_text = head_cav
            numbers_before = [
                float(m) for m in _CAVEAT_DECIMAL_RE.findall(head_text)
                if 0.0 <= float(m) <= 1.0
            ]
        else:
            numbers_before = []
        candidate_values = [
            node.dynamic.inbound_hhi,
            node.dynamic.outbound_criticality,
            node.dynamic.concentration,
        ]
        candidate_values = [v for v in candidate_values if v is not None]
        stale = [
            n for n in numbers
            if not any(abs(n - v) <= _CAVEAT_TOLERANCE for v in candidate_values)
        ]
        caveat_audit.append({
            "id": nid,
            "caveat_shape": caveat_shape,
            "asserted_numbers": numbers,
            "asserted_numbers_before": numbers_before,
            "current_inbound_hhi": node.dynamic.inbound_hhi,
            "current_outbound_criticality": node.dynamic.outbound_criticality,
            "current_concentration": node.dynamic.concentration,
            "stale_numbers": stale,
            "verdict": "accurate" if not stale else "stale",
        })

    # -------- suite (Pass Q.1 §6 — dual invocations) --------
    # Pass Q.1 §4 pinned pytest.ini so `pytest`, `pytest backend/tests`,
    # and `python -m pytest` all agree. Record both the module and bare
    # invocations so the artifact carries direct evidence the pin holds.
    #
    # Pass Q.1 §6 — scraper widened. Pass Q's regex `^(\d+)\s+passed`
    # required the pytest summary line to begin with the passed count;
    # when there were failing tests the tail begins `N failed, M passed
    # in ...` and the numeric fields silently reported 0. Now search
    # anywhere in the line for `\d+ passed`, `\d+ failed`, `\d+ xfailed`.
    # The exit code is also captured so a caller can gate on it directly
    # without re-parsing prose.
    def _run_suite(argv: list[str]) -> dict:
        try:
            r = subprocess.run(
                argv, cwd=REPO, capture_output=True, text=True, timeout=180,
            )
            tail = r.stdout.strip().splitlines()[-1] if r.stdout else ""
            passed_m = re.search(r"(\d+)\s+passed", tail)
            failed_m = re.search(r"(\d+)\s+failed", tail)
            xfail_m = re.search(r"(\d+)\s+xfailed?", tail)
            return {
                "invocation": " ".join(argv),
                "passed": int(passed_m.group(1)) if passed_m else 0,
                "failed": int(failed_m.group(1)) if failed_m else 0,
                "xfail": int(xfail_m.group(1)) if xfail_m else 0,
                "exit_code": r.returncode,
                "tail": tail,
            }
        except Exception as exc:
            return {"invocation": " ".join(argv), "error": str(exc)}

    suite = {
        "python_m_pytest": _run_suite(
            ["python", "-m", "pytest", "backend/tests/", "-q", "--tb=no"],
        ),
        "bare_pytest": _run_suite(
            ["pytest", "backend/tests/", "-q", "--tb=no"],
        ),
    }

    # -------- Pass R §7 — copper_axis_check --------
    import math
    copper = g.nodes.get("mineral:copper")
    copper_before = before_nodes.get("mineral:copper", {})
    if copper is not None:
        inb_a = copper.dynamic.inbound_hhi
        out_a = copper.dynamic.outbound_criticality
        conc_a = copper.dynamic.concentration
        sev_a = copper.dynamic.baseline_severity
        b_lower = inb_a  # region A ceiling = current inbound
        crit_boundary = c.chokepoint_thresholds.get("critical", 0.0)
        sub = copper.static.substitutability.value if copper.static.substitutability else 0.0
        lt = copper.static.lead_time_years.value if copper.static.lead_time_years else 0.0
        coef = (1.0 - sub) * math.log10(lt + 1.0) / math.log10(26)
        c_lower = crit_boundary / coef if coef > 0 else float("inf")
        if out_a <= b_lower:
            region = "A"
        elif conc_a < c_lower:
            region = "B"
        else:
            region = "C"
        copper_axis_check = {
            "inbound_before": copper_before.get("inbound_hhi"),
            "inbound_after": inb_a,
            "outbound_before": copper_before.get("outbound_criticality"),
            "outbound_after": out_a,
            "concentration_before": copper_before.get("concentration"),
            "concentration_after": conc_a,
            "severity_before": copper_before.get("severity"),
            "severity_after": sev_a,
            "tier_before": copper_before.get("tier"),
            "tier_after": (
                copper.dynamic.baseline_tier.value
                if copper.dynamic.baseline_tier is not None else "unscored"
            ),
            "region": region,
            "region_thresholds": {"b_lower": b_lower, "c_lower": c_lower},
        }
    else:
        copper_axis_check = None

    # -------- Pass R.1 §4 — outbound clamp visibility --------
    # Emit for every node: raw outbound (pre-normalization walk value),
    # normalized (raw / fixed_reference), and clamped (True when
    # normalized > 1.0). Under `outbound.normalization: fixed` the
    # engine clamps to 1.0, so several nodes may share
    # `outbound_criticality = 1.0` while their RAW values differ
    # substantially. This flattens the top of the concentration
    # distribution; the re-baseline pass (P.5.2) needs to see it
    # before it re-derives boundaries.
    from app.scoring.engine import _outbound_criticality_raw
    outbound_raw_map = {
        nid: _outbound_criticality_raw(
            nid, g,
            c.concentration_outbound_decay,
            c.concentration_outbound_max_hops,
            c.concentration_outbound_min_influence,
            share_field=c.outbound_share_field,
            fallback=c.outbound_fallback_to_input_share,
        )
        for nid in g.nodes
    }
    _fixed_ref = c.outbound_fixed_reference
    _clamp_records = {}
    for nid, raw_val in outbound_raw_map.items():
        norm_val = raw_val / _fixed_ref if _fixed_ref and _fixed_ref > 0 else None
        _clamp_records[nid] = {
            "outbound_raw": raw_val,
            "outbound_normalized": norm_val,
            "outbound_clamped": (norm_val is not None and norm_val > 1.0),
        }

    # -------- Pass R §7 — boundary_proximity --------
    # For every scored node, distance to nearest frozen boundary above
    # and below. Lets the next pass inherit a proximity map instead of
    # rediscovering situations like copper's boundary-anchor position
    # node by node.
    boundaries_sorted = sorted(c.chokepoint_thresholds.items(), key=lambda kv: kv[1])
    boundary_proximity = []
    for nid, node in g.nodes.items():
        sev = node.dynamic.baseline_severity
        if sev is None:
            continue
        below = None
        below_v = None
        above = None
        above_v = None
        for name, v in boundaries_sorted:
            if v <= sev and (below_v is None or v > below_v):
                below, below_v = name, v
            if v > sev and (above_v is None or v < above_v):
                above, above_v = name, v
        boundary_proximity.append({
            "id": nid,
            "severity": sev,
            "tier": (
                node.dynamic.baseline_tier.value
                if node.dynamic.baseline_tier is not None else "unscored"
            ),
            "nearest_boundary_below": below,
            "distance_below": (sev - below_v) if below_v is not None else None,
            "nearest_boundary_above": above,
            "distance_above": (above_v - sev) if above_v is not None else None,
        })
    boundary_proximity.sort(key=lambda r: -r["severity"])

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
            # Pass Q.1 §6 — split `eps` into configured vs applied.
            # `noisy_or` (Pass N) takes no eps argument; the config
            # carries an eps value only because `noisy_or_eps` was
            # evaluated in Pass M and the key remained. Emitting a
            # single `eps` field misled the Pass Q artifact into
            # asserting `eps: 0.01` under a `method: noisy_or` run
            # where the value is dormant. `eps_applied` is None when
            # the method does not consume eps; `eps_configured` records
            # what the file carries regardless (Pass O provenance
            # principle: capture the config, don't infer applicability).
            "eps_configured": c.inbound_per_stage_eps,
            "eps_applied": (
                c.inbound_per_stage_eps
                if c.inbound_per_stage_method == "noisy_or_eps"
                else None
            ),
        },
        "edges": edges_facts,
        "nodes_touched": nodes_facts,
        "caveat_check": caveat_facts,
        "caveat_number_audit": caveat_audit,
        "copper_axis_check": copper_axis_check,
        "boundary_proximity": boundary_proximity,
        # Pass R.1 §4 — outbound clamp visibility. Every node, sorted by
        # outbound_raw descending so the ceiling-cluster is at the top.
        "outbound_clamp_check": [
            {"id": nid, **_clamp_records[nid]}
            for nid in sorted(
                _clamp_records, key=lambda k: -_clamp_records[k]["outbound_raw"]
            )
        ],
        "suite": suite,
    }
    out_path = REPO / "docs" / "generated" / args.output_name
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
