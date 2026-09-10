-- 866_nirmana_l3_w3_sangam_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_sangam`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (14868, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-865's convention for this range).
--
-- **This closes a two-cycle investigation.** The prior two cycles' Held-item notes recorded an
-- unreconciled ~2.3x gap between a naive Mode-D ingress estimate and the live total. This
-- migration closes it -- the gap was real and had a precise, verifiable cause, found by RUNNING
-- the actual production `find_ingress_events` (pipeline/transit_search.py) directly rather than
-- approximating further:
--
--   Mode D (SAV-bindhu, `mode_d_av_bindhu`) fires ONCE PER SUBSTEP (`if pred_dict is
--   pred_dicts[0]`), but `_generate_windows` routes any predicate whose `signature_class` contains
--   'SUBSYSTEM' to Mode C FIRST, with a `continue` that skips the rest of the function --
--   including the Mode D block. So Mode D fires ONLY for a substep whose own single predicate is
--   NOT SUBSYSTEM-classified. Live-verified: of the 60 lifetime substeps this chart selected
--   (`build_substep_progress`), exactly 25 have a non-SUBSYSTEM predicate -- 5 each of the 5
--   non-SUBSYSTEM signature classes (CLASSIFY_RESIDUAL, DIGNITY, DISPOSITOR_RELATIONAL, DOSHA,
--   YOGA), matching `_select_top_predicates_with_class_quota`'s own per-class floor exactly. The
--   'near' substep's own first predicate is SUBSYSTEM, so Mode D never fires there (0 rows,
--   confirmed live).
--
--   The SECOND missing piece: `_derive_birth_year` (writer.py:866-875) does NOT read the native's
--   real birth date -- it reads `MIN(chart_dashas.start_date) WHERE level_n=1`, which is the
--   THEORETICAL pre-birth "balance of dasha" start (T-9's own documented pre-birth-clip concern,
--   ka_jivana_parva/migration 858), not the lived birth year. Live for this chart: 1950-01-01, not
--   1984. So the lifetime horizon Mode D actually scans is [1950-01-01, 2050-12-31] -- a full
--   century anchored 34 years BEFORE the native's real birth, not [birth_year, birth_year+100].
--
--   With both facts corrected, running the REAL `find_ingress_events` (not an approximation) for
--   Jupiter/Saturn/Mars into the 6 of 12 signs with SAV>=28 (signs 1,2,4,5,7,8, read from
--   `chart_facts`/`ashtakavarga_bindu_sign`/SARVA, `lahiri_chitrapaksha`) over [1950-01-01,
--   2050-12-31] gives EXACTLY 478 windows. 25 (qualifying substeps) x 478 = 11950 -- matches the
--   live `mode='D'` row count EXACTLY, with zero remaining discrepancy.
--
--   The other 2918 rows (Mode A: dasha-prior transit search; Mode B: off-dasha sweep; Mode C:
--   SUBSYSTEM sign-ingress trigger) are genuinely per-predicate, per-transit-alignment-dependent
--   -- live breakdown: near tier A=484/B=361/C=119 (964), lifetime tier A=644/B=505/C=805 (2918-964
--   =1954... see structured breakdown below for the exact split). These are NOT further decomposed
--   in this migration -- unlike Mode D, whose count is a deterministic function of 3 fixed inputs
--   (scan planets, strong signs, horizon), Modes A/B/C depend on real-time astronomical alignment
--   against each SELECTED predicate's own dasha_eligibility_rule/transit_trigger, which varies
--   candidate-by-candidate and is not reducible to a small set of named constants the way Mode D
--   is.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_convergence WHERE chart_id=... GROUP BY horizon_tier, mode`:
--   near      A   484
--   near      B   361
--   near      C   119
--   lifetime  A   644
--   lifetime  B   505
--   lifetime  C   805
--   lifetime  D 11950   (= 25 qualifying substeps x 478, exactly derived, see above)
--   -----------------------
--   TOTAL          14868   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852-865's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because Modes A/B/C are genuinely per-predicate-alignment-
-- dependent even though Mode D (80% of the total) is now a fully closed-form, verified derivation.
-- This migration does not touch the seed; the row is DB-authoritative and seed-divergent in the
-- same documented, already-flagged way migration 690's six rows (and migrations 852-865's rows)
-- are.

UPDATE asset_registry
   SET expected_volume_formula = 'EXACT: 25 x 478 (Mode D, fully derived) + 2918 (Modes A/B/C, per-predicate transit-alignment-dependent, not further decomposed)',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'mixed_exact_and_alignment_dependent_count',
         'chart_scoped', true,
         'mode_d_fully_derived', jsonb_build_object(
           'gate', 'mode_d_av_bindhu fires only for a substep whose sole predicate is NOT signature_class SUBSYSTEM (SUBSYSTEM predicates continue to Mode C before the Mode D block is ever reached)',
           'qualifying_lifetime_substeps', 25,
           'qualifying_substep_classes', jsonb_build_array('CLASSIFY_RESIDUAL', 'DIGNITY', 'DISPOSITOR_RELATIONAL', 'DOSHA', 'YOGA'),
           'lifetime_horizon', '[1950-01-01, 2050-12-31], derived from MIN(chart_dashas.start_date) WHERE level_n=1 (the theoretical pre-birth balance-of-dasha start, NOT the native''s real 1984 birth year)',
           'scan_planets', jsonb_build_array('Jupiter', 'Saturn', 'Mars'),
           'strong_signs_sav_threshold', 28,
           'strong_signs_count', 6,
           'windows_per_qualifying_substep', 478,
           'derivation_method', 'computed by running the real production pipeline.transit_search.find_ingress_events directly against the live ephemeris (not approximated), matching the live row count exactly',
           'total', 11950
         ),
         'modes_a_b_c_not_decomposed', jsonb_build_object(
           'reason', 'genuinely per-predicate transit/dasha-alignment-dependent. Mode A (dasha-prior search) and Mode B (off-dasha sweep) for non-SUBSYSTEM predicates, Mode C (sign-ingress trigger) for SUBSYSTEM predicates, not reducible to a small set of named constants the way Mode D is',
           'observed_breakdown', jsonb_build_object(
             'near_A', 484, 'near_B', 361, 'near_C', 119,
             'lifetime_A', 644, 'lifetime_B', 505, 'lifetime_C', 805
           ),
           'total', 2918
         ),
         'derivation', 'derived from pipeline/orchestrator/writers/ka_sangam.py and services/ka_sangam/engine.py directly, not guessed. Mode D is a fully closed-form, exactly-verified derivation. Modes A/B/C are honestly left as a per-predicate-dependent residual',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'mode_d_total', 11950, 'modes_abc_total', 2918, 'total', 14868
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'A mixed exact-and-dependent derivation: Mode D (SAV-bindhu convergence, 11950 of 14868 rows, 80%) is now FULLY and exactly derived. 25 of this chart''s 60 lifetime substeps have a non-SUBSYSTEM predicate (the only kind that reaches the Mode D code path), each producing exactly 478 windows (3 scan planets x 6 SAV>=28 signs, real ingress events over the true [1950-01-01, 2050-12-31] century horizon derived from chart_dashas'' earliest theoretical dasha start, not the native''s real birth year). 25 x 478 = 11950 exactly, verified by running the real production ingress-search code, not approximated. The remaining 2918 rows (Modes A/B/C) are genuinely per-predicate transit/dasha-alignment-dependent and are not further decomposed here. 14868 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_sangam'
   AND expected_volume_formula IS NULL;
