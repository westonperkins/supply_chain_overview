# Pass J replay — summary

One row per event. Nodes-reached counts nodes with |Δ| > 1e-6 (includes both scored-baseline nodes with current_severity moved and unscored nodes whose current_severity moved off None).

Tier-changed = did any node's `current_tier` differ from its `baseline_tier` after propagation? For unscored nodes `current_tier` stays UNSCORED per Pass H.1 — a walk touching an unscored downstream node writes current_severity but never a scored tier.

| event | origin(s) | origin scale | nodes reached (Δ>0) | max Δ | top affected | any tier change? |
|---|---|---|---|---|---|---|
| J-2024-04-taiwan-quake | company:tsmc, country_region:taiwan | 0.023 | 13 | +0.012 | company:tsmc | no |
| J-2024-09-asml-export | company:asml, country_region:netherlands | 0.000 | 0 | +0.000 | — | no |
| J-2024-10-kachin-kia | country_region:kachin, country_region:myanmar | 0.030 | 8 | +0.003 | mineral:dysprosium | no |
| J-2024-11-hynix-hbm | company:sk_hynix, product:hbm | 0.011 | 13 | +0.008 | company:sk_hynix | no |
| J-2024-12-china-gallium | country_region:china, mineral:gallium, country_region:usa | 0.248 | 34 | +0.077 | product:rf_power_semis | yes |
| J-2025-04-china-rees | country_region:china, mineral:dysprosium | 0.290 | 34 | +0.090 | product:rf_power_semis | yes |
| J-2025-10-nexperia | country_region:netherlands | 0.000 | 0 | +0.000 | — | no |

