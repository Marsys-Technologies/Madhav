-- 1071_kala_gochara_windows_generation_guard.sql
--
-- KĀLA (L3) PRE-ELEVATION, Phase 1.1 / B1 — Strategy W0, "make the programme safe".
-- Restore a DATABASE-level guard over the never-rebuildable gochara snapshot.
--
-- WHY
-- ---
-- `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §4: "ka_gochara_sweep remains retired,
-- snapshot-protected and never rebuildable." Migration 588 (2026-08-23, native
-- instruction) dropped the only database enforcement of that ruling — the migration-540
-- row/TRUNCATE triggers and the migration-566 gen-3.0 trigger — and emptied
-- `build_protected_assets`. Measured live on production 2026-09-22, immediately before
-- authoring this file:
--
--   kala_gochara_windows  generation='v1'   38,287 rows over 3 charts
--                                           (1c826d5a… 19,323 · 482012f1… 16,297 ·
--                                            cb73cd3d… 2,667)
--   kala_gochara_windows  generation='3.0'   1,830 rows over 2 charts
--   build_protected_assets                        0 rows, every chart
--   non-internal triggers on ANY kala_* table     0
--     (positive control: 130 non-internal triggers exist in `public`, so the
--      measurement is a real zero, not a query that finds nothing anywhere)
--
-- The v1 rows have NO registered writer: `@register` was removed from
-- `writers/ka_gochara_sweep.py` at retirement, which migration 588's own STANDING
-- CAUTION records — "the build system CANNOT regenerate them. The snapshot above is
-- their only recovery path." A DELETE of those rows is unrecoverable from inside the
-- product.
--
-- WHAT THIS GUARD COVERS, AND WHY EXACTLY THAT
-- --------------------------------------------
-- COVERED — `generation='v1'` DELETE/UPDATE, unconditionally, for EVERY chart_id:
--   * No legitimate writer exists, so the guard's false-positive rate is structurally
--     zero: there is no build path it can break.
--   * It is deliberately NOT keyed on a `build_protected_assets` row. Migration 540's
--     guard was, and was therefore fail-OPEN for any chart absent from the registry —
--     which is not hypothetical: chart cb73cd3d… ("Kiran Shenoy") holds 2,667 v1 rows
--     and was never seeded into `build_protected_assets` by 540 or 566. A corpus that
--     cannot be rebuilt must fail closed by default, including for charts created after
--     this migration.
--
-- COVERED — TRUNCATE, unconditionally (statement level):
--   A TRUNCATE has no per-row OLD to test and is always generation-blind, so the
--   row-level rule cannot see it. It is refused outright.
--
-- NOT COVERED — a `generation='3.0'`-pinned DELETE/UPDATE:
--   `ka_gochara_v3_century_materialize` is the LIVE, LEGITIMATE writer of the gen-3.0
--   production rows, and its idempotent rebuild is literally
--   `DELETE FROM kala_gochara_windows WHERE … generation='3.0' …`
--   (writers/ka_gochara_v3_century_materialize.py:2257; INSERT at :540). Blocking that
--   is precisely Defect D-02 — the reason migration 588 removed the protection in the
--   first place ("The trigger could not tell a legitimate write from a destructive one,
--   and left that writer in a permanent BUILD-PROTECTED error"). 588's own closing
--   instruction is the design this migration follows: "If protection is ever reinstated,
--   key it on (table, generation) rather than asset_id, so it cannot again block the
--   writer it is meant to protect."
--
--   Gen-3.0 rows are nevertheless protected from GENERATION-BLIND destruction, which is
--   the failure mode the W0 field-contract register's fence 2 names ("protected sweep v1
--   and century v3 rows coexist in kala_gochara_windows; generation-blind mutation is
--   forbidden"): a statement with no `generation` predicate sweeps v1 rows too, so the
--   v1 rule aborts the whole statement before any row is removed. That transitive
--   coverage rests on a MEASURED fact, not a structural one — both charts holding
--   gen-3.0 rows also hold v1 rows (above) — and this migration states it as such rather
--   than claiming a protection it does not enforce (CLAUDE.md §N.8). TRUNCATE, the one
--   generation-blind statement that would bypass the row rule, is separately refused.
--
-- OVERRIDE
-- --------
-- `SET LOCAL app.allow_protected_sweep_rewrite = 'on'` — deliberately the SAME
-- per-session, non-default GUC migrations 540/566 established and that operator
-- runbooks and `tests/integration/build_protected_assets_sweep_guard.db.test.ts`
-- already know. A new name would strand that vocabulary. INSERT is never gated.
--
-- WHAT THIS MIGRATION DOES NOT DO
-- -------------------------------
--   * It does not touch migration 566, the origin of the century BUILD-PROTECTED guard,
--     nor re-create 566's trigger; 566 is not this migration's to reopen.
--   * It does not alter `kala_gochara_windows`'s schema, its rows, or any index.
--   * It does not re-create migration 540's asset_id-keyed trigger functions (dropped by
--     588). This guard is generation-keyed, per 588's instruction.
--
-- AUTHORITY / SAFETY
-- ------------------
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021); 1071 verified free in BOTH
-- `platform/migrations/` and `platform/supabase/migrations/` (max in either = 1070),
-- which `platform/scripts/migrate.ts:832-835` reads as one numeric sequence.
--
-- IDEMPOTENT: CREATE OR REPLACE FUNCTION + DROP TRIGGER IF EXISTS/CREATE TRIGGER, so a
-- re-run is a clean no-op rebuild of the same definitions. Proven by applying this file
-- twice against a disposable Postgres (see PHASE1_1_B1_CLOSURE.md).
--
-- lock_timeout: `kala_gochara_windows` is a live table with an active writer. CREATE
-- TRIGGER takes a brief ACCESS EXCLUSIVE lock, and Postgres's FIFO lock queue means every
-- later query would queue behind a blocked DDL. `SET LOCAL lock_timeout` aborts cleanly
-- instead — the same hardening migrations 540/566 applied.

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── Row-level guard: generation='v1' is untouchable ──────────────────────────

CREATE OR REPLACE FUNCTION kala_gochara_windows_generation_guard_row()
RETURNS TRIGGER AS $$
BEGIN
  -- `true` as the second arg to current_setting means "missing_ok": an unset GUC
  -- reads NULL rather than raising, so an ordinary session that never opted in
  -- takes the guarded path instead of erroring on the lookup itself.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  IF OLD.generation = 'v1' THEN
    RAISE EXCEPTION
      'BUILD-PROTECTED: kala_gochara_windows generation=''v1'' row(s) for chart_id % '
      'are the retired ka_gochara_sweep snapshot — % is refused. These rows have NO '
      'registered writer and cannot be rebuilt (migration 588 STANDING CAUTION). Set '
      'app.allow_protected_sweep_rewrite=on for this transaction to override (native '
      'decision required).',
      OLD.chart_id, TG_OP;
  END IF;

  -- Every other generation — including the gen-3.0 production rows the century
  -- materializer legitimately DELETE-then-INSERTs — passes untouched. This branch
  -- is what makes the guard's PASS an earned signal rather than a blanket refusal:
  -- there is a real statement that reaches it and is allowed through.
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION kala_gochara_windows_generation_guard_row() IS
  'Kāla B1 (migration 1071): BEFORE DELETE/UPDATE row guard on '
  'kala_gochara_windows. Refuses any mutation of a generation=''v1'' row — the '
  'retired, never-rebuildable ka_gochara_sweep snapshot — for EVERY chart_id, '
  'with no dependence on a build_protected_assets row (migration 540''s guard '
  'was registry-keyed and therefore fail-open for unlisted charts). Other '
  'generations pass, so ka_gochara_v3_century_materialize''s generation-pinned '
  'gen-3.0 rebuild is not blocked (Defect D-02, migration 588). Override with '
  'SET LOCAL app.allow_protected_sweep_rewrite=''on''. INSERT is never gated.';

DROP TRIGGER IF EXISTS trg_kala_gochara_windows_generation_guard_row ON kala_gochara_windows;
CREATE TRIGGER trg_kala_gochara_windows_generation_guard_row
  BEFORE DELETE OR UPDATE ON kala_gochara_windows
  FOR EACH ROW EXECUTE FUNCTION kala_gochara_windows_generation_guard_row();

-- ── Statement-level guard: TRUNCATE is always generation-blind ───────────────

CREATE OR REPLACE FUNCTION kala_gochara_windows_generation_guard_truncate()
RETURNS TRIGGER AS $$
BEGIN
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN NULL;
  END IF;

  RAISE EXCEPTION
    'BUILD-PROTECTED: kala_gochara_windows cannot be TRUNCATEd. A TRUNCATE has no '
    'per-row generation to test and would destroy the retired ka_gochara_sweep '
    'generation=''v1'' snapshot along with every other generation. Delete with an '
    'explicit generation predicate instead, or set '
    'app.allow_protected_sweep_rewrite=on for this transaction (native decision '
    'required).';

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION kala_gochara_windows_generation_guard_truncate() IS
  'Kāla B1 (migration 1071): BEFORE TRUNCATE statement guard on '
  'kala_gochara_windows. TRUNCATE is unconditionally generation-blind, so the '
  'row-level generation rule cannot see it; it is refused outright unless '
  'app.allow_protected_sweep_rewrite=''on'' is set for the transaction.';

DROP TRIGGER IF EXISTS trg_kala_gochara_windows_generation_guard_truncate ON kala_gochara_windows;
CREATE TRIGGER trg_kala_gochara_windows_generation_guard_truncate
  BEFORE TRUNCATE ON kala_gochara_windows
  FOR EACH STATEMENT EXECUTE FUNCTION kala_gochara_windows_generation_guard_truncate();

-- ── Fail closed if the guard did not actually install ───────────────────────
-- A silent no-op must not pass as applied (CLAUDE.md §N.8). Each check below can
-- genuinely read false: drop either trigger and this block raises.

DO $$
DECLARE
  missing text := '';
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
     WHERE c.relname = 'kala_gochara_windows'
       AND t.tgname  = 'trg_kala_gochara_windows_generation_guard_row'
       AND NOT t.tgisinternal
  ) THEN missing := missing || ' row-trigger'; END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
     WHERE c.relname = 'kala_gochara_windows'
       AND t.tgname  = 'trg_kala_gochara_windows_generation_guard_truncate'
       AND NOT t.tgisinternal
  ) THEN missing := missing || ' truncate-trigger'; END IF;

  IF to_regprocedure('public.kala_gochara_windows_generation_guard_row()') IS NULL
    THEN missing := missing || ' row-function'; END IF;
  IF to_regprocedure('public.kala_gochara_windows_generation_guard_truncate()') IS NULL
    THEN missing := missing || ' truncate-function'; END IF;

  IF missing <> '' THEN
    RAISE EXCEPTION 'migration 1071 did not take effect; still missing:%', missing;
  END IF;
END $$;

-- Behavioural self-test: prove the guard actually REFUSES, not merely that the
-- catalog rows exist. An installed-but-inert trigger would pass the checks above
-- (that was §N.8 instance 3's exact shape); this block makes the migration's own
-- PASS depend on the refusal firing. Runs only when at least one v1 row exists;
-- when none does, it says so rather than reporting a check it never ran.
DO $$
DECLARE
  probe_chart uuid;
  refused     boolean := false;
BEGIN
  SELECT chart_id INTO probe_chart
    FROM kala_gochara_windows WHERE generation = 'v1' LIMIT 1;

  IF probe_chart IS NULL THEN
    RAISE NOTICE 'migration 1071: no generation=''v1'' row present; refusal self-test '
                 'NOT RUN (honest skip, not a pass)';
    RETURN;
  END IF;

  BEGIN
    -- Inside a nested block so the expected failure rolls back to here, not to
    -- the whole migration. `WHERE false` on the id keeps this a no-op even in the
    -- impossible case that it is permitted.
    UPDATE kala_gochara_windows
       SET valence = valence
     WHERE chart_id = probe_chart AND generation = 'v1'
       AND id = (SELECT MIN(id) FROM kala_gochara_windows
                  WHERE chart_id = probe_chart AND generation = 'v1');
  EXCEPTION WHEN raise_exception THEN
    -- Only OUR refusal counts. Any other raise_exception (a constraint, a
    -- different trigger) must not be mistaken for the guard working.
    IF SQLERRM LIKE '%BUILD-PROTECTED%' THEN
      refused := true;
    ELSE
      RAISE;
    END IF;
  END;

  IF NOT refused THEN
    RAISE EXCEPTION
      'migration 1071 self-test FAILED: a generation=''v1'' UPDATE was permitted; '
      'the guard is installed but inert';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   DROP TRIGGER IF EXISTS trg_kala_gochara_windows_generation_guard_truncate ON kala_gochara_windows;
--   DROP TRIGGER IF EXISTS trg_kala_gochara_windows_generation_guard_row      ON kala_gochara_windows;
--   DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_truncate();
--   DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_row();
--   COMMIT;
-- kala_gochara_windows itself, its schema and its rows are untouched by both this
-- migration and its DOWN: this file only ever adds protection around that table.
-- =============================================================================
