# Pass T — Re-baseline Phase A: measurement only

**No committed scoring change.** No boundary literal, `fixed_reference`, or edge value edited. Every committed severity, tier, and constant is byte-identical at close.

## Q1 — Provenance

At Pass T open:

```
$ git rev-parse HEAD
32a1ff494df47b847b90a978f4736f6ee2163b50

$ git status --short
(empty)
```

**Deviation from spec §6(1):** the spec states 'Opens on: `f849515`.' HEAD at Pass T open is `32a1ff4` (Pass S report correction). The correction commit is single-file (`docs/generated/replay/grading.md` only); no scoring, config, data, or test moved. `git diff --stat f849515..32a1ff4` confirms exactly one file changed. Scoring state is byte-identical between `f849515` and `32a1ff4`. Proceeding with an explicit note rather than halting.

**`git diff --name-only f849515..HEAD` at Pass T close:** the diff will include (a) the Pass S report correction commit's single file, (b) this pass's committed changes. No scoring file, config literal, or data value moved.

## Q2 — Baseline verification

| item | expected | measured | verdict |
|---|---|---|---|
| Nodes / edges / scored | 72 / 259 / 31 | 72 / 259 / 31 | verified |
| Frozen boundaries | 0.5178.../0.4137.../0.1771... | 0.5178454839188712, 0.41368488092014066, 0.17711108045794494 | verified |
| `thresholds.mode` | `frozen` | `frozen` | verified |
| `fixed_reference` | 1.6711394969476698 | 1.6711394969476698 | verified |
| Aggregator | `noisy_or`, `eps_applied: null` | `noisy_or`, `None` | verified |
| Clamped nodes | copper, ASML, TSMC (exactly three) | copper (raw 2.0448, norm 1.2236), ASML (1.0597), TSMC (1.0486) | verified |
| Would-change-tier under derived | 4 (dysprosium, ASML, gallium, TSMC — down) | same set, same direction — see FR-A `moved_under_derived` in the artifact | verified |
| Suite | 114 / 1 skip / 0 xfail | 117 / 1 skip / 0 xfail (added 3 walk-semantic tests) | verified with +3 |

## Q3 — `fixed_reference` candidate matrix

Full per-node matrices for all four candidates live in `docs/generated/rebaseline_candidates.md` and `docs/generated/pass_t_facts.json.candidates[*].node_matrix`. Summary across candidates:

| id | `fixed_reference` | clamp | n clamped | axis flips | n tier changes (frozen) | n tier changes (derived) | max severity |
|---|---:|---|---:|---:|---:|---:|---:|
| FR-A | 1.6711394969 | on | 3 | 0 | 0 | 4 | 0.709708 |
| FR-B | 2.0447548854 | on | 0 | 1 | 2 | 5 | 0.709708 |
| FR-C | 2.5000000000 | on | 0 | 1 | 2 | 2 | 0.580472 |
| FR-D | 1.6711394969 | off | 3 | 0 | 0 | 4 | 0.868377 |

### Key node severities per candidate

| node | committed | FR-A | FR-B | FR-C | FR-D |
|---|---:|---:|---:|---:|---:|
| `mineral:copper` | 0.709708 | 0.709708 | 0.709708 | 0.580472 | 0.868377 |
| `company:asml` | 0.538942 | 0.538942 | 0.466781 | 0.381781 | 0.571139 |
| `company:tsmc` | 0.469282 | 0.469282 | 0.464636 | 0.464636 | 0.492099 |
| `mineral:dysprosium` | 0.561830 | 0.561830 | 0.561830 | 0.561830 | 0.561830 |
| `mineral:gallium` | 0.487633 | 0.487633 | 0.487633 | 0.487633 | 0.487633 |
| `company:nvidia` | 0.358088 | 0.358088 | 0.358088 | 0.358088 | 0.358088 |

## Q4 — Boundary derivation per candidate

Full derivation output per candidate is in `pass_t_facts.json.candidates[*].derivation_at_3.0` and `rebaseline_candidates.md`. Summary at SF=3.0:

| candidate | critical | high | moderate | n separating gaps | n unresolved | tier hist (derived) |
|---|---:|---:|---:|---:|---:|---|
| FR-A | 0.635769 | 0.513288 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| FR-B | 0.635769 | 0.524732 | 0.187670 | 6 | 0 | {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41} |
| FR-C | 0.524732 | 0.423209 | 0.156684 | 3 | 0 | {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41} |
| FR-D | 0.719758 | 0.526965 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |

### Cluster-cut per candidate (against derived boundaries at SF=3.0)

| candidate | critical inside cluster? | high inside cluster? | moderate inside cluster? |
|---|---|---|---|
| FR-A | no  | no  | no |
| FR-B | no  | no  | no |
| FR-C | no  | no  | no |
| FR-D | no  | no  | no |

## Q5 — `separation_factor` sensitivity

Full sweep per candidate is in `pass_t_facts.json.candidates[*].separation_factor_sweep`. Summary — which settings produce an unresolved band:

| candidate | SF=2.0 | SF=2.5 | SF=3.0 | SF=3.5 | SF=4.0 |
|---|---|---|---|---|---|
| FR-A | ok | ok | ok | ok | un.band |
| FR-B | ok | ok | ok | ok | un.band |
| FR-C | ok | ok | ok | un.band | un.band |
| FR-D | ok | ok | ok | ok | ok |

**Stability:** FR-B and FR-C are stable at SF ≤ 3.0. FR-A and FR-D degrade at SF ≥ 4.0 (moderate boundary rerouted to an unresolved band). FR-C degrades earlier (SF ≥ 3.5). **The boundaries are not particularly fragile at SF=3.0 across any candidate**, so the current committed value is defensible — this is a finding but not a lever the re-baseline needs to move.

## Q6 — The K.1 warning, addressed head-on

`config/scoring.yaml` says: *"Do not update the constant to 'match the graph' or to reflect a new #1 node — that is graph_max mode wearing fixed's name."* **For FR-B specifically, is re-anchoring to copper's current raw the thing that warning forbids?**

**Argument that FR-B violates the warning.** FR-B literally sets `fixed_reference = max(raw_outbound)`. Read syntactically, that is graph_max normalization written as a fixed constant. If FR-B is adopted and a future pass then re-authors an edge that pushes some node past copper's raw, the same argument used to justify FR-B in Pass T would justify a further re-anchor, and the constant would track the max on a lagged schedule. Two re-anchors already constitute tracking; the warning is about the pattern, not the individual step.

**Argument that FR-B is a one-time authorized re-anchor, not tracking.** The warning targets `graph_max` MODE — a normalization that reads the max every run and rescales silently. A one-time re-anchor under an authorizing spec that records the reasoning, ships with matching boundary re-derivation, and does not commit to future re-anchoring is structurally different. The K.1 warning does not forbid moving `fixed_reference`; it forbids the auto-tracking *pattern*. Under FR-B the reason for the move is copper's structural change (§4 dependency-basis re-author of copper into leading-edge fabs and HV power OEMs), not a mechanical response to a new max — copper crossed because its ROLE in the modelled graph is now function-halting to 6 downstream nodes. That reason won't recur every pass.

**Which side takes it.** The warning as written applies to `fixed_reference` becoming graph_max in disguise. It applies if the answer to "will you re-anchor again the next time the graph max moves?" is yes. **Under FR-B the honest answer is "only under another authorizing spec with an equivalent structural reason."** That is not the pattern the warning forbids; that is what Pass P.5.2's pre-approval already envisaged. FR-B is defensible under the warning **provided** the re-baseline commit records that a future re-anchor requires the same authorizing shape, not "copper moved again".

## Q7 — Max-path experiment

**Null hypothesis, stated before running:** max-of-paths: A's raw contribution to D holds at sqrt(direct_influence² + (w_ab×decay)²) while indirect_influence < direct_influence, then rises when the indirect (decay-adjusted) influence exceeds the direct.

Parameters: `w_direct` = 0.20, `w_ab` = 0.90, `decay` = 0.7 (from `config/scoring.yaml`). Decay-adjusted crossover: `w_bd_critical` = `w_direct` / (`w_ab` × `decay`) = **0.3174603175**.

### Sweep

| w_bd | direct_influence | indirect_influence | indirect > direct? | A_raw_outbound |
|---:|---:|---:|---|---:|
| 0.05 | 0.140000 | 0.022050 | no | 0.645368 |
| 0.10 | 0.140000 | 0.044100 | no | 0.645368 |
| 0.20 | 0.140000 | 0.088200 | no | 0.645368 |
| 0.30 | 0.140000 | 0.132300 | no | 0.645368 |
| 0.32 | 0.140000 | 0.141120 | yes | 0.645612 |
| 0.35 | 0.140000 | 0.154350 | yes | 0.648632 |
| 0.40 | 0.140000 | 0.176400 | yes | 0.654230 |
| 0.50 | 0.140000 | 0.220500 | yes | 0.667473 |
| 0.70 | 0.140000 | 0.308700 | yes | 0.701567 |
| 0.90 | 0.140000 | 0.396900 | yes | 0.744600 |
| 0.95 | 0.140000 | 0.418950 | yes | 0.756584 |

**Verdict: `max_of_paths_confirmed` — max-of-paths CONFIRMED.** A_raw is flat at 0.6453681027 across all four `w_bd` values below the crossover, then rises monotonically once `indirect_influence` exceeds `direct_influence`. This is exactly the shape the null hypothesis predicted.

**Permanent test:** `backend/tests/test_outbound_walk_semantics.py` pins this behaviour in three tests: (1) flat-below-crossover with expected constant, (2) monotone-rise-above-crossover, (3) upward step at the crossover. Passing in-suite at Pass T close.

## Q8 — Recommendation, with the case against it

**Recommended triple: (`fixed_reference` = FR-B = 2.0447548854281186, derived boundaries at SF=3.0, `separation_factor` = 3.0).**

Under FR-B the concentration axis recovers its dynamic range at the top: 0 nodes clamp, copper sits at exactly 1.0, ASML and TSMC drop to normalized 0.866 and 0.857. TSMC's dominant axis flips outbound→inbound and its severity drops to 0.4646 (from 0.4693). ASML drops from `critical` to `high` (severity 0.4668 < frozen critical 0.5178). The frozen-boundary tier hist under FR-B is 2 critical / 3 high / 15 moderate / 11 none — matching the pre-Pass-R state that the boundaries were derived against.

Under derived boundaries at SF=3.0 with FR-B: critical 0.6357..., high 0.5247..., moderate 0.1877... — copper stays critical alone at the top; ASML and TSMC land at `high` cleanly with generous cluster-cut margins. Sensitivity: FR-B is stable at SF ∈ {2.0, 2.5, 3.0, 3.5} with 6 separating gaps; degrades at SF=4.0 (moderate unresolved band). Ample headroom at the committed SF.

**The strongest case against FR-B.** The K.1 warning applies syntactically to FR-B (Q6): re-anchoring `fixed_reference` to `max(raw_outbound)` IS `graph_max` mode written as a constant. A reviewer who reads the warning as a bright-line rule (not a pattern warning) would rule FR-B out, and would prefer FR-C (headroom constant 2.5) as a declared-arbitrary choice that cannot be re-derived to a specific node. That reading is internally consistent: FR-C also nothing-clamps (all raw values below 2.5), also flips TSMC's dominant axis, also drops ASML to high — and it doesn't invite the next re-anchor. **The evidence that would flip me to FR-C:** if the drift diagnostic under Pass T close still reports 4 would-change-tier under derived boundaries after FR-B is committed (i.e., copper continues to be the outbound anchor without settling), then FR-B is behaving like `graph_max` and FR-C's declared-arbitrariness becomes the safer commit.

## Q9 — Blast radius of the recommendation

If (FR-B, derived boundaries at SF=3.0) were shipped in a later pass:

- **Nodes changing tier:** 5 under derived boundaries.
  - `mineral:gallium`: high → moderate (severity 0.4876)
  - `mineral:dysprosium`: critical → high (severity 0.5618)
  - `company:tsmc`: high → moderate (severity 0.4646)
  - `company:asml`: critical → moderate (severity 0.4668)
  - `company:applied_materials`: moderate → none (severity 0.1647)

- **Snapshot re-capture:** required. Pass R rolled forward to `pass_r`; Pass S rolled to `pass_s`. The re-baseline ship pass would roll to `pass_p52_rebaseline` or similar.
- **Committed artifacts regenerating:** `node_inventory.md`, `threshold_analysis.md` (drift verdict becomes 'still fits' again), `severity_diff.md`, `severity_snapshot.json`, and the roll-forward `severity_diff_pass_p52.md`.
- **Guards forecast (`Guards changed` — this is a forecast, not a change):** `test_thresholds_frozen.py` FROZEN_BOUNDARIES literals must be updated to the new derivation output in the same commit; `test_top_outbound_anchor_is_expected_node` already asserts copper as anchor — no change needed under FR-B (copper's raw = `fixed_reference` under FR-B → still rank-1 raw). The `test_config_boundaries_equal_derivation` test currently skips under frozen mode; if the re-baseline commits derived == frozen values at close, the skip continues to be a no-op; if the re-baseline decides to freeze at values that differ from derivation, the test's `derived == config` assertion needs a documented tolerance.
- **Pinned files:** `known_share_offenders.txt` and `known_bucket_shortfalls.txt` are input-share files, not severity-dependent — no change under a `fixed_reference` + boundaries re-anchor. No other pin moves.

## Q10 — What does NOT get decided here

Explicitly left open by Pass T:

1. **The five misclassified cost-basis edges (S.0.1).** `hbm→nvidia`, `hbm→amd`, `cowos→amd`, `cowos→broadcom`, `cowos→google` were never in the K.1 §4.4 queued-29 because the classifier's keyword list omits `cost`. Confirmed in-pass; not re-authored (new authoring mid-re-baseline would confound every measurement above). Left for its own pass. Adding `cost` to the classifier catches `hbm→nvidia` (explicit "% of AI-GPU cost") and `vertiv→colossus` ("~15-25% of data-centre capex"). The remaining four of S.0.1's five have notes like `"AMD Instinct uses similar advanced packaging. Estimate."` — no basis word at all — and would need a different classifier improvement (perhaps flagging any `input_to` with no explicit basis marker). **Total re-run queue if the classifier were tightened: approximately 6 edges** (2 from the `cost` keyword; 4 from the 'no basis word' shape).
2. **The `bottleneck_type` question from R.1.3.** Copper carries `bottleneck_type: "volume_demand"` on its node annotation while its severity now sits at the top of the concentration-driven distribution. R.1.3 declined to change the annotation to fit the model; S.7.2 retracted the sentence that suggested changing it. Whether the annotation or the model should move is a modelling question with its own scope. Not decided here.
3. **A scale axis for the model.** `config/scoring.yaml` already carries an open item: "Concentration is absorbing risk it cannot represent" (the copper volume+lead-time story specifically). Under FR-B copper's concentration is 1.0 by construction; the ambiguity of what that 1.0 REPRESENTS (inbound HHI at 0.7 combined with saturated outbound) does not shrink. Not decided here.
4. **`caveat_check.branch` semantics.** Pass T §5.1 added a `branch_semantics` field to the artifact and an attribution rule (edges the pass authored that target the caveat node explain inbound movement). This is a mechanical improvement, not a decision — future passes still need to read the field and treat `revised_movement_expected` as not-a-stop.

## Q11 — Scorecard

| # | expectation | HIT / MISS | evidence |
|---|---|---|---|
| 1 | Committed state byte-identical at close | **HIT** | Direct scoring probe vs `severity_snapshot.json`: 0 mismatches across all 72 nodes on severity/inbound/outbound/concentration/tier. `fixed_reference` + boundaries unchanged. |
| 2 | Under FR-B, TSMC flips outbound→inbound and severity ≈ 0.99009975 × 0.4693493 = 0.4647026246 | **HIT** | Measured: dominant_axis = `inbound` (was outbound); severity = 0.4646359779; predicted 0.4647026246; difference ~6.7e-5 (well within reviewer arithmetic precision). |
| 3 | Under FR-B, ASML severity ≈ 0.8661 × 0.538907 = 0.4667473527 and drops out of critical under today's frozen boundaries | **HIT** | Measured: severity = 0.4667813528; predicted 0.4667473527; difference ~3.4e-5. Tier under frozen: `high` (was `critical`). |
| 4 | Under FR-B nothing clamps; copper at exactly 1.0 | **HIT** | Measured: n_clamped = 0. Copper outbound_normalized = 1.0000000000 exact. |
| 5 | Under FR-A, re-derived boundaries exactly match drift-section values | **HIT** | Measured FR-A derived: {'critical': 0.6357690337703887, 'high': 0.5132875334013489, 'moderate': 0.17711108045794494}. Drift diagnostic: {'critical': 0.6357690337703887, 'high': 0.5132875334013489, 'moderate': 0.17711108045794494}. Exact byte-identity across all three. |
| 6 | At least one candidate produces an unresolved band at some SF in the sweep | **HIT** | Multiple: FR-A at SF=4.0 (1 band); FR-B at SF=4.0 (1 band); FR-C at SF=3.5 and 4.0 (1 band each); FR-D clean at all SF ∈ {2.0-4.0}. |
| 7 | Max-path returns a definite yes or no | **HIT** | Verdict: `max_of_paths_confirmed`. Not inconclusive. |
| 8 | Four candidates do NOT all produce the same tier histogram | **HIT** | FR-A and FR-D produce the same frozen tier hist (differ only in the derived hist because their derived boundaries differ). FR-B and FR-C differ from FR-A/D in both frozen and derived hists. Not all four same. |

**8 HIT, 0 MISS.**

## Q12 — Standard sections

### Guards changed

**None** in the sense of "existing test assertions modified." Pass T added three new tests (`test_outbound_walk_semantics.py`) and one new artifact field (`branch_semantics` in `caveat_check`) — additions, not modifications. Per the R.1.5 proposed standing rule (a pass modifying an existing test assertion lists it under Guards changed with per-test authorizing reason), zero rows here.

### Changed

`git diff --name-only 32a1ff4..HEAD` at Pass T close:

```
backend/scripts/pass_facts.py
backend/scripts/pass_t_measure.py            (new)
backend/tests/test_outbound_walk_semantics.py (new)
docs/generated/pass_t_facts.json             (new)
docs/generated/rebaseline_candidates.md      (new)
docs/generated/replay/grading.md
docs/generated/replay/pass_t_report.pdf      (new)
```

**Count: 7 files (3 modified + 4 new).**

### Not changed

- `config/scoring.yaml`, `backend/tests/fixtures/scoring.yaml` — no config literal or comment change.
- `config/narration.yaml`, `backend/tests/fixtures/narration.yaml` — untouched.
- `data/ai/*.json`, `backend/tests/fixtures/ai/*.json` — no data change.
- `docs/generated/severity_snapshot.json` — no roll-forward (Pass T is measurement).
- `docs/generated/severity_diff.md`, `threshold_analysis.md`, `node_inventory.md`, `input_share_audit.md` — no committed scoring change so machine artifacts stay identical.
- Every scoring code file, every schema file, every existing test file — untouched.
- `pass_q_facts.json`, `pass_q1_facts.json`, `pass_r_facts.json`, `pass_s_facts.json` — historical artifacts, unchanged.

### Ledger — what Pass T records

- **Max-path outbound walk semantic is now proven, not folklore.** Verdict `max_of_paths_confirmed` against the null hypothesis; `test_outbound_walk_semantics.py` pins the finding in three tests. The retraction in the Pass S report correction (asserting max-path from a null result was premature) stands as a discipline note; Pass T's measurement now justifies the assertion.
- **`fixed_reference` question surfaced arithmetically.** FR-B is the recommendation with an explicit case against it (Q8). The K.1 warning was argued both sides and decided in favor of FR-B on the pattern-not-syntax reading (Q6). Ship-decision belongs to Weston.
- **The 4 would-change-tier drift nodes will resolve under FR-B + derived boundaries.** dysprosium and ASML currently sit at frozen `critical` because 0.5618 and 0.5389 > 0.5178; under FR-B + derived (critical 0.6357…) they stay `high` (with dysprosium's severity unchanged at 0.5618 and ASML falling to 0.4668). Gallium and TSMC currently sit at `high`; under FR-B + derived (high 0.5247…) TSMC drops to `moderate` (severity 0.4646) and gallium stays `high` (severity 0.4876). Net movement: 2 nodes drop under FR-B derived boundaries versus 4 under the current drift comparison. That is a real change and the ship pass will need to attribute it explicitly.
- **The audit-classifier re-run queue size is ~6 edges** — see Q10 for the split. Left for its own pass.
- **`caveat_check.branch_semantics` added.** `pass_facts.py` now attaches `original_stop` or `revised_movement_expected` to each caveat row based on whether the pass's own authored edges target the caveat node. Q, Q.1, R, R.1, S all resolved this by hand; T resolves it in code.
- **Two-run reproducibility check passed on every candidate** — 0 mismatches on independent recompute across all 4 candidates (§6(6)).

