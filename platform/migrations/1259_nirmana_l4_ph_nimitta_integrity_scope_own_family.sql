-- 1259_nirmana_l4_ph_nimitta_integrity_scope_own_family.sql
--
-- Suvarna (SS ruling N-99, Q-L4-02, A.L4 finding): an integrity check must claim only what its own writer produces.
-- ph_nimitta's registry integrity_check_sql carries one GLOBAL term over the L5 table mimamsa_predictions
-- (every row, every chart): "no mimamsa_predictions.source_pramana_id may fail to resolve to a phala_anchors
-- row". ph_nimitta writes phala_anchors; it does not write, and cannot repair, a frozen L5 table. This migration
-- REMOVES exactly that term (one SQL line) and nothing else of the check's logic. The reference-resolution
-- detector for L5 -> L4 is a separate design item (Q-L4-02) and is NOT part of this migration.
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: one UPDATE of
-- one column of one asset_registry row; no table is altered; no function is created.
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1259-001). Number 1259 allocated by SS. Merge only AFTER S-L1 and only
-- on SS's review. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images
-- roll). Not for the S-L1 window itself.
--
-- WHAT THE REMOVED TERM DOES TODAY (production, read as suvarna_reader, 2026-10-03; piecewise because the
-- reader holds no EXECUTE on phala_anchor_identity, see "READBACKS" below):
--   mimamsa_predictions rows 195 (139 on 482012f1-..., 56 on 1c826d5a-...), all with source_pramana_id set;
--   phala_anchors rows 60 (4 on 482012f1-..., 56 on 1c826d5a-...);
--   dangling references (source_pramana_id with no phala_anchors row) = 135, all on the canonical chart.
--   So the term is FALSE today, and because the check is a conjunction the whole check is false.
--   WHY THAT MATTERS: the orchestrator runs integrity_check_sql after the writer
--   (platform/python-sidecar/pipeline/orchestrator/asset_runner.py, the `has_integrity_check` gate near :1167):
--   for a light writer a false result rolls the write back, for a heavy writer it blocks acceptance. A ph_nimitta
--   rebuild could therefore never be accepted while frozen L5 rows (which the L4 rebuild did not create and cannot
--   fix) cite anchors that no longer exist.
--
-- WHY THE TERM DOES NOT BELONG HERE. ph_nimitta is delete-then-insert on phala_anchors (CLAUDE.md N.3). The L5
-- predictions are frozen on purpose (mi_bhavisya preserves adjudicated rows); they were minted against an earlier
-- anchor generation. Migration 680 (D-CND-04) added the term to catch ORPHAN GENERATION, which is a real concern,
-- but it assigned an L5 symptom to an L4 gate. Detection of "an L5 row cites a vanished anchor" moves to an
-- L5-side reference-resolution detector: reported, not build-blocking (SS ruling). Until that detector exists the
-- dangling count is not measured anywhere in the build path (stated as NOT DONE below).
--
-- BASE TEXT. The live ph_nimitta integrity_check_sql was read as suvarna_reader on 2026-10-03: 3,063 chars,
-- md5 658ffdbcb6d531e8cf5eed6c5260a966. It is the text of migration 680's check with migration 683's addition appended (the
-- C13 cross-chart conjunct). The new text is 3,167 chars, md5 45192b2752989dc4398d81c0135e1473.
-- NEW TEXT = BASE TEXT MINUS the one `AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ...) = 0`
-- line, PLUS comment lines only: the "(a)" comment said "8 columns" and now says "7 columns", with a 4-line comment
-- where the term was, saying why it is gone (comments carry no logic; a test strips comments and proves the
-- executable text is the base text minus that one line).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-03, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW
--   WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   Affected asset: ph_nimitta ONLY. Affected charts: every asset_freshness row of ph_nimitta. Today there are
--   NONE: asset_freshness holds 98 rows and 0 of them belong to any ph_* asset (no RLS on asset_freshness, so
--   this is the whole table, not a filtered view). So the trigger updates 0 rows and NO chart's freshness or
--   served-generation state changes. (If a ph_nimitta receipt row is written before this applies, that row, on
--   its chart, goes stale; re-read the count at apply time.) No other asset is touched. A re-run is an
--   idempotent no-op (updates 0 rows, does not fire the trigger).
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, nothing rewritten). Any other md5 RAISES: the migration refuses to overwrite a text it was not
-- written against. The UPDATE is also guarded by the base md5. The post-check proves the new text took.
--
-- 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ph_nimitta at apply (read-only check; 0 on 2026-10-03):
--   SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--    WHERE a.asset_id = 'ph_nimitta' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- READBACKS (production, suvarna_reader, 2026-10-03). The reader has NO EXECUTE on phala_anchor_identity, so
-- neither the old nor the new WHOLE text can be run as the reader (ERROR: permission denied for function
-- phala_anchor_identity). Each conjunct was therefore evaluated separately; conjunct (b) was recomputed outside
-- the database from the 60 anchor rows with the function's own definition (uuid v5, namespace
-- a5f7c1e2-0b3d-5e88-9c41-6d2f8a7b4e10, canonical jsonb text) and the live BEFORE INSERT trigger
-- phala_anchors_identity_biu is enabled:
--   (a1) phala_suddha_sodhana dangling 0 | (a2) phala_sodhana 0 | (a3) phala_pramana 0 | (a4) phala_sankrama 0
--   (a5) phala_muhurta 0 | (a6) phala_mitigation 0
--   (a7) phala_phaladesa.top_anchor_id dangling = 6  <-- FALSE (6 of the 7 non-null top_anchor_id on 482012f1)
--   (a8) mimamsa_predictions dangling = 135            <-- the term this migration removes
--   (b)  anchors whose id differs from phala_anchor_identity(...) = 0 (<= 4 allowed): true
--   (c)  phala_pramana duplicate anchor_id groups = 0: true
--   (C13) cross-chart signal citations = 0: true
--   OLD text: FALSE (a7 = 6 and a8 = 135).
--   NEW text: STILL FALSE, for ANOTHER reason: (a7) phala_phaladesa.top_anchor_id has 6 dangling references.
--   THIS MIGRATION DOES NOT MAKE ph_nimitta's CHECK TRUE BY ITSELF. phala_phaladesa is written by ph_phaladesa,
--   not ph_nimitta: the same "claim only what your writer produces" principle applies to (a7), and to the other
--   child-table terms (a1)-(a6). Today's zeros for (a1)-(a4) are kept by FK ON DELETE CASCADE (which migration
--   1260 replaces with a detector; after 1260 these terms are the only thing that can read an orphan) and for
--   (a5)-(a6) by FK ON DELETE SET NULL. Not widened here (SS ruled exactly the mimamsa term); reported to SS.
--   WHOLE-TEXT CHECK on a replica: the rows the check reads (ids only; bodha_msr_signals 150,724 rows; phala_anchors 60;
--   mimamsa_predictions 195; phala_phaladesa 26; ...) were copied with the reader's SELECT into a disposable local
--   PostgreSQL 15 with the production definition of phala_anchor_identity(), and the two WHOLE texts were run there:
--   OLD (md5 658ffdbc...) = false; NEW (md5 45192b27...) = false; NEW minus the (a7) line, as a diagnostic only, = true.
--   So (a7) is the one remaining reason the check is false. Nothing was written to production.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect one row with md5 = 45192b2752989dc4398d81c0135e1473 and length 3167:
--   SELECT md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ph_nimitta';
-- and expect zero ph_nimitta rows in asset_freshness unless a receipt was written since (then: stale/registry_changed):
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness WHERE asset_id = 'ph_nimitta';
--
-- NOT DONE HERE: the L5-side reference-resolution detector (separate design item); moving (a7) or (a1)-(a6); any
-- ph_nimitta rebuild; any change to mimamsa_predictions, phala_anchors or any table.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 680's check with
-- 683's addition, md5 658ffdbcb6d531e8cf5eed6c5260a966> WHERE asset_id = 'ph_nimitta'; fires the same trigger. Re-adding the term would make the
-- check false again while the 135 dangling references exist.

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ph_nimitta';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1259: expected exactly one ph_nimitta registry row, found %', v_n;
  END IF;
  IF v_md5 = '45192b2752989dc4398d81c0135e1473' THEN
    RAISE NOTICE '1259: ph_nimitta integrity_check_sql already carries the own-family text; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '658ffdbcb6d531e8cf5eed6c5260a966' THEN
    RAISE EXCEPTION '1259: ph_nimitta integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
SELECT
  -- (a) referential integrity: no reference to a non-existent anchor, in any of the
  --     7 columns THIS ASSET'S OWN FAMILY writes (L4 phala_* tables). The 8th reference
  --     (L5 mimamsa_predictions.source_pramana_id) was removed by migration 1259: a
  --     frozen L5 table is not something ph_nimitta produces, so a build of this asset
  --     must not be judged by it; that check belongs to an L5-side detector.
  (SELECT count(*) FROM phala_suddha_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_pramana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_sankrama c LEFT JOIN phala_anchors a ON a.anchor_id = c.source_anchor_id WHERE c.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_muhurta c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_mitigation c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  -- (b) D-CND-04 itself: every anchor's stored id must equal its computed identity.
  --     A row that fails this was written by a path that bypassed the deterministic
  --     key -- which is the specific regression this asset must never have again.
  --     The <= 4 allowance is the named, escalated exception (issue #1748): 2 pairs
  --     of rows that are content-identical apart from a grade, whose merge re-points
  --     L5 rows and is therefore not this session's decision alone. It is an explicit
  --     counted allowance, not a silent skip, and it must SHRINK, never grow.
  AND (SELECT count(*) FROM phala_anchors a
        WHERE a.anchor_id <> phala_anchor_identity(a.chart_id, a.anchor_source, a.event_type,
              a.direction, a.domain, a.horizon_tier, a.window_start, a.peak_date,
              a.window_end, a.falsifier)) <= 4
  -- (c) the anchor->pramana->prediction chain is 1:1 where it exists at all.
  AND (SELECT count(*) FROM (SELECT anchor_id FROM phala_pramana GROUP BY anchor_id HAVING count(*) > 1) d) = 0

  -- C13 / #1748: an anchor may cite a signal that no longer exists (orphan-tolerant by
  -- disposition -- see phala_anchor_signal_provenance()), but it must NEVER cite a signal
  -- belonging to a DIFFERENT CHART. That is cross-chart contamination (the JL-017 class),
  -- not staleness, and nothing else detects it.
  AND NOT EXISTS (
    SELECT 1 FROM phala_anchors a
      JOIN bodha_msr_signals s ON s.signal_id::text = a.signal_id::text
     WHERE a.signal_id IS NOT NULL AND s.chart_id <> a.chart_id
     GROUP BY a.chart_id HAVING count(*) > 0)
$ck$
WHERE asset_id = 'ph_nimitta'
  AND md5(integrity_check_sql) = '658ffdbcb6d531e8cf5eed6c5260a966';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'ph_nimitta';
  IF v_md5 IS DISTINCT FROM '45192b2752989dc4398d81c0135e1473' THEN
    RAISE EXCEPTION '1259: the new ph_nimitta integrity_check_sql did not take (md5 %)', v_md5;
  END IF;
END
$post$;
