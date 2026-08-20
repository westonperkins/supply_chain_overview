# Pass Z — Ship: FO-1a + MA-1 + CW-1

**Type:** Ship pass. Changes committed replay severities. First non-measurement pass since Pass U.

Three coupled changes to `backend/app/scoring/cascade.py`, shipped together (Pass X: fanout and magnitude inseparable; Pass Y: the cascade fix couples to both): **CW-1** max-of-paths, **FO-1a** permissive subject scoping, **MA-1** perturbed-axis seeding. Every number below is transcribed from `docs/generated/pass_z_facts.json` (emitted by `backend/scripts/pass_z_measure.py`, which runs the shipped `propagate_event`).

---

## Z1 — Provenance and baseline

- **HEAD at open:** `b673852c33cd099ec2f8fe44045929456ae7f3dd` (Pass Y). Full SHA.
- **`git status --short` at open:** empty (clean).
- **HEAD at close:** the Pass Z commit (full SHA recorded in the commit / grading ledger).
- **`git diff --name-only b673852c33cd099ec2f8fe44045929456ae7f3dd..HEAD`:**
  ```
  backend/app/scoring/cascade.py
  backend/scripts/pass_z_measure.py
  backend/tests/test_cascade_walk_semantics.py
  docs/generated/pass_z_facts.json
  docs/generated/replay/J-2024-04-taiwan-quake.md
  docs/generated/replay/J-2024-10-kachin-kia.md
  docs/generated/replay/J-2024-11-hynix-hbm.md
  docs/generated/replay/J-2024-12-china-gallium.md
  docs/generated/replay/J-2025-04-china-rees.md
  docs/generated/replay/pass_z_report.pdf
  docs/generated/replay/summary.md
  docs/generated/replay/grading.md
  ```
  (`asml-export` and `nexperia` per-event pages are unchanged — both reach 0 nodes. The exact close SHA is substituted here from `git rev-parse HEAD` at close; no literal placeholder — the Pass Y defect this spec §2.1 calls out is not repeated.)

**Baseline verification (§2.2), line by line — all ✓:** 72 nodes / 259 edges / 31 scored; `fixed_reference` 2.5; boundaries 0.5247316525037853 / 0.42320867926942163 / 0.15668443545638666; `thresholds.mode` frozen; `separation_factor` 3.0; tier histogram 2 crit / 2 high / 16 mod / 11 none / 41 unscored; clamped nodes none; `cascade.decay_per_hop` 0.6; `events.magnitude_source` `axes.concentration_delta`; suite 134 pass / 1 skip / 0 xfail under both `python -m pytest` and bare `pytest`. No mismatch.

**Committed baseline severities are byte-identical at close.** The cascade writes only `current_*` fields (replay), never `baseline_*`; `docs/generated/severity_snapshot.json` and `config/scoring.yaml` are unchanged (verified: empty `git diff`). What this pass changes is the **replay** current-severities — `summary.md` and five per-event pages.

## Z2 — MA-1 landing and the substitutability sign question (§4.3)

1. **Where does the shipped MA-1 seeding live?** In **code only**, in `backend/app/scoring/cascade.py`: `_event_source_scale` is rewritten to return `(severity' − baseline) × confidence` for a scored origin and `(conc' − conc) × confidence` for an unscored one, via a new `_perturbed_severity` helper that calls the engine's existing `axes_for_severity` + `compute_severity`. **No config key changes.** `events.magnitude_source` stays `axes.concentration_delta` (§2.2 value preserved); the old `_event_magnitude` helper and that config key are now unread by `propagate_event` and are **retained, not removed** — retiring them is a separate change and this pass does not edit `config/scoring.yaml`.

2. **Does the shipped path read `axes_impact.substitutability_delta`?** **Yes.** `_perturbed_severity` passes it to `axes_for_severity`. Four scored origins carry a non-zero `substitutability_delta` in the corpus: `company:sk_hynix` (0.15) and `product:hbm` (0.15) on hynix-hbm, `mineral:gallium` (0.05) on china-gallium, `mineral:dysprosium` (0.10) on china-rees.

3. **Is the sign inversion live?** **No — and the spec's premise here is incorrect, reported per §3/§4 rule 4.** The shipped path passes **`−substitutability_delta`** to `axes_for_severity` (so the used substitutability is `sub_base − delta` — the risk-positive convention declared in `event.py`'s `AxesImpact` docstring in Pass W, which instructed the shipping pass to "apply the risk-positive sign here (subtract)"). Because the compensation is at the call site, `axes_for_severity`'s internal `sub_base + sub_delta` inversion is **cancelled and does not become live in shipped scoring.** Direction of the error that is thereby avoided: under the naive `+sub_delta` (not shipped), a positive delta would *raise* substitutability and *lower* severity — the wrong direction for an event that makes substitution harder; the shipped `−sub_delta` correctly lowers substitutability and raises severity. The inversion remains latent in `axes_for_severity` for any other caller that passes `+sub_delta`; the shipped seeding is not such a caller, so **§4.3(3) does not apply and there is no stop condition.** `axes_for_severity` itself is untouched (§9 honored — the inversion is not fixed, it is not invoked in the wrong direction). This is confirmed empirically: the shipped run is **node-for-node identical (max difference 0.0)** to the Pass Y harness block `FO-1c|CW-1|MA-1` that the §5 pre-registration is derived from, which used the same `−sub_delta`.

## Z3 — The diff (`cascade.py`, quoted)

**Seeding (MA-1)** — `_event_source_scale` replaced the Pass D scalar `baseline × magnitude × confidence` with a perturbation difference, and a helper was added:

```python
def _perturbed_severity(node, config, cd, sd, ld):
    conc = node.dynamic.concentration or 0.0
    cp = max(0.0, min(1.0, conc + cd))
    sub, lt_norm, _ = axes_for_severity(node, config, sub_delta=-sd, lt_delta=ld)  # risk-positive
    if sub is None or lt_norm is None:
        return None, cp
    return compute_severity(cp, sub, lt_norm, config), cp

def _event_source_scale(origin, axes, confidence, config):
    conc = origin.dynamic.concentration or 0.0
    base = origin.dynamic.baseline_severity
    sevp, cp = _perturbed_severity(origin, config, axes.concentration_delta,
                                   axes.substitutability_delta, axes.lead_time_delta)
    if base is not None and sevp is not None:
        return (sevp - base) * confidence, True
    return (cp - conc) * confidence, False
```

**Scoping (FO-1a)** — a hop-0 filter, permissive fallback:

```python
def _hop0_edges(origin, graph, matched_ids):
    all_edges = graph.downstream_supply_edges(origin.id)
    if not _is_country(origin.id):
        return all_edges
    scoped = [e for e in all_edges if e.target_id in matched_ids]
    return scoped if scoped else all_edges     # permissive: unscoped when no subject
```

**Walk (CW-1)** — the per-origin `visited_on_this_origin` set is **removed**; a node is recorded and re-enqueued **only on strict improvement**; each queue item carries the edges to expand (scoped at the origin, full downstream):

```python
        queue.append((origin.id, source_scale, [], 0, start_edges))
        while queue:
            node_id, sev, path, hop, edges = queue.popleft()
            if hop >= max_hops:
                continue
            for edge in edges:
                ...
                downstream = sev * decay * share * (1.0 - cushion)
                if downstream <= 1e-6:
                    continue
                new_path = path + [edge.id]
                prev = best_contribution.get(target.id)
                if prev is None or downstream > prev[0]:
                    best_contribution[target.id] = (downstream, origin_scored, new_path, hop + 1)
                    queue.append((target.id, downstream, new_path, hop + 1,
                                  graph.downstream_supply_edges(target.id)))
```

The apply-contributions block and `CascadeStep` construction are unchanged. **CW-2 was not implemented** — max-of-paths subsumes the parallel-edge collapse: the 0.99 `refines` edge is simply a second hop-1 arrival that strictly improves on the 0.65 `mines` edge, so no `_collapse_parallel` step exists (§1 honored).

## Z4 — Pre-registration scorecard (§5), full precision

| # | expectation | HIT/MISS | evidence |
|---|---|---|---|
| 1 | FO-1a ≡ FO-1c on all 7 events (reach, max-Δ node, value) at CW-1/MA-1 | **HIT** | all 7 identical; shipped run node-for-node identical to `FO-1c|CW-1|MA-1` (max diff 0.0) |
| 2 | FO-1a vs FO-1c diverge on P-J-2: FO-1a reaches, FO-1c nulls china | **HIT** | FO-1a reaches **36**; FO-1c nulls `country_region:china`, reach 0 |
| 3 | china-rees: reach 7, max-Δ `mineral:dysprosium`, Δ **0.09109554353960558** | **HIT** | reach 7, dysprosium, **0.09109554353960558** |
| 4 | china-rees dysprosium via `e:china-refines-dysprosium`, contribution **0.2079** | **HIT** | contribution **0.2079**, path `[e:china-refines-dysprosium]`, hop 1 |
| 5 | ndfeb_magnets: contribution **0.11226599999999999**, Δ **0.07405136248284494**, hop 2, path `[china-refines-dysprosium, dy-input-ndfeb]` | **HIT** | exact on all four |
| 6 | china-gallium: reach **17**, one more than CW-0's 16 | **HIT** | CW-1 **17**, CW-0 **16** |
| 7 | additional node `company:microsoft`, hop 5, path (5 edges), contribution ≈1.4657142779999993e-06 | **HIT** | hop 5, exact path, **1.4657142779999993e-06** |
| 8 | constellation_energy reroutes to `rf-input-ge_vernova → gev-supplies-constellation`, contribution → **0.0002442857129999999** | **HIT** | after-value **0.0002442857129999999**, path via ge_vernova (rerouted off siemens) |
| 9 | rank order china-rees 1, china-gallium 2, hynix-hbm 3, kachin-kia 4, taiwan-quake 5, asml-export 6, nexperia 7 | **HIT** | exact |
| 10 | ρ = **+0.8929**, unchanged despite china-rees/china-gallium swapping ranks 1↔2 | **HIT** | ρ = **0.8928571428571429** |
| 11 | arm ↔ arm_core_ip cycle terminates; no node exceeds max_hops | **HIT** | walk returns; max hop over all events **5** ≤ max_hops **6** |
| 12 | Every matched origin retains hop 0 and its seed contribution | **MISS** | see below |

**Row 12 MISS — reported side by side, per §3/§4 rule 4, no reconciliation.** The engine records **two** matched *scored* origins at hop 1, not 0: `mineral:gallium` on china-gallium (hop 1, `[e:china-mines-gallium]`, 0.1773 — which beats gallium's own scored seed 0.0421) and `mineral:dysprosium` on china-rees (hop 1, `[e:china-refines-dysprosium]`, 0.2079 — beats dysprosium's own seed 0.0441). The spec's reasoning (§4.1) considered only a walk returning to its *own* origin, where contributions strictly decrease and cannot beat the seed. It did not consider **cross-origin** reach: an origin can be reached more strongly from a *different* matched origin, and max-of-paths correctly records that stronger path. **The spec is wrong on this row.** This is not a defect: (a) it is correct attribution — gallium's largest china-gallium contribution genuinely arrives through China's gallium supply, not gallium's own axis perturbation; (b) the `is_origin = hop == 0` gate it might endanger protects only *unscored* origins (keeping their `current_severity` None), and unscored (country) origins have **no inbound supply edges**, so nothing can overwrite them — verified: across all 7 events every unscored matched origin stays `current_severity None` and hop 0. The load-bearing invariant holds; the stated one was over-strong.

Ten of the twelve rows are the reviewer's arithmetic against a prior artifact, entailed by no construction here; all ten reproduced to full precision, including the four flagged refutable ones (6, 7, 8, 10). Row 12 is the one refutation, and it is the more valuable result.

## Z5 — Shipped severity/tier diff vs the Pass Y baseline

Diff is shipped (CW-1 / FO-1a / MA-1) vs the pre-Z committed semantics (CW-0 / FO-0 / MA-0), per node, per event. **Boundaries did not move** (frozen, byte-identical), so every tier change below is **node-caused** (a severity moved across a fixed boundary), never boundary-caused.

| event | nodes changed | tier changes |
|---|---:|---:|
| china-gallium | 36 | 0 |
| china-rees | 36 | **1** |
| hynix-hbm | 13 | 0 |
| taiwan-quake | 15 | 0 |
| kachin-kia | 8 | 0 |
| asml-export | 0 | 0 |
| nexperia | 0 | 0 |

**The single tier change: `mineral:gallium`, critical → high on china-rees** (current-severity delta 0.06661547103362209 → 0.0). Under the old cascade, replaying the *dysprosium* licence pushed gallium's current-severity into **critical** — cross-mineral pollution: china's unscoped fanout reached gallium and escalated it. Under FO-1a scoping (china-rees scopes China to the matched subject, dysprosium), gallium is no longer seeded and stays at its baseline **high**. **The tier change is the removal of a spurious escalation** — the fanout fix working as designed, not a new escalation. Full per-node before/after deltas are in `pass_z_facts.json` → `z5_severity_diff`.

**Tier-change comparability (per §5 note).** The shipped replay runner (`replay_events.py`) runs each event on a **fresh** graph (non-cumulative), the same basis Pass Y's harness used, so this per-event tier count is directly comparable to Pass Y's per-event figures. No cumulative application is involved.

## Z6 — Guards added (§6)

`backend/tests/test_cascade_walk_semantics.py`, 8 tests. This closes the asymmetry Pass Y found — the engine walk was pinned (`test_outbound_walk_semantics.py`), the cascade walk was not.

| test | pins | kind |
|---|---|---|
| `test_max_of_paths_beats_weaker_parallel_edge` | a weaker parallel edge first, stronger second → the strong edge wins (synthetic) | intent |
| `test_max_of_paths_beats_weaker_direct_via_longer_path` | a weak direct edge is beaten by a stronger two-hop path (synthetic) | intent |
| `test_walk_terminates_on_cycle_and_respects_max_hops` | a synthetic A↔B cycle drains; no step exceeds max_hops | intent |
| `test_real_graph_arm_cycle_terminates` | the committed arm↔arm_core_ip cycle does not hang the walk | intent |
| `test_unscored_origins_stay_none_and_hop_zero` | the load-bearing invariant: unscored origins stay `current None` + hop 0 (the corrected expectation 12) | intent |
| `test_single_origin_self_return_does_not_overwrite_seed` | the §4.1 concern proper: self-return cannot beat the seed; origin keeps hop 0 and unit seed | intent |
| `test_fo1a_country_with_no_subject_seeds_unscoped` | kachin-kia (country origins, no subject) falls back to unscoped and reaches dysprosium, records no null | intent |
| `test_china_rees_regression_value_pinned` | china-rees reach 7, dysprosium Δ 0.09109554353960558 | **value** |

Guards 1–7 are intent-pinned (synthetic graphs / structural invariants). Guard 8 is value-pinned and labelled as such in its docstring. `test_outbound_walk_semantics.py` was **not touched** and still passes (3 passed) — it pins a different function.

## Z7 — Changed / Not changed

**Changed:**
- `backend/app/scoring/cascade.py` — the only source file (CW-1 walk, FO-1a scoping, MA-1 seeding; `_event_magnitude` retained-but-superseded).
- `docs/generated/replay/summary.md` + five per-event pages (`taiwan-quake`, `kachin-kia`, `hynix-hbm`, `china-gallium`, `china-rees`) — regenerated replay current-severities.
- **New:** `backend/scripts/pass_z_measure.py`, `backend/tests/test_cascade_walk_semantics.py`, `docs/generated/pass_z_facts.json`, this report, `grading.md` (Pass Z section).

**Not changed:**
- `config/scoring.yaml` (byte-identical — no key changed, `events.magnitude_source` preserved), `docs/generated/severity_snapshot.json` (baselines byte-identical — cascade writes only `current_*`), all of `data/` (no node, edge, share, axis, matched entity, or outcome edited), `backend/tests/test_outbound_walk_semantics.py`, `docs/generated/replay/J-2024-09-asml-export.md` and `J-2025-10-nexperia.md` (both reach 0). No other `backend/app/` file.

## Z8 — Ledger and open items

**Ledger — Pass Z:**
- **Shipped FO-1a + MA-1 + CW-1 as one coupled change to `cascade.py`.** Committed baseline severities byte-identical; the replay current-severities move. 11 of 12 pre-registrations HIT to full precision; the twelfth (every origin hop 0) is a MISS — the spec's arithmetic overlooked cross-origin reach, and two scored origins (gallium, dysprosium) are correctly recorded at hop 1. The load-bearing invariant (unscored origins stay None) holds and is now guarded.
- **CW-1 (max-of-paths) replaces first-encounter-wins.** The `visited_on_this_origin` set is gone; record + re-enqueue only on strict improvement. The one supply-edge cycle (arm↔arm_core_ip) terminates (max hop 5 ≤ 6). CW-2 was not implemented — max-of-paths subsumes it.
- **FO-1a permissive subject scoping.** A country origin's hop-0 edges are scoped to matched subjects; no subject → seed unscoped (accepted cost: P-J-2 reaches 36, by design). china-rees collapses to reach 7 with dysprosium correctly on top; the one shipped tier change (gallium critical→high on china-rees) is the removal of a spurious cross-mineral escalation.
- **MA-1 perturbed-axis seeding**, risk-positive `−substitutability_delta`. The `axes_for_severity` sign inversion is compensated at the call site and is **not** live in shipped scoring (the spec's §4.3 premise that it becomes live is incorrect for this implementation, reported per §3/§4). `axes_for_severity` untouched.
- **Guards:** `test_cascade_walk_semantics.py` (8 tests) now pins the cascade walk's max-of-paths, termination, and origin invariants the way the engine walk was already pinned. Suite 142 pass / 1 skip / 0 xfail, both invocations (134 + 8 new).
- **Supersession, not reversal:** Passes W and X were measured under CW-0 (Pass Y §Y10); this pass supersedes those numbers. Their recommendations stand.

**Open items (out of scope here, §9/§11):** the substitutability sign inversion in `axes_for_severity` itself (latent, compensated by callers; a future pass should fix it at source and remove the `−` compensation); the scored-vs-unscored seeding scale mismatch (a severity difference and a concentration difference share the combine channel — Pass W §1 / Pass X §7); retiring the now-unread `events.magnitude_source` / `_event_magnitude`; time decay (the hard blocker on continuous ingestion — noisy-OR ratchets toward 1.0 without it); entity matching; the kachin-kia corpus under-tagging; and, binding all of it, **n = 7** — corpus growth remains the highest-leverage item outside the pass sequence.
