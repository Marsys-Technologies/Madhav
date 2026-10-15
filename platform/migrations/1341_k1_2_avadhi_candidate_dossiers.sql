-- Migration 1341: K1-2 pinned F2/F1 candidate period dossiers.
-- Created: 2026-10-10. NEEDS-PROTECTED-WINDOW (constraint/index replacement).
-- migrate.ts owns the transaction. Legacy dates, payloads and ids are retained.
SET LOCAL lock_timeout = '5s';

ALTER TABLE public.kala_avadhi
    ADD COLUMN IF NOT EXISTS generation text NOT NULL DEFAULT 'legacy',
    ADD COLUMN IF NOT EXISTS source_dasha_row_id uuid,
    ADD COLUMN IF NOT EXISTS source_dasha_build_id uuid,
    ADD COLUMN IF NOT EXISTS source_natal_build_id uuid,
    ADD COLUMN IF NOT EXISTS ayanamsha_id text,
    ADD COLUMN IF NOT EXISTS tier text,
    ADD COLUMN IF NOT EXISTS period_start_iso timestamptz,
    ADD COLUMN IF NOT EXISTS period_end_iso timestamptz;

ALTER TABLE public.kala_avadhi DROP CONSTRAINT IF EXISTS kala_avadhi_chart_id_system_id_level_n_period_start_key;
ALTER TABLE public.kala_avadhi DROP CONSTRAINT IF EXISTS kala_avadhi_level_n_check;
DO $constraints$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.kala_avadhi'::regclass
                   AND conname='kala_avadhi_level_n_candidate_check') THEN
        ALTER TABLE public.kala_avadhi ADD CONSTRAINT kala_avadhi_level_n_candidate_check
            CHECK (level_n BETWEEN 1 AND 4);
    END IF;
END $constraints$;
-- Retain the old natural key within the immutable legacy partition. F2's
-- exact instants distinguish sub-periods which begin on the same civil date.
CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_avadhi_legacy_period
    ON public.kala_avadhi(chart_id,system_id,level_n,period_start) WHERE generation='legacy';
CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_avadhi_candidate_period
    ON public.kala_avadhi(chart_id,generation,source_dasha_row_id) WHERE generation<>'legacy';

DO $registry$
DECLARE old_check text;
BEGIN
    SELECT integrity_check_sql INTO old_check FROM asset_registry WHERE asset_id='ka_avadhi';
    IF old_check IS NULL OR position('AS integrity_passed' IN old_check)=0 THEN
        RAISE EXCEPTION 'K1-2 requires the retained Avadhi integrity contract';
    END IF;
    IF old_check NOT LIKE 'WITH k1_legacy_avadhi AS%' THEN
        UPDATE asset_registry SET integrity_check_sql =
          'WITH k1_legacy_avadhi AS (SELECT * FROM kala_avadhi WHERE generation=''legacy'') '
          || replace(replace(old_check, 'kala_avadhi', 'k1_legacy_avadhi'), 'AS integrity_passed', $candidate$
          AND NOT EXISTS (
            SELECT 1 FROM kala_avadhi a WHERE generation<>'legacy' AND (
              quality IS NOT NULL OR source_dasha_row_id IS NULL OR source_natal_build_id IS NULL
              OR NOT EXISTS (SELECT 1 FROM chart_dashas d WHERE d.dasha_row_id=a.source_dasha_row_id
                AND d.chart_id=a.chart_id AND d.build_id=a.source_dasha_build_id
                AND d.ayanamsha_id=a.ayanamsha_id AND d.verification_pass_status=a.tier
                AND d.system_id=a.system_id AND d.level_n=a.level_n AND d.lord_graha=a.lord_graha
                AND d.start_iso=a.period_start_iso AND d.end_iso=a.period_end_iso)
              OR NOT EXISTS (SELECT 1 FROM kala_layer_candidate c WHERE c.chart_id=a.chart_id
                AND c.generation=a.generation
                AND c.conventions->'f2'->>'build_id'=a.source_dasha_build_id::text
                AND c.conventions->'f2'->>'ayanamsha_id'=a.ayanamsha_id
                AND c.conventions->'f2'->>'tier'=a.tier
                AND c.conventions->'natal'->>'build_id'=a.source_natal_build_id::text)
              OR NOT (a.dossier->'lord_condition' ? 'value')
              OR (a.dossier->'lord_condition'->>'null_reason' IS NULL
                  AND COALESCE(a.dossier->'lord_condition'->'value','null'::jsonb)='null'::jsonb)
              OR EXISTS (SELECT 1 FROM jsonb_array_elements(a.dossier->'lord_condition_fact_refs') f
                WHERE NOT EXISTS (SELECT 1 FROM chart_facts n WHERE n.chart_id=a.chart_id
                  AND n.build_id=a.source_natal_build_id AND n.ayanamsha_id=a.ayanamsha_id
                  AND n.fact_id=f->>'fact_id'))
              OR EXISTS (SELECT 1 FROM jsonb_array_elements(a.dossier->'attached_mechanisms') m
                WHERE NOT EXISTS (SELECT 1 FROM kala_activation_predicates p WHERE p.chart_id=a.chart_id
                  AND p.generation=a.generation AND p.ayanamsha_id=a.ayanamsha_id
                  AND p.mechanism_id=m->>'mechanism_id'
                  AND p.conclusion_state_jsonb->>'effective_state'=m->>'effective_state'))
            )
          ) AS integrity_passed
          $candidate$)
        WHERE asset_id='ka_avadhi';
    END IF;
    UPDATE asset_registry SET depends_on=ARRAY['ga_positions','ga_dashas','ka_yojaka','ka_dasha_kala']::text[],
      count_sql='SELECT COUNT(*) FROM kala_avadhi WHERE chart_id=$1 AND generation=COALESCE((SELECT generation FROM kala_layer_head WHERE chart_id=$1),''legacy'')'
    WHERE asset_id='ka_avadhi';
END $registry$;
