-- 678_nirmana_l3_f_parva_2_volume_explanation.sql
--
-- NIRMĀṆA L3 Kāla — W3. Discharges F-PARVA-2 (L3_W1_ANALYSIS_BATCH_E.md, ka_jivana_parva
-- finding 2, §N.7 narration fidelity): `asset_registry.volume_explanation` for
-- `ka_jivana_parva` reads "One row per mahadasha (typically 9 for a full Vimshottari
-- cycle)" — a description of the MD-only design this writer explicitly superseded at D7
-- (MD + AD) and O6 (+ PD of the currently-running AD; see the writer's own module
-- docstring, pipeline/orchestrator/writers/ka_jivana_parva.py). Measured live on the
-- canonical chart: 100 rows, not ~9 — the stale description is 11x wrong and describes a
-- design this asset no longer implements. The cockpit reads this table's metadata directly,
-- so a stale description here is a live, reader-facing narration defect, not dead text.
--
-- Corrected text names all three levels this writer actually emits (matching the writer's
-- own module docstring verbatim in spirit): one row per lived mahādaśā (MD), one per
-- antardaśā (AD) within each lived MD, and one per pratyantardaśā (PD) of the currently-
-- running AD only — never a fixed row count, since the T-9 pre-birth clip and the
-- currently-running-AD-only PD scope both make the total chart-dependent.
--
-- Deliberately NOT done here (a separate, larger step — F-PARVA-1, MUST): adding a
-- `parva_level` column so a consumer can machine-distinguish MD/AD/PD rows without
-- string-parsing `source_citation`. That needs a schema change + writer change + a new
-- natural key and does not belong in a metadata-text-only migration.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
SET volume_explanation = 'One row per lived mahādaśā (MD, pre-birth-clipped per T-9), one row per antardaśā (AD) within each lived MD, and one row per pratyantardaśā (PD) of the currently-running AD only — not a fixed count (measured 100 on the canonical chart). MD-only was the pre-D7/O6 design and no longer describes this writer.'
WHERE asset_id = 'ka_jivana_parva';
