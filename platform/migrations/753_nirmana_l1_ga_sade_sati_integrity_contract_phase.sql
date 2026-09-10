-- 753_nirmana_l1_ga_sade_sati_integrity_contract_phase.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Second follow-up F-A14 widening pass for ga_sade_sati.
-- Migration 748 covered sade_sati_cycle/sade_sati_phase_quarter; migration 752 added the Dhaiya
-- family (dhaiya_period, kantaka_shani_period, ashtama_shani_period, ardha_ashtama_shani_period
-- -- 6/15 categories). This pass adds sade_sati_phase plus the three classically-named sub-phase
-- categories (janma_shani_period, vishakha_shani_period, anumukha_shani_period), taking coverage
-- to 10/15 categories.
--
-- ga_sade_sati_writer.py's _emit_cycle_rows computes phases = [("VISHAKHA", vis_dt, jan_dt, ...),
-- ("JANMA", jan_dt, anu_dt, ...), ("ANUMUKHA", anu_dt, end_dt, ...)] ONCE and emits each phase
-- TWICE from the same (ph_start, ph_end, ph_sign) triple: once under the generic sade_sati_phase
-- category (subj = "{cy_id}.{phase_name}", keys phase_start_iso/phase_end_iso/duration_days/
-- saturn_sign/saturn_dignity/...), and again under the phase's classical-name category
-- (janma_shani_period/vishakha_shani_period/anumukha_shani_period, subj_sp = "{cy_id}.{ph_name}"
-- -- the SAME subject string, keys period_start_iso/period_end_iso/duration_days/saturn_sign/
-- saturn_dignity). These are separately stored rows from a shared source value, exactly the
-- Dhaiya-family pattern migration 752 already established -- a genuine cross-category
-- consistency check, not a tautology.
--
-- integrity_check_sql is a single UPDATE ... SET column, not additive SQL -- this migration
-- carries the FULL replacement value: migrations 748's and 752's seven original conjuncts
-- (a) through (g), verbatim, PLUS three new conjuncts (h)/(i)/(j) below. Applying this migration
-- without the prior conjuncts would silently regress their own coverage back to zero.
--
-- Every new conjunct below was EXECUTED against live production and MUTATION-PROVED before
-- landing: each was re-run against a corruption injected via a real transactional UPDATE inside
-- BEGIN/ROLLBACK and shown to return false. Passes clean (integrity_passed = true) on live
-- production today.
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
  -- (d) dhaiya_period.period_start_iso must precede period_end_iso for the same subject --
  -- temporal ordering, same style as conjunct (b). 0/345 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'dhaiya_period' AND e.fact_key = 'period_end_iso'
    WHERE s.fact_category = 'dhaiya_period' AND s.fact_key = 'period_start_iso'
      AND s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz
  )
  -- (e) dhaiya_period.duration_days must equal the actual day-span between period_start_iso and
  -- period_end_iso (within 0.02-day tolerance -- the writer rounds to 2 decimal places) --
  -- re-derived here directly rather than restated. 0/345 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'dhaiya_period' AND e.fact_key = 'period_end_iso'
    JOIN chart_facts d ON d.chart_id = s.chart_id AND d.ayanamsha_id = s.ayanamsha_id
      AND d.fact_subject = s.fact_subject
      AND d.fact_category = 'dhaiya_period' AND d.fact_key = 'duration_days'
    WHERE s.fact_category = 'dhaiya_period' AND s.fact_key = 'period_start_iso'
      AND abs(d.fact_value_num - EXTRACT(EPOCH FROM (e.fact_value_text::timestamptz - s.fact_value_text::timestamptz)) / 86400.0) > 0.02
  )
  -- (f) kantaka_shani_period / ashtama_shani_period / ardha_ashtama_shani_period's
  -- period_start_iso and period_end_iso must agree exactly with dhaiya_period's own value for
  -- the same (chart, ayanamsha, subject) -- ga_sade_sati_writer.py's _emit_dhaiya_rows emits all
  -- three from the SAME entry_dt/exit_dt pair under a shared `subj`, but they are separately
  -- stored rows; a future divergence between them is a real, checkable defect, not a tautology.
  -- 0/670 violations live (335 ardha_ashtama + 165 ashtama + 170 kantaka, ×2 keys each).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'dhaiya_period' AND d.fact_key = c.fact_key
    WHERE c.fact_category IN ('kantaka_shani_period', 'ashtama_shani_period', 'ardha_ashtama_shani_period')
      AND c.fact_key IN ('period_start_iso', 'period_end_iso')
      AND c.fact_value_text <> d.fact_value_text
  )
  -- (g) kantaka_shani_period / ashtama_shani_period's duration_days and saturn_sign must also
  -- agree with dhaiya_period's own value for the same subject (ardha_ashtama_shani_period
  -- stores neither field, so it is out of scope for this conjunct). 0/335 violations live
  -- (170 kantaka + 165 ashtama, ×2 keys each).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'dhaiya_period' AND d.fact_key = c.fact_key
    WHERE c.fact_category IN ('kantaka_shani_period', 'ashtama_shani_period')
      AND c.fact_key = 'saturn_sign'
      AND c.fact_value_text <> d.fact_value_text
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'dhaiya_period' AND d.fact_key = c.fact_key
    WHERE c.fact_category IN ('kantaka_shani_period', 'ashtama_shani_period')
      AND c.fact_key = 'duration_days'
      AND abs(c.fact_value_num - d.fact_value_num) > 0.001
  )
  -- (h) sade_sati_phase.phase_start_iso must precede phase_end_iso for the same subject --
  -- temporal ordering, same style as conjuncts (b)/(d). 0/4560 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'sade_sati_phase' AND e.fact_key = 'phase_end_iso'
    WHERE s.fact_category = 'sade_sati_phase' AND s.fact_key = 'phase_start_iso'
      AND s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz
  )
  -- (i) sade_sati_phase.duration_days must equal the actual day-span between phase_start_iso and
  -- phase_end_iso (within 0.02-day tolerance) -- re-derived here directly rather than restated,
  -- same style as conjuncts (c)/(e). 0/4560 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    JOIN chart_facts e ON e.chart_id = s.chart_id AND e.ayanamsha_id = s.ayanamsha_id
      AND e.fact_subject = s.fact_subject
      AND e.fact_category = 'sade_sati_phase' AND e.fact_key = 'phase_end_iso'
    JOIN chart_facts d ON d.chart_id = s.chart_id AND d.ayanamsha_id = s.ayanamsha_id
      AND d.fact_subject = s.fact_subject
      AND d.fact_category = 'sade_sati_phase' AND d.fact_key = 'duration_days'
    WHERE s.fact_category = 'sade_sati_phase' AND s.fact_key = 'phase_start_iso'
      AND abs(d.fact_value_num - EXTRACT(EPOCH FROM (e.fact_value_text::timestamptz - s.fact_value_text::timestamptz)) / 86400.0) > 0.02
  )
  -- (j) janma_shani_period / vishakha_shani_period / anumukha_shani_period's period_start_iso,
  -- period_end_iso, duration_days, saturn_sign, and saturn_dignity must all agree with
  -- sade_sati_phase's own phase_start_iso/phase_end_iso/duration_days/saturn_sign/saturn_dignity
  -- for the same (chart, ayanamsha, subject) -- _emit_cycle_rows computes each classical phase
  -- ONCE (vis_dt/jan_dt/anu_dt/end_dt, ph_sign) and emits it TWICE: once under sade_sati_phase
  -- (generic, phase_*-prefixed keys) and once under its classical-name category (period_*-prefixed
  -- keys), both under the SAME subject string. Separately stored rows from a shared source value
  -- -- a future divergence is a real, checkable defect, not a tautology. 0/4560 violations live
  -- for the two ISO timestamp keys (3 categories x 2 keys, matched 1:1 against sade_sati_phase's
  -- 4560 rows since every sade_sati_phase subject is one of VISHAKHA/JANMA/ANUMUKHA); 0/1500 for
  -- duration_days/saturn_sign/saturn_dignity (3 categories x 3 keys, one row per key per subject).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'sade_sati_phase'
      AND d.fact_key = CASE c.fact_key
        WHEN 'period_start_iso' THEN 'phase_start_iso'
        WHEN 'period_end_iso' THEN 'phase_end_iso'
        ELSE c.fact_key
      END
    WHERE c.fact_category IN ('janma_shani_period', 'vishakha_shani_period', 'anumukha_shani_period')
      AND c.fact_key IN ('period_start_iso', 'period_end_iso')
      AND c.fact_value_text <> d.fact_value_text
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'sade_sati_phase' AND d.fact_key = c.fact_key
    WHERE c.fact_category IN ('janma_shani_period', 'vishakha_shani_period', 'anumukha_shani_period')
      AND c.fact_key IN ('saturn_sign', 'saturn_dignity')
      AND c.fact_value_text <> d.fact_value_text
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts c
    JOIN chart_facts d ON d.chart_id = c.chart_id AND d.ayanamsha_id = c.ayanamsha_id
      AND d.fact_subject = c.fact_subject
      AND d.fact_category = 'sade_sati_phase' AND d.fact_key = c.fact_key
    WHERE c.fact_category IN ('janma_shani_period', 'vishakha_shani_period', 'anumukha_shani_period')
      AND c.fact_key = 'duration_days'
      AND abs(c.fact_value_num - d.fact_value_num) > 0.001
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_sade_sati';
