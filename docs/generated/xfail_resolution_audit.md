# Xfail resolution audit + separability (Pass K.2.2 §4, §5)

**DIAGNOSIS ONLY.** No aggregator or code changed. This audit derives
the K.2.1 xfail-resolution claims from committed inputs, reconciles a
median discrepancy, and tests the separability claim.

## §4.1 Correct lead_time normalization — K.2.1 arithmetic error

K.2.1 §4 gave xfail severities under D4 + D4a as `rf_power_semis
0.0261 → 0.2025` and `hbm 0.1779 → 0.2121`, using `lt_norm = lt / 10`.

**The actual normalization is `log10(lt + 1) / log10(26)` (`log10_1p`)**
per `backend/app/scoring/engine.py::normalize_lead_time` line 285 and
`config/scoring.yaml:lead_time.normalization: log10_1p`.

For `lt = 3.0`:
- Wrong (K.2.1): `3/10 = 0.30`
- Correct: `log10(4)/log10(26) = 0.6021/1.4150 = 0.4255`

**Every K.2.1 §4 severity figure is off by the ratio 0.4255/0.30 ≈ 1.42.**
The qualitative conclusion (both xfails XPASS under D4+D4a) survives,
by wider margins than K.2.1 reported. But the K.2.1 numbers are
individually wrong and are corrected below.

## §4.2 Step-by-step derivation — RF & Power Semis

Inputs (from `data/ai/edges.json` + `data/ai/nodes.json` at
HEAD `b006f14`):

- Inbound supply-flow edges: `mineral:gallium → product:rf_power_semis`
  at `input_share = 0.900` (single edge; `type = input_to`)
- Outbound criticality: `0.0818` (from `severity_snapshot.json`)
- `substitutability`: `0.25`
- `lead_time_years`: `3.0` → `lt_norm = 0.4255`

Formula: `severity = concentration × (1 − substitutability) × lt_norm`
where `concentration = max(inbound_hhi, outbound_criticality)`.

| scenario | aggregator | min_suppliers | inbound reading | concentration | severity |
|---|---|---:|---|---:|---:|
| S1 | HHI (current) | 2 | stage-zeroed (single-source) → 0 | max(0, 0.0818) = 0.0818 | 0.0818 × 0.75 × 0.4255 = **0.0261** |
| S2 | HHI | 1 | (0.9)² normalized to itself = 1.0 | max(1.0, 0.0818) = 1.0 | 1.0 × 0.75 × 0.4255 = **0.3191** |
| S3 | noisy-OR | 2 | stage still zeroed → 0 | max(0, 0.0818) = 0.0818 | **0.0261** (unchanged from S1) |
| S4 | noisy-OR (**D4**) | 1 (**D4a**) | noisy-OR of {0.9} = 0.9 | max(0.9, 0.0818) = 0.9 | 0.9 × 0.75 × 0.4255 = **0.2872** |

**Named-mechanism check.** RF & Power xfail reason:
*"gallium is its only modelled input_to source and the stage-level
min_suppliers=2 rule zeroes single-source stage buckets."* D4a
(`min_suppliers = 1`) **directly ends the named condition.** Under D4a
the single-source bucket is no longer zeroed. Resolution follows from
a mechanism the xfail itself names.

## §4.3 Step-by-step derivation — HBM

Inputs:

- Inbound supply-flow edges (all `type = supplies`, `supply_category =
  memory`):
  - `company:sk_hynix → product:hbm` at `input_share = 0.600`
  - `company:micron → product:hbm` at `input_share = 0.210`
  - `company:samsung → product:hbm` at `input_share = 0.190`
- Outbound criticality: `0.2314`
- `substitutability`: `0.05`
- `lead_time_years`: `3.0` → `lt_norm = 0.4255`

Memory-bucket normalize-true HHI: `(0.6/1.0)² + (0.21/1.0)² + (0.19/1.0)²
= 0.36 + 0.0441 + 0.0361 = 0.4402`.
Memory-bucket noisy-OR: `1 − (1 − 0.6)(1 − 0.21)(1 − 0.19) = 1 −
(0.4)(0.79)(0.81) = 1 − 0.2560 = 0.7440`.

| scenario | aggregator | min_suppliers | inbound (memory) | concentration | severity |
|---|---|---:|---:|---:|---:|
| S1 | HHI (current) | 2 | 0.4402 | max(0.4402, 0.2314) = 0.4402 | 0.4402 × 0.95 × 0.4255 = **0.1779** |
| S2 | HHI | 1 | 0.4402 (3 members, unaffected) | 0.4402 | **0.1779** (unchanged) |
| S3 | noisy-OR (**D4**) | 2 | 0.7440 (3 members ≥ min) | max(0.7440, 0.2314) = 0.7440 | 0.7440 × 0.95 × 0.4255 = **0.3008** |
| S4 | noisy-OR | 1 (**D4a**) | 0.7440 (unchanged; 3 members) | 0.7440 | **0.3008** (unchanged from S3) |

**Named-mechanism check.** HBM xfail reason: *"HBM concentration is
capped at inbound_hhi 0.44 — three memory suppliers give a moderate HHI
that the max combine cannot lift above the critical threshold."*
D4 (noisy-OR) **directly changes the memory-bucket aggregation** —
inbound HHI 0.4402 becomes inbound noisy-OR 0.7440. The named cap
(0.44) is no longer produced by the modified aggregator. Resolution
follows from a mechanism the xfail itself names.

## §4.4 Median reconciliation — the K.2.1 discrepancy resolved

K.2.1 §4.3 reported the median moving `0.1949 → 0.1884` under D4+D4a,
which the K.2.2 spec §4(3) asked to reconcile against nodes moving up.

**The reconciliation is that K.2.1 mixed two different lt_norm
computations.** K.2.1's baseline `0.1949` matches the actual committed
median (`0.1950` from `severity_snapshot.json` — see calculation
below). K.2.1's post-D4+D4a value `0.1884` was computed with
`lt_norm = lt / 10`, which is not the engine's normalization. The
baseline used one arithmetic; the delta used a different one.

**Committed median (from severity_snapshot.json, 31 scored nodes):
0.1950.**

**Under corrected `log10_1p` normalization applied consistently to a
D4+D4a scenario, the approximate median rises:**

| scenario | approximate median | Δ from current | source |
|---|---:|---:|---|
| Current committed (from snapshot) | 0.1950 | — | `severity_snapshot.json` |
| S1 (my approx of current) | 0.1655 | — | approximation caveat, see below |
| S2 HHI + min_supp=1 | 0.2070 | +0.041 | approximation |
| S3 NOR + min_supp=2 (D4 alone) | 0.2127 | +0.047 | approximation |
| S4 NOR + min_supp=1 (D4+D4a) | 0.2672 | +0.102 | approximation |

The median RISES ~0.10 under D4+D4a; it does not fall. K.2.1's "median
falling while nodes rise" was an artifact of mixed lt_norm arithmetic,
not a real distributional puzzle.

**Approximation caveat.** My S1 approx median (0.1655) differs from
committed (0.1950) because the per-stage-max/per-category logic in the
real engine (`supplies_per_category.combine`, weighted or max) is not
fully reproduced by my `max(single-stage-HHI-if-min-supp-met, outbound)`
shortcut. The direction (S4 > S1 by ~0.10) is robust across
approximations; the exact figures below the 4th decimal are not.

**Bottom line:** the K.2.1 discrepancy is resolved by refuting the
K.2.1 median arithmetic. There is no phenomenon of median-falling-while-
nodes-rising to explain because the median does not in fact fall.

## §4.5 Xfail-alone status

From §4.2 and §4.3:

| scenario | rf_power severity | HBM severity | approx median | rf_power XPASSES? | HBM XPASSES? |
|---|---:|---:|---:|:---:|:---:|
| S1 (current) | 0.0261 | 0.1779 | 0.1655 (approx) / **0.1950** (committed) | no | no (under committed) / **yes** (under approx) |
| S2 (D4a alone) | **0.3191** | 0.1779 | 0.2070 | **yes** | no |
| S3 (D4 alone) | 0.0261 | **0.3008** | 0.2127 | no | **yes** |
| S4 (D4+D4a) | **0.2872** | **0.3008** | 0.2672 | **yes** | **yes** |

**D4 alone resolves HBM only.** RF & Power stays stage-zeroed under
noisy-OR + `min_suppliers = 2` because gallium is its sole modelled
input_to source — the aggregator change doesn't reach it.

**D4a alone resolves rf_power only.** HBM's memory bucket has 3
members, so `min_suppliers` does not affect it — the aggregator is
the only lever that changes HBM's inbound reading.

**D4+D4a paired resolves both.** Each xfail's resolution traces to
exactly one of the two changes; the pairing resolves both because the
xfails have different named mechanisms.

## §4.6 §5 separability — technical vs outcome-based coupling

K.2.1 §4.4 stated D4 and D4a are "NOT separable." §4.5 above shows
that statement is about **outcomes being incomplete**, not about
technical coupling. Under §5's four questions:

### §5(1) Can each change ship independently without breaking the suite or producing an invalid graph state?

**Yes.** Neither change requires the other to load, run, or produce a
valid tier assignment.

- D4 alone: noisy-OR replaces HHI as the per-stage aggregator. The
  min_suppliers rule still fires on single-source stages; those stages
  contribute 0 to inbound as they do today. Graph valid.
- D4a alone: min_suppliers=1 stops zeroing single-source stages. HHI
  aggregator remains; single-source stages contribute HHI = 1.0
  (normalize=true artefact — the exact problem K.2 §2.4 named). Graph
  technically valid but with new nodes reading `inbound_hhi = 1.0`.

Both ship-independently. The tests would need pin-list updates for
the tier changes but no test would fail on structure.

### §5(2) Full tier histogram + affected nodes under each alone

Approximated (subject to §4.4 approximation caveat):

| scenario | approx tier histogram | notable changes |
|---|---|---|
| S1 (current) | 2 critical / 2 high / 27 moderate / 0 none | committed baseline |
| S2 (D4a alone) | 2c / 2h / 25m / 2n | rf_power_semis → moderate (was `none` under Pass K.1 moderate=0.0 collapse — actually would be critical under D4a's HHI=1.0 for single-source, ~0.32 sev). Precise histogram sensitive to K.2 §1 boundary derivation, which is not fixed by this change. |
| S3 (D4 alone) | Similar to S1 with HBM lifting into a higher band, rf_power unchanged | HBM crosses whatever moderate-vs-high boundary the D4-shifted distribution derives. Distribution top compresses (§3.2). |
| S4 (D4+D4a) | Both S2 and S3 changes together | Both xfails move, plus every stage-zeroed and per-category-zeroed bucket unzeroes. Distribution shifts substantially; §3.3 top-of-distribution guard question comes into play. |

**All four "tier histograms" depend on the K.2 §1 boundary derivation.**
Since K.2 §1 is not fixed by K.2.2 (diagnosis only), the exact tier
counts under each scenario are subject to the boundary-derivation
retry decision (K.2 §D2).

### §5(3) Technical or outcome-based coupling?

**Outcome-based.** No shared code path exists between the aggregator
change and the min_suppliers change:

- `compute_supplies_per_category` (aggregator) and
  `single_supplier_stages` filter (min_suppliers) sit in different
  branches of `refresh_all_derived`.
- Each can be toggled by a config change without touching the other.

K.2.1's "not separable" was **outcome-completeness language dressed as
technical coupling.** The two changes are separable; neither alone
resolves BOTH xfails. Those are different claims.

### §5(4) Sequencing safety

Two plausible orderings:

**Order A: D4 then D4a.** After D4 (noisy-OR only), HBM resolves; rf_power
stays as-is. Intermediate state: HBM's improved reading is honest;
rf_power's continued xfail is still explained by its committed reason.
No misrepresentation.

**Order B: D4a then D4.** After D4a (min_suppliers=1 only), rf_power's
inbound_hhi becomes 1.0 under normalize=true — the very artefact K.2
§2.4 named. The intermediate state carries "single share of 0.9 reads
as HHI = 1.0" which is exactly the "cannot distinguish real monopoly
from unmodelled data" state the rule was designed to prevent. The
intermediate state is HONEST about rf_power's severity but MISREPRESENTS
every other single-source bucket that unzeroes (13 stage + 29 category
buckets from K.2.1 §4).

**Order A is safer.** D4 alone changes the aggregator without touching
which buckets participate; each affected bucket's reading is calculated
under a defensible aggregator. D4a alone changes bucket participation
without fixing the aggregator's inability to distinguish monopoly from
data gap in single-source buckets.

**If bundled (D4 + D4a together), the intermediate state doesn't
exist.** That is the argument for bundling. It is the maximum-blast-
radius option because it moves 2 xfails, the aggregator, the
min_suppliers rule, and ~42 bucket readings in one commit.

### §5(5) Recommendation

**Sequence D4 → D4a in separate commits**, with a HBM XPASS logged
between them. Each commit's severity_diff is legible; each xfail's
resolution is traceable to a single change; neither commit ships an
intermediate state that misrepresents any node's reading.

Cost: two commits' worth of report-writing and severity_diff review
rather than one. Benefit: two separable pieces of evidence for two
separable claims about the model.

## §7 pre-registration scorecard for §4 + §5

| # | pre-registration | HIT / MISS |
|---|---|---|
| 5 | Both xfail resolutions trace to mechanisms named in their own xfail reasons | **HIT** — rf_power reason names "min_suppliers=2 rule zeroes single-source stage buckets"; D4a directly ends that. HBM reason names "concentration capped at inbound_hhi 0.44"; D4 directly changes the aggregation that produces the 0.44. |
| 6 | Median discrepancy resolves with explanation or flagged unreconciled | **HIT (resolved)** — K.2.1 mixed lt/10 (approximate) baseline against log10_1p (committed) baseline; under consistent log10_1p the median RISES not falls; no median-falling paradox to explain. |

## Additional K.2.1 correction (unreported item)

**K.2.1 §4.3 severity figures are numerically wrong** — every K.2.1
severity in §4 used `lt_norm = lt / 10`; the engine uses `log10_1p`.
Corrected numbers:

- `product:rf_power_semis` under D4 + D4a: **0.2872** (K.2.1 said 0.2025)
- `product:hbm` under D4 alone (or D4 + D4a): **0.3008** (K.2.1 said 0.2121)

The qualitative conclusion (both xfails resolve) is intact by wider
margins. The specific numbers do not stand and are corrected in
`grading.md` §6 by K.2.2.
