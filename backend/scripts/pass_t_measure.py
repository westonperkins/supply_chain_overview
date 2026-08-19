"""Pass T — measurement pass for the P.5.2 re-baseline.

Emits `docs/generated/pass_t_facts.json` with:
  - full node matrices under 4 fixed_reference candidates (FR-A/B/C/D)
  - boundary derivation per candidate at separation_factor 3.0
  - separation_factor sensitivity strip {2.0, 2.5, 3.0, 3.5, 4.0}
  - max-path outbound walk experiment (synthetic sub-graph)
  - reproducibility second-run diff (§6(6))

No config file is edited. Every candidate is computed in-process by
re-normalizing raw outbound values against a candidate `fixed_reference`
and re-computing concentration + severity + tier via the standard
formulas. The committed graph state is untouched.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.engine import _outbound_criticality_raw
from app.scoring.thresholds import derive_thresholds
from app.schema.enums import EdgeType


BOUNDARY_NAMES = ("critical", "high", "moderate")


def _tier_from_boundaries(severity, boundaries):
    """Same lower-bound convention as the scoring engine."""
    if severity is None:
        return "unscored"
    if severity >= boundaries.get("critical", float("inf")):
        return "critical"
    if severity >= boundaries.get("high", float("inf")):
        return "high"
    if severity >= boundaries.get("moderate", float("inf")):
        return "moderate"
    return "none"


def _substitutability(n):
    sv = n.static.substitutability
    return float(sv.value) if sv is not None else None


def _lead_time(n):
    sv = n.static.lead_time_years
    return float(sv.value) if sv is not None else None


def _severity_coef(sub, lt):
    """severity = concentration × (1 − substitutability) × log10(lt+1)/log10(26)"""
    if sub is None or lt is None:
        return None
    return (1.0 - sub) * math.log10(lt + 1.0) / math.log10(26.0)


def _score_under_candidate(g, c, raw, fr, clamp):
    """Return {nid: {inbound, outbound_raw, outbound_normalized, clamped,
    outbound_criticality, concentration, dominant_axis, severity, tier_frozen}}
    where tier_frozen is the tier under the CURRENTLY COMMITTED frozen
    boundaries (not derived). For nodes without static axes, severity is None.
    """
    out = {}
    for nid, n in g.nodes.items():
        inbound = n.dynamic.inbound_hhi
        raw_out = raw[nid]
        norm = raw_out / fr if fr and fr > 0 else None
        clamped = norm is not None and norm > 1.0
        oc = norm
        if clamp and clamped:
            oc = 1.0
        conc = None
        if inbound is None and oc is None:
            conc = None
        elif inbound is None:
            conc = oc
        elif oc is None:
            conc = inbound
        else:
            conc = max(inbound, oc)
        dom_axis = None
        if inbound is not None and oc is not None:
            dom_axis = "inbound" if inbound >= oc else "outbound"
        elif inbound is not None:
            dom_axis = "inbound"
        elif oc is not None:
            dom_axis = "outbound"
        sub = _substitutability(n)
        lt = _lead_time(n)
        coef = _severity_coef(sub, lt)
        sev = conc * coef if (conc is not None and coef is not None) else None
        tier_frozen = _tier_from_boundaries(sev, c.chokepoint_thresholds)
        out[nid] = {
            "inbound_hhi": inbound,
            "outbound_raw": raw_out,
            "outbound_normalized": norm,
            "clamped": clamped,
            "outbound_criticality": oc,
            "concentration": conc,
            "dominant_axis": dom_axis,
            "substitutability": sub,
            "lead_time_years": lt,
            "severity_coefficient": coef,
            "severity": sev,
            "tier_under_frozen": tier_frozen,
        }
    return out


def _derivation_for(candidate_scored, sep_factor):
    """Wrap derive_thresholds and return a JSON-serializable summary."""
    severities = [(nid, r["severity"]) for nid, r in candidate_scored.items()]
    d = derive_thresholds(severities, sep_factor)
    return {
        "boundaries": {k: d.boundaries.get(k) for k in BOUNDARY_NAMES},
        "median_gap": d.median_gap,
        "separating_threshold": sep_factor * d.median_gap,
        "n_separating_gaps": len(d.separating_gaps),
        "unresolved_bands": [
            {
                "lower": b.lower, "upper": b.upper, "tiers": list(b.tiers),
                "reason": b.reason,
            }
            for b in d.unresolved_bands
        ],
        "scored_sorted": [
            {"id": nid, "severity": sev} for nid, sev in d.scored
        ],
        "gaps": [
            {"upper_id": g.upper_id, "upper_sev": g.upper_sev,
             "lower_id": g.lower_id, "lower_sev": g.lower_sev,
             "size": g.size, "midpoint": g.midpoint,
             "is_separating": g.size >= sep_factor * d.median_gap}
            for g in d.gaps
        ],
    }


def _tier_hist(candidate_scored, boundaries):
    hist = Counter()
    for r in candidate_scored.values():
        t = _tier_from_boundaries(r["severity"], boundaries)
        hist[t] += 1
    # scored + unscored total should equal graph size
    return dict(hist)


def _cluster_cut(boundaries, candidate_scored):
    """Distance from each boundary to nearest severity above/below;
    flag if inside the median-adjacent-gap window."""
    scored_sev = sorted(
        r["severity"] for r in candidate_scored.values()
        if r["severity"] is not None
    )
    # median adjacent gap
    gaps = [scored_sev[i+1] - scored_sev[i] for i in range(len(scored_sev)-1)]
    med = statistics.median(gaps) if gaps else 0.0
    out = []
    for name in BOUNDARY_NAMES:
        b = boundaries.get(name)
        if b is None:
            out.append({"boundary": name, "value": None})
            continue
        below = max((s for s in scored_sev if s < b), default=None)
        above = min((s for s in scored_sev if s > b), default=None)
        d_below = (b - below) if below is not None else None
        d_above = (above - b) if above is not None else None
        min_dist = min([x for x in (d_below, d_above) if x is not None], default=None)
        out.append({
            "boundary": name,
            "value": b,
            "nearest_below": below,
            "distance_below": d_below,
            "nearest_above": above,
            "distance_above": d_above,
            "inside_cluster": (min_dist is not None and min_dist < med),
            "median_adjacent_gap": med,
        })
    return out


def _run_maxpath_experiment():
    """§4 hypothesis test on a synthetic sub-graph — is the walk
    max-of-paths or sum-of-paths (or something else)?

    Uses the real engine's `_outbound_criticality_raw` against a graph
    with just A, B, D and three edges (A→D at w_direct, A→B at w_ab,
    B→D at w_bd). Sweeps w_bd while holding w_direct + w_ab fixed.
    """
    from app.schema.node import Node, StaticFields, DynamicFields, NodeType
    from app.schema.edge import Edge

    def _mkgraph(w_direct, w_ab, w_bd):
        g = SupplyChainGraph()
        for nid in ("test:A", "test:B", "test:D"):
            g.nodes[nid] = Node(
                id=nid, type=NodeType.COMPANY, name=nid,
                aliases=[], domains=["ai"], layer=None, sub_category=None,
                description="test", static=StaticFields(),
                dynamic=DynamicFields(),
            )
        edges_def = [
            ("test:e-ad", "test:A", "test:D", w_direct),
            ("test:e-ab", "test:A", "test:B", w_ab),
            ("test:e-bd", "test:B", "test:D", w_bd),
        ]
        for eid, s, t, w in edges_def:
            g.edges[eid] = Edge(
                id=eid, source_id=s, target_id=t,
                type=EdgeType.SUPPLIES, static={}, input_share=w,
                output_share=None, supply_category="foundry_wafers",
            )
        g._reindex()
        return g

    # Use the same scoring config's walk params
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    decay = c.concentration_outbound_decay
    max_hops = c.concentration_outbound_max_hops
    min_influence = c.concentration_outbound_min_influence
    share_field = c.outbound_share_field
    fallback = c.outbound_fallback_to_input_share

    # Correction: the walk applies decay^depth per hop, so the actual
    # threshold for "indirect beats direct" is
    #     w_ab × w_bd × decay² > w_direct × decay
    # → w_bd > w_direct / (w_ab × decay).
    # Choose parameters where the sweep CAN cross this threshold within
    # w_bd ∈ [0, 1]. With w_direct=0.20, w_ab=0.90, decay=0.7:
    #     w_bd_critical = 0.20 / (0.90 × 0.7) = 0.317…
    # so a sweep 0.05 → 0.95 straddles it cleanly.
    w_direct = 0.20
    w_ab = 0.90
    w_bd_critical = w_direct / (w_ab * decay)
    sweep = [0.05, 0.10, 0.20, 0.30, 0.32, 0.35, 0.40, 0.50, 0.70, 0.90, 0.95]
    rows = []
    for w_bd in sweep:
        g = _mkgraph(w_direct, w_ab, w_bd)
        raw = _outbound_criticality_raw(
            "test:A", g, decay, max_hops, min_influence,
            share_field=share_field, fallback=fallback,
        )
        # decay-adjusted influence comparison
        direct_infl = w_direct * decay
        indirect_infl = w_ab * w_bd * (decay ** 2)
        rows.append({
            "w_direct": w_direct,
            "w_ab": w_ab,
            "w_bd": w_bd,
            "decay": decay,
            "direct_influence": direct_infl,
            "indirect_influence": indirect_infl,
            "indirect_beats_direct": indirect_infl > direct_infl,
            "A_raw_outbound": raw,
        })
    # A raw = sqrt(best_infl[D]² + best_infl[B]²)
    # best_infl[B] = w_ab × decay (constant across sweep since w_ab is fixed)
    # best_infl[D] = max(direct_infl, indirect_infl)
    #
    # Verdict:
    #   max-of-paths: A_raw stays flat at sqrt(direct² + (w_ab×decay)²)
    #     while indirect_infl < direct_infl, then rises when indirect > direct.
    #   sum-of-paths: A_raw would rise from the first w_bd move.
    #   something-else: neither pattern.
    below = [r for r in rows if not r["indirect_beats_direct"]]
    above = [r for r in rows if r["indirect_beats_direct"]]
    below_vals = [r["A_raw_outbound"] for r in below]
    above_vals = [r["A_raw_outbound"] for r in above]
    below_flat = (
        len(set(round(v, 10) for v in below_vals)) <= 1
    )
    above_monotone_up = all(
        above_vals[i+1] >= above_vals[i] - 1e-10
        for i in range(len(above_vals) - 1)
    )
    step_at_boundary = (
        len(above_vals) > 0 and len(below_vals) > 0
        and above_vals[0] > below_vals[-1] - 1e-10
    )
    if below_flat and above_monotone_up and step_at_boundary:
        verdict = "max_of_paths_confirmed"
    elif not below_flat:
        verdict = "sum_of_paths_or_other"
    else:
        verdict = "inconclusive"
    return {
        "null_hypothesis": (
            "max-of-paths: A's raw contribution to D holds at "
            "sqrt(direct_influence² + (w_ab×decay)²) while "
            "indirect_influence < direct_influence, then rises when the "
            "indirect (decay-adjusted) influence exceeds the direct."
        ),
        "w_bd_critical": w_bd_critical,
        "params_fixed": {
            "w_direct": w_direct, "w_ab": w_ab, "decay": decay,
        },
        "sweep": rows,
        "verdict": verdict,
    }


def main() -> None:
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for ev in g.events.values():
        propagate_event(ev, g, c)

    # Raw outbound per node — this is fixed_reference-independent.
    raw = {
        nid: _outbound_criticality_raw(
            nid, g, c.concentration_outbound_decay,
            c.concentration_outbound_max_hops,
            c.concentration_outbound_min_influence,
            share_field=c.outbound_share_field,
            fallback=c.outbound_fallback_to_input_share,
        )
        for nid in g.nodes
    }

    committed_fr = c.outbound_fixed_reference
    copper_raw = raw["mineral:copper"]

    candidates = [
        {"id": "FR-A", "label": "Status quo (ASML anchor, frozen K.1 value)",
         "fixed_reference": committed_fr, "clamp": True},
        {"id": "FR-B", "label": "Re-anchor to copper's current raw",
         "fixed_reference": copper_raw, "clamp": True},
        {"id": "FR-C", "label": "Headroom constant 2.5",
         "fixed_reference": 2.5, "clamp": True},
        {"id": "FR-D", "label": "Frozen value, clamp DISABLED",
         "fixed_reference": committed_fr, "clamp": False},
    ]

    # Score committed graph (for delta reference)
    committed_scored = {
        nid: {
            "severity": n.dynamic.baseline_severity,
            "tier": n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else "unscored",
            "concentration": n.dynamic.concentration,
            "inbound_hhi": n.dynamic.inbound_hhi,
            "outbound_criticality": n.dynamic.outbound_criticality,
        }
        for nid, n in g.nodes.items()
    }

    sep_factors = [2.0, 2.5, 3.0, 3.5, 4.0]

    candidate_results = []
    reproducibility_check = {}
    for cand in candidates:
        # Two independent runs to check determinism (§6(6))
        scored_a = _score_under_candidate(g, c, raw, cand["fixed_reference"], cand["clamp"])
        scored_b = _score_under_candidate(g, c, raw, cand["fixed_reference"], cand["clamp"])
        # Compare
        mismatches = 0
        for nid in scored_a:
            for k in ("severity", "concentration", "outbound_criticality"):
                if scored_a[nid][k] != scored_b[nid][k]:
                    mismatches += 1
        reproducibility_check[cand["id"]] = {"mismatches": mismatches}

        # Derivation at 3.0 (primary)
        deriv = _derivation_for(scored_a, 3.0)
        tier_hist_derived = _tier_hist(scored_a, deriv["boundaries"])
        tier_hist_frozen = Counter(r["tier_under_frozen"] for r in scored_a.values())

        # Movement vs committed
        moved_under_frozen = []
        for nid, r in scored_a.items():
            committed_tier = committed_scored[nid]["tier"]
            if r["tier_under_frozen"] != committed_tier:
                moved_under_frozen.append({
                    "id": nid,
                    "severity_committed": committed_scored[nid]["severity"],
                    "severity_candidate": r["severity"],
                    "tier_committed": committed_tier,
                    "tier_candidate": r["tier_under_frozen"],
                })
        moved_under_derived = []
        for nid, r in scored_a.items():
            committed_tier = committed_scored[nid]["tier"]
            derived_tier = _tier_from_boundaries(r["severity"], deriv["boundaries"])
            if derived_tier != committed_tier:
                moved_under_derived.append({
                    "id": nid,
                    "severity_committed": committed_scored[nid]["severity"],
                    "severity_candidate": r["severity"],
                    "tier_committed": committed_tier,
                    "tier_candidate": derived_tier,
                })

        # Cluster cut against derived boundaries at 3.0
        cluster_cut = _cluster_cut(deriv["boundaries"], scored_a)

        # Sep-factor sweep — boundaries + tier hist at each factor
        sep_strip = []
        for sf in sep_factors:
            d = _derivation_for(scored_a, sf)
            hist = _tier_hist(scored_a, d["boundaries"])
            sep_strip.append({
                "separation_factor": sf,
                "boundaries": d["boundaries"],
                "tier_histogram": hist,
                "n_separating_gaps": d["n_separating_gaps"],
                "n_unresolved_bands": len(d["unresolved_bands"]),
                "unresolved_bands": d["unresolved_bands"],
            })

        # Summary metrics
        n_clamped = sum(1 for r in scored_a.values() if r["clamped"])
        flipped_axis = 0
        for nid, r in scored_a.items():
            base_dom = "inbound" if (committed_scored[nid]["inbound_hhi"] or 0) >= (committed_scored[nid]["outbound_criticality"] or 0) else "outbound"
            if r["dominant_axis"] and r["dominant_axis"] != base_dom:
                flipped_axis += 1
        sev_values = [r["severity"] for r in scored_a.values() if r["severity"] is not None]

        # Per-node matrix (JSON-friendly)
        node_matrix = []
        for nid in sorted(scored_a):
            r = scored_a[nid]
            if r["severity"] is None:
                continue
            node_matrix.append({
                "id": nid,
                "inbound_hhi": r["inbound_hhi"],
                "outbound_raw": r["outbound_raw"],
                "outbound_normalized": r["outbound_normalized"],
                "clamped": r["clamped"],
                "outbound_criticality": r["outbound_criticality"],
                "concentration": r["concentration"],
                "dominant_axis": r["dominant_axis"],
                "severity": r["severity"],
                "severity_delta_vs_committed": (
                    (r["severity"] or 0) - (committed_scored[nid]["severity"] or 0)
                    if r["severity"] is not None else None
                ),
                "tier_under_frozen": r["tier_under_frozen"],
                "tier_committed": committed_scored[nid]["tier"],
            })

        candidate_results.append({
            "id": cand["id"],
            "label": cand["label"],
            "fixed_reference": cand["fixed_reference"],
            "clamp_enabled": cand["clamp"],
            "n_clamped": n_clamped,
            "n_flipped_dominant_axis": flipped_axis,
            "n_tier_changes_under_frozen": len(moved_under_frozen),
            "n_tier_changes_under_derived": len(moved_under_derived),
            "severity_min": min(sev_values) if sev_values else None,
            "severity_max": max(sev_values) if sev_values else None,
            "severity_median": statistics.median(sev_values) if sev_values else None,
            "tier_histogram_frozen": dict(tier_hist_frozen),
            "tier_histogram_derived": tier_hist_derived,
            "derivation_at_3.0": deriv,
            "moved_under_frozen": moved_under_frozen,
            "moved_under_derived": moved_under_derived,
            "cluster_cut_derived": cluster_cut,
            "separation_factor_sweep": sep_strip,
            "node_matrix": node_matrix,
        })

    maxpath = _run_maxpath_experiment()

    out = {
        "head_sha_at_open": None,  # filled after commit
        "committed_state_summary": {
            "n_nodes": len(g.nodes),
            "n_edges": len(g.edges),
            "n_scored": sum(1 for n in g.nodes.values() if n.dynamic.baseline_severity is not None),
            "boundaries_frozen": dict(c.chokepoint_thresholds),
            "fixed_reference_frozen": c.outbound_fixed_reference,
            "threshold_mode": c.threshold_mode,
            "aggregator_method": c.inbound_per_stage_method,
            "aggregator_eps_configured": c.inbound_per_stage_eps,
            "aggregator_eps_applied": (
                c.inbound_per_stage_eps
                if c.inbound_per_stage_method == "noisy_or_eps" else None
            ),
        },
        "raw_outbound_per_node": raw,
        "committed_scored": committed_scored,
        "candidates": candidate_results,
        "reproducibility_check": reproducibility_check,
        "max_path_experiment": maxpath,
    }
    out_path = REPO / "docs" / "generated" / "pass_t_facts.json"
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
