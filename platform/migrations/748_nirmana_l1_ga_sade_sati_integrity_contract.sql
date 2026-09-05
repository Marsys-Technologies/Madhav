-- 748_nirmana_l1_ga_sade_sati_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_sade_sati: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: chart_facts, scoped to the SAME 15-category scope this asset's own count_sql
-- already declares. This is GA9's Sade Sati writer (~2,150 lines) -- three conjuncts here are a
-- bounded first pass on the sade_sati_cycle and sade_sati_phase_quarter categories, not
-- exhaustive coverage of all 15.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_sade_sati integrity contract (target table: chart_facts, scoped to the count_sql's own
-- 15 fact_categories). D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare
-- count pin (C12). chart_facts_unique_null_formula already exactly matches the natural key --
-- no distinctness conjunct here (D-CND-03 rule 4); sade_sati_cycle additionally carries its own
-- dedicated partial UNIQUE indexes on cycle_start_iso/cycle_end_iso (ux_chart_facts_sade_sati_
-- cycle_start_value / _end_value), also not re-asserted.
SELECT
  -- (a) quarter_intensity_rationale_jsonb's first element must cite the BPHS Ch.71 base
  -- intensity classical table (PHASE_QUARTER_INTENSITY, ga_sade_sati_writer.py:147-160) for the
  -- (phase, quarter) pair encoded in fact_subject (CYCLE_N.PHASE.QN) -- re-derived here directly
  -- rather than restated. 720/720 rows matched live.
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT fact_value_jsonb->>0 AS rationale_first,
             split_part(fact_subject,'.',2) AS phase,
             substring(split_part(fact_subject,'.',3) from 2)::int AS quarter
      FROM chart_facts
      WHERE fact_category = 'sade_sati_phase_quarter'
        AND fact_key = 'quarter_intensity_rationale_jsonb'
    ) p
    JOIN (VALUES
      ('VISHAKHA',1,'Medium'), ('VISHAKHA',2,'Low'), ('VISHAKHA',3,'Low'), ('VISHAKHA',4,'Medium'),
      ('JANMA',1,'High'), ('JANMA',2,'High'), ('JANMA',3,'High'), ('JANMA',4,'Medium'),
      ('ANUMUKHA',1,'Medium'), ('ANUMUKHA',2,'Low'), ('ANUMUKHA',3,'Low'), ('ANUMUKHA',4,'Low')
    ) AS base(phase, quarter, expected) ON base.phase = p.phase AND base.quarter = p.quarter
    WHERE p.rationale_first <> ('BPHS.Ch71: ' || p.phase || '.Q' || p.quarter || ' base = ' || base.expected)
  )
  -- (b) cycle_start_iso must precede cycle_end_iso for the same cycle -- temporal ordering.
  -- 0/60 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'sade_sati_cycle' AND e.fact_key = 'cycle_end_iso'
    WHERE s.fact_category = 'sade_sati_cycle' AND s.fact_key = 'cycle_start_iso'
      AND s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz
  )
  -- (c) duration_days must equal the actual day-span between cycle_start_iso and cycle_end_iso
  -- (within 1-day tolerance) -- re-derived here directly rather than restated. 0/60 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'sade_sati_cycle' AND e.fact_key = 'cycle_end_iso'
    JOIN chart_facts d ON d.chart_id = s.chart_id AND d.ayanamsha_id = s.ayanamsha_id
      AND d.fact_subject = s.fact_subject
      AND d.fact_category = 'sade_sati_cycle' AND d.fact_key = 'duration_days'
    WHERE s.fact_category = 'sade_sati_cycle' AND s.fact_key = 'cycle_start_iso'
      AND abs(d.fact_value_num - EXTRACT(EPOCH FROM (e.fact_value_text::timestamptz - s.fact_value_text::timestamptz)) / 86400.0) > 1.0
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_sade_sati';
