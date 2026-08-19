# Replay — J-2025-04-china-rees

**Headline.** China imposes export licence requirement on seven heavy rare earths including dysprosium

**Timestamp.** 2025-04-04T00:00:00Z

**Origin(s).**
- `country_region:china` (country_region, China) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored
- `mineral:dysprosium` (mineral, Dysprosium) — SCORED origin; baseline_severity=0.562, baseline_tier=critical

**Origin scale** (event severity attributed to strongest origin): `0.220`

**Origin scored?** `True` — walk seeded from baseline_severity × magnitude × confidence

**Authored axes (Phase A).** concentration_delta=0.35, substitutability_delta=0.1, lead_time_delta=0.2

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:china | 0 | 0.220 | ∅ | ∅ | +0.000 | — |
| mineral:dysprosium | 0 | 0.197 | 0.562 | 0.648 | +0.086 | — |
| mineral:gallium | 1 | 0.130 | 0.488 | 0.554 | +0.067 | high → critical |
| product:ndfeb_magnets | 1 | 0.106 | 0.340 | 0.410 | +0.070 | — |
| mineral:neodymium | 1 | 0.079 | 0.295 | 0.351 | +0.056 | — |
| mineral:indium | 1 | 0.040 | 0.120 | 0.155 | +0.035 | — |
| mineral:copper | 1 | 0.013 | 0.580 | 0.586 | +0.006 | — |
| product:rf_power_semis | 2 | 0.070 | 0.287 | 0.337 | +0.050 | — |
| company:vertiv | 2 | 0.009 | 0.069 | 0.077 | +0.008 | — |
| facility:colossus | 2 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:stargate_abilene | 2 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:vantage_frontier | 2 | 0.005 | ∅ | 0.005 | +0.005 | — |
| facility:the_citadel | 2 | 0.005 | ∅ | 0.005 | +0.005 | — |
| company:sk_hynix | 2 | 0.004 | 0.263 | 0.266 | +0.003 | — |
| company:micron | 2 | 0.003 | 0.243 | 0.245 | +0.003 | — |
| company:siemens_energy | 2 | 0.003 | 0.315 | 0.317 | +0.002 | — |
| company:ge_vernova | 2 | 0.003 | 0.318 | 0.320 | +0.002 | — |
| company:tsmc | 2 | 0.002 | 0.465 | 0.465 | +0.001 | — |
| company:quanta_services | 2 | 0.001 | 0.077 | 0.078 | +0.001 | — |
| company:samsung | 2 | 0.000 | 0.284 | 0.284 | +0.000 | — |
| company:broadcom | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| company:amd | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:arm | 3 | 0.000 | 0.211 | 0.211 | +0.000 | — |
| company:nvidia | 3 | 0.000 | 0.358 | 0.358 | +0.000 | — |
| company:duke_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:constellation_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:nextera_energy | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:meta | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:google | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:amazon | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:microsoft | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| product:hbm | 3 | 0.000 | 0.301 | 0.301 | +0.000 | — |
| product:cowos_packaging | 3 | 0.000 | 0.330 | 0.330 | +0.000 | — |
| product:arm_core_ip | 4 | 0.000 | 0.330 | 0.330 | +0.000 | — |
| facility:three_mile_island | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:xai | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |
| company:openai | 4 | 0.000 | ∅ | 0.000 | +0.000 | — |

## Top-10 most-affected nodes by delta

| node_id | type | before | after | Δ | tier |
|---|---|---|---|---|---|
| mineral:dysprosium | mineral | 0.562 | 0.648 | +0.086 | — |
| product:ndfeb_magnets | product | 0.340 | 0.410 | +0.070 | — |
| mineral:gallium | mineral | 0.488 | 0.554 | +0.067 | high → critical |
| mineral:neodymium | mineral | 0.295 | 0.351 | +0.056 | — |
| product:rf_power_semis | product | 0.287 | 0.337 | +0.050 | — |
| mineral:indium | mineral | 0.120 | 0.155 | +0.035 | — |
| company:vertiv | company | 0.069 | 0.077 | +0.008 | — |
| mineral:copper | mineral | 0.580 | 0.586 | +0.006 | — |
| facility:colossus | facility | ∅ | 0.005 | +0.005 | — |
| facility:stargate_abilene | facility | ∅ | 0.005 | +0.005 | — |

## Propagation path for top-3

- **`mineral:dysprosium`** — edges: `(origin)`
- **`product:ndfeb_magnets`** — edges: `e:dy-input-ndfeb`
- **`mineral:gallium`** — edges: `e:china-mines-gallium`

