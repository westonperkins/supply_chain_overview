"""Pass M validation script — runs the 6 candidate aggregators × 2
min_suppliers values through the REAL engine.

MEASUREMENT ONLY. Writes to docs/generated/aggregator_engine_validation.md,
epsilon_sweep.md, count_aware_cost.md. Does NOT touch data/, config/,
or the snapshot. Does NOT decide D4 / D4a / ε.

Every run uses `refresh_all_derived(..., aggregator_method=..., eps=...,
min_suppliers_override=...)` — the seam added in Pass M §2 that defaults
to the committed HHI path, so this script cannot affect any committed
artifact.
"""
from __future__ import annotations

import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived
from app.scoring.thresholds import derive_thresholds
from app.scoring.engine import compute_severity, axes_for_severity

DOCS = REPO / "docs" / "generated"

# ---------------------------------------------------------------- #
# The 6 candidates × 2 min_suppliers matrix                        #
# ---------------------------------------------------------------- #

# Each entry: (label, method, eps or None) — RMS ignores eps.
CANDIDATES = [
    ("hhi",         "hhi",          None),
    ("noisy_or",    "noisy_or",     None),
    ("nor_eps_001", "noisy_or_eps", 0.01),
    ("nor_eps_005", "noisy_or_eps", 0.05),
    ("rms",         "rms",          None),
]
# count-aware is an ordering wrapper over one of the above, not a
# separate aggregator (the scalar is nor_eps_001). Emitted as a
# projection in §5 rather than as a new engine run.

MIN_SUPPLIERS_VALUES = [2, 1]  # current, D4a


def load_graph_and_config():
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    return g, c


def run_candidate(g, c, method, eps, min_supp):
    """Run a candidate through the real engine and return per-node
    concentration + severity + tier data."""
    refresh_all_derived(
        g, c,
        aggregator_method=method,
        aggregator_eps=eps if eps is not None else 0.01,
        min_suppliers_override=min_supp,
        stage_min_suppliers_override=min_supp,
    )
    rows = []
    for n in g.nodes.values():
        rows.append({
            "id": n.id,
            "inbound_hhi": n.dynamic.inbound_hhi,
            "outbound_criticality": n.dynamic.outbound_criticality,
            "concentration": n.dynamic.concentration,
            "baseline_severity": n.dynamic.baseline_severity,
            "baseline_tier": (
                n.dynamic.baseline_tier.value
                if n.dynamic.baseline_tier else None
            ),
        })
    return rows


def derive_boundaries(rows, c):
    """Run derive_thresholds on the scored severities from a candidate
    run and return the derivation."""
    severities = [(r["id"], r["baseline_severity"]) for r in rows]
    return derive_thresholds(severities, c.threshold_separation_factor)


def summarize(rows, derivation, label):
    """Extract the summary statistics one candidate needs to report."""
    scored = [r for r in rows if r["baseline_severity"] is not None]
    scored.sort(key=lambda r: -r["baseline_severity"])
    inbound_vals = [r["inbound_hhi"] for r in rows if r["inbound_hhi"] is not None]
    at_1 = sum(1 for v in inbound_vals if v >= 1.0 - 1e-9)
    ge_099 = sum(1 for v in inbound_vals if v >= 0.99)
    from collections import Counter
    tier_hist = Counter(
        r.get("baseline_tier") or "unscored" for r in rows
    )
    seps = len(derivation.separating_gaps)
    return {
        "label": label,
        "at_1": at_1,
        "ge_099": ge_099,
        "median_scored_sev": median([r["baseline_severity"] for r in scored]) if scored else None,
        "tier_hist": dict(tier_hist),
        "separating_gaps": seps,
        "boundaries": dict(derivation.boundaries),
        "unresolved_bands_count": len(derivation.unresolved_bands),
        "rf_power": next((r for r in scored if r["id"] == "product:rf_power_semis"), None),
        "hbm": next((r for r in scored if r["id"] == "product:hbm"), None),
        "ndfeb": next((r for r in scored if r["id"] == "product:ndfeb_magnets"), None),
        "arm_core_ip": next((r for r in scored if r["id"] == "product:arm_core_ip"), None),
        "top_5": [(r["id"], r["baseline_severity"]) for r in scored[:5]],
        "scored_count": len(scored),
    }


def compute_current_matrix():
    g, c = load_graph_and_config()
    results = {}
    for label, method, eps in CANDIDATES:
        for min_supp in MIN_SUPPLIERS_VALUES:
            key = f"{label}_min{min_supp}"
            # Reload graph each iteration so no state leaks between runs
            g_run = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
            rows = run_candidate(g_run, c, method, eps, min_supp)
            deriv = derive_boundaries(rows, c)
            results[key] = summarize(rows, deriv, key)
    return results


# ---------------------------------------------------------------- #
# Projected run — with K.2.2 §2 dependency values overlaid          #
# ---------------------------------------------------------------- #

# K.2.2 §2.2 authored dependency-basis candidate values. Overlaid on a
# graph COPY only; never written to data/ai/edges.json. Every value
# below is analysis-basis authoring the K.2.2 §2.5 audit trail
# defends; if honest dep value is not determinable from committed
# source_notes, the edge is left at its current value (marked as
# `undeterminable` in K.2.2 §2.2).
PROJECTED_EDGE_OVERRIDES = {
    # (source_id, target_id, edge_type, supply_category or None) → new input_share
    # NdFeB — already dep-authored in K.1
    # NVIDIA input_to co-critical HBM/CoWoS
    ("product:hbm", "company:nvidia", "input_to", None): 0.85,
    ("product:cowos_packaging", "company:nvidia", "input_to", None): 0.85,
    # AMD
    ("product:hbm", "company:amd", "input_to", None): 0.85,
    ("product:cowos_packaging", "company:amd", "input_to", None): 0.85,
    # Broadcom
    ("product:hbm", "company:broadcom", "input_to", None): 0.75,
    ("product:cowos_packaging", "company:broadcom", "input_to", None): 0.75,
    ("product:rf_power_semis", "company:broadcom", "input_to", None): 0.40,
    # Google
    ("product:hbm", "company:google", "input_to", None): 0.75,
    ("product:cowos_packaging", "company:google", "input_to", None): 0.75,
    # Amazon
    ("product:hbm", "company:amazon", "input_to", None): 0.75,
    # Microsoft
    ("product:hbm", "company:microsoft", "input_to", None): 0.75,
    # Meta
    ("product:hbm", "company:meta", "input_to", None): 0.75,
    # ge_vernova, siemens_energy — projected higher on copper (K.2.2 §2.5)
    ("mineral:copper", "company:ge_vernova", "input_to", None): 0.90,
    ("product:rf_power_semis", "company:ge_vernova", "input_to", None): 0.20,
    ("mineral:copper", "company:siemens_energy", "input_to", None): 0.90,
    ("product:rf_power_semis", "company:siemens_energy", "input_to", None): 0.20,
    # vertiv
    ("product:ndfeb_magnets", "company:vertiv", "input_to", None): 0.85,
    ("mineral:copper", "company:vertiv", "input_to", None): 0.75,
    ("product:rf_power_semis", "company:vertiv", "input_to", None): 0.30,
    # openai / xai gpu_accelerators
    ("company:nvidia", "company:openai", "supplies", "gpu_accelerators"): 0.95,
    ("company:amd", "company:openai", "supplies", "gpu_accelerators"): 0.20,
    ("company:nvidia", "company:xai", "supplies", "gpu_accelerators"): 0.95,
    ("company:amd", "company:xai", "supplies", "gpu_accelerators"): 0.20,
    # Samsung input_to (undeterminable per K.2.2 §2.5) — LEFT AT CURRENT
}


def apply_projected_overrides(g):
    """Overlay K.2.2 §2 authored dep values on a graph COPY.
    Every override is labelled projected in the report; nothing writes
    to data/. Returns count of edges overridden and count of overrides
    that matched no edge (data drift check)."""
    overridden = 0
    unmatched = 0
    for (src, tgt, etype, cat), new_v in PROJECTED_EDGE_OVERRIDES.items():
        found = False
        for e in list(g.edges.values()):
            if e.source_id != src or e.target_id != tgt: continue
            if e.type.value != etype: continue
            if cat is not None and (e.supply_category or None) != cat:
                continue
            e.input_share = new_v
            overridden += 1
            found = True
            break
        if not found:
            unmatched += 1
    return overridden, unmatched


def compute_projected_matrix():
    _, c = load_graph_and_config()
    results = {}
    override_count = 0
    unmatched_count = 0
    for label, method, eps in CANDIDATES:
        for min_supp in MIN_SUPPLIERS_VALUES:
            key = f"{label}_min{min_supp}"
            g_run = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
            over, unm = apply_projected_overrides(g_run)
            if override_count == 0:
                override_count, unmatched_count = over, unm
            rows = run_candidate(g_run, c, method, eps, min_supp)
            deriv = derive_boundaries(rows, c)
            results[key] = summarize(rows, deriv, key)
    return results, override_count, unmatched_count


# ---------------------------------------------------------------- #
# ε sweep                                                           #
# ---------------------------------------------------------------- #

EPS_VALUES = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10]


def epsilon_sweep(projected=False):
    """Sweep ε at min_suppliers=1 (D4a — the pairing K.2.2 recommended).
    Returns per-ε summary."""
    _, c = load_graph_and_config()
    results = []
    for eps in EPS_VALUES:
        g_run = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
        if projected:
            apply_projected_overrides(g_run)
        rows = run_candidate(g_run, c, "noisy_or_eps", eps, 1)
        deriv = derive_boundaries(rows, c)
        s = summarize(rows, deriv, f"nor_eps_{eps}")
        s["eps"] = eps
        # Ordering — save the sorted (id, severity) list for ordering-change check
        scored = [r for r in rows if r["baseline_severity"] is not None]
        scored.sort(key=lambda r: (-r["baseline_severity"], r["id"]))
        s["ordering"] = [r["id"] for r in scored]
        results.append(s)
    return results


# ---------------------------------------------------------------- #
# Main                                                               #
# ---------------------------------------------------------------- #

if __name__ == "__main__":
    print("Running candidate matrix on current graph…")
    current = compute_current_matrix()

    print("Running candidate matrix on projected graph (K.2.2 §2 overrides)…")
    projected, over_count, unmatched = compute_projected_matrix()
    print(f"  projected overrides applied: {over_count}, unmatched: {unmatched}")

    print("Running ε sweep on current graph (min_supp=1)…")
    eps_current = epsilon_sweep(projected=False)
    print("Running ε sweep on projected graph (min_supp=1)…")
    eps_projected = epsilon_sweep(projected=True)

    # Emit intermediate JSON so the writer can consume it deterministically
    out = {
        "current": current,
        "projected": projected,
        "projected_override_count": over_count,
        "projected_unmatched_count": unmatched,
        "epsilon_current": eps_current,
        "epsilon_projected": eps_projected,
    }
    (DOCS / "aggregator_validation_data.json").write_text(
        json.dumps(out, indent=2, default=str) + "\n"
    )
    print(f"\nWrote {DOCS / 'aggregator_validation_data.json'}")
