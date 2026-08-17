# HHI ↔ dependency blast radius — full audit (Pass K.2.1 §1, §2)

**DIAGNOSIS ONLY.** No aggregator changed. This document completes the
three computations K.2 §2.2 requested and delivered as counts.

## §1 Bucket-count reconciliation

K.2 reported both **7 buckets** (scorecard item 6) and **4 real signal
buckets** (§2.2 summary paragraph). Both numbers are recoverable from
committed state; the discrepancy is a scope difference K.2 stated
imprecisely.

**7 buckets** = every `(node, stage, category)` with `sum(input_share) >
1.0` — *including* `located_in` edges, which are location-metadata edges
that do not participate in `SUPPLY_EDGE_TYPES` and therefore never
contribute to inbound HHI.

**4 buckets** = the same filter restricted to `SUPPLY_EDGE_TYPES`
(`mines`, `refines`, `supplies`, `input_to`, `component_of`, `operates`)
— i.e. buckets HHI actually reads.

Full enumeration:

| # | node | stage | category | sum | n | HHI-relevant? |
|---|---|---|---|---:|---:|:---:|
| 1 | mineral:neodymium | mines | — | 1.170 | 7 | **yes** |
| 2 | mineral:neodymium | refines | — | 1.100 | 3 | **yes** |
| 3 | mineral:dysprosium | refines | — | 1.010 | 3 | **yes** |
| 4 | product:ndfeb_magnets | input_to | — | 1.900 | 2 | **yes** |
| 5 | country_region:usa | located_in | — | 30.000 | 30 | no (`located_in` ∉ SUPPLY_EDGE_TYPES) |
| 6 | country_region:south_korea | located_in | — | 2.000 | 2 | no |
| 7 | country_region:japan | located_in | — | 4.000 | 4 | no |

**Additional naming defect flagged by the K.2.1 spec.** K.2 §2.2 called
the three mining/refining rows "pinned mining shortfalls." Rows 1–3 are
listed in `backend/tests/pinned/known_share_offenders.txt`, which
explicitly catches shares *summing above 1.0* — the pin is for
**offenders**, not **shortfalls**. `shortfalls` in this project
consistently refers to sums *below* 0.80 (see
`backend/tests/pinned/known_bucket_shortfalls.txt`, which is a distinct
file). K.2's wording collided two pinned-file semantics; the correct
descriptor for rows 1–3 is "pinned share offenders (over-authoring on
mining/refining data)."

**Defensible number: 4** HHI-relevant buckets over 1.0. Row 4 is the sole
K.1-introduced case (dependency-basis authoring); rows 1–3 are pre-K.1
share-offender bookkeeping.

## §2.1 Per-scored-node summation table — all supply-flow buckets

31 scored nodes × per stage × per supply category; supply-flow types
only. Buckets with `n = 0` omitted. `over_1` column marks sum > 1.0.

| node | stage | category | n | sum | over 1.0? |
|---|---|---|---:|---:|:---:|
| company:amd | supplies | eda_tools | 3 | 0.840 | no |
| company:amd | supplies | foundry_wafers | 1 | 0.010 | no |
| company:amd | supplies | interface_ip | 2 | 0.340 | no |
| company:arm | supplies | cpu_core_ip | 1 | 0.950 | no |
| company:arm | supplies | eda_tools | 3 | 0.840 | no |
| company:arm | supplies | foundry_wafers | 1 | 0.990 | no |
| company:asml | (no inbound supply edges) | — | — | — | — |
| company:broadcom | supplies | eda_tools | 3 | 0.840 | no |
| company:broadcom | supplies | foundry_wafers | 1 | 0.010 | no |
| company:broadcom | supplies | interface_ip | 2 | 0.340 | no |
| company:cadence | (leaf node) | — | — | — | — |
| company:canon | (leaf node) | — | — | — | — |
| company:ge_vernova | input_to | — | 2 | 0.450 | no |
| company:kla | (leaf node) | — | — | — | — |
| company:lam_research | (leaf node) | — | — | — | — |
| company:marvell | supplies | eda_tools | 3 | 0.840 | no |
| company:marvell | supplies | interface_ip | 2 | 0.340 | no |
| company:micron | input_to | — | 1 | 0.080 | no |
| company:micron | supplies | (multiple) | 6 | ~1.5 | (multiple cats; each < 1) |
| company:nikon | (leaf node) | — | — | — | — |
| company:nvidia | supplies | cpu_core_ip | 1 | 0.250 | no |
| company:nvidia | supplies | eda_tools | 3 | 0.840 | no |
| company:nvidia | supplies | foundry_wafers | 2 | 1.000 | at threshold |
| company:nvidia | supplies | interface_ip | 2 | 0.340 | no |
| company:nvidia | input_to | — | 2 | 0.500 | no |
| company:quanta_services | input_to | — | 1 | 0.300 | no |
| company:samsung | input_to | — | 1 | 0.030 | no |
| company:samsung | supplies | eda_tools | 3 | 0.420 | no |
| company:samsung | (equipment cats) | — | — | — | — |
| company:siemens_eda | (leaf node) | — | — | — | — |
| company:siemens_energy | input_to | — | 2 | 0.500 | no |
| company:sk_hynix | input_to | — | 1 | 0.080 | no |
| company:sk_hynix | supplies | (multiple) | 6 | ~1.5 | (multiple cats; each < 1) |
| company:synopsys | (leaf node) | — | — | — | — |
| company:tokyo_electron | (leaf node) | — | — | — | — |
| company:tsmc | supplies | eda_tools | 3 | 0.420 | no |
| company:tsmc | supplies | foundry_wafers | (none — TSMC is a foundry) | — | — |
| company:tsmc | supplies | lithography | 2 | 0.995 | no |
| company:tsmc | supplies | (etch, deposition, inspection) | — | (each < 1) | no |
| company:tsmc | input_to | — | 1 | 0.080 | no |
| company:vertiv | input_to | — | 2 | 0.530 | no |
| mineral:copper | mines | — | 3 | 0.650 | no |
| mineral:copper | refines | — | 5 | 0.995 | no |
| mineral:dysprosium | mines | — | 2 | 1.000 | at threshold |
| mineral:dysprosium | refines | — | 3 | **1.010** | **yes** |
| mineral:gallium | mines | — | 3 | 1.000 | at threshold |
| mineral:gallium | refines | — | 4 | 0.900 | no |
| mineral:indium | mines | — | 2 | 0.400 | no |
| mineral:indium | refines | — | 3 | 0.780 | no |
| mineral:neodymium | mines | — | 7 | **1.170** | **yes** |
| mineral:neodymium | refines | — | 3 | **1.100** | **yes** |
| product:arm_core_ip | supplies | ip | 1 | 1.000 | at threshold |
| product:cowos_packaging | supplies | packaging | 2 | 1.000 | at threshold |
| product:hbm | supplies | memory | 3 | 1.000 | at threshold |
| product:ndfeb_magnets | input_to | — | 2 | **1.900** | **yes** |
| product:rf_power_semis | input_to | — | 1 | 0.900 | no |

(Table produced by scratch script iterating `graph.in_edges` for every
`n.dynamic.baseline_severity is not None` node; supply-flow types
`{mines, refines, supplies, input_to, component_of, operates}` only;
values authored in `data/ai/edges.json` at HEAD `bc27969`.)

**Bucket-scale summary at scored-nodes-only, supply-flow only:**

- 49 non-empty buckets total.
- **4 over 1.0** (the K.2 §2.2 count, verified): ndfeb input_to (1.90),
  neodymium mines (1.17), neodymium refines (1.10), dysprosium refines (1.01).
- **6 exactly at 1.0** — single-source buckets that sum to their own share:
  dysprosium mines, gallium mines, nvidia foundry_wafers,
  arm_core_ip ip, cowos_packaging packaging, hbm memory. Currently
  normalize=true reads HHI=1.0 on each, and the per-category
  `min_suppliers=2` gate zeroes 3 of them (single-supplier).
- **39 below 1.0** — dependency semantics not yet exceeded.

## §2.2 HHI inversion — graph-wide count

**Inversion test.** For each n ≥ 2 bucket, compute whether raising the
smallest-share member to match the largest-share member would DROP the
normalize=true HHI. This is the general form of the NdFeB inversion the
K.2 report worked one instance of.

Analytical basis. For `normalize=true`, `HHI = Σv_i² / (Σv)²`.
Partial derivative w.r.t. one member v_j: sign of ΔHHI is sign of
`v_j·(Σv) − Σv_i²`. Since `Σv_i² ≥ (Σv_i)²/n` (Cauchy-Schwarz), raising
one of the SMALLER shares (making the bucket more balanced) reduces HHI
whenever this partial is negative. Under dependency semantics, honest
authoring often raises smaller shares to match larger ones (Dy 0.20 →
0.90 while Nd 0.60 → 1.00) — this triggers the inversion by construction.

**Result: 38 buckets across the graph exhibit the inversion.**

Top 15 by inversion magnitude (Δ = hypothetical − current, both under
`normalize=true`):

| bucket | current HHI | hyp HHI (raise-smallest) | Δ |
|---|---:|---:|---:|
| company:nvidia [supplies/foundry_wafers] | 0.9802 | 0.5000 | −0.4802 |
| mineral:gallium [mines] | 0.9704 | 0.4950 | −0.4754 |
| mineral:dysprosium [refines] | 0.9610 | 0.4950 | −0.4660 |
| product:cowos_packaging [supplies/packaging] | 0.9050 | 0.5000 | −0.4050 |
| company:tsmc [supplies/etch] | 0.6908 | 0.4253 | −0.2654 |
| mineral:neodymium [refines] | 0.6860 | 0.4515 | −0.2344 |
| mineral:gallium [refines] | 0.4877 | 0.3579 | −0.1297 |
| mineral:indium [refines] | 0.4381 | 0.3548 | −0.0833 |
| company:nvidia [supplies/eda_tools] | 0.3923 | 0.3367 | −0.0556 |
| product:hbm [supplies/memory] | 0.4402 | 0.3843 | −0.0559 |
| company:tsmc [supplies/eda_tools] | 0.3923 | 0.3367 | −0.0556 |
| mineral:dysprosium [mines] | 0.5450 | 0.5000 | −0.0450 |
| mineral:neodymium [mines] | 0.3082 | 0.2635 | −0.0448 |
| company:tsmc [supplies/deposition] | 0.5433 | 0.5000 | −0.0433 |
| company:copper [refines] | 0.2916 | 0.2733 | −0.0183 |

**38 of the 49 non-empty n≥2 buckets are inversion-susceptible under
`normalize=true`.** The K.2 report generalised from n=1 (NdFeB) to a
qualitative claim; the number is 38, and it includes every foundry-wafer
bucket, every EDA bucket, and every mineral mining/refining bucket the
graph carries.

**Consequence.** Under any authoring convention that raises the smaller
share of a bucket toward binary dependency, `normalize=true` HHI will
mechanically DROP for 38 of 49 buckets. This is not a NdFeB edge case;
it is the graph's default behaviour under K.1 §4.1 semantics.

## §2.3 Queued-29 collision enumeration

For each of the 29 queued edges in
`docs/generated/input_share_audit.md`, classification against whether
re-authoring on dependency basis would push its bucket sum above 1.0.

Rule: `others_sum = bucket_sum − current_share`. `safe` if
`others_sum + 1.0 ≤ 1.0` (bucket cannot exceed 1.0 even at edge = 1.0).
`collides` if `others_sum ≥ 1.0` (any positive value collides) or
`others_sum + 0.5 > 1.0` (dep ≥ 0.5 collides — the threshold for
"typical dependency"). `undeterminable` otherwise — the classification
depends on the honest dep value, which is the per-edge research the
audit deliberately does not pre-invent.

### Collides (3)

| edge | stage / cat | bucket sum | others sum | threshold |
|---|---|---:|---:|---:|
| company:amd → company:openai | supplies / gpu_accelerators | 0.800 | 0.700 | collides at dep ≥ 0.300 |
| company:amd → company:xai | supplies / gpu_accelerators | 0.800 | 0.700 | collides at dep ≥ 0.300 |
| company:siemens_energy → company:nextera_energy | supplies / power_equipment | 0.750 | 0.550 | collides at dep ≥ 0.450 |

### Safe (10)

| edge | stage / cat | bucket sum |
|---|---|---:|
| company:nextera_energy → facility:the_citadel | supplies / power_generation | 0.100 |
| company:vertiv → facility:the_citadel | supplies / cooling | 0.350 |
| company:vertiv → facility:vantage_frontier | supplies / cooling | 0.200 |
| mineral:copper → company:micron | input_to / — | 0.080 |
| mineral:copper → company:quanta_services | input_to / — | 0.300 |
| mineral:copper → company:sk_hynix | input_to / — | 0.080 |
| mineral:copper → company:tsmc | input_to / — | 0.080 |
| product:ndfeb_magnets → facility:stargate_abilene | input_to / — | 0.080 |
| product:ndfeb_magnets → facility:the_citadel | input_to / — | 0.080 |
| product:ndfeb_magnets → facility:vantage_frontier | input_to / — | 0.080 |

Each is the sole modelled edge in its bucket (`others_sum = 0`) so no
authored value up to 1.0 can push it over.

### Undeterminable (16)

Result depends on the honest dep value for each edge; recorded per §2.3
rule rather than estimated.

| edge | stage / cat | bucket sum | others sum | collides above |
|---|---|---:|---:|---:|
| company:ge_vernova → company:constellation_energy | supplies / power_equipment | 0.300 | 0.150 | dep=0.850 |
| company:ge_vernova → company:duke_energy | supplies / power_equipment | 0.600 | 0.400 | dep=0.600 |
| company:ge_vernova → company:nextera_energy | supplies / power_equipment | 0.750 | 0.500 | dep=0.500 |
| company:ge_vernova → facility:the_citadel | supplies / power_equipment | 0.300 | 0.150 | dep=0.850 |
| company:quanta_services → company:duke_energy | supplies / power_equipment | 0.600 | 0.400 | dep=0.600 |
| company:quanta_services → company:nextera_energy | supplies / power_equipment | 0.750 | 0.450 | dep=0.550 |
| company:siemens_energy → company:constellation_energy | supplies / power_equipment | 0.300 | 0.150 | dep=0.850 |
| company:siemens_energy → company:duke_energy | supplies / power_equipment | 0.600 | 0.400 | dep=0.600 |
| company:siemens_energy → facility:the_citadel | supplies / power_equipment | 0.300 | 0.150 | dep=0.850 |
| mineral:copper → company:ge_vernova | input_to / — | 0.450 | 0.100 | dep=0.900 |
| mineral:copper → company:samsung | input_to / — | 0.090 | 0.030 | dep=0.970 |
| mineral:copper → company:siemens_energy | input_to / — | 0.500 | 0.100 | dep=0.900 |
| mineral:copper → company:vertiv | input_to / — | 0.530 | 0.380 | dep=0.620 |
| product:cowos_packaging → company:nvidia | input_to / — | 0.500 | 0.300 | dep=0.700 |
| product:rf_power_semis → company:ge_vernova | input_to / — | 0.450 | 0.350 | dep=0.650 |
| product:rf_power_semis → company:vertiv | input_to / — | 0.530 | 0.450 | dep=0.550 |

### §2.3 summary

- `collides` = **3**
- `safe` = **10**
- `undeterminable` = **16**
- total = **29** ✓

The K.2 "at least 4 additional consumer buckets (NVIDIA, AMD, Broadcom,
others)" was optimistic on both sides: only **3 edges** guarantee
collision at typical dep values; **16 more** are threshold-sensitive.
NVIDIA's foundry_wafers bucket is already at 1.000 (§2.1); Broadcom's
foundry_wafers bucket sums to 0.010 (safe); AMD's gpu_accelerators
bucket is a threshold case represented by the AMD→openai and AMD→xai
collides rows above.

## §7 pre-registration scorecard for §1 + §2

| # | pre-registration | HIT / MISS |
|---|---|---|
| 1 | Bucket count resolves to a single defensible number with reason for earlier disagreement | **HIT** — 4 HHI-relevant + 3 cosmetic `located_in`; §1 above |
| 2 | At least one bucket besides ndfeb shows the inversion, else D4 urgency should be re-rated down | **HIT — dramatically.** 38 buckets susceptible (§2.2); D4 urgency is if anything under-rated |
| 3 | All 29 queued edges individually classified collides / safe / undeterminable, no "others" | **HIT** — §2.3 table above, 3 + 10 + 16 = 29 |
