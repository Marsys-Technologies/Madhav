-- 655_nirmana_l1_ga_strength_shadbala_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_strength's graha_shadbala_total
-- fact_category: integrity_check_sql was NULL, so the freeze-time detector fell back to
-- count(*) > 0 (§N.8 -- an unearned signal).
--
-- SCOPE, read before touching anything. ga_strength writes to chart_facts, a table SHARED by
-- many L1 writers, across 26 distinct fact_categories (ashtakavarga_*, graha_shadbala_*,
-- graha_vimsopaka_*, house_bhava_bala_*, graha_ishta_phala, graha_kashta_phala -- measured live,
-- SELECT DISTINCT fact_category). This contract covers graha_shadbala_total ONLY -- the category
-- this writer's own F-C1 finding (L1_W1_ANALYSIS_BATCH_C.md) centers on and the one ga_dashas'
-- F-A12 natal-context enrichment reads. The remaining 25 categories are NOT covered here and are
-- a separate future unit, not silently assumed clean.
--
-- Standard: D-CND-03 -- chart-partitioned, attribution-preserving invariants, no bare count pin
-- (C12). chart_facts_unique_null_formula / chart_facts_unique_with_formula (partial UNIQUE
-- indexes on (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id[,
-- formula_id])) are ALREADY DB-enforced, so no distinctness conjunct appears here (D-CND-03
-- rule 4) -- ga_strength's own ON CONFLICT target (ga_strength_writer.py:1640) matches this
-- exactly, and replace_prior_chart_facts (_idempotency.py:40-56) deletes at
-- (chart_id, fact_category, ayanamsha_id) grain before every rebuild, correctly including the
-- 'INVARIANT' pseudo-ayanamsha that required_rupa rows use.
--
-- F-C1 itself is NOT this asset's own defect: the W2 DECIDE record (L1_W2_DECIDE_v1_0.md, the
-- authoritative route, superseding the earlier W1-proposal snapshot still shown in
-- L1_STATE.md's asset table) rules ga_strength `rebuild_only` -- "Writer sound and honestly
-- tiered. MUST F-C1 (shadbala selector) is serving-side" -- and the actual selector code
-- (deriveShadbalaWeakestGraha, query_ucd.ts) lives under layers/L2_bodha/, not L1. L2 has already
-- fixed it on their side (their own PR history shows the selector re-pinned to fact_key='rupa').
-- Nothing here re-encodes that finding; this contract is ga_strength's own internal-consistency
-- check, which measured clean.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_strength integrity contract (graha_shadbala_total fact_category ONLY; target table:
-- chart_facts, shared with other writers -- see this migration's header for the 25 categories
-- this contract does NOT cover).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (chart_facts_unique_null_formula/_with_formula); not
-- re-asserted here (D-CND-03 rule 4).
SELECT
  -- (a) the writer's own formula (ga_strength_writer.py:799: "ratio = achieved_total / req")
  -- re-derived directly from the two rows it divides, not a restated literal. required_rupa is
  -- looked up under ayanamsha_id='INVARIANT' specifically -- it is the one ayanamsha-independent
  -- fact_key in this category (the classical minimum threshold does not vary by ayanamsha),
  -- confirmed live before writing this join (a first draft joined same-ayanamsha and found 105
  -- false mismatches purely from that wrong assumption).
  NOT EXISTS (
    SELECT 1 FROM chart_facts r
    WHERE r.fact_category = 'graha_shadbala_total' AND r.fact_key = 'ratio'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts rupa, chart_facts req
        WHERE rupa.chart_id = r.chart_id AND rupa.ayanamsha_id = r.ayanamsha_id
          AND rupa.fact_subject = r.fact_subject
          AND rupa.fact_category = 'graha_shadbala_total' AND rupa.fact_key = 'rupa'
          AND req.chart_id = r.chart_id AND req.ayanamsha_id = 'INVARIANT'
          AND req.fact_subject = r.fact_subject
          AND req.fact_category = 'graha_shadbala_total' AND req.fact_key = 'required_rupa'
          AND req.fact_value_num <> 0
          AND abs(r.fact_value_num - (rupa.fact_value_num / req.fact_value_num)) < 1e-6
      )
  )
  -- (b) required_rupa's ayanamsha-independence must actually hold as WRITTEN, not just as
  -- intended: exactly one row per (chart, subject), never zero (silently dropped) or more than
  -- one (an emit-loop bug or a build that failed to clear a stale extra). Not redundant with the
  -- partial UNIQUE indexes, which key on (..., ayanamsha_id, ..., build_id[, formula_id]) and so
  -- permit two different build_ids' INVARIANT rows to coexist if a rebuild's delete scope ever
  -- missed this category.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_shadbala_total' AND fact_key = 'required_rupa'
    GROUP BY chart_id, fact_subject
    HAVING count(*) <> 1
  )
  -- (c) range guard: chart_facts carries no CHECK on fact_value_num at all. Shadbala rupas and
  -- their ratio can never be negative (a strength score), and required_rupa specifically can
  -- never be zero (conjunct (a)'s division depends on it, and a classical minimum of zero rupas
  -- has no meaning).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_shadbala_total'
      AND fact_key = ANY (ARRAY['rupa', 'ratio', 'required_rupa'])
      AND (fact_value_num IS NULL OR fact_value_num < 0)
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_shadbala_total' AND fact_key = 'required_rupa'
      AND fact_value_num = 0
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_strength';
