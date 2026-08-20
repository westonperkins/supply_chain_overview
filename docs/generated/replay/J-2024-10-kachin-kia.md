# Replay — J-2024-10-kachin-kia

**Headline.** Kachin Independence Army takes control of Chipwi and Pangwa townships

**Timestamp.** 2024-10-27T00:00:00Z

**Origin(s).**
- `country_region:kachin` (country_region, Kachin State) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored
- `country_region:myanmar` (country_region, Myanmar) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.200`

**Origin scored?** `False` — walk seeded from concentration × magnitude × confidence (see Pass D §4)

**Authored axes (Phase A).** concentration_delta=0.2, substitutability_delta=0.0, lead_time_delta=0.1

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:kachin | 0 | 0.200 | ∅ | ∅ | +0.000 | — |
| country_region:myanmar | 0 | 0.140 | ∅ | ∅ | +0.000 | — |
| mineral:dysprosium | 1 | 0.042 | 0.562 | 0.580 | +0.018 | — |
| mineral:neodymium | 1 | 0.008 | 0.295 | 0.301 | +0.006 | — |
| product:ndfeb_magnets | 2 | 0.023 | 0.340 | 0.355 | +0.015 | — |
| company:vertiv | 3 | 0.002 | 0.069 | 0.070 | +0.002 | — |
| facility:colossus | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:stargate_abilene | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:vantage_frontier | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:the_citadel | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| mineral:dysprosium | mineral | 0.562 | 0.580 | +0.018 | — |
| product:ndfeb_magnets | product | 0.340 | 0.355 | +0.015 | — |
| mineral:neodymium | mineral | 0.295 | 0.301 | +0.006 | — |
| company:vertiv | company | 0.069 | 0.070 | +0.002 | — |
| facility:colossus | facility | ∅ | 0.001 | +0.001 | — |
| facility:stargate_abilene | facility | ∅ | 0.001 | +0.001 | — |
| facility:vantage_frontier | facility | ∅ | 0.001 | +0.001 | — |
| facility:the_citadel | facility | ∅ | 0.001 | +0.001 | — |

## Propagation path for top-3

- **`mineral:dysprosium`** — edges: `e:kachin-mines-dysprosium`
- **`product:ndfeb_magnets`** — edges: `e:kachin-mines-dysprosium → e:dy-input-ndfeb`
- **`mineral:neodymium`** — edges: `e:myanmar-mines-neodymium`

