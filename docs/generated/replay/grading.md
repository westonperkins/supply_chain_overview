# Pass J Phase B — grading

> ⚠ **Pass K §6 provenance banner.** Every number in this document refers to
> the replay artifacts computed on the **Pass J 67-node graph** (commit
> `1bd6090`). Those artifacts are archived verbatim under
> `docs/generated/replay/archive/pass_j_67node/`. The live artifacts in
> `docs/generated/replay/*.md` and `summary.md` may regenerate against a
> newer graph (Pass K adds design-IP nodes and moves scoring); do NOT
> compare cited numbers below against a later regeneration. Re-grading is a
> separate pass with its own blinding discipline (Pass J.1 §10 four-phase
> rule); Pass K does not re-run the replay.

**Discipline reminder.** Axes were authored in Phase A (commit `e111af7`) and
frozen. This grading document was written from `data/ai/replay/outcomes.json`
in a separate commit. No Phase A file has been edited to reach any grade
below; see `git log --oneline` for ordering evidence.

Each event answers three questions:

1. **Reach.** Did the cascade touch the nodes reality moved? Both misses
   and spurious hits count.
2. **Ranking.** Where does this event sit in the model's severity ordering
   vs the observed disruption ordering across all events?
3. **Classification.** For every mismatch, one of: **DATA GAP**,
   **FORMULA ARTIFACT**, **AXIS EXPRESSIVENESS**, **HONEST DISAGREEMENT**.

Ordinal from `outcomes.json` (1 = most disruption, 7 = least):
`HBM(1) > REE(2) > gallium(3) > kachin(4) > taiwan(5) > asml(6) > nexperia(7)`.

> **⚠ Pass J.1 correction (§1).** The paragraph immediately below stated the
> model ordering was `by (origin_scale, max_delta)`. That lexicographic sort
> does NOT produce the ordering that follows it (under that sort, kachin
> ranks 3, not 5). The ordering was in fact a pure `max_delta` sort.
> Rank is now computed in `backend/scripts/replay_events.py::_rank_events`
> and emitted in `summary.md` as `model_rank`. All grading below cites
> `model_rank` from that file rather than restating an ordering.

Model ordering by `(origin_scale, max_delta)` from the summary:
`REE(1) > gallium(2) > taiwan(3) > HBM(4) > kachin(5) > asml(6) ≈ nexperia(7)`.

> **⚠ Pass J.1 restatement.** The authoritative model ordering is now
> `model_rank` in `docs/generated/replay/summary.md` (metric: `max_delta ↓`,
> tie-broken by `nodes_reached ↓, origin_scale ↓, event_id ↑`):
> `REE(1) > gallium(2) > taiwan(3) > HBM(4) > kachin(5) > asml(6) ≈ nexperia(7)`.
> An alternate metric `rank_by_origin_scale` is also emitted (Pass J.1 §2):
> `REE(1) > gallium(2) > kachin(3) > taiwan(4) > HBM(5) > asml(6) ≈ nexperia(7)`.
> The two metrics disagree by ≥ 2 slots on **kachin** (3 ↔ 5) — see F-J-5.

Two big rank inversions to explain: **HBM 1→4** (the model badly under-fires
the story of 2024-25) and **Taiwan 5→3** (moderate model over-fire).

> **⚠ Pass J.1 restatement of A-J-2 inversion.** Under `model_rank` the HBM
> inversion is 1 → 4; under `rank_by_origin_scale` it is 1 → 5. A-J-2's row
> in the findings table quotes the primary-metric number and cross-notes the
> alternate.

---

## J-2024-04-taiwan-quake

**Model:** 13 nodes reached, max Δ +0.012 at TSMC; no tier change; ranking 3 of 7.
**Reality:** minor, short-lived, no allocation cuts; ranking 5 of 7.

- **Reach.** The nodes moved (TSMC downstream to NVIDIA/AMD/Broadcom) are
  the plausibly-affected ones. The specific-fab granularity reality had
  (Fab 18 vs older nodes) cannot be represented — the graph models TSMC
  at company level. Reach is correct up to the model's granularity.
- **Ranking.** Model puts it 3, reality puts it 5. Model over-fires by
  attributing 0.05 concentration_delta at TSMC as if TSMC lost 5% of
  something structural; reality was a same-day pause. Two rank slots too high.
- **Classification.** **FORMULA ARTIFACT (F-J-1)** — the concentration axis
  does not distinguish "structural share loss" from "transient halt";
  authoring 0.05 was a reasonable estimate but the pipeline reads it as a
  permanent 5-point concentration hit. Absent time-decay, transient events
  are systematically overweighted at the tier the axis lands on.

## J-2024-09-asml-export

**Model:** 0 nodes reached, cascade empty.
**Reality:** measurable ASML-China revenue impact; ZERO impact on AI-facing
supply because ASML→non-China customer relationships are unchanged.

- **Reach.** Correct null result on AI-compute-facing supply. But the model
  reached zero for the *wrong reason*: it does not have an ASML→China edge
  to lose (**DATA GAP D-J-1**), and it has no axis to express demand-side
  restriction on a supplier (**AXIS EXPRESSIVENESS A-J-1**). Match by
  coincidence, not by mechanism. If the graph ever added an ASML→China
  edge, the current formula would still produce zero without a demand-side
  axis.
- **Ranking.** Model 6, reality 6. Correct rank; wrong mechanism.
- **Classification.** **AXIS EXPRESSIVENESS (A-J-1)** primary;
  **DATA GAP (D-J-1)** secondary. Recorded as a finding despite the ordinal
  match because the mechanism is the load-bearing part.

## J-2024-10-kachin-kia

**Model:** 8 nodes reached, max Δ +0.003 at dysprosium; ranking 5 of 7.
**Reality:** moderate price effect via feedstock tightening, resolved over
1-2 quarters; ranking 4 of 7.

- **Reach.** Correct in direction — Kachin → mineral:dysprosium fires
  as the graph's path predicts. But the magnitude is tiny (+0.003 at
  dysprosium) because:
  1. Kachin has no `baseline_severity` (unscored origin) so the walk seeds
     from `concentration × magnitude × confidence`, and Kachin's
     concentration is low.
  2. Even after the walk, the dysprosium → NdFeB Magnets outbound edge is
     input_share 0.20 — dysprosium is a small fraction of NdFeB by mass —
     so the cascade dampens hard downstream of the mineral.
- **Ranking.** Rank 5 vs reality's rank 4. One slot too low.
- **Classification.** **FORMULA ARTIFACT (F-J-2)** — an unscored-origin
  event with low concentration under-fires even when the graph HAS the
  correct path. The paper's canonical "news says Kachin, impact is
  dysprosium" case is technically carried but with severity almost lost in
  the noise floor. Needs either an unscored-origin seed floor or an
  input-share-independent path signal for upstream feedstock events.

## J-2024-11-hynix-hbm

**Model:** 13 nodes reached, max Δ +0.008 at SK Hynix; no tier change;
ranking 4 of 7.
**Reality:** **the most disruptive event of the set** — binding constraint
on AI capex through 2025; ranking 1 of 7.

- **Reach.** The nodes moved (SK Hynix → HBM → NVIDIA/AMD/hyperscalers)
  are the ones reality moved. Reach is correct.
- **Ranking.** Rank 4 vs reality's rank 1. **Three rank slots too low —
  the largest miss in the set.**
- **Classification.** **AXIS EXPRESSIVENESS (A-J-2)** — the event's true
  magnitude sits in `lead_time_delta = 0.25` and `substitutability_delta =
  0.15`, but the pipeline reads only `concentration_delta` (authored
  honestly at 0.05 because no share moved). The formula CAN'T see this
  event as it was: capacity was committed forward, share was unchanged,
  supply tightened via time, not concentration. This is the exact case the
  Phase A axis-authoring rule was designed to expose: the gap between what
  the event needed and what the read axis could carry.

## J-2024-12-china-gallium

**Model:** 34 nodes reached, max Δ +0.077 at RF & Power Semis, gallium
tier `high → critical`; ranking 2 of 7.
**Reality:** sustained gallium supply premium through 2025, no widespread
outage; ranking 3 of 7.

- **Reach.** Correctly reaches gallium (the direct target) and RF & Power
  Semis (the primary downstream product). BUT: the walk also lights up
  **dysprosium, neodymium, indium, copper** — every one of China's
  outbound minerals — because the event is applied at country_region:china
  with a single `concentration_delta`. The ban was on gallium and germanium
  specifically; the cascade spuriously fires on all other China-supplied
  materials.
- **Ranking.** Rank 2 vs reality's rank 3. Roughly right; over-fire by
  one slot.
- **Classification.** **FORMULA ARTIFACT (F-J-3)** — country-origin fanout.
  A single-magnitude event at a country_region walks over every outbound
  supply edge equally. Real ban semantics ("this mineral, not that one")
  cannot be represented without per-edge scoping on the event.
  **DATA GAP (D-J-2)** secondary — germanium is not modelled and was
  dropped from `entities_matched` in Phase A. If ingestion is to run on
  Dec 2024 material, germanium needs a node.

## J-2025-04-china-rees

**Model:** 34 nodes reached, max Δ +0.090 at RF & Power Semis (?), tier
change; ranking 1 of 7.
**Reality:** dysprosium/terbium price shock, magnet-manufacturer
warnings, downstream motor/actuator effects; ranking 2 of 7.

- **Reach.** Correctly reaches dysprosium (direct target). But note the
  top-affected node from the summary was `product:rf_power_semis`
  (Δ +0.090) — same as the gallium ban. This is the **country-origin
  fanout artifact again**: the walk from china fires equally over all
  outbound minerals, so gallium's downstream product tops the delta chart
  even though this event was about heavy REEs. The correct top-affected
  product for this event is `product:ndfeb_magnets`, but that only ranks
  8th at Δ +0.009 because dysprosium's outbound input_share into NdFeB
  is 0.20 (small mass fraction).
- **Ranking.** Rank 1 vs reality's rank 2. Roughly right by luck — the
  formula ranks it top because of the fanout, not because it correctly
  weighs the NdFeB chain.
- **Classification.** **FORMULA ARTIFACT (F-J-3, same as gallium)** —
  country-origin fanout. **DATA GAP (D-J-3)** — dysprosium's real
  irreplaceability in NdFeB isn't captured by the 0.20 input_share weight;
  the graph needs an "irreplaceability" or "criticality-of-share" concept
  for cases where a small mass fraction is a mission-critical additive.

## J-2025-10-nexperia

**Model:** 0 nodes reached; entity resolution matched only
`country_region:netherlands`, which produced no cascade because
`concentration_delta = 0.0`.
**Reality:** automotive-only impact; zero AI compute effect; ranking 7 of 7.

- **Reach.** Correct null result. The right answer for the right reason
  (out-of-domain event, no entity match, no cascade). But the pipeline
  produces no explicit "out-of-domain / no entity match" signal — it
  silently returns a 0/0 cascade indistinguishable from an authored
  zero-magnitude in-domain event.
- **Ranking.** Rank 7 vs reality's rank 7. Correct.
- **Classification.** **DATA GAP (D-J-4)** — no "unresolved event" state
  in the pipeline. Ingestion needs an explicit unmatched-entity result
  so out-of-domain news is visibly filtered out rather than silently
  swallowed.

---

## Findings table

| id | event | classification | one-line description |
|---|---|---|---|
| **F-J-1** | Taiwan quake | FORMULA ARTIFACT | Concentration axis reads a transient event as a structural share loss; no time-decay to attenuate. |
| **F-J-2** | Kachin KIA | FORMULA ARTIFACT | ⚠ Pass J.1 amendment: Kachin under-fires because Kachin's own **concentration** is low (≈ 0.15 implied by seed 0.030 ÷ magnitude 0.20 ÷ confidence 1.0), NOT because the unscored-origin seed under-weights in general. The seeding mechanism itself over-weights unscored origins — see [[F-J-4]]. The remaining defect for Kachin is that the downstream dampens further via dysprosium's low `input_share` (0.20) into NdFeB, so the paper's canonical "news says Kachin, impact is dysprosium" case survives with severity in the noise floor. |
| **F-J-3** | gallium ban, REE licence | FORMULA ARTIFACT | Country-origin fanout — a single-magnitude event at country_region walks over every outbound supply edge equally; ban-specificity ("this mineral, not that one") cannot be represented without per-edge event scoping. |
| **F-J-4** | any country-origin event | FORMULA ARTIFACT | **Pass J.1 §7.** Unscored origins systematically **out-seed** scored origins. The unscored seed is `concentration × magnitude × confidence`; the scored seed is `baseline_severity × magnitude × confidence`. Since `severity = concentration × (1 − substitutability) × lead_time_norm` and both remaining factors are ≤ 1, `severity ≤ concentration` always. Committed evidence from `docs/generated/replay/J-2024-12-china-gallium.md`: at identical magnitude, `country_region:china` (unscored) seeds **0.248** while `mineral:gallium` (scored, tier `high`, baseline 0.480) seeds **0.144** (`0.480 × 0.30 × 1.0`). ⚠ **Pass K §0.1 correction:** the earlier value 0.147 in this row was gallium's **hop-1 cascade contribution** from China (`0.248 × 0.6 × 0.99`, decay 0.6 × `input_share` 0.99) — hence gallium appearing at hop 1, not hop 0, in the artifact. The finding is unaffected and slightly wider: 0.144 < 0.248, so the unscored China origin out-seeds scored gallium by a wider margin than previously reported. A second-order corollary: the China→gallium walk (0.147) also outweighs gallium's own seed (0.144), which is why gallium never appears at hop 0 in the artifact — its seed is masked by the max-of-paths rule. Under live ingestion, country-origin events are the majority case, so this dominates in practice. Shares fix surface with [[F-J-3]] but is a separable defect (seed weight vs edge scoping). |
| **F-J-5** | Kachin KIA (metric-instability exemplar) | FORMULA ARTIFACT | **Pass J.1 §2.** The model's severity ordering of the event set depends on which observable is chosen as the ordering statistic. The two available observables — `max_delta` and `origin_scale` — disagree by ≥ 2 slots on kachin (`model_rank` 5, `rank_by_origin_scale` 3). Live ingestion cannot rank events without picking one; the picked metric materially changes which events lead. |
| **A-J-1** | ASML export licence | AXIS EXPRESSIVENESS | Demand-side restriction on a supplier has no axis. Even with an ASML→China edge, "restrict downstream customers by geography" would not map onto concentration / substitutability / lead_time. |
| **A-J-2** | HBM sellout | AXIS EXPRESSIVENESS | The pipeline reads only `concentration_delta`. Capacity-commitment events whose real signal sits in `lead_time_delta` and `substitutability_delta` are systematically under-weighted. ⚠ Pass J.1 restatement: the HBM inversion is **1 → 4 under `model_rank`** (primary metric) and **1 → 5 under `rank_by_origin_scale`** (alternate). The finding stands under either metric; the size is metric-dependent. See [[F-J-5]]. |
| **D-J-1** | ASML export licence | DATA GAP | No ASML→China edge (nor should there be for AI graph); recorded as a pre-registered gap because a demand-side-axis fix without this data would still produce nothing. |
| **D-J-2** | gallium ban | DATA GAP | Germanium is not modelled. Pre-registered in Phase A. If ingestion targets Dec 2024 material, needs a node. |
| **D-J-3** | REE licence | DATA GAP | Dysprosium's real irreplaceability in NdFeB is not captured by the mass-fraction `input_share` of 0.20. Needs a criticality-of-share concept for "small mass fraction, no substitute" cases. |
| **D-J-4** | Nexperia | DATA GAP | ⚠ Pass J.1 correction: probe `P-J-1` (nexperia copy with injected `concentration_delta = 0.20`, artifact `docs/generated/replay/probes/P-J-1.md`) reaches **0 nodes**. `country_region:netherlands` has `concentration = 0.0` and **no outbound material-flow edges** (only `located_in` inbound from ASML). The null in Pass J was **structural**, not a spurious partial match suppressed by the authored zero magnitude. ⚠ **Pass K §0.2 correction & re-scoping:** the earlier conclusion "out-of-domain events do not, on the current graph, produce a spurious cascade even at non-zero magnitude" was an `n = 1` generalisation from the most inert node in the graph and is withdrawn. What P-J-1 shows narrowly: out-of-domain events matching **only zero-concentration, zero-outbound-edge nodes** produce no cascade. Probe P-J-2 (see below) tests the live-ingestion-relevant case: an out-of-domain story that merely *mentions* China matches `country_region:china` (34-node reach) — see §Out-of-domain sensitivity probe P-J-2. |
| **H-J-1** | Taiwan quake (rank) | HONEST DISAGREEMENT | Rank 3 vs 5 is a two-slot inversion, but within the authoring-basis uncertainty. Not a defect requiring code work — logged as a data point for future recalibration once several similar physical-halt events are in the corpus. |

## Nexperia sensitivity probe — Pass J.1 §6

The probe `P-J-1` is a copy of `J-2025-10-nexperia` with `concentration_delta`
injected to 0.20 (all other fields byte-identical). It is quarantined in
`data/ai/replay/probes.json`, run via `python backend/scripts/replay_events.py
--probes`, and its artifact lives at `docs/generated/replay/probes/P-J-1.md`.
Probes never enter `summary.md`, `model_rank`, or `outcomes.json`.

Result: **nodes reached = 0**; max Δ = +0.000; top-5 affected = (none);
**none** of the six pre-registered nodes (`company:asml`, `company:tsmc`,
`company:samsung`, `company:intel`, `company:sk_hynix`, `company:micron`) is
touched.

Mechanism: `country_region:netherlands` is the only matched entity;
`_event_source_scale` for an unscored origin returns
`concentration × magnitude × confidence`; Netherlands has `concentration = 0.0`
(no material-flow outbound edges — only `located_in` inbound from ASML). Seed
is `0.0 × 0.20 × 0.7 = 0.0` so no walk occurs, and even if it did, there are
no `mines`/`refines`/`supplies`/`input_to`/`component_of` edges from
Netherlands to traverse.

Per the Pass J.1 §6 pre-registration, this is **branch (2): reach was zero
and the null was structural.** D-J-4's framing is weakened accordingly —
recorded inline in the findings table above.

## Out-of-domain sensitivity probe — Pass K §0.2 (P-J-2)

The Pass J.1 review noted that P-J-1's null was over-generalised to "all
out-of-domain events" from an `n = 1` test against the most inert node in
the graph. The live-ingestion risk is the opposite: an out-of-domain story
that mentions a **high-reach** country matches that country and fires a
34-node fanout.

Probe **P-J-2** — plausible non-AI China event (Chinese port congestion,
timestamp 2026-03-14), only matched entity `country_region:china`,
`concentration_delta = 0.20`, confidence 0.7. Same quarantine rules as
P-J-1 (`data/ai/replay/probes.json`; run via `--probes`; artifact
`docs/generated/replay/probes/P-J-2.md`). Run **before K-1 landed** so the
result is comparable to P-J-1's against the 67-node graph.

Result:

- **Nodes reached: 34** — matches the pre-registered "on the order of 34".
- Max Δ **+0.036** at **`product:rf_power_semis`** — matches the
  pre-registered "tops out on `product:rf_power_semis`".
- Top-5 affected: `product:rf_power_semis` +0.036, `mineral:gallium` +0.036,
  `mineral:neodymium` +0.033, `mineral:dysprosium` +0.021,
  `mineral:indium` +0.019 (all China outbound minerals — [[F-J-3]] fanout).
- AI-facing nodes touched (9): `company:broadcom` +0.0006, and
  `sk_hynix`/`micron`/`samsung`/`tsmc`/`amd`/`nvidia`/`hbm`/`cowos_packaging`
  each at |Δ| ≤ 0.0001 — small but non-zero.

**D-J-4 restored and re-scoped.** The exposure is not out-of-domain events
in general (as Pass J.1 wrongly generalised from P-J-1) and it is not
zero-concentration nodes (P-J-1's specific case). **The exposure is
out-of-domain events whose only match is a high-reach country node** —
the live-ingestion majority case per F-J-4. An unresolved-event /
low-specificity signal remains on the must-close gate list; the
justification is now this probe number, not the P-J-1 argument.

## Ingestion gate list

Findings that **must** close before live news ingestion can be built:

- **A-J-2 (HBM / multi-axis intake).** The pipeline must read at least
  `substitutability_delta` and `lead_time_delta` alongside
  `concentration_delta`, or ingestion will systematically miss the class
  of events that mattered most in 2024-25 AI supply. This is the largest
  observed rank inversion.
- **F-J-3 (country-origin fanout).** Without per-edge event scoping, any
  China-material event floods the entire China outbound edge set. Live
  news ingestion runs many China-source events; the pipeline needs a way
  to say "this event targets these edges" rather than "this event is at
  this origin".
- **F-J-4 (unscored origins out-seed scored).** Added Pass J.1 §7.
  Unscored origins (every `country_region`) seed the walk with
  `concentration × magnitude × confidence`, which mathematically
  dominates the `baseline_severity × magnitude × confidence` seed used
  for scored origins at the same concentration. Country-origin events
  are the majority case under live ingestion, so this bias runs
  everywhere. Shares fix surface with F-J-3 (both involve rethinking
  how country-origin events enter the walk) but is a separable defect
  — do not merge them into one finding. ⚠ **Pass K §0.1**: the
  supporting number in the findings-table row corrected from 0.147
  (hop-1 walk contribution) to **0.144** (gallium's actual seed,
  `0.480 × 0.30 × 1.0`).
- **D-J-4 (unresolved-event signal).** ⚠ Pass K §0.2: P-J-1 weakened
  the finding to "out-of-domain matches on zero-concentration,
  zero-outbound-edge nodes produce no cascade"; P-J-2 (China-mentioning
  out-of-domain event) **restores it at full strength and re-scopes**:
  an out-of-domain story that matches only a high-reach country
  produces the full country-origin fanout (P-J-2 reached 34 nodes,
  topped by `product:rf_power_semis`). Under live ingestion this is the
  majority-case exposure (per [[F-J-4]]). Kept on the must-close list;
  the justification is now the P-J-2 number, not the P-J-1 argument.

Findings that **can wait** until after first ingestion:

- **A-J-1 (demand-side axis).** Real for ASML-class events, but the AI
  graph has few pure demand-side supplier events; can be deferred until
  the corpus contains multiple examples.
- **F-J-1 (transient vs structural).** Real, but time-decay is its own
  design pass; the transient-event over-fire is bounded per-event.
- **F-J-2 (Kachin-style low-concentration origins).** ⚠ Pass J.1
  amendment: the diagnosis was originally "unscored-origin seed
  under-fires". Per F-J-4, unscored-origin seeding OVER-weights in
  general; Kachin under-fires specifically because Kachin's own
  concentration is low. Improves Kachin-style upstream events; not a
  blocker for the majority of events which have scored
  origins.
- **D-J-1, D-J-2 (data gaps).** Add nodes/edges/weights as the news
  corpus surfaces them; not preconditions.
- **~~D-J-3~~ — CLOSED in Pass K.1 §4.** ⚠ Pass K.1 closes D-J-3 as a
  **systemic finding**, not a third patch. The disease was `input_share`
  authored on cost / BOM / mass basis rather than dependency basis.
  Resolution: `config/scoring.yaml` now carries the §4.1 definition of
  `input_share` at the top of the file; `docs/generated/input_share_audit.md`
  is the pass-wide sweep. Prior instances (dysprosium→magnets 0.20→0.90,
  neodymium→magnets 0.60→1.00, ARM→NVIDIA via arm_core_ip 0.02→0.25)
  are re-authored; 29 additional cost/volume-basis edges are queued
  for future research rather than invented.
- **H-J-1.** Recalibrate once more physical-halt events are in the corpus.

---

## Pass K.1 corrections to the Pass K report (§6)

### K.1 §0.1 — China-reach re-pin (33 → 35) confirmed authorised

The Pass K report claimed the China-reach re-pin was approved mid-execution.
The claim is **confirmed**: Claude Code asked during Pass K execution and
Weston approved. The 35 pin in `backend/tests/test_narration.py` stands as
authorised; no ledger deviation is required.

The mechanism is independently verified: pre-existing `copper input_to
tsmc` at 0.08 combined with Pass K's new `tsmc supplies arm` at 0.99
(foundry_wafers for the AGI CPU) attaches `company:arm` and
`product:arm_core_ip` to China's transitive closure over material-flow
edges. This is real supply-chain reality — ARM's AGI CPU depends on TSMC,
which depends on Chinese copper.

Pass K.1 expects the reach pin to remain 35 through K.1. It did — no §4.4
audit re-authoring moved the numerator or denominator.

### K.1 §6.1 — pre-K tier baseline was wrong

The Pass K report §6 recorded the pre-K tier histogram as **13 moderate /
9 none**. Ground truth is **14 moderate / 8 none** — passes J and J.1
changed no scores. With 14/8, the pass reconciles at zero tier changes
across K without any distribution-shift explanation.

### K.1 §6.2 — the applied_materials "distribution shift" was fabricated

Pass K §6 attributed "+1 moderate" tier movement to an
`applied_materials` distribution shift. No such shift occurred; the
attribution was a fabricated explanation for a discrepancy that arose
from the mistyped baseline in §6.1. The row is retracted.

### K.1 §6.3 — the §1.5(3) Synopsys raw outbound = 1.164 claim was wrong

Pass K §3.5 row §1.5(3) gave Synopsys' raw outbound criticality as 1.164.
Committed post-K state was `outbound_criticality` normalized 0.017630 ×
`fixed_reference` 1.770976984672585 = **0.0312 raw** — off by ~37×. The
double-count analysis built on the 1.164 figure is unanchored and is
withdrawn. The double-count phenomenon is real (§1.5(3) still HIT after
K.1's re-authoring); the specific quantification does not stand.

### K.1 §6.4 — Pass K v2 §1.4 spec-author error logged

Pass K v2 §1.4 specified edge `type: input_to` for the EDA / CPU-core-IP /
interface-IP buckets. The engine's `compute_supplies_per_category`
inspects only `EdgeType.SUPPLIES`, so the buckets the spec introduced
were never engaged for their nodes. `company:tsmc → company:arm` and
`company:arm → product:arm_core_ip` were correctly typed `supplies` in
the same pass, which made the mistype internally inconsistent.

The defect is a **spec-author error**, distinct from Pass K's report
errors above and from the D-J-3 cost-basis authoring flaw. Logged
here because spec defects belong in the ledger alongside implementation
defects.

Resolved in Pass K.1 §3 by retyping all 34 design-IP edges to
`type: supplies`.

---

## D-J-4 reframe — growth mechanism, not hygiene

Deferred from prior session; recorded here so it survives into the next
handoff. The Pass K.1 P-J-2 probe demonstrated the live risk. D-J-4 is
not a signal-cleanup gate; it is a **corpus growth mechanism** that
turns unresolved / partial-match events into candidates for graph
expansion.

**Three flavours of unresolved entity, ranked by insidiousness:**

1. **Nothing matched.** Event names an entity the graph has no node for.
   Obvious null result; easy to audit. Low insidiousness.
2. **Wrong alias.** Event names a real modelled node under an alias
   the graph doesn't know. Still an obvious null but requires alias
   authoring to close.
3. **Partial match — the insidious case.** Event names entities where
   *some* match and the walk silently cascades on the ones that matched.
   The cascade LOOKS clean (no null result, no unresolved flag) but
   is quietly under-scoped. P-J-2 (Chinese port congestion matching
   only `country_region:china`, 34-node fanout, top rf_power_semis)
   is the canonical demonstration.

**Signal principle:** *recurrence, not first appearance*, is what
promotes an entity from candidate to real. A single event mentioning
"Kachin" is not enough to add `country_region:kachin` as a node; three
independent events over a window are. This prevents corpus noise from
inflating the graph.

**Rule: candidates are proposed and queued, never auto-created.** The
ingestion pass emits a per-event unresolved-entity list. A human
reviews on cadence, decides whether to close as: alias / new node /
noise / defer. Auto-creation would let a graph grow unaudited.

**Tag each future candidate:**

- **data-change (cheap):** just needs a node or alias added to
  `nodes.json`.
- **code-change (expensive):** requires schema / matcher / engine
  changes to accommodate.

Data-changes close inside the next ingestion pass; code-changes get
their own scoped pass with the four-phase blinding discipline (J.1 §10).

---

## Pass K.2 corrections to the Pass K.1 report (§6)

Pass K.2 is a diagnosis pass — no scoring or data changed. These are
ledger entries only.

### K.2 §6.1 — K.1 tier-change attribution corrected (MISS)

The K.1 report §12 decomposed 13 tier changes as **5 Phase B + 7 RESCALE-
crossing-boundary + 1 rf_power_semis**. Arithmetic refutes this: pre-K.1
was 14 moderate / 13 none; post-K.1 is 27 / 0; and 14 + 13 = 27. The
uniform mechanism was **the moderate boundary collapsing to 0.0** (§1),
which flipped every previously-`none` node to `moderate` regardless of
severity delta.

Confirmed at the node level:

- `company:vertiv` (severity 0.0642, Δ 0.0000) — none → moderate, but
  vertiv appears in NEITHER the 9 RESCALE nor the 7 STRUCTURAL rows of
  K.1's severity_diff. It changed tier with zero severity delta.
- `mineral:indium` (severity 0.0739, Δ 0.0000) — same pattern.

Both are 100% boundary-collapse tier changes. The Pass K.1 decomposition
into a Phase-B / RESCALE / rf_power_semis mix is a **fabricated causal
explanation for a discrepancy that arose from the mistyped mechanism.**

### K.2 §6.2 — K.1 expectation 6 regraded: PARTIAL HIT → MISS

K.1 §9 marked expectation 6 as PARTIAL HIT. The correct grade is MISS.
Expectation 6 said "tier changes are confined to design-IP nodes plus
whatever the §4.4 audit legitimately moves." 13 tier changes actually
occurred, of which only 4 (synopsys, cadence-adjacent, arm_core_ip, arm)
are design-IP; the other 9 are the boundary-collapse effect the pass
did not anticipate.

Under the honest reading, expectation 6 failed.

### K.2 §6.3 — recurrence pattern: unfounded causal decomposition

K.1 §7 explicitly retracted Pass K's fabricated `applied_materials`
distribution shift as an "unfounded causal explanation for a discrepancy
that arose from a mistyped baseline." K.1 §12 then produced its own
unfounded causal decomposition (§6.1 above) in the same report.

**Log as a repeat pattern, not a one-off.** Pattern: a discrepancy is
observed between an author's mental model and a committed number; the
author reconciles by inventing a per-node causal story that fits the
mental model; the mechanism is a bulk effect the author didn't consider.

Guardrail proposal (not implemented): a diff-cause claim in any report
must be traceable to a specific row in `severity_diff_*.md`'s cause
column. If a claim decomposes N tier changes, the decomposition must sum
to N and every subgroup must name its nodes.

### K.2 §6.4 — K.1 audit completeness: framed as complete, was ~54%

K.1 §5.4's audit found 259 edges, of which **119 (~46%)** classified as
`unclassified` — basis unrecoverable from committed source_notes. The
audit was framed in the K.1 report as complete ("the point of this
pass"). Under the honest reading, the audit is **~54% complete**; the
remaining 46% is basis-unknown.

Queuing 29 rather than inventing them was correct (§4.4 rule).
Framing the audit as complete was not.

Not a defect to fix; a framing correction. Future audit passes should
say "N edges classified, M unclassified, X queued" up front rather than
leading with the queued count.

### K.2 §6.5 — K.1 expectation 8 evidence mismatch

K.1 §8 pre-registration 8 asked: *"Restoring `fixed_reference` to
1.6711394969476698 returns prior-pass severities to their pre-K values
within floating-point tolerance for every node whose structure did not
change."*

**Floating-point tolerance** = ~1e-9 to 1e-12.

**Evidence given** = the RESCALE classifier's 5% relative tolerance
tagging (K.1 §6.3). 5% ≠ floating-point.

The specified comparison was not run. The RESCALE classifier tags a
delta as rescale-consistent when the observed movement matches the
expected `(ratio − 1) × severity_before` within 5% relative — that
answers "was the movement approximately the size a scale change would
produce" (a different, looser test).

The spec's original expectation cannot be tested strictly today because
Phase B re-authoring moves severities as well as Phase C's rescale, so
"structure unchanged" cannot be isolated on the current diff.
Recommendation for future rescale-only passes: exclude nodes whose
structure changed (edge list changed) and check remaining nodes at
floating-point tolerance.

### K.2 §6.6 — reviewer error on record

During the K.2 review process I initially stated that the derivation had
failed to declare the unresolved band. **That was wrong.** The
derivation declares the band correctly in `threshold_analysis.md` (§3.1).
The actual defect is that the declaration never reaches the config
(§3.1's confirmed finding).

Reviewer errors belong in the ledger alongside implementer and
spec-author errors.

### K.2 §6.7 — K.1 §5.2 Cadence pre-K.1 input_share reconciled

K.1 §5.2 gives Cadence's pre-K.1 `input_share` as **0.012** in the
`eda_tools` bucket table. A review record cited **0.01**. Resolved
against committed state at commit `fc7ee3e` (`git show
fc7ee3e:data/ai/edges.json`):

- `cadence → nvidia` `eda_tools` → **0.012** ✓ (K.1 report correct)
- `cadence → nvidia` `interface_ip` → **0.010** ✓

Both numbers exist; they name different buckets. The review record was
citing the interface_ip value in the eda_tools context. Reconciled: K.1
report was right, review-record note was misindexed.

### K.2 §6.8 — cosmetic K.1 report items (not-blocking)

Recorded so a future report does not repeat:

- K.1 §12 named the diff test `test_severity_diff_matches_committed_file`
  while §3 placed the change in `test_generated_artifacts.py`. Both are
  correct: the test lives in that file. Consistent naming across sections
  is a hygiene item.
- K.1 §4.2 labels a result "§3.3 pre-registration HIT" when it is
  expectation 2 (about stage-level min_suppliers). Cross-reference typo.
- K.1 §5.4 header wrote "SHA-25" once where SHA-256 was meant.

### K.2.1 §6 ledger additions

Appended by the completion pass K.2.1 (commit will follow this write).

#### K.2.1 §6.1 — K.2 §2 under-delivery

K.2 Diagnosis B was reported all-HIT on the §7 scorecard, but §2.2 asked
for three computations (full per-node summation table + graph-wide HHI
inversion count + per-edge queued-29 collision classification) and K.2
delivered only counts of buckets above 1.0. Scorecard item 6 verified a
narrow claim — "at least one bucket over 1.0" — while the broader §2.2
requirement was unmet.

This surfaces a scorecard-design lesson broader than this one instance:
**a pre-registration item can pass while the section it belongs to is
incomplete.** Future pass scorecards should include a "delivered in
full" check alongside per-claim verification, or pre-registration items
should be authored at the granularity of the requested output rather
than at the granularity of a single verifiable claim within it.

K.2.1 completes the missing computations in `docs/generated/hhi_blast_radius.md`.
Full graph exhibits 38 HHI inversions (K.2 worked 1); all 29 queued edges
classified individually (3 collides / 10 safe / 16 undeterminable).

#### K.2.1 §6.2 — third instance of asserted-precision-without-derivation

K.2 §6.1 retracted Pass K's fabricated `applied_materials` distribution
shift; K.2 §6.3 flagged the recurrence in K.1's fabricated tier-change
decomposition; **K.2 itself introduced a third instance** — the D3 cost
figures "triples if deferred past robotics; six-fold after aerospace" —
with no committed derivation.

The K.2 numbers are withdrawn in `docs/generated/k2_decisions.md` D3
(K.2.1 §5 correction). Direction reaffirmed qualitatively; multipliers
removed.

Pattern is now three-for-three across the K sequence. Guardrail:
**quantitative claims in a pass report must trace to a committed
artifact or explicit calculation shown in the report itself.** Where the
right answer is qualitative, say so; the corrective is honest imprecision,
not fabricated precision. Recorded across three instances; further recurrences
should trigger a spec change on report requirements rather than another
per-instance retraction.

#### K.2.1 §6.3 — chokepoint test status corollary

K.2 §4 established that "5 of 7 chokepoints not in critical" dates to
Pass C, not K.1. The reassuring corollary K.2 did not record:

Under the current test (`test_paper_chokepoint_severity_above_median`)
— severity strictly greater than the median scored severity —
**5 of 7 paper chokepoints PASS.** The 2 that fail (`product:hbm` and
`product:rf_power_semis`) are **exactly** the 2 pinned xfails, with
byte-identical SHA-256 reasons.

There are no unpinned model failures on the chokepoint list. The
regression K.2 §4 walked is real; the model's failure on it is fully
enumerated in the xfail registry. Nothing silently non-critical.

**Additional forward-looking finding from K.2.1 §4.3:** both currently-
pinned xfails would XPASS under D4 + D4a (noisy-OR aggregator + `min_suppliers=1`).
When the fix pass lands D4, retire the SHA-256-pinned reasons rather
than deleting them silently — the xfails' resolution is the D4 acceptance
criterion.

#### K.2.1 §6.4 — reviewer correction: K.2 §4 premise was wrong

The K.2 spec §4 opened with "5 of seven remain critical. Establish
**when** this diverged — was it Pass K.1's boundary movement, or did it
drift earlier and go unremarked?" The framing carried a hint of "recent
and unexplained regression."

K.2 §4's git-log walk **corrected the reviewer's premise**: the divergence
dates to Pass C's F1/F2 changes and was a recorded, deliberate reframe
(F2: replace "lands in critical" with "severity > median" as the actual
test). Not silent breakage; a documented decision the project has
consciously carried.

Reviewer errors belong on the ledger alongside implementer errors and
spec-author errors. Recorded.

#### K.2.2 §6 ledger additions

Appended by the diagnosis-only pass K.2.2.

**§6.1 — K.2.1 expectation 2 regraded HIT → MISS.** K.2.1 reported
"HIT DRAMATICALLY" on the claim that 38 buckets were inversion-
susceptible. The underlying test was circular: raising the smallest
share of any n≥2 unequal bucket to match the largest always drops
normalize=true HHI, because normalized HHI is minimized at equal
shares by construction. K.2.1's number "38" restated "38 currently
unequal buckets," not an inversion property. Regraded MISS. The NdFeB
inversion remains real, demonstrated, and — until K.2.2 §2 — was
unquantified in scope.

Under honest §4.1 dependency authoring (K.2.2 §2), the
inversion-EXPECTED count is **3**, not 38:
`product:ndfeb_magnets` (already realised K.1), `company:vertiv`
input_to, and `company:{openai, xai}` gpu_accelerators. Two orders of
magnitude below the K.2.1 figure. D4 urgency is real but narrower
than K.2.1 framed.

**§6.2 — New failure pattern logged: measurements entailed by
construction.** Distinct from the precision-without-derivation pattern
(K.2.1 §6.2 recorded 3-for-3 across the K sequence). Both produce
confident numbers that do not bear weight, by different routes:

- **Precision-without-derivation** — an unsupported figure asserted
  with more sig-figs than the source provides. Fixable by demanding
  a derivation.
- **Circular measurement** — a test whose result is entailed by its
  construction. Fixable by rewriting the test so it can return no,
  before running it. K.2.1 §2.2's inversion test is the reference
  case.

Both patterns share the same failure surface: a report reader takes
the number as evidence, and it doesn't survive scrutiny.

Proposed guardrail: **any pass-report claim that a metric "shows" a
phenomenon must state the metric's null hypothesis** — what result
would refute the claim. If the metric cannot return the refuting
value, the claim is circular and the metric is not evidence.

**§6.3 — Sequencing fact K.2.1 established but did not state.** The
10 "safe" queued edges in K.2.1 §2.3 are safe because they are
sole-supplier buckets. Sole-supplier buckets are exactly the buckets
currently zeroed by `min_suppliers_for_concentration: 2` (K.2 §2.4).
**Re-authoring them changes NOTHING for scoring until D4a lands.**

The queued-29 audit's collision analysis treated all 29 edges as
authoring candidates independent of D4a. That is not what the graph
does: 10 of them are inert-until-D4a-decides. Their position in the
queue depends on a decision K.2.1 did not tie to their status.

Recorded so the fix-pass ordering (see D4a §5 recommendation)
prioritises D4/D4a before re-authoring queued edges whose signal
depends on D4a's outcome.

**§6.4 — K.2.1 reporting defect (second occurrence).** K.2.1's
deliverables block listed the 4 changed files under a heading that
said **"Unchanged."** Same error appeared in K.2's deliverables block.
Two consecutive reports made the same cosmetic error in the same
field.

Fix: K.2.2 report §Deliverables uses **"Changed"** as the heading.
Also add a lint rule for future reports: if a file appears in
`git diff --name-only <prev>..HEAD`, it MUST NOT appear under any
"Unchanged" heading in the pass report.

**§6.5 — Reviewer position on record.** The K.2.2 reviewer
recommended against deciding D4 on K.2.1's evidence alone and called
for this pass. K.2.2 §2 confirmed the reviewer's circularity
objection was correct: the actual inversion-expected count is 3, not
38. The reviewer's urgency framing ("D4 gates every future dep-basis
authoring; cannot be decided on evidence that assumes its own answer")
survives.

K.2.1's arithmetic errors surfaced by K.2.2 §4 (K.2.1 used lt_norm =
lt/10; engine uses log10_1p) further support the reviewer's call —
K.2.1's specific severity figures were wrong even where its
qualitative conclusion was right. The pattern strengthens the
"scrutinise K.2.1 hard" call.

**§6.6 — K.2.1 arithmetic errors: lt_norm.** K.2.1 §4.3 gave xfail
severity figures under D4+D4a using `lt_norm = lt / 10`. The engine
uses `log10(lt+1)/log10(26)`. Corrected in
`xfail_resolution_audit.md` §4.1:

- `product:rf_power_semis` under D4+D4a: **0.2872** (K.2.1 said 0.2025).
- `product:hbm` under D4 or D4+D4a: **0.3008** (K.2.1 said 0.2121).
- Median direction: K.2.1 said 0.1949 → 0.1884 (falls). Under
  consistent log10_1p the median RISES ~0.10 (approximation: 0.1655
  → 0.2672). The "median falling while nodes rise" paradox K.2.2 §4(3)
  asked to reconcile is an artefact of K.2.1 mixing correct-baseline
  (from committed severities) against wrong-approximation.

Qualitative K.2.1 conclusion (both xfails XPASS under D4+D4a) intact,
by wider margins. Specific K.2.1 numbers are wrong.

**§6.7 — K.2.1 separability claim reframed.** K.2.1 §4.4 stated D4
and D4a are "NOT separable." K.2.2 §5 shows the two changes are
technically separable — no shared code path — and each independently
resolves ONE xfail (D4→HBM, D4a→rf_power). K.2.1's "not separable"
was outcome-completeness ("neither alone resolves both") dressed as
technical coupling.

Reframed with recommendation: ship D4 and D4a in **separate commits**,
in that order. Each xfail's resolution then has a single-change
provenance in the git history; intermediate state is legible; the
bundled-blast-radius alternative is available if Weston prefers it,
recorded as a deliberate choice rather than inherited from K.2.1's
misframing.

#### K.2.1 §6.5 — Cadence discrepancy resolved against the reviewer

K.2 §6.7 resolved the K.1 §5.2 Cadence value dispute (0.012 vs 0.01):
**both correct, different buckets** (eda_tools = 0.012, interface_ip =
0.01). K.1's report was right; the review-record note was misindexed
across two categories.

Confirming here in the K.2.1 ledger for completeness — no action needed;
recorded so the resolution is discoverable in one place.

### K.2 §6.9 — paper-chokepoint validity claim reframed (regression record)

The original validation claim was "every chokepoint the paper names
independently lands in `critical`." Current committed
`threshold_analysis.md`:

- 2 of 7 in `critical`: dysprosium, ASML
- 2 of 7 in `high`: gallium, TSMC
- 3 of 7 in `moderate`: CoWoS, HBM, RF & Power Semis

**The claim is currently false and has been since Pass C.** The Pass C F2
reframe explicitly replaced the tier-landing check with a
severity-above-median check (`test_paper_chokepoints.py` docstring:
"reframed in Pass C (F2)") because tier landings are distribution-anchored
and can move with the graph.

The severity-above-median claim currently holds for 5 of 7 (HBM and RF &
Power are pinned xfails with byte-identical reasons; K.1 §5 verified
those reasons unchanged).

Recorded plainly so the paper-vs-model gap is legible in the ledger.
This is a Pass C decision the project has consciously carried; nothing in
Pass K.1 or K.2 introduced it.

---

## Pass L ledger additions

Pass L is the first code-changing pass since K.1. Scope was three
narrow items diagnosed across K.2 and K.2.2. All commits atomic per
§5 sequencing.

### L.6.1 — Boundary collapse CLOSED

`moderate: 0.0` and the resulting collapse of 27 of 31 scored nodes
into a single `moderate` tier is resolved. Retry loop replaces F1.b's
veto: on median-guard failure, iterate unused separating gaps by
descending midpoint and take the first with midpoint ≤ median.
Purely structural per spec §1.2.

Committed evidence: `docs/generated/severity_diff_pass_l.md` reports
0 severity deltas and 11 tier changes on the current distribution.
New boundaries: critical 0.5096065543117585, high 0.4118946228794891,
moderate **0.13666630472569183** (was 0.0). K.2 §1 diagnosis was the
evidence path.

### L.6.2 — `unresolved_bands` serialization gap CLOSED

Both silent-drop paths K.2 §3.1.1 identified are fixed:

- `_write_boundaries_to_config` (`backend/scripts/generate_inventory.py`)
  now writes `unresolved_bands` from the derivation. `_serialize_unresolved_bands`
  helper renders empty as inline `[]` and non-empty as a YAML block
  matching the engine's read schema.
- `build_inventory` (`backend/app/reporting/inventory.py`) now emits
  `tier_ambiguous` and `tier_ambiguous_with` as columns on the
  scored-nodes table.

Zero visible effect on the current committed distribution — Phase A's
retry produces no band — so the fix is verified by
`backend/tests/test_unresolved_bands_roundtrip.py` against a synthetic
distribution that forces one.

### L.6.3 — D2 DECIDED: guard replaced with retry, not deleted

K.2 §D2 asked whether the median guard survives. Pass L §1 chose
**REPLACE, not DELETE.** The guard stays as a residual degeneracy
check for distributions where the retry exhausts every candidate. K.2
§5 recommended this; the K.2.2 review reaffirmed. Recorded here as
closed.

### L.6.4 — D1 DEFERRED with reasoning

K.2 §D1 asked whether unresolvable boundaries should yield a withheld
tier or continue to fall back to 0.0. **Deferred.** Once the retry
loop landed (Phase A), the 0.0 path stops firing on the current
distribution — the residual case is a distribution that exhausts
every separating gap without finding one below median, which does not
exist on the AI graph today.

D1 therefore becomes a robustness question for future graph shapes
rather than a live defect, and it costs 8 downstream surfaces to
answer (K.2 §1.3 enumeration). Revisit when a graph actually exhausts
its candidates; not before.

### L.6.5 — Tier signal was degenerate from K.1 through K.2.2

**Every tier reading committed in the K.1 → K.2.2 window is
unreliable.** From Pass K.1 to Pass L Phase A, the moderate boundary
was 0.0 and 27 of 31 scored nodes carried the same tier label.

Anything a report inferred from tier membership during Pass K.1, K.2,
K.2.1, or K.2.2 must be re-checked against the Pass L snapshot before
being cited. Specific implicated claims:

- K.1 §6 tier histogram "2 critical / 2 high / 27 moderate / 0 none
  / 41 unscored" — was a rendering of the collapsed state; NOT a
  distributional finding.
- K.2 §4 chokepoint landing table (specifically CoWoS / HBM /
  RF & Power in `moderate`) — HBM and RF & Power in `moderate`
  reflected the collapse. Under Pass L: HBM stays `moderate` at
  0.1779; RF & Power moves to `none` at 0.0261.
- K.2.1 §6.9 paper-chokepoint validity claim — the tier-landing
  numbers should be re-quoted against the Pass L snapshot when
  next cited.
- K.2.2 §4 median-reconciliation (K.2.1 said 0.1949 → 0.1884) —
  correct in identifying that K.2.1 mixed lt/10 against log10_1p,
  but the specific reference values need re-checking against the
  post-Pass-L median.

### L.6.6 — Reporting-defect recurrence (third occurrence)

K.2 report listed changed files under an "Unchanged" heading.
K.2.1 report repeated the error. K.2.2 added a correct "Changed"
heading — and then repeated the "Unchanged" error below it in the
same report.

This is a **cosmetic reporting recurrence**: three consecutive reports
made the same error at the same field. The K.2.2 §6.4 proposed
guardrail (lint rule: if a file appears in `git diff --name-only
<prev>..HEAD`, it MUST NOT appear under any "Unchanged" heading in
the pass report) has not been implemented. Pass L would be the fourth
consecutive occurrence if the fix isn't applied.

**Pass L report explicitly separates Changed from Unchanged and does
not repeat the error.** Proposed guardrail remains open — a shell
script or CI check should enforce it before the next report defect
occurs.

---

## Pass M ledger entry

Pass M ran the six D4 candidate aggregators × two min_suppliers values
through the REAL engine via a config-selectable seam defaulting to the
current HHI path. Every committed artifact regenerated byte-identically
under the default. Measurement-only; no decision on D4.

### M.6.1 K.2.2 approximation graded

Bimodal divergence from engine-measured values:

- **Per-bucket concentrations (NdFeB, xfail severities): 0% divergence.**
  K.2.2's arithmetic on isolated buckets was right; approximation
  caveat was over-weighted on these claims.
- **Distribution-wide claims: 50–75% divergence.** K.2.2 §3.2.3
  "15–20 nodes saturate under projected" measured as 6. K.2.2 §3.2.1
  "6 separating gaps under noisy-OR" measured as 3.

Both distribution-wide errors overstated saturation concern. Post-M:
ε=0.01 clears saturation cleanly; the top-of-distribution collapse
K.2.2 worried about does not materialise.

### M.6.2 Aggregator seam added to engine

`backend/app/scoring/engine.py::compute_concentration_aggregate` is
the new dispatcher. `refresh_all_derived` accepts optional
`aggregator_method`, `aggregator_eps`, `min_suppliers_override`,
`stage_min_suppliers_override` keyword-only parameters. All defaults
route to committed HHI behaviour byte-identically.

The seam exists so future validation passes never need to reimplement
the per-stage / per-category logic — the exact critique that motivated
this pass. If it stops being used it can be removed; leaving it in
place adds ~120 lines and zero committed-artifact drift.

### M.6.3 Reviewer position on approximation

The K.2.2 reviewer called for engine validation before D4 could be
decided. Pass M confirms the reviewer's methodological concern was
warranted (distribution-wide K.2.2 numbers were significantly wrong)
and simultaneously confirms K.2.2's per-bucket arithmetic (NdFeB,
xfail severities) was exact. Both findings on the record.

### M.6.4 D4 recommendation now measured

k2_decisions.md D4 updated with Pass M-measured numbers replacing
K.2.2's approximations (approximated figures struck rather than
deleted so the correction is legible). New D4 recommendation:
noisy-OR + ε (plateau [0.001, 0.100]) + min_supp=1 for both-xfails
resolution; count-aware deferrable per §5 test.

**Pass M does not decide D4.** The evidence is now in a shape the
decision can rest on.

---

## Pass N ledger — the fix

Pass N is the fix pass. D4 shipped as plain noisy-OR (no ε); D4a
shipped as `min_suppliers=1`; both xfails retired. Six commits in
three phases.

### N.6.1 D4 decided and shipped: noisy-OR, ε rejected on implementation review

Both K.2.2 and Pass M recommended pairing noisy-OR with an internal
ε=0.01. **Rejected on implementation review**, on two grounds:

1. `compute_noisy_or_eps` caps each *input* at `1 − eps` before
   combining. It prevents the single-input-at-1.0 case only. A bucket
   of many mid-range inputs still combines toward 0.999; ε does
   nothing there. It is not a saturation guard; it is a 1.0 guard.
2. As a 1.0 guard it is a milder form of the B1 author-cap K.2.2
   itself rejected as tuning-toward-target. Better located (inside
   the engine, one place, authored value stays honest) but the same
   kind of adjustment.

Pass M measured the problem as small: 1 node at exactly 1.0 under
D4 + min_supp=2, 2 nodes at 1.0 under D4 + D4a, zero severity-level
ties across the 31-node scored set. Saturation exists and is not
producing observable downstream effect.

Ship plain noisy-OR. Pre-registered expected saturation. If a future
distribution produces real ordering breaks at the severity level, add
ε then, with evidence. Do not build the machinery ahead of the need.

A recommendation overturned by reading the code it proposed. Recorded
so a future author can see the reasoning.

### N.6.2 D4a decided and shipped: min_suppliers 2 → 1 (safe only under noisy-OR)

Stage-level and per-category values both lowered. Comment blocks
rewritten with dependency-semantics reasoning and an explicit ⚠
safety note: **`min_suppliers=1` is safe ONLY under noisy-OR**. If
a future config switches `method` back to `hhi`, the value must
revert to 2 — Pass M measured `hhi_min1` producing 19 nodes at
concentration 1.0 and retry-exhaust boundary collapse. The two
config keys must stay in lockstep.

Accepted cost: thin-graph nodes named in the scoring.yaml TODO
(`quanta_services`, `xai`, `openai`) now read as more concentrated
under min_suppliers=1. Part of the concentration is modelling
incompleteness rather than real risk. The completeness backlog
tracks these explicitly; the artefact stays visible.

Pre-existing `all_stages_single_supplier` fallback branch is now
unreachable under min_supp=1. **Retained, not deleted** — reachable
under any future config raising the threshold.

### N.6.3 Both xfails retired

`product:hbm` and `product:rf_power_semis` — the model's only two
disagreements with the paper. Both resolved when D4+D4a shipped:

- **HBM**: memory-bucket concentration jumped HHI 0.4402 → noisy-OR
  0.7440 (D4 by construction). Severity 0.1779 → 0.3008, crosses
  post-D4 median 0.2015 → XPASS. Reason string explicitly named
  "inbound_hhi 0.44 cap" — the aggregator change ends that mechanism
  directly.
- **RF & Power**: sole-source gallium input_to bucket unzeroed (D4a).
  Severity 0.0261 → 0.2872, crosses post-D4+D4a median 0.2404 →
  XPASS. Reason string explicitly named "min_suppliers=2 rule zeroes
  single-source stage buckets" — the rule change ends that mechanism
  directly.

Neither resolves via unrelated side effect crossing a threshold. Both
mechanisms are named in their own reason strings. Aggregator was
chosen on grounds independent of the xfails (HHI is mathematically
wrong for shares that don't sum to 1 regardless of any xfail movement).

Registry now empty. Pinning machinery (Pass J.1 §3) retained;
`test_xfail_registry_is_pinned` asserts the empty-shape invariant.

### N.6.4 HHI/dependency incompatibility CLOSED

Opened K.1 §4.3 (NdFeB inversion: raising Nd 0.60→1.00 and Dy
0.20→0.90 LOWERED the computed HHI). Diagnosed across K.2 / K.2.1
/ K.2.2. Measured in Pass M. **Fixed in Pass N by shipping noisy-OR**,
which is bounded [0,1], monotonic, and requires no summation
constraint — the properties dependency-basis shares actually need.

### N.6.5 The 29 queued re-authors are UNBLOCKED

They were paused pending D4. With D4 shipped they are free to
proceed. Each still needs the research K.1 §4.4 identified per edge;
the unblocking is on the aggregator dependency, not on the research
itself. Ordering per K.2.2 §6.3: the 10 "safe" queued edges are all
sole-supplier buckets; under Pass N D4a they now contribute to
concentration (they didn't before), so their honest re-author matters.

### N.6.6 Two-level `min_suppliers` fallback asymmetry logged

Pre-existing open item surfaced by Pass N Phase B. When ALL stages on
a node are single-supplier, the stage-level rule sets `inbound = 0.0`;
when all supplies-categories on a node are single-supplier, the
per-category rule falls back to the aggregate reading. **Two opposite
responses to the same condition one level apart.** Not introduced by
Pass N; logged, not fixed. See config/scoring.yaml comment on the
category-level `min_suppliers_for_concentration` block for the note.

### N.6.7 Paper is no longer an independent check on the model

After this pass the model agrees with the paper everywhere (7 of 7
chokepoints pass severity > median). The paper is a hypothesis
document, not ground truth — agreement with it is not validation.
Having evaluated six aggregator candidates in Pass M and shipped the
one whose recommendation was independent of the xfail outcomes, the
resolution is accepted as genuine (§N.6.3 named-mechanism check). But
the paper no longer provides an independent check on the model
going forward.

**Real validation still waits on live ingestion and the two-lane
prediction log** — recorded per Pass N §1.3.

---

## Pass N.1 ledger — reconciliation of the Pass N report

Diagnosis-only reconciliation of two node-level contradictions in the
Pass N report. No fix, no data or config change, no snapshot movement.
See `docs/generated/pass_n_reconciliation.md` and
`inbound_movement_sweep.md` for the full artefacts.

### N.1.6.1 `product:arm_core_ip` numbers reconciled

Pass N reported for the same node:
- Phase A bullet: `+0.1788 (moderate → none)`, prose "actually moved DOWN"
- Phase B bullet: `+0.1755 (none → moderate, 0.1512 → 0.3267)`

Both wrong. Committed diff artifacts settle it:

- **Phase A delta 0.0000.** Severity did not move at all. Tier dropped
  moderate → none only because the moderate BOUNDARY moved from
  0.1367 to 0.1771 and severity 0.1512 fell below the new cut. **The
  node did not move; the boundary passed it.**
- **Phase B delta +0.1788.** Sole-source cpu_core_ip bucket unzeroed
  by min_supp=1; inbound_hhi jumped 0.0 → 1.0; severity 0.1512 →
  0.3300 (not the 0.3267 the report quoted — 0.3267 was Pass M's
  ε=0.01 value; Pass N shipped plain noisy-OR).

**Defect origin: Pass N report prose, not the diff generator.** Diff
artifacts are internally consistent.

### N.1.6.2 Downward concentration movement mechanism: implicit incompleteness dampening

Pass N attributed ge_vernova's fall to "noisy-OR reads its inbound
differently" — a restatement, not a mechanism.

Full sweep (`inbound_movement_sweep.md` §2.3): 2 of 31 scored nodes'
inbound fell — **ge_vernova and siemens_energy, both power-layer**.
15 rose; 14 unchanged (stage-zeroed on both sides).

Mechanism confirmed on both: their input_to buckets sum to 0.45 / 0.50
(incomplete — missing steel, magnets, composites, etc). HHI with
`normalize=true` renormalizes to pretend the bucket sums to 1.0,
inflating the reading; noisy-OR reads raw magnitudes without
renormalization.

**Noisy-OR does what `normalize: false` was designed to do — dampen
incomplete buckets in proportion to shortfall — as a side effect of
the aggregator switch.** This is a second semantic change that
shipped inside D4 unremarked in Pass N's ledger. Not a defect (the
incompleteness handling is a strict improvement over HHI's
discarding of it) but a future auditor could mistake it for an
intended aggregator effect. Logged here so it is not.

Power-layer finding: the falls are systematic. Power-equipment BOM
has many uncommonly-modelled inputs (steel, control electronics,
cooling); the power layer's input_to buckets are structurally thin,
which HHI hid and noisy-OR surfaces. Not per-node curiosity.

### N.1.6.3 Phase B histogram independently reconciled

Phase A ended at 11m/15n; Phase B moved three nodes up (arm,
arm_core_ip, rf_power_semis) and none down → 14m/12n. Reconciles
exactly. **Phase B's miss is fully explained by the Phase A baseline
being wrong**, not by anything intrinsic to Phase B. Pass N graded
both misses as a single Pass M artefact by assertion; Pass N.1
provides the independent check.

### N.1.6.4 Pass M defect still open

`docs/generated/aggregator_validation_data.json` was generated by
`aggregator_validation.py` which tiered noisy-OR severities against
whatever committed HHI boundaries were in config at Pass M time. Every
`tier_hist` value in that file is contaminated by the same half-update
that Pass N.1 §1 and the Pass N histogram misses trace to — not only
the two cells Pass N quoted.

**The file was not regenerated in Pass N, and Pass N.1 does not
regenerate it either** (per §0 constraint). A wrong number sitting in
a committed artifact is how the defect recurs — the Pass N spec
quoted those exact numbers verbatim without asking how they were
derived. If a future pass wants Pass M's tier_hist values, it must
regenerate them against the CURRENT config or annotate the file with
the half-update caveat. Recorded as open.

### N.1.6.5 Reviewer error on record

The Pass N spec pre-registered tier histograms taken from Pass M's
data.json verbatim. Both were wrong for the reason §N.1.6.4 names.
The reviewer did not ask how the numbers were computed. Logged
alongside the implementer defect (§N.1.6.4) — the two together
produced Pass N's two histogram misses.

### N.1.6.6 Pass N report file-count mismatch

Pass N report header says "**12 files across 6 commits**" and then
lists 17 file paths. Cosmetic reporting defect. Actual scope was 17
files across 6 commits; the "12" was arithmetic sloppiness in the
prose. Recorded so the discipline of matching prose counts to enumerated
lists carries into future reports.

## Pass O — diff attribution, snapshot provenance, modeling caveats

Fix pass. Tooling and data only; scoring untouched. Every severity and
tier is byte-identical to Pass N end state (72 nodes × 5 fields per
node, all identical against a pre-Pass-O snapshot copy). Suite
94 → **99 pass** (+5 from the new BOUNDARY-cause / arm_core_ip replay
tests); 0 xfail.

### O.6.1 Diff attribution: BOUNDARY cause added to per-row classifier

Pass N Phase A shipped a zero-delta tier change on `product:arm_core_ip`
that the diff generator called `STRUCTURAL` because it had no
snapshot boundaries to compare against. Same class of defect —
attributing a boundary movement to node movement — is now
structurally impossible.

Two changes in `backend/app/reporting/inventory.py`:

- `snapshot_severity` captures `boundaries` (from
  `config.chokepoint_thresholds`) alongside the existing
  `fixed_reference`. Same conditional-capture pattern as K.1.
- `build_severity_diff` per-row classifier gained a fourth branch:
  zero severity delta + tier changed + snapshot has boundaries that
  differ → `BOUNDARY`. If the snapshot has no boundaries (pre-Pass-O
  shape) → `BOUNDARY (unverified)`. If boundaries are equal on both
  sides → `UNEXPLAINED` (the row must not silently be absorbed into
  any BOUNDARY bucket — a zero-delta tier change with unchanged
  boundaries is an invariant violation and the classifier records
  ignorance rather than manufacture a cause). Summary block gained a
  sub-count `BOUNDARY (zero severity delta, tier moved because
  boundary moved): N` under tier changes.

Header block renamed from "Scale-constant status" to "Snapshot vs
current — constants and knobs" so the section title matches its
expanded scope (fixed_reference + boundaries + aggregator method).

Synthetic acceptance test —
`backend/tests/test_diff_attribution.py::test_arm_core_ip_replay_pass_l_to_phase_a_classifies_BOUNDARY` —
replays the Pass N Phase A transition against the post-O classifier
using pass_l-shape snapshot (moderate boundary 0.1367) vs post-Phase-A
config (moderate boundary 0.1771). Classification: **BOUNDARY**, not
STRUCTURAL. Recorded as the acceptance test per spec §5(5); run as a
fixture rather than against committed artifacts.

### O.6.2 Snapshot provenance: capture anything that can silently change meaning

Principle recorded so future scoring-adjacent knob changes don't
recur the arm_core_ip class of defect. **Anything that can silently
change the meaning of a severity number gets captured in the
snapshot that severity is compared against.** Pass K.1 §5.4 applied
this to `fixed_reference`; Pass O extends to tier boundaries
(§O.6.1) and the aggregator method + ε.

`snapshot_severity` now also captures `aggregator_method` (from
`config.inbound_per_stage_method`) and `aggregator_eps` (from
`config.inbound_per_stage_eps`). The diff header states whether the
method changed and — if it did — notes that every non-zero delta
below is potentially method-attributable, because a method switch
changes every node's inbound in principle. Row-level classification
of method-caused deltas is **not** attempted: it is not computable
from the snapshot alone (would need the previous method to re-score
against). Header-level flag only, per spec §2.

Snapshot re-captured under the existing `pass_n_d4a` label rather
than rolled forward to a new pass name (spec §7 note), so the
historic `severity_diff_pass_n_d4a.md` roll-forward artifact is not
overwritten.

### O.6.3 Modeling caveats populated on ge_vernova and siemens_energy; key convention introduced

Two `power/grid_equipment` nodes now carry the caveat that Pass N.1
§2.5 named:

> Inbound concentration is dampened here because the modelled input
> bucket is incomplete — steel, control electronics, cooling systems
> and structural composites are not yet in the graph, so the
> aggregator reads the partial bucket at its raw magnitude rather
> than assuming completeness.

Shape decision: `static.modeling_caveat` now accepts EITHER literal
prose (the historic shape — 4 existing nodes carry literal text) OR
a key reference `caveat:<name>` that resolves via
`config/narration.yaml modeling_caveats.<name>`. The two power-layer
nodes both reference `caveat:power_thin_input_bucket` — one authored
sentence, two data rows. A key that resolves to `None` is a config
error (raises `ValueError`) rather than a silent skip; the panel
must not lose a caveat it was authored to carry.

Only two nodes are populated in this pass. Other thin-graph nodes
that carry similar coverage caveats today (`company:quanta_services`,
`company:xai`, `company:openai`) already have literal text on record
and are not touched; a future pass may migrate them to shared keys if
their wording converges. Data change scope: two node rows in
`data/ai/nodes.json`. Fixture synced
(`backend/tests/fixtures/ai/nodes.json`, `backend/tests/fixtures/narration.yaml`).

### O.6.4 RESCALE_REL_TOL justification is unsound — logged, not fixed

`backend/app/reporting/inventory.py::build_severity_diff` carries
`RESCALE_REL_TOL = 0.05`. The pre-Pass-O comment justified it as
"absorbs boundary-shift-induced tier rebucketing that correlates but
isn't strictly proportional." That justification is unsound: tier
rebucketing does not affect severity, and the classifier operates
on severity deltas only. Boundary-shift attribution is now a
first-class cause (§O.6.1) — it has nothing to do with the rescale
tolerance.

Value NOT changed in this pass. Changing 0.05 to a different value
would re-classify a subset of historic rows as RESCALE vs STRUCTURAL,
which is a separate decision with its own diff scope. Comment
updated in place to record the unsound-justification finding and
point out that whatever tolerance the classifier should carry, it is
independent of boundary movement. Open item.

### O.6.5 `single_supplier_stages` / `operates` comment audit — no change needed

Verified two comment-authorship claims that Pass N updated:

- `backend/app/scoring/engine.py:717–724` — comment on the stage-level
  `min_suppliers` gate. Still accurate post-D4a: gating produces
  `single_supplier_stages` for reporting; the aggregator reads only
  the gated set. `min_suppliers=1` unzeroed some stages (per Pass N
  Phase B) but the comment doesn't overspecify what the gate zeros
  out; no drift.
- `backend/app/schema/enums.py:50–63` — `SUPPLY_EDGE_TYPES` comment
  states that `operates` participates in cascade propagation but is
  NOT in `SHARE_INTO_TARGET`, so it does not double-count for inbound
  HHI. Verified: the share-derivation set the scoring engine reads
  (in `graph.py`) still excludes `operates`. Comment and behaviour
  match.

No code change. Recorded so the audit is on file if a future pass
adds `operates` handling to inbound or removes it from cascade.

## Pass P — D3 decided: tier boundaries frozen as absolute constants

Fix pass. Config mechanism + a diagnostic. No scoring change; every
severity and every tier is byte-identical to Pass O end state. Suite
99 → **110 pass** (+4 boundary-guard, +7 drift-diagnostic); 0 xfail.
Graph shape: 72 nodes / 259 edges / 31 scored. China material-flow
reach: 35. `fixed_reference`: 1.6711394969476698 (unchanged).

### P.5.1 D3 decided — boundaries frozen

Tier boundaries stopped being live-derived on every generator run.
`thresholds.mode: frozen` in `config/scoring.yaml` is now the default;
`_write_boundaries_to_config` is a no-op under frozen; the natural-
breaks derivation is retained as a diagnostic and feeds the drift
section in `docs/generated/threshold_analysis.md`.

Three reasons on the record (spec §0):
1. **Precedent.** `fixed_reference` was frozen for the same class of
   silent-drift defect (Pass K.1 §2, §5.4); Pass P applies the same
   pattern to the same problem.
2. **The scale is already AI-anchored.** `fixed_reference` is ASML's
   raw outbound from THIS graph; every future domain divides by it.
   Concentration was already absolute; relative tiers sat inconsistently
   on top of a half-absolute foundation.
3. **Boundaries were unstable from internal change alone.** Pass N's
   aggregator switch alone moved critical 0.5096→0.5178, high
   0.4119→0.4137, moderate 0.1367→0.1771 — no new domain, no new
   nodes. Adding robotics or aerospace would have moved them far more.

Decision was taken at 72 nodes rather than deferred until after the
29 queued re-authors, because D3 is time-sensitive before robotics
onboarding and the value of freezing now exceeds the value of a
one-time cleaner baseline. See P.5.2 for the pre-approved re-baseline.

### P.5.2 Re-baseline expected after the 29 re-authors — pre-approved in principle

The 29 queued re-authors will move severities on HBM, CoWoS, copper,
and RF Power — real movement in the middle of the distribution.
Freezing at today's values means baselining on numbers already known
to be wrong. This is accepted; the re-baseline pass is **pre-approved
in principle** but still requires its own spec + diff scope + a
snapshot re-capture (the movement from today's frozen boundaries to
whatever the re-baseline chooses must be diffable, so the diff
generator can attribute it to `mode: derived` + the 29 re-authors,
not to node movement).

Recorded so the next author does not treat the re-baseline as
unauthorized boundary drift. The mechanism (`mode: derived`) is
retained specifically for this pass; committed output under
`mode: derived` outside the re-baseline flow is a defect and the
guard test in `test_thresholds_frozen.py` catches it.

### P.5.3 K.2 §3.3 closed — generated boundary values can no longer commit without a human decision point

Pass K.2 §3.3 logged that `moderate: 0.0` reached committed config
via `generate_inventory.py` without any human decision point — a
side-effect write path from a documentation-generation script.
Under `mode: frozen`, that path no longer exists for boundaries:
the writer is inert, and any change to a boundary literal must be
edited by hand under an authorizing spec, with the guard test
updated in the same commit. Closed.

`unresolved_bands` gets the same treatment: under frozen the
derivation may still SIGNAL a band via the drift section, but
`_write_boundaries_to_config` does not touch the config's
`unresolved_bands` list. A live band under frozen boundaries is a
drift signal, not a config truth.

### P.5.4 Snapshot provenance principle extended — capture + freeze

Pass O established that anything which can silently change the
meaning of a severity number gets captured in the snapshot
(`fixed_reference`, `boundaries`, aggregator method + ε). Pass P
extends the treatment for boundaries specifically: **captured in
the snapshot AND frozen in config AND guarded by a test**, the
same treatment `fixed_reference` receives. The drift diagnostic
becomes the third leg: capture makes past state legible, freezing
makes current state stable, drift reporting makes the divergence
visible so the next re-baseline is a decision instead of an
accident.

### P.5.5 Frozen-with-drift-reporting is now a pattern (n=2)

`fixed_reference` (Pass K.1) and now tier boundaries (Pass P) have
both moved from live-derived to frozen-with-drift-reporting. The
pattern:
- committed literal + inline comment naming what changes require
- guard test that fails on drift
- diagnostic that keeps running so drift is measurable, not silent
- write path is inert under frozen; a `derived` mode exists for the
  pre-approved re-baseline

If a third value ever fits the same shape (a scoring input that
depends on distribution shape and where silent drift changes the
meaning of every downstream number), it is worth naming the pattern
and factoring the shared machinery. At n=2 the code duplication is
tolerable; at n=3 it is a refactor worth doing.

## Pass Q — dependency re-author, power/electrical cluster (13 of 29)

Data pass. Edge weights only. 3 of 13 power-cluster edges re-authored
on the K.1 §4.1 dependency basis; 10 left as reviewed-and-undeterminable
with specific reasons. No scoring code change, no config change, no
formula or aggregator change. Every severity byte-identical to Pass P
end state. 110 pass, 0 xfail.

### Q.0 Provenance

At pass open:

```
$ git log --oneline -5
40e2afa Pass P: D3 decided — tier boundaries frozen as absolute constants
f0dd482 Pass O: diff attribution, snapshot provenance, modeling caveats
63f08f2 Pass N.1 (diagnosis only): reconcile arm_core_ip + downward-movement mechanism
f3f8e4d Pass N ledger + k2_decisions D4/D4a marked DECIDED
694e382 Pass N Phase C: retire both xfails

$ git status --short
(empty)

$ git rev-parse HEAD
40e2afa330cfebf5aacd32deb885088f650edb82

$ git diff --name-only HEAD
(empty)
```

**Commit shape finding: two commits.** Pass O (`f0dd482`) and Pass P
(`40e2afa`) each have a recoverable diff in history. Per-pass file
attribution is retrievable from `git show <sha>` for either commit.
Working tree at open is empty; HEAD is as expected.

**HEAD at close:** the SHA of the commit carrying this Pass Q section is retrievable via `git log --oneline -1 --grep "Pass Q"`. Not baked in as a literal here because doing so would require an `--amend` cycle to make the literal match the commit it names (chicken-and-egg with the commit hash). Open SHA + `git log` on the branch is the authoritative record.

### Q.4.baseline — verified state at open

Cross-checked against §2 of the spec via inline scoring probe; every
row matched byte-for-byte:

| item | verified value |
|---|---|
| nodes / edges / scored | 72 / 259 / 31 |
| tier histogram | 2 critical / 3 high / 14 moderate / 12 none / 41 unscored |
| boundaries (frozen) | 0.5178454839188712 / 0.41368488092014066 / 0.17711108045794494 |
| `thresholds.mode` | `frozen` |
| `fixed_reference` | 1.6711394969476698 |
| aggregator method / eps | `noisy_or` / 0.01 config-carried, not applied under `noisy_or` |
| `min_suppliers_for_concentration` (stage + category) | 1 |
| snapshot label | `pass_n_d4a` (unchanged; Pass Q did not roll forward) |
| suite | 110 pass, 0 xfail |

### Q.8 pre-registration scorecard

| # | expectation | HIT / MISS | evidence |
|---|---|---|---|
| 1 | `inbound_hhi` on `ge_vernova` and `siemens_energy` byte-identical | **HIT** | `pass_q_facts.json` caveat_check: ge_vernova 0.4149999999999999 → 0.4149999999999999; siemens_energy 0.45999999999999996 → 0.45999999999999996. Full float equality. |
| 2 | Both power caveats resolve to branch A | **HIT** | ge_vernova branch=A, siemens_energy branch=A, quanta_services branch=A. All: "inbound_hhi unchanged AND inbound still the dominant axis." |
| 3 | `outbound_criticality` rises on at least one of ge_vernova / siemens_energy / quanta_services / vertiv | **HIT** | ge_vernova outbound 0.1819268342116367 → 0.19473684861108456 (+0.0128). Siemens/quanta/vertiv outbound unchanged (no edges of those three re-authored on value). |
| 4 | At least one consumer bucket sum crosses 1.0 after re-authoring, and no value was reduced to prevent it | **MISS (outcome), author discipline maintained** | No bucket crossed 1.0 — the highest post-Q bucket sum among the 4 affected consumers is NextEra `power_equipment` at 0.80 (0.75 → 0.80). This is because 10 of 13 edges were left undeterminable; the K.2.1 §2.3 collision case (siemens → nextera authored high) did not fire because that edge was undeterminable, not because a value was reduced to prevent it. Author discipline was maintained: `bucket_sum_before` = `bucket_sum_after` for every consumer bucket except NextEra's; NextEra's rose 0.75 → 0.80 (from the honest §4-basis re-author of GE Vernova's wind exposure, not from reduction anywhere). If a subsequent pass authors any of the remaining undeterminable edges honestly high, the K.2.1 collision may fire then — recorded so the next author does not treat it as unexpected. |
| 5 | Zero severity movement on constellation_energy, duke_energy, nextera_energy | **HIT** | All three unscored (severity None) both before and after. Their concentrations may have moved (nextera inbound_hhi 0.58 → 0.608) but severity remains `null` and tier remains `unscored` — no severity movement is possible on an unscored node. |
| 6 | Every frozen constant unchanged | **HIT** | `fixed_reference` 1.6711394969476698 unchanged; boundaries {0.5178454839188712, 0.41368488092014066, 0.17711108045794494} unchanged; guard test `test_thresholds_boundaries_are_frozen` still green. |
| 7 | Suite ≥ 110 pass, 0 xfail | **HIT** | 110 pass, 0 xfail. Two transient failures during Q were expected and closed inside the pass: `test_node_inventory_matches_committed_file` (regenerated `node_inventory.md`) and `test_no_stage_bucket_sums_below_0_80` (removed `nextera_energy/supplies` from the pinned shortfall list, which it exited by moving to 0.80). |
| 8 | At least one edge is marked undeterminable rather than all 13 re-authored | **HIT** | 10 of 13 marked undeterminable in `pass_q_facts.json`. The 3 re-authored are named with specific public-knowledge sources (GE Vernova's US onshore wind #1 position; Quanta's public 10-K NextEra concentration; paper §4B naming Vertiv as data-centre cooling leader). |

**7 HIT, 1 MISS (outcome, not discipline).**

### Per-edge table (13 of 13)

Every value, status, and confidence quoted from `docs/generated/pass_q_facts.json` (spec §6 mechanical artifact).

| # | edge | before | after | status | confidence | basis (see full source_note in edges.json for the 3 reauthored; see below for the 10 undeterminable) |
|---|---|---:|---:|---|---|---|
| 1 | `ge_vernova → constellation_energy` | 0.15 | 0.15 | undeterminable | estimate | Constellation's fleet is nuclear-heavy (12 reactors); non-nuclear side (gas peakers, transformers) uses GE and Siemens equipment. Cannot decompose Constellation's function attributable specifically to GE Vernova without published fleet composition + reactor-vs-peaker function share. Left at pre-Q 0.15. |
| 2 | `ge_vernova → duke_energy` | 0.20 | 0.20 | undeterminable | estimate | Duke's grid-equipment dependency spans transformers, generators, switchgear across fossil + nuclear + renewables. Substitutable among GE / Siemens Energy / Hitachi Energy but published Duke-specific mix not accessible. Left at pre-Q 0.20. |
| 3 | `ge_vernova → nextera_energy` | 0.25 | **0.30** | **reauthored_value** | estimate | GE Vernova is #1 US onshore wind turbine OEM (public knowledge). NextEra Energy Resources is largest US wind operator (~30 GW installed). NextEra's wind fleet composition carries material GE exposure over-indexing the generic three-way grid-equipment split. §4.1: withdrawal impairs fleet growth + service + parts over 3-5y horizon (platform lock-in). |
| 4 | `ge_vernova → facility:the_citadel` | 0.15 | 0.15 | undeterminable | estimate | Facility-specific on-site power equipment mix (backup gensets, UPS, transformer sizing) not accessible. Left at pre-Q 0.15. |
| 5 | `nextera_energy → facility:the_citadel` | 0.10 | 0.10 | undeterminable | estimate | Whether the Citadel is Texas-served (ERCOT) or elsewhere, and NextEra's share of its grid supply, not published. **Sole-supplier bucket** (`power_generation`, 1 modelled member) — under `min_suppliers=1` (Pass N D4a) this now contributes; noted for the record. Left at pre-Q 0.10. |
| 6 | `quanta_services → duke_energy` | 0.20 | 0.20 | undeterminable | estimate | Duke's construction-services dependency on Quanta specifically (vs MYR, Primoris, in-house) not published. Left at pre-Q 0.20. |
| 7 | `quanta_services → nextera_energy` | 0.30 | 0.30 | **reauthored_note_only** | estimate | NextEra publicly identified as Quanta's largest customer (Quanta 10-K customer-concentration disclosures over multiple years). Value 0.30 retained as consistent with named-largest-customer + leading utility construction contractor position. See NOTE in source_note about `supply_category` semantic approximation (Quanta is construction contractor, currently labelled `power_equipment`). |
| 8 | `siemens_energy → constellation_energy` | 0.15 | 0.15 | undeterminable | estimate | Same reasoning as edge 1: Constellation nuclear-heavy, Siemens exposure on non-nuclear side not decomposable from public disclosures. Left at pre-Q 0.15. |
| 9 | `siemens_energy → duke_energy` | 0.20 | 0.20 | undeterminable | estimate | Same reasoning as edge 2. Left at pre-Q 0.20. |
| 10 | `siemens_energy → nextera_energy` | 0.20 | 0.20 | undeterminable | estimate | K.2.1 §2.3 collision candidate — a §4-basis high author here (~0.30-0.35) would cross the 1.0 bucket sum. Left undeterminable rather than authored to relieve or provoke the collision; noise-OR permits the collision but the value should come from evidence, not from testing the aggregator. Left at pre-Q 0.20. |
| 11 | `siemens_energy → facility:the_citadel` | 0.15 | 0.15 | undeterminable | estimate | Same reasoning as edge 4. Left at pre-Q 0.15. |
| 12 | `vertiv → facility:the_citadel` | 0.35 | 0.35 | **reauthored_note_only** | estimate | Paper §4B explicitly names "Vertiv (leader)" in data-centre cooling. Hyperscale AI training facilities are cooling-critical (thermal shutdown in hours without adequate cooling). Withdrawal causes partial function loss over ~months substitution window (Schneider, Johnson Controls, Trane, STULZ as alternatives). Value 0.35 retained as consistent with paper-named class leader with active competitors. **Sole-supplier bucket** (`cooling`, 1 modelled member) — under `min_suppliers=1` contributes; noted. |
| 13 | `vertiv → facility:vantage_frontier` | 0.20 | 0.20 | undeterminable | estimate | Pre-existing source_note "Same rationale." refers to Vertiv's other facility edges. Facility-specific Vertiv share at Vantage Frontier not decomposable without published cooling BOM. **Sole-supplier bucket** (`cooling`, 1 modelled member) under `min_suppliers=1`. Left at pre-Q 0.20. |

**Data changes:** 1 value change (edge 3), 2 source-note additions (edges 7, 12), 10 edges untouched. Fixture `backend/tests/fixtures/ai/edges.json` synced.

**`supply_category` observation.** Actual categories from `data/ai/edges.json`: 11 edges `power_equipment`, 1 `power_generation` (edge 5), 2 `cooling` (edges 12–13). The spec §3 table's descriptive labels ("grid/generation equipment", "site power", "grid construction/services", "site power/cooling") do not appear as `supply_category` values in the data; the spec was descriptive per its own §3 note. Reported as required.

### Q.5 caveat branch verdicts

Quoted from `pass_q_facts.json`:

- `company:ge_vernova` → **branch A**. inbound_hhi 0.4149999999999999 → 0.4149999999999999 (byte-identical). Post-Q outbound_criticality 0.19473684861108456 < inbound_hhi 0.4149999999999999. Inbound still the dominant axis. Caveat stands, unchanged.
- `company:siemens_energy` → **branch A**. inbound_hhi 0.45999999999999996 → 0.45999999999999996 (byte-identical). Post-Q outbound_criticality 0.1707325122849878 (unchanged) < inbound_hhi 0.45999999999999996. Inbound still dominant. Caveat stands, unchanged.
- `company:quanta_services` → **branch A**. inbound_hhi 0.30000000000000004 → 0.30000000000000004 (byte-identical). Post-Q outbound_criticality 0.15236677911939359 (unchanged) < inbound_hhi 0.30000000000000004. Inbound still dominant. Caveat stands, unchanged. (Quanta's literal caveat is on the record from a prior pass — "Inbound HHI reads 1.0 because copper is the only modelled input. Real inputs include steel, transformers, labour and permits — Quanta is not single-sourced to the degree the number suggests." — its literal text does not resolve through the narration key convention but the branch check applies identically.)

### Threshold drift section — quoted verbatim

Copy of `## Drift diagnostic — frozen vs derived (Pass P §3)` from `docs/generated/threshold_analysis.md`:

**1. Per-boundary drift** — all three deltas `+0.0000000000`. Frozen and derived agree.

**2. Would-change-tier under derived boundaries** — **0 nodes would change tier.** Frozen boundaries and the current derivation agree on every scored node's tier.

**3. Cluster-cut check** — all three boundaries clear of clusters: critical Δ nearest 0.0210962753 ≥ median gap 0.0133607067; high Δ 0.0555971060; moderate Δ 0.0244370443. No YES flags.

**4. Unresolved bands** — _None declared._

**Verdict** — **Frozen set still fits the distribution.** No node would change tier under the derived boundaries, no frozen boundary sits inside a tight cluster, and no unresolved band is declared. A re-baseline would produce identical tiers today.

**Stop condition 7 clear.** No would-change-tier movement on any node this pass did not touch — because no node's severity moved at all this pass.

### Changed

`git diff --name-only HEAD` — 7 modified files:

```
backend/tests/_out/share_backlog.txt
backend/tests/fixtures/ai/edges.json
backend/tests/pinned/known_bucket_shortfalls.txt
data/ai/edges.json
docs/generated/input_share_audit.md
docs/generated/node_inventory.md
docs/generated/threshold_analysis.md
```

`git ls-files -o --exclude-standard` — 2 untracked files:

```
backend/scripts/pass_facts.py
docs/generated/pass_q_facts.json
```

`docs/generated/replay/grading.md` will be modified by this Pass Q section — count 8 modified + 2 untracked = **10 files** in the Pass Q commit.

**Not changed** — files genuinely absent from the diff:

- `config/scoring.yaml` and `backend/tests/fixtures/scoring.yaml` — verified untouched via `git diff --name-only HEAD config/scoring.yaml` (empty output). The Pass P `mode: frozen` short-circuit in `_write_boundaries_to_config` held; the generator did not touch the config.
- `docs/generated/severity_snapshot.json` — no roll-forward invoked; still labelled `pass_n_d4a` post-Q.
- `docs/generated/severity_diff.md` — regenerated in-place by the generator run but byte-identical to its pre-Q state (Non-zero severity deltas: **0**; Tier changes: **0**; BOUNDARY: **0**). Not in `git diff --name-only`.
- Every scoring code file (`backend/app/scoring/*.py`), every narration file, every schema file, every test file.
- `data/ai/nodes.json` — no node touched.

Cross-check: every file listed above under "Not changed" is genuinely absent from the `git diff --name-only HEAD` output shown. The failure mode this section exists to catch (changed files leaking under an Unchanged heading) has occurred in prior reports; verified against the diff before submission this time.

### Q.6 mechanical artifact — `docs/generated/pass_q_facts.json`

Written by `backend/scripts/pass_facts.py`. Contains, at full float precision: HEAD SHA, commit shape (two — Pass O and Pass P separately committed), graph shape, boundaries, threshold_mode, fixed_reference, aggregator, per-edge before/after with status/confidence/bucket-sums/sole-supplier flag, per-node before/after with dominant-axis, caveat check with branch verdicts, and suite counts. The report above **quotes** this artifact rather than re-computing values from memory.

Current suite field in the artifact: `{"passed": 110, "failed": 0, "xfail": 0, "tail": "110 passed in 0.66s"}`. Known fragility for future passes: the `passed`/`failed` scraper uses `^(\d+)\s+passed` and only fires when the pytest tail begins with the passed count. If a future run has failing tests the pytest tail begins with the failure count instead (`"N failed, M passed in ..."`) and the numeric fields would silently misreport. Recorded as an open item — the `tail` field is authoritative regardless; the scalar fields are convenience.
