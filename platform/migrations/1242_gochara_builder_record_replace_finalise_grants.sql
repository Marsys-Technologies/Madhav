-- Migration 1242: grant data_plane_builder the record-table REPLACE and FINALISE privileges — four grants, nothing else.
-- Pravāha B6.0, steward M20261002T064220-07d6 (Stream A's restricted-builder rebuild flow), 2026-10-02.
-- Author: pravaha stream B. STATUS: HOLD. GRANTS ONLY — creates no object, replaces no function, edits no applied migration.
--
-- CORRECTION OF 1216's HEADER (1216 is applied and is NOT edited — this header is the correction of record)
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════
-- 1216 says the chart×generation-scoped candidate rows (ka_gochara_contact, ka_gochara_relationship_record,
-- ka_gochara_record_prerequisite) are "insert-if-absent only (nothing FKs them away; replacement is impossible by design)" and grants
-- SELECT, INSERT only. That claim was wrong for an UNSEALED generation, and it contradicts the registered writer. What the write
-- guards actually say (read, not assumed):
--   * 1155 ka_gochara_chart_write_guard (relationship_record / record_prerequisite / window tables): on DELETE it refuses ONLY when the
--     generation is SEALED ("DELETE refused; a re-evaluation is a new generation" — 1155:419-426); on UPDATE it refuses only a changed
--     (chart_id, generation), a 'no_update' table, a non-`result` change on a 'result_only' table, or a SEALED generation (1155:437-458).
--     So DELETE/UPDATE on rows of a candidate (unsealed) generation are permitted by the database — and refused after the seal.
--   * 1153 ka_gochara_contact_1_write_guard: "sealed generation: DELETE refused, INSERT (append) and enrichment permitted" (1153:176-177)
--     — i.e. DELETE of an unsealed generation's contact rows is the intended path; only a sealed one is frozen.
--   * 1153's own TRUNCATE refusal says it in words: "rebuild a CANDIDATE generation with a scoped DELETE" (1153:379); 1153:1109-1110:
--     "Writer: per-(chart_id × generation) delete-then-insert of CANDIDATE generations (CLAUDE.md §N.3); a sealed generation refuses DELETE".
--   * CLAUDE.md §N.3 (L1+ rebuild REPLACES, never accretes) and AM-3 (delete-then-insert per (chart × natural key)) say the same.
-- So replacement of UNSEALED rows IS the contract; "insert-only" holds for the GLOBAL families (conventions, physical objects, sky events,
-- contact identities, the rule registry) — not for the chart×generation candidate tables. 1216's grants were the minimum for a FIRST build
-- and the registered writer's REBUILD and FINALISE paths need four more. The grants are not weakened by the guards: once the generation
-- is sealed (the seal trigger), every one of these statements is refused by the same guards — verified by the live test.
--
-- THE MISSING PRIVILEGES (derived by running the registered writer AS data_plane_builder, a full build then a rebuild, on a deployment-
-- faithful role mirror — objects owned by amjis_app, PUBLIC EXECUTE revoked — and checked statement-by-statement against
-- has_table_privilege; Stream A's fixture pending_builder_record_grants.sql names the same set)
-- ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
--   ka_gochara_relationship_record   DELETE                  record_store.delete_record_grain / delete_class_chain — the AM-3 replace
--   ka_gochara_contact               DELETE                  the same replace (the class chain's contacts)
--   ka_gochara_relationship_record   UPDATE (admission_state) the F5 finalisation: the record's admission state once its prerequisites resolve
--   ka_gochara_record_prerequisite   UPDATE (result)          set_prerequisite_result — the F5 finalisation of a prerequisite result
-- Column-level UPDATE, not table-level: the writer sets only those columns; the 1155 guard additionally bounds a prerequisite UPDATE to
-- `result` alone (mode 'result_only'). SELECT is already held (1216) — a DELETE/UPDATE with a WHERE clause reads its filter columns.
-- NOT granted: UPDATE on any other column; DELETE on ka_gochara_record_prerequisite (its rows leave with the record via the 1155 cascade —
-- measured by the live test, not assumed); UPDATE on ka_gochara_contact (the writer does not enrich in place); TRUNCATE; TRIGGER; anything on
-- the window, verification, inventory or seal tables (1234, 1206 §7, 1240, 1241 own those).
--
-- ROUTE / WINDOW: a ROUTINE migration (the owner grants on existing objects; no object is created in schema public), so it is NOT in
-- PROTECTED_PUBLIC_SCHEMA_MIGRATIONS. It is numbered ABOVE 1240, so it is NOT an unapplied predecessor of the protected window (`migrate.ts
-- --only` refuses only unselected, unapplied files numbered BELOW the highest selected one): the window's ledger precondition stays 1234 and
-- 1236. It is needed before the first RESTRICTED build (the builder cannot replace or finalise record rows without it) and may be applied by
-- the routine route before or after the window — either order works. It touches only tables 1153/1155 created (already applied in
-- production). Idempotent: GRANT of an already-held privilege is a no-op. ROLLBACK: REVOKE the same grants.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    RAISE EXCEPTION 'migration 1242: role data_plane_builder does not exist — refusing to grant to nobody (CLAUDE.md §N.4)';
  END IF;
  IF to_regclass('public.ka_gochara_relationship_record') IS NULL
     OR to_regclass('public.ka_gochara_contact') IS NULL
     OR to_regclass('public.ka_gochara_record_prerequisite') IS NULL THEN
    RAISE EXCEPTION 'migration 1242: a record table is missing — apply 1153/1155 first';
  END IF;
END;
$$;

GRANT DELETE ON public.ka_gochara_relationship_record TO data_plane_builder;
GRANT DELETE ON public.ka_gochara_contact TO data_plane_builder;
GRANT UPDATE (admission_state) ON public.ka_gochara_relationship_record TO data_plane_builder;
GRANT UPDATE (result) ON public.ka_gochara_record_prerequisite TO data_plane_builder;

-- Presence check: verify the grants are ACTUALLY held, and that nothing beyond the derived set is (§N.4 — never a grant to nobody).
DO $$
BEGIN
  IF NOT (has_table_privilege('data_plane_builder', 'public.ka_gochara_relationship_record', 'DELETE')
          AND has_table_privilege('data_plane_builder', 'public.ka_gochara_contact', 'DELETE')
          AND has_column_privilege('data_plane_builder', 'public.ka_gochara_relationship_record', 'admission_state', 'UPDATE')
          AND has_column_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'result', 'UPDATE')) THEN
    RAISE EXCEPTION 'migration 1242 post-apply check failed: the builder does not hold the record replace/finalise privileges';
  END IF;
  IF has_table_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'DELETE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_contact', 'UPDATE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_relationship_record', 'UPDATE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'UPDATE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_relationship_record', 'TRUNCATE')
     OR has_column_privilege('data_plane_builder', 'public.ka_gochara_relationship_record', 'record_id', 'UPDATE')
     OR has_column_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'record_id', 'UPDATE') THEN
    RAISE EXCEPTION 'migration 1242 post-apply check failed: the builder holds a record-table privilege beyond the derived set';
  END IF;
  RAISE NOTICE 'migration 1242: presence checks passed';
END;
$$;
