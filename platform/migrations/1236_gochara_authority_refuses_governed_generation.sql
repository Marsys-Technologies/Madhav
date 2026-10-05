-- Migration 1236: kala_gochara_authority REFUSES any governed ('5.x' and above) generation — a one-constraint guard.
-- Pravāha B6.0, steward M20261002T040210-923a (serving inventory C14), 2026-10-02. Author: pravaha stream B. STATUS: HOLD.
--
-- WHY
-- ═══
-- kala_gochara_authority (527) is the per-chart pointer that every serving path resolves through (the gochara MCP tools, kala_now_get /
-- kala_explain_get, gochara_contact_ledger_get, fetchGocharaSweep — Kimi's C14 inventory). It has a PRIMARY KEY and NOTHING ELSE: no
-- CHECK, no trigger. A row naming '5.0' would be served by all of them with NO code change — reading kala_gochara_WINDOWS, with no
-- stored_scope, no completeness state and no reader at all for ka_gochara_eval_window (what the '5.0' writer writes). Read-only
-- production check (2026-10-02): the table holds two rows, both '3.0'; role_orchestrator and data_plane_builder (the pipeline's login)
-- hold INSERT/UPDATE/DELETE on it; the only intended writer is the operator-run flip script (step08_flip.py). So today NOTHING in the
-- database prevents a governed generation from becoming authoritative — the flip (D-FLIP) is the native's decision and its serving
-- pre-conditions (an eval-window reader/projection + the mandatory scope constructor at one packaging point) do not exist.
--
-- WHAT THIS DOES
-- ══════════════
-- ONE CHECK constraint, kga_governed_generation_refused_ck: authoritative_generation must NOT match the governed pattern
-- '^([5-9]|[1-9][0-9]+)\.[0-9]+$' — the same pattern as ka_gochara_generation_governed (1153): the contract's 'governed generation' is
-- major >= 5. A CHECK (not a trigger) is deliberate: it needs no CREATE on schema public (so this is a ROUTINE migration — the owner
-- alters its own table), no function EXECUTE for any writer, it applies to every role including superusers, and session_replication_role
-- cannot bypass it. Legacy values ('v1', '2.0', '3.0', '4.0', '4.1') are unaffected.
-- THE RELAXATION IS AN EXPLICIT, REVIEWED ACT: a later migration drops/replaces this constraint when the serving pre-conditions are met and
-- the native decides the flip. It is never edited in place.
--
-- NOT CHANGED: any grant (the builder's write privilege on this table is a separate question — only the flip script writes it, but removing a
-- grant without proving no pipeline path depends on it is out of scope), any existing row, any reader.
-- Existing rows: the gate refuses to apply while a governed value is already present (none today).
-- Transaction ownership: NO BEGIN/COMMIT. ROLLBACK: DROP CONSTRAINT kga_governed_generation_refused_ck.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF to_regclass('public.kala_gochara_authority') IS NULL THEN
    RAISE EXCEPTION 'preflight 1236 BLOCKED: kala_gochara_authority_missing';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.kala_gochara_authority'::regclass
               AND conname = 'kga_governed_generation_refused_ck') THEN
    RAISE EXCEPTION 'preflight 1236 BLOCKED: migration_1236_already_applied';
  END IF;
  IF EXISTS (SELECT 1 FROM public.kala_gochara_authority WHERE authoritative_generation ~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$') THEN
    RAISE EXCEPTION 'preflight 1236 BLOCKED: a governed generation is already authoritative for a chart — resolve it first';
  END IF;
END;
$$;

ALTER TABLE public.kala_gochara_authority
  ADD CONSTRAINT kga_governed_generation_refused_ck
  CHECK (authoritative_generation !~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$');

COMMENT ON CONSTRAINT kga_governed_generation_refused_ck ON public.kala_gochara_authority IS
  '1236: a governed (major >= 5) generation can not be authoritative until its serving pre-conditions exist (an eval-window reader or governed projection + the mandatory scope constructor at one packaging point) and the native decides the flip (D-FLIP). Relax by a new reviewed migration, never in place.';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conrelid = 'public.kala_gochara_authority'::regclass
                   AND c.conname = 'kga_governed_generation_refused_ck' AND c.contype = 'c' AND c.convalidated) THEN
    RAISE EXCEPTION 'migration 1236 post-apply check failed: the constraint is absent or not validated';
  END IF;
  RAISE NOTICE 'migration 1236: presence checks passed';
END;
$$;
