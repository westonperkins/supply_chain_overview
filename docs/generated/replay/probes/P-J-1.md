> **PROBE.** This is an injected-magnitude counterfactual — the axes on this record are not an estimate of any real event's impact. Probes do not enter summary.md, ranking, or outcomes.json. See Pass J.1 §6 and the probe's `notes` field for rationale.

# Replay — P-J-1

**Headline.** PROBE — Nexperia (Oct 2025) with injected concentration_delta=0.20

**Timestamp.** 2025-10-13T00:00:00Z

**Origin(s).**
- `country_region:netherlands` (country_region, Netherlands) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.000`

**Origin scored?** `False` — walk seeded from concentration × magnitude × confidence (see Pass D §4)

**Authored axes (Phase A).** concentration_delta=0.2, substitutability_delta=0.0, lead_time_delta=0.0

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:netherlands | 0 | 0.000 | ∅ | ∅ | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Propagation path for top-3

- (no cascade — see Phase B grading for interpretation)

