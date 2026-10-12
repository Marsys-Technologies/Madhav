-- 1074_data_plane_builder_explicit_session_timeouts.sql
--
-- Give `data_plane_builder` an EXPLICIT, deliberate server-side session bound. It has none
-- today: not a tighter one, not a looser one — none at all.
--
-- THE MEASURED STATE (live, read-only as `amjis_app`, 2026-09-22)
-- ---------------------------------------------------------------
--   SELECT rolname, rolconfig FROM pg_roles WHERE rolname IN (...);
--     amjis_app           -> {idle_in_transaction_session_timeout=600s, statement_timeout=1800s}
--     data_plane_builder  -> NULL          <-- no rolconfig at all
--
--   Cluster defaults (pg_settings.boot_val), PostgreSQL 15.18:
--     idle_in_transaction_session_timeout -> 0   (disabled)
--     statement_timeout                   -> 0   (disabled)
--
--   `data_plane_builder` also holds ZERO role memberships, so it inherits no other role's
--   settings either. A NEW builder connection that issues no SET of its own therefore runs
--   with BOTH killers disabled. That is the gap this closes.
--
-- WHY THIS IS NOT "COPY amjis_app"
-- --------------------------------
-- The most probable cause of `ka_kshetra`'s recorded failure —
--   asset_throughput: ka_kshetra / 482012f1-…, state='error',
--   last_error='worker_crash: OperationalError: the connection is lost',
--   last_built_at = 2026-09-11 03:31:31Z  (verified live at the authority)
-- — is precisely `amjis_app`'s 600 s idle-in-transaction killer. That run predates the
-- identity cutover (migrations 1035/1036, 2026-09-18) by a week, so it ran as `amjis_app`.
-- `pipeline/orchestrator/db.py:46-70` documents why 600 s is fatal there: the orchestrator
-- holds a transaction open while a writer does CPU-heavy work, and "legitimately slow
-- ayanamsha substeps (up to ~20 min of pure CPU with no DB traffic)" must survive. 1200 s of
-- CPU against a 600 s idle killer is a 2x overrun — the crash is the expected outcome, not a
-- surprise.
--
-- The new identity removes that failure mode and introduces the opposite one: an unattended
-- hung build with no server-side bound whatsoever. Copying `amjis_app`'s 600 s/1800 s would
-- re-import the exact bug that killed the 2026-09-11 run. A bound that kills a legitimate
-- build is worse than no bound; a bound that never fires is not a bound. Hence deliberate,
-- separately-derived values.
--
-- WHY THE TWO GUCs NEED DIFFERENT VALUES — the crux
-- --------------------------------------------------
-- They measure different things, and the orchestrator's own execution shape puts its worst
-- case squarely in one of them and nowhere near the other:
--
--   `idle_in_transaction_session_timeout` bounds time spent INSIDE AN OPEN TRANSACTION WITH NO
--   STATEMENT RUNNING. A long CPU-bound Python substep is exactly this: the writer's last
--   statement has RETURNED, the transaction is still open, and from the server's point of view
--   the session is idle while Python computes. The ~20-minute pure-CPU ayanamsha substep is a
--   1200-second IDLE gap, not a 1200-second statement. This GUC is the one that must clear it.
--
--   `statement_timeout` bounds the execution of a SINGLE STATEMENT. Python CPU time is not
--   counted — the statement already finished. It never sees the 20-minute gap at all. What it
--   must clear is the longest single SQL statement a sanctioned build may legitimately issue.
--
-- Proven on a disposable PostgreSQL 15.17 (same major version as production) before choosing
-- the values; all four cells reproduced, output recorded in
-- 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/PHASE1_2_3_GRANTS_AND_TIMEOUT.md:
--
--                              | ACTIVE 5 s statement | 5 s client-side idle gap in txn
--   idle_in_txn = 2s           | SURVIVES             | KILLED   (FATAL, 25P03)
--   statement_timeout = 2s     | KILLED (57014)       | SURVIVES
--
-- Getting this backwards is how a build dies: a 600 s `statement_timeout` would NOT have
-- protected the 2026-09-11 run, and a 600 s idle bound is what killed it.
--
-- THE VALUES, AND WHAT EACH IS JUSTIFIED AGAINST
-- ----------------------------------------------
-- idle_in_transaction_session_timeout = 1800s (30 min)
--   * Floor: must exceed the documented ~20 min (1200 s) pure-CPU substep gap
--     (db.py:46-70). 600 s does not — that is the 2026-09-11 failure mode, excluded by
--     construction. 1800 s clears it with 1.5x headroom.
--   * Ceiling: finite, so a genuinely wedged connection auto-recovers instead of requiring
--     manual `pg_terminate_backend` (the S7459 finding db.py:8-10 records against the prior
--     `= 0`). 30 min after the last statement, with no statement in flight, is a hang.
--   * Chosen to be EXACTLY the value the orchestrator already sets for itself
--     (db.py:62 `options=`, db.py:75 explicit `SET`; likewise run_ka_sangam_prod.py:49 and
--     run_ph_pratikara_prod.py:48). That is the point: a connection whose SET is stripped or
--     never issued degrades to the SAME bound the orchestrator intended, rather than to
--     today's unbounded 0. No build behaviour changes; the floor stops being absent.
--
-- statement_timeout = 86400s (24 h)
--   * Floor: it must never be tighter than the largest budget the system itself sanctions.
--     `asset_registry.writer_timeout_seconds` for `ka_kshetra` is 86,400 — the maximum across
--     all 129 assets carrying a value (verified live) — and it is READ BY A LIVE DETECTOR at
--     `pipeline/orchestrator/runner.py:741`, which builds `timeouts_of` from that column for
--     the per-asset watchdog. A server-side bound below 86,400 would let the server kill a
--     build the registry and the live watchdog both authorize. That contradiction is the
--     "kills a legitimate build" failure mode, so 86,400 is a floor, not a preference.
--   * Real measured worst case is well inside it: `ka_kshetra` ~7.5 h. 24 h is ~3.2x that —
--     and 7.5 h is the whole multi-statement asset, so the longest SINGLE statement is far
--     smaller again.
--   * It still fires. Today the value on this role is 0: a wedged statement on a bypass path
--     runs FOREVER. This converts "forever" into "at most one day", which is the only claim
--     made for it. It is deliberately the OUTER backstop — looser than every inner detector
--     (the per-asset watchdog at runner.py:741, and `lock_timeout='300s'` at db.py:79) — and
--     is the last line, not the first.
--
-- HONEST SCOPE — what this does NOT bound
-- ---------------------------------------
-- `pipeline/orchestrator/db.py:75-76` issues `SET idle_in_transaction_session_timeout =
-- 1800000` and `SET statement_timeout = 0` as REAL STATEMENTS on every connection from
-- `connect()`, and `runner.py`'s `worker()` gives every asset a dedicated `connect()`
-- connection. A session-level SET beats a role default. So for an orchestrator build session
-- that reaches those SETs, this migration changes nothing at all — the idle bound is already
-- the same 1800 s, and `statement_timeout` is deliberately 0 there. It must not be claimed
-- that this bounds those sessions.
--
-- What it genuinely covers, all verified in source at this commit:
--   * The pre-SET window. db.py:62-76 states in-file that the `options=` startup parameter is
--     NOT guaranteed to survive a pooler ("a local Cloud SQL Auth Proxy — or any intermediate
--     pooler — may not forward arbitrary libpq startup options"). Between connect and the
--     explicit SETs, the role default is the only bound in force.
--   * Build paths that set only SOME of the GUCs. `run_ka_sangam_prod.py:49` and
--     `run_ph_pratikara_prod.py:48` are production build runners on bare `psycopg.connect()`
--     that set `idle_in_transaction_session_timeout` and NOT `statement_timeout` (they only
--     read it, for the smoke-log, at :54 / :53). Those sessions are unbounded on statements
--     today.
--   * Build paths that set NEITHER: `run_bo_samskara_parallel.py:86`,
--     `backfill_missing_signal_embeddings.py:37,:68,:119`, `pipeline/brahma_pipeline.py:52`.
--   * psql / ad-hoc / cron sessions authenticating as `data_plane_builder`, and any future
--     runner that forgets the factory — the exact recurrence class MR-39 already had to fix
--     once (db.py:10-18).
--
-- DELIBERATELY NOT SET
-- --------------------
--   * `lock_timeout`. `connect()` sets '300s' per session (db.py:79) with a specific rationale
--     ("blocked on a lock for more than 5 minutes is a hang"). A ROLE-level 300 s would also
--     apply to migration/maintenance sessions run under this identity, where a legitimate lock
--     wait behind a long transaction can exceed 5 minutes; and lock-wait hangs are not the
--     failure mode this item names. Left to the session that has the context to choose it.
--   * `transaction_timeout` — PostgreSQL 17+; production is 15.18 (verified live). Not
--     available.
--   * No change to `amjis_app`, whose 600 s/1800 s stay as they are — narrowing or widening
--     the serving role is a different decision with a different blast radius.
--   * No credential change, no role attribute change, no membership grant. In particular this
--     does NOT put `data_plane_builder` into `role_orchestrator` (which would hand it that
--     role's full DML on every table at once); the zero-membership topology is preserved.
--
-- PRIVILEGE PRECONDITION — THIS MIGRATION NEEDS A DBA PREFLIGHT (read this before deploying)
-- ------------------------------------------------------------------------------------------
-- `ALTER ROLE <other role> SET ...` is not a table privilege. In PostgreSQL 15 it requires
-- SUPERUSER or CREATEROLE on the executing role; role membership, even WITH ADMIN OPTION, does
-- NOT confer it (all three cases reproduced on the disposable PG 15.17 — see the deliverable
-- doc). Measured live on production, 2026-09-22:
--
--   rolname             rolsuper  rolcreaterole
--   amjis_app           f         f          <-- the migration runner
--   data_plane_builder  f         f
--   postgres            f         t
--   cloudsqlsuperuser   f         t
--
-- and `amjis_app` holds no role memberships. So `amjis_app` CANNOT apply the two ALTER ROLE
-- statements below. Migration 241 (`ALTER ROLE amjis_app SET idle_in_transaction_session_
-- timeout = '120s'`) is not a counter-example: a role may always alter ITSELF, which is a
-- different permission check — confirmed by direct test.
--
-- This migration therefore declares that requirement explicitly and FAILS LOUDLY rather than
-- landing green having changed nothing (CLAUDE.md §N.8; the same DBA-preflight shape migrations
-- 1035/1036 already use for `E1035_PREFLIGHT_EXTENSION`). Before the deploy that carries 1074,
-- a role with CREATEROLE (`postgres` or `cloudsqlsuperuser`) must run ONE of:
--
--   -- either: let the ordinary runner apply it
--   ALTER ROLE amjis_app CREATEROLE;              -- widens amjis_app; needs a native ruling
--   -- or (preferred): apply the two statements directly as the privileged role
--   ALTER ROLE data_plane_builder SET idle_in_transaction_session_timeout = '1800s';
--   ALTER ROLE data_plane_builder SET statement_timeout = '86400s';
--   -- then re-run the deploy; 1074's verification block will pass and record it as applied.
--
-- Either path leaves the verification block below as the thing that decides whether the
-- migration may be called applied. Doing it by hand and skipping the migration is not an
-- option: then nothing records that it happened.
--
-- AUTHORITY / SAFETY
-- ------------------
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021); 1074 is inside it and free in BOTH
-- migration directories, which platform/scripts/migrate.ts:832-835 reads as ONE numeric
-- sequence. `ALTER ROLE ... SET` is naturally idempotent and this migration is re-runnable. It
-- affects only NEW connections; sessions already open are untouched.

BEGIN;

-- Preflight: can this session actually perform the ALTER ROLE below? If not, fail with an
-- actionable error instead of an opaque bare "permission denied" 20 lines later.
DO $$
DECLARE
  can_admin boolean;
BEGIN
  SELECT (rolsuper OR rolcreaterole) INTO can_admin FROM pg_roles WHERE rolname = current_user;
  IF NOT coalesce(can_admin, false) THEN
    RAISE EXCEPTION
      'E1074_PREFLIGHT_ROLE_ADMIN: current_user=% has neither SUPERUSER nor CREATEROLE, so it '
      'cannot ALTER ROLE data_plane_builder (PG15: role membership, even WITH ADMIN OPTION, '
      'does not confer this). A privileged role must first run either '
      '"ALTER ROLE % CREATEROLE;" or, preferred, the two ALTER ROLE data_plane_builder SET '
      'statements this migration contains. See the PRIVILEGE PRECONDITION header of migration '
      '1074.', current_user, current_user;
  END IF;
END $$;

-- Clears the documented ~20-minute pure-CPU substep (db.py:46-70) with 1.5x headroom; finite
-- so a wedged connection auto-recovers. Identical to the value connect() sets for itself.
ALTER ROLE data_plane_builder SET idle_in_transaction_session_timeout = '1800s';

-- Outer backstop only: never tighter than the largest sanctioned writer budget
-- (asset_registry.writer_timeout_seconds max = 86400, read live at runner.py:741), finite so
-- nothing runs forever on a path that sets no statement_timeout of its own.
ALTER ROLE data_plane_builder SET statement_timeout = '86400s';

-- Fail closed if the ALTER ROLE did not take effect, so a silent no-op cannot pass as applied
-- (CLAUDE.md §N.8). Read back from pg_roles rather than from this session's own GUCs — this
-- session is NOT `data_plane_builder`, and `current_setting()` here would report the migration
-- runner's settings, which is precisely the proxy-instead-of-claim defect §N.8 warns about.
--
-- The checks assert the INVARIANT each value was chosen for, not the literal string. An
-- earlier draft asserted `idle = '1800s'` exactly AND, after that, that it cleared the 1200 s
-- floor — which made the floor check unreachable dead code: no value could ever reach it and
-- fail. That is the §N.8 defect this file's own header lectures about, so it was removed.
-- What survives is reachable in both directions: absence fails, and a value that violates the
-- floor fails (both reproduced by mutation on the disposable PG — see the deliverable doc).
DO $$
DECLARE
  cfg   text[];
  idle  text;
  stmt  text;
BEGIN
  SELECT rolconfig INTO cfg FROM pg_roles WHERE rolname = 'data_plane_builder';
  IF cfg IS NULL THEN
    RAISE EXCEPTION 'migration 1074 did not take effect: data_plane_builder still has no rolconfig';
  END IF;

  SELECT split_part(c, '=', 2) INTO idle
    FROM unnest(cfg) c WHERE c LIKE 'idle_in_transaction_session_timeout=%';
  SELECT split_part(c, '=', 2) INTO stmt
    FROM unnest(cfg) c WHERE c LIKE 'statement_timeout=%';

  IF idle IS NULL THEN
    RAISE EXCEPTION 'migration 1074 did not take effect: idle_in_transaction_session_timeout absent from rolconfig';
  END IF;
  IF stmt IS NULL THEN
    RAISE EXCEPTION 'migration 1074 did not take effect: statement_timeout absent from rolconfig';
  END IF;

  -- Invariant 1 — the idle bound must CLEAR the documented ~20 min (1200 s) pure-CPU substep
  -- (pipeline/orchestrator/db.py:46-70). amjis_app's 600 s does not; adopting it here would
  -- re-import the 2026-09-11 `ka_kshetra` worker_crash. This is the check that makes the
  -- number defensible rather than arbitrary.
  IF (idle::interval) <= interval '1200 seconds' THEN
    RAISE EXCEPTION
      'migration 1074: idle_in_transaction_session_timeout=% does not clear the documented '
      '~20 min (1200s) pure-CPU substep (pipeline/orchestrator/db.py:46-70); 600s is the '
      '2026-09-11 ka_kshetra worker_crash failure mode', idle;
  END IF;

  -- Invariant 2 — the statement bound must never be TIGHTER than the largest budget the system
  -- itself sanctions (max asset_registry.writer_timeout_seconds = 86400, ka_kshetra, read live
  -- by the detector at pipeline/orchestrator/runner.py:741). A tighter server-side bound would
  -- let the server kill a build the registry and the live watchdog both authorize.
  IF (stmt::interval) < interval '86400 seconds' THEN
    RAISE EXCEPTION
      'migration 1074: statement_timeout=% is tighter than the largest sanctioned writer '
      'budget (asset_registry.writer_timeout_seconds max = 86400s, read at runner.py:741)', stmt;
  END IF;

  -- (There is deliberately no separate "is it 0?" check: '0'::interval is 0, so a disabled
  -- idle bound already fails invariant 1 and a disabled statement bound already fails
  -- invariant 2. A third check would be unreachable — §N.8 again.)

  RAISE NOTICE 'migration 1074 applied: data_plane_builder idle_in_txn=% statement_timeout=%', idle, stmt;
END $$;

COMMIT;
