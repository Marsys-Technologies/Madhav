-- Migration 432: ga_sensitive_degree + ga_ayurdaya — new L1 Gaṇita assets (WP-2.5)
-- =============================================================================
-- Context: REMEDIATION_PLAN_v2_0 §5 WP-2.5 / R-47 / LCA-10 + LCA-16. Two never-computed
-- L1 quantity families — UNREACHABLE-by-nonexistence (the canon calls for them, no writer
-- computed them):
--
--   ga_sensitive_degree  → fact_category 'sensitive_degree_check' in chart_facts.
--        Per-graha sensitive-degree checks: mrityu-bhaga, neecha-bhanga, kartari,
--        sarvatobhadra-vedha, khareshwara (22nd drekkana + 64th navamsa), pushkara,
--        kranti/declination, gandanta. Each by its cited classical rule (B.10) —
--        mrityu-bhaga & pushkara degrees delegated 1:1 from PyJHora const arrays.
--
--   ga_ayurdaya          → fact_category 'ayurdaya' in chart_facts.
--        ALL THREE classical longevity methods (Pindayu / Nisargayu / Amsayu),
--        method-attributed (§7.2 BINDING: serve all three, no autonomous adjudication),
--        + classical applicability rule + alpa/madhya/purna classification + maraka
--        significators. Delegated to PyJHora jhora.horoscope.dhasa.graha.aayu (cited).
--
-- Both write into the existing chart_facts table (no new per-chart table). Idempotency is
-- L1 delete-then-insert scoped to (chart_id, ayanamsha_id, fact_category) — no overlap with
-- any other writer's categories (avoids the mig-416 shared-category lock-contention class).
-- Both depend on ga_positions (they read stored graha longitudes — §N.5 L1-authority; never
-- recompute positions). Orchestrator-native: @register WriterBase subclasses, ctx.db_conn
-- no-commit, orchestrator is the sole asset_throughput writer (§N.2 FROZEN contract).
-- =============================================================================

BEGIN;

-- ── ga_sensitive_degree ──────────────────────────────────────────────────────
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, depends_on,
    layer_name, layer_index, catalog_status
) VALUES (
    'ga_sensitive_degree', 'ganita', 50,
    'Marma Aṃśa Parīkṣā', 'Sensitive-Degree Checks',
    'Per-graha sensitive-degree facts (LCA-10): mrityu-bhaga, neecha-bhanga, kartari, '
    'sarvatobhadra-vedha, khareshwara (22nd drekkana + 64th navamsa), pushkara-bhaga/navamsa, '
    'kranti/declination, gandanta. Each computed by its cited classical rule. '
    'Writer: ga_sensitive_degree after ga_positions. Category: sensitive_degree_check.',
    'postgres_table', 'chart_facts',
    'SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category=''sensitive_degree_check''',
    NULL,
    0, 'per_chart', true, true, ARRAY['ga_positions'],
    'Ganita', 1, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    depends_on   = EXCLUDED.depends_on,
    sort_order   = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

-- ── ga_ayurdaya ──────────────────────────────────────────────────────────────
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, depends_on,
    layer_name, layer_index, catalog_status
) VALUES (
    'ga_ayurdaya', 'ganita', 51,
    'Āyurdāya', 'Longevity (Three Methods)',
    'Ayurdaya / longevity (LCA-16): ALL THREE classical methods (Pindayu, Nisargayu, Amsayu) '
    'method-attributed, with the classical applicability rule served alongside (no autonomous '
    'adjudication — §7.2), alpa/madhya/purna classification and maraka significators. '
    'Delegated to PyJHora aayu (cited). Writer: ga_ayurdaya after ga_positions. Category: ayurdaya.',
    'postgres_table', 'chart_facts',
    'SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category=''ayurdaya''',
    NULL,
    0, 'per_chart', true, true, ARRAY['ga_positions'],
    'Ganita', 1, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    depends_on   = EXCLUDED.depends_on,
    sort_order   = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id IN ('ga_sensitive_degree','ga_ayurdaya');
--   DELETE FROM chart_facts WHERE fact_category IN ('sensitive_degree_check','ayurdaya');
--   COMMIT;
-- =============================================================================
