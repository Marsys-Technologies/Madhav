-- 931_nirmana_l2_bo_laksana_integrity_contract.sql
--
-- NIRMANA v2.5 -- L1 lane as integrity-contract specialist (RESOLUTION_L1 v4
-- priority 1; adjudication #2455). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Discharges the #2455 block: bo_laksana's asset_registry row had
-- integrity_check_sql IS NULL and a parameterised count_sql, which
-- collectIntegrityObservation rejects at integrity_verified ("the count_sql
-- fallback is parameterised and cannot be evaluated" -- confirmed live via
-- HTTP 409, see #2455). Every other frozen bodha_msr_signals co-writer
-- (bo_arudha 710, bo_sudarshana 667, bo_nakshatra_semantic 669,
-- bo_special_lagna 668) already carries a chart-agnostic contract; bo_laksana
-- never got one. This joins the M-14 layer-wide gap class (663-669/710-722/
-- 761-763) and follows the D-CND-03 discipline of L1's 740-754 series:
-- chart-partitioned/row-wise, attribution-preserving, derive-don't-pin, no
-- bare count(*)=N equality pins (C12).
--
-- bo_laksana (pipeline/orchestrator/writers/bo_laksana.py) projects ALL
-- chart_facts into the SHARED table bodha_msr_signals. Every conjunct below
-- is therefore scoped to bo_laksana's closed ownership allowlist
-- (BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES, bo_laksana.py:145 -- the same
-- 15-class set migrations 448/929/930 scope count_sql, the output-digest
-- spec, and natural_key_partition to), never to the whole table -- the check
-- must not fail bo_laksana on a sibling writer's rows (bo_arudha,
-- bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna,
-- bo_vargottama_dhana own the other 4 classes).
--
-- Conjuncts -- every one EXECUTED green against live production (all 3
-- charts, 150,280 owned rows, 2026-09-08) AND mutation-proved via a
-- CTE-overlay corruption (each shown to flip integrity_passed to false
-- against a synthetic row corrupting exactly that invariant):
--   (a) Cross-build accretion detector: the natural signal tuple
--       (chart_id, ayanamsha_id, signal_type_id, varga_id,
--       configuration_jsonb) -- the exact bodha_signal_identity() input
--       tuple, migration 661 -- appears at most once. The table's own UNIQUE
--       constraint includes build_id, so a failed delete-then-insert cycle
--       (stale generation accreting beside a fresh one) is invisible to the
--       DB constraint; this is the write-path idempotency gap CLAUDE.md
--       SN.7 item 2 honestly notes the fact-pin lint cannot cover.
--   (b) lel_origin is false on every owned row -- "LEL data is L3-gated; L2
--       is timeless structural" (bo_laksana.py module docstring; emit sites
--       :1413, :2494, :2961 and the bhavat_bhavam module all hardcode False).
--   (c) valence vocabulary {benefic, malefic, mixed, neutral}, NOT NULL --
--       _infer_valence (:364) emits the first three's subset
--       {benefic, malefic, neutral}; _VICHARA_TO_MSR_VALENCE (:388) adds
--       'mixed' (DR-9: first-class, never collapsed to neutral).
--   (d) valence_source vocabulary {ga_vichara_v1, keyword_heuristic_v1,
--       bhavat_bhavam_amplifier_v1}, NOT NULL -- _resolve_valence (:396,
--       CR-42: no silent degradation, source always visible) plus
--       bhavat_bhavam_amplifier.py:390. The third literal was surfaced by
--       the live sweep, not the main writer path -- vocabulary derived from
--       ALL emit sites, then re-verified live.
--   (e) 'mixed' is ga_vichara-judged ONLY: the keyword heuristic cannot
--       return 'mixed' (_infer_valence has no mixed branch), so a mixed row
--       whose source is not ga_vichara_v1 is a provenance lie.
--   (f) bhavat_bhavam bijection: valence_source='bhavat_bhavam_amplifier_v1'
--       iff signal_type_class='bhavat_bhavam_amplifier', and amplifier rows
--       carry the module's own 'bhavat_bhavam_amplifier:' signal_type_id
--       prefix (bhavat_bhavam_amplifier.py:294,390; CR-97 Lane B-4).
--   (g) signature_tier vocabulary = _TIER_ORDER (:788)
--       {background, supporting, major, chart_defining}, NOT NULL --
--       _assign_tiers_by_percentile (:836) assigns every row exactly one.
--   (h) constituent_facts_array never empty -- WP-2.4 9b-5 / SN.5
--       traceability floor: the signal's own resolving fact_id is always
--       unioned in (module docstring; enforced by
--       platform/scripts/governance/msr_referential_integrity.py).
--   (i) signal_tradition vocabulary -- _infer_tradition (:492) is a total
--       mapping onto {parashari, jaimini, kp, tajika, lal_kitab, esoteric};
--       special emit sites hardcode 'parashari'.
--   (j) fact_kind vocabulary -- _infer_fact_kind (:306) is a total mapping
--       onto {relationship, magnitude, birth_moment, time_window, position,
--       configuration}; special emit sites hardcode 'configuration'.
--   (k) ayanamsha_id vocabulary = CANONICAL_AYANAMSHAS (:66) -- the writer
--       plans exactly one substep per canonical ayanamsha; a row outside the
--       five is one the writer could never have produced.
--   (l) varga_ratification_divergence class<->prefix biconditional: the
--       CR-57 emit site (:1388) is the only producer of that class and
--       always stamps the 'varga_ratification_divergence:' signal_type_id
--       prefix; conversely no other class may wear that prefix.
--
-- Deliberately NOT checked, with reasons (C12 -- never land a conjunct that
-- has yet to be green; D-CND-03 rule 4 -- never re-assert what an index
-- already enforces):
--   * signal_id uniqueness / NOT NULL -- PK-enforced
--     (bodha_msr_signals_pkey); rule 4.
--   * Per-chart volumes -- genuinely chart-data-dependent (category-agnostic
--     projection of chart_facts); no volume is asserted anywhere in this
--     contract, so no expected_volume_formula accompanies it (C12: the
--     formula obligation attaches only where volume IS asserted).
--   * signal_id re-derivation via bodha_signal_identity() over stored
--     columns -- UNWRITABLE today: assign_deterministic_signal_ids
--     (bo_laksana.py:3142) feeds the function row["configuration_jsonb"]
--     which is already a json.dumps STRING at every emit site, so the
--     identity hashes a JSON-string scalar whose exact Python
--     dict-order/separator form does not survive jsonb normalisation in the
--     stored column. Verified live: 150,280/150,280 owned rows mismatch the
--     naive re-derivation. This also quietly defeats migration 661's stated
--     "jsonb, not text, so key order cannot matter" normalisation intent --
--     flagged on #2455 for adjudication, deliberately NOT self-fixed here (a
--     writer change shifts bo_laksana's registry fingerprint AND every
--     stored signal_id; that is a Conductor-ruled mass-identity migration,
--     not a registry contract).
--   * The WP-2.4 9b-2 flood-family tier ceiling ("an aggregate rollup
--       cannot escape into major/chart_defining") -- live-RED today: 2,019
--     owned rows (1,231 on the freshly rebuilt canonical chart) sit at
--     major/chart_defining inside _FLOOD_PRONE_FAMILIES prefixes, incl.
--     'lord_aspects_lord_per_varga:aggregate_D21' at chart_defining. Root
--     cause (read from the writer, not guessed): _assign_tiers_by_percentile
--     POPS "_tier_ceiling" (:873) on its first call (:3532); when
--     bhavat_bhavam amplifiers fire, the augmented set is re-run through the
--     SAME function (:3636) whose second pass finds every ceiling already
--     consumed -- and re-assigns tiers un-clamped. The ceiling CR-82->CR-65
--     explicitly preserved is thus silently defeated on every build where
--     any amplifier fires. Flagged on #2455 for adjudication; the conjunct
--     lands with the writer fix, not before it (C12).
--   * signal_type_class re-derivation from the signal_type_id category
--     prefix for the 13 heuristic classes -- _signal_type_class (:462) is an
--     ORDER-SENSITIVE substring chain ("yoga" wins over "karaka" for
--     'graha_yoga_karaka_flag' purely by branch order); a SQL mirror of it
--     would be a drift-prone reimplementation, the exact hazard SN.7 exists
--     to bar. Only the two structurally-unambiguous classes (f)/(l) get
--     prefix checks.
--
-- Fingerprint consequence (stated, not hidden): updating integrity_check_sql
-- shifts bo_laksana's live registry_fingerprint_sha256, invalidating the
-- currently-assembled W1/W2/W4 evidence chain (#2455 predicted exactly this
-- and asked for the migration anyway -- "worth doing once, correctly"). The
-- Conductor fires the fresh resubmission cycle after ratification.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
-- bo_laksana integrity contract (target table: bodha_msr_signals -- SHARED;
-- every conjunct scoped to bo_laksana's 15-class ownership allowlist).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare
-- count pin (C12). signal_id uniqueness/NOT NULL PK-enforced; not re-asserted
-- (rule 4).
WITH owned AS (
  SELECT * FROM bodha_msr_signals
  WHERE signal_type_class = ANY(ARRAY[
    'yoga','dosha','sade_sati','panchanga','karaka_alignment',
    'tradition_specific','parivartana','configuration','varga_pattern',
    'annual','medical','vastu','composite_state',
    'varga_ratification_divergence','bhavat_bhavam_amplifier'])
)
SELECT
  -- (a) cross-build accretion: the natural identity tuple (migration 661's
  -- bodha_signal_identity input) appears at most once; the DB UNIQUE
  -- constraint includes build_id and cannot see a stale generation.
  NOT EXISTS (
    SELECT 1 FROM owned
    GROUP BY chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb
    HAVING count(*) > 1
  )
  -- (b) L2 is timeless structural; LEL is L3-gated.
  AND NOT EXISTS (
    SELECT 1 FROM owned WHERE lel_origin IS DISTINCT FROM false
  )
  -- (c) valence vocabulary, NOT NULL.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE valence IS NULL OR valence NOT IN ('benefic','malefic','mixed','neutral')
  )
  -- (d) valence_source vocabulary, NOT NULL (CR-42: provenance always visible).
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE valence_source IS NULL
       OR valence_source NOT IN ('ga_vichara_v1','keyword_heuristic_v1','bhavat_bhavam_amplifier_v1')
  )
  -- (e) 'mixed' is ga_vichara-judged only; the keyword heuristic has no mixed branch.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE valence = 'mixed' AND valence_source IS DISTINCT FROM 'ga_vichara_v1'
  )
  -- (f) bhavat_bhavam bijection + its own signal_type_id prefix (CR-97).
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE valence_source = 'bhavat_bhavam_amplifier_v1'
      AND signal_type_class != 'bhavat_bhavam_amplifier'
  )
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE signal_type_class = 'bhavat_bhavam_amplifier'
      AND (valence_source IS DISTINCT FROM 'bhavat_bhavam_amplifier_v1'
           OR signal_type_id NOT LIKE 'bhavat_bhavam_amplifier:%')
  )
  -- (g) signature_tier = _TIER_ORDER lattice, NOT NULL.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE signature_tier IS NULL
       OR signature_tier NOT IN ('background','supporting','major','chart_defining')
  )
  -- (h) 9b-5 traceability floor: every signal cites at least one resolving fact.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE constituent_facts_array IS NULL
       OR COALESCE(array_length(constituent_facts_array, 1), 0) = 0
  )
  -- (i) signal_tradition vocabulary (_infer_tradition is total onto this set).
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE signal_tradition NOT IN ('parashari','jaimini','kp','tajika','lal_kitab','esoteric')
  )
  -- (j) fact_kind vocabulary (_infer_fact_kind is total onto this set).
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE fact_kind NOT IN ('relationship','magnitude','birth_moment','time_window','position','configuration')
  )
  -- (k) one substep per canonical ayanamsha; nothing else can exist.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE ayanamsha_id NOT IN ('lahiri_chitrapaksha','raman','krishnamurti','surya_siddhanta_classical','true_chitra')
  )
  -- (l) CR-57 divergence class <-> prefix biconditional.
  AND NOT EXISTS (
    SELECT 1 FROM owned
    WHERE (signal_type_class = 'varga_ratification_divergence')
       != (signal_type_id LIKE 'varga_ratification_divergence:%')
  )
  AS integrity_passed
$ic$
 WHERE asset_id = 'bo_laksana';
