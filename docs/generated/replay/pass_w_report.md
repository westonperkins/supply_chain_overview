# Pass W — Multi-axis event intake, Phase A: measurement only

**Type:** Measurement pass. No committed scoring change, no config-key change, no edge or node value authored. Every committed severity, tier, and constant byte-identical at close. Candidates driven in-process through the real engine.

**Addresses:** A-J-2 — HBM ranked 4 of 7 by the model against 1 of 7 observed, the largest inversion in the replay set.

Numbers are read from `docs/generated/pass_w_facts.json` and `docs/generated/multi_axis_candidates.md`, both written by `backend/scripts/pass_w_measure.py`.

---

## W1 — Provenance

- **HEAD at open:** the Pass V commit `b40f2a2`. Working tree clean.
- **HEAD at close:** the Pass W commit.
- **`git status --short` at open:** clean.
- **`git diff --name-only b40f2a2..HEAD`:**
  ```
  backend/app/schema/event.py          (docstring only — §0.3)
  backend/scripts/pass_w_measure.py    (new; in-process harness)
  docs/generated/multi_axis_candidates.md   (new; generated)
  docs/generated/pass_w_facts.json          (new; generated)
  docs/generated/replay/pass_w_report.pdf   (new)
  docs/generated/replay/grading.md          (Pass W section)
  ```
- **No scoring code, config value, or authored axis moved.** `config/scoring.yaml`, `config/ingestion.yaml`, `data/`, and `backend/app/scoring/` are untouched. The only `backend/app/` change is the §0.3 docstring in `event.py`. Committed severities/tiers are byte-identical to the snapshot (verified).

---

## W2 — The four §0 findings, confirmed or refuted

**§0.1 — The multi-axis machinery exists and nothing calls it. CONFIRMED.** `engine.axes_for_severity(sub_delta=0.0, lt_delta=0.0)` applies `sub_base + sub_delta` and `lt_base_years + lt_delta`. A repo-wide search for its call sites finds exactly three, all with no deltas: `engine.compute_baseline_severity` (line 422, `axes_for_severity(node, config)`) and two tests (`test_scoring_correctness.py:54,72`). `cascade.py` **imports** the helper (line 31) but never calls it — it routes through `_event_magnitude` (a scalar) instead. `aggregator_validation.py` imports but never calls it. **No caller anywhere passes a non-zero `sub_delta` or `lt_delta`.** The perturbation path was half-built and orphaned by Pass D's scalar-magnitude cascade. (Expectation #2: HIT.)

**§0.2 — The substitutability sign convention is inverted in the code. CONFIRMED.** The `AxesImpact` docstring and all seven authored events are risk-positive (positive delta = substitution harder = more risk; HBM's `0.15` note: "sold-out capacity removes the ability to substitute"). But `axes_for_severity` computes `sub_base + sub_delta`, and severity is `concentration × (1 − substitutability) × lead_time`, so a positive delta *raises* substitutability and *lowers* severity — opposite to the authored intent. Concretely for HBM (sub 0.05, δ 0.15): the current code gives `sub_used = 0.20`, `(1 − 0.20) = 0.80` against baseline `(1 − 0.05) = 0.95` — severity would **fall ~16%** on an event whose entire significance is that substitution got harder. Latent because no caller passes a non-zero delta. Resolved for this pass by measuring all candidates under **risk-positive** signs (apply as `sub − delta`), and declared in the schema docstring (§0.3 / W3).

**§0.3 — `lead_time_delta` unit is years, and the code's reading is consistent with the corpus. CONFIRMED.** `axes_for_severity` does `lt_base_years + lt_delta`. Checked against all seven events: taiwan `0.02`≈7d ("a small number of days"), kachin `0.10`≈5wk, HBM `0.25`≈3mo ("multi-quarter"), gallium `0.15`≈8wk, china-rees `0.20`≈10wk ("multi-month"); asml and nexperia are `0.0`. All coherent as years. Declared in the schema docstring this pass (docstring only).

**§0.4 — Additive concentration perturbation saturates on exactly the nodes events target. CONFIRMED.** Gallium's concentration is `0.985224`; a `concentration_delta` of `0.30` gives `1.285`, clamped to `1.0` — an **effective move of `0.014776`** from a 30-point authored delta (Expectation #5: HIT, `< 0.02`). Dysprosium (`0.990199`, δ `0.35`) moves `0.009801`. The events that matter most target the most concentrated nodes, which is exactly where additive perturbation has no headroom. Measured per event in W7.

---

## W3 — Conventions resolved

- **Substitutability sign: RISK-POSITIVE** (chosen). Positive `substitutability_delta` = substitution harder = more risk, matching the schema docstring and all seven authored events. Applied by passing `−substitutability_delta` to `axes_for_severity` so the used substitutability falls and `(1 − sub)` rises. The alternative (axis-signed: positive = more substitutable) would require re-authoring the sign on every event that carries a non-zero delta — HBM, gallium, china-rees — and contradicts the corpus. Recorded, not assumed.
- **`lead_time_delta` unit: YEARS** (declared). Added to the `AxesImpact` docstring; no behaviour change.
- **`test_cascade_and_engine_use_identical_axis_handling` status.** The test **exists and passes non-vacuously**, but it does **not** assert what the engine docstring claims. It asserts `cascade.axes_for_severity is engine.axes_for_severity` — i.e. import identity (that cascade didn't fork a copy of the helper). It does **not** reference `_event_severity_at_source` and does **not** test that two callers handle deltas identically. The stale reference is in the **engine docstring** (`engine.py:476` names `cascade._event_severity_at_source`, which does not exist), not in the test. So the reviewer's exp 3 is half right: the function is absent (HIT), but "the test naming it is dead or vacuous" is wrong — no test names it, and the test the docstring points to is alive and asserts a real (if weaker) invariant. See scorecard exp 3.

---

## W4 — Candidate matrix

All seven events, per candidate. `origin Δ` = max origin contribution among matched entities; `max Δ` = largest node severity move (the ranking key); full precision in `pass_w_facts.json`. **MA-0 was validated node-for-node against the real `propagate_event` (0 mismatches on all 7 events)** before any candidate was trusted.

**MA-0 (status quo) — ρ = +0.7143**

| rank | event | origin Δ | reached | max Δ | max Δ node | tier chg | observed | disp |
|---:|---|---:|---:|---:|---|---:|---:|---:|
| 1 | china-rees | 0.219994 | 36 | 0.086160 | mineral:dysprosium | 0 | 2 | −1 |
| 2 | gallium | 0.188565 | 36 | 0.074954 | product:rf_power_semis | 0 | 3 | −1 |
| 3 | taiwan | 0.023233 | 15 | 0.012437 | company:tsmc | 0 | 5 | −2 |
| 4 | **HBM** | 0.015038 | 13 | 0.010515 | product:hbm | 0 | **1** | **+3** |
| 5 | kachin | 0.023350 | 8 | 0.002151 | mineral:dysprosium | 0 | 4 | +1 |
| 6 | asml | 0.000000 | 0 | 0.000000 | — | 0 | 6 | 0 |
| 7 | nexperia | 0.000000 | 0 | 0.000000 | — | 0 | 7 | 0 |

**MA-1 (axis perturbation at origin, scalar propagation) — ρ = +0.8929**

| rank | event | origin Δ | reached | max Δ | max Δ node | observed | disp |
|---:|---|---:|---:|---:|---|---:|---:|
| 1 | china-rees | 0.350000 | 36 | 0.105983 | mineral:gallium | 2 | −1 |
| 2 | gallium | 0.300000 | 36 | 0.090843 | mineral:gallium | 3 | −1 |
| 3 | **HBM** | 0.092538 | 13 | 0.068225 | company:sk_hynix | **1** | **+2** |
| 4 | kachin | 0.200000 | 8 | 0.018400 | mineral:dysprosium | 4 | 0 |
| 5 | taiwan | 0.050000 | 15 | 0.003110 | company:tsmc | 5 | 0 |
| 6 | asml | 0.000000 | 0 | 0.000000 | — | 6 | 0 |
| 7 | nexperia | 0.000000 | 0 | 0.000000 | — | 7 | 0 |

**MA-1b (headroom-relative concentration) — ρ = +1.0000**

| rank | event | origin Δ | reached | max Δ | max Δ node | observed | disp |
|---:|---|---:|---:|---:|---|---:|---:|
| 1 | HBM | 0.075662 | 13 | 0.055783 | company:sk_hynix | 1 | 0 |
| 2 | china-rees | 0.130008 | 36 | 0.039368 | mineral:gallium | 2 | 0 |
| 3 | gallium | 0.190326 | 36 | 0.033744 | mineral:gallium | 3 | 0 |
| 4 | kachin | 0.176650 | 8 | 0.016247 | mineral:dysprosium | 4 | 0 |
| 5 | taiwan | 0.050000 | 15 | 0.000740 | company:tsmc | 5 | 0 |
| 6 | asml | 0.000000 | 0 | 0.000000 | — | 6 | 0 |
| 7 | nexperia | 0.000000 | 0 | 0.000000 | — | 7 | 0 |

**MA-2 (perturbed axes propagate downstream) — ρ = +0.9286**

| rank | event | origin Δ | reached | max Δ | max Δ node | observed | disp |
|---:|---|---:|---:|---:|---|---:|---:|
| 1 | HBM | 0.092538 | 13 | 0.068225 | company:sk_hynix | 1 | 0 |
| 2 | gallium | 0.300000 | 36 | 0.023950 | product:rf_power_semis | 3 | −1 |
| 3 | china-rees | 0.350000 | 36 | 0.021915 | mineral:gallium | 2 | +1 |
| 4 | taiwan | 0.050000 | 15 | 0.007125 | company:broadcom | 5 | −1 |
| 5 | kachin | 0.200000 | 8 | 0.001267 | mineral:neodymium | 4 | +1 |
| 6 | asml | 0.000000 | 0 | 0.000000 | — | 6 | 0 |
| 7 | nexperia | 0.000000 | 0 | 0.000000 | — | 7 | 0 |

**MA-3 (combined scalar magnitude) — ρ = +0.8571.** Normalization rule: `magnitude = noisy_or(clamp(concentration_delta), clamp(|substitutability_delta|), normalize_lead_time(lead_time_delta))`, where `normalize_lead_time` is the config's `log10_1p` transform — the same transform that maps years→[0,1] for the formula. **This is the candidate's declared weakness:** a lead-time delta in years and a concentration delta on [0,1] are not the same quantity, and blending them through one `noisy_or` asserts they are.

| rank | event | origin Δ | reached | max Δ | max Δ node | observed | disp |
|---:|---|---:|---:|---:|---|---:|---:|
| 1 | china-rees | 0.281424 | 36 | 0.110222 | mineral:dysprosium | 2 | −1 |
| 2 | gallium | 0.228490 | 36 | 0.090830 | product:rf_power_semis | 3 | −1 |
| 3 | HBM | 0.074528 | 13 | 0.052114 | product:hbm | 1 | +2 |
| 4 | taiwan | 0.025910 | 15 | 0.013870 | company:tsmc | 5 | −1 |
| 5 | kachin | 0.026080 | 8 | 0.002400 | mineral:dysprosium | 4 | +1 |
| 6 | asml | 0.000000 | 0 | 0.000000 | — | 6 | 0 |
| 7 | nexperia | 0.000000 | 0 | 0.000000 | — | 7 | 0 |

---

## W5 — The HBM case, traced end to end

HBM's axes: `concentration_delta 0.05`, `substitutability_delta 0.15`, `lead_time_delta 0.25`. Both origins scored: `sk_hynix` (sub 0.35, lt 3y, conc 0.95, baseline 0.2627) and `product:hbm` (sub 0.05, lt 3y, conc 0.744, baseline 0.3008). The event's significance lives almost entirely in the two non-concentration axes.

| candidate | sk_hynix perturbed → contribution | hbm perturbed → contribution | origin Δ | max Δ | model_rank |
|---|---|---|---:|---:|---:|
| MA-0 | magnitude=0.05 → 0.2627×0.05 = **0.013137** | 0.3008×0.05 = **0.015038** | 0.015038 | 0.010515 | **4** |
| MA-1 | conc 0.95→1.0, sub 0.35→0.20, lt 3→3.25; sev 0.3553 → **0.092538** | conc 0.744→0.794, sub 0.05→0.0, lt 3→3.25; sev 0.3526 → **0.051879** | 0.092538 | 0.068225 | **3** |
| MA-1b | headroom conc; **0.075662** | **0.035357** | 0.075662 | 0.055783 | **1** |
| MA-2 | same as MA-1 origin; **0.092538** | **0.051879** | 0.092538 | 0.068225 | **1** |
| MA-3 | blended magnitude; **0.065109** | **0.074528** | 0.074528 | 0.052114 | **3** |

**MA-0 reads only `concentration_delta = 0.05`, so HBM's origin contribution is `0.015` — the smallest scored event — and it ranks 4th.** The moment the sub and lt deltas count (MA-1), sk_hynix's contribution jumps to `0.0925` — **6.15× MA-0** (Expectation #4: HIT, ≥3×; my estimate was ~5×, actual 6.15×) — and HBM moves to **rank 3**. Candidates that push it to **rank 1** are MA-1b and MA-2, both rejected below. So: every candidate improves HBM (Expectation #7: HIT), but the semantically-clean one (MA-1) moves it 4→3, not 4→1.

---

## W6 — Rank correlation, with the §4.1 caveat attached

> **§4.1 caveat, reproduced.** n = 7. Selecting a design by maximizing rank correlation on seven events is overfitting — the same "outcome entailed by the setup" failure this project has logged repeatedly. **The design is chosen on semantic grounds; ρ is a check, not a selector.** No normalization, weight, or combination rule was tuned to improve ρ. No candidate was preferred solely because HBM ranks higher under it. **No tuning was performed anywhere** — the five candidates are fixed designs, run once.

| candidate | ρ (Spearman vs observed) | per-event displacement (taiwan, asml, kachin, HBM, gallium, china-rees, nexperia) |
|---|---:|---|
| MA-0 | +0.7143 | −2, 0, +1, **+3**, −1, −1, 0 |
| MA-1 | +0.8929 | 0, 0, 0, **+2**, −1, −1, 0 |
| MA-1b | **+1.0000** | 0, 0, 0, **0**, 0, 0, 0 |
| MA-2 | +0.9286 | −1, 0, +1, **0**, −1, +1, 0 |
| MA-3 | +0.8571 | −1, 0, +1, **+2**, −1, −1, 0 |

**MA-1b's ρ = 1.0 is an overfitting artifact, not evidence it is correct** (Expectation #8: MISS — a perfect fit on n=7, which §6 flagged as suggesting circularity). It achieves perfect rank alignment by **suppressing the concentrated-mineral events**: headroom-relative concentration moves gallium `0.0044` and dysprosium even less, so china-rees's max Δ falls from MA-1's `0.106` to `0.039` and gallium's from `0.091` to `0.034`. That demotion of the two big mineral events is exactly what lifts HBM to rank 1. It is the §0.4 **under-firing** pathology — "a design that barely moves the most concentrated node may be under-firing rather than well-behaved" — dressed as a perfect score. **MA-0's ρ (0.7143) is reported** (Expectation #10: HIT): the status quo already correlates positively, so the case for change rests on the HBM inversion specifically (displacement +3), not on aggregate fit.

---

## W7 — Saturation

Per origin, concentration before, authored delta, effective move under additive (MA-1) vs headroom (MA-1b), and loss to the `[0,1]` clamp:

| event | node | conc | δ | MA-1 effective move | lost to clamp | MA-1b effective move |
|---|---|---:|---:|---:|---:|---:|
| gallium | mineral:gallium | 0.985224 | 0.30 | **0.014776** | 0.285224 | 0.004433 |
| china-rees | mineral:dysprosium | 0.990199 | 0.35 | **0.009801** | 0.340199 | 0.003432 |
| china-gallium | country_region:china | 0.628548 | 0.30 | 0.300000 | 0 | 0.111544 |
| china-rees | country_region:china | 0.628548 | 0.35 | 0.350000 | 0 | 0.130117 |
| kachin | country_region:kachin | 0.116755 | 0.20 | 0.200000 | 0 | 0.176650 |
| HBM | product:hbm | 0.744040 | 0.05 | 0.050000 | 0 | 0.012784 |

The two scored mineral origins — gallium and dysprosium, the most concentrated nodes in the graph — lose almost the entire authored delta to the clamp under additive perturbation (`0.285` and `0.340` lost). Headroom-relative (MA-1b) does not saturate, but moves them **even less** (`0.0044`, `0.0034`) — which is why **Expectation #6 is a MISS**: MA-1b moves gallium `0.004433` versus MA-1's `0.014776`, i.e. **less**, not more. The reviewer had the direction backwards; §3's own arithmetic ("moves it 0.0044 instead of saturating") agrees with the MISS.

---

## W8 — MA-2, rejected

Under `J-2025-04-china-rees` — a **dysprosium** export licence (`sub δ 0.10`, `lt δ 0.20`) — MA-2 re-scores every downstream node under those deltas applied to **its own** axes. One indefensible case, in one sentence:

> **MA-2 asserts the Chinese dysprosium export licence made `mineral:gallium`'s substitutability 0.10 harder** (contribution `0.0428`, hop 1) — but gallium is a distinct element with an independent supply chain that a dysprosium measure never touches; it is only graph-downstream here because it shares the `country_region:china` origin node.

The same walk applies the dysprosium deltas to `mineral:copper`, `mineral:indium`, and four data-center facilities (`facility:colossus`, `stargate_abilene`, …) — none of whose substitutability or lead-time a dysprosium licence changes. (`product:ndfeb_magnets` is the one downstream node where the re-score is *defensible* — NdFeB genuinely consumes dysprosium — which sharpens the point: MA-2 cannot tell the difference between the node it's right about and the six it's wrong about.) **MA-2 is rejected on evidence** (Expectation #9: HIT), not on argument: its ρ (0.9286) and its HBM rank (1) are good, and it is still wrong, because it fabricates axis movements on unrelated nodes.

---

## W9 — Recommendation, with the case against it

**Recommended (semantic grounds): MA-1 — axis perturbation at origin, scalar propagation.** It is the design `axes_for_severity`'s orphaned parameters were built for: it recomputes the origin's severity under the event's actual axis changes (concentration up, substitution harder, lead time longer) through the **real severity formula**, and takes the honest difference from baseline. It represents what the event did to the node's axes, and nothing else. It resolves the HBM inversion's mechanism — the event's significance lives in the sub/lt axes, which MA-0 discards — moving HBM from rank 4 to rank 3 and cutting its displacement from +3 to +2. It requires no re-authoring (the corpus is already risk-positive) and keeps the formula's structure (unlike MA-3) and locality (unlike MA-2).

**The case against MA-1.** It is **not** the highest-ρ candidate: MA-1b (1.0) and MA-2 (0.9286) both score higher and both put HBM at rank 1, which MA-1 does not. Taken at face value that looks like a concession — the recommended design fits the outcomes *worse* and *doesn't fully fix the inversion that motivated the pass.* It is not a concession, for two reasons the measurement establishes: MA-1b's higher ρ is bought by under-firing the two largest real events (W6) — a perfect score on n=7 that a single new event could break — and MA-2's is bought by fabricating axis movements on unrelated nodes (W8). **A semantically-worse design scoring higher on ρ than the semantically-correct one is exactly the §4.1 situation, and it is the finding, not a defect in MA-1.** What would change the recommendation: a larger, independent event corpus on which MA-1's ρ stayed below MA-2's *without* MA-2 exhibiting the indefensible re-scores — that would mean the locality objection costs real accuracy. On the current evidence it does not.

**On A-J-2 specifically:** the semantically-correct design improves the HBM inversion but does not eliminate it. Making HBM rank 1 on this corpus requires either the overfit (MA-1b) or the indefensible (MA-2) design. The honest reading is that the model still ranks the two Chinese mineral export-controls above HBM by max-Δ because they hit far more concentrated origins — and whether *that* is a model error or a defensible disagreement with the observed ordinal is a question the seven-event corpus cannot settle (W11).

---

## W10 — Blast radius of the recommendation (MA-1), if shipped later

- **Files that change:** `backend/app/scoring/cascade.py` — `_event_source_scale` (and the origin seeding in `propagate_event`) recompute severity under perturbed axes instead of `baseline × magnitude`. `backend/app/scoring/engine.py` — fix `axes_for_severity` to apply the **risk-positive** substitutability sign (subtract), and repair the stale docstring naming `_event_severity_at_source`.
- **`events.magnitude_source`:** repurposed, not simply retired. `concentration_delta` stops being the sole scalar magnitude and becomes one of three perturbed axes; the config key either points at the perturbation path or is removed with the scalar path.
- **Authored axes re-signing:** **none needed.** The corpus is already risk-positive; MA-1 applies the sign in code. (If axis-signed had been chosen instead, every non-zero `substitutability_delta` would need re-authoring — a reason the sign choice matters.)
- **Committed replay artifacts regenerate:** `summary.md` and the seven per-event pages — every event with a non-zero sub/lt delta changes its cascade and rank. `outcomes.json` unchanged (it is the measuring instrument).
- **`grading.md` re-grading:** **A-J-2 must be re-graded** — HBM 4→3 (partial fix), and the finding's framing shifts from "the model ignores the event's axes" to "the model reads the axes but still ranks concentration events higher." Any finding that quoted MA-0 replay ranks is affected.
- **Guards changed (forecast):** upgrade `test_cascade_and_engine_use_identical_axis_handling` from an import-identity assertion to an actual delta-handling identity between the engine and cascade paths; add a sign-convention regression test (a positive `substitutability_delta` must *raise* severity); add coverage that a non-zero delta actually flows through `propagate_event`.

---

## W11 — What this does not settle

- **Country-origin fanout and time decay are untouched.** The China export-control events still apply their delta at the all-customers level because the graph has no demand-by-geography decomposition; cumulative/time-decayed replay is still out of scope.
- **Seven events cannot validate a design; they can only rule some out.** This pass rules out MA-2 (indefensible re-scores) and flags MA-1b (overfit by under-firing), and recommends MA-1 on semantics. It does **not** prove MA-1 is right. **What would validate one:** a substantially larger, independently-authored event corpus with frozen outcome ordinals, on which the semantically-chosen design's rank correlation holds up *without* the rejected designs' pathologies — and ideally a held-out split so the check is not run on the same events used to reason about the design.

---

## W12 — Scorecard and standard sections

| # | expectation | verdict | evidence |
|---|---|---|---|
| 1 | Committed state byte-identical at close | **HIT** | severities/tiers byte-identical to snapshot; only `event.py` docstring + generated/harness files in diff (W1) |
| 2 | `axes_for_severity`'s deltas have no non-zero caller anywhere | **HIT** | 3 call sites, all delta-free; cascade + aggregator_validation import but never call (W2/§0.1) |
| 3 | `_event_severity_at_source` absent; the test naming it is dead/vacuous | **SPLIT — HIT on absence, MISS on the test claim** | function absent (only in a stale engine docstring); no test names it; the referenced test asserts real import identity, non-vacuously (W3) |
| 4 | HBM's MA-1 origin contribution ≥ 3× MA-0's | **HIT** | 0.092538 / 0.015038 = **6.15×** (est. ~5×) (W5) |
| 5 | Gallium's MA-1 effective concentration move < 0.02 despite δ 0.30 | **HIT** | 0.014776 (W7) |
| 6 | MA-1b moves gallium **more** than MA-1 | **MISS** | MA-1b 0.004433 < MA-1 0.014776 — headroom moves a concentrated node *less* (W7) |
| 7 | HBM's model_rank improves under at least one candidate | **HIT** | MA-1 4→3, MA-1b/MA-2 4→1, MA-3 4→3 (W4/W5) |
| 8 | No candidate achieves ρ = 1.0 | **MISS** | MA-1b = 1.0 — an overfitting flag (under-fires the mineral events), not correctness (W6) |
| 9 | MA-2 yields a downstream node whose perturbed axes are indefensible, nameable in one sentence | **HIT** | `mineral:gallium` re-scored by a dysprosium licence (W8) |
| 10 | MA-0's ρ reported alongside the others | **HIT** | ρ = +0.7143 (W6) |

Graded strictly (2–9). Two MISSes (6, 8) and one split (3) are all reviewer-side pre-registrations refuted by measurement — the intended outcome of a refutable scorecard.

### Guards changed

**None.** This pass adds no test and modifies no guard. (W10 forecasts the guard changes a future MA-1 ship would need.)

### Changed

- `backend/app/schema/event.py` — `AxesImpact` docstring only: the `lead_time_delta` unit (years) and the risk-positive substitutability sign, with the §0.1–§0.2 orphaned-path/sign-inversion caveat. **No behaviour change.**
- **New:** `backend/scripts/pass_w_measure.py` (in-process harness), `docs/generated/multi_axis_candidates.md`, `docs/generated/pass_w_facts.json`, this report, and the `grading.md` Pass W section.

### Not changed

- No file under `backend/app/scoring/`, `config/`, or `data/`. No authored `axes_impact` value edited. `events.magnitude_source` unchanged. No candidate committed. The served graph and all committed severities/tiers are byte-identical.

### Ledger — Pass W

- **Four code findings confirmed** (§0.1 orphaned multi-axis path; §0.2 inverted substitutability sign in the engine; §0.3 undeclared lead-time unit = years; §0.4 additive-concentration saturation on the most-concentrated origins). The engine docstring's reference to `cascade._event_severity_at_source` is stale — that function does not exist; the guard the docstring cites tests import identity only.
- **Conventions declared (docstring only):** risk-positive substitutability, lead-time delta in years. No behaviour shipped.
- **Five candidates measured through the real engine**, MA-0 validated node-for-node (0 mismatches). Recommendation on semantic grounds: **MA-1** (axis perturbation at origin, scalar propagation), which resolves the HBM inversion's mechanism and moves it rank 4→3.
- **MA-1 is not the highest-ρ candidate, and that is the finding.** MA-1b reaches ρ=1.0 by under-firing the two largest mineral events (the §0.4 pathology); MA-2 reaches HBM=rank 1 by fabricating axis movements on unrelated nodes (gallium re-scored by a dysprosium licence). Both rejected; ρ is a check, not a selector, and nothing was tuned.
- **A-J-2 partially addressed, not closed.** The semantically-correct design improves HBM by one rank but does not make it rank 1; forcing rank 1 requires a rejected design. Whether the model's ranking of the mineral export-controls above HBM is an error is unsettleable on n=7.
- **Suite:** 134 pass, 1 skip, 0 xfail — both invocations. Measurement reproducible on a second run. Committed scoring byte-identical.
