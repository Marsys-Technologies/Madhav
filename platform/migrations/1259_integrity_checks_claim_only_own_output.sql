-- 1259_integrity_checks_claim_only_own_output.sql
--
-- Suvarna (SS rulings N-99 / Q-L4-02, widened by N-104 and N-105): an integrity check claims ONLY facts about its own
-- writer's output. A reference from another asset's table INTO this asset's table, and a reference from this asset's
-- table into another asset's table, are the OTHER asset's / this asset's own claim respectively, never the producer's.
-- Dangling references are reported by the orphan detector of migration 1260 (and the L5-side ledger design, PR #3023),
-- NEVER build-blocking for the parent. This migration applies that principle to ph_nimitta and mi_bhavisya and
-- gives the moved terms an owner. Four guarded UPDATEs of ONE column (integrity_check_sql) of four asset_registry rows,
-- each md5-guarded on its own live text; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Data-only: no table or function is created or altered.
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1259-001). Number 1259 allocated by SS. Merge only AFTER S-L1 and only
-- on SS's review. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images
-- roll). Not for the S-L1 window itself. Apply together with (or after) 1260 so the detector exists when the terms leave.
--
-- WHAT MOVES WHERE (live texts read as suvarna_reader, 2026-10-03):
--   ph_nimitta (L4, writes phala_anchors) keeps ONLY: (b) D-CND-04 identity (every anchor id equals phala_anchor_identity(...),
--   <= 4 named exception) and C13 (no anchor cites a signal of another chart). It LOSES:
--     * mimamsa_predictions.source_pramana_id -> phala_anchors      (L5 table; the 135 dangling): NOT re-homed here; the L5-side
--                                                                    detector (PR #3023) and mi_bhavisya (below) own it
--     * phala_phaladesa.top_anchor_id         -> ph_phaladesa already has it ("No dangling verdict anchor")
--     * phala_pramana.anchor_id               -> ph_pramana already has it (FULL OUTER JOIN tiling, both directions, per chart)
--     * phala_sodhana.anchor_id               -> ph_sodhana already has it (LEFT JOIN, missing or cross-chart anchor)
--     * phala_suddha_sodhana.anchor_id        -> ph_suddha_sodhana already has it (FULL OUTER JOIN tiling, both directions)
--     * phala_muhurta.linked_anchor_id        -> ph_muhurta already has it (resolves, and to the SAME chart)
--     * phala_sankrama.source_anchor_id       -> ph_sankrama had NONE: this migration ADDS it (UPDATE 3 below)
--     * phala_mitigation.linked_anchor_id     -> ph_pratikara had NONE: this migration ADDS it (UPDATE 4 below). Not named in N-105,
--                                                added on the same principle so the term is not orphaned; its FK is ON DELETE SET
--                                                NULL, so it cannot fail today. Drop UPDATE 4 if SS does not want it.
--     * phala_pramana one-row-per-anchor grain-> ph_pramana already has it ("Grain assertion: one row per anchor, per chart")
--   mi_bhavisya (L5) LOSES its branch that requires every prediction's source_pramana_id to resolve to a phala_anchors row.
--   Where the owner ALREADY carries the term it is not duplicated. The pre-check below REFUSES to apply if any of those
--   five owners has lost its term in the meantime (a moved term must always have an owner); owners are matched by a
--   fragment of their own text, not by md5, so an unrelated edit of an owner does not block the deploy.
--
-- BASE AND TARGET TEXTS (md5 over the full text; lengths in chars):
--   ph_nimitta  base 658ffdbcb6d531e8cf5eed6c5260a966 (3063)  ->  a32f6d86553f67458dfd8373e4fdbe39 (2100)
--       base = migration 680's check + migration 683's C13 addition (reproduced by the tests).
--   mi_bhavisya base 19b5ea334236eaffa493069a7d4b318b (2186)  ->  8e88e9d4ed07f47cdcecc7861fc8516d (1951)
--       base = migration 691's check verbatim; target = base minus the one OR branch, nothing added.
--   ph_sankrama base 298b2259cda7bd5b4759061e74d75d17 (823)  ->  e97e797678f23c673d962b7c6cbb74ee (1409)
--       base = migration 681's check (reproduced by the tests); target = base + one appended NOT EXISTS conjunct
--       (source_anchor_id resolves; NULL legal).
--   ph_pratikara base c00c6c88e3a9fc74489bde3988870ef0 (1108)  ->  fac43b4e3117b30efb93aa87aaf80f5f (1703)
--       base = migration 681's check (reproduced by the tests); target = base + one appended NOT EXISTS conjunct
--       (linked_anchor_id resolves; NULL legal).
--   For ph_nimitta the new text differs from the base by removed conjuncts and comment lines only (a test strips comments
--   and proves the executable text is the base minus exactly those conjuncts).
--
-- READBACKS, production, suvarna_reader, 2026-10-03, read-only (whole text where the reader may execute it; ph_nimitta's
-- text calls phala_anchor_identity() and the reader has NO EXECUTE on it (permission denied), so it was evaluated per
-- conjunct AND as a whole text on a disposable local PostgreSQL 15 holding a SELECT-only copy of the rows it reads,
-- with the production definition of the function):
--   asset            OLD     NEW     reason / conjunct values
--   ph_nimitta       false   TRUE    old: phaladesa dangling 6, mimamsa dangling 135; new: (b) 0 identity mismatches (<= 4), C13 0
--   mi_bhavisya      false   TRUE    old: 135 of 139 canonical predictions fail the removed branch (0 of 56 on 1c826d5a)
--   ph_sankrama      true    true    new term: 0 dangling source_anchor_id of 630 rows
--   ph_pratikara     false   false   both false for a PRE-EXISTING reason, untouched here: its obstruction/mitigation tiling term (536
--                                    violating rows on 1 chart: mitigation rows citing obstructions that no longer exist);
--                                    new term: 0 dangling linked_anchor_id
--   Owners that already carry their term (UNCHANGED by this migration), current value, same session:
--   ph_phaladesa     false           FALSE, honestly, for TWO reasons the migration does not touch: top_anchor_id dangling = 6 rows
--                                    (its own term), and anchor_count drift vs phala_anchors = 7 rows (another cross-asset claim it
--                                    carries); it stays false until ph_phaladesa is rebuilt
--   ph_pramana true, ph_sodhana true, ph_suddha_sodhana true, ph_muhurta true
--   (per-conjunct values, row counts and the replica's row counts are in the PR body and the evidence files.)
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-03, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW
--   WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   Assets touched, and no others: ph_nimitta, mi_bhavisya, ph_sankrama, ph_pratikara. Affected charts: every
--   asset_freshness row of those four assets. Today there are NONE: asset_freshness holds 98 rows, 0 belong to any ph_* asset,
--   and the only mi_* rows are mi_jivanaghatana, mi_kula, mi_vistara; none is mi_bhavisya (no RLS on asset_freshness, so this
--   is the whole table, not a filtered view). So the trigger updates 0 rows and NO chart's freshness or served-generation
--   state changes for any of the four. The five owners are NOT updated, so their freshness is untouched. (If a receipt row for
--   any of the four is written before this applies, that row, on its chart, goes stale; re-read the counts at apply time.)
--   A re-run is an idempotent no-op (updates 0 rows, does not fire the trigger).
--
-- IDEMPOTENT SHAPE. The pre-check accepts, per asset, exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, nothing rewritten). Any other md5 RAISES, for any of the four, and nothing is changed: the migration refuses
-- to overwrite a text it was not written against. Every UPDATE is also guarded by its base md5; the post-check proves each new
-- text took.
--
-- 0 ACTIVE RUNS AT APPLY (ENFORCED, not advisory): the first DO block below RAISES, and changes nothing, if build_runs holds
-- any run that is not completed/failed/stopped (i.e. planned, running or paused) for any of the four assets. 0 on 2026-10-03.
-- (A raise here fails that deploy's migrate job until the run finishes and the job is re-run; merge in an idle window.)
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect four rows:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry
--    WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya', 'ph_sankrama', 'ph_pratikara') ORDER BY 1;
--   -- mi_bhavisya 8e88e9d4ed07f47cdcecc7861fc8516d 1951 ; ph_nimitta a32f6d86553f67458dfd8373e4fdbe39 2100
--   -- ph_pratikara fac43b4e3117b30efb93aa87aaf80f5f 1703 ; ph_sankrama e97e797678f23c673d962b7c6cbb74ee 1409
-- and expect no freshness rows for any of them unless a receipt was written since (then: stale/registry_changed):
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
--    WHERE asset_id IN ('ph_nimitta', 'mi_bhavisya', 'ph_sankrama', 'ph_pratikara');
--
-- NOT DONE HERE: the L5-side reference-resolution detector (PR #3023 design; separate); the detector for the L4 references
-- is migration 1260's views; ph_phaladesa's anchor_count-drift term (another cross-asset claim it carries; untouched); any
-- rebuild of any asset; any change to mimamsa_predictions, phala_anchors or any table.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <that asset's base text, md5 above>
-- WHERE asset_id = '<asset>'; fires the same trigger. Re-adding a term to ph_nimitta/mi_bhavisya makes that check false again
-- while the dangling references exist.

SET LOCAL lock_timeout = '5s';

DO $runs$
DECLARE n_active int; v_assets text;
BEGIN
  SELECT count(*), string_agg(DISTINCT a.asset_id, ', ') INTO n_active, v_assets
    FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
   WHERE a.asset_id IN ('ph_nimitta', 'mi_bhavisya', 'ph_sankrama', 'ph_pratikara')
     AND r.state NOT IN ('completed', 'failed', 'stopped');
  IF n_active > 0 THEN
    RAISE EXCEPTION '1259: % active build run(s) (planned/running/paused) for %; refusing to change integrity checks under a running build', n_active, v_assets;
  END IF;
END
$runs$;

DO $pre$
DECLARE r record; v_md5 text; v_n int; v_txt text;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('ph_nimitta',   '658ffdbcb6d531e8cf5eed6c5260a966', 'a32f6d86553f67458dfd8373e4fdbe39'),
      ('mi_bhavisya',  '19b5ea334236eaffa493069a7d4b318b', '8e88e9d4ed07f47cdcecc7861fc8516d'),
      ('ph_sankrama',  '298b2259cda7bd5b4759061e74d75d17', 'e97e797678f23c673d962b7c6cbb74ee'),
      ('ph_pratikara', 'c00c6c88e3a9fc74489bde3988870ef0', 'fac43b4e3117b30efb93aa87aaf80f5f')
    ) AS t(asset_id, old_md5, new_md5)
  LOOP
    SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = r.asset_id;
    IF v_n <> 1 THEN
      RAISE EXCEPTION '1259: expected exactly one % registry row, found %', r.asset_id, v_n;
    END IF;
    IF v_md5 = r.new_md5 THEN
      RAISE NOTICE '1259: % integrity_check_sql already carries the own-output text; nothing to do', r.asset_id;
    ELSIF v_md5 IS DISTINCT FROM r.old_md5 THEN
      RAISE EXCEPTION '1259: % integrity_check_sql is not the text this migration was written against (md5 %)', r.asset_id, v_md5;
    END IF;
  END LOOP;
END
$pre$;

-- Ownership precondition: every moved term must have an owner. Each of these assets already carries its own anchor-reference
-- term (fragment of its live text); if one has lost it, refuse rather than leave the term unowned.
DO $own$
DECLARE r record; v_txt text;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('ph_phaladesa',     'a.anchor_id = pd.top_anchor_id'),
      ('ph_pramana',       'FULL OUTER JOIN phala_pramana p ON p.anchor_id = a.anchor_id'),
      ('ph_pramana',       'count(*) <> count(DISTINCT anchor_id)'),
      ('ph_sodhana',       'LEFT JOIN phala_anchors a ON a.anchor_id = s.anchor_id'),
      ('ph_suddha_sodhana','FULL OUTER JOIN phala_suddha_sodhana s ON s.anchor_id = a.anchor_id'),
      ('ph_muhurta',       'LEFT JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id')
    ) AS t(asset_id, fragment)
  LOOP
    SELECT integrity_check_sql INTO v_txt FROM asset_registry WHERE asset_id = r.asset_id;
    IF v_txt IS NULL OR position(r.fragment IN v_txt) = 0 THEN
      RAISE EXCEPTION '1259: % no longer carries its own anchor-reference term (%); a term moved out of ph_nimitta would be unowned', r.asset_id, r.fragment;
    END IF;
  END LOOP;
END
$own$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
SELECT
  -- Facts about THIS asset's own output (phala_anchors) ONLY (migration 1259; SS N-99, N-105). Every reference INTO
  -- phala_anchors from another asset's table (the L4 children phala_pramana/sankrama/sodhana/suddha_sodhana/phaladesa/
  -- muhurta/mitigation, and the L5 table mimamsa_predictions) and the one-pramana-per-anchor grain of phala_pramana were
  -- removed from this check: each is that asset's own claim (ph_phaladesa, ph_pramana, ph_sodhana, ph_suddha_sodhana,
  -- ph_muhurta already carry theirs; migration 1259 adds ph_sankrama's and ph_pratikara's). Dangling references are
  -- reported by the orphan detector (migration 1260) and never block this asset's build.
  -- (b) D-CND-04 itself: every anchor's stored id must equal its computed identity.
  --     A row that fails this was written by a path that bypassed the deterministic
  --     key -- which is the specific regression this asset must never have again.
  --     The <= 4 allowance is the named, escalated exception (issue #1748): 2 pairs
  --     of rows that are content-identical apart from a grade, whose merge re-points
  --     L5 rows and is therefore not this session's decision alone. It is an explicit
  --     counted allowance, not a silent skip, and it must SHRINK, never grow.
  (SELECT count(*) FROM phala_anchors a
        WHERE a.anchor_id <> phala_anchor_identity(a.chart_id, a.anchor_source, a.event_type,
              a.direction, a.domain, a.horizon_tier, a.window_start, a.peak_date,
              a.window_end, a.falsifier)) <= 4
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

UPDATE asset_registry
SET integrity_check_sql = $sk$
-- D-CND-03: chart-partitioned.
SELECT
  -- §N.5: L4 must not have drifted from the L2 value it copied.
  NOT EXISTS (SELECT 1 FROM phala_sankrama s
      JOIN bodha_cdlm_cells c ON c.cell_id = s.cdlm_cell_id AND c.chart_id = s.chart_id
     WHERE s.linkage_strength IS DISTINCT FROM c.net_linkage_strength
        OR s.target_domain IS DISTINCT FROM c.domain_col
     GROUP BY s.chart_id HAVING count(*) > 0)
  -- Projected windows are ordered.
  AND NOT EXISTS (SELECT 1 FROM phala_sankrama
     WHERE projected_window_end IS NOT NULL AND projected_window_start > projected_window_end
     GROUP BY chart_id HAVING count(*) > 0)
  -- The natural key is distinct within each chart.
  AND NOT EXISTS (SELECT 1 FROM phala_sankrama
     GROUP BY chart_id HAVING count(*) <> count(DISTINCT (source_anchor_id, cdlm_cell_id)))
  -- Every source anchor resolves to a phala_anchors row. Moved here from ph_nimitta's check by migration 1259 (N-99/N-105):
  -- a reference from THIS asset's rows into phala_anchors is this asset's claim, not the anchor writer's. NULL (no source
  -- anchor) is legal. A violation is also reported by the 1260 orphan detector, which never blocks a build.
  AND NOT EXISTS (SELECT 1 FROM phala_sankrama s
      LEFT JOIN phala_anchors a ON a.anchor_id = s.source_anchor_id
     WHERE s.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL
     GROUP BY s.chart_id HAVING count(*) > 0)
$sk$
WHERE asset_id = 'ph_sankrama'
  AND md5(integrity_check_sql) = '298b2259cda7bd5b4759061e74d75d17';

UPDATE asset_registry
SET integrity_check_sql = $rk$
-- D-CND-03: chart-partitioned. The tiling is additionally restricted to charts that HAVE
-- mitigation rows: chart cb73cd3d has 6 obstructions and none, because its ph_nimitta build
-- errored and ph_pratikara never ran. An unbuilt chart is not corruption -- and the scoped
-- form still goes red on a genuine partial build (verified by probe).
SELECT
  NOT EXISTS (SELECT 1 FROM kala_obstruction o
      FULL OUTER JOIN phala_mitigation m ON m.obstruction_id = o.id AND m.chart_id = o.chart_id
     WHERE (o.id IS NULL OR m.mitigation_id IS NULL)
       AND coalesce(o.chart_id, m.chart_id) IN (SELECT DISTINCT chart_id FROM phala_mitigation)
     GROUP BY coalesce(o.chart_id, m.chart_id) HAVING count(*) > 0)
  -- §N.5: the stored severity must be the declared mapping of the upstream it restates.
  AND NOT EXISTS (SELECT 1 FROM phala_mitigation m JOIN kala_obstruction o ON o.id = m.obstruction_id
     WHERE m.obstruction_severity IS DISTINCT FROM CASE o.severity
       WHEN 'mild' THEN 'low' WHEN 'moderate' THEN 'medium' WHEN 'severe' THEN 'high' END
     GROUP BY m.chart_id HAVING count(*) > 0)
  -- Every linked anchor resolves to a phala_anchors row. Moved here from ph_nimitta's check by migration 1259 (N-99/N-105):
  -- a reference from THIS asset's rows (phala_mitigation) into phala_anchors is this asset's claim. NULL is legal. The FK is
  -- ON DELETE SET NULL, so today this cannot fail; it is kept so the term has an owner if that FK ever changes.
  AND NOT EXISTS (SELECT 1 FROM phala_mitigation m
      LEFT JOIN phala_anchors a ON a.anchor_id = m.linked_anchor_id
     WHERE m.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL
     GROUP BY m.chart_id HAVING count(*) > 0)
$rk$
WHERE asset_id = 'ph_pratikara'
  AND md5(integrity_check_sql) = 'c00c6c88e3a9fc74489bde3988870ef0';

DO $post$
DECLARE r record; v_md5 text;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('ph_nimitta',   'a32f6d86553f67458dfd8373e4fdbe39'),
      ('mi_bhavisya',  '8e88e9d4ed07f47cdcecc7861fc8516d'),
      ('ph_sankrama',  'e97e797678f23c673d962b7c6cbb74ee'),
      ('ph_pratikara', 'fac43b4e3117b30efb93aa87aaf80f5f')
    ) AS t(asset_id, new_md5)
  LOOP
    SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = r.asset_id;
    IF v_md5 IS DISTINCT FROM r.new_md5 THEN
      RAISE EXCEPTION '1259: the new % integrity_check_sql did not take (md5 %)', r.asset_id, v_md5;
    END IF;
  END LOOP;
END
$post$;
