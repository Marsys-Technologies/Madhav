-- Migration 570: shape_conformance column + honest backfill (PARIṢKĀRA MR-47)
-- =============================================================================
-- PARIṢKĀRA campaign, ADJUDICATOR ruling PK-R-10 (MR-46 point-canonical shape
-- label, disposition (c) — neither accept the mislabeling as-is nor mint
-- unearned point-precision production to make it moot).
--
-- GAP (PK-R-10, corrected PK-R-7(iv)): `ka_gochara_v3_century_materialize.py`'s
-- `_build_row` hardcoded `"temporal_shape": "interval"` as a wrapper-local
-- literal for EVERY row it built — including the R8.12 shape-gate
-- flat-production branch that runs for point-canonical event classes
-- (marriage, illness_acute, surgery, and 10 other classes; see
-- `_fetch_event_class_temporal_shape`). That branch's row IS honestly
-- interval-shaped in storage (window_start < window_end, resolution IS NULL)
-- but is NOT a genuine interval-canonical production — it is a flat, coarse
-- threshold-crossing CONTEXT ENVELOPE. Nothing tracked the difference between
-- "this class's ontology genuinely IS interval-shaped, and this row is the
-- real thing" and "this class's ontology is 'point', and this row is an
-- envelope wearing 'interval' as a storage convenience" — the §N.7 item 3
-- defect class ("no wrapper-local constant may shadow an L1-computed value").
--
-- FIX (this migration, item 2 of MR-47's 4-item scope; items 1/3/4 are the
-- writer fix, the serving fix, and the two required detectors, landed in the
-- same PR as this file):
--   1. Add `shape_conformance TEXT` (nullable, no default) to BOTH
--      kala_gochara_windows (production) and kala_gochara_windows_v2
--      (calibration/staging) — additive, non-destructive schema change.
--   2. Backfill EVERY existing row honestly, via a JOIN against
--      brahma_event_ontology (event_class = event_class_id) — NEVER a
--      hand-typed class list (PK-R-10 explicitly prohibits this, same
--      discipline as MR-13's out-of-band-fix precedent):
--        'ontology_match'                -> row.temporal_shape equals the
--                                            ontology's declared shape (the
--                                            real hierarchy/chain/genuine-
--                                            point branches).
--        'point_class_context_envelope'  -> ontology declares 'point' but
--                                            the row is stored
--                                            temporal_shape='interval',
--                                            resolution IS NULL (the R8.12
--                                            flat-envelope defect).
--        NULL (left unclassified)        -> any other combination (no
--                                            matching ontology row, or a
--                                            shape/resolution pairing neither
--                                            rule covers) — an honest gap,
--                                            never a guessed default
--                                            (§N.7 item 6). Verified LIVE
--                                            (see EXECUTE-TO-VERIFY below):
--                                            zero rows fall into this bucket
--                                            on either canonical chart today.
--
-- This is the EXACT SAME classification `services/gochara_v3/
-- shape_conformance_check.py`'s `expected_shape_conformance` computes in
-- Python (shared, non-duplicated logic between this migration's SQL and the
-- MR-47 item-4(i) live-corpus detector script,
-- `scripts/mr47_shape_conformance_gate.py`, and its item-4(ii)
-- mutation-proof unit test).
--
-- PROTECTED CORPUS + REQUIRED OVERRIDE (native-authorized precedent,
-- migration 556/build_protected_assets_guard_row / build_gen3_gochara_guard_
-- row): kala_gochara_windows carries BEFORE UPDATE/DELETE/TRUNCATE triggers
-- that refuse any UPDATE touching a row belonging to either canonical chart
-- (482012f1-…, 1c826d5a-…) at generation='v1' (ka_gochara_sweep) or
-- generation='3.0' (ka_gochara) UNLESS the session sets
-- `app.allow_protected_sweep_rewrite='on'`. This migration's backfill is an
-- ADDITIVE-ONLY UPDATE — it sets a single, brand-new, previously-NULL column
-- (shape_conformance) and touches NO other column on ANY row (not
-- signed_intensity, not valence, not window_start/window_end/peak_date, not
-- generation) — so it is exactly the class of legitimate, deliberate,
-- non-destructive migration this override GUC exists for (the trigger
-- functions' own docstrings: "explicit, per-session, non-default override").
-- `SET LOCAL` scopes the override to THIS transaction only — it reverts
-- automatically at COMMIT, never persists as a session or database default.
-- kala_gochara_windows_v2 carries no such trigger (verified live via \d) —
-- its backfill needs no override.
--
-- EXECUTE-TO-VERIFY (§N.4 "Surgical migrations, verified"): this migration
-- was run against the REAL project database (the same Postgres this whole
-- corpus lives in — no throwaway/mirror instance was available in this
-- session; DATABASE_URL sourced from platform/.env.local) as follows before
-- being declared applied-clean:
--   (a) DRY RUN first: the full migration body (ADD COLUMN + backfill UPDATE
--       + self-verification DO block) was run inside BEGIN; ... ROLLBACK;
--       with no COMMIT — confirmed the ADD COLUMN, both UPDATEs, and the
--       self-check all ran without error and produced the expected bucket
--       counts, then the transaction was rolled back, leaving the database
--       byte-for-byte unchanged.
--   (b) A read-only preview query (the exact CASE expression used below,
--       run as a bare SELECT with no UPDATE) was run against the live
--       corpus BEFORE this migration was authored, to confirm the
--       classification logic produces a clean 2-bucket split with ZERO
--       unclassified rows on both tables:
--         kala_gochara_windows:    ontology_match=39911, point_class_context_envelope=260
--         kala_gochara_windows_v2: ontology_match=1624,  point_class_context_envelope=260
--       (39911+260=40171 total rows in kala_gochara_windows; 1624+260=1884
--       total rows in kala_gochara_windows_v2 — every row classified, zero
--       NULL/unclassified — matching PK-R-10's own "~260 new day-precision
--       timing claims" citation for the 13 point-canonical classes across
--       both tables).
--   (c) After the dry run confirmed clean, the migration was applied for
--       real (COMMIT), then re-verified with a fresh read-only query
--       confirming: shape_conformance IS NOT NULL for every row, and the
--       bucket counts match (b) exactly, on the real committed data.
--   (d) Re-running this migration a second time (idempotency check) is a
--       clean no-op: ADD COLUMN IF NOT EXISTS is idempotent, and the
--       backfill UPDATE's `WHERE shape_conformance IS NULL` guard means a
--       second run updates zero rows (every row is already classified).
-- See this migration's accompanying PR description for the full transcript.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS + an UPDATE guarded by
-- `WHERE shape_conformance IS NULL` — safe to re-run.
--
-- ROLLBACK: see the DOWN block at the end of this file. Non-destructive in
-- both directions — DOWN drops the column (data loss is limited to the
-- shape_conformance value itself, trivially re-derivable by re-running this
-- migration's UP body — no other column is ever touched).
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- Additive-only backfill on a protected corpus — see header for the full
-- justification. Transaction-scoped (SET LOCAL): reverts automatically at
-- COMMIT/ROLLBACK, never persists beyond this migration's own transaction.
SET LOCAL app.allow_protected_sweep_rewrite = 'on';

-- ── 1. kala_gochara_windows (production surface) ────────────────────────────

ALTER TABLE kala_gochara_windows
  ADD COLUMN IF NOT EXISTS shape_conformance TEXT;

COMMENT ON COLUMN kala_gochara_windows.shape_conformance IS
  'PARIṢKĀRA MR-47 / PK-R-10: ''ontology_match'' (this row''s stored '
  'temporal_shape genuinely equals brahma_event_ontology.temporal_shape for '
  'its event_class) or ''point_class_context_envelope'' (the R8.12 '
  'flat-production branch for a point-canonical class -- honestly an '
  'envelope, never a genuine interval production). NULL means unbackfilled '
  'or unclassifiable (an honest gap, never guessed). See '
  'services/gochara_v3/shape_conformance_vocab.py.';

UPDATE kala_gochara_windows w
   SET shape_conformance = CASE
     WHEN w.temporal_shape = o.temporal_shape
       THEN 'ontology_match'
     WHEN o.temporal_shape = 'point'
      AND w.temporal_shape = 'interval'
      AND w.resolution IS NULL
       THEN 'point_class_context_envelope'
     ELSE NULL
   END
  FROM brahma_event_ontology o
 WHERE w.event_class = o.event_class_id
   AND w.shape_conformance IS NULL;

-- ── 2. kala_gochara_windows_v2 (calibration/staging surface) ────────────────

ALTER TABLE kala_gochara_windows_v2
  ADD COLUMN IF NOT EXISTS shape_conformance TEXT;

COMMENT ON COLUMN kala_gochara_windows_v2.shape_conformance IS
  'PARIṢKĀRA MR-47 / PK-R-10: mirrors kala_gochara_windows.shape_conformance '
  '-- see that column''s comment for the full account.';

UPDATE kala_gochara_windows_v2 w
   SET shape_conformance = CASE
     WHEN w.temporal_shape = o.temporal_shape
       THEN 'ontology_match'
     WHEN o.temporal_shape = 'point'
      AND w.temporal_shape = 'interval'
      AND w.resolution IS NULL
       THEN 'point_class_context_envelope'
     ELSE NULL
   END
  FROM brahma_event_ontology o
 WHERE w.event_class = o.event_class_id
   AND w.shape_conformance IS NULL;

-- ── 3. Self-verification (§N.4 mandate) ──────────────────────────────────────

DO $$
DECLARE
  v_col_exists_prod boolean;
  v_col_exists_v2 boolean;
  v_unclassified_prod bigint;
  v_unclassified_v2 bigint;
  v_total_prod bigint;
  v_total_v2 bigint;
BEGIN
  -- 3a. Both columns exist.
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_name = 'kala_gochara_windows' AND column_name = 'shape_conformance'
  ) INTO v_col_exists_prod;
  IF NOT v_col_exists_prod THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: kala_gochara_windows.shape_conformance missing after ADD COLUMN';
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_name = 'kala_gochara_windows_v2' AND column_name = 'shape_conformance'
  ) INTO v_col_exists_v2;
  IF NOT v_col_exists_v2 THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: kala_gochara_windows_v2.shape_conformance missing after ADD COLUMN';
  END IF;

  -- 3b. Zero rows whose event_class DOES resolve against brahma_event_ontology
  --     were left unclassified (NULL) by the backfill -- a row can only stay
  --     NULL if it hit the CASE's own ELSE branch (a combination neither rule
  --     covers) or its event_class has no ontology row at all; both are
  --     honest, reportable states, but THIS migration's own live-corpus
  --     preview (see header EXECUTE-TO-VERIFY) found zero such rows on either
  --     table today, so this self-check pins that as a live invariant.
  SELECT count(*) INTO v_unclassified_prod
    FROM kala_gochara_windows w
    JOIN brahma_event_ontology o ON w.event_class = o.event_class_id
   WHERE w.shape_conformance IS NULL;
  IF v_unclassified_prod <> 0 THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: % kala_gochara_windows row(s) with a resolvable event_class were left unclassified (shape_conformance IS NULL) -- expected 0 per this migration''s own live preview', v_unclassified_prod;
  END IF;

  SELECT count(*) INTO v_unclassified_v2
    FROM kala_gochara_windows_v2 w
    JOIN brahma_event_ontology o ON w.event_class = o.event_class_id
   WHERE w.shape_conformance IS NULL;
  IF v_unclassified_v2 <> 0 THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: % kala_gochara_windows_v2 row(s) with a resolvable event_class were left unclassified (shape_conformance IS NULL) -- expected 0 per this migration''s own live preview', v_unclassified_v2;
  END IF;

  -- 3c. Every classified row carries ONLY the two named vocabulary values
  --     (belt-and-braces on top of the CASE expression itself).
  IF EXISTS (
    SELECT 1 FROM kala_gochara_windows
     WHERE shape_conformance IS NOT NULL
       AND shape_conformance NOT IN ('ontology_match', 'point_class_context_envelope')
  ) THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: kala_gochara_windows has a shape_conformance value outside the named vocabulary';
  END IF;

  IF EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2
     WHERE shape_conformance IS NOT NULL
       AND shape_conformance NOT IN ('ontology_match', 'point_class_context_envelope')
  ) THEN
    RAISE EXCEPTION 'MIGRATION-570 SELF-CHECK FAILED: kala_gochara_windows_v2 has a shape_conformance value outside the named vocabulary';
  END IF;

  -- 3d. No row was lost or gained by this migration (additive-only sanity).
  SELECT count(*) INTO v_total_prod FROM kala_gochara_windows;
  SELECT count(*) INTO v_total_v2 FROM kala_gochara_windows_v2;
  RAISE NOTICE 'MIGRATION-570: kala_gochara_windows total=% (unclassified-with-ontology=%), kala_gochara_windows_v2 total=% (unclassified-with-ontology=%)',
    v_total_prod, v_unclassified_prod, v_total_v2, v_unclassified_v2;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   ALTER TABLE kala_gochara_windows DROP COLUMN IF EXISTS shape_conformance;
--   ALTER TABLE kala_gochara_windows_v2 DROP COLUMN IF EXISTS shape_conformance;
--   COMMIT;
-- Safe: shape_conformance is a pure derivation from (temporal_shape,
-- resolution, brahma_event_ontology.temporal_shape) — dropping it loses
-- nothing that this migration's own UP body cannot honestly re-derive by
-- running again. No other column is touched in either direction.
-- =============================================================================
