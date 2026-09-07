-- 871_nirmana_l1_ga_sade_sati_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Fourth of seven natural_key_partition backfills authorized by the
-- Conductor's ruling on adjudication #2180 (2026-09-07). First
-- (`ga_positions`) shipped in migration 868 (PR #2205, merged); second
-- (`ga_ayurdaya`) in migration 869 (PR #2208); third (`ga_sensitive_
-- degree`) in migration 870 (PR #2209); this is the fourth.
--
-- `ga_sade_sati`'s ownership verified directly against
-- `ga_sade_sati_writer.py`'s own fact_category literals (grepped for
-- every `sade_sati_*`/`*_shani_period`/`dhaiya_period` string): 14
-- categories -- `sade_sati_cycle`, `sade_sati_phase`,
-- `sade_sati_phase_quarter`, `sade_sati_modifier_overlay`,
-- `sade_sati_cancellation_check`, `sade_sati_concurrent_dasha_overlay`,
-- `sade_sati_downstream_cross_reference`,
-- `sade_sati_saturn_retrograde_subset`, `janma_shani_period`,
-- `anumukha_shani_period`, `ardha_ashtama_shani_period`,
-- `ashtama_shani_period`, `dhaiya_period`, `vishakha_shani_period`,
-- `kantaka_shani_period`. All fall under two clean naming prefixes/
-- suffixes (`sade_sati_*`, `*_shani_period`) plus the one-off
-- `dhaiya_period`. Confirmed no overlap: grepped all six sibling
-- writers for the same pattern set, zero hits.
--
-- Note: `ga_sade_sati_writer.py` separately READS (never writes)
-- `argala_natal_matrix`, `graha_position`, `tara_bala_natal_baseline`,
-- `varga_karya_bhava_per_varga`, `varga_position` from other assets'
-- own chart_facts rows (confirmed during this session's earlier DAG
-- audit, cycle 144) -- those are not this asset's partition.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category IN (sade_sati_cycle, sade_sati_phase, sade_sati_phase_quarter, sade_sati_modifier_overlay, sade_sati_cancellation_check, sade_sati_concurrent_dasha_overlay, sade_sati_downstream_cross_reference, sade_sati_saturn_retrograde_subset, janma_shani_period, anumukha_shani_period, ardha_ashtama_shani_period, ashtama_shani_period, dhaiya_period, vishakha_shani_period, kantaka_shani_period)'
 WHERE asset_id = 'ga_sade_sati'
   AND natural_key_partition IS NULL;
