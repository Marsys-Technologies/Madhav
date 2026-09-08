-- 927_nirmana_l2_bo_arudha_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 908/909/910 -- see 908 for the full
-- partition_undeclared rationale (migrations 868-874, adjudication #2180;
-- bo_sudarshana's own fix, migration 880). Authored ahead of bo_arudha's W4
-- dispatch under RESOLUTION_L2 v3 priority 1 (Conductor-directed recovery of
-- the never-W1/W2-recorded asset), alongside its output-digest spec
-- (migration 926).
--
-- bo_arudha's own ownership, verified directly against the orchestrator
-- writer's declared allowlist (BO_ARUDHA_OWNED_SIGNAL_TYPE_CLASSES =
-- ["arudha"], pipeline/orchestrator/writers/bo_arudha.py:39) and
-- bodha_writers/arudha_emitter.py's single declared class constant
-- (SIGNAL_TYPE_CLASS = "arudha", line 42) -- ONE signal_type_class, like
-- 908/909's assets. Confirmed live on production (canonical chart): exactly
-- 25 rows at signal_type_class='arudha' (5 ayanamshas x 5 signals: 1
-- AL_bhava_relation + 2 tenancy [A2, A11] + 2 AL_conjunction [SUN, MER],
-- consistent with the 710 integrity contract's per-ayanamsha shape), no
-- other co-writer emits this class.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class = arudha'
 WHERE asset_id = 'bo_arudha'
   AND natural_key_partition IS NULL;
