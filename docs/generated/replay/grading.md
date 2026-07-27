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
- **D-J-1, D-J-2, D-J-3 (data gaps).** Add nodes/edges/weights as the
  news corpus surfaces them; not preconditions.
- **H-J-1.** Recalibrate once more physical-halt events are in the corpus.
