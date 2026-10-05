-- 1299_bo_sangati_integrity_conjunct3_invariant.sql
--
-- Suvarna S-L2 FAST PATH (number 1299 allocated by SS; owner-surrogate ruling option (a) via Strategic Suvarna): replace ONE
-- conjunct of asset_registry.integrity_check_sql of bo_sangati with the relation that actually holds. ONE md5-guarded UPDATE of ONE
-- column of ONE asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT
-- here). Data-only: no table or function is created or altered, so it runs as the routine role (no CREATE on public).
--
-- THE DEFECT. Conjunct 3 of migration 712's check says
--     NOT EXISTS (SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count != shared_factor_count)
-- on the premise (712's header, item 3) that "both columns are set from the same len(shared_ids)". That was true when 712 was written
-- and stopped being true when the writer changed: pipeline/orchestrator/writers/bo_sangati.py now writes
--     shared_signal_count = len(shared_ids)                (the number of shared signals in the cell)
--     shared_factor_count = len(shared_root_groups)        (the number of DISTINCT constituent-fact roots across those signals,
--                                                           _signal_root_groups: shared_factor_keys_jsonb roots, else
--                                                           constituent_facts_array)
-- Those two numbers legitimately differ as soon as one signal cites several facts or several signals cite the same fact. The old data
-- was one fact per signal, so they coincided; a replay on patched-laksana rows gave 28 of 56 cells with the counts unequal. The
-- conjunct would therefore turn bo_sangati's integrity check false on a CORRECT build and block S-L2 run 2.
--
-- THE REPLACEMENT (what IS invariant). A cell carries shared roots exactly when it carries shared signals, and neither count is
-- negative. Both columns are NOT NULL (read from the production schema), so the new term has the same NULL behaviour as the old one:
--     NOT EXISTS (SELECT 1 FROM bodha_cdlm_cells
--                 WHERE shared_signal_count < 0
--                    OR shared_factor_count < 0
--                    OR (shared_signal_count > 0) != (shared_factor_count > 0))
-- It still catches: a cell with signals but no roots, a cell with roots but no signals, a negative count. Conjunct 4 (shared_signal_count
-- > 0 for every stored cell) and 5 (array_length(shared_signal_ids_array) = shared_signal_count) are UNCHANGED and keep the signal
-- count honest. Every other conjunct (1, 2, 4..12) is BYTE-IDENTICAL to the live text (a static test proves the new text is the old
-- text with exactly this one block replaced).
--     Residual premise, stated plainly: "has signals => has roots" assumes every signal in a stored cell cites at least one fact
--     (constituent_facts_array or shared_factor_keys_jsonb). The writer's own contract (B2 / N.5) requires that, and 0 of 150,720 live
--     bodha_msr_signals rows have an empty constituent_facts_array (read 2026-10-05). If a later build produces a legitimate cell whose
--     signals all carry no facts, this term would flag it, and the ruling's fallback applies: drop the term entirely.
--
--   OLD (live, read 2026-10-05 as suvarna_reader; md5 0fb89ae68f370d02bada11f492f662f7, 2455 chars; = migration 712's text)
--   NEW (md5 222188fd9a48644176f34311fd3ea5f6, 2539 chars)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents: 1259, 1297). The UPDATE is guarded by md5(integrity_check_sql) of the
-- OLD text, so it only ever replaces the exact text it was written against. If the live text is anything else the UPDATE matches 0
-- rows and the migration is a NOTICE-and-NO-OP that does not fail the deploy (the NOTICE names the md5 found); the check then keeps
-- whatever text it has until reconciled by hand. If the live text already equals the NEW text it is an idempotent no-op (NOTICE,
-- nothing rewritten, trigger not fired). The ONE case that RAISES: the post-check finds the row still carries the OLD md5 (the UPDATE
-- silently did nothing; never trust a silent no-op, CLAUDE.md N.4 / Trap 103).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). `UPDATE ... SET integrity_check_sql` fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN
-- (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets asset_freshness.freshness_state =
-- 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. So applying this STALES bo_sangati's freshness rows (every chart
-- that holds one). That is ACCEPTED by the ruling: bo_sangati is rebuilt in S-L2 run 2, which writes fresh receipts. No other asset is
-- touched (the trigger is keyed on NEW.asset_id). A re-run is a no-op (updates 0 rows, does not fire the trigger).
--
-- NO ACTIVE-RUN GUARD (unlike 1259), on purpose: the ruling asks for NOTICE-and-no-op on mismatch and a raise only when the update
-- silently did not take. The check text is read when an asset's integrity check runs; a build that straddles the apply reads the new
-- text at its next check, which is the intended effect.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103: never trust a deploy log). After the deploy, as suvarna_reader, expect
-- md5 222188fd9a48644176f34311fd3ea5f6 and length 2539:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'bo_sangati';
-- and bo_sangati asset_freshness rows stale/registry_changed until run 2 rebuilds it:
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness WHERE asset_id = 'bo_sangati';
--
-- NOT CHANGED HERE: any other conjunct, any other asset's check, the writer, the TypeScript (bo_sangati's integrity text is not carried
-- by any TypeScript seed; its only source is migration 712, which is never edited after apply), any data row.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <the text of migration 712, md5 above>
-- WHERE asset_id = 'bo_sangati' AND md5(integrity_check_sql) = '222188fd9a48644176f34311fd3ea5f6'; fires the same trigger. Restoring
-- the old text makes the check false again on any build whose cells hold more than one fact per signal.

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'bo_sangati';
  IF v_n = 0 THEN
    RAISE NOTICE '1299: no bo_sangati registry row (empty registry); nothing to do';
  ELSIF v_md5 = '222188fd9a48644176f34311fd3ea5f6' THEN
    RAISE NOTICE '1299: bo_sangati integrity_check_sql already carries the invariant conjunct 3; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '0fb89ae68f370d02bada11f492f662f7' THEN
    RAISE NOTICE '1299: bo_sangati integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE domain_row >= domain_col
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE domain_row NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
    OR domain_col NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE shared_signal_count < 0
       OR shared_factor_count < 0
       OR (shared_signal_count > 0) != (shared_factor_count > 0)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count <= 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE array_length(shared_signal_ids_array, 1) IS NULL
       OR array_length(shared_signal_ids_array, 1) != shared_signal_count
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE domain_relationship_class != (
      CASE
        WHEN net_linkage_strength >= 2000 THEN 'positive_strong'
        WHEN net_linkage_strength >= 500 THEN 'positive_moderate'
        WHEN net_linkage_strength > 0 THEN 'positive_weak'
        WHEN net_linkage_strength = 0 THEN 'neutral'
        ELSE 'inverse'
      END
    )
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cdlm_cells
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != count(DISTINCT top_k_rank_in_snapshot)
        OR min(top_k_rank_in_snapshot) != 1
        OR max(top_k_rank_in_snapshot) != count(*)
  )
  AND NOT EXISTS (
    SELECT 1
    FROM bodha_cdlm_cells a
    JOIN bodha_cdlm_cells b
      ON a.chart_id = b.chart_id AND a.ayanamsha_id = b.ayanamsha_id
     AND b.top_k_rank_in_snapshot = a.top_k_rank_in_snapshot + 1
    WHERE a.computed_linkage_strength < b.computed_linkage_strength
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence
    WHERE domain NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence WHERE convergence_count <= 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence WHERE array_length(top_signal_ids_array, 1) > 5
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, domain FROM bodha_convergence
    GROUP BY 1, 2, 3
    HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_sangati'
   AND md5(integrity_check_sql) = '0fb89ae68f370d02bada11f492f662f7';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bo_sangati';
  IF v_md5 = '0fb89ae68f370d02bada11f492f662f7' THEN
    RAISE EXCEPTION '1299: bo_sangati integrity_check_sql update did not take (still the old text)';
  END IF;
END
$post$;
