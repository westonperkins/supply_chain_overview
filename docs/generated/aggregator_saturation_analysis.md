# Aggregator saturation + `min_suppliers` pairing — diagnosis (Pass K.2.1 §3, §4)

**DIAGNOSIS ONLY.** No aggregator changed. No `min_suppliers` change. This
document completes what K.2 §2.3–§2.4 asked for and evaluates D4 against
the failure mode K.2 did not surface.

## §3.1 Saturation — the mechanism

Noisy-OR: `combined = 1 − Π(1 − share_i)`. If ANY single input reaches
share = 1.0, the entire product collapses to 0, and `combined = 1.0`
regardless of every other input. All discrimination among such buckets
disappears.

Under dependency semantics an input at share = 1.0 means "withdrawal
halts the consumer's function completely" — a genuinely binary dependency.
K.1 authored two such inputs directly:

- `mineral:neodymium → product:ndfeb_magnets` at **1.00** (no Nd, no NdFeB)
- `company:arm → product:arm_core_ip` at **1.00** (sole producer)

Neither is an outlier under the K.1 §4.1 definition — they are the
central case of what dependency-basis authoring should produce.
Saturation is therefore not an edge case; it is the expected shape of
the graph after correct authoring.

## §3.2 Quantified — noisy-OR on the current graph

Reproduced from committed `data/ai/edges.json` at HEAD `bc27969`. Every
scored node's inbound `input_share` values fed through `noisy-OR` with
each value clamped to [0, 1].

### §3.2.1 Nodes reaching noisy-OR concentration = 1.0 today

**2 of 31 scored nodes** saturate on current committed shares:

| node | reason |
|---|---|
| `product:ndfeb_magnets` | neodymium input_share = 1.00 alone forces saturation; dysprosium (0.90) adds nothing measurable |
| `product:arm_core_ip` | `company:arm → product:arm_core_ip` = 1.00 (sole producer) forces saturation |

### §3.2.2 Distribution under noisy-OR

Inbound-noisy-OR concentration across the 20 scored nodes with modelled
inbound supply-flow edges (11 leaf-nodes have no inbound and are omitted):

| bucket | count |
|---|---:|
| ≥ 0.99 | 9 |
| 0.90 – 0.99 | 4 |
| 0.50 – 0.90 | 3 |
| < 0.50 | 4 |

- max: 1.0000
- median: 0.9801
- min: 0.3000

**9 of 20 nodes sit at or above 0.99 inbound.** The top of the
distribution is compressed. Under noisy-OR the current graph's inbound
concentration axis loses most of its resolution at the top — the
distinction between saturated (1.0) and near-saturated (0.99+) is
determined by trailing digits of the second- and third-largest shares,
which are precisely the values K.1 §4.1 semantics say do NOT distinguish
the consumer's exposure ("either input's withdrawal halts function").

### §3.2.3 After the queued 29 land

Using the §2.3 collision analysis from `hhi_blast_radius.md`:

- 3 `collides` edges push their buckets over 1.0 — each is a bucket
  where noisy-OR would saturate on contact.
- 10 `safe` edges are all sole-supplier buckets today; re-authored at
  any dependency value ≥ 1.0, each becomes another saturated bucket
  (their `others_sum = 0` was WHY they were safe in the sum test —
  under noisy-OR, one supplier at 1.0 IS the whole product).
- 16 `undeterminable` sit at various threshold points; those authored
  at dep ≥ 1.0 all saturate.

**Rough post-queued-29 estimate: 15 – 20 of the 20 non-leaf scored nodes
would sit at noisy-OR ≥ 0.99.** The axis effectively stops
discriminating at the top of the graph.

### §3.2.4 Gap survival under approximate noisy-OR severities

Approximate severity under `noisy_or_inbound × (1 − substitutability) ×
lead_time_norm` and current outbound (max of inbound-noisy-OR and current
outbound_criticality goes into `concentration`):

- Median: **0.1884** (was 0.1949 under current HHI)
- Median gap: **0.0122**, threshold at separation_factor=3: **0.0365**
- **6 separating gaps survive** (was 7 under current HHI)

Three boundaries can plausibly still be placed under `derive_thresholds`'s
size-ordering. But the top of the distribution now includes 9 nodes
within 0.20 of each other where under HHI it was 4 — the "critical" gap
becomes harder to isolate as more nodes cluster at the ceiling.

**Consequence.** Under noisy-OR the boundary problem does not
disappear; it migrates from the bottom (K.2 §1's moderate-boundary
collapse) to the top (a compressed critical/high band). Diagnosis A's
retry loop closes the bottom failure; a top-of-distribution failure is
harder to address by retry because the compression is structural, not a
selection artefact.

## §3.3 Re-evaluate options against saturation

Re-scoring the K.2 §2.3 four options against the saturation failure
mode.

| option | ndfeb reading | # saturated today | in [0,1] | resolution at top | verdict |
|---|---:|---:|---|---|---|
| A HHI + restore summation | 0.625 (renormalize) | 0 | yes | preserved | reverts K.1 §4.1 |
| B noisy-OR | **1.000** | **2 today, 15–20 post-queued-29** | yes | **collapses** at top | ndfeb ok, top-of-distribution problem |
| C max-share | **1.000** | 2 today, similar post-queued | yes | collapses at top | same saturation as noisy-OR |
| D hybrid per-stage | 1.000 for input_to via noisy-OR/max; HHI for mines/refines | same | yes | mixed | inherits the saturation for input_to |

**All three non-A options saturate.** The saturation is inherent to
dependency semantics, not the aggregator — any function that maps
"input at share 1.0 (binary dependency)" to "concentration 1.0" will
saturate whenever multiple binary dependencies are authored on the same
consumer. Only Option A avoids saturation, and it does so by rejecting
the K.1 §4.1 semantic, which regresses the pass.

**Mitigations** that keep dependency semantics but reduce saturation:

**B1 — noisy-OR with authored cap.** Ban `input_share = 1.0` by author
convention; cap at, say, 0.95. Preserves ordering: an authored 0.95
means "≥95% of function lost on withdrawal" — the residual 5% is
authored uncertainty, not an assertion that some function survives.
Under noisy-OR two 0.95 inputs give `1 − 0.05·0.05 = 0.9975` — still
near-saturated but distinct from a single 0.95 (0.9500). Preserves
ordering under multi-input stacking.

- ndfeb reading (Nd 0.95 + Dy 0.85 substituted for the current
  1.00/0.90): `1 − 0.05·0.15 = 0.9925` (down from 1.000).
- Cost: an authoring convention rather than a numeric change. The
  0.95 cap has no principled basis — it is an epsilon choice, and one
  Weston would need to sign off on.

**B2 — evidentiary bar for `input_share = 1.0`.** Reserve exactly 1.0
for a documented class of edges: single-source AND no substitute AND no
graceful degradation. NdFeB→Nd meets it (no Nd, no product). NdFeB→Dy
plausibly does NOT — 10% low-temp NdFeB survives without Dy (the K.1
author's own reasoning). If applied honestly, this brings ndfeb to
noisy-OR of (Nd 1.00, Dy 0.90) = still saturated because of Nd alone;
so B2 only reduces saturation for cases where NO input actually meets
the bar.

- Requires authoring-review discipline: each 1.0 attaches an
  evidentiary note. Cost: friction on every dep-basis author.

**B3 — noisy-OR replaced with a bounded sum that preserves ordering.**
Aggregator: `combined = 1 − max(0, 1 − Σ share_i²·w_i)` for some weight
w_i, or similar. Not a standard function; inventing one has the same
tuning-toward-tier-membership risk as authoring cost figures without
derivation (see §5). Reject on principle.

**Recommendation update to D4.**

Noisy-OR **remains the strongest candidate** despite saturation, with
**caveats**:

1. Saturation is real and material — 9 of 20 nodes at ≥ 0.99 today, and
   the top of the distribution compresses under queued-29 re-authoring.
2. Mitigation **B1 (0.95 cap)** is the smallest change that recovers
   top-of-distribution resolution without regressing dep semantics.
   Preserves ordering under multi-input stacking.
3. **Do NOT recommend B2** (evidentiary bar) — the bar is
   author-judgment-dependent and would reintroduce tuning-toward-target
   risk.
4. The boundary-derivation retry loop from Diagnosis A remains
   necessary regardless of aggregator choice; but under noisy-OR + B1
   the boundary problem may shift to the top of the distribution (§3.2.4)
   and Diagnosis A's retry addresses only the bottom. **A top-of-distribution
   guard may be needed** — flag for a follow-up diagnosis or the
   fix-pass.

## §4 `min_suppliers_for_concentration: 1` pairing — full impact

### §4.1 Stage-level buckets currently zeroed (13)

Reproduced from `n.dynamic.single_supplier_stages`:

| node | stage | supplier | raw share |
|---|---|---|---:|
| `product:rf_power_semis` | input_to | mineral:gallium | 0.900 |
| `company:tsmc` | input_to | mineral:copper | 0.080 |
| `company:sk_hynix` | input_to | mineral:copper | 0.080 |
| `company:micron` | input_to | mineral:copper | 0.080 |
| `company:amazon` | input_to | mineral:copper | 0.120 |
| `company:microsoft` | input_to | mineral:copper | 0.120 |
| `company:meta` | input_to | mineral:copper | 0.120 |
| `company:quanta_services` | input_to | mineral:copper | 0.300 |
| `facility:colossus` | input_to | product:ndfeb_magnets | 0.080 |
| `facility:stargate_abilene` | input_to | product:ndfeb_magnets | 0.080 |
| `facility:vantage_frontier` | input_to | product:ndfeb_magnets | 0.080 |
| `facility:the_citadel` | input_to | product:ndfeb_magnets | 0.080 |
| `product:arm_core_ip` | supplies | company:arm | 1.000 |

**Under `min_suppliers_for_concentration: 1`, each of these unzeroes.**
Under the current HHI aggregator with `normalize=true`, each would
contribute HHI = 1.0 (single share normalizes to itself). Under
noisy-OR each would contribute its raw share directly.

Severity impact per node (current sub × lt_norm × new_conc), computed
under noisy-OR:

- `product:rf_power_semis`: currently `sub=0.25, lt=3.0, lt_norm=0.30`;
  conc = max(inbound noisy-OR 0.900, current outbound 0.082) = **0.900**;
  new severity = `0.900 × 0.75 × 0.30 = 0.2025` (was **0.0261**, ×7.8).
- `product:arm_core_ip`: currently `sub=0.40, lt=5.0`; noisy-OR inbound
  = 1.000; new severity ≈ 0.30 (was 0.0066, ×45).
- The other 11 (copper into hyperscalers, ndfeb into facilities) each
  add ~0.08–0.30 concentration inbound; severity moves modestly for
  each — none becomes a critical.

### §4.2 Per-category buckets currently zeroed (29)

**K.2 §2.4.1 stated 27.** Actual count is **29** — K.2 was one bucket
short (`company:arm supplies/cpu_core_ip` and `company:arm supplies/foundry_wafers`
both zero; K.2 counted arm's category-zeroed contribution imprecisely).
K.2 correction logged in §6.

Full list:

| consumer | category | supplier | share |
|---|---|---|---:|
| company:nvidia | memory | company:sk_hynix | 0.600 |
| company:nvidia | cpu_core_ip | product:arm_core_ip | 0.250 |
| company:broadcom | foundry_wafers | company:tsmc | 0.950 |
| company:amd | foundry_wafers | company:tsmc | 0.980 |
| company:intel | deposition | company:applied_materials | 0.550 |
| company:micron | deposition | company:applied_materials | 0.600 |
| company:google | foundry_wafers | company:tsmc | 0.300 |
| company:google | ai_asics | company:broadcom | 0.200 |
| company:google | gpu_accelerators | company:nvidia | 0.100 |
| company:google | cpu_core_ip | product:arm_core_ip | 0.200 |
| company:amazon | foundry_wafers | company:tsmc | 0.300 |
| company:amazon | ai_asics | company:marvell | 0.100 |
| company:amazon | gpu_accelerators | company:nvidia | 0.200 |
| company:amazon | cpu_core_ip | product:arm_core_ip | 0.350 |
| company:microsoft | foundry_wafers | company:tsmc | 0.300 |
| company:microsoft | gpu_accelerators | company:nvidia | 0.300 |
| company:microsoft | power_generation | company:constellation_energy | 0.100 |
| company:microsoft | cpu_core_ip | product:arm_core_ip | 0.150 |
| company:meta | foundry_wafers | company:tsmc | 0.300 |
| company:meta | ai_asics | company:broadcom | 0.150 |
| company:meta | gpu_accelerators | company:nvidia | 0.250 |
| facility:colossus | cooling | company:vertiv | 0.200 |
| facility:stargate_abilene | cooling | company:vertiv | 0.200 |
| facility:vantage_frontier | cooling | company:vertiv | 0.200 |
| facility:the_citadel | power_generation | company:vistra | 0.100 |
| facility:the_citadel | cooling | company:vertiv | 0.350 |
| company:arm | cpu_core_ip | product:arm_core_ip | 0.950 |
| company:arm | foundry_wafers | company:tsmc | 0.990 |
| product:arm_core_ip | ip | company:arm | 1.000 |

### §4.3 **Explicit xfail impact** — the number K.2 did not report

Committed xfails (`test_paper_chokepoints.py::KNOWN_MISS_XFAIL_REASONS`):

**`product:rf_power_semis`.** Reason string states verbatim:
*"RF & Power reads inbound=0 because gallium is its only modelled
input_to source and the stage-level min_suppliers=2 rule zeroes
single-source stage buckets. Outbound alone (0.082) doesn't lift
severity above moderate."*

Under `min_suppliers_for_concentration: 1` **the stated condition ends
entirely.** rf_power_semis inbound is no longer zeroed; the raw share
0.900 becomes signal, `inbound_hhi = 1.0` (normalize=true) or 0.900
(noisy-OR). The xfail reason ceases to describe the model's behaviour.

**Approximate post-change severity: 0.2025** (noisy-OR path, current
sub/lt). Approximate post-change median across scored nodes under
noisy-OR: **0.1884**. **0.2025 > 0.1884 → rf_power_semis PASSES the
test.** The xfail would XPASS.

**`product:hbm`.** Reason string states verbatim: *"HBM concentration is
capped at inbound_hhi 0.44 — three memory suppliers (SK Hynix 0.60,
Micron 0.21, Samsung 0.19) give a moderate HHI that the max combine
cannot lift above the critical threshold. Would move on either (a) a
memory sub-category split (hbm vs dram — spec explicitly forbids) or
(b) output_share populated on HBM → NVIDIA at paper-supported basis."*

HBM's `memory` category has 3 suppliers, so `min_suppliers=2` does not
zero it. **`min_suppliers` change alone does not affect HBM.** But
under noisy-OR replacing HHI:
- memory bucket noisy-OR: `1 − (0.4)(0.79)(0.81) = 0.744`
- HBM inbound concentration under noisy-OR: **0.744** (was 0.4402)
- Severity under noisy-OR: `0.744 × (1 − 0.05) × 0.30 = 0.2121`
- **0.2121 > 0.1884 → HBM PASSES the test.** The xfail would XPASS
  under noisy-OR without any `min_suppliers` change.

**Both xfails XPASS under D4-as-paired.** Under the K.1 §5 conditional-
xfail mechanism (`strict=False`), XPASS is a legitimate outcome — it is
what the mechanism was built to catch. This is a **material finding**
for the fix pass: D4 acceptance closes 2 of 2 pinned modelling gaps.

### §4.4 Separability

**Can the aggregator change ship without the `min_suppliers` change?**
Yes — but not cleanly.

Under noisy-OR + `min_suppliers=2` (current):

- rf_power_semis stays zeroed (still single-source input_to gallium);
  inbound_hhi 0.0, severity remains at current 0.0261 — xfail persists
  under this alternative pairing.
- HBM's memory bucket becomes noisy-OR 0.744 — xfail XPASSES via the
  aggregator alone.
- The 29 category-zeroed buckets remain zeroed; single-source
  categories continue to be dropped as "ambiguous" data. But under
  noisy-OR that framing is no longer the correct rejection reason —
  noisy-OR at 0.95 for a single supplier is a valid concentration
  reading, not an HHI-normalizes-to-1 artefact.

**Can the `min_suppliers` change ship without the aggregator change?**
Yes and it is worse.

Under HHI (normalize=true) + `min_suppliers=1`:

- rf_power_semis unzeroed; single share of gallium 0.900 normalized to
  itself gives HHI = 1.0. Severity `1.0 × 0.75 × 0.30 = 0.225` — xfail
  XPASSES.
- BUT single-source at share 0.001 also reads HHI = 1.0. This is
  exactly the "cannot distinguish real monopoly from unmodelled data"
  problem the rule was designed to prevent — reintroduced. The 12 other
  currently-stage-zeroed buckets would each contribute HHI = 1.0
  regardless of raw share, inflating concentration on hyperscalers etc.
  by artefact rather than signal.

**Both changes are needed together.** The pairing is not a corollary of
convenience — it is load-bearing. K.2 §D4's presentation of them as
paired was correct; K.2's failure to establish the pairing's mechanism
and xfail impact is what §4.4 completes.

## §7 pre-registration scorecard for §3 + §4

| # | pre-registration | HIT / MISS |
|---|---|---|
| 4 | Under noisy-OR with current shares, at least one scored node reaches inbound concentration exactly 1.0 | **HIT** — 2 nodes (ndfeb, arm_core_ip) at 1.0 today (§3.2.1) |
| 5 | Dropping `min_suppliers_for_concentration` to 1 changes the condition named in the `product:rf_power_semis` xfail reason | **HIT** — the reason states verbatim "zeroed by min_suppliers=2 rule"; with min_suppliers=1 that condition ends; §4.3 above |
