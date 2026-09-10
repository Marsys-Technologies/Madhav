-- 730_nirmana_l3_f_vighna_5_depends_on.sql
--
-- NIRMĀṆA L3 Kāla — W3 (continuation range, ruled by the Conductor for L3: 730-739 —
-- see #1942/#1878, the previous 670-679 range fully consumed by migrations 670-679).
--
-- Discharges F-VIGHNA-5 (L3_W1_ANALYSIS_BATCH_E.md, ka_vighnakara finding 5): the live
-- `depends_on` for `ka_vighnakara` is `{ka_sangam, ka_gochara, ka_muhurta_seva,
-- ga_positions}` — verified against the writer's own SQL/imports before writing this
-- migration, not assumed from the analysis batch alone:
--
--   - `ka_gochara` — declared, but genuinely UNREAD. `ka_vighnakara.py` imports
--     `swisseph` directly and calls its own `_get_sidereal_lon` helper rather than going
--     through `KaGocharaService` — grepped for any `KaGocharaService`/`kala_gochara`
--     reference in the writer: zero matches. FICTIONAL edge — removed.
--   - `bg_combustion_orbs` — read (`_fetch_combustion_orbs`, `bg_combustion_orbs` table),
--     but UNDECLARED. Grepped which writer populates that table: `bg_dignity_reference`
--     (`@register("bg_dignity_reference")`, its own `_seed_combustion_orbs` step) — that
--     is the real asset_id to declare, not the bare table name. Added.
--   - `kala_activation_predicates` — read (`_dasha_anchor_peaks`), but UNDECLARED. That
--     table is `ka_yojaka`'s own output — a REAL ordering dependency (F-VIGHNA-5's own
--     text: "the ka_yojaka edge is a real ordering dependency and its absence from
--     depends_on is a DAG correctness issue, not just bookkeeping"). Added.
--   - `ka_sangam`, `ka_muhurta_seva`, `ga_positions` — all three verified genuinely read
--     (`FROM kala_convergence`; `KaMuhurtaSevaService()`; natal lagna longitude via
--     `chart_facts`) — kept unchanged.
--
-- Same scope caveat as migration 676 (N5's analogous ka_muhurta_seva fix): this corrects
-- the LIVE `asset_registry.depends_on` — the authoritative source future definition
-- freezes read from — and does NOT retroactively alter the current frozen manifest's
-- already-snapshotted `depends_on` for this asset. The TypeScript seed file
-- (platform/scripts/seed/asset_registry_seed.ts) is deliberately left as-is, matching
-- this session's established precedent (migrations 673/676 made the identical choice):
-- the seed file is the as-originally-authored record; migrations are the living
-- correction layer on top of it.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
SET depends_on = '{ka_sangam,ka_muhurta_seva,ga_positions,bg_dignity_reference,ka_yojaka}'
WHERE asset_id = 'ka_vighnakara';
