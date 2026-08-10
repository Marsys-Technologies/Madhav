-- Migration 557: utkarsha_builder restricted Postgres role (GOCHARA-UTKARSA campaign I6(a))
-- ADJUDICATOR-approved: no DDL, no app.allow_protected_sweep_rewrite GUC
-- kala_gochara_windows: SELECT only (campaign reads v1 rows as benchmark)
-- kala_gochara_windows: INSERT only for generation='3.0' writes at W6 cutover
--
-- Role attributes: NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
-- No DDL privileges on any table.
-- No ability to SET app.allow_protected_sweep_rewrite GUC.
--
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.
-- Idempotency: DO block guards role creation; GRANTs are idempotent by Postgres semantics.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'utkarsha_builder') THEN
    CREATE ROLE utkarsha_builder NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

-- ── READ grants (SELECT only) ────────────────────────────────────────────────

GRANT SELECT ON TABLE gochara_resonance_map TO utkarsha_builder;
GRANT SELECT ON TABLE bg_gochara_arcs TO utkarsha_builder;
GRANT SELECT ON TABLE ephemeris_daily TO utkarsha_builder;
GRANT SELECT ON TABLE chart_facts TO utkarsha_builder;
GRANT SELECT ON TABLE chart_dashas TO utkarsha_builder;
GRANT SELECT ON TABLE public.charts TO utkarsha_builder;
GRANT SELECT ON TABLE bg_transit_rules TO utkarsha_builder;
GRANT SELECT ON TABLE bg_transit_engine TO utkarsha_builder;
GRANT SELECT ON TABLE bg_transit_av_gates TO utkarsha_builder;
GRANT SELECT ON TABLE brahma_event_ontology TO utkarsha_builder;
GRANT SELECT ON TABLE kala_gochara_authority TO utkarsha_builder;
GRANT SELECT ON TABLE kala_gochara_windows TO utkarsha_builder;   -- SELECT only; NO INSERT/UPDATE/DELETE via this grant (INSERT handled separately below)
GRANT SELECT ON TABLE build_protected_assets TO utkarsha_builder;
GRANT SELECT ON TABLE kala_vedha_gochara TO utkarsha_builder;
GRANT SELECT ON TABLE kala_moorti_nirnaya TO utkarsha_builder;
GRANT SELECT ON TABLE kala_kota_chakra TO utkarsha_builder;
GRANT SELECT ON TABLE kala_tithi_pravesha TO utkarsha_builder;
GRANT SELECT ON TABLE bg_sky_calendar TO utkarsha_builder;
GRANT SELECT ON TABLE bg_vedha_malefic_scale TO utkarsha_builder;
GRANT SELECT ON TABLE bg_phaladeepika_latta TO utkarsha_builder;
GRANT SELECT ON TABLE bg_kota_chakra_rings TO utkarsha_builder;

-- ── WRITE grants ─────────────────────────────────────────────────────────────

-- kala_gochara_windows_v2: full DML (primary write target for generation=3.0 output)
GRANT INSERT, UPDATE, DELETE ON TABLE kala_gochara_windows_v2 TO utkarsha_builder;

-- kala_gochara_v2_build_state: INSERT + UPDATE for upsert (no DELETE)
GRANT INSERT, UPDATE ON TABLE kala_gochara_v2_build_state TO utkarsha_builder;

-- kala_gochara_windows: INSERT only for generation='3.0' writes at W6 cutover
-- NO UPDATE, NO DELETE — v1 rows are read-only benchmark; only new rows appended
GRANT INSERT ON TABLE kala_gochara_windows TO utkarsha_builder;

-- build_substep_progress: INSERT + UPDATE for upsert (progress tracking)
GRANT INSERT, UPDATE ON TABLE build_substep_progress TO utkarsha_builder;

-- asset_registry: UPDATE only for health updates (no INSERT, no DELETE)
GRANT UPDATE ON TABLE asset_registry TO utkarsha_builder;

-- ── Sequence grants (USAGE + SELECT for nextval / currval) ───────────────────

GRANT USAGE, SELECT ON SEQUENCE kala_gochara_windows_v2_id_seq TO utkarsha_builder;
GRANT USAGE, SELECT ON SEQUENCE kala_gochara_windows_id_seq TO utkarsha_builder;
