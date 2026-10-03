-- Migration 1220: grant data_plane_builder EXECUTE on exactly the 1153–1157
-- contract functions its governed writes reach, plus the one read it needs on
-- the generation-seal table.
-- Pravāha B / steward M20261001T224443-bfc4 (2026-10-02). Author: pravaha stream B.
--
-- WHY THIS EXISTS (the 1216 gap)
-- ══════════════════════════════
-- Migration 1216 granted data_plane_builder the TABLE privileges the governed
-- gochara writers need. It did not (and by itself cannot) grant EXECUTE on the
-- contract FUNCTIONS. In production every function created by amjis_app has
-- PUBLIC EXECUTE revoked by default (the governed bootstrap issues
--   ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC
-- — platform/scripts/nirmana-evidence-ownership-preflight.ts:259), and verified
-- read-only against production: the builder can EXECUTE none of the 42
-- ka_gochara_* functions created by 1153–1157. Every governed write therefore
-- stops at 'permission denied for function …' before it reaches a table:
--   * the chart/global lock helpers the writers call first;
--   * the CHECK-constraint functions PostgreSQL evaluates AS THE INVOKER on
--     every INSERT (a CHECK that calls a function the inserter cannot execute
--     fails the INSERT);
--   * the helpers the invoker-security guard triggers call from inside their
--     bodies. (A trigger FUNCTION itself needs no EXECUTE at fire time —
--     PostgreSQL checks only the table's TRIGGER privilege at CREATE TRIGGER —
--     so the 15 trigger functions on in-scope tables are deliberately NOT
--     granted.)
-- The earlier 1216 live suite did not catch this because it created the objects
-- as the superuser, whose functions keep PUBLIC EXECUTE — the mirror was not
-- deployment-faithful. The sibling suite for THIS migration builds the schema
-- the way production does (see the test header).
--
-- DERIVATION — each grant below is justified by a reachable call, nothing more
-- ═══════════════════════════════════════════════════════════════════════════
-- Method: (1) static closure — the CHECK-constraint functions on the in-scope
-- tables, plus every ka_gochara_* function called from the body of a trigger on
-- an in-scope table, closed transitively over function bodies; (2) empirical
-- confirmation — the builder-mirror's write sequence (convention, bridge,
-- physical object, contact identity, ledger rows, registry rows, contact,
-- relationship record, record prerequisite) was run against the
-- deployment-faithful schema, adding one EXECUTE at a time on each
-- 'permission denied for function X'; the loop converged on EXACTLY the 18
-- functions of the static closure, and one further 'permission denied for
-- table ka_gochara_generation_seal' (below). The sibling suite re-proves that
-- each of the 18 is individually necessary (revoking any one breaks a write).
--
-- Lock helpers (called by the writer, and by guard triggers):
--   ka_gochara_lock_chart            chart EXCLUSIVE key; the writer takes it first
--   ka_gochara_lock_global           global EXCLUSIVE key; registry construction
--   ka_gochara_lock_global_shared    global SHARED key; the record-time
--                                    require-sealed-rule-path guard
-- Generation helpers:
--   ka_gochara_generation_is_sealed  called by the contact and chart write guards
--   ka_gochara_generation_governed   CHECK kgc_/kgrr_/kgrpr_generation_governed_ck
--                                    (contact, relationship_record, record_prerequisite)
-- Coverage helpers (record-time coverage guard):
--   ka_gochara_coverage_facts        record-time coverage guard (and the writer's own
--                                    facts snapshot); calls horizon_finite_ok
--   ka_gochara_horizon_finite_ok     coverage_facts / intervals_ok
-- CHECK-constraint predicates evaluated at INSERT:
--   ka_gochara_finite_nonneg_ok      contact, sky_event, relationship_record
--   ka_gochara_finite_ok             relationship_record, factor
--   ka_gochara_frame_ok              relationship_record, rule_path
--   ka_gochara_intervals_ok          relationship_record (kgrr_support_intervals_ck)
--   ka_gochara_precision_ok          relationship_record (kgrr_precision_typed_ck)
--   ka_gochara_string_array_ok       factor, relationship_record, and via vocab_array_ok
--   ka_gochara_vocab_array_ok        rule_path
--   ka_gochara_named_operands_ok     predicate, factor
--   ka_gochara_selector_token_ok     via named_operands_ok
--   ka_gochara_object_selector_consistent_ok  rule_path
--   ka_gochara_object_selector_ok    via object_selector_consistent_ok
--
-- DELIBERATELY NOT GRANTED (24 of the 42), with the reason
-- ═══════════════════════════════════════════════════════
--   ka_gochara_seal_generation       the generation seal is a flip-time act (D-FLIP
--                                    is the native's); the builder never seals.
--   ka_gochara_coverage_drift, _membership_violation(s), _facts_horizon,
--   ka_gochara_text_array_ok         seal-time / eval-window-side verifiers; no
--                                    in-scope builder write reaches them.
--   the 15 trigger functions on in-scope tables, and the 3 on the DEFERRED
--   tables (generation_seal, eval_window, eval_window_record) — no EXECUTE is
--   needed to fire a trigger.
--
-- ONE TABLE READ THE FUNCTIONS NEED — SELECT on ka_gochara_generation_seal
-- ═══════════════════════════════════════════════════════════════════════
-- ka_gochara_generation_is_sealed runs as the INVOKER and reads
-- ka_gochara_generation_seal (invoked from the contact and chart write guards on
-- every contact/record INSERT). 1216 correctly withheld WRITE on the seal table;
-- it also, by omission, withheld the READ — so even with EXECUTE granted, the
-- write guard dies with 'permission denied for table ka_gochara_generation_seal'
-- (reproduced). SELECT only is granted here: it reveals which generations are
-- sealed (a fact the builder must already respect), and INSERT/UPDATE/DELETE
-- stay withheld, so the builder/sealer separation is unchanged. This is NOT
-- done by making the function SECURITY DEFINER: that would be CREATE OR REPLACE
-- of a frozen 1155 function (protected object window) for no gain.
--
-- WINDOW — ROUTINE, NOT PROTECTED
-- ═══════════════════════════════
-- This migration creates, alters and drops no object; it only GRANTs on existing
-- objects, all of which amjis_app (the routine runner's role,
-- validate-migration-database-routes.ts) owns, so every statement is issued by
-- the owner. It is therefore NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
-- (platform/scripts/migrate.ts) — same classification as 1216. Idempotent:
-- GRANT of an already-held privilege is a no-op.
--
-- NO ALLOWLIST DRIFT: none of these functions or the seal table appears in the
-- ownership-preflight allowlists (verified as for 1216).

-- Lock helpers
GRANT EXECUTE ON FUNCTION public.ka_gochara_lock_chart(uuid) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_lock_global() TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_lock_global_shared() TO data_plane_builder;
-- Generation helpers
GRANT EXECUTE ON FUNCTION public.ka_gochara_generation_is_sealed(uuid, text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_generation_governed(text) TO data_plane_builder;
-- Record-time coverage helpers
GRANT EXECUTE ON FUNCTION public.ka_gochara_coverage_facts(text, tstzrange, text[]) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_horizon_finite_ok(tstzrange) TO data_plane_builder;
-- CHECK-constraint predicates (evaluated as the invoker on INSERT)
GRANT EXECUTE ON FUNCTION public.ka_gochara_finite_nonneg_ok(double precision) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_finite_ok(double precision) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_frame_ok(text, text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_intervals_ok(tstzrange[]) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_precision_ok(jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_string_array_ok(jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_vocab_array_ok(jsonb, text[]) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_named_operands_ok(jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_selector_token_ok(text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_object_selector_consistent_ok(jsonb, jsonb, jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_object_selector_ok(jsonb) TO data_plane_builder;

-- The one table READ the invoker-security write guards need (see header).
GRANT SELECT ON public.ka_gochara_generation_seal TO data_plane_builder;
