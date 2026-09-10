-- 659_nirmana_l1_ga_tajaka_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_tajaka: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- This is the LAST free number in L1's 650-659 migration range (measured: checked all open L1
-- PRs' migration files before claiming it). Remaining assets needing F-A14
-- (ga_nakshatra, ga_sensitive, ga_sensitive_degree, ga_structural, ga_yoga, ga_vichara,
-- ga_sade_sati, ga_transit_anchors, ga_ayurdaya, ga_medical, ga_vastu, ga_prashna) will need a
-- newly-assigned range from a future cycle -- flagged in L1_STATE.md rather than left implicit.
--
-- Target table: l1_tajik_varsha_year_lords, a DEDICATED table. Its UNIQUE constraint
-- (chart_id, ayanamsha_id, build_id, varsha_year) INCLUDES build_id -- confirmed via
-- replace_prior_tajik_varsha's own docstring (_idempotency.py:100-108): "The table's UNIQUE key
-- includes build_id, so without [deleting regardless of build_id] a re-run would append a
-- second copy per varsha." This means the DB-level UNIQUE cannot by itself detect an accretion
-- bug (two different build_ids' rows for the same varsha coexisting) -- conjunct (a) below is
-- NOT redundant with it (D-CND-03 rule 4 is about redundant checks, not this one).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_tajaka integrity contract (target table: l1_tajik_varsha_year_lords)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
SELECT
  -- (a) §N.3 accretion detector on the semantic natural key (chart_id, ayanamsha_id,
  -- varsha_year) -- WITHOUT build_id, unlike the table's own DB UNIQUE, which by design permits
  -- two build_ids' rows to coexist for the same varsha unless replace_prior_tajik_varsha's
  -- delete-regardless-of-build_id discipline actually ran. A rebuild that skipped that delete
  -- (or a bug in its own year/chart/ayanamsha scoping) would show up here and nowhere else.
  NOT EXISTS (
    SELECT 1 FROM l1_tajik_varsha_year_lords
    GROUP BY chart_id, ayanamsha_id, varsha_year
    HAVING count(*) > 1
  )
  -- (b) window validity: every varsha (solar-return year) must be a real, forward-in-time,
  -- ~365.25-day span -- these are genuine ephemeris solar-return instants (same class of
  -- computation as ga_dashas' mudda system and ga_tajaka's own sibling ga_tithi_pravesha),
  -- so 364-367 days covers real year-length variation without asserting an exact constant.
  AND NOT EXISTS (
    SELECT 1 FROM l1_tajik_varsha_year_lords
    WHERE varsha_end_iso <= varsha_start_iso
       OR extract(epoch FROM (varsha_end_iso - varsha_start_iso)) / 86400 NOT BETWEEN 364 AND 367
  )
  -- (c) year_lord vocabulary: Tajika Varshaphal's classical year-lord (Varsheshwara) candidacy
  -- is the seven classical grahas only -- Rahu/Ketu are never year-lord candidates in this
  -- system (confirmed by reading the writer's own candidate-scoring logic, not assumed from the
  -- currently-observed values alone).
  AND NOT EXISTS (
    SELECT 1 FROM l1_tajik_varsha_year_lords
    WHERE year_lord NOT IN ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
  )
  -- (d) year_lord_method: the writer hardcodes exactly one literal
  -- (ga_tajaka_writer.py:618: "year_lord_method": "tajik_classical") -- no other method exists
  -- in the code today, so any other value is a corruption, not a legitimate alternative.
  AND NOT EXISTS (
    SELECT 1 FROM l1_tajik_varsha_year_lords WHERE year_lord_method <> 'tajik_classical'
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_tajaka';
