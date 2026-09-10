-- 661_l2_bodha_signal_identity.sql
--
-- NIRMĀṆA L2-W3 — deterministic signal identity + the §N.5 resolution detector.
-- Ruling: adjudication #1804 (D-NATIVE-05 action 8; D-CND-11 as AMENDED by that
-- ruling). Pattern mirrors L4's landed migration 680 (phala_anchor_identity).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- WHY THIS EXISTS. bodha_msr_signals.signal_id is str(uuid.uuid4()) at three
-- emit sites in bo_laksana.py (:1346, :2406, :2880). Every rebuild therefore
-- mints new identities for the same signals, which is the mechanism behind the
-- orphaning D-NATIVE-05 §5 assigns dispositions for: bodha_triangulation holds
-- 143 dangling references today, on the two HEALTHY charts and ZERO on the
-- DAMAGED one (D-CND-17), because the array kept ids a later run replaced.

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 1 — the identity function (single source of truth, in SQL)
--
-- The tuple is (chart_id, ayanamsha_id, signal_type_id, varga_id,
-- configuration_jsonb), ruled on #1804. Measured on the canonical chart it is
-- EXACTLY unique: 50,104 distinct over 50,104 rows.
--
-- D-CND-11 (AMENDED, #1804) draws the line this key is built on:
--   EXCLUDED — how good / how strong / how well-verified we currently think it
--   is: computed_salience, salience_*, epistemic_tier, signature_tier,
--   verification_pass_status, verification_certainty, every *_modifier /
--   *_multiplier / *_score, every *_corroboration_count, top_k_salience_rank,
--   build_id. A change in any of these means WE RE-GRADED IT and the identity
--   must NOT move.
--   INCLUDED — what the thing is about: configuration_jsonb, including fact_key
--   and the fact's value. A change here means IT IS A DIFFERENT SIGNAL.
--
-- The original D-CND-11 also excluded "recomputed" quantities. That word was
-- withdrawn by the ruling because it is what made the rule wrong: on the strict
-- reading, 2,559 colliding groups were measured campaign-wide and 2,559 of them
-- differed ONLY by the fact value, with ZERO true duplicates. Collapsing on the
-- strict tuple would have been data loss dressed as deduplication.
--
-- constituent_facts_array is deliberately NOT in the key, though it is the
-- obvious §N.5 discriminator and is exactly unique. L1's fact_id hashes build_id
-- into itself (ga_positions_writer.py:92-95), so an identity derived from it
-- would LOOK deterministic — it is a sha256 — while being no more stable than
-- uuid4() across an L1 rebuild. fact_id stability is L1's, raised separately.

CREATE OR REPLACE FUNCTION bodha_signal_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'c3e1b7d4-8a25-5f96-b0e3-47a9d18c6f52'::uuid $$;

COMMENT ON FUNCTION bodha_signal_identity_namespace() IS
  'Fixed v5 namespace for bodha_msr_signals identities (Nirmana #1804). Distinct '
  'from phala_anchor_identity_namespace so the two id spaces can never collide.';

CREATE OR REPLACE FUNCTION bodha_signal_identity(
  p_chart_id       uuid,
  p_ayanamsha_id   text,
  p_signal_type_id text,
  p_varga_id       text,
  p_configuration  jsonb
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  -- jsonb_build_array gives a canonical, unambiguous, NULL-PRESERVING encoding.
  -- Null-preserving matters here and is not incidental: varga_id is NULL on
  -- 52,533 of 150,150 live rows, so an encoding that coerced NULL to '' would
  -- collide a varga-less signal with a signal whose varga is literally empty.
  --
  -- p_configuration is embedded as jsonb, not as text: Postgres normalises jsonb
  -- key order, so two writers emitting the same object with different key order
  -- produce the SAME identity. Casting to text first would make the identity
  -- depend on emit order, which is the non-determinism this function exists to
  -- remove.
  SELECT uuid_generate_v5(
    bodha_signal_identity_namespace(),
    jsonb_build_array(
      p_chart_id::text, p_ayanamsha_id, p_signal_type_id, p_varga_id, p_configuration
    )::text
  )
$$;

COMMENT ON FUNCTION bodha_signal_identity(uuid, text, text, text, jsonb) IS
  'Deterministic bodha_msr_signals.signal_id (Nirmana #1804, D-CND-11 amended). '
  'Stable across RE-GRADING; deliberately NOT stable across a change in what the '
  'signal describes. Any FK built on it must expect that -- e.g. L1''s ga_vargas '
  'birth-instant correction (#1747) changes ~22% of varga sign assignments, so '
  'those signals legitimately take new identities on the next bo_laksana rebuild.';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 2 — the §N.5 resolution detector
--
-- Assigned by the #1804 ruling: "the only thing that will make that window
-- visible when it opens." The window: constituent_facts_array resolves at
-- 99.93% today ONLY because the current L1 and L2 builds are aligned. L1 is
-- rebuilding ga_positions / ga_vargas / ga_dashas this campaign while
-- bo_laksana is HELD, and every L1 rebuild dangles every reference until
-- bo_laksana re-runs.
--
-- Chart-partitioned per D-CND-03: it attributes a violation to a specific
-- chart rather than saying "some chart is broken", and it binds no parameter.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION bodha_n5_lineage_report()
RETURNS TABLE (chart_id uuid, fact_refs bigint, dangling bigint, pct_dangling numeric)
LANGUAGE sql STABLE AS
$$
  WITH e AS (
    SELECT s.chart_id AS cid, unnest(s.constituent_facts_array) AS fid
      FROM bodha_msr_signals s
  )
  SELECT e.cid,
         count(*),
         count(*) FILTER (WHERE f.fact_id IS NULL),
         round(100.0 * count(*) FILTER (WHERE f.fact_id IS NULL) / NULLIF(count(*), 0), 4)
    FROM e LEFT JOIN chart_facts f
      ON f.fact_id = e.fid AND f.chart_id = e.cid
   GROUP BY e.cid
$$;

COMMENT ON FUNCTION bodha_n5_lineage_report() IS
  'Per-chart §N.5 lineage health: how many constituent_facts_array references '
  'still resolve to chart_facts. Measured at migration time: 482012f1 49/71,967 '
  'dangling, 1c826d5a 6/72,029, cb73cd3d 0/71,680. Note the shape -- the '
  'dangling refs are on the two HEALTHY charts and zero on the DAMAGED one '
  '(D-CND-17), so this is real skew, not a damaged-baseline artefact.';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 3 — bo_sangati.count_sql: a whole table counted by nobody
--
-- bo_sangati writes BOTH bodha_cdlm_cells (its declared target_table) and
-- bodha_triangulation (bo_sangati.py:122, :448), but its count_sql counted only
-- the first. So 405 rows carrying 276,086 signal references were invisible to
-- the cockpit -- the §N.4 cockpit-truth defect, since the stats route reads
-- count_sql and an omission there is invisible everywhere else.
--
-- Verified live before changing it: no other asset's count_sql references
-- bodha_triangulation, so this double-counts nothing.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE asset_registry
   SET count_sql =
         'SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1)'
         || ' + (SELECT count(*) FROM bodha_triangulation WHERE chart_id = $1) AS count'
 WHERE asset_id = 'bo_sangati'
   AND count_sql NOT LIKE '%bodha_triangulation%';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 4 — what this migration deliberately does NOT do
--
-- It does NOT set integrity_check_sql on bo_laksana, and the reason is C12:
-- "a check that has never been green is a PROPOSAL, not a gate."
--
-- Both candidate checks are RED today, and neither because of bad data:
--
--   (a) §N.5 zero-dangling  -- 55 dangling refs across the two HEALTHY charts.
--   (b) identity conformance (every stored signal_id equals
--       bodha_signal_identity(...) recomputed from its own columns) -- red on
--       all 150,150 rows, because they still carry uuid4()s.
--
-- (b) is the strong check and it is the one L2 will adopt: it can fail on real
-- corruption, on a hand-edited row, and on writer drift away from this
-- function. But it is green only AFTER bo_laksana rebuilds with deterministic
-- ids, and that rebuild is HELD campaign-wide under D-NATIVE-05.
--
-- So the honest position, recorded rather than papered over: L2 CANNOT have a
-- green integrity_check_sql on bo_laksana until the held rebuild happens.
-- Choosing a weaker check that happens to pass today would assert nothing and
-- would be exactly the defect C12 names. The conformance check lands in the
-- migration that follows the rebuild.
