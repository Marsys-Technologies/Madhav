-- Migration 1390: narrow reads for the separate whole-layer verifier operation.
-- Created: 2026-10-16. K9-23 pre-build, SR-A4-01; no production application.
-- Allocated to K9-23 in /Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json.
-- Idempotent grants only: no schema privileges, writes, or ownership changes.
-- Existing 1330/1334 grants retain exclusive receipt INSERT/conflict-key reads.
GRANT SELECT (chart_id, generation, build_id, expected_head_generation, state, conventions)
ON TABLE public.kala_layer_candidate TO verifier_principal;

GRANT SELECT (id, chart_id, scope, scope_target, action, plan, state, plan_manifest, plan_manifest_digest)
ON TABLE public.build_runs TO verifier_principal;
