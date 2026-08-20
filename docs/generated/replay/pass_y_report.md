# Pass Y — Cascade Walk Semantics and FO-1c

**Type:** Measurement pass. **Ships nothing.** Two findings from the Pass X verdict, neither previously measured: the cascade BFS resolves multi-path arrivals by first encounter, not strength (§4); and FO-1c, an unmeasured fanout variant (§5).

All candidates run in-process in `backend/scripts/pass_y_measure.py`. Numbers below are transcribed from `docs/generated/pass_y_facts.json`. **Weston decides.**

---

## Provenance

- **HEAD at open:** `d0a09a4e4c1533cee05a129b6348526d881fedf4` (Pass X). No stated SHA was supplied at handoff; opened on the current HEAD, which is the Pass X commit — the natural predecessor — with a clean tree, and recorded here per §2.
- **`git status --short` at open:** empty (clean).
- **`git diff --name-only` at open:** empty.
- **HEAD at close:** the Pass Y commit.
- **`git diff --name-only <PassX>..HEAD`:**
  ```
  backend/scripts/pass_y_measure.py            (new; in-process harness)
  docs/generated/cascade_fanout_candidates.md  (new; generated)
  docs/generated/pass_y_facts.json             (new; generated)
  docs/generated/replay/pass_y_report.pdf      (new)
  docs/generated/replay/grading.md             (Pass Y section)
  ```

## Baseline verification (§2.1, line by line)

| item | expected | observed | ✓ |
|---|---|---|---|
| Graph | 72 / 259 / 31 | 72 nodes, 259 edges, 31 scored | ✓ |
| `fixed_reference` | 2.5 | 2.5 | ✓ |
| Boundaries | 0.5247…/0.4232…/0.1567… | identical | ✓ |
| `thresholds.mode` | frozen | frozen | ✓ |
| `separation_factor` | 3.0 | 3.0 | ✓ |
| Tier histogram | 2/2/16/11/41 | 2 crit / 2 high / 16 mod / 11 none / 41 unscored | ✓ |
| Clamped nodes | none | none | ✓ |
| `cascade.decay_per_hop` | 0.6 | 0.6 | ✓ |
| `events.magnitude_source` | axes.concentration_delta | axes.concentration_delta | ✓ |
| Suite | 134/1/0 both invocations | 134 passed, 1 skipped, both | ✓ |

No mismatch. Proceeded.

---

## Y1 — Provenance and baseline

Answered above. HEAD `d0a09a4` at open (clean); §2.1 table verified line by line, all ✓; suite 134 pass / 1 skip / 0 xfail under both `python -m pytest` and bare `pytest`.

## Y2 — Edge iteration order

`graph.downstream_supply_edges("country_region:china")` in returned order:

| # | edge id | type | target | input_share | resolved |
|---:|---|---|---|---:|---:|
| 1 | e:china-mines-gallium | mines | gallium | 0.985 | 0.985 |
| 2 | e:china-refines-gallium | refines | gallium | 0.60 | 0.60 |
| 3 | e:china-mines-dysprosium | mines | dysprosium | 0.65 | 0.65 |
| 4 | e:china-refines-dysprosium | refines | dysprosium | 0.99 | 0.99 |
| 5 | e:china-mines-neodymium | mines | neodymium | 0.60 | 0.60 |
| 6 | e:china-refines-neodymium | refines | neodymium | 0.90 | 0.90 |
| 7 | e:china-mines-indium | mines | indium | 0.30 | 0.30 |
| 8 | e:china-refines-indium | refines | indium | 0.58 | 0.58 |
| 9 | e:china-mines-copper | mines | copper | 0.10 | 0.10 |
| 10 | e:china-refines-copper | refines | copper | 0.47 | 0.47 |

**Returned order equals `edges.json` array order — proven two ways.** From the code: `_reindex` iterates `self.edges.values()` (a dict populated in `edges.json` array order by `from_dir`) and appends edge ids to `_out[source_id]`; `out_edges` reads `_out[node_id]` and filters by type **without reordering**. Empirically: the returned edge-id list equals the `edges.json`-filtered list for `country_region:china` exactly (`china returned == file order: True`). **The §4.4 copper row is confirmed** — mines (0.10) precedes refines (0.47); CW-0 takes 0.10 and skips 0.47, ratio 4.70.

## Y3 — Full parallel-edge census

The graph has **31** `(source, target)` pairs with ≥2 supply edges; **9 carry a nonzero loss** under CW-0's first-encounter rule (**18 edges** in lossy pairs). The defect is **not confined to China** — the handoff named only country hop-0 edges, but the census finds a company case too (`hitachi_high_tech`):

| source → target | takes | share | max | ratio |
|---|---|---:|---:|---:|
| country_region:china → copper | mines | 0.1000 | 0.4700 | 4.700000 |
| country_region:china → dysprosium | mines | 0.6500 | 0.9900 | 1.523077 |
| country_region:china → indium | mines | 0.3000 | 0.5800 | 1.933333 |
| country_region:china → neodymium | mines | 0.6000 | 0.9000 | 1.500000 |
| country_region:japan → gallium | mines | 0.0100 | 0.1000 | 10.000000 |
| country_region:peru → copper | mines | 0.1100 | 0.1300 | 1.181818 |
| country_region:usa → copper | mines | 0.0600 | 0.1200 | 2.000000 |
| company:hitachi_high_tech → samsung | supplies (etch, 0.03) | 0.0300 | 0.0500 | 1.666667 |
| company:hitachi_high_tech → sk_hynix | supplies (etch, 0.03) | 0.0300 | 0.0500 | 1.666667 |

The remaining 22 multi-edge pairs are loss-free (the file-order-first edge already carries the max). **China–gallium is the only China pair where CW-0's choice equals the max** (0.985 mines precedes 0.60 refines) — Expectation #5: HIT.

## Y4 — Dysprosium both ways

`china-rees`, FO-0, MA-1, dysprosium's hop-1 contribution: **CW-0 = 0.136500** (China seed 0.35 × 0.6 × 0.65) → **CW-2 = 0.207900** (× 0.99), ratio **1.523077**, matching the pre-registered value exactly (Expectation #6: HIT). Under **FO-1b** the same holds: dysprosium's Δ is **0.059810 under both FO-0 and FO-1b at CW-0** — FO-1b scopes hop-0 to dysprosium's two edges but CW-0's first-encounter still takes the 0.65 mines edge and discards the 0.99 refines edge. **§4.5 confirmed: FO-1b does not escape the parallel-edge defect** (Expectation #8: HIT).

## Y5 — Blast radius (CW-0 → CW-2)

Across all 7 events, the parallel-edge fix changes contribution on the four China minerals whose mines edge is weaker than their refines edge (dysprosium ×1.523, neodymium ×1.500, indium ×1.933, copper ×4.700) **plus every node downstream of them** that CW-0 reached through the weaker edge. On `china-rees` + MA-1, the direct movers are dysprosium/neodymium/indium/copper; the **inherited** movers (changed only because a parent's contribution rose) include `product:ndfeb_magnets`, the RF/power chain, and the data-center facilities. `pass_y_facts.json` carries every node's before/after contribution, ratio, hop, and both paths. **Gallium is unchanged** (its mines edge already carries the max), which is why it remains a fixed reference point through the fix.

## Y6 — Attribution

`china-rees` max-Δ node, FO-0, by cascade × seeding:

| seeding | CW-0 | CW-2 | CW-1 |
|---|---|---|---|
| MA-0 | dysprosium ✓ | dysprosium ✓ | dysprosium ✓ |
| MA-1 | **gallium** ✗ | **neodymium** ✗ | **neodymium** ✗ |

Under MA-0 dysprosium is already on top and stays there. **Under MA-1 the cascade fix moves the max from one wrong mineral (gallium) to another wrong mineral (neodymium) — it does not restore the subject.** The §4.4b prediction is graded node by node at full precision and **HITs exactly**: after CW-2, `mineral:neodymium` takes the max at **0.133230** (predicted ≈0.133229), `mineral:indium` at **0.107203** overtakes gallium's **0.105983**, dysprosium rises to **0.091096** (predicted ≈0.091095) but **remains fourth**. So the reviewer's characterisation holds: indium overtaking gallium is unambiguous cross-mineral pollution; neodymium (itself a heavy REE) winning is "differently wrong," not obviously worse. **The decisive finding: CW-2 alone does not deliver `china-rees`'s attribution — the cascade fix and fanout scoping are coupled** (carried into Y14).

## Y7 — Is the defect confined to parallel edges?

**No.** CW-1 (full max-of-paths) and CW-2 (parallel-only) **diverge on 46 (node × event × seeding) instances** across `china-gallium` and `china-rees`. Two classes:

- **Parallel-adjacent (small):** e.g. `product:ndfeb_magnets` — CW-2 locks the dysprosium path (0.99 × 0.6 = contribution 0.112266) by popping dysprosium before neodymium; CW-1 finds the stronger neodymium path (0.90 × 0.6 → 0.113400). Margin **1.01%** (Expectation #11: HIT, full precision).
- **Longer-path suppression (large):** the defect the handoff's parallel-edge framing misses. `product:hbm` on `china-rees`+MA-1 — CW-2 reaches it via a weak `indium → samsung → hbm` path (0.000075) marked visited first; CW-1 finds `copper → sk_hynix → hbm` (0.010127), a **135×** difference. `product:cowos_packaging` diverges **325×** (weak `indium→samsung→cowos` vs strong `copper→tsmc→cowos`); `company:samsung` **25.7×** (indium vs copper). CW-0/CW-2 marked these nodes visited via a weak early path, permanently blocking the strong later one.

**What this rules out:** the parallel-edge fix (CW-2) is *not* the whole fix. First-encounter-wins suppresses both weaker parallel edges *and* stronger longer paths; only CW-1 addresses both.

## Y8 — Intentional or accident?

**Refutable reviewer claim, adjudicated on the record.**

**The case FOR the current semantics.** The supply-edge subgraph contains a cycle (`company:arm → product:arm_core_ip → company:arm`, Y9). A per-origin `visited` set is a legitimate **termination / cycle-protection** mechanism, and first-hop-wins could in principle be a deliberate per-origin dilution control (each origin's influence spreads once, not repeatedly).

**Whether it survives.** It does not survive as *intended-and-correct*. `propagate_event`'s own docstring states: *"each downstream node's contribution is the **BEST (max) path** from any origin (existing behaviour)."* **The code does not deliver that** — the `visited` check precedes the `downstream > prev[0]` comparison and `visited_on_this_origin` is never cleared, so within a single origin's walk the max comparison can never fire; it fires only *across* origins. The docstring documents max-of-paths; the code implements first-encounter-within-origin. That gap is the signature of an **unintended side effect**, not a design: the author wrote down max-path semantics and the visited set silently defeated them. Reinforcing this, `engine._outbound_criticality_raw` implements genuine max-of-paths (no visited, re-enqueue on strict improvement) and is pinned by `test_outbound_walk_semantics.py` since Pass T — the same author knew the correct shape and used it there. **Verdict:** the `visited` set serves a real purpose (termination) via the wrong mechanism (discard-all-revisits), and its first-encounter-wins behaviour is contradicted by the function's own contract. Not intentional-and-correct; a termination guard with an unintended attribution defect. `cascade.py`'s last substantive walk change was the Pass D rewrite (`70ba9e6`); the semantics have not been revisited since.

## Y9 — Termination and cost

**Cycles:** exactly one supply-edge cycle in the AI graph — `company:arm ↔ product:arm_core_ip` (a 2-cycle; reachable from copper via TSMC→arm). Proven by DFS three-colouring, not assumed. **CW-1's bound:** `max_hops = 6`, plus re-enqueue only on strict improvement, plus the `downstream ≤ 1e-6` floor — each cycle traversal multiplies by `decay × share < 1`, so values strictly decrease and the queue drains. **Cost:** on the full 7-event replay (avg of 20 runs) CW-0 = 43.8 ms, CW-2 = 44.2 ms, **CW-1 = 42.6 ms** — CW-1 is **not** more expensive; strict-improve re-enqueue keeps the frontier small. The "CW-1 is expensive" concern is refuted on measurement.

## Y10 — Harness contamination

`pass_w_measure.py` (line 186 `visited = {origin.id}`, line 208 `visited.add(tgt.id)`) and `pass_x_measure.py` (lines 129, 150) both mark `visited` **unconditionally** after processing a node — i.e. both replicate **CW-0** (Expectation #10: HIT). **Therefore every published Pass W and Pass X number was measured under first-encounter-wins.** Effect on their conclusions:

- **Pass W (recommend MA-1 on semantic grounds):** the recommendation was explicitly semantic (recompute severity under perturbed axes), independent of walk semantics; it does **not** change. But its attribution numbers (china-rees→gallium under MA-1) are CW-0 artifacts, and under CW-2 the mis-attribution moves to neodymium — the coupling with fanout **deepens**, reinforcing (not reversing) Pass W's finding that MA-1 needs fanout scoping.
- **Pass X (recommend FO-1b on semantic grounds):** direction unchanged, but this pass supersedes FO-1b with FO-1c (Y13), and shows the cascade fix must ride along (Y14). No Pass X *recommendation* reverses; the specific china-rees reach/attribution numbers were CW-0.

**Neither prior recommendation changes. The numbers were CW-0 and are now labelled as such.**

## Y11 — FO-1c rule text

**Predicate (exact):** at hop 0, for a `country_region` origin, if the origin has **more than one distinct outbound-supply target**, apply FO-1b subject scoping (follow only edges whose target is in `entities_matched`; strict null if none); otherwise (**≤ 1 distinct target**) seed normally with the full unscoped edge set.

- **Distinct targets, not distinct edges** — the load-bearing choice, and it couples §5 to §4. `country_region:japan` has two edges into gallium (mines 0.01, refines 0.10) but **one distinct target** (gallium); counting edges would misclassify japan as multi-target on a single mineral. Worked: **japan** → distinct targets {gallium, indium} = 2 → **scoped**; **china** → {gallium, dysprosium, neodymium, indium, copper} = 5 → **scoped**; **kachin** → {dysprosium} = 1 → **seed normally**.
- **Zero-target countries** (taiwan, netherlands, germany reach nothing): the `>1` predicate is false, so they **seed normally** (reaching nothing either way). Stated explicitly; the behavioural difference is nil, but FO-1b would spuriously record a strict null for them (Y12 shows FO-1b nulling taiwan/netherlands) whereas FO-1c does not.

Classification of all 16 country nodes:

| seed normally (≤1 target) | scoped (>1 target) |
|---|---|
| australia (1), brazil (1), chile (1), drc (1), kachin (1), myanmar (1), peru (1) | canada (2), china (5), japan (2), malaysia (2), south_korea (2), usa (3) |
| germany (0), netherlands (0), taiwan (0) | |

## Y12 — FO candidate matrix

FO-0 / FO-1a / FO-1b / FO-1c × MA-0 / MA-1, all seven events, at **CW-0** (numbers directly comparable to Pass X). **ρ is reported as a check only — n = 7, ρ never selects a candidate, and nothing in this pass was tuned toward it.** Under **MA-0 all four candidates share ρ = +0.7143** (fanout scoping is invisible to event-ranking when the top node is already correct). Under **MA-1**:

| candidate | ρ | china-rees | kachin | P-J-2 | spurious nulls |
|---|---:|---|---|---:|---|
| FO-0 | +0.8929 | 36, gallium ✗ | 8 | 36 | — |
| FO-1a | +0.8929 | 7, dysprosium ✓ | 8 | 36 | — |
| FO-1b | +0.8571 | 7, dysprosium ✓ | **0 (nulled)** | 0 | taiwan, netherlands×2 |
| **FO-1c** | **+0.8929** | 7, dysprosium ✓ | **8 (kept)** | 0 | **none** |

Full per-event tables (reached, max-Δ node/value, origin contribution, tier changes, nulls) are in `pass_y_facts.json`. Tier changes are 0 for every event under every candidate at these magnitudes.

## Y13 — Does FO-1c dominate FO-1b?

**Semantic case, made first and independent of ρ.** FO-1b's strict fallback exists to convert "a country named with no subject" into an honest recorded null instead of a 34-node fanout. But that reasoning only applies when there **is** a fanout to prevent. `country_region:kachin` has exactly **one** outbound supply edge — scoping it prevents nothing and simply deletes a real event's signal. FO-1c refines the predicate to fire the strict fallback **only where fanout is structurally possible** (>1 distinct target). On the corpus this means: china-rees still scopes to dysprosium (China is multi-target); P-J-2 still nulls (China is multi-target); **kachin keeps its 8 nodes and its rank** because there was never anything to scope; and taiwan/netherlands stop getting spurious nulls. FO-1c gets everything FO-1b's philosophy wanted **without** the false null on a single-target country. **ρ recovering from 0.8571 to 0.8929 is a consequence to check, not the argument** (Expectation #14: HIT) — and it checks out.

**The cost FO-1b does not have (§5.3), confronted directly.** FO-1c makes walk semantics **conditional on current graph shape**. Kachin is single-target *today*. If a future data pass adds a second mineral edge out of kachin (e.g. kachin also mines a second REE), kachin **silently** flips from "seed normally" to "strict scoping" — with no authoring event about walk behaviour and no reviewable diff that says "kachin's cascade semantics changed." FO-1b has no such conditional: its behaviour depends only on whether a subject was matched, which is visible in the event. **This is the strongest argument against FO-1c and it is real.** Weighing: the FO-1b cost is a **false null on a real event, today, on the committed corpus** — a concrete, present defect. The FO-1c cost is a **latent trap that fires only on a specific future edge addition** — contingent, and **fully mitigable** by a guard test that asserts each country's target-count class and fails when an edge addition changes it (Y15). A present defect outweighs a guardable future one. **FO-1c dominates FO-1b on this corpus, conditional on shipping that guard.** If the guard is judged insufficient, FO-1b + a corpus re-authoring of kachin (add the dysprosium subject) is the alternative — but that edits the corpus, which is out of scope here.

## Y14 — Interaction (Block C)

**Cascade semantics and fanout are coupled, exactly as Pass X found fanout and MA-1 to be.** `china-rees` max-Δ node at MA-1:

| | CW-0 | CW-2 | CW-1 |
|---|---|---|---|
| **FO-0** (no scoping) | gallium ✗ | neodymium ✗ | neodymium ✗ |
| **FO-1c** (scoped) | dysprosium ✓ (Δ 0.059810) | **dysprosium ✓ (Δ 0.091096)** | dysprosium ✓ (Δ 0.091096) |

Neither fix alone is sufficient and neither is redundant:
- **Cascade fix alone** (FO-0 + CW-2): moves the max from gallium to neodymium — still the wrong element.
- **Fanout scoping alone** (FO-1c + CW-0): correct node (dysprosium) but at the **wrong magnitude** — Δ 0.059810 via the 0.65 *mines* edge, when China's actual dysprosium chokehold is the 0.99 *refining* share.
- **Both** (FO-1c + CW-2): correct node **and** correct magnitude — dysprosium at 0.091096 via the 0.99 refining edge.

Also: **fanout scoping removes most of the CW-1/CW-2 divergence.** Under FO-0 the two diverge on 46 node-instances (hbm 135×, cowos 325×); under FO-1c that drops to **9**, all low-magnitude china-gallium facilities, none affecting any event's attribution. Scoping prunes the multi-mineral competition that longer-path suppression feeds on, so once scoping ships, **CW-2 (the minimal parallel-edge fix) is sufficient for attribution** and CW-1's extra machinery changes only sub-0.001 deep-facility contributions.

**Sequencing constraint, in the same load-bearing form as Pass X:** the ship pass that takes fanout scoping (FO-1c) + MA-1 **must also take the cascade parallel-edge fix (CW-2)** in the same pass. FO-1c + MA-1 without CW-2 lands the right node at the wrong magnitude (0.059 not 0.091); shipping the cascade fix *without* scoping (FO-0 + CW-2) actively mis-attributes to neodymium. The three are one change.

## Y15 — Recommendation, blast radius, guards, ledger, open

**Recommendation (measurement pass — this ships nothing; Weston decides):** in the forthcoming ship pass, adopt **FO-1c (subject scoping, multi-target predicate) + CW-2 (parallel-edge collapse) + MA-1**, as one coupled change. CW-2 over CW-1 because, once fanout scoping is in place, CW-1's longer-path handling changes no attribution and only sub-0.001 contributions (Y14) — CW-2 is the smaller diff for the same result, and the residual longer-path cases can be revisited if a future non-country event surfaces one. FO-1c over FO-1b because it removes the false null on single-target kachin without losing anything FO-1b's philosophy wanted (Y13), **conditional on a graph-shape guard**.

**Blast radius, per change:**
- **CW-2:** edit `backend/app/scoring/cascade.py` — collapse each node's outbound supply edges to the max-share edge per target before expanding. Regenerates `summary.md` + the per-event replay pages (dysprosium/neodymium/indium/copper contributions and everything downstream). Re-grades: A-J-2's china-rees numbers; any finding quoting cascade contributions. **`test_outbound_walk_semantics.py` is untouched and still passes** (it pins the *engine* walk, a different function).
- **FO-1c + MA-1:** the fanout filter + perturbation seeding from Passes X/W, in `cascade.py`; no `Event` field (subject is in `entities_matched`); a durable, countable null record for scoped-country-with-no-subject (unresolved-register precedent). Regenerates the replay artifacts; re-grades the fanout blocker.
- **Files that would change:** `backend/app/scoring/cascade.py`; regenerated `docs/generated/replay/summary.md` and per-event pages; possibly a new null-register artifact. `config/scoring.yaml` unchanged (all structural).

**Guards that would need to exist:**
1. **A permanent test pinning the cascade walk's max-of-paths / parallel-edge semantics**, the way `test_outbound_walk_semantics.py` pins the engine's — this pass shows the two walks have diverged and only one is pinned; that asymmetry is itself a latent-defect source and should be closed when CW-2 ships.
2. **A graph-shape guard for FO-1c:** assert each country's distinct-target-count class and fail when an edge addition would silently flip a country between "seed normally" and "scoped" (the Y13 mitigation — without it, FO-1c's conditional is unreviewable).
3. A regression pinning P-J-2 at 0 and kachin at its non-null reach under the shipped candidate.

**Guards changed this pass: None.** No test was edited; `test_outbound_walk_semantics.py` remained untouched and passing.

**What this does not settle.** The n = 7 corpus binds every conclusion — FO-1c "dominates" on *these* seven events; growing the corpus is the highest-leverage move outside the pass sequence. Time decay, ingestion, the five misclassified cost-basis edges, the eight unmodelled minerals, the scale axis, the diff classifier's clamp-blindness, copper's `bottleneck_type`, and the `kachin-kia` corpus under-tagging are all out of scope and untouched. Whether CW-1's longer-path fidelity ever matters for a real event (vs CW-2's parallel-only fix) is unresolved on this corpus — no event's attribution turned on it once scoping was applied, but a future non-country-origin event might.

---

## Pre-registration scorecard (§7, citation column preserved)

| # | expectation | derived from | HIT/MISS | evidence |
|---|---|---|---|---|
| 1 | Committed byte-identical; suite 134/1/0 both | §3 | **HIT** | severities byte-identical to snapshot; suite 134/1/0 both invocations |
| 2 | CW-0 reproduces real `propagate_event`, 0 mismatches, 7 events | §3,§4.3 | **HIT** | `cw0_validation_mismatches` = 0 |
| 3 | `downstream_supply_edges` returns `edges.json` order, empirically confirmed | §4.4 | **HIT** | `china returned == file order: True` (Y2) |
| 4 | China gallium/dysprosium/neodymium/indium ordered mines-before-refines | §4.4 | **HIT** | Y2 table; copper too |
| 5 | China–gallium is the **only** China pair where CW-0's choice = max | §4.4 | **HIT** | Y3 census |
| 6 | Dysprosium hop-1 contribution rises exactly **1.523077×** under CW-2 | §4.4 | **HIT** | 0.136500 → 0.207900 (Y4) |
| 7a | Dysprosium `china-rees` Δ 0.059810 → ≈0.091095, below gallium 0.105983 | §4.4b | **HIT** | 0.091096; gallium 0.105983 (Y6) |
| 7b | Max-Δ flips to neodymium ≈0.133229; indium ≈0.107203 overtakes gallium; dysprosium 4th | §4.4b | **HIT** | neodymium 0.133230, indium 0.107203, dysprosium 4th (Y6) |
| 8 | Dysprosium Δ identical FO-0 and FO-1b at CW-0 (0.059810) | §4.5 | **HIT** | both 0.059810 (Y4) |
| 9 | `product:ndfeb_magnets` rises under CW-2 | §4.4 | **HIT** | 0.048620 → 0.074051 (china-rees MA-1) |
| 10 | `pass_w_measure` and `pass_x_measure` mark visited unconditionally | §4.7 | **HIT** | lines quoted (Y10) |
| 11 | CW-1 vs CW-2 differ on ndfeb_magnets: CW-1 neodymium 0.113400 vs CW-2 dysprosium 0.112266, 1.01% | §4.2,§4.4b | **HIT** | exact match, full precision (Y7) |
| 12 | FO-1c leaves P-J-2 at 0 | §5.4 | **HIT** | probe_matrix P-J-2\|FO-1c reached 0 |
| 13 | FO-1c leaves kachin-kia reach at 8, no unscoped null | §5.4 | **HIT** | reached 8, nulls [] (Y12) |
| 14 | FO-1c ρ under MA-1 ≥ FO-1b's +0.8571 | §5.4 | **HIT** | +0.8929 (Y12) |

**14 HIT, 0 MISS.** Both refutable rows (7b and 11) — the reviewer's arithmetic against published Pass X numbers, entailed by no harness construction — reproduced against the engine to full precision. The §7 citation discipline held: every expectation traced to a body section and none contradicted it.

## Guards changed

**None.** No test was added, edited, or removed. `test_outbound_walk_semantics.py` was not touched and still passes (3 passed). "None" is the expected answer for a measurement pass.

## Changed

- **New:** `backend/scripts/pass_y_measure.py` (in-process harness; imports Pass W's validated seed primitives so seeding cannot diverge), `docs/generated/cascade_fanout_candidates.md`, `docs/generated/pass_y_facts.json`, this report, and the `grading.md` Pass Y section.

## Not changed

- `config/scoring.yaml`, `data/ai/edges.json`, `data/ai/nodes.json`, `backend/app/scoring/cascade.py` — untouched. No authored `axes_impact`, `entities_matched`, or `outcomes.json` value edited. Committed severities/tiers/boundaries/constants byte-identical. Probes quarantined (`summary.md`/`outcomes.json` unchanged). No candidate shipped.

## Ledger — Pass Y

- **The cascade walk is first-encounter-wins, and it is broader than parallel edges.** The `visited_on_this_origin` set (never cleared, checked before the max comparison) discards, within one origin's walk, every arrival after the first — both weaker parallel edges (9 lossy pairs, 18 edges) and stronger longer paths (hbm 135×, cowos 325× on china-rees). The function's own docstring claims "BEST (max) path"; the code does not deliver it. Verdict (Y8): a termination guard (there is one supply-edge cycle) implemented via the wrong mechanism, with an unintended attribution defect — not intentional-and-correct.
- **CW-2 fixes parallel edges; CW-1 additionally fixes longer paths; CW-1 is not more expensive** (42.6 vs 43.8 ms). Once fanout scoping is applied, CW-1 vs CW-2 divergence collapses from 46 to 9 low-magnitude nodes and never affects attribution — so **CW-2 suffices with scoping**.
- **The cascade fix and fanout scoping are coupled** (Y14): cascade-alone moves china-rees's MA-1 max from gallium to neodymium (still wrong); fanout-alone lands dysprosium at the wrong magnitude (0.059 via mines, not 0.091 via refines); both together are correct on node and magnitude. The ship pass must take FO-1c + CW-2 + MA-1 as one change.
- **FO-1c dominates FO-1b on this corpus** (Y13): the >1-distinct-target predicate fires strict scoping only where fanout is structurally possible, keeping single-target kachin's real signal (8 nodes, rank held, ρ 0.8571→0.8929) and dropping FO-1b's spurious nulls on zero-target taiwan/netherlands — at the cost of making walk semantics conditional on graph shape, which is real but guardable and outweighed by FO-1b's present false null.
- **Harness note (Y10):** all Pass W and Pass X numbers were measured under CW-0. Neither pass's recommendation changes; the numbers are now labelled.
- **Retraction/correction:** none. Every §7 pre-registration HIT.
- **Open:** the n=7 binding constraint; cascade semantics unpinned by any test (the engine walk is pinned, the cascade walk is not) — should be closed when CW-2 ships; whether CW-1's longer-path fidelity ever changes a real event's attribution once scoping is in place.
- **Suite:** 134 pass, 1 skip, 0 xfail — both invocations. CW-0 validated node-for-node (0 mismatches). Measurement reproducible. Nothing shipped.
