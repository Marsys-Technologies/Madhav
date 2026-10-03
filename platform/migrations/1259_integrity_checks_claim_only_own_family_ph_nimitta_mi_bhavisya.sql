-- 1259_integrity_checks_claim_only_own_family_ph_nimitta_mi_bhavisya.sql
--
-- Suvarna (SS ruling N-99, Q-L4-02, widened by SS N-104): an integrity check must claim only what its own writer
-- produces. Two registry integrity_check_sql texts carry the SAME GLOBAL term that reaches into a table their writer
-- does not produce, and both are false in production today because of it:
--   * ph_nimitta (L4; writes phala_anchors): "no mimamsa_predictions.source_pramana_id may fail to resolve to a
--     phala_anchors row", over every row of the frozen L5 table mimamsa_predictions, every chart.
--   * mi_bhavisya (L5; writes mimamsa_predictions + mimamsa_manifestation_sets): the same dangling-anchor test,
--     "every prediction's source_pramana_id must resolve to a phala_anchors row of the same chart", i.e. a
--     reference INTO the L4 table phala_anchors, which mi_bhavisya reads but does not produce.
-- This migration REMOVES exactly that term from each (two guarded UPDATEs, one per asset, each md5-guarded on its own
-- live text) and nothing else of either check's logic. The dangling-reference check moves to the L5-side
-- reference-resolution detector of the ledger design (PR #3023, L5_REFERENCE_RESOLUTION_LEDGER_DESIGN_v1_0.md; Q-L4-02):
-- reported, not build-blocking. The detector itself is a separate design item and is NOT part of this migration.
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: two UPDATEs of
-- one column of two asset_registry rows; no table is altered; no function is created.
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1259-001). Number 1259 allocated by SS. Merge only AFTER S-L1 and only
-- on SS's review. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images
-- roll). Not for the S-L1 window itself.
--
-- WHAT THE REMOVED ph_nimitta TERM DOES TODAY (production, read as suvarna_reader, 2026-10-03; piecewise because the
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
-- WHY THE TERM DOES NOT BELONG IN ph_nimitta. ph_nimitta is delete-then-insert on phala_anchors (CLAUDE.md N.3). The L5
-- predictions are frozen on purpose (mi_bhavisya preserves adjudicated rows); they were minted against an earlier
-- anchor generation. Migration 680 (D-CND-04) added the term to catch ORPHAN GENERATION, which is a real concern,
-- but it assigned an L5 symptom to an L4 gate. Detection of "an L5 row cites a vanished anchor" moves to an
-- L5-side reference-resolution detector: reported, not build-blocking (SS ruling). Until that detector exists the
-- dangling count is not measured anywhere in the build path (stated as NOT DONE below).
--
-- WHAT THE REMOVED mi_bhavisya TERM DOES TODAY (production, suvarna_reader, 2026-10-03). It is one OR branch of the
-- HAVING clause of the per-chart scan: count(*) FILTER (WHERE p.prediction_id IS NOT NULL AND NOT EXISTS (SELECT 1
-- FROM phala_anchors a WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0. Predictions
-- failing it: 135 of 139 on 482012f1-..., 0 of 56 on 1c826d5a-... So the check is FALSE today (whole text evaluated
-- read-only as the reader: old = false, new = true), and a mi_bhavisya rebuild could not be accepted for a fact its
-- writer neither produced nor can repair (phala_anchors is L4's). mi_bhavisya's own internal checks (windows,
-- confidence bands, frozen-hash and outcome fields, manifestation-set pairing, chart existence, uniqueness) all stay.
--
-- ph_nimitta BASE TEXT. The live ph_nimitta integrity_check_sql was read as suvarna_reader on 2026-10-03: 3,063 chars,
-- md5 658ffdbcb6d531e8cf5eed6c5260a966. It is the text of migration 680's check with migration 683's addition appended (the
-- C13 cross-chart conjunct). The new text is 3,167 chars, md5 45192b2752989dc4398d81c0135e1473.
-- NEW TEXT = BASE TEXT MINUS the one `AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ...) = 0`
-- line, PLUS comment lines only: the "(a)" comment said "8 columns" and now says "7 columns", with a 4-line comment
-- where the term was, saying why it is gone (comments carry no logic; a test strips comments and proves the
-- executable text is the base text minus that one line).
--
-- mi_bhavisya BASE TEXT. The live mi_bhavisya integrity_check_sql was read as suvarna_reader on 2026-10-03: 2,186
-- chars, md5 19b5ea334236eaffa493069a7d4b318b; it is migration 691's mi_bhavisya check, verbatim (reproduced from that
-- file by the tests). The new text is 1,951 chars, md5 8e88e9d4ed07f47cdcecc7861fc8516d: the base text MINUS that one
-- three-line OR branch, nothing else (the text has no comments, so none were added).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-03, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW
--   WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   Affected assets: ph_nimitta and mi_bhavisya, and no others. Affected charts: every asset_freshness row of those
--   two assets. Today there are NONE: asset_freshness holds 98 rows, 0 belong to any ph_* asset and the only mi_*
--   rows are mi_jivanaghatana, mi_kula, mi_vistara (1 each); none is ph_nimitta or mi_bhavisya (no RLS on
--   asset_freshness, so this is the whole table, not a filtered view). So the trigger updates 0 rows and NO chart's
--   freshness or served-generation state changes for either asset. (If a receipt row for either asset is written
--   before this applies, that row, on its chart, goes stale; re-read the counts at apply time.) A re-run is an
--   idempotent no-op (updates 0 rows, does not fire the trigger).
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, nothing rewritten). Any other md5 RAISES: the migration refuses to overwrite a text it was not
-- written against. The UPDATE is also guarded by the base md5. The post-check proves the new text took.
--
-- 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ph_nimitta or mi_bhavisya at apply (read-only check; 0 for
-- both on 2026-10-03):
--   SELECT a.asset_id, count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--    WHERE a.asset_id IN ('ph_nimitta', 'mi_bhavisya') AND r.state NOT IN ('completed', 'failed', 'stopped') GROUP BY 1;
--
-- ph_nimitta READBACKS (production, suvarna_reader, 2026-10-03). The reader has NO EXECUTE on phala_anchor_identity, so
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
-- mi_bhavisya READBACK (production, suvarna_reader, 2026-10-03): the reader can run the whole mi_bhavisya text.
--   OLD (md5 19b5ea33...) = false; NEW (md5 8e88e9d4...) = true.
--   So after this migration mi_bhavisya's check is true on today's data; ph_nimitta's is still false (a7) as above.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect two rows:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry
--    WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya') ORDER BY 1;
--   -- mi_bhavisya 8e88e9d4ed07f47cdcecc7861fc8516d 1951 ; ph_nimitta 45192b2752989dc4398d81c0135e1473 3167
-- and expect no freshness rows for either unless a receipt was written since (then: stale/registry_changed):
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya');
--
-- NOT DONE HERE: the L5-side reference-resolution detector (PR #3023 design; separate); moving ph_nimitta's (a7) or
-- (a1)-(a6); any rebuild of either asset; any change to mimamsa_predictions, phala_anchors or any table.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <the base text of that asset,
-- ph_nimitta md5 658ffdbcb6d531e8cf5eed6c5260a966 (migration 680's check with 683's addition), mi_bhavisya md5
-- 19b5ea334236eaffa493069a7d4b318b> WHERE asset_id = '<asset>'; fires the same trigger. Re-adding a term makes that check false again while the
-- 135 dangling references exist.

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE r record; v_md5 text; v_n int;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('ph_nimitta',  '658ffdbcb6d531e8cf5eed6c5260a966', '45192b2752989dc4398d81c0135e1473'),
      ('mi_bhavisya', '19b5ea334236eaffa493069a7d4b318b', '8e88e9d4ed07f47cdcecc7861fc8516d')
    ) AS t(asset_id, old_md5, new_md5)
  LOOP
    SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = r.asset_id;
    IF v_n <> 1 THEN
      RAISE EXCEPTION '1259: expected exactly one % registry row, found %', r.asset_id, v_n;
    END IF;
    IF v_md5 = r.new_md5 THEN
      RAISE NOTICE '1259: % integrity_check_sql already carries the own-family text; nothing to do', r.asset_id;
    ELSIF v_md5 IS DISTINCT FROM r.old_md5 THEN
      RAISE EXCEPTION '1259: % integrity_check_sql is not the text this migration was written against (md5 %)', r.asset_id, v_md5;
    END IF;
  END LOOP;
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

UPDATE asset_registry
SET integrity_check_sql = $mk$
SELECT
  NOT EXISTS (
    SELECT 1
    FROM mimamsa_predictions p
    FULL JOIN mimamsa_manifestation_sets m
      ON m.chart_id = p.chart_id AND m.prediction_id = p.prediction_id
    LEFT JOIN charts c ON c.id = coalesce(p.chart_id, m.chart_id)
    GROUP BY coalesce(p.chart_id, m.chart_id)
    HAVING count(*) FILTER (WHERE p.prediction_id IS NULL OR m.prediction_id IS NULL) > 0
        OR count(*) FILTER (WHERE c.id IS NULL) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (isempty(p.observation_window) OR NOT lower_inc(p.observation_window)
                    OR upper_inc(p.observation_window) OR p.eval_date <> upper(p.observation_window))) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (p.confidence_band IS NULL OR isempty(p.confidence_band)
                    OR lower(p.confidence_band) < 0 OR upper(p.confidence_band) > 1)) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (btrim(coalesce(p.frozen_bundle_hash, '')) = ''
                    OR btrim(coalesce(p.bundle_formula_version, '')) = ''
                    OR btrim(coalesce(p.outcome_claim, '')) = ''
                    OR btrim(coalesce(p.domain, '')) = ''
                    OR p.falsifier_jsonb IS NULL OR p.driving_signals IS NULL)) > 0
        OR count(*) FILTER (WHERE m.prediction_id IS NOT NULL AND m.domain IS DISTINCT FROM p.domain) > 0
        OR count(*) FILTER (WHERE m.prediction_id IS NOT NULL
               AND (m.citation_ref IS NULL OR btrim(coalesce(m.channel_id, '')) = ''
                    OR btrim(coalesce(m.source, '')) = '')) > 0
  )
  AND NOT EXISTS (SELECT 1 FROM mimamsa_predictions GROUP BY chart_id
                   HAVING count(DISTINCT prediction_id) <> count(*))
  AND NOT EXISTS (SELECT 1 FROM mimamsa_manifestation_sets GROUP BY chart_id
                   HAVING count(DISTINCT (prediction_id, channel_id)) <> count(*))
$mk$
WHERE asset_id = 'mi_bhavisya'
  AND md5(integrity_check_sql) = '19b5ea334236eaffa493069a7d4b318b';

DO $post$
DECLARE r record; v_md5 text;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('ph_nimitta',  '45192b2752989dc4398d81c0135e1473'),
      ('mi_bhavisya', '8e88e9d4ed07f47cdcecc7861fc8516d')
    ) AS t(asset_id, new_md5)
  LOOP
    SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = r.asset_id;
    IF v_md5 IS DISTINCT FROM r.new_md5 THEN
      RAISE EXCEPTION '1259: the new % integrity_check_sql did not take (md5 %)', r.asset_id, v_md5;
    END IF;
  END LOOP;
END
$post$;
