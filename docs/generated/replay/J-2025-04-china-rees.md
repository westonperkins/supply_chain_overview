# Replay — J-2025-04-china-rees

**Headline.** China imposes export licence requirement on seven heavy rare earths including dysprosium

**Timestamp.** 2025-04-04T00:00:00Z

**Origin(s).**
- `country_region:china` (country_region, China) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored
- `mineral:dysprosium` (mineral, Dysprosium) — SCORED origin; baseline_severity=0.562, baseline_tier=critical

**Origin scale** (event severity attributed to strongest origin): `0.350`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.35, substitutability_delta=0.1, lead_time_delta=0.2

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:china | 0 | 0.350 | ∅ | ∅ | +0.000 | — |
| mineral:dysprosium | 1 | 0.208 | 0.562 | 0.653 | +0.091 | — |
| product:ndfeb_magnets | 2 | 0.112 | 0.340 | 0.414 | +0.074 | — |
| company:vertiv | 3 | 0.009 | 0.069 | 0.077 | +0.008 | — |
| facility:colossus | 3 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:stargate_abilene | 3 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:vantage_frontier | 3 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:the_citadel | 3 | 0.005 | ∅ | 0.005 | +0.005 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| mineral:dysprosium | mineral | 0.562 | 0.653 | +0.091 | — |
| product:ndfeb_magnets | product | 0.340 | 0.414 | +0.074 | — |
| company:vertiv | company | 0.069 | 0.077 | +0.008 | — |
| facility:colossus | facility | ∅ | 0.005 | +0.005 | — |
| facility:stargate_abilene | facility | ∅ | 0.005 | +0.005 | — |
| facility:vantage_frontier | facility | ∅ | 0.005 | +0.005 | — |
| facility:the_citadel | facility | ∅ | 0.005 | +0.005 | — |

## Propagation path for top-3

- **`mineral:dysprosium`** — edges: `e:china-refines-dysprosium`
- **`product:ndfeb_magnets`** — edges: `e:china-refines-dysprosium → e:dy-input-ndfeb`
- **`company:vertiv`** — edges: `e:china-refines-dysprosium → e:dy-input-ndfeb → e:ndfeb-input-vertiv`

