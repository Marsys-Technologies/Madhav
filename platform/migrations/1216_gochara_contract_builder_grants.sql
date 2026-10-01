-- Migration 1216: grant data_plane_builder the exact table privileges the
-- governed gochara writers need on the 1153–1157 contract tables and the 1081
-- kala_gochara ledger tables.
-- Pravāha A2.5/A5.3 (steward M20261001T180830-5166, 2026-10-01).
-- Created: 2026-10-02. Author: pravaha stream A.
--
-- WHY THIS EXISTS
-- ═══════════════
-- The '4.1' candidate writer (ka_gochara_v4_41_candidate, PR #2799) and the
-- registered '5.0' writer (ka_gochara_v5, A5.3) run on the governed build path
-- as data_plane_builder. Their tables were created by migrations 1081 and
-- 1153–1157 with owner-only privileges; the builder held NOTHING on any of the
-- 18 tables below (verified read-only against production before authoring:
-- has_table_privilege('data_plane_builder', <each table>, 'SELECT') = false for
-- all 18; the builder's existing privileges cover only the legacy
-- kala_gochara_windows / _v2 / _authority / _v2_build_state / archive tables).
-- Without these grants every governed gochara write fails with
-- 'permission denied for table …' at the first DML.
--
-- GRANT MATRIX — derived from the actual code paths, per table, nothing more
-- ═══════════════════════════════════════════════════════════════════════════
-- Global, INSERT-ONLY families (AM-3 revised, steward M20261001T171150-1b1a:
-- conventions, physical objects, sky events, contact identities and the rule
-- registry are GLOBAL and INSERT-ONLY; persistence is insert-if-absent with
-- identity equality checks — never delete-then-insert). SELECT is needed for
-- the insert-if-absent read / equality check; INSERT for the absent case:
--   ka_gochara_sky_convention, ka_gochara_physical_object, ka_gochara_sky_event,
--   ka_gochara_contact_identity, ka_gochara_convention_bridge,
--   ka_gochara_predicate, ka_gochara_factor, ka_gochara_rule_path,
--   ka_gochara_rule_path_prerequisite, ka_gochara_rule_path_soft_factor,
--   ka_gochara_rule_path_seal
-- Chart×generation-scoped candidate rows, insert-if-absent only (nothing FKs
-- them away; replacement is impossible by design): SELECT, INSERT:
--   ka_gochara_contact, ka_gochara_relationship_record,
--   ka_gochara_record_prerequisite
-- kala ledger (1081):
--   kala_gochara_convention   — SELECT, INSERT (insert-only by trigger;
--                               convention registration reads-then-inserts)
--   kala_gochara_contacts     — SELECT, INSERT, DELETE (the v4_41 body-scoped
--                               delete-then-insert: DELETE … WHERE chart_id,
--                               generation, body; then INSERT)
--   kala_gochara_coverage     — SELECT, INSERT, DELETE (same scoped rewrite)
--   kala_gochara_publication  — SELECT, INSERT, UPDATE (publish_candidate
--                               replaces the CANDIDATE row in place; the
--                               partial unique index on status='published'
--                               and the sealed-generation guards bound what
--                               UPDATE can reach — no grant can weaken those)
-- DEFERRED — no write path exists yet, so no grant (disclosed, not silent):
--   ka_gochara_eval_window, ka_gochara_eval_window_record (interval sweep
--   persistence lands with A5.3's writerbase conformance),
--   ka_gochara_av_polarity_declaration, ka_gochara_generation_seal
--   (generation seal is a flip-time object; D-FLIP is the native's).
-- NOT INCLUDED: asset_freshness / bg_transit_moorti grants — those are
-- Suvarṇa's migration 1217.
--
-- No sequence grants: none of the 18 tables has an identity or serial column
-- (verified: UUID PKs default gen_random_uuid(); TEXT/UUID keys are
-- caller-minted). data_plane_builder gains no CREATE on schema public and no
-- TRUNCATE/TRIGGER/REFERENCES anywhere; the 1153 truncate-refusal triggers and
-- the 1155/1156 write guards stay exactly as created.
--
-- DEPLOY-GATE SAFETY (allowlist drift)
-- ════════════════════════════════════
-- None of the 18 tables appears in L1_ACTIVE_TABLES / L2_ACTIVE_TABLES
-- (platform/scripts/data-plane-ownership-preflight.ts) nor in the protected
-- relation sets of data-plane-ownership-status.ts or
-- data-plane-ownership-protected-cutover.ts (verified by grep across all three
-- scripts), so no ACL allowlist check sees them and these grants cannot trip
-- an allowlist-drift gate.
--
-- RUNNER AUTHORITY
-- ════════════════
-- The routine migration runner connects as amjis_app (PROD_DATABASE_URL —
-- platform/scripts/validate-migration-database-routes.ts), and amjis_app OWNS
-- all 18 tables (verified read-only: pg_tables.tableowner = 'amjis_app' for
-- each), so every GRANT below is issued by the owner. This migration creates
-- no object; it only grants on existing unprotected ones.
--
-- Idempotent: GRANT of an already-held privilege is a no-op in PostgreSQL.

-- Global insert-only families: SELECT (insert-if-absent read + equality check)
-- + INSERT.
GRANT SELECT, INSERT ON public.ka_gochara_sky_convention TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_physical_object TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_sky_event TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_contact_identity TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_convention_bridge TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_predicate TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_factor TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_rule_path TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_rule_path_prerequisite TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_rule_path_soft_factor TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_rule_path_seal TO data_plane_builder;

-- Chart×generation-scoped candidate rows: SELECT + INSERT only.
GRANT SELECT, INSERT ON public.ka_gochara_contact TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_relationship_record TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_record_prerequisite TO data_plane_builder;

-- kala ledger (1081).
GRANT SELECT, INSERT ON public.kala_gochara_convention TO data_plane_builder;
GRANT SELECT, INSERT, DELETE ON public.kala_gochara_contacts TO data_plane_builder;
GRANT SELECT, INSERT, DELETE ON public.kala_gochara_coverage TO data_plane_builder;
GRANT SELECT, INSERT, UPDATE ON public.kala_gochara_publication TO data_plane_builder;
