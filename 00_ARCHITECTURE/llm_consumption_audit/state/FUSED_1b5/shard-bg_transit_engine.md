# FUSED 1b+5 shard — bg_transit_engine

families_total: 1 | channel: truly-UNREACHABLE | members_sampled: 1 | per_family_rows_written: 1

DB-truth: `SELECT count(*) FROM bg_transit_engine` → 9 (matches ledger family_key `__table_row_count__=9`, VF-3017). Columns: id, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, graha, classical_citation — global Gochara engine-parameter config (per-graha transit motion constants).
Serving check: ZERO manifest reference as a served table; NOT in ALIVE surgical; NOT in DEAD-19. Consumed only build-time / at compute by `brahmagyan/l0_transit.py`, `services/ka_sangam/engine.py`, `services/ka_yojaka/binder.py` (L3 Kala transit engines). `query_transit_event` (L1, ALIVE at MCP layer) serves computed per-chart transit EVENTS, not this config catalog — and in this audit env it returns inner `sidecar 401: Invalid API key, rows:[]`. asset_registry count_sql = cockpit stat only. No wire path → no diff possible.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| __table_row_count__=9 | truly-UNREACHABLE | UNREACHABLE (class 1) — transit engine-parameter config served by no tool | N/A — no wire path, diff impossible | path-grade(exemplar=__table_row_count__=9) + member-confirmation (family_count=1) |

Finding: lane 1b, class 1 UNREACHABLE, severity LOW. Internal Gochara compute config; its effect surfaces only via derived transit windows/events. Suspected layer: serving-query / architecture (config table by design). Dedupe: new (transit-config UNREACHABLE).
