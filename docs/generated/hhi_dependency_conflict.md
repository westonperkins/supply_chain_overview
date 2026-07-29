# HHI ↔ dependency-share incompatibility — diagnosis (Pass K.2 §2)

**DIAGNOSIS ONLY.** No aggregator is changed. §5 D4 records the aggregator
decision this diagnosis feeds. The 29 queued edges in
`docs/generated/input_share_audit.md` remain queued.

## §2.1 The incompatibility — VERIFIED

HHI = Σ(share_i)² is defined on shares that partition a market and sum to 1.

Pass K.1 §4.1 redefined `input_share` as *the fraction of the consuming
node's function that ceases if this input is withdrawn* — a quantity with
**no summation constraint**. Co-critical inputs are each independently near
1.0. The graph now contains at least one such node:

- `product:ndfeb_magnets` input_to: `mineral:neodymium` 1.00 + `mineral:dysprosium` 0.90 = **1.90**

Under the two available normalization modes:

| mode | ndfeb inbound HHI | in [0,1]? |
|---|---:|:---:|
| `normalize: true` (current) | 0.5014 | yes |
| `normalize: false` | 1.8100 | **NO** — exceeds axis range |

**Under `normalize: true` the HHI DROPPED when both dependencies were
correctly raised.** Pre-K.1 mass-fraction authoring was (Nd=0.60, Dy=0.20),
normalized shares (0.75, 0.25), HHI 0.625. Post-K.1 dependency authoring is
(Nd=1.00, Dy=0.90), normalized (0.526, 0.474), HHI 0.501. The two
dependencies now look "balanced" from the aggregation perspective — the
axis lost 0.124 of signal for a strictly more-honest reading of the inputs.
This is the ndfeb severity drop of −0.042 captured in
`docs/generated/severity_diff_pass_k1.md` under STRUCTURAL.

Neither `normalize` setting handles the new semantics.

## §2.2 Blast radius — inbound share sums

Reproduced from committed `data/ai/edges.json` via scratch. All buckets
scoped to a single node × stage × supply_category.

**7 buckets currently exceed sum 1.0:**

| node | stage | category | sum | n_suppliers |
|---|---|---|---:|---:|
| mineral:neodymium | mines | — | 1.170 | 7 |
| mineral:neodymium | refines | — | 1.100 | 3 |
| mineral:dysprosium | refines | — | 1.010 | 3 |
| product:ndfeb_magnets | input_to | — | 1.900 | 2 |
| country_region:usa | located_in | — | 30.000 | 30 |
| country_region:south_korea | located_in | — | 2.000 | 2 |
| country_region:japan | located_in | — | 4.000 | 4 |

Three flavours:

- **Nd / Dy over-mining bookkeeping (`mineral:*_[mines|refines]`).** These
  are on `known_share_offenders.txt` (pinned). Mining shares total 1.0
  world; when three regions each claim ≥ ⅓, sums exceed 1 by construction.
  This is pre-K.1 modelling debt, unrelated to the K.1 semantic change.
- **NdFeB Magnets input_to (1.90).** This IS the K.1 semantic change —
  the two co-critical dependencies each near 1.0 under §4.1.
- **country_region located_in (2 – 30).** These are corporate-location
  edges: every company `located_in` a country accumulates on the country's
  inbound. Not concentration signal; `located_in` is not in
  `SUPPLY_EDGE_TYPES` so it does not contribute to `inbound_hhi`. Cosmetic
  count only.

**Real signal count: 1 K.1 case (ndfeb) + 3 pre-K.1 pinned cases (Nd/Dy).**

**Per-stage aggregated across categories, 17 nodes have sum > 1.0** —
mostly `supplies` on hyperscalers/designers where multiple supply
categories accumulate (NVIDIA supplies sum 3.03 = foundry_wafers +
memory + gpu-adjacent categories). Not directly relevant to HHI, which
splits supplies per-category before aggregating; recorded for
completeness.

### §2.2.1 The 29 queued edges — future risk

Queued edges by target (`docs/generated/input_share_audit.md`, current
values):

| target | current input_to sum | # queued edges |
|---|---:|---:|
| company:vertiv | 0.530 | 2 |
| company:nvidia | 0.500 | 1 |
| company:siemens_energy | 0.500 | 1 |
| company:ge_vernova | 0.450 | 2 |
| company:quanta_services | 0.300 | 1 |
| facility:the_citadel | 0.080 | 5 |
| company:samsung, company:tsmc, company:sk_hynix, company:micron | 0.080 each | 1 each |
| facility:stargate_abilene, facility:vantage_frontier | 0.080, 0.080 | 1, 2 |
| company:xai, openai, constellation_energy, duke_energy, nextera_energy | 0.000 | 1 – 3 each |

**Zero of the 17 targets are currently at or above sum 1.0.** No queued
edge would deepen an existing >1 bucket on contact.

But the queued edges include HBM→NVIDIA (currently 0.30, cost-basis) —
if re-authored on dependency basis (~0.85, per K.1 §5.4 hint), NVIDIA's
input_to jumps to ~1.05. Similarly CoWoS→NVIDIA (~0.20 → ~0.85) would
add another ~0.65. Under honest dependency-basis authoring, **NVIDIA's
input_to bucket would sum to ~2.0**. And this is one hyperscaler; the
same logic applies to every consumer with HBM + CoWoS + copper + arm_core_ip
+ EDA all rising together.

**Expected outcome of an unmodified rollout of the queued 29: 4+ additional
nodes' inbound HHI would DROP as their share sums pass 1.0** and
normalize=true redistributes toward equal shares. The formula lies more
loudly as the data gets more honest. This is the disease this diagnosis
exists to name.

## §2.3 Aggregator options — analysis only

Four candidates evaluated against the four properties dependency-share
authoring requires: monotonic in each input, bounded [0,1], no summation
constraint, coexists with per-stage/per-category structure.

### Option A — restore HHI's summation constraint

Revert K.1 §4.1. Author `input_share` as share of the consumer's inputs
(the pre-K.1 convention). Buckets partition to 1; HHI works as designed.

- Pros: no code change. Preserves the ndfeb reading before K.1 (0.625).
  Cross-pass severity comparisons unchanged.
- Cons: **loses the dependency signal** that K.1 §4.1 exists to represent.
  D-J-3 (cost/BOM under-representing critical) reopens as unsolved.
  Cheap-but-critical is back in the noise floor. Regresses the pass.
- ndfeb reading: 0.625 (pre-K.1).
- Coexists with per-stage / per-category: yes (current behaviour).
- Recommendation: **REJECT.** The whole point of K.1 was to abandon this
  reading.

### Option B — noisy-OR over dependency shares

Aggregator: `concentration = 1 − Π(1 − share_i)`. Already used by the
events system (`events.combine: noisy_or`) on the stated grounds that it
is bounded [0,1], monotonic, and does not require its inputs to sum to 1.

- Pros: **exactly the properties dependency shares need.** ndfeb becomes
  1 − (1 − 1.0)(1 − 0.9) = 1 − 0 = **1.0** — matches intuition (either
  input's withdrawal halts the product; concentration is total).
  Monotonic in each share. Adding a supplier can only raise concentration,
  never lower it — no perverse inversion.
- Cons: noisy-OR assumes **independence** of failures. Two co-critical
  inputs whose withdrawals are correlated (e.g. both sourced from China)
  are double-counted. HHI double-counts these too, so noisy-OR is not
  strictly worse. But if a future extension models supplier-supplier
  correlation, noisy-OR needs a correction term HHI does not.
- Where per-category logic uses noisy-OR internally: each category's
  contribution can still be its own noisy-OR, and the max-across-categories
  rule survives. Coexists with per-stage/per-category cleanly.
- ndfeb reading: 1.0. Materially different from HHI's 0.501; recovers the
  signal lost by normalize=true dilution.
- Recommendation: **STRONG CANDIDATE.** The graph already has the code
  path (`_combine` in `cascade.py`).

### Option C — max-share

Aggregator: `concentration = max(share_i)`. Take the largest single
dependency as the concentration reading.

- Pros: simplest to implement. Bounded [0,1] iff each share ≤ 1.
  No summation constraint. Behaves correctly under dependency semantics
  (largest binary dependency IS the effective concentration).
- Cons: **discards multi-supplier information entirely.** Two dependencies
  at 0.5 each read as 0.5 (same as a single dependency at 0.5). Loses the
  "many critical inputs stacking" signal.
- ndfeb reading: 1.0 (max of {1.00, 0.90}).
- Recommendation: **KEEP AS A FLOOR CANDIDATE.** Simpler than noisy-OR
  but loses information. Prefer noisy-OR unless implementation cost is
  a decisive factor.

### Option D — hybrid: HHI for market-share stages, noisy-OR (or dep-aware) for dependency stages

Aggregator dispatched per stage:

- **`mines`, `refines`**: keep HHI. These ARE market shares — countries'
  fractions of world mining/refining sum to 1 by physics. `input_share`
  here retains the K.1 pre-existing convention.
- **`supplies`, `input_to`, `component_of`**: noisy-OR (or max-share). These
  are dependency stages under §4.1 semantics.
- The stage-level combine (`combine: max`) survives — a node's inbound
  HHI is the max across stage aggregations, each computed with its own
  semantics.

- Pros: **honest to how the graph actually uses each stage.** Mining and
  refining have a legitimate market-share reading; supply/input/component
  do not. Preserves the K.1 dep-basis intent for dep stages without
  giving up the well-defined HHI for market stages.
- Cons: two mental models to track. The `input_share` field carries
  different meanings by stage; documentation must be crystal clear.
  Per-category logic within `supplies` needs the same dispatch (some
  categories are market-share — lithography is *ASML market share*
  arguably — others are pure dependency).
- ndfeb reading: 1.0 (input_to stage → noisy-OR / max).
- Recommendation: **PREFERRED long-term.** Matches the actual semantics
  of each stage. Highest implementation cost of the four; probably
  needs its own dedicated pass to land cleanly.

### Summary table

| option | ndfeb | in [0,1] | monotonic | keeps dep-semantics | coexists per-stage / per-cat | cost |
|---|---:|---|---|---|---|---|
| A HHI + summation | 0.625 | yes | yes | **no** | yes | none |
| B noisy-OR | 1.000 | yes | yes | yes | yes | small |
| C max-share | 1.000 | yes | yes | yes (info-loss) | yes | trivial |
| D hybrid | 1.000 (input_to via B/C) | yes | yes | yes | needs care | large |

Recorded in `k2_decisions.md::D4`.

## §2.4 min_suppliers under dependency semantics — INVERTS

Both stage-level and per-category rules exclude buckets with fewer than 2
modelled suppliers (`min_suppliers_for_concentration: 2`). Rationale from
`config/scoring.yaml`: *"a single share normalizes to HHI 1.0 and cannot
be distinguished from unmodelled data."*

Under dependency semantics this inverts. A sole supplier at `input_share`
0.95 is **the most dangerous configuration the model can represent** —
one dependency, near-total function loss on withdrawal. Currently it is
discarded as incomplete data.

### §2.4.1 Currently zeroed

Stage-level (single_supplier_stages) — 13 nodes:

- `product:rf_power_semis` [input_to] — gallium sole modelled input. This
  is the mechanism the RF & Power xfail names.
- `company:tsmc, sk_hynix, micron, amazon, microsoft, meta, quanta_services`
  [input_to] — copper as sole modelled input.
- `facility:colossus, stargate_abilene, vantage_frontier, the_citadel`
  [input_to] — NdFeB Magnets sole input.
- `product:arm_core_ip` [supplies] — company:arm sole producer.

Per-category (`min_suppliers < 2` within `supplies`):

| category | # zeroed consumers | consumers |
|---|---:|---|
| `foundry_wafers` | 7 | broadcom, amd, google, amazon, microsoft, meta, marvell |
| `cpu_core_ip` | 5 | nvidia, google, amazon, microsoft, arm |
| `gpu_accelerators` | 4 | google, amazon, microsoft, meta |
| `cooling` | 4 | facility × 4 |
| `ai_asics` | 3 | google, amazon, meta |
| `deposition`, `power_generation` | 2 each | (equipment / power) |
| `memory`, `ip` | 1 each | nvidia, arm_core_ip |

**Under dependency semantics, every one of these single-source buckets
should be counted at input_share = 1.0 (or the authored share, if < 1),
not zeroed as "ambiguous."**

`cpu_core_ip → NVIDIA` at 0.25 is a real ~25 % dependency on ARM ISA;
zeroing it under min_suppliers=2 says "we don't know" when what the graph
does know is "sole source, moderate dependency." Different claim.

### §2.4.2 If the 29 queued edges land, adds to the zeroed set

Queued edges include multiple single-source targets that would sit alone
in their category:

- HBM → hyperscalers (google, amazon, microsoft, meta): if HBM is authored
  as a single-source supply into their supplies bucket, `memory` category
  becomes single-source at each and would be zeroed.
- CoWoS → hyperscalers: same shape.
- copper → hyperscalers: same shape (already zeroed for micron/etc.).

Rough estimate: **10 – 15 additional consumer × category pairs** would be
zeroed by the current rule under queued dep-basis authoring.

### §2.4.3 Recommendation for the fix pass

The min_suppliers rule and the aggregator choice (§2.3) are **the same
underlying problem** viewed at two layers. Both assume HHI-style
market-share semantics; both invert under dependency semantics.

Recommendation: fix both together in the aggregator-decision pass. If
Option B (noisy-OR) is chosen, min_suppliers becomes a floor for a
different reason: with one supplier at share s, noisy-OR = s directly,
and there is no HHI-normalizes-to-1 artefact. The rule can drop to
`min_suppliers_for_concentration: 1` — single-source buckets contribute
their authored share, which is now the honest signal.

Do not change today.

## §2.5 §7 pre-registration scorecard for §2

| # | pre-registration | HIT / MISS |
|---|---|---|
| 6 | At least one scored node has inbound shares summing above 1.0; expected: `ndfeb_magnets` at 1.90 | **HIT** — 7 buckets over 1.0 total (see §2.2); ndfeb at 1.900 exactly |
| 7 | Under `normalize: false`, `ndfeb_magnets` inbound HHI exceeds 1.0 — i.e. leaves the axis range | **HIT** — 1.8100 raw sum-of-squared-shares (see §2.1 table) |
