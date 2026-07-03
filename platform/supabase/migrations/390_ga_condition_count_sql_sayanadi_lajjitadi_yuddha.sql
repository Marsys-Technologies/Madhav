-- Migration 390: extend ga_condition count_sql to include P3A L1 extension categories
--
-- P3A (mig 385-389) added three new fact_category values written by ga_condition_writer:
--   graha_avastha_sayanadi   — sayana (sleeping) avastha, 9 rows × 5 ayanamshas per chart
--   graha_avastha_lajjitadi  — lajjitadi avasthas (6 subtypes), 9 rows × 5 ayanamshas
--   graha_yuddha             — planetary war records, 3-4 rows × 5 ayanamshas per chart
--
-- These are chart_facts rows NOT matched by the existing LIKE 'graha_avastha_%_per_varga'
-- pattern (sayanadi and lajjitadi are base categories, not per-varga; yuddha has a
-- different prefix entirely). The cockpit stats route reads count_sql via $1 substitution;
-- without this fix the ga_condition count understates the asset's total output.
--
-- Fix: extend the chart_facts subquery to OR-in the three new categories.
-- Reference: BA pre-rebuild audit M1; [verify-against: prod] after cockpit L1 rebuild.

UPDATE asset_registry
SET count_sql = $$SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1)
       + (SELECT count(*) FROM chart_facts
          WHERE chart_id = $1
            AND (fact_category LIKE 'graha_avastha_%_per_varga'
                 OR fact_category = 'graha_avastha_sayanadi'
                 OR fact_category = 'graha_avastha_lajjitadi'
                 OR fact_category = 'graha_yuddha')) AS count$$
WHERE asset_id = 'ga_condition';
