-- 1030_nirmana_l2_shared_msr_consumer_dependencies.sql
-- Migration 1030: order shared MSR consumers after all producers
-- Created: 2026-09-11
--
-- Six assets insert rows into bodha_msr_signals: bo_laksana plus five
-- satellite producers. Every writer that scans that shared relation as a
-- complete input must declare the full producer set rather than relying on a
-- low historical sort_order.
--
-- Bimba builds a node per signal. Samskara embeds every signal. Grounding
-- classifies every signal's source evidence. Karanajala builds the graph from
-- the completed Bimba node set and full signals. Rerank consumes Karanajala's
-- completed graph/contradictions and updates the full signal set. Sangati is
-- terminal among these shared-table consumers and reads the reranked signals.
--
-- The resulting post-producer order is Bimba 24, supporting Grounding 25,
-- Samskara 26, Karanajala 27, rerank 28, and Sangati 29. Only existing rows
-- are updated; registry identity and the frozen 128-asset denominator do not
-- change.

BEGIN;

UPDATE asset_registry
   SET depends_on = ARRAY[
         'bo_laksana', 'bo_sudarshana', 'bo_nakshatra_semantic',
         'bo_arudha', 'bo_special_lagna', 'bo_vargottama_dhana'
       ]::text[],
       sort_order = 24
 WHERE asset_id = 'bo_bimba';

UPDATE asset_registry
   SET depends_on = ARRAY[
         'ga_yoga', 'bo_laksana', 'bo_sudarshana',
         'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
         'bo_vargottama_dhana'
       ]::text[],
       sort_order = 25
 WHERE asset_id = 'bo_grounding';

UPDATE asset_registry
   SET depends_on = ARRAY[
         'bo_arudha', 'bo_laksana', 'bo_nakshatra_semantic',
         'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana'
       ]::text[],
       sort_order = 26
 WHERE asset_id = 'bo_samskara';

UPDATE asset_registry
   SET depends_on = ARRAY[
         'bo_laksana', 'bo_bimba', 'ga_positions', 'bo_sudarshana',
         'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
         'bo_vargottama_dhana'
       ]::text[],
       sort_order = 27
 WHERE asset_id = 'bo_karanajala';

UPDATE asset_registry
   SET depends_on = ARRAY[
         'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
         'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
         'bo_vargottama_dhana'
       ]::text[],
       sort_order = 28
 WHERE asset_id = 'bo_laksana_rerank';

UPDATE asset_registry
   SET depends_on = ARRAY[
         'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
         'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
         'bo_vargottama_dhana', 'bo_laksana_rerank'
       ]::text[],
       sort_order = 29
 WHERE asset_id = 'bo_sangati';

DO $$
DECLARE
  corrected_count integer;
BEGIN
  SELECT count(*)
    INTO corrected_count
    FROM asset_registry
   WHERE (asset_id, sort_order, depends_on) IN (
     ('bo_bimba', 24, ARRAY[
       'bo_laksana', 'bo_sudarshana', 'bo_nakshatra_semantic',
       'bo_arudha', 'bo_special_lagna', 'bo_vargottama_dhana'
     ]::text[]),
     ('bo_grounding', 25, ARRAY[
       'ga_yoga', 'bo_laksana', 'bo_sudarshana',
       'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
       'bo_vargottama_dhana'
     ]::text[]),
     ('bo_samskara', 26, ARRAY[
       'bo_arudha', 'bo_laksana', 'bo_nakshatra_semantic',
       'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana'
     ]::text[]),
     ('bo_karanajala', 27, ARRAY[
       'bo_laksana', 'bo_bimba', 'ga_positions', 'bo_sudarshana',
       'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
       'bo_vargottama_dhana'
     ]::text[]),
     ('bo_laksana_rerank', 28, ARRAY[
       'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
       'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
       'bo_vargottama_dhana'
     ]::text[]),
     ('bo_sangati', 29, ARRAY[
       'bo_laksana', 'bo_karanajala', 'bo_sudarshana',
       'bo_nakshatra_semantic', 'bo_arudha', 'bo_special_lagna',
       'bo_vargottama_dhana', 'bo_laksana_rerank'
     ]::text[])
   );

  IF corrected_count <> 6 THEN
    RAISE EXCEPTION 'shared-MSR consumer registry correction applied to % of 6 exact rows', corrected_count;
  END IF;

  IF EXISTS (
    SELECT 1
      FROM asset_registry
     WHERE layer = 'bodha'
       AND sort_order BETWEEN 24 AND 29
       AND asset_id NOT IN (
         'bo_bimba', 'bo_grounding', 'bo_samskara', 'bo_karanajala',
         'bo_laksana_rerank', 'bo_sangati'
       )
  ) THEN
    RAISE EXCEPTION 'Bodha sort_order 24 through 29 is occupied outside the corrected consumer set';
  END IF;
END
$$;

COMMIT;
