> **PROBE.** This is an injected-magnitude counterfactual — the axes on this record are not an estimate of any real event's impact. Probes do not enter summary.md, ranking, or outcomes.json. See Pass J.1 §6 and the probe's `notes` field for rationale.

# Replay — P-J-2

**Headline.** PROBE — Chinese port congestion (Shanghai) with injected concentration_delta=0.20; entity match: country_region:china only

**Timestamp.** 2026-03-14T00:00:00Z

**Origin(s).**
- `country_region:china` (country_region, China) — UNSCORED origin; baseline_severity=∅, baseline_tier=unscored

**Origin scale** (event severity attributed to strongest origin): `0.116`

**Origin scored?** `False` — walk seeded from concentration × magnitude × confidence (see Pass D §4)

**Authored axes (Phase A).** concentration_delta=0.2, substitutability_delta=0.0, lead_time_delta=0.0

> Reminder — the pipeline reads only `concentration_delta` as the event magnitude today. The other axes are authored for Phase B analysis but do not enter the walk.

## Cascade table

Every node touched by this event's walk, in order (hop, then severity descending). Contribution is the walk value at this node; before/after are the raw severity numbers; tiers use `derive_current_tier` (baseline None → tier stays UNSCORED).

| node_id | hop | contrib | before | after | Δ | tier |
|---|---|---|---|---|---|---|
| country_region:china | 0 | 0.116 | ∅ | ∅ | +0.000 | — |
| mineral:gallium | 1 | 0.068 | 0.480 | 0.516 | +0.036 | high → critical |
| mineral:dysprosium | 1 | 0.045 | 0.545 | 0.566 | +0.021 | — |
| mineral:neodymium | 1 | 0.042 | 0.220 | 0.253 | +0.033 | — |
| mineral:indium | 1 | 0.021 | 0.074 | 0.093 | +0.019 | — |
| mineral:copper | 1 | 0.007 | 0.207 | 0.212 | +0.006 | — |
| product:rf_power_semis | 2 | 0.037 | 0.026 | 0.062 | +0.036 | — |
| product:ndfeb_magnets | 2 | 0.005 | 0.213 | 0.217 | +0.004 | — |
| company:siemens_energy | 2 | 0.001 | 0.224 | 0.225 | +0.000 | — |
| company:quanta_services | 2 | 0.001 | 0.039 | 0.039 | +0.001 | — |
| company:ge_vernova | 2 | 0.001 | 0.216 | 0.216 | +0.000 | — |
| company:vertiv | 2 | 0.000 | 0.064 | 0.064 | +0.000 | — |
| company:sk_hynix | 2 | 0.000 | 0.211 | 0.211 | +0.000 | — |
| company:micron | 2 | 0.000 | 0.195 | 0.195 | +0.000 | — |
| company:samsung | 2 | 0.000 | 0.275 | 0.275 | +0.000 | — |
| company:tsmc | 2 | 0.000 | 0.460 | 0.460 | +0.000 | — |
| company:broadcom | 3 | 0.001 | ∅ | 0.001 | +0.001 | — |
| facility:colossus | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:stargate_abilene | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:vantage_frontier | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
| facility:the_citadel | 3 | 0.000 | ∅ | 0.000 | +0.000 | — |
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
| product:rf_power_semis | product | 0.026 | 0.062 | +0.036 | — |
| mineral:gallium | mineral | 0.480 | 0.516 | +0.036 | high → critical |
| mineral:neodymium | mineral | 0.220 | 0.253 | +0.033 | — |
| mineral:dysprosium | mineral | 0.545 | 0.566 | +0.021 | — |
| mineral:indium | mineral | 0.074 | 0.093 | +0.019 | — |
| mineral:copper | mineral | 0.207 | 0.212 | +0.006 | — |
| product:ndfeb_magnets | product | 0.213 | 0.217 | +0.004 | — |
| company:broadcom | company | ∅ | 0.001 | +0.001 | — |
| company:quanta_services | company | 0.039 | 0.039 | +0.001 | — |
| company:siemens_energy | company | 0.224 | 0.225 | +0.000 | — |

## Propagation path for top-3

- **`product:rf_power_semis`** — edges: `e:china-mines-gallium → e:gallium-input-rf`
- **`mineral:gallium`** — edges: `e:china-mines-gallium`
- **`mineral:neodymium`** — edges: `e:china-mines-neodymium`

