# Replay — J-2024-11-hynix-hbm

**Headline.** SK Hynix confirms HBM3E capacity sold out through 2025; HBM4 volumes largely committed

**Timestamp.** 2024-11-04T00:00:00Z

**Origin(s).**
- `company:sk_hynix` (company, SK Hynix) — SCORED origin; baseline_severity=0.263, baseline_tier=moderate
- `product:hbm` (product, High Bandwidth Memory (HBM)) — SCORED origin; baseline_severity=0.301, baseline_tier=moderate

**Origin scale** (event severity attributed to strongest origin): `0.093`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.05, substitutability_delta=0.15, lead_time_delta=0.25

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| company:sk_hynix | 0 | 0.093 | 0.263 | 0.331 | +0.068 | — |
| product:hbm | 0 | 0.052 | 0.301 | 0.337 | +0.036 | — |
| company:nvidia | 1 | 0.008 | 0.358 | 0.363 | +0.005 | — |
| company:amd | 1 | 0.004 | ∅ | 0.004 | +0.004 | — |
| company:broadcom | 1 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:meta | 1 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:google | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:amazon | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:microsoft | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:xai | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:openai | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:colossus | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:stargate_abilene | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| company:sk_hynix | company | 0.263 | 0.331 | +0.068 | — |
| product:hbm | product | 0.301 | 0.337 | +0.036 | — |
| company:nvidia | company | 0.358 | 0.363 | +0.005 | — |
| company:amd | company | ∅ | 0.004 | +0.004 | — |
| company:xai | company | ∅ | 0.001 | +0.001 | — |
| company:openai | company | ∅ | 0.001 | +0.001 | — |
| company:broadcom | company | ∅ | 0.001 | +0.001 | — |
| facility:colossus | facility | ∅ | 0.001 | +0.001 | — |
| facility:stargate_abilene | facility | ∅ | 0.001 | +0.001 | — |
| company:meta | company | ∅ | 0.001 | +0.001 | — |

## Propagation path for top-3

- **`company:sk_hynix`** — edges: `(origin)`
- **`product:hbm`** — edges: `(origin)`
- **`company:nvidia`** — edges: `e:sk_hynix-supplies-nvidia`

