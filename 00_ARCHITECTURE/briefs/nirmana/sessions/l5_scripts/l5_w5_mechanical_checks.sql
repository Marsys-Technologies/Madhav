-- l5_w5_mechanical_checks.sql
--
-- L5 (Mimamsa) W5 VERIFY — mechanical checks, READ-ONLY.
--
-- Plan §4 W5 requires, per asset: "scripted mechanical checks (integrity SQL,
-- digests, counts, consumer reachability) + fresh-context judgment
-- verification".  This file is the scripted half.  It is deliberately NOT the
-- integrity_check_sql contracts (those live on asset_registry and are authored
-- separately under C12 / D-CND-03) -- these are the CROSS-asset checks that no
-- single asset's contract can express.
--
-- Every check returns one row: check_id, passed (boolean), detail.
-- A check that cannot fail on real corruption does not belong here (C12
-- rewrite-floor test).  Where a check passes vacuously on empty data, it SAYS SO
-- in its detail column rather than reporting a bare green.
--
-- READ-ONLY.  Nothing here writes.  Run before any capsule is proposed; the
-- capsule cites the output, and a fresh-context verifier re-runs it
-- independently (implementer != certifier, charter C8 / prompt §7.4).

\echo '=== L5 W5 MECHANICAL CHECKS (read-only) ==='
--
-- RUN STATUS AS OF 2026-09-05 (recorded so a reader knows these are RUN, not merely
-- authored -- C12: a check that has never been green is a PROPOSAL, not a gate):
--   7 of 12 PASS. 5 FAIL, and EVERY failure is on a defect already found and recorded:
--     C1  neg_control consistency  FAIL -- C-F-05, the cross-writer contradiction
--     C2b base_rate not degenerate FAIL -- A-F-24, 57/57 rows at the invented 0.10
--     C6  no empirical w/o scores  FAIL -- B-F-14, 10 rows graded empirical at scored_count 0
--     C7a darshana formula current FAIL -- B-F-21, served data predates 3 merged fixes
--     C7b sambandha formula current FAIL -- same
--   Those five failures are the C12 rewrite-floor test PASSING: these checks CAN fail on real
--   corruption, and they do, on the corruption that actually exists. W3 fixes the code; only a
--   W4 rebuild fixes the data. Expect all five to stay red until then -- that is the point.

-- ---------------------------------------------------------------------------
-- C1. CROSS-WRITER FLAG CONSISTENCY  (the check L5-W1 batch C argued for)
-- ---------------------------------------------------------------------------
-- Two L5 writers make OPPOSITE claims about the same check, on the same chart,
-- in the same build: mi_pariksha writes mimamsa_qa_eval rows saying
-- negative_control | not_implemented (its JL-019 comment: "the comparison is a
-- tautology that can never fail"), while mi_gunanaka writes neg_control_clear =
-- true on every mimamsa_multipliers row those controls exist to police.
--
-- This is detectable by SQL alone and no per-asset integrity contract can see
-- it, because it spans two assets.  It is the reason this file exists.
SELECT
  'C1_neg_control_consistency' AS check_id,
  NOT EXISTS (
    SELECT 1
    FROM mimamsa_multipliers m
    WHERE m.neg_control_clear IS TRUE
      AND EXISTS (
        SELECT 1 FROM mimamsa_qa_eval q
        WHERE q.chart_id = m.chart_id
          AND q.check_type = 'negative_control'
          AND q.status <> 'pass'
      )
  ) AS passed,
  'a multiplier may not assert neg_control_clear on a chart whose own negative-control battery did not pass' AS detail;

-- ---------------------------------------------------------------------------
-- C2. NO FABRICATED CLIMATOLOGY PRIOR  (regression guard for finding A-F-24)
-- ---------------------------------------------------------------------------
-- Before the W3 fix, base_rate was the hardcoded literal 0.10 on 57/57 rows,
-- with brier_vs_null -- a skill-VERSUS-null metric -- computed from it.  This
-- check asserts the repaired invariant: brier_vs_null may exist ONLY where a
-- real base_rate backs it, and a base_rate may not be the old sentinel unless
-- it was genuinely derived.
--
-- NOTE the direction: this does NOT assert base_rate IS NULL.  If a future
-- programme derives a real age-banded prior, this check must keep passing.  It
-- asserts the RELATIONSHIP, not the absence.
SELECT
  'C2_no_fabricated_base_rate' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM mimamsa_calibration
    WHERE brier_vs_null IS NOT NULL AND base_rate IS NULL
  ) AS passed,
  'brier_vs_null may not be populated where base_rate is NULL -- a skill metric measured against an absent null is an invented value (§N.8)' AS detail;

SELECT
  'C2b_base_rate_not_degenerate' AS check_id,
  (SELECT count(DISTINCT base_rate) FROM mimamsa_calibration WHERE base_rate IS NOT NULL) <> 1
    OR (SELECT count(*) FROM mimamsa_calibration WHERE base_rate IS NOT NULL) = 0 AS passed,
  'if every non-null base_rate is the SAME value across all rows and charts, it is a constant wearing a measurement''s name -- the exact A-F-24 signature. Vacuously true while all base_rates are NULL, which is the current honest state.' AS detail;

-- ---------------------------------------------------------------------------
-- C3. LEAKAGE FIREWALL IS REAL, NOT TAUTOLOGICAL  (finding A-F-10)
-- ---------------------------------------------------------------------------
-- admissible_clean was true on 64/64 rows with no code path able to produce
-- false.  A flag that cannot read false is not a firewall.  This check does not
-- assert a distribution (that would be fabricating an expectation); it asserts
-- the two invariants the partition MUST satisfy if it is real.
SELECT
  'C3a_scored_rows_are_admissible' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM mimamsa_calibration c
    JOIN mimamsa_event_provenance p
      ON p.chart_id = c.chart_id AND p.event_id = c.event_id
    WHERE p.held_out IS TRUE OR p.admissible_clean IS NOT TRUE
  ) AS passed,
  'no calibration row may score against a held-out or inadmissible event -- the leakage invariant this layer exists to protect' AS detail;

SELECT
  'C3b_holdout_partition_reproducible' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM mimamsa_event_provenance
    WHERE partition_seed_version = 'v1_md5_mod10'
      AND held_out IS DISTINCT FROM (('x' || substr(md5(event_id::text), 1, 8))::bit(32)::bigint % 10 >= 8)
  ) AS passed,
  'held_out must be recomputable from its declared seed formula -- catches a silent seed-version change that a row count cannot see' AS detail;

-- ---------------------------------------------------------------------------
-- C4. PROVENANCE CHAIN CLOSURE  (mandate item 2; the #1732 / #1748 tripwire)
-- ---------------------------------------------------------------------------
-- All four links measured 0 orphans at W1.  A rebuild of an upstream with
-- non-deterministic ids would break them silently, which is exactly what #1732
-- (phala_anchors.anchor_id) and #1748 (bodha_msr_signals.signal_id) are about.
-- This is the tripwire that would catch it.
SELECT
  'C4a_calibration_to_predictions' AS check_id,
  NOT EXISTS (SELECT 1 FROM mimamsa_calibration c
              LEFT JOIN mimamsa_predictions p USING (prediction_id)
              WHERE p.prediction_id IS NULL) AS passed,
  'every calibration row resolves to its prediction' AS detail;

SELECT
  'C4b_provenance_to_life_events' AS check_id,
  NOT EXISTS (SELECT 1 FROM mimamsa_event_provenance v
              LEFT JOIN life_events l ON l.event_id = v.event_id
              WHERE l.event_id IS NULL) AS passed,
  'every provenance row resolves to its source life event' AS detail;

SELECT
  'C4c_driving_signals_resolve' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT (jsonb_array_elements(driving_signals)->>'signal_id') AS sid
      FROM mimamsa_predictions WHERE jsonb_typeof(driving_signals) = 'array'
    ) d LEFT JOIN bodha_msr_signals s ON s.signal_id::text = d.sid
    WHERE s.signal_id IS NULL
  ) AS passed,
  'every signal_id inside driving_signals JSONB resolves -- the surface a column-name sweep cannot see (975 refs at W1); this is the #1748 tripwire' AS detail;

-- ---------------------------------------------------------------------------
-- C5. STRUCTURAL MODE IS INTERNALLY CONSISTENT  (mandate item 1)
-- ---------------------------------------------------------------------------
-- Not "is L5 structural" -- that is a documentation question.  This asserts the
-- consistency that must hold WHILE it is structural: a promoted multiplier
-- claims empirical standing, so it must not coexist with zero observations.
SELECT
  'C5_promotion_requires_observations' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM mimamsa_multipliers
    WHERE promotion_status = 'promoted'
      AND (n_observations IS NULL OR n_observations = 0)
  ) AS passed,
  'a multiplier may not be promoted on zero observations' AS detail;

-- ---------------------------------------------------------------------------
-- C6. NO UNEARNED EMPIRICAL GRADE AT REST  (finding B-F-14)
-- ---------------------------------------------------------------------------
-- 10 live manifestation_grammar rows carried evidence_grade='empirical' with
-- scored_count = 0 -- "measured, and it never fires" -- which is precisely what
-- the merged F-147 fix replaced with an honest NULL.  This is the regression
-- guard for that fix landing in DATA, not just in code.
SELECT
  'C6_no_empirical_without_scores' AS check_id,
  NOT EXISTS (
    SELECT 1 FROM mimamsa_manifestation_grammar
    WHERE evidence_grade = 'empirical'
      AND (scored_count IS NULL OR scored_count = 0)
  ) AS passed,
  'an empirical evidence grade requires a non-zero scored_count' AS detail;

-- ---------------------------------------------------------------------------
-- C7. SERVED DATA IS NOT BEHIND ITS WRITER  (the W2 verified_reuse refusal)
-- ---------------------------------------------------------------------------
-- The reason no L5 asset takes verified_reuse: served rows carried *_v1.0
-- formula versions while the writers were at v1.2, so the layer was serving
-- sentences three merged fixes had removed.  These are the checks that will say
-- whether the W4 rebuild actually fixed that -- they are EXPECTED TO FAIL until
-- it runs, and that expected failure is the point.
SELECT
  'C7a_darshana_formula_current' AS check_id,
  NOT EXISTS (SELECT 1 FROM mimamsa_insight_units
              WHERE surface_formula_version < 'mi_darshana_v1.2') AS passed,
  'EXPECTED TO FAIL pre-rebuild: served insight units must not predate the merged narration fixes' AS detail;

SELECT
  'C7b_sambandha_formula_current' AS check_id,
  NOT EXISTS (SELECT 1 FROM mimamsa_manifestation_grammar
              WHERE grammar_formula_version < 'mi_sambandha_v1.2') AS passed,
  'EXPECTED TO FAIL pre-rebuild: served grammar rows must not predate the merged F-147 fix' AS detail;

-- ---------------------------------------------------------------------------
-- C8. VACUITY DISCLOSURE — not a check, a required disclosure
-- ---------------------------------------------------------------------------
-- Charter C12: a check that passes vacuously on an empty table attests nothing
-- about today.  Any capsule citing this file MUST carry these counts alongside
-- the passes, or it is reporting a green that no data earned.
SELECT
  'C8_vacuity_disclosure' AS check_id,
  NULL::boolean AS passed,
  'row counts backing the checks above -- a pass over 0 rows is vacuous: '
  || 'calibration=' || (SELECT count(*) FROM mimamsa_calibration)
  || ' provenance='  || (SELECT count(*) FROM mimamsa_event_provenance)
  || ' predictions=' || (SELECT count(*) FROM mimamsa_predictions)
  || ' multipliers=' || (SELECT count(*) FROM mimamsa_multipliers)
  || ' grammar='     || (SELECT count(*) FROM mimamsa_manifestation_grammar)
  || ' insights='    || (SELECT count(*) FROM mimamsa_insight_units)
  || ' journal='     || (SELECT count(*) FROM mimamsa_journal)
  || ' ledger='      || (SELECT count(*) FROM mimamsa_intervention_ledger)
  || ' export_log='  || (SELECT count(*) FROM mimamsa_export_log)
  || ' preferences=' || (SELECT count(*) FROM mimamsa_preferences)
  AS detail;
