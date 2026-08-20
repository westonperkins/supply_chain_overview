# Replay — J-2024-12-china-gallium

**Headline.** China announces immediate ban on exports of gallium, germanium, antimony to the United States

**Timestamp.** 2024-12-02T00:00:00Z

**Origin(s).**
- `country_region:china` (country_region, China) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored
- `mineral:gallium` (mineral, Gallium) — SCORED origin; baseline_severity=0.488, baseline_tier=high
- `country_region:usa` (country_region, United States) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.300`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.3, substitutability_delta=0.05, lead_time_delta=0.15

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:china | 0 | 0.300 | ∅ | ∅ | +0.000 | — |
| country_region:usa | 0 | 0.210 | ∅ | ∅ | +0.000 | — |
| mineral:gallium | 1 | 0.177 | 0.488 | 0.578 | +0.091 | high → critical |
| product:rf_power_semis | 2 | 0.096 | 0.287 | 0.355 | +0.068 | — |
| company:ge_vernova | 3 | 0.006 | 0.318 | 0.323 | +0.004 | — |
| company:vertiv | 3 | 0.002 | 0.069 | 0.071 | +0.002 | — |
| company:siemens_energy | 3 | 0.002 | 0.315 | 0.316 | +0.001 | — |
| company:broadcom | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:the_citadel | 4 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:colossus | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:stargate_abilene | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:vantage_frontier | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:nextera_energy | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:duke_energy | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:constellation_energy | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:meta | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:google | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:three_mile_island | 5 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:microsoft | 5 | 0.000 | ∅ | 0.000 | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| mineral:gallium | mineral | 0.488 | 0.578 | +0.091 | high → critical |
| product:rf_power_semis | product | 0.287 | 0.355 | +0.068 | — |
| company:ge_vernova | company | 0.318 | 0.323 | +0.004 | — |
| company:vertiv | company | 0.069 | 0.071 | +0.002 | — |
| company:broadcom | company | ∅ | 0.001 | +0.001 | — |
| company:siemens_energy | company | 0.315 | 0.316 | +0.001 | — |
| facility:the_citadel | facility | ∅ | 0.001 | +0.001 | — |
| facility:colossus | facility | ∅ | 0.000 | +0.000 | — |
| facility:stargate_abilene | facility | ∅ | 0.000 | +0.000 | — |
| facility:vantage_frontier | facility | ∅ | 0.000 | +0.000 | — |

## Propagation path for top-3

- **`mineral:gallium`** — edges: `e:china-mines-gallium`
- **`product:rf_power_semis`** — edges: `e:china-mines-gallium → e:gallium-input-rf`
- **`company:ge_vernova`** — edges: `e:china-mines-gallium → e:gallium-input-rf → e:rf-input-ge_vernova`

