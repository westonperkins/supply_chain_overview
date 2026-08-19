# Replay — J-2024-09-asml-export

**Headline.** Netherlands expands ASML DUV export licence to include additional immersion tools for shipments to China

**Timestamp.** 2024-09-06T00:00:00Z

**Origin(s).**
- `company:asml` (company, ASML) — SCORED origin; baseline_severity=0.382, baseline_tier=moderate
- `country_region:netherlands` (country_region, Netherlands) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.000`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.0, substitutability_delta=0.0, lead_time_delta=0.0

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| company:asml | 0 | 0.000 | 0.382 | 0.382 | +0.000 | — |
| country_region:netherlands | 0 | 0.000 | ∅ | ∅ | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Propagation path for top-3

- (no cascade — see Phase B grading for interpretation)

