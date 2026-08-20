# Pass X — Country-origin fanout, Phase A: measurement only

**Type:** Measurement pass. No committed scoring change, no config-key change, no edge, node, or authored-axis value edited. Every committed severity, tier, and constant byte-identical at close. Candidates driven in-process.

**Addresses:** the country-origin fanout blocker, and the two Pass W findings — MA-1 makes fanout worse (it mis-attributes `china-rees` to gallium), and unscored-origin seeding puts a concentration difference into a channel that otherwise carries severity differences.

Numbers are read from `docs/generated/pass_x_facts.json` and `docs/generated/fanout_candidates.md`, written by `backend/scripts/pass_x_measure.py`.

---

## X1 — Provenance

- **HEAD at open:** the Pass W commit `5a0b7f6`. Working tree clean.
- **HEAD at close:** the Pass X commit.
- **`git status --short` at open:** clean.
- **`git diff --name-only 5a0b7f6..HEAD`:**
  ```
  backend/scripts/pass_x_measure.py         (new; in-process harness)
  docs/generated/fanout_candidates.md       (new; generated)
  docs/generated/pass_x_facts.json          (new; generated)
  docs/generated/replay/pass_x_report.pdf   (new)
  docs/generated/replay/grading.md          (Pass X section)
  ```
- **No scoring code, config value, authored axis, or matched entity moved.** `config/`, `data/`, `backend/app/scoring/`, and `backend/app/graph/` are untouched. Committed severities/tiers are byte-identical to the snapshot (verified). Probes stayed quarantined — `summary.md` and `outcomes.json` unchanged.

---

## X2 — The fanout surface, enumerated

Every `country_region` node's outbound supply edges (`downstream_supply_edges` = `out_edges` filtered to `SUPPLY_EDGE_TYPES` = `{mines, refines, supplies, input_to, component_of, operates}`; `located_in` is not a supply type and runs company→country, i.e. inbound to the country):

| country | outbound supply edges (type → target : input_share) |
|---|---|
| australia | mines→neodymium 0.10 |
| brazil | mines→neodymium 0.05 |
| canada | refines→gallium 0.15; mines→indium 0.15; refines→indium 0.10 |
| chile | mines→copper 0.25; refines→copper 0.15 |
| **china** | mines→gallium 0.985; refines→gallium 0.60; mines→dysprosium 0.65; refines→dysprosium 0.99; mines→neodymium 0.60; refines→neodymium 0.90; mines→indium 0.30; refines→indium 0.58; mines→copper 0.10; refines→copper 0.47 |
| drc | mines→copper 0.13; refines→copper 0.13 |
| japan | mines→gallium 0.01; refines→gallium 0.10; mines→indium 0.10; refines→indium 0.10 |
| kachin | mines→dysprosium 0.35 |
| malaysia | refines→dysprosium 0.01; refines→neodymium 0.10 |
| myanmar | mines→neodymium 0.10 |
| peru | mines→copper 0.11; refines→copper 0.13 |
| south_korea | mines→gallium 0.005; mines→indium 0.20; refines→indium 0.15 |
| usa | refines→gallium 0.05; mines→neodymium 0.15; mines→copper 0.06; refines→copper 0.12 |

**§0 confirmed.** Across all 16 country nodes, every outbound supply edge is `mines` or `refines` into a mineral — **no `supplies`, `operates`, or other type appears** (Expectation #2: HIT). `country_region:china` has **exactly 10** outbound supply edges, matching the §0 table byte-for-byte (Expectation #3: HIT). The fanout surface is therefore small, enumerable, and mineral-only. (Note: taiwan and netherlands have **zero** outbound supply edges — they are not mineral sources — so an event matching only those countries fans out nowhere, which is why taiwan-quake and nexperia are unaffected by any scoping candidate.)

---

## X3 — Candidate × seeding matrix

Five candidates × two seedings × seven events. **FO-0 + MA-0 was validated node-for-node against the real `propagate_event` (0 mismatches on all 7 events)** before any candidate was trusted. `hop0` = distinct hop-0 edges the walk followed; `reached` = nodes with |Δ|>1e-6; `max Δ node` is the attribution readout; `subject?` = is the max-Δ node the event's named subject mineral or downstream of it.

**Seeding MA-0** (all five candidates give ρ = +0.7143 — see X8):

| candidate | china-rees reached | china-rees max-Δ node | china-gallium reached | kachin reached | probe P-J-2 reached |
|---|---:|---|---:|---:|---:|
| FO-0 | 36 | mineral:dysprosium | 36 | 8 | 36 |
| FO-1a | **7** | mineral:dysprosium | **16** | 8 | 36 |
| FO-1b | **7** | mineral:dysprosium | **16** | **0** | **0** |
| FO-2 | 7 | mineral:dysprosium | 16 | 8 | 36 |
| FO-3 | 7 | mineral:dysprosium | 16 | **0** | **0** |

**Seeding MA-1** (ρ varies — X8):

| candidate | ρ | china-rees reached | china-rees max-Δ node | kachin reached/rank | probe P-J-2 reached |
|---|---:|---:|---|---:|---:|
| FO-0 | +0.8929 | 36 | **mineral:gallium** | 8 / 4 | 36 |
| FO-1a | +0.8929 | **7** | **mineral:dysprosium** | 8 / 4 | 36 |
| FO-1b | +0.8571 | **7** | **mineral:dysprosium** | **0 / 5** | **0** |
| FO-2 | +0.9643 | 7 | mineral:dysprosium | 8 / 4 | 36 |
| FO-3 | +0.8571 | 7 | mineral:dysprosium | 0 / 5 | 0 |

Full per-event tables (all seven events, `model_rank`, tier changes) are in `fanout_candidates.md`. Tier changes are 0 for every event under every candidate × seeding (no event crosses a boundary at these magnitudes).

**Expectation #4: HIT** — under FO-1a and FO-1b with MA-0, `china-rees` reaches **7** nodes (< 15), down from 36 (my estimate was ~10). **Expectation #6: HIT** — FO-0 + MA-1 reproduces Pass W's W4: `china-rees`'s max-Δ node is `mineral:gallium`. **Expectation #7: HIT** — under FO-1a/1b/2/3 with MA-1, the max-Δ node is `mineral:dysprosium` (the subject).

---

## X4 — Attribution, the primary readout

The top-5 affected nodes beside the observed prose. **Nothing was tuned toward the subject binary or toward ρ** (X8).

**`J-2025-04-china-rees`** — observed (`outcomes.json`, ordinal 2): *"Dysprosium and terbium prices spiked ~40-70%… NdFeB magnet buyers accelerated recycling… AI compute impact was indirect: any AI-adjacent motor/actuator hardware saw price and lead-time pressure."* The real story is a **dysprosium** shock flowing to NdFeB magnets.

| rank | FO-0 + MA-1 (top-5) | Δ | FO-1b + MA-1 (top-5) | Δ |
|---:|---|---:|---|---:|
| 1 | **mineral:gallium** | 0.105983 | **mineral:dysprosium** | 0.059810 |
| 2 | mineral:neodymium | 0.088820 | product:ndfeb_magnets | 0.048620 |
| 3 | product:rf_power_semis | 0.079618 | company:vertiv | 0.005560 |
| 4 | mineral:dysprosium | 0.059810 | facility:colossus | 0.003538 |
| 5 | mineral:indium | 0.055450 | facility:stargate_abilene | 0.003538 |

Under FO-0 + MA-1 the dysprosium licence's four largest effects land on **gallium, neodymium, RF/power semis, and only then dysprosium** — the event's own subject is fourth. Under FO-1b the top two are **dysprosium and NdFeB magnets** — exactly the observed chain. Even under **MA-0**, FO-0's top-5 is polluted by gallium (rank 3, 0.0666) and neodymium (rank 4) — cross-mineral bleed from China's other edges; FO-1b removes it, leaving dysprosium → NdFeB → downstream. Scoping improves attribution under both seedings; it only changes the **#1** node under MA-1 (where the concentration-difference seed floods the fanout — X7).

### Subject binary (is max-Δ node the subject mineral or downstream of it?)

| event (subject) | seeding | FO-0 | FO-1a | FO-1b | FO-2 | FO-3 |
|---|---|:--:|:--:|:--:|:--:|:--:|
| china-rees (dysprosium) | MA-0 | yes | yes | yes | yes | yes |
| china-rees (dysprosium) | MA-1 | **NO** | yes | yes | yes | yes |
| china-gallium (gallium) | MA-0 | yes | yes | yes | yes | yes |
| china-gallium (gallium) | MA-1 | yes | yes | yes | yes | yes |

The only binary failure is **FO-0 + MA-1 on china-rees** — the exact case the Sequencing rationale named. Every scoping candidate repairs it. (The other five events have no country-with-subject structure that lets the binary fail: china-gallium's subject *is* the most-concentrated node it reaches, so even FO-0+MA-1 keeps it.) **This binary was reported, not optimized** — with seven events and a binary, tuning it would be trivial and was not done.

---

## X5 — The china-rees case, traced

`china-rees` matches `country_region:china` (conf 1.0) and `mineral:dysprosium` (conf 1.0); axes `cd 0.35, sd 0.10, ld 0.20`.

**Under FO-0, which of China's edges carried the walk.** China (unscored origin) seeds all five minerals it mines/refines: dysprosium, gallium, neodymium, indium, copper — each then propagates downstream (NdFeB, RF/power, data-center facilities). Dysprosium *also* seeds independently as a scored origin. That is 36 reached nodes.

**How gallium overtook dysprosium under MA-1 (the defect).** MA-1's contribution for the **unscored** China origin is `(conc' − conc) × confidence = (min(0.6285 + 0.35, 1) − 0.6285) × 1.0 = 0.350000` — a **concentration difference** (X7). China's seed of `0.35` flows into all five minerals; gallium's downstream path (→ RF & power semis, a high-share chain) amplifies more than dysprosium's (→ NdFeB at input_share 0.20, which dampens). Meanwhile dysprosium's *own* scored seed is only `severity' − baseline = 0.044070` — an eighth of China's concentration-difference seed. So the walk from China, flooding gallium's amplifying downstream, produces a larger max-Δ at gallium (0.106) than at dysprosium (0.060). **The event's largest modelled effect lands on a different element than the one it is about.**

**Under each scoping candidate.** FO-1a/1b/3 restrict China's hop-0 edges to matched targets — only `dysprosium` is matched, so China seeds **only** dysprosium (mines 0.65 / refines 0.99), and the four other minerals are never lit. Reached collapses 36 → 7; max-Δ returns to dysprosium (0.060). FO-2 drops the China origin entirely (a non-country entity, dysprosium, is present), leaving dysprosium's own seed (0.044) — also max-Δ = dysprosium, reached 7, but a smaller magnitude because China's contribution is discarded rather than redirected.

---

## X6 — The probes

Both probes carry an injected `concentration_delta = 0.20` and match a single country. **Both stayed quarantined** — no probe entered `summary.md`, ranking, or `outcomes.json` (the harness runs them in a separate `probe_matrix`; the committed replay `summary.md`/`outcomes.json` are byte-identical).

| probe | match | FO-0 reached | FO-1a reached | FO-1b reached | FO-2 reached | FO-3 reached |
|---|---|---:|---:|---:|---:|---:|
| **P-J-2** (Chinese port congestion) | china only | 36 | 36 | **0** | 36 | **0** |
| P-J-1 (Nexperia) | netherlands only | 0 | 0 | 0 | 0 | 0 |

**P-J-2 was authored precisely to expose country-origin fanout and no pass had used it until now.** It matches `country_region:china` and nothing else — a story with zero AI-supply content that nonetheless lights **36 nodes** under the status quo. It is the cleanest test of each candidate:

- **FO-0, FO-1a, FO-2 leave it at 36** — they do **not** address the problem the probe was built to expose. FO-1a's permissive fallback fires the full unscoped set when no subject is matched (which is P-J-2's whole nature); FO-2 only drops country origins when a *non-country* entity is present, and P-J-2 has none.
- **FO-1b and FO-3 null it (36 → 0)** and record `country_region:china` as an unscoped-country-origin null — the honest answer for a country match with no subject.
- **P-J-1 is the control:** netherlands has no outbound supply edges, so it reaches 0 under every candidate. Fanout is a property of mineral-source countries only.

**Expectation #5: HIT** — FO-1a leaves P-J-2 at 36 (the spec's §0 estimate of 34 was from an earlier graph; the current 72-node graph gives 36, consistent with china-rees/china-gallium also at 36); FO-1b takes it to 0.

---

## X7 — Unscored-origin seeding (§1)

Every unscored (country) origin in the corpus, and the quantity it seeds:

| event | origin | conc | cd | MA-0 seed | MA-1 seed |
|---|---|---:|---:|---:|---:|
| taiwan-quake | taiwan | 0.0000 | 0.05 | 0.00000 | 0.05000 |
| kachin-kia | kachin | 0.1168 | 0.20 | 0.02335 | 0.20000 |
| kachin-kia | myanmar | 0.0345 | 0.20 | 0.00483 | 0.14000 |
| china-gallium | china | 0.6285 | 0.30 | 0.18856 | 0.30000 |
| china-gallium | usa | 0.0937 | 0.30 | 0.01967 | 0.21000 |
| china-rees | china | 0.6285 | 0.35 | 0.21999 | 0.35000 |

- **MA-0 formula:** `concentration × concentration_delta × confidence` — a magnitude-scaled fraction of the origin's concentration.
- **MA-1 formula:** `(conc′ − conc) × confidence` — **a concentration difference**.

**A concentration difference and a severity difference are entering the same channel.** For a scored origin, MA-1 seeds `severity′ − baseline` (e.g. dysprosium `0.044`); for an unscored country origin, it seeds `conc′ − conc` (e.g. China `0.35`). These are different quantities on different scales — and on `china-rees` the unscored concentration difference (`0.35`) is **~8× the scored severity difference (`0.044`)** of the event's actual subject, which is the mechanism behind the gallium mis-attribution (X5). Both then combine through the same noisy-OR.

**What the ship spec must decide** (posed, not answered here): whether an unscored origin's event contribution should be (a) placed on the severity scale — e.g. seeded through the origin's concentration-into-severity coefficient rather than as a bare concentration delta; (b) left as a concentration difference but kept out of the severity channel; or (c) suppressed at the country level entirely (which fanout scoping partially achieves — FO-1b's null removes the unscored-origin seed for subject-less events, and subject scoping routes it through the scored subject). Fanout scoping mitigates this but does not resolve it: a scored-subject country event (china-rees under FO-1b) still routes China's `0.35` concentration difference into dysprosium's downstream. **Expectation #8: HIT** — every unscored origin under MA-1 seeds `conc′ − conc`, not a severity difference.

---

## X8 — Rank correlation, with the §4 caveat attached

> **§4 caveat, reproduced.** ρ is the **wrong primary instrument** for this pass. Fanout is an attribution defect — the event ranks fine while hitting the wrong node — so a candidate can leave ρ unchanged and still be the right fix. n = 7; ρ is a check, never a selector. **Nothing was tuned toward ρ or toward the subject binary anywhere in this pass.**

| candidate | ρ (MA-0) | ρ (MA-1) | displacement changed vs FO-0? | attribution changed vs FO-0? |
|---|---:|---:|---|---|
| FO-0 | +0.7143 | +0.8929 | — | — |
| FO-1a | +0.7143 | +0.8929 | no (identical) | **yes** (china-rees 36→7; MA-1 gallium→dysprosium) |
| FO-1b | +0.7143 | +0.8571 | MA-0 no / MA-1 yes | yes |
| FO-2 | +0.7143 | +0.9643 | MA-0 no / MA-1 yes | yes |
| FO-3 | +0.7143 | +0.8571 | MA-0 no / MA-1 yes | yes |

**Under MA-0, all five candidates have identical ρ (+0.7143) — yet FO-1a/1b/2/3 all change attribution** (china-rees 36→7, cross-mineral pollution removed). This is the §4 thesis exactly: **ρ is blind to the fanout fix**, because under MA-0 the max-Δ node was already dysprosium, so the *event's rank* doesn't move even as the *reached set* collapses from 36 to 7. **Expectation #10: HIT** — FO-1a leaves ρ unchanged versus FO-0 under both seedings while changing attribution.

Under MA-1: FO-1a holds ρ at FO-0's 0.8929 while fixing the gallium mis-attribution. FO-1b and FO-3 **lower** ρ to 0.8571 — not because scoping is wrong, but because nulling `kachin-kia` (a real event, observed ordinal 4) drops its rank 4→5. FO-2 **raises** ρ to 0.9643, the best of any candidate — but its high ρ is not a reason to pick it (X10). **No tuning was performed**; the five candidates are fixed rules run once each.

---

## X9 — FO-3, rejected

FO-3 (per-edge event scoping via a new `Event` field) is **mechanically identical to FO-1b on this corpus** — verified: for every event under both seedings, FO-3's reached count and max-Δ equal FO-1b's. The honest authoring of a per-edge field is "the subject minerals," which is exactly what FO-1b derives automatically from `entities_matched`; so the extra field changes **no number**.

It does two things FO-1b does not: it adds an **authoring burden** (every country event must now carry an edge/subject list in addition to `entities_matched`), and it **lets the author encode the answer** — the exact failure mode the §4.1 discipline exists to catch. An author who knows the expected ranking can name the edge set that produces it, and no structural check can distinguish a faithful edge list from a results-driven one. **That risk is inherent to the design, not avoidable by construction:** a free-form author-named edge set is, by definition, capable of encoding any attribution. Since FO-3 buys zero mechanical improvement over FO-1b's automatic scoping while adding burden and an unremovable encoding hazard, **FO-3 is rejected.**

---

## X10 — Recommendation, with the case against it

**Recommended (semantic grounds): FO-1b — subject scoping with strict fallback — assuming MA-1 seeding.**

When an event names a subject, FO-1b routes the country origin's walk to that subject's supply relationship only: `china-rees` → dysprosium, `china-gallium` → gallium. That is semantically exact — a Chinese dysprosium licence concerns the China→dysprosium relationship and no other, and `entities_matched` already carries the subject. When an event names a country and **no** subject, FO-1b produces a **recorded, countable null** rather than lighting 36 unrelated nodes — the honest answer, following the unresolved-register precedent the spec invokes. It is the only candidate (with FO-3, its mechanical twin) that **addresses the problem P-J-2 was built to expose** (36 → 0), and it repairs the MA-1 gallium mis-attribution that motivated the pass.

**The strongest case against FO-1b.** On the current corpus it **nulls `kachin-kia`**, a real event (KIA seizing dysprosium-mining townships, observed ordinal 4), because its author matched `kachin` and `myanmar` but not `dysprosium` — and that null drops its rank 4→5, lowering ρ to 0.8571, **below FO-0's 0.8929 and well below FO-2's 0.9643.** Taken at face value the recommended design fits the outcomes *worse* than the status quo and worse than a rival. That is not a concession, for a specific reason the trace establishes: `kachin-kia`'s null is a correct consequence of an **authoring omission** — the story is explicitly about heavy-REE feedstock and *should* match dysprosium; FO-1b surfaces that gap as a reviewable null instead of hiding it under an 8-node fanout. The fix is to re-author the under-tagged event (out of scope here — the corpus is the instrument), after which FO-1b scopes it correctly and ρ recovers. **What would change the recommendation:** if re-authoring under-tagged country events proves impractical at corpus scale, **FO-1a** (permissive fallback) is the fallback recommendation — it never produces a false null and holds ρ at FO-0's level, at the cost of leaving genuinely subject-less country events (and the P-J-2 probe) over-firing. FO-1a fixes the common case (subject named) and accepts the rare case (subject absent); FO-1b fixes both but leans on corpus discipline.

**Not FO-2, despite the best ρ.** FO-2's 0.9643 is the highest number in the pass, and it is not the recommendation. FO-2 drops the country signal entirely whenever any specific entity is present — it cannot represent an event that is genuinely about both a country and a subject, and it does nothing for country-*only* events (kachin, P-J-2 stay at 36/8). Its double-counting argument (dysprosium's inbound HHI already encodes China's 0.99 refining share) is real, but the remedy — discard the country origin — is coarser than scoping it. **A higher ρ from a coarser rule is exactly what §4 warns against treating as decisive.**

---

## X11 — Blast radius and sequencing

- **Where the filter belongs:** in **`cascade.py`**, not `downstream_supply_edges`. The graph accessor is a pure structural query used in several places (outbound criticality, the reach BFS, provenance); adding event-scoping there would couple graph topology to event state. The right shape is a hop-0 edge filter inside `propagate_event`, parameterized by the event's `entities_matched` — precisely what this harness does. `downstream_supply_edges` stays untouched.
- **Does `Event` gain a field?** **No** under FO-1b — the subject is already in `entities_matched`; scoping reads it. (FO-3 would add a field; rejected, X9.) FO-1b needs a place to record the unscoped-country-origin null — following the spec, a durable countable record like the unresolved register, not a log line; a small `entities_unscoped`-style artifact under `docs/generated/replay/`.
- **Files that change if shipped:** `cascade.py` (hop-0 scoping + null recording); possibly a new generated null-register artifact. `config/scoring.yaml` unchanged (scoping is structural, not a knob) unless a toggle is wanted.
- **Replay artifacts regenerate:** `summary.md` and the per-event pages for `china-rees`, `china-gallium`, and `kachin-kia` (reach and — if MA-1 also ships — attribution change). `outcomes.json` unchanged (the instrument).
- **Findings to re-grade:** the country-fanout blocker (addressed); `kachin-kia`'s handling flags a **corpus-authoring** finding (missing dysprosium subject) that should be filed before or with the ship. Any grading that cited china-rees reach (36) or its MA-1 top node.
- **Guards changed (forecast):** a test that a country origin with a matched subject seeds only that subject's edges; a test that a subject-less country origin under strict fallback seeds nothing and records the null; a regression pinning P-J-2 at 0 under the shipped candidate; and the probe-quarantine guard extended to the null register.
- **Sequencing — the load-bearing conclusion:** **fanout scoping must ship *with* or *before* MA-1, never after.** Under MA-1 *without* scoping, `china-rees`'s largest effect is mis-attributed to gallium (X5) — Pass W would improve ρ while degrading attribution. Under MA-0, scoping is invisible to ρ but still correct (it removes cross-mineral pollution and cuts reach 36→7). So the safe order is: ship FO-1b (fanout scoping) first or in the same pass as MA-1. Shipping MA-1 alone is the one order this pass rules out.

---

## X12 — What this does not settle, scorecard, standard sections

**Not settled.** Time decay is untouched (still no cumulative replay). The **country/region semantics** question — whether a `country_region` node should be a supply-source aggregate at all, versus modelling the specific mine/refinery — this pass **works around rather than resolves**: FO-1b scopes the *walk* out of a country node without changing what the node *is*. A deeper fix would split "China the place" from "China's five independent supply chains," which is a data-model change beyond a scoping filter. The `kachin-kia` case shows the workaround's seam: scoping is only as good as the subject authoring.

### Scorecard (§6 pre-registrations, graded strictly 2–10)

| # | expectation | verdict | evidence |
|---|---|---|---|
| 1 | Committed state byte-identical at close | **HIT** | severities/tiers byte-identical to snapshot; only harness + generated + report files in diff (X1) |
| 2 | Every country's outbound supply edges are `mines`/`refines` only | **HIT** | all 16 countries enumerated; no other type (X2) |
| 3 | `china` has exactly 10 outbound supply edges matching the §0 table | **HIT** | 10 edges, exact match (X2) |
| 4 | FO-1a/1b + MA-0: china-rees reaches < 15 (from 36) | **HIT** | 7 (est. ~10) (X3) |
| 5 | FO-1a leaves P-J-2 ≈34; FO-1b takes it to 0 | **HIT** | FO-1a 36 (current-graph value; spec's 34 was stale), FO-1b 0 (X6) |
| 6 | FO-0 + MA-1: china-rees max-Δ node is gallium (reproduces W4) | **HIT** | mineral:gallium, 0.105983 (X3/X4) |
| 7 | ≥1 candidate + MA-1: china-rees max-Δ node is dysprosium or downstream | **HIT** | FO-1a/1b/2/3 → mineral:dysprosium (X3/X4) |
| 8 | Every unscored origin under MA-1 seeds `conc′ − conc`, not a severity difference | **HIT** | seeding table; china seeds 0.35 (X7) |
| 9 | FO-2 changes china-rees origin Δ from China's seed to dysprosium's | **HIT** | 0.350000 → 0.044070 (X5, facts) |
| 10 | ≥1 candidate leaves ρ unchanged vs FO-0 while changing attribution | **HIT** | FO-1a both seedings; all four under MA-0 (X8) |

**10 HIT, 0 MISS.** The §6 note held: expectations derived by quotation from the body all reproduced against the engine. (This is not tuning — the candidates were run once; the expectations simply described the mechanism the code implements.)

### Guards changed

**None.** This pass adds no test and modifies no guard. (X11 forecasts the guards a future ship would add.)

### Changed

- **New:** `backend/scripts/pass_x_measure.py` (in-process harness, imports Pass W's validated seed primitives so seeding cannot diverge), `docs/generated/fanout_candidates.md`, `docs/generated/pass_x_facts.json`, this report, and the `grading.md` Pass X section.

### Not changed

- No file under `backend/app/`, `config/`, or `data/`. No authored `axes_impact` or `entities_matched` value edited. No candidate committed. `events.magnitude_source` unchanged. Probes quarantined — `summary.md` and `outcomes.json` byte-identical. Served graph and all committed severities/tiers byte-identical.

### Ledger — Pass X

- **Fanout surface enumerated and small.** Every `country_region` outbound supply edge is `mines`/`refines` into a mineral; china carries exactly 10. taiwan/netherlands carry none (no fanout). The surface is mineral-only and enumerable.
- **The defect confirmed and its MA-1 amplification traced.** Under FO-0 an event matching a country lights every mineral it sources (china-rees/china-gallium/P-J-2 each reach 36). Under MA-1 the unscored country origin seeds a **concentration difference** (China `0.35`), ~8× the scored subject's severity difference (dysprosium `0.044`), flooding the fanout so `china-rees`'s largest effect mis-lands on **gallium** — a dysprosium event attributed to a different element.
- **Five candidates measured, MA-0 validated node-for-node (0 mismatches).** Subject scoping (FO-1a/1b/3) collapses china-rees 36→7 and repairs the MA-1 attribution (gallium→dysprosium); FO-2 does likewise by dropping the country origin.
- **ρ is blind to the fix, as §4 predicted.** Under MA-0 all candidates share ρ=+0.7143 while attribution changes; under MA-1 FO-1a holds ρ, FO-1b lowers it (nulling under-authored kachin-kia), FO-2 raises it (coarse).
- **Recommendation (semantic): FO-1b + MA-1** — scope to the named subject; produce an honest recorded null when a country is named with no subject (addresses P-J-2, 36→0). Case against: nulls the under-authored `kachin-kia`, lowering ρ — a corpus-authoring gap, not a scoping error; FO-1a is the fallback if corpus discipline can't be assured. **FO-3 rejected** (mechanically identical to FO-1b, adds burden + an inherent encode-the-answer hazard). **FO-2 not chosen despite the best ρ** (coarse; discards the country signal).
- **Unscored-origin seeding (§1) posed for the ship spec:** a concentration difference and a severity difference share the noisy-OR channel; fanout scoping mitigates but does not resolve it.
- **Sequencing:** fanout scoping ships **with or before MA-1, never after** — MA-1 alone mis-attributes china-rees.
- **Suite:** 134 pass, 1 skip, 0 xfail — both invocations. Measurement reproducible; committed scoring byte-identical; no candidate committed; probes quarantined.
