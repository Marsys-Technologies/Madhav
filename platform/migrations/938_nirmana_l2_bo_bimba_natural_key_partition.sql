-- 938_nirmana_l2_bo_bimba_natural_key_partition.sql
--
-- NIRMĀṆA L1 — RESOLUTION_L1 v5 priority 3 (chain pre-clear). Sibling to
-- migration 937 (bo_bimba's output-digest spec) -- see 937 for the full
-- shared-table ownership investigation. `bodha_cgm_nodes` is written by TWO
-- writers (`bo_bimba.py`: node_type IN graha/bhava/domain/yoga/dosha;
-- `bo_karanajala.py`: node_type IN arudha/special_lagna, added under D-2
-- Lane V-4). Live-verified split on the canonical chart (482012f1):
-- graha=45, bhava=60, domain=65, dosha=16, yoga=69 (255 rows, bo_bimba) vs
-- arudha=95, special_lagna=35 (130 rows, bo_karanajala) -- 385 total, zero
-- overlap. Records bo_bimba's partition using the same free-text convention
-- as 908/909/910/927 (`<table>.<column> IN (...)`, values in the same order
-- as 937's `where_in` list).
--
-- bo_karanajala's own `natural_key_partition` is a separate, not-yet-closed
-- gap (still NULL as of this migration) -- left for a following migration in
-- this series, not addressed here.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_cgm_nodes.node_type IN (bhava, domain, dosha, graha, yoga)'
 WHERE asset_id = 'bo_bimba'
   AND natural_key_partition IS NULL;
