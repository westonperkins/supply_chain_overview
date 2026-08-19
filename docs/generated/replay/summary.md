# Pass J replay — summary

_Provenance: graph @ commit `62b02ee` — 72 nodes, 259 edges. Archived Pass J artifacts (67-node graph, commit `1bd6090`) live under `docs/generated/replay/archive/pass_j_67node/`._

One row per event. `nodes reached` counts nodes with |Δ| > 1e-6 (includes both scored-baseline nodes with `current_severity` moved and unscored nodes whose `current_severity` moved off None).

`tier change?` = did any node's `current_tier` differ from its `baseline_tier` after propagation? For unscored nodes `current_tier` stays UNSCORED per Pass H.1 — a walk touching an unscored downstream node writes `current_severity` but never a scored tier.

`model_rank` is `max_delta ↓`, tie-broken by `nodes_reached ↓, origin_scale ↓, event_id ↑` (Pass J.1 §1). `rank_by_origin_scale` is the same chain with `origin_scale` promoted to primary (Pass J.1 §2). Rank definitions live in `backend/scripts/replay_events.py::_rank_events`; any doc that restates an ordering is a defect.

`class` is rendered from the committed `tags` array on each event (Pass J.1 §5). Vocabulary: `home_turf`, `misfit`, `misfit_candidate`.

| event | class | origins | origin scale | nodes reached | max Δ | top affected | tier change? | model_rank | rank_by_origin_scale |
|---|---|---|---|---|---|---|---|---|---|
| J-2025-04-china-rees | home_turf | country_region:china, mineral:dysprosium | 0.220 | 36 | +0.086 | mineral:dysprosium | yes | 1 | 1 |
| J-2024-12-china-gallium | home_turf | country_region:china, mineral:gallium, country_region:usa | 0.189 | 36 | +0.075 | mineral:gallium | yes | 2 | 2 |
| J-2024-04-taiwan-quake | misfit_candidate | company:tsmc, country_region:taiwan | 0.023 | 15 | +0.012 | company:tsmc | no | 3 | 4 |
| J-2024-11-hynix-hbm | misfit_candidate | company:sk_hynix, product:hbm | 0.015 | 13 | +0.011 | product:hbm | no | 4 | 5 |
| J-2024-10-kachin-kia | misfit_candidate | country_region:kachin, country_region:myanmar | 0.023 | 8 | +0.002 | mineral:dysprosium | no | 5 | 3 |
| J-2024-09-asml-export | misfit | company:asml, country_region:netherlands | 0.000 | 0 | +0.000 | — | no | 6 | 6 |
| J-2025-10-nexperia | misfit | country_region:netherlands | 0.000 | 0 | +0.000 | — | no | 7 | 7 |

