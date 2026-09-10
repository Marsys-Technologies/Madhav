-- 1015_nirmana_l4_ph_nimitta_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L4 (Phala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 1014 (ph_nimitta output_digest_spec) -- see that
-- migration's header for the full verified account of sole-writer
-- confirmation, the natural key, and the live NULL/rehearsal checks.
-- Declared per the DEP-ASSERT precedent (880/908/909/.../1012-1013):
-- `natural_key_partition` being NULL reads as `freshness_state='unknown'`
-- (reason `partition_undeclared`) regardless of writer exclusivity or build
-- success.

UPDATE asset_registry
   SET natural_key_partition = 'ph_nimitta writes exactly one table, phala_anchors, via a chart-scoped delete-then-insert (PhNimittaWriter, @register(''ph_nimitta'')). Sole-writer confirmed by tree-wide grep for INSERT/UPDATE/DELETE against phala_anchors (excluding tests): only ph_nimitta.py''s own delete-then-insert and run_ka_sangam_prod.py''s pre-delete (a standalone operator utility for ka_sangam reruns that only DELETEs anchor_source=''convergence'' rows to avoid an FK-cascade/unique-index conflict -- it never INSERTs into phala_anchors, and any orchestrator-driven build supersedes its effect with ph_nimitta''s own full rebuild). Natural key: anchor_id -- the table''s own PRIMARY KEY, computed deterministically by phala_anchor_identity() (migration 680, IMMUTABLE SQL function, uuid_v5 over chart_id/anchor_source/event_type/direction/domain/horizon_tier/window_start/peak_date/window_end/falsifier) called inline by the writer''s INSERT. Being the live PRIMARY KEY, it needs no fleet-wide duplicate check (structurally impossible) -- it is the strongest possible key declaration, stronger than the table''s secondary phala_anchors_natural_key UNIQUE constraint (which serves a different purpose, ON CONFLICT-safety against upstream FK churn, and omits several identity-bearing columns). anchor_id live-verified NOT NULL on every row via the real compute_output_digest NULL-reviewed-key preflight (migration 1014 rehearsal) -- no vacuous key candidacy. chart_id scoped via where_equals in the digest spec per the standard convention.'
 WHERE asset_id = 'ph_nimitta'
   AND natural_key_partition IS NULL;
