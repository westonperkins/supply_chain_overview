# Replay — J-2024-04-taiwan-quake

**Headline.** M7.4 earthquake off Hualien; TSMC evacuates fabs

**Timestamp.** 2024-04-03T00:58:00Z

**Origin(s).**
- `company:tsmc` (company, TSMC) — SCORED origin; baseline_severity=0.465, baseline_tier=high
- `country_region:taiwan` (country_region, Taiwan) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.023`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.05, substitutability_delta=0.0, lead_time_delta=0.02

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| company:tsmc | 0 | 0.023 | 0.465 | 0.477 | +0.012 | — |
| country_region:taiwan | 0 | 0.000 | ∅ | ∅ | +0.000 | — |
| product:cowos_packaging | 1 | 0.013 | 0.330 | 0.338 | +0.009 | — |
| company:amd | 1 | 0.006 | ∅ | 0.006 | +0.006 | — |
| company:arm | 1 | 0.005 | 0.211 | 0.214 | +0.004 | — |
| company:nvidia | 1 | 0.003 | 0.358 | 0.360 | +0.002 | — |
| company:broadcom | 1 | 0.003 | ∅ | 0.003 | +0.003 | — |
| company:meta | 1 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:google | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:amazon | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:microsoft | 1 | 0.000 | ∅ | 0.000 | +0.000 | — |
| product:arm_core_ip | 2 | 0.003 | 0.330 | 0.332 | +0.002 | — |
| company:xai | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:openai | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:colossus | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:stargate_abilene | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| company:tsmc | company | 0.465 | 0.477 | +0.012 | — |
| product:cowos_packaging | product | 0.330 | 0.338 | +0.009 | — |
| company:amd | company | ∅ | 0.006 | +0.006 | — |
| company:arm | company | 0.211 | 0.214 | +0.004 | — |
| company:broadcom | company | ∅ | 0.003 | +0.003 | — |
| company:nvidia | company | 0.358 | 0.360 | +0.002 | — |
| product:arm_core_ip | product | 0.330 | 0.332 | +0.002 | — |
| company:meta | company | ∅ | 0.001 | +0.001 | — |
| company:xai | company | ∅ | 0.001 | +0.001 | — |
| company:openai | company | ∅ | 0.001 | +0.001 | — |

## Propagation path for top-3

- **`company:tsmc`** — edges: `(origin)`
- **`product:cowos_packaging`** — edges: `e:tsmc-supplies-cowos`
- **`company:amd`** — edges: `e:tsmc-supplies-amd`

