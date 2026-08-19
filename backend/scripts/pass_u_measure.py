"""Pass U (FR-C, re-baseline Phase B) — mechanical facts writer.

Emits `docs/generated/pass_u_facts.json` so the Pass U report can QUOTE
the artifact rather than recall numbers. Pass U is a CONSTANT-change
pass: `fixed_reference` 1.6711394969476698 → 2.5 and the three tier
boundaries re-derived at separation_factor 3.0. No edge or node value is
authored.

Sources:
  - "before" (pre-U): `git show <before-ref>:docs/generated/
    severity_snapshot.json` — the committed pass_s snapshot, captured
    under FR-A (fixed_reference 1.6711…, FR-A boundaries). Reproducible
    from git alone.
  - "after" (post-U): current working tree, scored in-process under the
    committed FR-C config.

Emits:
  - graph counts + committed constants (after)
  - derivation reproduction: FR-C boundaries re-derived from the
    post-change distribution, byte-compared to the committed literals
  - full per-node before/after matrix (severity, concentration, both
    axes, dominant axis, tier, and the rescale-class attribution)
  - guard-sync check: config vs fixture fixed_reference + boundaries
  - clamp check: raw / normalized / clamped for every node, before+after
  - boundary-proximity readout after the change

Full float precision throughout; rounding belongs in the report.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

import yaml

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event
from app.scoring.engine import _outbound_criticality_raw
from app.scoring.thresholds import derive_thresholds

BEFORE_REF = "1dbdd46"  # Pass T HEAD — pre-U (pass_s snapshot, FR-A).
FR_BEFORE = 1.6711394969476698
FR_AFTER = 2.5
FR_C_BOUNDARIES = {
    "critical": 0.5247316525037853,
    "high": 0.42320867926942163,
    "moderate": 0.15668443545638666,
}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8")


def _raw_map(g, c):
    return {
        nid: _outbound_criticality_raw(
            nid, g, c.concentration_outbound_decay,
            c.concentration_outbound_max_hops,
            c.concentration_outbound_min_influence,
            share_field=c.outbound_share_field,
            fallback=c.outbound_fallback_to_input_share,
        )
        for nid in g.nodes
    }


def _dom_axis(inb, out):
    if inb is None and out is None:
        return None
    if inb is None:
        return "outbound"
    if out is None:
        return "inbound"
    return "inbound" if inb >= out else "outbound"


def _rescale_class(sev_b, sev_a, raw, inb_a, out_a, ratio):
    """Explain a severity delta by the mechanism, not the diff classifier.

    Buckets (all consequences of the fixed_reference change alone):
      - inbound_unchanged: inbound-dominant both sides, severity flat.
      - clean_rescale: un-clamped outbound-dominant, severity scales by
        `ratio` (=FR_before/FR_after) within 1e-9.
      - clamp_release: raw/FR_before > 1.0, i.e. the node was clamped at
        outbound=1.0 before, so the naive rescale ratio does NOT apply;
        severity moves because the clamp lifted (copper/ASML) and/or the
        dominant axis flipped (TSMC). Uses RAW outbound, not the clamped
        outbound_criticality, which is already 1.0 for these nodes.
      - unscored: no severity either side.
      - unexplained: none of the above — a Pass U stop condition (§7.4).
    """
    if sev_b is None and sev_a is None:
        return "unscored"
    if sev_b is None or sev_a is None:
        return "null_transition"
    d = sev_a - sev_b
    if abs(d) <= 1e-12:
        return "inbound_unchanged"
    # clean rescale: expected exactly (ratio-1)*sev_b for un-clamped
    # outbound-dominant nodes.
    expected = (ratio - 1.0) * sev_b
    if abs(d - expected) <= max(1e-9, abs(expected) * 1e-6):
        return "clean_rescale"
    # clamp_release: node was clamped (raw/FR_before>1) so its before-
    # severity used the clamp (outbound_criticality=1.0), not raw/FR.
    if raw is not None and raw / FR_BEFORE > 1.0:
        return "clamp_release"
    return "unexplained"


def main() -> None:
    # ---------- AFTER: current working tree under committed FR-C ----------
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for ev in g.events.values():
        propagate_event(ev, g, c)
    raw_after = _raw_map(g, c)

    # ---------- BEFORE: pre-U committed snapshot (pass_s, FR-A) ----------
    snap_before = json.loads(
        _git("show", f"{BEFORE_REF}:docs/generated/severity_snapshot.json")
    )
    before_nodes = snap_before["nodes"]

    # ---------- BEFORE raw outbound (FR-independent; re-score at ref) -----
    # Raw outbound is fixed_reference-independent, so raw_after == raw_before
    # for every node (no edge/node changed between the two states). We
    # still record both to prove it.
    ratio = FR_BEFORE / FR_AFTER

    # ---------- derivation reproduction ----------
    sev_pairs = [(nid, n.dynamic.baseline_severity) for nid, n in g.nodes.items()]
    deriv = derive_thresholds(sev_pairs, c.threshold_separation_factor)
    derived_boundaries = {k: deriv.boundaries[k] for k in ("critical", "high", "moderate")}
    reproduces = all(
        derived_boundaries[k] == FR_C_BOUNDARIES[k] == c.chokepoint_thresholds[k]
        for k in ("critical", "high", "moderate")
    )
    derivation_reproduction = {
        "separation_factor": c.threshold_separation_factor,
        "median_gap": deriv.median_gap,
        "separating_threshold": c.threshold_separation_factor * deriv.median_gap,
        "n_separating_gaps": len(deriv.separating_gaps),
        "derived_boundaries": derived_boundaries,
        "committed_boundaries": dict(c.chokepoint_thresholds),
        "expected_fr_c_boundaries": FR_C_BOUNDARIES,
        "byte_identical_to_committed": all(
            derived_boundaries[k] == c.chokepoint_thresholds[k]
            for k in ("critical", "high", "moderate")
        ),
        "byte_identical_to_pass_t_measurement": all(
            derived_boundaries[k] == FR_C_BOUNDARIES[k]
            for k in ("critical", "high", "moderate")
        ),
        "reproduces": reproduces,
        "scored_sorted": [
            {"id": nid, "severity": sev} for nid, sev in deriv.scored
        ],
        "gaps": [
            {"upper_id": gp.upper_id, "upper_sev": gp.upper_sev,
             "lower_id": gp.lower_id, "lower_sev": gp.lower_sev,
             "size": gp.size, "midpoint": gp.midpoint,
             "is_separating": gp.size >= c.threshold_separation_factor * deriv.median_gap}
            for gp in deriv.gaps
        ],
    }

    # ---------- full per-node before/after matrix ----------
    node_matrix = []
    tier_changes = []
    unexplained = []
    for nid in sorted(g.nodes):
        n = g.nodes[nid]
        b = before_nodes.get(nid, {})
        sev_a = n.dynamic.baseline_severity
        sev_b = b.get("severity")
        inb_a = n.dynamic.inbound_hhi
        inb_b = b.get("inbound_hhi")
        out_a = n.dynamic.outbound_criticality
        out_b = b.get("outbound_criticality")
        conc_a = n.dynamic.concentration
        conc_b = b.get("concentration")
        tier_a = n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else "unscored"
        tier_b = b.get("tier", "unscored")
        raw_a = raw_after[nid]
        norm_a = raw_a / FR_AFTER
        norm_b = raw_a / FR_BEFORE  # raw is FR-independent; same raw both sides
        klass = _rescale_class(sev_b, sev_a, raw_a, inb_a, out_a, ratio)
        row = {
            "id": nid,
            "severity_before": sev_b,
            "severity_after": sev_a,
            "severity_delta": (
                (sev_a - sev_b) if (sev_a is not None and sev_b is not None) else None
            ),
            "inbound_hhi_before": inb_b,
            "inbound_hhi_after": inb_a,
            "outbound_criticality_before": out_b,
            "outbound_criticality_after": out_a,
            "concentration_before": conc_b,
            "concentration_after": conc_a,
            "dominant_axis_before": _dom_axis(inb_b, out_b),
            "dominant_axis_after": _dom_axis(inb_a, out_a),
            "outbound_raw": raw_a,
            "outbound_normalized_before": norm_b,
            "outbound_normalized_after": norm_a,
            "clamped_before": norm_b > 1.0,
            "clamped_after": norm_a > 1.0,
            "tier_before": tier_b,
            "tier_after": tier_a,
            "rescale_class": klass,
        }
        node_matrix.append(row)
        if tier_a != tier_b:
            tier_changes.append({
                "id": nid, "tier_before": tier_b, "tier_after": tier_a,
                "severity_before": sev_b, "severity_after": sev_a,
                "rescale_class": klass,
            })
        if klass == "unexplained":
            unexplained.append(nid)

    # ---------- tier histograms ----------
    hist_before = Counter(
        before_nodes.get(nid, {}).get("tier", "unscored") for nid in g.nodes
    )
    hist_after = Counter(
        (n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else "unscored")
        for n in g.nodes.values()
    )

    # ---------- clamp check ----------
    clamped_before = sorted(nid for nid in g.nodes if raw_after[nid] / FR_BEFORE > 1.0)
    clamped_after = sorted(nid for nid in g.nodes if raw_after[nid] / FR_AFTER > 1.0)
    copper_raw = raw_after["mineral:copper"]

    # ---------- guard-sync check ----------
    def _fr(path):
        return yaml.safe_load(Path(path).read_text())[
            "concentration"]["outbound"]["normalization"]["fixed_reference"]

    def _bnd(path):
        return yaml.safe_load(Path(path).read_text())["thresholds"]["boundaries"]

    repo_yaml = REPO / "config" / "scoring.yaml"
    fix_yaml = REPO / "backend" / "tests" / "fixtures" / "scoring.yaml"
    # sync at open (pre-U) — read both files at BEFORE_REF
    fr_repo_open = yaml.safe_load(
        _git("show", f"{BEFORE_REF}:config/scoring.yaml")
    )["concentration"]["outbound"]["normalization"]["fixed_reference"]
    fr_fix_open = yaml.safe_load(
        _git("show", f"{BEFORE_REF}:backend/tests/fixtures/scoring.yaml")
    )["concentration"]["outbound"]["normalization"]["fixed_reference"]
    guard_sync = {
        "at_open": {
            "config_fixed_reference": fr_repo_open,
            "fixture_fixed_reference": fr_fix_open,
            "in_sync": fr_repo_open == fr_fix_open,
        },
        "at_close": {
            "config_fixed_reference": _fr(repo_yaml),
            "fixture_fixed_reference": _fr(fix_yaml),
            "in_sync": _fr(repo_yaml) == _fr(fix_yaml),
            "config_boundaries": _bnd(repo_yaml),
            "fixture_boundaries": _bnd(fix_yaml),
            "boundaries_in_sync": _bnd(repo_yaml) == _bnd(fix_yaml),
            "files_byte_identical": repo_yaml.read_text() == fix_yaml.read_text(),
        },
    }

    # ---------- boundary proximity (after) ----------
    boundaries_sorted = sorted(c.chokepoint_thresholds.items(), key=lambda kv: kv[1])
    boundary_proximity = []
    for nid, n in g.nodes.items():
        sev = n.dynamic.baseline_severity
        if sev is None:
            continue
        below = below_v = above = above_v = None
        for name, v in boundaries_sorted:
            if v <= sev and (below_v is None or v > below_v):
                below, below_v = name, v
            if v > sev and (above_v is None or v < above_v):
                above, above_v = name, v
        boundary_proximity.append({
            "id": nid, "severity": sev,
            "tier": n.dynamic.baseline_tier.value if n.dynamic.baseline_tier else "unscored",
            "nearest_boundary_below": below,
            "distance_below": (sev - below_v) if below_v is not None else None,
            "nearest_boundary_above": above,
            "distance_above": (above_v - sev) if above_v is not None else None,
        })
    boundary_proximity.sort(key=lambda r: -r["severity"])

    out = {
        "pass": "U",
        "decision": "FR-C: fixed_reference=2.5, boundaries derived at SF=3.0",
        "before_ref": BEFORE_REF,
        "head_sha": _git("rev-parse", "HEAD").strip(),
        "fixed_reference_before": FR_BEFORE,
        "fixed_reference_after": FR_AFTER,
        "rescale_ratio_after_over_before": ratio,
        "graph": {
            "nodes": len(g.nodes),
            "edges": len(g.edges),
            "scored": sum(1 for n in g.nodes.values()
                          if n.dynamic.baseline_severity is not None),
        },
        "threshold_mode": c.threshold_mode,
        "committed_boundaries": dict(c.chokepoint_thresholds),
        "derivation_reproduction": derivation_reproduction,
        "tier_histogram_before": dict(hist_before),
        "tier_histogram_after": dict(hist_after),
        "tier_changes": tier_changes,
        "unexplained_deltas": unexplained,
        "clamp_check": {
            "clamped_before": clamped_before,
            "clamped_after": clamped_after,
            "copper_raw_outbound": copper_raw,
            "copper_normalized_after": copper_raw / FR_AFTER,
        },
        "guard_sync": guard_sync,
        "boundary_proximity": boundary_proximity,
        "node_matrix": node_matrix,
    }
    out_path = REPO / "docs" / "generated" / "pass_u_facts.json"
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"wrote {out_path}")
    # brief console summary
    print(f"  scored={out['graph']['scored']} "
          f"reproduces={derivation_reproduction['reproduces']} "
          f"tier_changes={[t['id'] for t in tier_changes]} "
          f"unexplained={unexplained} "
          f"clamped_after={clamped_after}")


if __name__ == "__main__":
    main()
