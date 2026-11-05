-- 1276_mi_bhavisya_natural_key_partition_append_only.sql
--
-- Suvarna (SS allocation 1276; N-104 / N-107). Replaces the stale justification text stored in asset_registry.natural_key_partition for
-- mi_bhavisya. Migration 991 stored a text that justifies the partition declaration by the writer's "idempotent DELETE FROM
-- mimamsa_manifestation_sets WHERE chart_id = %s before the insert pass means exactly the current run's row set exists per chart_id". mi_bhavisya is
-- now APPEND-ONLY (SS N-104 / N-107; PR #3040, branch suvarna/land/TI-mi-bhavisya-appendonly-001, design note
-- 00_ARCHITECTURE/briefs/suvarna/layers/L5/MI_BHAVISYA_APPEND_ONLY_v1_0.md section 4 item 4, which names this registry string as stale and
-- says a new migration must correct it because applied migrations are not edited). Migration 991 is NOT edited. One md5-guarded UPDATE of
-- one column of one row. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only.
--
-- HELD, POST-WINDOW. Own draft PR (suvarna/land/TI-mig-1276-001). Routine path (amjis_app owns asset_registry; no schema CREATE needed).
-- ORDER (hard): apply only AFTER PR #3040 (the append-only writer) is merged AND DEPLOYED. Before that the writer still deletes, and the new text
-- would be false. Independent of 1259 (which changes integrity_check_sql of the same row: a different column, its own md5 guard; either order works).
--
-- THE TEXT. Live (suvarna_reader, 2026-10-03): 2,838 chars, md5 07d729f8f0487ac3d3ddb114dd4cdc73; it equals the single-quoted literal in migration 991. New: 3,544 chars,
-- md5 a411af1488287dced6b8b121ec1eb28b; full text in the UPDATE below. It keeps the component declaration the partition exists for
-- ('mimamsa_manifestation_sets (chart_id, prediction_id, channel_id)'), the sole-writer evidence, the exclusions and the open flags, and replaces
-- the delete-based reasoning with: append-only (no DELETE/UPDATE/TRUNCATE/DO UPDATE; every insert DO NOTHING; a set only with its prediction),
-- the cumulative row set, the two-part natural key (prediction_id = 'pred_<anchor>' OR source_pramana_id = '<anchor>'), idempotency by existing-key
-- skip, and a fresh read-only verification (195 rows, 0 duplicate groups, 0 NULL keys, sets and predictions pair 1:1).
--
-- SERVING / FRESHNESS EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-03, suvarna_reader).
--   `UPDATE ... SET natural_key_partition` fires the live trigger nirmana_registry_receipt_invalidation: natural_key_partition IS in its column list
--   (AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer,
--   is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*); function nirmana_invalidate_registry_receipts() sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id). Asset touched: mi_bhavisya only.
--   asset_freshness has 0 rows for mi_bhavisya (98 rows in the table, the only mi_* rows are mi_jivanaghatana, mi_kula, mi_vistara; no RLS), on any
--   chart, so 0 rows are staled and no chart's freshness or served-generation state changes. asset_provenance_receipts holds 0 rows for mi_bhavisya
--   either. A re-run is a no-op (0 rows updated, trigger not fired).
--   IMPORTANT, THE TEXT IS A KEY: asset_runner / provenance.py use natural_key_partition as the receipt PARTITION KEY (partition_key =
--   natural_key_partition or '__whole_asset__') and fold it into the partition digest. Changing the text changes the key a future receipt is stored
--   under, so any receipt/freshness row written under the OLD text would be stranded (never read again) and the next build writes a fresh row under
--   the new key (its previous_output_digest lookup finds none, so the first output_changed reads null). Because mi_bhavisya has NO receipt or
--   freshness row today, nothing is stranded. THE MIGRATION ENFORCES THAT: it raises (changing nothing) if any asset_provenance_receipts or
--   asset_freshness row exists for mi_bhavisya, so it can never silently strand one. If one appears before apply, that is a decision for SS
--   (re-key the rows in the same migration, or accept a fresh start); a rebuild on the old text cannot help, it would write under the old key.
--
-- OTHER COLUMNS OF THE SAME ROW (read 2026-10-03, every text/jsonb column scanned for delete/replace/idempot/clear/truncate/wipe): none names a delete,
-- clear or replace. Stale or imprecise but NOT touched (reported, not edited; not delete-related):
--   volume_explanation 'Accumulates as predictions are logged - not a deterministic target'  (consistent with append-only; fine)
--   expected_volume_formula 'COUNT(phala_anchors WHERE chart_id = $chart)' and expected_volume_inputs.derivation 'one frozen prediction per L4 anchor
--     for the chart': no longer exact once predictions are cumulative (production holds 139 predictions on the canonical chart against 4 current
--     anchors, and a re-identified anchor adds a new prediction beside the old one); a floor/volume ruling, not changed here.
--   clear_tables is NULL (no registry-derived clear); integrity_check_sql belongs to migration 1259 (not touched). The output-digest spec
--     (asset_output_digest_specs, migration 990) still covers only mimamsa_manifestation_sets; unchanged.
--   Outside the registry (PR #3040's list, not here): assetClearSpec.ts / assetInvalidation.ts (set to skip), the writer, the digests json.
--
-- ACTIVE RUNS (ENFORCED, not advisory): the first DO block RAISES, changing nothing, if build_runs holds a run that is not completed/failed/stopped
-- (planned, running or paused) for mi_bhavisya. 0 on 2026-10-03.
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already applied: NOTICE, nothing rewritten).
-- Any other md5 RAISES (including NULL): the migration refuses to overwrite a text it was not written against. The UPDATE is also guarded by the base
-- md5. The post-check RAISES unless the new text is stored (md5, length AND the exact text), and unless no other column of the row changed
-- relative to the pre-state (integrity_check_sql in particular).
--
-- NOT DONE HERE: integrity_check_sql (1259); the digest spec; floors / volume text; the writer and clear-spec changes of PR #3040.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103). After the deploy, as suvarna_reader, expect one row md5 a411af1488287dced6b8b121ec1eb28b, length 3544:
--   SELECT md5(natural_key_partition), length(natural_key_partition) FROM asset_registry WHERE asset_id = 'mi_bhavisya';
-- and no freshness / receipt rows for the asset:
--   SELECT count(*) FROM asset_freshness WHERE asset_id = 'mi_bhavisya';   SELECT count(*) FROM asset_provenance_receipts WHERE asset_id = 'mi_bhavisya';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET natural_key_partition = <migration 991's literal, md5 07d729f8f0487ac3d3ddb114dd4cdc73> WHERE asset_id = 'mi_bhavisya';
-- (same trigger and key consequences; only sensible if PR #3040 is reverted).

SET LOCAL lock_timeout = '5s';

DO $runs$
DECLARE n_active int;
BEGIN
    SELECT count(*) INTO n_active
      FROM public.build_runs r JOIN public.build_run_assets a ON a.run_id = r.id
     WHERE a.asset_id = 'mi_bhavisya' AND r.state NOT IN ('completed', 'failed', 'stopped');
    IF n_active > 0 THEN
        RAISE EXCEPTION '1276: % active build run(s) (planned/running/paused) for mi_bhavisya; refusing to change its partition declaration under a running build', n_active;
    END IF;
END
$runs$;

DO $pre$
DECLARE v_md5 text; v_n int; v_old_row jsonb; v_fresh bigint; v_rcpt bigint;
BEGIN
  SELECT count(*), max(md5(natural_key_partition)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'mi_bhavisya';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1276: expected exactly one mi_bhavisya registry row, found %', v_n;
  END IF;
  IF v_md5 = 'a411af1488287dced6b8b121ec1eb28b' THEN
    RAISE NOTICE '1276: mi_bhavisya natural_key_partition already carries the append-only text; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '07d729f8f0487ac3d3ddb114dd4cdc73' THEN
    RAISE EXCEPTION '1276: mi_bhavisya natural_key_partition is not the text this migration was written against (md5 %)', v_md5;
  ELSE
    SELECT count(*) INTO v_fresh FROM public.asset_freshness WHERE asset_id = 'mi_bhavisya';
    SELECT count(*) INTO v_rcpt FROM public.asset_provenance_receipts WHERE asset_id = 'mi_bhavisya';
    IF v_fresh > 0 OR v_rcpt > 0 THEN
      RAISE EXCEPTION '1276: mi_bhavisya has % asset_freshness and % asset_provenance_receipts row(s) keyed by the old natural_key_partition text; changing the text would strand them (the text is the partition key). Ask SS: re-key them or accept a fresh start', v_fresh, v_rcpt;
    END IF;
  END IF;
END
$pre$;

CREATE TEMP TABLE _m1276_before ON COMMIT DROP AS
  SELECT to_jsonb(r) - 'natural_key_partition' AS rest FROM asset_registry r WHERE asset_id = 'mi_bhavisya';

UPDATE asset_registry
SET natural_key_partition = $nkp$mimamsa_manifestation_sets (chart_id, prediction_id, channel_id) -- MiBhavisyaWriter (@register('mi_bhavisya')) is the confirmed sole live BUILD-TIME writer of this table (grepped tree-wide for INSERT/UPDATE/DELETE across pipeline/orchestrator/writers/*.py and brahmagyan/, excluding this writer's own file and tests/: mi_sambandha.py and mi_pramana.py both only read it via SELECT, neither is a writer). The key matches the table's own live PRIMARY KEY exactly. APPEND-ONLY (SS N-104 / N-107; PR #3040, 00_ARCHITECTURE/briefs/suvarna/layers/L5/MI_BHAVISYA_APPEND_ONLY_v1_0.md): the writer never DELETEs or UPDATEs a row of this table or of mimamsa_predictions, never TRUNCATEs, and has no ON CONFLICT DO UPDATE. Every insert is ON CONFLICT DO NOTHING (predictions on (chart_id, prediction_id), sets on (chart_id, prediction_id, channel_id)), and a manifestation set is inserted only together with a prediction inserted in the same run. A rebuild therefore ADDS rows for anchors not yet frozen and leaves every existing row byte-identical: the row set per chart is CUMULATIVE (it grows; a re-identified anchor adds a new prediction and set and leaves the old pair), not the current run's row set. TWO-PART NATURAL KEY of a prediction, used to decide whether an anchor is already frozen: prediction_id = 'pred_<anchor_id>' (the freeze-time key) OR source_pramana_id = '<anchor_id>' (the current anchor reference; migration 680 re-pointed source_pramana_id to the deterministic anchor id and left prediction_id alone, so the primary key (chart_id, prediction_id) alone would add duplicates). Idempotency therefore rests on the existing-key skip plus the ON CONFLICT DO NOTHING guard, not on a delete: a rebuild with no new anchor inserts nothing and leaves this asset's output digest unchanged (output_changed false), and an insert changes it. Last verified against the live table (2026-10-03, read-only): 195 rows, 0 duplicate (chart_id, prediction_id, channel_id) groups, 0 NULL keys, a set for every prediction and a prediction for every set. Surrogate/non-owned column excluded from the digest value columns: frozen_at (a write-time stamp, a wall-clock artifact, same exclusion class as created_at used throughout this campaign; each row keeps the value it was inserted with). DELIBERATELY NOT COVERED by this partition declaration (the digest spec of migration 990 is unchanged): mimamsa_predictions. Its driving_signals field is populated, per prediction, from either a per-domain or chart-wide top-5-by-computed_salience pick over an ORDER BY computed_salience DESC-but-untied bodha_msr_signals query (recorded at the authoring of migration 991: REAL ties at the top-5 cutoff in 9 of 10 domains checked on the canonical chart, including one domain, relationship, where the entire 14-row candidate set shares one tied salience value), so which signal_ids land in the top-5 of a NEW row is not guaranteed stable; append-only means such a row is never rewritten after insert, but this declaration still does not claim coverage of it; flagged on #1770 for a future writer fix (e.g. a secondary ORDER BY tiebreak key such as signal_id), not fabricated here per SS N.8. Separately, recorded at the same time and not re-verified here, and not itself a blocker since it never executes: brahmagyan/mimamsa/prediction_ledger.py's log_prediction API route (POST /api/brahma/mimamsa/log_prediction) targets column names that do not exist on the live mimamsa_predictions schema, so any call would raise psycopg.errors.UndefinedColumn; flagged on #1770.$nkp$
WHERE asset_id = 'mi_bhavisya'
  AND md5(natural_key_partition) = '07d729f8f0487ac3d3ddb114dd4cdc73';

DO $post$
DECLARE v_md5 text; v_len int; v_txt text; v_rest jsonb;
BEGIN
  SELECT md5(natural_key_partition), length(natural_key_partition), natural_key_partition INTO v_md5, v_len, v_txt FROM asset_registry WHERE asset_id = 'mi_bhavisya';
  IF v_md5 IS DISTINCT FROM 'a411af1488287dced6b8b121ec1eb28b' OR v_len IS DISTINCT FROM 3544 THEN
    RAISE EXCEPTION '1276: the new mi_bhavisya natural_key_partition did not take (md5 %, length %)', v_md5, v_len;
  END IF;
  IF position('idempotent DELETE' IN v_txt) > 0 OR v_txt NOT LIKE 'mimamsa_manifestation_sets (chart_id, prediction_id, channel_id) -- %' OR v_txt NOT LIKE '%APPEND-ONLY%' OR v_txt NOT LIKE '%TWO-PART NATURAL KEY%' THEN
    RAISE EXCEPTION '1276: the stored mi_bhavisya natural_key_partition is not the append-only text';
  END IF;
  SELECT to_jsonb(r) - 'natural_key_partition' INTO v_rest FROM asset_registry r WHERE asset_id = 'mi_bhavisya';
  IF v_rest IS DISTINCT FROM (SELECT rest FROM _m1276_before) THEN
    RAISE EXCEPTION '1276: another column of the mi_bhavisya registry row changed';
  END IF;
END
$post$;
