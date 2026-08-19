# Pass U — Re-baseline, Phase B: ship FR-C

**Type:** Constant change. `fixed_reference` and the three tier boundaries move; their guards move in the same commit; snapshots re-baseline. No edge value, node value, formula, aggregator, or code-path change. One measurement/facts script and one guard-gap test set were added.

**Decision shipped:** FR-C — `fixed_reference = 2.5`, boundaries re-derived at `separation_factor 3.0` from the FR-C distribution: critical `0.5247316525037853`, high `0.42320867926942163`, moderate `0.15668443545638666`.

Every number below is read from `docs/generated/pass_u_facts.json` (written by `backend/scripts/pass_u_measure.py`), `docs/generated/severity_diff_pass_u.md`, and `docs/generated/threshold_analysis.md`. The report quotes the artifacts; it does not recall numbers.

---

## U1 — Provenance

- **HEAD at open:** `1dbdd465092faf433e821b5aef49c28358f73898` (Pass T). The spec required verifying this because Pass T itself opened on a corrected HEAD rather than the one its spec named. Confirmed: HEAD **was** `1dbdd46` at open.
- **HEAD at close:** unchanged until the Pass U commit is made; the commit is this pass's single commit (see §10 / U12).
- **`git status --short` at open:**
  ```
   M docs/generated/replay/grading.md
  ?? docs/generated/replay/pass_t_addendum.md
  ?? docs/generated/replay/pass_t_addendum.pdf
  ```
  The working tree carried only the Pass T addendum artifacts (untracked) and the addendum's grading.md ledger edit. No scoring state was dirty at open.
- **`git diff --name-only 1dbdd46..HEAD`** (tracked files changed by this pass, pre-commit working set):
  ```
  backend/tests/_out/outbound_sensitivity.txt
  backend/tests/fixtures/scoring.yaml
  backend/tests/test_thresholds_frozen.py
  backend/tests/test_unscored.py
  config/scoring.yaml
  docs/generated/node_inventory.md
  docs/generated/replay/grading.md
  docs/generated/severity_diff.md
  docs/generated/severity_snapshot.json
  docs/generated/threshold_analysis.md
  ```
  New (untracked, added by this pass): `backend/scripts/pass_u_measure.py`, `docs/generated/pass_u_facts.json`, `docs/generated/severity_diff_pass_u.md`.
- **No edge, node, or scoring-code file moved.** `data/` is untouched; `backend/app/scoring/` and `backend/app/graph/` are untouched; `edges.json`, `nodes.json`, `events.json` are untouched. Verified by filtering the diff against those paths — the set is empty.

The one non-obvious entry, `backend/tests/_out/outbound_sensitivity.txt`, is a **test-generated diagnostic** (a sensitivity probe that hypothetically removes the top-outbound node and renormalizes). It regenerated because copper's normalized outbound moved `1.000 → 0.818`; it is not scoring code, an edge, or a node value, and its change is a downstream consequence of the constant change. Detailed in U12.

---

## U2 — The three K.1 requirements

`test_fixed_reference_is_frozen`'s docstring names three conditions for a legitimate change to the constant. **This pass is the first invocation of that clause.**

1. **An explicit spec authorization stating why.** This document (§0 of the Pass U spec, restated at the top here) authorizes FR-C. The reasoning on the record: smaller blast radius than FR-B (2 tier changes vs 5); a clean relationship to the K.1 graph_max warning (2.5 is a declared-arbitrary headroom value, not `max(raw_outbound)`, so the warning does not engage); and the observation that FR-B's dynamic-range advantage was cosmetic (copper reading exactly 1.0 rather than 0.818 changes no ordering). The accepted cost — FR-C enters an unresolved band at `separation_factor 3.5` where FR-B holds to 4.0 — is stated knowingly.

2. **A full re-baseline of every committed severity snapshot.** Performed. The pre-U `severity_snapshot.json` (label `pass_s`, `fixed_reference 1.6711…`, FR-A boundaries) was the diff reference; after re-scoring under FR-C, the snapshot was rolled forward atomically to label `pass_u_rebaseline` (`fixed_reference 2.5`, FR-C boundaries) via `generate_inventory.py --roll-forward`. The pre-U → post-U transition is captured permanently in `severity_diff_pass_u.md` before the snapshot was overwritten; the ordering is enforced in code (the diff is written before the snapshot rolls).

3. **Updating the literal in the SAME commit as the config change.** Both guard literals move in this commit: `test_thresholds_frozen.py::FROZEN_BOUNDARIES` → the FR-C triple, and `test_unscored.py::_FROZEN_FIXED_REFERENCE` → `2.5`. Neither the config nor the guards were committed independently.

---

## U3 — Constant changes, before and after

| key | before | after |
|---|---|---|
| `concentration.outbound.normalization.fixed_reference` | `1.6711394969476698` | `2.5` |
| `thresholds.boundaries.critical` | `0.5178454839188712` | `0.5247316525037853` |
| `thresholds.boundaries.high` | `0.41368488092014066` | `0.42320867926942163` |
| `thresholds.boundaries.moderate` | `0.17711108045794494` | `0.15668443545638666` |
| `thresholds.mode` | `frozen` | `frozen` (unchanged) |

**`thresholds.mode` never left `frozen`.** `derived` was never committed. The derivation ran only as an in-process diagnostic (§2.2 / U4) and via the drift section of `threshold_analysis.md`; `_write_boundaries_to_config` is a no-op under frozen mode and did not touch either YAML.

**Rewritten `fixed_reference` comment block** (quoted from `config/scoring.yaml`):

> ```
> # ------------------------------------------------------------------
> # Pass K.1 §2 (DECIDED: Option A) — FROZEN SCALE CONSTANT.
> # Pass U (FR-C, re-baseline Phase B) — re-authored value + basis.
> #
> # This value is a permanent scale constant. Its purpose is exactly
> # to make `fixed` mode NOT behave like `graph_max`; re-deriving it
> # each pass collapses the two modes into one and destroys cross-pass
> # severity comparability. That collapse was what Pass K silently did:
> # `outbound_criticality = raw / fixed_reference` with fixed_reference
> # re-derived from the same graph — always 1.0 at the ranking-1 node,
> # regardless of graph edits.
> #
> # The value below is a DECLARED-ARBITRARY HEADROOM CONSTANT. It is
> # deliberately NOT equal to any node's raw outbound — no node
> # produces 2.5. It is chosen ABOVE the current graph maximum raw
> # outbound (mineral:copper, 2.0447548854281186) so that (a) nothing
> # clamps under `fixed` normalization and (b) near-term authoring
> # growth does not push a node back over 1.0 and re-clamp. Prior to
> # Pass U the constant was ASML's raw outbound from the honesty-fixes
> # pass (1.6711394969476698); Pass T measured that this clamped the
> # top three outbound nodes (copper, ASML, TSMC) at 1.0 and flattened
> # the concentration axis. FR-C trades that flattening for one step of
> # separation-factor headroom (accepted cost, Pass U §0).
> #
> # Changing this value requires an explicit spec authorization and a
> # full re-baseline of committed severity snapshots. It is guarded by
> # test_fixed_reference_is_frozen (Pass K.1 §5.3) which fails if the
> # literal drifts. Do not update the constant to "match the graph" or
> # to reflect a new #1 node — that is graph_max mode wearing fixed's
> # name.
> # ------------------------------------------------------------------
> ```

The `graph_max` warning (final paragraph) is kept **verbatim** from the K.1 text — it is more relevant now, not less: a future author looking at a max of ~2.04 will be tempted to re-anchor to it.

---

## U4 — Derivation reproduction

Re-run against the **post-change** distribution (31 scored severities under `fixed_reference 2.5`) at `separation_factor 3.0`:

- Median adjacent gap: `0.014621990208914283`
- Separating threshold (`3.0 × median`): `0.04386597062674285`
- Separating gaps: **3** — every required boundary landed on one.

| boundary | separating gap (upper → lower) | gap size | midpoint = boundary |
|---|---|---:|---:|
| critical | dysprosium 0.5618299974 → gallium 0.4876333076 | 0.0741966898 | `0.5247316525037853` |
| high | TSMC 0.4646359779 → ASML 0.3817813806 | 0.0828545973 | `0.42320867926942163` |
| moderate | KLA 0.1786428582 → applied_materials 0.1347260127 | 0.0439168455 | `0.15668443545638666` |

**Byte-identity confirmed on both axes:** the three derived boundaries equal (a) the committed config literals and (b) Pass T's measured `candidates["FR-C"].derivation_at_3.0`, to full float precision (`derivation_reproduction.byte_identical_to_committed = true`, `byte_identical_to_pass_t_measurement = true`, `reproduces = true`). No mismatch — stop-condition §7.2 not triggered. **Expectation #1: HIT.**

---

## U5 — Full severity movement table

Every scored node, sorted by post-change severity. `mechanism` is Pass U's causal classification (from `pass_u_facts.json`, computed against raw outbound + clamp state); `diff cause` is what `build_severity_diff` independently labelled the row (§U7). Full precision.

| node | sev before | sev after | delta | axis before | axis after | tier before | tier after | mechanism | diff cause |
|---|---:|---:|---:|---|---|---|---|---|---|
| mineral:copper | 0.7097080701 | 0.5804716175 | -0.1292364527 | outbound | outbound | critical | critical | clamp_release | STRUCTURAL |
| mineral:dysprosium | 0.5618299974 | 0.5618299974 | +0.0000000000 | inbound | inbound | critical | critical | inbound_unchanged |  |
| mineral:gallium | 0.4876333076 | 0.4876333076 | +0.0000000000 | inbound | inbound | high | high | inbound_unchanged |  |
| company:tsmc | 0.4692819869 | 0.4646359779 | -0.0046460090 | outbound | inbound | high | high | clamp_release | STRUCTURAL |
| company:asml | 0.5389417592 | 0.3817813806 | -0.1571603786 | outbound | outbound | critical | moderate | clamp_release | STRUCTURAL |
| company:nvidia | 0.3580877750 | 0.3580877750 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| product:ndfeb_magnets | 0.3403936857 | 0.3403936857 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| product:arm_core_ip | 0.3299643424 | 0.3299643424 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| product:cowos_packaging | 0.3296191633 | 0.3296191633 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:ge_vernova | 0.3184155904 | 0.3184155904 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:siemens_energy | 0.3151159470 | 0.3151159470 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| product:hbm | 0.3007539900 | 0.3007539900 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| mineral:neodymium | 0.2950795735 | 0.2950795735 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| product:rf_power_semis | 0.2872071723 | 0.2872071723 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:samsung | 0.2835434725 | 0.2835434725 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:sk_hynix | 0.2627413761 | 0.2627413761 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:micron | 0.2425305011 | 0.2425305011 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:arm | 0.2106185930 | 0.2106185930 | +0.0000000000 | inbound | inbound | moderate | moderate | inbound_unchanged |  |
| company:lam_research | 0.2716304489 | 0.1815729487 | -0.0900575002 | outbound | outbound | moderate | moderate | clean_rescale | RESCALE |
| company:kla | 0.2672470768 | 0.1786428582 | -0.0886042186 | outbound | outbound | moderate | moderate | clean_rescale | RESCALE |
| company:applied_materials | 0.2015481248 | 0.1347260127 | -0.0668221120 | outbound | outbound | moderate | none | clean_rescale | RESCALE |
| mineral:indium | 0.1198439893 | 0.1198439893 | +0.0000000000 | inbound | inbound | none | none | inbound_unchanged |  |
| company:synopsys | 0.1526740361 | 0.1020558448 | -0.0506181914 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:cadence | 0.1221392289 | 0.0816446758 | -0.0404945531 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:quanta_services | 0.0765885793 | 0.0765885793 | +0.0000000000 | inbound | inbound | none | none | inbound_unchanged |  |
| company:vertiv | 0.0686764073 | 0.0686764073 | +0.0000000000 | inbound | inbound | none | none | inbound_unchanged |  |
| company:tokyo_electron | 0.0928948847 | 0.0620961244 | -0.0307987604 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:siemens_eda | 0.0366338858 | 0.0244881334 | -0.0121457524 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:nikon | 0.0207811919 | 0.0138913082 | -0.0068898837 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:hitachi_high_tech | 0.0088557516 | 0.0059196785 | -0.0029360731 | outbound | outbound | none | none | clean_rescale | RESCALE |
| company:canon | 0.0035715304 | 0.0023874102 | -0.0011841202 | outbound | outbound | none | none | clean_rescale | RESCALE |

**Movement classes (31 scored):** 18 `inbound_unchanged` (delta exactly 0), 10 `clean_rescale` (un-clamped outbound-dominant, scale by `0.6684557988`), 3 `clamp_release` (copper, ASML, TSMC — previously clamped at outbound = 1.0). **Zero `unexplained` deltas** — stop-condition §7.4 not triggered. Every non-zero delta is a consequence of the `fixed_reference` change alone.

---

## U6 — The two tier changes, attributed

Both tier changes are caused by the `fixed_reference` change. **Neither node changed structurally** — no edge into or out of ASML or applied_materials was touched (confirmed against the diff scope, U1). No node axis input moved. The concentration axis moved because the denominator moved.

**`company:asml`: critical → moderate (2 tiers down).**
- Mechanism: `clamp_release`. Before, ASML's raw outbound `1.7710…` normalized to `1.7710/1.6711 = 1.0596 > 1.0` and was **clamped** to `outbound_criticality = 1.0`; concentration = max(inbound 0.0, 1.0) = 1.0; severity = `1.0 × coef = 0.5389417592`.
- After, `1.7710/2.5 = 0.7084…`, no longer clamped; concentration = 0.7084…; severity = `0.7084… × coef = 0.38178138064859357`.
- The `coef` (= `(1−sub)·log10(lt+1)/log10(26)`) is a node property and did not move; the whole delta is the release of the clamp. ASML crosses the FR-C **high** boundary `0.4232…` (falls below) and the **critical** boundary; it lands in `moderate` (`0.1567… ≤ 0.3818 < 0.4232`). Two tiers.

**`company:applied_materials`: moderate → none (1 tier down).**
- Mechanism: `clean_rescale`. AMAT was **not** clamped before (raw `1.1308…`, `1.1308/1.6711 = 0.6767 < 1.0`). Severity scales by exactly `0.6684557988`: `0.20154812477767337 × 0.6684557988 = 0.1347260127406829`.
- It crosses the FR-C **moderate** boundary `0.15668443545638666` from above; `0.1347… < 0.1567…` → `none`. One tier.

**Expectation #2 (exactly two tier changes, this pair): HIT. Expectation #3 (ASML ≈ 0.3817813806, AMAT ≈ 0.1347260127 to Pass T precision): HIT** — engine values match the reviewer arithmetic byte-for-byte.

---

## U7 — Classifier behaviour under a non-uniform rescale

`build_severity_diff` sees the snapshot's `fixed_reference 1.6711…` and the current `2.5`, computes **rescale ratio = `0.6684557988`**, and flags a delta `RESCALE` when it matches `(ratio − 1) × severity_before` within `RESCALE_REL_TOL = 0.05`. The header **correctly flagged both** the `fixed_reference` change (with the ratio) **and** the boundary movement (critical/high/moderate all listed as moved). Summary: **13 non-zero deltas → 10 RESCALE, 3 STRUCTURAL; 2 tier changes, 0 BOUNDARY.**

The rescale is **not uniform**, and the classifier's handling of the three classes is:

- **Un-clamped outbound-dominant (10 nodes: KLA, Lam, AMAT, synopsys, cadence, tokyo_electron, siemens_eda, nikon, hitachi_high_tech, canon).** Severity scales by exactly `0.6684557988`, so the observed delta equals `(ratio − 1) × sev_before` to machine precision. The tolerance **absorbs** these cleanly → `RESCALE`. Correct.
- **Inbound-dominant (18 nodes).** Outbound scales down but inbound is unchanged and remains the max, so concentration and severity do not move; delta is exactly 0, cause blank. The classifier **correctly leaves them unflagged**. Correct.
- **Previously-clamped nodes — copper, ASML (both outbound-dominant after) — labelled `STRUCTURAL`.** This is the classifier **missing** the rescale. Because these nodes were clamped at `outbound_criticality = 1.0` before (not `raw/1.6711`), their before-severity did not use the ratio's denominator, so the naive `(ratio − 1) × sev_before` does not predict their delta (copper: expected `−0.2353`, actual `−0.1292`; ASML: expected `−0.1787`, actual `−0.1572`). The `RESCALE_REL_TOL = 0.05` tolerance is nowhere near wide enough to absorb the gap, so the classifier calls them `STRUCTURAL` — **a false structural label**, since no edge or node changed. The movement is entirely a `fixed_reference` effect (the clamp lifting), which `pass_u_facts.json` labels `clamp_release`.
- **TSMC — axis flip, labelled `STRUCTURAL`.** TSMC was outbound-clamped at 1.0 before (outbound-dominant); after, `raw/2.5 = 0.857…` drops **below** its inbound HHI `0.99009975`, so the **dominant axis flips outbound → inbound** and severity becomes `inbound × coef = 0.46463597789024974`. The delta is tiny (`−0.0046`) precisely because the new inbound-driven concentration (0.990) is close to the old clamped 1.0. Neither pure rescale nor pure structure; the classifier labels it `STRUCTURAL`.

**Assessment (recorded, not fixed).** O.6.4 already logged that `RESCALE_REL_TOL`'s stated justification is unsound. Pass U is its first real stress, and the finding is concrete: the tolerance is not the problem — **the classifier's rescale model has no notion of clamping.** It assumes every outbound-dominant node's severity is `raw/FR × coef`, which is false for any node that was clamped in the snapshot. The three false `STRUCTURAL` labels are exactly the pre-U clamped set `{copper, ASML, TSMC}`. Per §5 / §7, the tolerance was **not** changed; this is the record of what it did. A future fix would teach the classifier to reconstruct `raw` from the snapshot (the snapshot already stores `outbound_criticality`, but clamped values lose `raw`; it would need `raw` captured too) — noted as an open item, not actioned here.

---

## U8 — Guard gap (§4)

**Were the repo config and the fixture in sync at open?** Yes. `pass_u_facts.json.guard_sync.at_open` reads both files at `1dbdd46`: `config_fixed_reference = 1.6711394969476698`, `fixture_fixed_reference = 1.6711394969476698`, `in_sync = true`. **Expectation #10: HIT** — the §4 gap had not yet bitten; the two files had been kept in sync by hand.

**The gap.** `test_thresholds_frozen.py::_load_config_thresholds` reads `REPO/config/scoring.yaml` (the committed config), but `test_unscored.py::test_fixed_reference_is_frozen` read `FIX/scoring.yaml` (the fixture). So since Pass K.1, the `fixed_reference` freeze guarded only the fixture; a drift in the real config with the fixture untouched would have stayed green. Three tests close it (all in `test_unscored.py`):

1. **`test_config_fixed_reference_is_frozen`** — reads `config/scoring.yaml` directly and asserts its `fixed_reference` equals `_FROZEN_FIXED_REFERENCE`. The committed config is now guarded, not only the fixture.
2. **`test_config_and_fixture_fixed_reference_agree`** — asserts the repo config and the fixture carry the same `fixed_reference`. The hand-sync is now a checked invariant, reported against the constant by name (distinct from the whole-file `test_fixtures_and_data_are_content_identical`).
3. **`test_guard_actually_fails_when_fixed_reference_drifts`** — proof-of-guard. The assertion was extracted into `_assert_fixed_reference_frozen(ref)`; the test feeds it `_FROZEN_FIXED_REFERENCE + 1e-9` and asserts it raises, naming `fixed_reference` and the `spec` requirement. The boundaries guard has had this proof since Pass P (`_assert_frozen`); the `fixed_reference` guard never did until Pass U.

**Proof-of-guard fires, quoted.** Feeding `2.500000001`:

> ``` `fixed_reference` moved from the frozen literal 2.5 to 2.500000001. If the change is authorized by a spec, update _FROZEN_FIXED_REFERENCE in the same commit and cite the spec. Do not update the constant alone — the defect this test catches is silent drift, not the value itself. ```

**At close** (`guard_sync.at_close`): config and fixture `fixed_reference` both `2.5` (`in_sync = true`), boundaries in sync (`boundaries_in_sync = true`), and the two files are byte-identical (`files_byte_identical = true`).

---

## U9 — Boundary-proximity readout after the change

Post-change, the nodes closest to any boundary (from `pass_u_facts.json.boundary_proximity` and the cluster-cut section of `threshold_analysis.md`), within one median gap (`0.01462`) or just beyond:

| node | severity | tier | nearest boundary | distance |
|---|---:|---|---|---:|
| company:applied_materials | 0.1347260127 | none | moderate (0.1566844355) above | +0.0219584227 |
| company:kla | 0.1786428582 | moderate | moderate (0.1566844355) below | +0.0219584227 |
| company:lam_research | 0.1815729487 | moderate | moderate (0.1566844355) below | +0.0248885133 |

The moderate boundary now sits symmetrically between **AMAT** (just demoted to `none`, `0.0219584227` below) and **KLA** (`0.0219584227` above) — they are exactly equidistant. **KLA and Lam Research are the two scored nodes nearest a boundary from the safe side**: they hold `moderate` with margins of `+0.0219584227` and `+0.0248885133` respectively. They are the next nodes at risk under any future downward movement, and AMAT is the first node that would return to `moderate` under any upward movement. No boundary sits inside a tight cluster: the critical and high boundaries clear their nearest neighbours by `0.0371` and `0.0414` (both ≥ the `0.01462` median gap); the moderate boundary clears by `0.0220`. This is the map the next pass inherits.

---

## U10 — What this does and does not settle

- **The drift diagnostic reading 0 would-change-tier is definitionally true and proves nothing about fit.** `threshold_analysis.md` reports per-boundary drift of `+0.0000000000` on all three boundaries and "**0 nodes would change tier**," with the verdict "a re-baseline would produce identical tiers today." This is entailed by the setup: the frozen boundaries were **set equal to** the FR-C derivation at ship time, so frozen = derived by construction. It is not validation. It becomes informative only when the graph next moves and the derived boundaries drift away from the frozen literals. (This is the same K.2.2 §6.2 pattern the Pass T addendum flagged in Q8 — a measurement whose outcome is entailed by how it is set up. The addendum's replacement watch condition, below, is deliberately not of that shape.)

**Open items carried forward:**
- **Five misclassified cost-basis edges (S.0.1)** — still open; untouched by Pass U.
- **`bottleneck_type` on copper (R.1.3)** — still open.
- **The scale axis** — the model still has no demand/scale axis; open.
- **`RESCALE_REL_TOL` (O.6.4)** — Pass U stressed it and recorded the result (U7): the tolerance is not the defect; the diff classifier has no notion of clamping, so it mislabels the pre-U clamped set `{copper, ASML, TSMC}` as `STRUCTURAL`. Not fixed here.
- **The FR-B flip test adopted in the Pass T addendum no longer applies**, because FR-B was not shipped. That test watched whether a future pass pushed raw outbound above copper's `2.0447548854281186` (which, under FR-B where `fixed_reference = max(raw)`, would have proven FR-B was tracking the max on a lag). Under FR-C, `fixed_reference = 2.5` is a declared constant with `2.5 − 2.0448 = 0.4553` of headroom, so the question is not "did the max change" but **"did the graph's max raw outbound rise above 2.5, re-introducing a clamp?"**

  **FR-C-appropriate watch condition (adopted):** *After FR-C ships, does any future pass's authoring push a node's raw outbound above `2.5`?* If yes, a node re-clamps, the headroom is exhausted, and the re-baseline question reopens (with the honest options being either a larger headroom constant or accepting a clamp). This is falsifiable — it can return `yes` (a future re-authoring of a high-fan-out chain, e.g. into TSMC's downstream, could lift a raw outbound past 2.5) or `no` (raws stay below 2.5 for several passes and FR-C holds as a genuine headroom anchor). Copper's raw at `2.0448` gives the current margin: `0.4553`.

---

## U11 — Scorecard

| # | expectation | verdict | evidence |
|---|---|---|---|
| 1 | FR-C derivation reproduces the three boundary literals byte-identically post-change | **HIT** | `derivation_reproduction.reproduces = true`; byte-identical to committed config AND to Pass T's measurement (U4) |
| 2 | Exactly two scored nodes change tier: ASML critical→moderate, AMAT moderate→none | **HIT** | `tier_changes` = `[applied_materials moderate→none, asml critical→moderate]`; no other node moved (U5, U6) |
| 3 | ASML ≈ 0.3817813806 and AMAT ≈ 0.1347260127, both to Pass T precision | **HIT** | engine: ASML `0.38178138064859357`, AMAT `0.1347260127406829` (U6) |
| 4 | TSMC dominant axis flips outbound → inbound; severity 0.4692819869 → 0.4646359779; tier holds | **HIT** | `dominant_axis_before=outbound, after=inbound`; sev `0.46463597789024974`; tier `high→high` (U5) |
| 5 | Copper stays `critical`; dysprosium, gallium, NVIDIA severities byte-identical | **HIT** | copper `critical→critical` (`0.5804716175`); dys/gal/nvidia deltas exactly 0 (U5) |
| 6 | Clamped set is empty; copper normalized = 0.8179019542 | **HIT** | `clamp_check.clamped_after = []`; `copper_normalized_after = 0.8179019541712474` |
| 7 | Tier histogram = 2 / 2 / 16 / 11 / 41 | **HIT** | `tier_histogram_after = {critical 2, high 2, moderate 16, none 11, unscored 41}` |
| 8 | Drift diagnostic reports 0 would-change-tier at close | **HIT (uninformative by construction)** | `threshold_analysis.md`: per-boundary drift +0.0 on all three; "0 nodes would change tier." Definitionally true since frozen = derived at ship (U10) |
| 9 | Both proof-of-guard tests still fail for the right reason after the literals move | **HIT** | boundaries: "…moderate drifted from the Pass P frozen literal…"; mode: "must be 'frozen'…"; fixed_reference: "…moved from the frozen literal 2.5 to 2.500000001…" (U8) |
| 10 | config and fixture were in sync on `fixed_reference` at open | **HIT** | `guard_sync.at_open.in_sync = true` (both `1.6711…`) (U8) |

Grades 2–7 and 10 are the reviewer's arithmetic, graded strictly against the engine. All HIT. On the one value not held to a strict pre-registration — copper's exact post-change severity — the reviewer's `0.5804720000` was a rounded estimate; the engine value is `0.5804716174555709` (difference ~`4e-7`, below the reviewer's stated precision). The pre-registration was "copper stays critical," which holds.

---

## U12 — Standard sections

### Guards changed (non-empty for the first time since R.1)

- **`backend/tests/test_thresholds_frozen.py::FROZEN_BOUNDARIES`** → FR-C triple (`critical 0.5247316525037853`, `high 0.42320867926942163`, `moderate 0.15668443545638666`), with a comment naming Pass U as the authorizing spec and Pass T's measurement as the derivation source. The two proof-of-guard tests (`test_guard_actually_fails_when_a_literal_is_altered`, `test_guard_actually_fails_when_mode_is_derived`) operate on in-memory dicts and needed no change; both confirmed still passing and still failing for the right reason.
- **`backend/tests/test_unscored.py::_FROZEN_FIXED_REFERENCE`** → `2.5`, with a comment naming Pass U and the FR-C reasoning and noting the first invocation of the docstring's authorized-change clause.
- **`test_top_outbound_anchor_is_expected_node` needed no change.** It computes `_outbound_criticality_raw` directly, and raw outbound is `fixed_reference`-independent; copper's raw is still `2.0448` (rank 1, no tie). Confirmed passing, unedited.
- New guard-gap tests (§4 / U8): `test_config_fixed_reference_is_frozen`, `test_config_and_fixture_fixed_reference_agree`, `test_guard_actually_fails_when_fixed_reference_drifts`.

### Changed

- `config/scoring.yaml` — four values + the `fixed_reference` comment block (U3).
- `backend/tests/fixtures/scoring.yaml` — synced byte-identical (§4 requires it; `test_fixtures_and_data_are_content_identical` enforces it).
- `backend/tests/test_thresholds_frozen.py`, `backend/tests/test_unscored.py` — guard literals + new guard tests.
- `docs/generated/node_inventory.md`, `threshold_analysis.md`, `severity_diff.md` — regenerated (`severity_diff.md` is the post-roll zero-diff against `pass_u_rebaseline`).
- `docs/generated/severity_snapshot.json` — rolled forward to `pass_u_rebaseline` (`fixed_reference 2.5`, FR-C boundaries).
- `backend/tests/_out/outbound_sensitivity.txt` — regenerated by `test_outbound_sensitivity_recorded`. The probe hypothetically removes the top-outbound node and renormalizes; copper's score reads `0.818` (was `1.000` clamped) and, under the FR-C boundaries, the probe now reports 3 tier shifts (copper, ASML, AMAT) instead of 1. A downstream consequence of the constant change; not scoring code, not an edge/node value.
- **New:** `backend/scripts/pass_u_measure.py`, `docs/generated/pass_u_facts.json`, `docs/generated/severity_diff_pass_u.md`, this report, and the `grading.md` Pass U section.

### Not changed

- No file under `data/` (no edge, node, or event value). No file under `backend/app/scoring/` or `backend/app/graph/` (no formula, aggregator, clamp logic, or code path). `thresholds.mode` stayed `frozen`. `separation_factor` stayed `3.0`. The aggregator stayed `noisy_or`. Verified against the diff scope (U1).

### Ledger — Pass U

- **FR-C shipped.** `fixed_reference` `1.6711394969476698 → 2.5` (declared-arbitrary headroom above copper's raw `2.0447548854281186`); boundaries re-derived at SF 3.0 to `0.5247316525037853 / 0.42320867926942163 / 0.15668443545638666`. Mode stayed `frozen`; `derived` never committed. First invocation of `test_fixed_reference_is_frozen`'s authorized-change clause.
- **Exactly two tier changes, both attributable to the constant, neither structural.** ASML critical → moderate (2 tiers, clamp release); applied_materials moderate → none (1 tier, clean rescale). All other movement is either inbound-unchanged (18 nodes) or clean rescale by `0.6684557988` (10 nodes). Zero unexplained deltas.
- **Clamped set emptied** (was `{copper, ASML, TSMC}`); copper normalized `0.8179019542`. TSMC's dominant axis flipped outbound → inbound.
- **§4 guard gap closed.** The `fixed_reference` freeze had guarded only the fixture since Pass K.1; three new tests now guard the committed config directly, check config↔fixture sync, and prove the guard fails on a drifted value. Config and fixture were in sync at open.
- **`RESCALE_REL_TOL` stressed, not fixed (O.6.4).** The diff classifier mislabels the pre-U clamped set `{copper, ASML, TSMC}` as `STRUCTURAL` because its rescale model has no notion of clamping. Recorded; unchanged.
- **FR-B flip test retired** (FR-B not shipped). Replaced by the FR-C watch condition: *does any future pass push a node's raw outbound above `2.5`, re-introducing a clamp?* Current headroom: `2.5 − 2.0448 = 0.4553`.
- **Suite:** 120 passed, 1 skipped, 0 xfail — both invocations (`python -m pytest` and bare `pytest`). Was 117 + 3 new §4 guard tests. The 1 skip is `test_config_boundaries_equal_derivation` (asserted only under `mode: derived`).
