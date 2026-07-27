# Replay — J-2025-04-china-rees

**Headline.** China imposes export licence requirement on seven heavy rare earths including dysprosium

**Timestamp.** 2025-04-04T00:00:00Z

**Origin(s).**
- `country_region:china` (country_region, China) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored
- `mineral:dysprosium` (mineral, Dysprosium) — SCORED origin; baseline_severity=0.545, baseline_tier=critical

**Origin scale** (event severity attributed to strongest origin): `0.290`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.35, substitutability_delta=0.1, lead_time_delta=0.2

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:china | 0 | 0.290 | ∅ | ∅ | +0.000 | — |
| mineral:dysprosium | 0 | 0.191 | 0.545 | 0.632 | +0.087 | — |
| mineral:gallium | 1 | 0.171 | 0.480 | 0.569 | +0.089 | high → critical |
| mineral:neodymium | 1 | 0.104 | 0.220 | 0.302 | +0.081 | — |
| mineral:indium | 1 | 0.052 | 0.074 | 0.122 | +0.048 | — |
| product:ndfeb_magnets | 1 | 0.023 | 0.213 | 0.231 | +0.018 | — |
| mineral:copper | 1 | 0.017 | 0.207 | 0.221 | +0.014 | — |
| product:rf_power_semis | 2 | 0.092 | 0.026 | 0.116 | +0.090 | — |
| company:vertiv | 2 | 0.002 | 0.064 | 0.066 | +0.002 | — |
| company:siemens_energy | 2 | 0.001 | 0.224 | 0.226 | +0.001 | — |
| company:quanta_services | 2 | 0.001 | 0.039 | 0.040 | +0.001 | — |
| company:ge_vernova | 2 | 0.001 | 0.216 | 0.217 | +0.001 | — |
| facility:colossus | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:stargate_abilene | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:vantage_frontier | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:the_citadel | 2 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:sk_hynix | 2 | 0.000 | 0.211 | 0.212 | +0.000 | — |
| company:micron | 2 | 0.000 | 0.195 | 0.195 | +0.000 | — |
| company:samsung | 2 | 0.000 | 0.275 | 0.275 | +0.000 | — |
| company:tsmc | 2 | 0.000 | 0.460 | 0.460 | +0.000 | — |
| company:broadcom | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:duke_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:constellation_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:nextera_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:amd | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| product:hbm | 3 | 0.000 | 0.178 | 0.178 | +0.000 | — |
| company:nvidia | 3 | 0.000 | 0.355 | 0.355 | +0.000 | — |
| product:cowos_packaging | 3 | 0.000 | 0.313 | 0.313 | +0.000 | — |
| company:meta | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:google | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:amazon | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:microsoft | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:three_mile_island | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:xai | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:openai | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| product:rf_power_semis | product | 0.026 | 0.116 | +0.090 | — |
| mineral:gallium | mineral | 0.480 | 0.569 | +0.089 | high → critical |
| mineral:dysprosium | mineral | 0.545 | 0.632 | +0.087 | — |
| mineral:neodymium | mineral | 0.220 | 0.302 | +0.081 | — |
| mineral:indium | mineral | 0.074 | 0.122 | +0.048 | — |
| product:ndfeb_magnets | product | 0.213 | 0.231 | +0.018 | — |
| mineral:copper | mineral | 0.207 | 0.221 | +0.014 | — |
| company:vertiv | company | 0.064 | 0.066 | +0.002 | — |
| company:broadcom | company | ∅ | 0.001 | +0.001 | — |
| company:quanta_services | company | 0.039 | 0.040 | +0.001 | — |

## Propagation path for top-3

- **`product:rf_power_semis`** — edges: `e:china-mines-gallium → e:gallium-input-rf`
- **`mineral:gallium`** — edges: `e:china-mines-gallium`
- **`mineral:dysprosium`** — edges: `(origin)`

