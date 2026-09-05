-- 691_nirmana_l5_w3_integrity_contracts.sql
--
-- NIRMANA v2.1 -- L5 (Mimamsa) W3 IMPLEMENT.
-- Source: L5_W2_DECIDE_v1_0.md §4.2 W3-2 -- author an integrity_check_sql
-- contract for each of the 15 L5 assets, all of which carried
-- integrity_check_sql IS NULL before this migration.
--
-- Authored under:
--   * Charter C12 -- real invariants only. Bare `count(*) = N` equality pins are
--     FORBIDDEN as volume assertions ("an equality wearing a floor's name");
--     volume expectations belong in expected_volume_formula, not here. Every
--     check must pass the REWRITE FLOOR TEST: it must be able to fail on real
--     corruption that a row count could not see. A check that has never been
--     green is a PROPOSAL, not a gate.
--   * D-CND-03 (Conductor ruling on issue #1723) -- for per_chart assets the
--     required shape is a chart-partitioned invariant with NO bind
--     placeholders:
--         SELECT NOT EXISTS (
--           SELECT 1 FROM <table> GROUP BY chart_id HAVING <violated here>
--         )
--     This quantifies over EVERY chart while still attributing a violation to a
--     specific one. `$1` placeholders are rejected outright -- binding the
--     canonical chart_id was ruled against because it would only ever assert
--     against one chart. For global assets a whole-table invariant is correct.
--   * D-CND-01 (standing) -- a bare `count(*) = N` is forbidden alone.
--
-- VERIFICATION. All 15 statements below were EXECUTED READ-ONLY AGAINST
-- PRODUCTION on 2026-09-05 and every one returned `true` before this migration
-- was written. The SQL in each UPDATE is the verbatim statement that was run --
-- not a re-derivation and not a tidy-up. Live schema was read from
-- information_schema.columns before authoring each check; every vocabulary list
-- is transcribed from live data, from a writer constant, or from a spec §, and
-- none is invented.
--
-- Charts in play during verification: 482012f1-710e-4a25-994a-93821f5871aa
-- (canonical), 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan -- legitimately
-- has no Life Event Log, hence zero calibration/provenance rows), and
-- cb73cd3d-9eba-4220-9902-0de91566e980 (present in build state with no L5 data).
-- A chart with no rows produces no `GROUP BY chart_id` group at all, so none of
-- these checks reads a legitimately-empty chart as corruption.
--
-- VACUITY. Five assets are wholly or partly vacuous today
-- (mi_abhilekha, mi_seva, mi_sankalpa, mi_vistara fully; mi_darshana's
-- embeddings half). Per C12 the vacuity caveat MUST ship with the check -- an
-- elevation capsule that cites a vacuous pass without it is reporting a green
-- that no data earned. Each caveat sentence is reproduced verbatim in the
-- per-asset comment below and must be carried forward into the capsule.
--
-- DROPPED INVARIANTS. Where an invariant we wanted is violated by real data
-- today, it was NOT shipped -- a gate that starts red is a broken gate, not a
-- detector. Those are recorded per-asset below and summarised in the
-- `-- KNOWN GAPS` block at the end of this file. They are DELIBERATE gaps.
-- Do not "helpfully" add the missing clause: it will turn the build red without
-- fixing the underlying defect.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts. No BEGIN/COMMIT
-- in this file.


-- ────────────────────────────────────────────────────────────────────────────
-- 1. lel_events -- the user-authored Life Event Log source corpus
--    (`life_events`); the L5 no-writer exception. per_chart.
--
-- INVARIANTS: per chart -- event_id distinct; chart_id resolves to `charts`;
--   event_id/category/description/build_id non-blank and event_date/provenance
--   non-null; date_confidence in {exact, month_known, year_only}; shape in
--   {point, interval}; shape='interval' IFF both interval bounds are present
--   (bi-conditional); interval_start <= interval_end; event_date lies inside
--   [interval_start, interval_end] when bounded; chain_parent_event_id resolves
--   to another life_events.event_id on the same chart.
--
-- REWRITE-FLOOR TEST: catches a chain-correction append whose
--   chain_parent_event_id points at a deleted or mistyped predecessor (chain
--   broken, count unchanged); a shape='interval' row whose bounds were dropped
--   by an intake regression (count unchanged, the event silently becomes a
--   point); an event_date tightened outside its own stated uncertainty interval
--   (the date_tightened_at path writing an inconsistent pair); an event row
--   written against a chart_id no longer in `charts`. A row count sees none of
--   these.
--
-- NOT VACUOUS: 64 live rows on the canonical chart.
--
-- PLACEMENT NOTE -- the FULL JOIN was RELOCATED, NOT DROPPED. W1 proposed a
--   FULL JOIN life_events <-> mimamsa_event_provenance here. It is live-verified
--   `true` and it DOES ship -- but under `mi_jivanaghatana` (asset 2 below),
--   which owns the bridge. `lel_events` has no writer. Asserting downstream
--   build completeness on the SOURCE CORPUS would make it fail whenever the
--   native appends a life event and the L5 build has not yet re-run -- a gate
--   that fails on correct user behaviour. The native appending an event is
--   correct behaviour, not corruption. Under mi_jivanaghatana the identical
--   clause is honest: the bridge asset genuinely has not done its job.
--
-- ALSO DROPPED:
--   * Reconciliation against the LEL markdown source of truth: no in-DB source
--     to join to (W1 L5-F-12 -- lel_file_sha is NULL 64/64, hardcoded None at
--     mi_jivanaghatana.py:180). Not expressible in SQL.
--   * A clause asserting the absence of the known demo row 5278d97c-e769-...
--     (source_section='D-4a-A4-append-hook-demo', W1 L5-F-03): it FAILS today.
--     Left as W1's recorded finding, awaiting the native's delete-vs-flag call.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1
  FROM life_events le
  LEFT JOIN charts c ON c.id = le.chart_id
  GROUP BY le.chart_id
  HAVING count(DISTINCT le.event_id) <> count(*)
      OR count(*) FILTER (WHERE c.id IS NULL) > 0
      OR count(*) FILTER (WHERE btrim(coalesce(le.event_id,'')) = ''
                             OR btrim(coalesce(le.category,'')) = ''
                             OR btrim(coalesce(le.description,'')) = ''
                             OR btrim(coalesce(le.build_id,'')) = ''
                             OR le.event_date IS NULL
                             OR le.provenance IS NULL) > 0
      OR count(*) FILTER (WHERE le.date_confidence NOT IN ('exact','month_known','year_only')) > 0
      OR count(*) FILTER (WHERE le.shape NOT IN ('point','interval')) > 0
      OR count(*) FILTER (WHERE (le.shape = 'interval')
                              <> (le.interval_start IS NOT NULL AND le.interval_end IS NOT NULL)) > 0
      OR count(*) FILTER (WHERE le.interval_start > le.interval_end) > 0
      OR count(*) FILTER (WHERE le.interval_start IS NOT NULL
                             AND (le.event_date < le.interval_start OR le.event_date > le.interval_end)) > 0
      OR count(*) FILTER (WHERE le.chain_parent_event_id IS NOT NULL
                             AND NOT EXISTS (SELECT 1 FROM life_events p
                                              WHERE p.chart_id = le.chart_id
                                                AND p.event_id = le.chain_parent_event_id)) > 0
)
$check$
 WHERE asset_id = 'lel_events';


-- ────────────────────────────────────────────────────────────────────────────
-- 2. mi_jivanaghatana -- the LEL->DB provenance bridge and leakage firewall
--    (`mimamsa_event_provenance`). per_chart.
--
-- INVARIANTS: per chart -- FULL JOIN life_events <-> mimamsa_event_provenance on
--   (chart_id, event_id) with ZERO one-sided rows in either direction (this is
--   the clause relocated from lel_events, see asset 1); event_id distinct;
--   HELD-OUT PARTITION REPRODUCIBILITY -- held_out = (MD5(event_id)[0:8] mod 10
--   >= 8) recomputed in SQL, matching _held_out() at
--   writers/mi_jivanaghatana.py:94-97 exactly;
--   partition_seed_version = 'v1_md5_mod10'; ADMISSIBILITY REPRODUCIBILITY --
--   admissible_clean = (NOT shaped_predictor AND disclosure_timing <>
--   'post_framework_undated' AND event_date IS NOT NULL), matching
--   _admissibility() at :100-105; event_date agrees with the source
--   life_events.event_date; lel_version / provenance_formula_ver /
--   domain_primary / admissibility_reason non-blank.
--
-- REWRITE-FLOOR TEST: the held-out clause catches A SILENT CHANGE TO THE
--   PARTITION SEED OR HASH FUNCTION -- a writer switch from MD5 to SHA-1, or
--   from `mod 10 >= 8` to `>= 7`, re-partitions the corpus while leaving the row
--   count at exactly 64. Every leakage guarantee downstream (mi_pramana's scored
--   set) rests on that partition being the one it was declared to be. The
--   admissibility clause catches admissible_clean drifting from its own three
--   stated conditions -- the exact "flag with no detector behind it" class of
--   CLAUDE.md §N.8. The FULL JOIN catches a provenance row for an event that no
--   longer exists (a deleted LEL row leaving a phantom in the calibration ground
--   truth) and an appended LEL event that never reached the bridge.
--
-- NOT VACUOUS: 64 rows; the SQL recomputation matches all 64 (13/64 held out).
--
-- OPERATIONAL SENSITIVITY -- READ THIS BEFORE FILING A BUG: a native LEL append
--   makes this check `false` until mi_jivanaghatana re-runs. That is DELIBERATE.
--   It is the only staleness detector L5 has for LEL changes -- W1 L5-F-01 shows
--   asset_registry.depends_on('mi_jivanaghatana') omits `lel_events` entirely,
--   so nothing else can see an LEL append at all. A red here should be read as
--   "the bridge is stale", not "the data is corrupt", and the detector message
--   should say so.
--
-- DROPPED:
--   * lel_file_sha pinning: NULL 64/64 by construction (W1 L5-F-12) -- an
--     equality would fail.
--   * event_magnitude non-null: NULL 64/64 (W1 L5-F-02, the root cause of the
--     constant score_magnitude=0.5 downstream) -- would fail.
--   * A meaningful disclosure_timing vocabulary: the column is the literal
--     'unknown' 64/64. A vocabulary pin on a single dead constant asserts
--     nothing, so it was dropped rather than shipped as a clause that cannot
--     fail (C12 rewrite-floor test).
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1
  FROM life_events le
  FULL JOIN mimamsa_event_provenance ep
    ON ep.chart_id = le.chart_id AND ep.event_id = le.event_id
  GROUP BY coalesce(le.chart_id, ep.chart_id)
  HAVING count(*) FILTER (WHERE le.event_id IS NULL OR ep.event_id IS NULL) > 0
      OR count(DISTINCT ep.event_id) <> count(ep.event_id)
      OR count(*) FILTER (WHERE ep.event_id IS NOT NULL
             AND ep.held_out <> ((('x' || lpad(substr(md5(ep.event_id), 1, 8), 16, '0'))::bit(64)::bigint % 10) >= 8)) > 0
      OR count(*) FILTER (WHERE ep.event_id IS NOT NULL AND ep.partition_seed_version <> 'v1_md5_mod10') > 0
      OR count(*) FILTER (WHERE ep.event_id IS NOT NULL
             AND ep.admissible_clean <> (NOT ep.shaped_predictor
                                         AND ep.disclosure_timing <> 'post_framework_undated'
                                         AND ep.event_date IS NOT NULL)) > 0
      OR count(*) FILTER (WHERE ep.event_id IS NOT NULL AND ep.event_date IS DISTINCT FROM le.event_date) > 0
      OR count(*) FILTER (WHERE ep.event_id IS NOT NULL
             AND (btrim(coalesce(ep.lel_version, '')) = ''
                  OR btrim(coalesce(ep.provenance_formula_ver, '')) = ''
                  OR btrim(coalesce(ep.domain_primary, '')) = ''
                  OR btrim(coalesce(ep.admissibility_reason, '')) = '')) > 0
)
$check$
 WHERE asset_id = 'mi_jivanaghatana';


-- ────────────────────────────────────────────────────────────────────────────
-- 3. mi_bhavisya -- the frozen prediction bundle (`mimamsa_predictions` +
--    `mimamsa_manifestation_sets`). per_chart.
--
-- INVARIANTS: per chart -- FULL JOIN predictions <-> manifestation_sets on
--   (chart_id, prediction_id), zero one-sided rows; REFERENTIAL CLOSURE TO L4 --
--   every source_pramana_id resolves to a phala_anchors.anchor_id ON THE SAME
--   CHART; DERIVED-VALUE REPRODUCIBILITY -- eval_date = upper(observation_window);
--   the window is a non-empty '[)' daterange; confidence_band non-empty within
--   [0,1]; frozen_bundle_hash / bundle_formula_version / outcome_claim / domain
--   non-blank and falsifier_jsonb / driving_signals non-null; each manifestation
--   set's domain agrees with its prediction's domain; prediction_id distinct per
--   chart; (prediction_id, channel_id) distinct per chart.
--
-- REWRITE-FLOOR TEST: the phala_anchors closure catches AN L4 REBUILD THAT
--   RE-MINTS anchor_ids WHILE L5 PREDICTIONS STILL CITE THE OLD ONES -- the exact
--   §N.5 authority-inversion failure; the row count on both sides stays 195.
--   eval_date = upper(observation_window) catches a window shifted without its
--   evaluation date following (a prediction that becomes unfalsifiable on
--   schedule). The domain-agreement clause catches a manifestation channel filed
--   against a prediction in a different domain -- the row is present, the count
--   is right, the linkage is wrong.
--
-- NOT VACUOUS: 195 predictions + 195 manifestation sets; 0 orphan anchors;
--   eval_date = upper(window) on 195/195.
--
-- DROPPED:
--   * frozen_bundle_hash DISTINCTNESS -- deliberately NOT pinned. W1 established
--     it is a per-run nonce (it mixes in emitted_at), which is ITSELF a defect.
--     Pinning its distinctness would enshrine the defect as a virtue. Only its
--     non-blankness is asserted.
--   * channel_id = 'ch_' || domain || '_verbal': holds 195/195 today but
--     enshrines W1 L5-F-13 (one channel per domain is structurally degenerate --
--     with a single channel, fire/opportunity can only be 0 or 1 and no channel
--     discrimination is possible). Scheduled to be fixed; dropped for the same
--     reason as the bundle hash.
--   * lifecycle_status closed vocabulary: only 'pending' exists live and the
--     full lifecycle vocabulary is unwritten anywhere readable. Inventing the
--     other states is forbidden.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1
    FROM mimamsa_predictions p
    FULL JOIN mimamsa_manifestation_sets m
      ON m.chart_id = p.chart_id AND m.prediction_id = p.prediction_id
    LEFT JOIN charts c ON c.id = coalesce(p.chart_id, m.chart_id)
    GROUP BY coalesce(p.chart_id, m.chart_id)
    HAVING count(*) FILTER (WHERE p.prediction_id IS NULL OR m.prediction_id IS NULL) > 0
        OR count(*) FILTER (WHERE c.id IS NULL) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (isempty(p.observation_window) OR NOT lower_inc(p.observation_window)
                    OR upper_inc(p.observation_window) OR p.eval_date <> upper(p.observation_window))) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (p.confidence_band IS NULL OR isempty(p.confidence_band)
                    OR lower(p.confidence_band) < 0 OR upper(p.confidence_band) > 1)) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND (btrim(coalesce(p.frozen_bundle_hash, '')) = ''
                    OR btrim(coalesce(p.bundle_formula_version, '')) = ''
                    OR btrim(coalesce(p.outcome_claim, '')) = ''
                    OR btrim(coalesce(p.domain, '')) = ''
                    OR p.falsifier_jsonb IS NULL OR p.driving_signals IS NULL)) > 0
        OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL
               AND NOT EXISTS (SELECT 1 FROM phala_anchors a
                                WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0
        OR count(*) FILTER (WHERE m.prediction_id IS NOT NULL AND m.domain IS DISTINCT FROM p.domain) > 0
        OR count(*) FILTER (WHERE m.prediction_id IS NOT NULL
               AND (m.citation_ref IS NULL OR btrim(coalesce(m.channel_id, '')) = ''
                    OR btrim(coalesce(m.source, '')) = '')) > 0
  )
  AND NOT EXISTS (SELECT 1 FROM mimamsa_predictions GROUP BY chart_id
                   HAVING count(DISTINCT prediction_id) <> count(*))
  AND NOT EXISTS (SELECT 1 FROM mimamsa_manifestation_sets GROUP BY chart_id
                   HAVING count(DISTINCT (prediction_id, channel_id)) <> count(*))
$check$
 WHERE asset_id = 'mi_bhavisya';


-- ────────────────────────────────────────────────────────────────────────────
-- 4. mi_pramana -- the STRUCTURAL-mode heart (`mimamsa_calibration` +
--    `mimamsa_reliability`). per_chart.
--
-- INVARIANTS: CALIBRATION -- match_id distinct per chart and
--   match_id = prediction_id || '_' || event_id; zero-orphan joins to
--   mimamsa_predictions and mimamsa_event_provenance on the same chart; THE
--   LEAKAGE FIREWALL -- no scored row may join a provenance row that is held_out
--   or NOT admissible_clean, and leakage_status = evidence_admissibility =
--   'clean'; composite_verdict in {CONFIRMED, PARTIAL, REFUTED, UNRESOLVED}; all
--   five dimension scores and composite_score in [0,1].
--   RELIABILITY -- stratum_key distinct per chart; sum(n) per chart EQUALS that
--   chart's calibration row count (aggregate closure); stratum_key =
--   'domain_all|' || predicted_prob_bin::text; bins non-empty within [0,1] and
--   PAIRWISE NON-OVERLAPPING (a proper tiling); hit_rate_by_tier = observed_rate;
--   held_out_validity / evidence_grade reproduce the writer's own n>=5 threshold
--   (pass/insufficient_n, empirical/prior_only -- mi_pramana.py:472-473).
--
-- REWRITE-FLOOR TEST: the leakage clause is the one the layer exists to protect
--   -- it catches A HELD-OUT EVENT ENTERING THE SCORED SET, the single failure
--   that would silently convert calibration into self-grading. The row count
--   would go UP, and an increase reads as progress. The sum(n) = calibration
--   count clause catches a partial re-score (calibration rebuilt, reliability
--   not, or vice versa) -- a straddle where both tables individually look
--   populated. The n>=5 => 'empirical' clause catches a grade promoted above its
--   own evidence threshold (§N.8 exactly).
--
-- NOT VACUOUS: 57 calibration rows, 6 reliability strata, sum(n) = 57 = 57.
--
-- DROPPED -- AND THIS ONE PRODUCED A LIVE FINDING (see KNOWN GAPS #1):
--   * reliability.n = the recomputed count of calibration rows in the bin --
--     DROPPED, IT FAILS AGAINST THE DATA THAT IS LIVE TODAY. See KNOWN GAPS #1.
--     The WRITER defect is already fixed on this branch (commit 14f8c0c94,
--     A-F-34), but the STORED reliability rows still carry the old binning until
--     mi_pramana is re-run, so the clause would start red. The sum(n) +
--     non-overlap clauses that DID ship still catch total-count straddles; only
--     per-bin PLACEMENT is un-gated until the rebuild lands.
--     RE-ADD THIS CLAUSE AFTER THE REBUILD -- at that point it becomes the
--     strongest check on this asset, and the gap closes.
--   * observed_rate recomputed per bin: same root cause, same two strata.
--   * ece / log_loss / ci_low / ci_high non-null: written None unconditionally
--     (mi_pramana.py:482-485, W1 L5-F-30) -- would fail.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1 FROM mimamsa_calibration c
    GROUP BY c.chart_id
    HAVING count(DISTINCT c.match_id) <> count(*)
        OR count(*) FILTER (WHERE c.match_id <> c.prediction_id || '_' || c.event_id) > 0
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_predictions p
                                               WHERE p.chart_id = c.chart_id AND p.prediction_id = c.prediction_id)) > 0
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_event_provenance e
                                               WHERE e.chart_id = c.chart_id AND e.event_id = c.event_id)) > 0
        OR count(*) FILTER (WHERE EXISTS (SELECT 1 FROM mimamsa_event_provenance e
                                           WHERE e.chart_id = c.chart_id AND e.event_id = c.event_id
                                             AND (e.held_out OR NOT e.admissible_clean))) > 0
        OR count(*) FILTER (WHERE c.leakage_status <> 'clean' OR c.evidence_admissibility <> 'clean') > 0
        OR count(*) FILTER (WHERE c.composite_verdict NOT IN ('CONFIRMED','PARTIAL','REFUTED','UNRESOLVED')) > 0
        OR count(*) FILTER (WHERE c.score_timing NOT BETWEEN 0 AND 1 OR c.score_magnitude NOT BETWEEN 0 AND 1
                              OR c.score_domain NOT BETWEEN 0 AND 1 OR c.score_falsifier NOT BETWEEN 0 AND 1
                              OR c.score_manifestation NOT BETWEEN 0 AND 1 OR c.composite_score NOT BETWEEN 0 AND 1) > 0
        OR count(*) FILTER (WHERE c.n_for_stratum < 0 OR btrim(coalesce(c.scoring_formula_version, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_reliability r
    GROUP BY r.chart_id
    HAVING count(DISTINCT r.stratum_key) <> count(*)
        OR sum(r.n) <> (SELECT count(*) FROM mimamsa_calibration c WHERE c.chart_id = r.chart_id)
        OR count(*) FILTER (WHERE r.stratum_key <> 'domain_all|' || r.predicted_prob_bin::text) > 0
        OR count(*) FILTER (WHERE r.predicted_prob_bin IS NULL OR isempty(r.predicted_prob_bin)
                              OR lower(r.predicted_prob_bin) < 0 OR upper(r.predicted_prob_bin) > 1) > 0
        OR count(*) FILTER (WHERE EXISTS (SELECT 1 FROM mimamsa_reliability r2
                                           WHERE r2.chart_id = r.chart_id AND r2.stratum_key <> r.stratum_key
                                             AND r2.predicted_prob_bin && r.predicted_prob_bin)) > 0
        OR count(*) FILTER (WHERE r.n < 1 OR r.observed_rate NOT BETWEEN 0 AND 1
                              OR r.hit_rate_by_tier IS DISTINCT FROM r.observed_rate) > 0
        OR count(*) FILTER (WHERE r.held_out_validity <> CASE WHEN r.n >= 5 THEN 'pass' ELSE 'insufficient_n' END
                              OR r.evidence_grade <> CASE WHEN r.n >= 5 THEN 'empirical' ELSE 'prior_only' END) > 0
        OR count(*) FILTER (WHERE btrim(coalesce(r.calibration_formula_ver, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_pramana';


-- ────────────────────────────────────────────────────────────────────────────
-- 5. mi_gunanaka -- per-chart learned multipliers over the non-control signal
--    families (`mimamsa_multipliers` + `mimamsa_calibration_snapshot`). per_chart.
--
-- INVARIANTS: MULTIPLIERS -- per chart, target_ref and weight_id distinct; every
--   target_ref resolves to an ACTIVE, NON-'CONTROL_ONLY'
--   mimamsa_signal_families.family_id, and the count of distinct target_refs
--   EQUALS the count of such families (set equality, both directions);
--   weight_id = mechanism || ':' || target_ref; DERIVED-VALUE REPRODUCIBILITY --
--   evidence_factor = round(raw_multiplier/2, 4) and divergence_from_classical =
--   round(|applied_multiplier - prior_weight| / prior_weight, 4);
--   n_observations = 0 => promotion_status='prior_only' AND applied_multiplier =
--   the family's prior_weight AND held_out_validity='insufficient_n' AND NOT
--   gate_passed AND NOT confidence_high; promotion_status='promoted' =>
--   n_observations > 0 AND gate_passed AND confidence_high AND neg_control_clear
--   AND held_out_validity='pass'.
--   SNAPSHOTS -- snapshot_id distinct and prefixed by its own chart's first 8
--   hex; two_key_complete IFF acharya_pratinidhi_key IS NOT NULL;
--   publication_status='published' => two_key_complete.
--
-- REWRITE-FLOOR TEST: the `promoted =>` clause is the earned-signal gate -- it
--   catches A MULTIPLIER PROMOTED INTO THE LIVE OVERLAY WHILE ITS OWN GATE FLAGS
--   SAY THE GATE DID NOT PASS; the count stays 9. The `n_observations = 0 =>
--   applied = prior_weight` clause catches an unearned multiplier drifting off
--   its prior with zero evidence behind it -- a learned weight invented from
--   nothing. divergence_from_classical reproducibility catches the divergence
--   figure being computed against a STALE prior after mi_kula reseeds: the
--   number stays plausible and stops being true. The two-key clause catches
--   two_key_complete = true with no second key present -- a governance approval
--   that no one gave.
--
-- NOT VACUOUS: 18 multiplier rows (9 families x 2 charts), both derived formulas
--   reproduce on 18/18; 5 snapshots.
--
-- DROPPED:
--   * applied_multiplier = raw_multiplier: holds 18/18 today but would break the
--     moment a legitimate clipping bound engages. Replaced with `> 0` plus the
--     two clauses that tie `applied` to prior_weight.
--   * promotion_status / kill_switch_state vocabularies beyond the live values
--     are permissive extras ('held', 'demoted', 'tripped' have no live
--     instances), so those list members cannot currently fail; only the live
--     values are load-bearing. Recorded so the clause is not mistaken for a
--     fully-exercised vocabulary gate.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1
    FROM mimamsa_multipliers m
    LEFT JOIN mimamsa_signal_families f
      ON f.family_id = m.target_ref AND f.is_active AND f.default_state <> 'CONTROL_ONLY'
    GROUP BY m.chart_id
    HAVING count(DISTINCT m.target_ref) <> count(*)
        OR count(DISTINCT m.weight_id) <> count(*)
        OR count(*) FILTER (WHERE f.family_id IS NULL) > 0
        OR count(DISTINCT m.target_ref) <> (SELECT count(*) FROM mimamsa_signal_families f2
                                             WHERE f2.is_active AND f2.default_state <> 'CONTROL_ONLY')
        OR count(*) FILTER (WHERE m.weight_id <> m.mechanism || ':' || m.target_ref) > 0
        OR count(*) FILTER (WHERE m.applied_multiplier <= 0 OR m.raw_multiplier <= 0 OR m.n_observations < 0) > 0
        OR count(*) FILTER (WHERE m.evidence_factor <> round(m.raw_multiplier / 2, 4)) > 0
        OR count(*) FILTER (WHERE m.divergence_from_classical
                                  <> round(abs(m.applied_multiplier - f.prior_weight) / f.prior_weight, 4)) > 0
        OR count(*) FILTER (WHERE m.n_observations = 0
                              AND NOT (m.promotion_status = 'prior_only'
                                       AND m.applied_multiplier = f.prior_weight
                                       AND m.held_out_validity = 'insufficient_n'
                                       AND NOT m.gate_passed AND NOT m.confidence_high)) > 0
        OR count(*) FILTER (WHERE m.promotion_status = 'promoted'
                              AND NOT (m.n_observations > 0 AND m.gate_passed AND m.confidence_high
                                       AND m.neg_control_clear AND m.held_out_validity = 'pass')) > 0
        OR count(*) FILTER (WHERE m.promotion_status NOT IN ('prior_only','promoted','held','demoted')
                              OR m.kill_switch_state NOT IN ('active','tripped')
                              OR m.audit_trail IS NULL
                              OR btrim(coalesce(m.weight_formula_version, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1
    FROM mimamsa_calibration_snapshot s
    LEFT JOIN charts c ON c.id = s.chart_id
    GROUP BY s.chart_id
    HAVING count(DISTINCT s.snapshot_id) <> count(*)
        OR count(*) FILTER (WHERE c.id IS NULL) > 0
        OR count(*) FILTER (WHERE s.snapshot_id NOT LIKE 'snap_' || left(s.chart_id::text, 8) || '\_%') > 0
        OR count(*) FILTER (WHERE s.two_key_complete <> (s.acharya_pratinidhi_key IS NOT NULL)) > 0
        OR count(*) FILTER (WHERE s.publication_status = 'published' AND NOT s.two_key_complete) > 0
        OR count(*) FILTER (WHERE s.publication_status NOT IN ('proposed','published','withdrawn')
                              OR s.cells_jsonb IS NULL
                              OR btrim(coalesce(s.proposing_executor, '')) = ''
                              OR btrim(coalesce(s.formula_version, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_gunanaka';


-- ────────────────────────────────────────────────────────────────────────────
-- 6. mi_pariksha -- attribution engine + QA harness + retrodiction suite
--    (`mimamsa_qa_eval` + `mimamsa_attribution` + `mimamsa_discoveries`).
--    per_chart.
--
-- INVARIANTS: QA EVAL -- per chart, check_id distinct; check_type and status in
--   their ACTUAL LIVE closed vocabularies (the status list explicitly names
--   'FAIL_event_too_close'); status='not_implemented' IFF result_score IS NULL
--   (a check with no detector reports no score, and a scoreless row must say
--   so); detail / checked_at non-null.
--   ATTRIBUTION -- (match_id, signal_id, dimension) distinct; dimension in the
--   five mimamsa_calibration score dimensions; EVERY (match_id, signal_id)
--   carries EXACTLY 5 dimensions (count(*) = 5 * count(DISTINCT (match_id,
--   signal_id)) -- complete tiling); every match_id resolves to
--   mimamsa_calibration and every family_id to mimamsa_signal_families;
--   credit_blame in [-1,1].
--   COVERAGE -- every calibration row on a chart has at least one attribution row.
--   DISCOVERIES -- discovery_id distinct; discovery_class in {retrodiction,
--   emergent_law}; citation_required => citation_ref IS NOT NULL; strength in
--   [0,1]; confidence_band bounded when present.
--
-- REWRITE-FLOOR TEST: the `not_implemented IFF result_score IS NULL`
--   bi-conditional is the §N.8 detector -- it catches negative_control ACQUIRING
--   A NUMERIC SCORE WITHOUT THE SYNTHETIC-INJECTION HARNESS THAT WOULD JUSTIFY
--   ONE (an unimplemented check quietly starting to report PASS-shaped numbers),
--   and equally catches a real check losing its score while keeping a confident
--   status. The `count(*) = 5 x distinct pairs` tiling catches a partial
--   executemany batch failure that drops one dimension across many rows -- the
--   total falls by a plausible-looking amount and the credit ledger silently
--   stops summing to the composite. The STATUS VOCABULARY PIN is the shipped
--   countermeasure to W1 L5-F-07: a new status string cannot enter the served
--   surface without this check going red, forcing the disclosure that
--   query_calibration.ts:150-151's exact `=== 'FAIL'` comparison currently
--   misses (61 live rows are 'FAIL_event_too_close' and are reported as 0
--   failures).
--
-- NOT VACUOUS: 174 qa rows / 1,425 attribution rows (= 285 x 5 exactly) / 71
--   discoveries.
--
-- DROPPED:
--   * status NOT LIKE 'FAIL%': 61 live rows are 'FAIL_event_too_close' -- an
--     assertion of no-failures would fail, and would also be the WRONG CLAIM:
--     those FAILs are honest writer output, not corruption.
--   * A clause requiring evidence behind a degenerate_distribution 'pass': W1
--     L5-F-08's defect is live on row degen_dist_1c826d5a (a `pass` emitted on a
--     chart with ZERO calibration rows, because `baseline` falls back to the
--     literal 0.5 at mi_pariksha.py:576-580). Any such clause fails today. Left
--     as W1's open finding.
--   * activation_status closed vocabulary: the writer only ever emits
--     'candidate' (mi_pariksha.py:260, :735), but the promotion vocabulary is
--     unwritten; pinning one value would forbid a legitimate future promotion.
--     Only non-blankness is asserted.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1 FROM mimamsa_qa_eval q LEFT JOIN charts ch ON ch.id = q.chart_id
    GROUP BY q.chart_id
    HAVING count(DISTINCT q.check_id) <> count(*)
        OR count(*) FILTER (WHERE ch.id IS NULL) > 0
        OR count(*) FILTER (WHERE q.check_type NOT IN
              ('ablation','control_window','degenerate_distribution','negative_control','tail_only')) > 0
        OR count(*) FILTER (WHERE q.status NOT IN
              ('pass','control_baseline','structural_proxy','not_implemented','FAIL_event_too_close')) > 0
        OR count(*) FILTER (WHERE (q.status = 'not_implemented') <> (q.result_score IS NULL)) > 0
        OR count(*) FILTER (WHERE q.detail IS NULL OR q.checked_at IS NULL
                              OR btrim(coalesce(q.check_id, '')) = '' OR btrim(coalesce(q.target, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_attribution a
    GROUP BY a.chart_id
    HAVING count(DISTINCT (a.match_id, a.signal_id, a.dimension)) <> count(*)
        OR count(*) <> 5 * count(DISTINCT (a.match_id, a.signal_id))
        OR count(*) FILTER (WHERE a.dimension NOT IN
              ('timing','magnitude','domain','falsifier','manifestation')) > 0
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_calibration c
                                               WHERE c.chart_id = a.chart_id AND c.match_id = a.match_id)) > 0
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_signal_families f
                                               WHERE f.family_id = a.family_id)) > 0
        OR count(*) FILTER (WHERE a.credit_blame NOT BETWEEN -1 AND 1
                              OR btrim(coalesce(a.signal_id, '')) = ''
                              OR btrim(coalesce(a.attribution_formula_ver, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_calibration c
    GROUP BY c.chart_id
    HAVING count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_attribution a
                                               WHERE a.chart_id = c.chart_id AND a.match_id = c.match_id)) > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_discoveries d LEFT JOIN charts ch ON ch.id = d.chart_id
    GROUP BY d.chart_id
    HAVING count(DISTINCT d.discovery_id) <> count(*)
        OR count(*) FILTER (WHERE ch.id IS NULL) > 0
        OR count(*) FILTER (WHERE d.discovery_class NOT IN ('retrodiction','emergent_law')) > 0
        OR count(*) FILTER (WHERE d.citation_required AND d.citation_ref IS NULL) > 0
        OR count(*) FILTER (WHERE d.strength IS NOT NULL AND d.strength NOT BETWEEN 0 AND 1) > 0
        OR count(*) FILTER (WHERE d.confidence_band IS NOT NULL
                              AND (isempty(d.confidence_band) OR lower(d.confidence_band) < 0
                                   OR upper(d.confidence_band) > 1)) > 0
        OR count(*) FILTER (WHERE d.n_support < 0 OR d.evidence_refs IS NULL
                              OR btrim(coalesce(d.statement, '')) = ''
                              OR btrim(coalesce(d.activation_status, '')) = ''
                              OR btrim(coalesce(d.discovery_formula_ver, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_pariksha';


-- ────────────────────────────────────────────────────────────────────────────
-- 7. mi_adhilepa -- calibration overlay across L1-L4 (4 *_adjustment tables) +
--    the load-bearing map (`mimamsa_load_bearing`). per_chart.
--
-- INVARIANTS: OVERLAYS (all four *_adjustment tables, unioned) -- per chart,
--   every weight_id resolves to a mimamsa_multipliers.weight_id ON THE SAME
--   CHART; each table's origin_layer is its own fixed layer (L1/L2/L3/L4);
--   OVERLAY-CONSISTENCY: multiplier = the multiplier row's applied_multiplier,
--   raw_multiplier = its raw_multiplier, evidence_n = its n_observations,
--   applied_bound = multiplier; derived_from_pramana_ids non-null; origin_id
--   distinct per chart per table.
--   LOAD-BEARING -- conclusion_id distinct and = 'concl_' || signal_id; role
--   vocabulary; EXACTLY ONE 'load_bearing' per chart and the 'supporting' count
--   = least(2, n-1) (the writer's rank tiering, mi_adhilepa.py:347); row count =
--   least(5, count of that chart's multipliers with applied_multiplier >= 1.0)
--   (mi_adhilepa.py:335-342); every signal_id resolves to such a multiplier;
--   sensitivity = round(least(applied_multiplier/2, 1.0), 4)
--   (mi_adhilepa.py:346); role rank MONOTONE with sensitivity (no higher-ranked
--   role carries strictly lower sensitivity than a lower-ranked one).
--
-- REWRITE-FLOOR TEST: the overlay-consistency clauses catch EXACTLY W1 L5-F-18's
--   stated live risk -- THE MULTIPLIER SET CHANGING WITHOUT A RE-OVERLAY.
--   mi_gunanaka re-runs, fam_graha_natal moves from 1.1 to 0.9924, and 123,272
--   mimamsa_fact_adjustment rows keep applying the old figure to every served L1
--   fact. The row count is IDENTICAL; the served numbers are stale. Nothing else
--   in the layer can see this. The least(5, qualifying multipliers) clause
--   catches the load-bearing map going stale the same way -- a family crossing
--   the 1.0 threshold without the map being rebuilt. The role-monotonicity
--   clause catches a rank tiering that no longer follows its own ordering.
--
-- NOT VACUOUS: 224,742 overlay rows across the 4 tables (0 mismatches on all
--   three overlay-consistency columns) + 9 load-bearing rows.
--
-- DROPPED:
--   * leakage_status closed vocabulary: only 'not_assessed' exists live and the
--     other states are unwritten -- pinning the one value would forbid the
--     honest future value. Only non-blankness is asserted.
--   * Any clause treating load_bearing.signal_id as drillable to a signal: it
--     holds a FAMILY_ID, not a signal id (W1 L5-F-19), so the drill contract is
--     unsatisfiable as the data is shaped. The check asserts what the column
--     really references; it does not pretend otherwise.
--   * NOTE FOR THE RELABELLING WORK (W1 L5-F-20): if `role -> prior_rank` and
--     `sensitivity -> prior_weight_scaled` land, this check needs exactly one
--     edit. It is written against the current column names.
UPDATE asset_registry
   SET integrity_check_sql = $check$
WITH ov AS (
  SELECT chart_id, origin_layer, origin_asset_id, origin_id, weight_id, multiplier,
         raw_multiplier, applied_bound, evidence_n, leakage_status,
         derived_from_pramana_ids, overlay_formula_version, 'L1' AS want_layer
    FROM mimamsa_fact_adjustment
  UNION ALL
  SELECT chart_id, origin_layer, origin_asset_id, origin_id, weight_id, multiplier,
         raw_multiplier, applied_bound, evidence_n, leakage_status,
         derived_from_pramana_ids, overlay_formula_version, 'L2'
    FROM mimamsa_signal_adjustment
  UNION ALL
  SELECT chart_id, origin_layer, origin_asset_id, origin_id, weight_id, multiplier,
         raw_multiplier, applied_bound, evidence_n, leakage_status,
         derived_from_pramana_ids, overlay_formula_version, 'L3'
    FROM mimamsa_convergence_adjustment
  UNION ALL
  SELECT chart_id, origin_layer, origin_asset_id, origin_id, weight_id, multiplier,
         raw_multiplier, applied_bound, evidence_n, leakage_status,
         derived_from_pramana_ids, overlay_formula_version, 'L4'
    FROM mimamsa_anchor_adjustment
)
SELECT
  NOT EXISTS (
    SELECT 1 FROM ov
    LEFT JOIN mimamsa_multipliers m ON m.chart_id = ov.chart_id AND m.weight_id = ov.weight_id
    GROUP BY ov.chart_id
    HAVING count(*) FILTER (WHERE m.weight_id IS NULL) > 0
        OR count(*) FILTER (WHERE ov.origin_layer <> ov.want_layer) > 0
        OR count(*) FILTER (WHERE ov.multiplier IS DISTINCT FROM m.applied_multiplier
                              OR ov.raw_multiplier IS DISTINCT FROM m.raw_multiplier
                              OR ov.applied_bound IS DISTINCT FROM ov.multiplier
                              OR ov.evidence_n IS DISTINCT FROM m.n_observations) > 0
        OR count(*) FILTER (WHERE ov.derived_from_pramana_ids IS NULL
                              OR btrim(coalesce(ov.origin_id, '')) = ''
                              OR btrim(coalesce(ov.origin_asset_id, '')) = ''
                              OR btrim(coalesce(ov.leakage_status, '')) = ''
                              OR btrim(coalesce(ov.overlay_formula_version, '')) = '') > 0
  )
  AND NOT EXISTS (SELECT 1 FROM mimamsa_fact_adjustment        GROUP BY chart_id HAVING count(DISTINCT origin_id) <> count(*))
  AND NOT EXISTS (SELECT 1 FROM mimamsa_signal_adjustment      GROUP BY chart_id HAVING count(DISTINCT origin_id) <> count(*))
  AND NOT EXISTS (SELECT 1 FROM mimamsa_convergence_adjustment GROUP BY chart_id HAVING count(DISTINCT origin_id) <> count(*))
  AND NOT EXISTS (SELECT 1 FROM mimamsa_anchor_adjustment      GROUP BY chart_id HAVING count(DISTINCT origin_id) <> count(*))
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_load_bearing lb
    GROUP BY lb.chart_id
    HAVING count(DISTINCT lb.conclusion_id) <> count(*)
        OR count(*) FILTER (WHERE lb.conclusion_id <> 'concl_' || lb.signal_id) > 0
        OR count(*) FILTER (WHERE lb.role NOT IN ('load_bearing','supporting','redundant')) > 0
        OR count(*) FILTER (WHERE lb.role = 'load_bearing') <> 1
        OR count(*) FILTER (WHERE lb.role = 'supporting') <> least(2, count(*) - 1)
        OR count(*) <> (SELECT least(5, count(*)) FROM mimamsa_multipliers m2
                         WHERE m2.chart_id = lb.chart_id AND m2.applied_multiplier >= 1.0)
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_multipliers m3
                                               WHERE m3.chart_id = lb.chart_id
                                                 AND m3.target_ref = lb.signal_id
                                                 AND m3.applied_multiplier >= 1.0)) > 0
        OR count(*) FILTER (WHERE lb.sensitivity IS DISTINCT FROM
                                  (SELECT round(least(m4.applied_multiplier / 2, 1.0), 4)
                                     FROM mimamsa_multipliers m4
                                    WHERE m4.chart_id = lb.chart_id AND m4.target_ref = lb.signal_id)) > 0
        OR count(*) FILTER (WHERE EXISTS (
              SELECT 1 FROM mimamsa_load_bearing lb2
               WHERE lb2.chart_id = lb.chart_id
                 AND CASE lb.role WHEN 'load_bearing' THEN 1 WHEN 'supporting' THEN 2 ELSE 3 END
                   < CASE lb2.role WHEN 'load_bearing' THEN 1 WHEN 'supporting' THEN 2 ELSE 3 END
                 AND lb.sensitivity < lb2.sensitivity)) > 0
        OR count(*) FILTER (WHERE btrim(coalesce(lb.formula_version, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_adhilepa';


-- ────────────────────────────────────────────────────────────────────────────
-- 8. mi_sambandha -- manifestation-channel propensity grammar
--    (`mimamsa_manifestation_grammar`). per_chart.
--
-- INVARIANTS: per chart -- (origin_kind, origin_ref, channel_id) distinct; counts
--   non-negative with fire_count <= opportunity_count and scored_count <=
--   opportunity_count; opportunity_count = 0 IFF channel_propensity IS NULL (the
--   honest-null discipline the F-147 fix installed);
--   DERIVED-VALUE REPRODUCIBILITY -- channel_propensity =
--   round(fire_count/opportunity_count, 4) whenever opportunity_count > 0, and
--   propensity_delta = round(channel_propensity - prior_propensity, 4)
--   (NULL-safe); propensities in [0,1]; confidence_band bounded when present;
--   opportunity_count > 0 => channel_id resolves to a mimamsa_manifestation_sets
--   row on the same chart; evidence_grade in {empirical, prior_only};
--   citation_ref non-null.
--
-- REWRITE-FLOOR TEST: the `opportunity_count = 0 IFF propensity IS NULL`
--   bi-conditional is the shipped guard against the exact defect F-147 was
--   written to fix -- A CHANNEL WITH NO OPPORTUNITIES ACQUIRING A NUMERIC 0.0
--   PROPENSITY, which the serving layer then narrates verbatim as "fires with 0%
--   propensity (n=37, empirical learning)". That is a fabricated measurement and
--   it is invisible to a row count. The propensity reproducibility clause
--   catches fire_count / opportunity_count being updated without the ratio
--   following -- a stale rate presented as current.
--
-- NOT VACUOUS: 47 rows; both derived formulas reproduce on 47/47.
--
-- DROPPED -- ALL THREE FAIL LIVE AND ARE REPORTED AS FINDINGS (KNOWN GAPS #3):
--   * evidence_grade='empirical' => scored_count > 0 -- FAILS on 10 rows (all 10
--     also carry a non-NULL channel_propensity). W1 L5-F-14 confirmed live: an
--     'empirical' grade with nothing scored behind it. This is the unearned-
--     signal defect (§N.8), to be fixed by the pending v1.2 rebuild, NOT gated
--     around. All 47 live rows are grammar_formula_version='mi_sambandha_v1.0'
--     while HEAD is v1.2 (PR #1439, commit 44f42fe94).
--   * n_support = scored_count -- FAILS on 13 rows. A naming defect: n_support is
--     not the count it is named for.
--   * UNCONDITIONAL channel referential closure -- FAILS on 34 rows (17 per
--     chart). The _PRIOR_PROPENSITIES seed (mi_sambandha.py:90-99) emits
--     prior_only rows for 20 channels (ch_career_material, ch_rel_partnership,
--     ...) that mi_bhavisya can NEVER produce -- it emits exactly 7, all
--     ch_<domain>_verbal (W1 L5-F-13). The SHIPPED clause is deliberately
--     narrowed to `opportunity_count > 0`, which is the honest scope: any
--     channel with real opportunities must exist in the prediction sets. The
--     seeded orphans stay un-gated until the vocabulary is reconciled.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1 FROM mimamsa_manifestation_grammar g
  GROUP BY g.chart_id
  HAVING count(DISTINCT (g.origin_kind, g.origin_ref, g.channel_id)) <> count(*)
      OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = g.chart_id)) > 0
      OR count(*) FILTER (WHERE g.fire_count < 0 OR g.opportunity_count < 0 OR g.scored_count < 0
                            OR g.n_support < 0 OR g.fire_count > g.opportunity_count
                            OR g.scored_count > g.opportunity_count) > 0
      OR count(*) FILTER (WHERE (g.opportunity_count = 0) <> (g.channel_propensity IS NULL)) > 0
      OR count(*) FILTER (WHERE g.opportunity_count > 0
                            AND g.channel_propensity
                                IS DISTINCT FROM round(g.fire_count::numeric / g.opportunity_count, 4)) > 0
      OR count(*) FILTER (WHERE g.propensity_delta
                                IS DISTINCT FROM round(g.channel_propensity - g.prior_propensity, 4)) > 0
      OR count(*) FILTER (WHERE g.prior_propensity NOT BETWEEN 0 AND 1
                            OR (g.channel_propensity IS NOT NULL
                                AND g.channel_propensity NOT BETWEEN 0 AND 1)) > 0
      OR count(*) FILTER (WHERE g.confidence_band IS NOT NULL
                            AND (isempty(g.confidence_band) OR lower(g.confidence_band) < 0
                                 OR upper(g.confidence_band) > 1)) > 0
      OR count(*) FILTER (WHERE g.opportunity_count > 0
                            AND NOT EXISTS (SELECT 1 FROM mimamsa_manifestation_sets s
                                             WHERE s.chart_id = g.chart_id AND s.channel_id = g.channel_id)) > 0
      OR count(*) FILTER (WHERE g.evidence_grade NOT IN ('empirical','prior_only')
                            OR g.citation_ref IS NULL
                            OR btrim(coalesce(g.origin_kind, '')) = ''
                            OR btrim(coalesce(g.origin_ref, '')) = ''
                            OR btrim(coalesce(g.domain, '')) = ''
                            OR btrim(coalesce(g.grammar_formula_version, '')) = '') > 0
)
$check$
 WHERE asset_id = 'mi_sambandha';


-- ────────────────────────────────────────────────────────────────────────────
-- 9. mi_darshana -- insight retrieval surface (`mimamsa_insight_units` +
--    `mimamsa_insight_embeddings`). per_chart. THE L5 READ FACE.
--
-- INVARIANTS: per chart -- insight_id distinct; insight_type and evidence_grade
--   in closed vocabularies; PER-TYPE COVERAGE AGAINST EVERY UPSTREAM SOURCE,
--   EXACTLY -- calibrated_outlook count = mimamsa_reliability count (writer reads
--   it unbounded, mi_darshana.py:211); emergent_law = mimamsa_discoveries where
--   class='emergent_law'; retrodiction = same for 'retrodiction' (:349,
--   unbounded); load_bearing = mimamsa_load_bearing count (:392, unbounded);
--   manifestation_grammar = least(20, grammar rows with evidence_grade IN
--   ('empirical','assignment_only')) -- the writer's own predicate + LIMIT 20 at
--   :263; verdict_object <= 40 (the bodha_pratijna LIMIT 40 at :436);
--   rank_consequence in [0,10]; provenance_chain non-null; confidence_band
--   bounded when present.
--   EMBEDDINGS -- insight_id distinct per chart, every embedding resolves to an
--   insight unit on the same chart, vector_dims(embedding) = 768,
--   embed_model_version non-blank.
--
-- REWRITE-FLOOR TEST: the five coverage identities catch THE L5 READ FACE
--   SILENTLY GOING OUT OF SYNC WITH THE LAYER BEHIND IT -- mi_pariksha mines 12
--   new discoveries and mi_darshana surfaces the old 71; a reliability stratum
--   is dropped and the calibrated outlook still narrates it. The count CHANGES
--   in both cases, so no volume floor sees a problem; only the cross-table
--   identity does. This is the highest-leverage check in the set, because
--   mimamsa_insight_units is the surface the native actually reads.
--
-- VACUITY CAVEAT -- HALF-VACUOUS. THIS SENTENCE MUST SHIP WITH THE CHECK:
--   "mimamsa_insight_embeddings holds 0 rows; the embeddings clause passes
--   vacuously, constrains any future embedding row, and attests nothing today.
--   The producer does not exist -- mi_darshana.py:715-741 logs
--   [EXTERNAL_COMPUTATION_REQUIRED] and writes nothing, and
--   _substep_insight_units DELETEs embeddings on every rebuild (:679-681), so
--   the table is zero after every build by construction."
--   The insight-units half is fully live on 150 rows and is NOT vacuous.
--   (The empty producer is correct B.10 conduct -- no fabricated vectors -- not a
--   defect to be fixed by inventing one.)
--
-- DROPPED:
--   * surface_formula_version = 'mi_darshana_v1.2' (HEAD): ALL 150 rows are
--     v1.0 (W1 L5-F-21) -- a version pin fails today. The right instrument for
--     that is the rebuild, not a gate.
--   * evidence_grade reproducing _discovery_evidence_grade per class: 51
--     'retrodiction' rows carry 'prior_only' while HEAD returns 'structural'
--     unconditionally -- would fail. Same root cause: the data predates the
--     merged F-143/F-147/F-148 fixes (2026-08-21/22) and the last successful
--     build (2026-08-12/13).
--   * verdict_object count = the chart's bodha_pratijna row count: the LIMIT 40
--     plus L2-side filtering makes the exact identity unverifiable from L5
--     alone. The bound `<= 40` is what can honestly be asserted.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1 FROM mimamsa_insight_units u
    GROUP BY u.chart_id
    HAVING count(DISTINCT u.insight_id) <> count(*)
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = u.chart_id)) > 0
        OR count(*) FILTER (WHERE u.insight_type NOT IN
              ('calibrated_outlook','manifestation_grammar','emergent_law',
               'retrodiction','load_bearing','verdict_object')) > 0
        OR count(*) FILTER (WHERE u.evidence_grade NOT IN ('empirical','prior_only','structural')) > 0
        OR count(*) FILTER (WHERE u.insight_type = 'calibrated_outlook')
             <> (SELECT count(*) FROM mimamsa_reliability r WHERE r.chart_id = u.chart_id)
        OR count(*) FILTER (WHERE u.insight_type = 'emergent_law')
             <> (SELECT count(*) FROM mimamsa_discoveries d
                  WHERE d.chart_id = u.chart_id AND d.discovery_class = 'emergent_law')
        OR count(*) FILTER (WHERE u.insight_type = 'retrodiction')
             <> (SELECT count(*) FROM mimamsa_discoveries d
                  WHERE d.chart_id = u.chart_id AND d.discovery_class = 'retrodiction')
        OR count(*) FILTER (WHERE u.insight_type = 'load_bearing')
             <> (SELECT count(*) FROM mimamsa_load_bearing l WHERE l.chart_id = u.chart_id)
        OR count(*) FILTER (WHERE u.insight_type = 'manifestation_grammar')
             <> (SELECT least(20, count(*)) FROM mimamsa_manifestation_grammar g
                  WHERE g.chart_id = u.chart_id
                    AND g.evidence_grade IN ('empirical','assignment_only'))
        OR count(*) FILTER (WHERE u.insight_type = 'verdict_object') > 40
        OR count(*) FILTER (WHERE u.rank_consequence NOT BETWEEN 0 AND 10 OR u.n_support < 0) > 0
        OR count(*) FILTER (WHERE u.confidence_band IS NOT NULL
                              AND (isempty(u.confidence_band) OR lower(u.confidence_band) < 0
                                   OR upper(u.confidence_band) > 1)) > 0
        OR count(*) FILTER (WHERE u.provenance_chain IS NULL
                              OR btrim(coalesce(u.statement, '')) = ''
                              OR btrim(coalesce(u.leakage_status, '')) = ''
                              OR btrim(coalesce(u.freshness_lel_version, '')) = ''
                              OR btrim(coalesce(u.surface_formula_version, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM mimamsa_insight_embeddings e
    GROUP BY e.chart_id
    HAVING count(DISTINCT e.insight_id) <> count(*)
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_insight_units u2
                                               WHERE u2.chart_id = e.chart_id
                                                 AND u2.insight_id = e.insight_id)) > 0
        OR count(*) FILTER (WHERE vector_dims(e.embedding) <> 768
                              OR e.embedded_at IS NULL
                              OR btrim(coalesce(e.embed_model_version, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_darshana';


-- ────────────────────────────────────────────────────────────────────────────
-- 10. mi_abhilekha -- L5 journal re-sync service; declared owner of
--     `mimamsa_journal`. per_chart (service).
--
-- INVARIANTS: per chart -- journal_id distinct; chart_id resolves; every
--   prediction_id resolves to a mimamsa_predictions row ON THE SAME CHART;
--   answered_at IS NOT NULL IFF native_answer IS NOT NULL; resulting_event_id IS
--   NOT NULL => the entry is answered AND the id resolves to
--   life_events.event_id on the same chart; answered_at >= created_at;
--   prompt_shown / provenance_tag / journal_id non-blank.
--
-- REWRITE-FLOOR TEST: mimamsa_journal has NO FOREIGN KEYS AT ALL -- migration
--   354_mimamsa_seva_abhilekha.sql:17-27 declares only a PRIMARY KEY. Every
--   referential guarantee here is therefore one the schema does not provide.
--   Once the append path exists, this catches a journal entry answering a
--   prediction that no longer exists after an mi_bhavisya rebuild -- i.e. AN
--   OUTCOME ATTRIBUTED TO NOTHING, which is precisely the provenance loss the L5
--   mandate forbids. The `answered_at IFF native_answer` bi-conditional catches a
--   half-written answer (a timestamp with no content, or content with no time),
--   which is the state mi_abhilekha's free-text verdict heuristic
--   (mi_abhilekha.py:66-67, `"confirmed" if "yes" in answer ... else "denied"`)
--   would silently map to 'denied'.
--
-- VACUITY CAVEAT -- FULLY VACUOUS. THIS SENTENCE MUST SHIP WITH THE CHECK:
--   "mimamsa_journal holds 0 rows; this check passes vacuously, constrains every
--   future journal entry, and attests nothing today. The table is empty because
--   NO APPEND PATH EXISTS ANYWHERE IN THE REPO (W1 L5-F-01: zero
--   `INSERT INTO mimamsa_journal`; mi_seva.py:29's pointer to
--   services/mi_seva/handler.py targets a nonexistent file), not because a live
--   producer is idle."
--
-- DROPPED: anything asserting the journal is POPULATED, or that mi_abhilekha's
--   drain has run -- both are volume claims about a documented-deferred seam, and
--   both would fail. provenance_tag closed vocabulary: no vocabulary exists to
--   read; non-blankness only.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1 FROM mimamsa_journal j
  GROUP BY j.chart_id
  HAVING count(DISTINCT j.journal_id) <> count(*)
      OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = j.chart_id)) > 0
      OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM mimamsa_predictions p
                                             WHERE p.chart_id = j.chart_id
                                               AND p.prediction_id = j.prediction_id)) > 0
      OR count(*) FILTER (WHERE (j.answered_at IS NOT NULL) <> (j.native_answer IS NOT NULL)) > 0
      OR count(*) FILTER (WHERE j.resulting_event_id IS NOT NULL
                            AND (j.answered_at IS NULL
                                 OR NOT EXISTS (SELECT 1 FROM life_events e
                                                 WHERE e.chart_id = j.chart_id
                                                   AND e.event_id = j.resulting_event_id))) > 0
      OR count(*) FILTER (WHERE j.answered_at IS NOT NULL AND j.answered_at < j.created_at) > 0
      OR count(*) FILTER (WHERE btrim(coalesce(j.prompt_shown, '')) = ''
                            OR btrim(coalesce(j.provenance_tag, '')) = ''
                            OR btrim(coalesce(j.journal_id, '')) = ''
                            OR j.created_at IS NULL) > 0
)
$check$
 WHERE asset_id = 'mi_abhilekha';


-- ────────────────────────────────────────────────────────────────────────────
-- 11. mi_seva -- declared serve-time contribution-control gateway
--     (`mimamsa_preferences`). Registered per_chart (service).
--
-- SHAPE NOTE -- REGISTRY-SCOPE MISMATCH, RECORDED DELIBERATELY. The asset is
--   registered `per_chart`, but `mimamsa_preferences` HAS NO chart_id COLUMN AT
--   ALL: its full schema is (user_id, channel_id, saved_state, updated_at) with
--   PRIMARY KEY (user_id, channel_id) -- migration 354:6-12. It is per-USER UI
--   state, not per-chart data. D-CND-03's chart-partitioned
--   `GROUP BY chart_id` shape is therefore STRUCTURALLY INAPPLICABLE here, and a
--   whole-table invariant is the only correct shape. This is why the statement
--   below does not follow the per_chart pattern. Either the registry scope
--   should be corrected to reflect the table, or this deviation should be
--   recorded as an accepted disposition.
--
-- INVARIANTS: whole-table -- (user_id, channel_id) distinct;
--   user_id / channel_id / saved_state non-blank; updated_at non-null and NOT IN
--   THE FUTURE.
--
-- REWRITE-FLOOR TEST -- AND AN HONEST ADMISSION: this is the THINNEST check in
--   the set and that is on the record deliberately. The `updated_at > now()`
--   clause catches a clock or backfill corruption that would make a preference
--   row win every last-write-wins resolution FOREVER -- a real, count-invisible
--   failure. The blank-saved_state clause catches a write path storing an empty
--   toggle state, which the (as yet unwritten) learning_influence gate would
--   read as an unset default rather than an explicit choice. Beyond that there
--   is genuinely little to assert against a four-column, constraint-free
--   preference store, and clauses were NOT manufactured to pad it.
--
-- VACUITY CAVEAT -- FULLY VACUOUS. THIS SENTENCE MUST SHIP WITH THE CHECK:
--   "mimamsa_preferences holds 0 rows; this check passes vacuously, constrains
--   any future preference row, and attests nothing today. The table is empty
--   because the mi_seva service does not exist -- platform/python-sidecar/
--   services/mi_seva/ is absent, the writer only loops
--   information_schema.tables, and grep for learning_influence / saved_state /
--   contribution_state across platform/src + platform-mcp/src returns zero
--   non-generated hits (W1 Batch D)."
--
-- DROPPED:
--   * saved_state closed vocabulary: the spec
--     (00_ARCHITECTURE/L5_SPECS/10_mi_seva_and_mi_abhilekha_SPEC_v1_0.md
--     §A1-A4) names a learning_influence toggle but never enumerates
--     saved_state's values. Inventing them is forbidden.
--   * channel_id resolving to a channel registry: no channel registry table
--     exists. mimamsa_manifestation_sets.channel_id is a PREDICTION channel
--     vocabulary and there is no basis to assume a user preference is confined
--     to it.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1 FROM mimamsa_preferences p
   WHERE btrim(coalesce(p.user_id, '')) = ''
      OR btrim(coalesce(p.channel_id, '')) = ''
      OR btrim(coalesce(p.saved_state, '')) = ''
      OR p.updated_at IS NULL
      OR p.updated_at > now()
)
AND (SELECT count(DISTINCT (user_id, channel_id)) = count(*) FROM mimamsa_preferences)
$check$
 WHERE asset_id = 'mi_seva';


-- ────────────────────────────────────────────────────────────────────────────
-- 12. mi_sankalpa -- unified intervention ledger
--     (`mimamsa_intervention_ledger`); the three-armed study of election itself.
--     per_chart.
--
-- INVARIANTS: per chart -- intervention_id distinct; chart_id resolves;
--   elected_window non-null, NON-EMPTY and bounded on both sides (the writer
--   carries a scar from start==end producing an EMPTY tstzrange --
--   writers/mi_sankalpa.py:207-210); outcome_event_id IS NOT NULL IFF
--   outcome_linked_at IS NOT NULL; performed IS NOT NULL => performed_attested_by
--   present; study_arm='elected_pending' => performed IS NULL;
--   study_arm='elected_not_acted' => performed IS FALSE;
--   study_arm='acted_with_election' => performed IS TRUE AND performed_at within
--   [lower(window), upper(window)]; performed IS NULL => outcome_event_id IS
--   NULL; performed IS FALSE => performed_at IS NULL; adjudication/score payloads
--   non-null and version fields non-blank.
--
-- REWRITE-FLOOR TEST: the study-arm implications ARE the integrity of the
--   three-armed study. They catch AN INTERVENTION FILED INTO
--   'acted_with_election' WHOSE ATTESTED PERFORMANCE FELL OUTSIDE ITS OWN
--   ELECTED WINDOW -- the single mis-filing that would make an election look
--   efficacious when the native acted at a different time. The arm counts stay
--   the same; the causal claim inverts. The `outcome_event_id IFF
--   outcome_linked_at` bi-conditional catches a half-completed LEL match (an
--   outcome attached with no record of when, or a link timestamp pointing at
--   nothing). `NOT isempty(elected_window)` catches the writer's own known
--   start==end hazard, which silently produces a window no performed_at can ever
--   fall inside.
--
-- VACUITY CAVEAT -- FULLY VACUOUS. THIS SENTENCE MUST SHIP WITH THE CHECK:
--   "mimamsa_intervention_ledger holds 0 rows; this check passes vacuously,
--   constrains every future intervention, and attests nothing today. mi_sankalpa
--   is the P7 substrate with no filed interventions yet -- a correctly terminal
--   0-row state, not a failure."
--
-- DROPPED / DELIBERATELY ASYMMETRIC -- READ BEFORE ADDING THE "MISSING" HALF:
--   * W1 L5-F-D19 proposed backward implications FROM study_arm, which are kept.
--     The FORWARD implications (performed IS TRUE => arm='acted_with_election')
--     were deliberately NOT added, because
--     services/mi_sankalpa/arms.py::classify_study_arm RETURNS None for
--     `performed IS TRUE` with a missing or out-of-window performed_at, leaving
--     the row's arm UNCHANGED -- its own LAW ZERO comment says it must never
--     invent a disposition the design never named. A forward implication would
--     red-flag the writer's intentional, documented refusal. The asymmetry is a
--     recorded decision, not an oversight.
--   * study_arm='acted_without_election' rules: arm 4 is ORIGINATED, never
--     reclassified (arms.py:49-52), and its relationship to elected_window is
--     not stated anywhere readable. No clause invented.
--   * The window-membership test uses `performed_at >= lower(...) AND <=
--     upper(...)` rather than `<@ elected_window` ON PURPOSE: classify_study_arm
--     uses INCLUSIVE bounds while the tstzrange is '[)', so `<@` would falsely
--     fail a row attested exactly at the upper bound. The check matches the CODE,
--     not the range operator.
--   * Vocabulary and FK clauses (study_arm, efficacy_tier, precision_regime,
--     intervention_class, adoption_basis, outcome_event_id -> life_events(id),
--     event_class -> brahma_event_ontology, and the natural-key UNIQUE) are
--     ALREADY ENFORCED BY REAL CHECK/FK CONSTRAINTS on the table, so restating
--     them adds nothing. This check deliberately covers only what the schema
--     does not.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1 FROM mimamsa_intervention_ledger l
  GROUP BY l.chart_id
  HAVING count(DISTINCT l.intervention_id) <> count(*)
      OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = l.chart_id)) > 0
      OR count(*) FILTER (WHERE l.elected_window IS NULL OR isempty(l.elected_window)
                            OR lower_inf(l.elected_window) OR upper_inf(l.elected_window)) > 0
      OR count(*) FILTER (WHERE (l.outcome_event_id IS NOT NULL) <> (l.outcome_linked_at IS NOT NULL)) > 0
      OR count(*) FILTER (WHERE l.performed IS NOT NULL
                            AND btrim(coalesce(l.performed_attested_by, '')) = '') > 0
      OR count(*) FILTER (WHERE l.study_arm = 'elected_pending' AND l.performed IS NOT NULL) > 0
      OR count(*) FILTER (WHERE l.study_arm = 'elected_not_acted' AND l.performed IS NOT FALSE) > 0
      OR count(*) FILTER (WHERE l.study_arm = 'acted_with_election'
                            AND NOT (l.performed IS TRUE
                                     AND l.performed_at IS NOT NULL
                                     AND l.performed_at >= lower(l.elected_window)
                                     AND l.performed_at <= upper(l.elected_window))) > 0
      OR count(*) FILTER (WHERE l.performed IS NULL AND l.outcome_event_id IS NOT NULL) > 0
      OR count(*) FILTER (WHERE l.performed IS FALSE AND l.performed_at IS NOT NULL) > 0
      OR count(*) FILTER (WHERE l.adjudication_record IS NULL OR l.score_vector IS NULL
                            OR btrim(coalesce(l.precision_basis, '')) = ''
                            OR btrim(coalesce(l.paddhati_version, '')) = ''
                            OR btrim(coalesce(l.predicted_differential, '')) = ''
                            OR btrim(coalesce(l.filed_by, '')) = ''
                            OR btrim(coalesce(l.engine_version, '')) = ''
                            OR l.created_at IS NULL) > 0
)
$check$
 WHERE asset_id = 'mi_sankalpa';


-- ────────────────────────────────────────────────────────────────────────────
-- 13. mi_bhara -- Stage 9 of the temporal-field pipeline: fits field weights
--     against the LEL, publishes skill + goodness-of-fit (`kala_field_skill` +
--     `kala_field_gof`). per_chart.
--
-- SHAPE NOTE -- DOCUMENTED REFINEMENT OF D-CND-03. The second NOT EXISTS below
--   groups by (chart_id, weights_version, field_snapshot_id) rather than
--   chart_id alone. This is a REFINEMENT of the D-CND-03 shape, not a departure:
--   it takes no bind placeholders, quantifies over every chart, and still
--   attributes any violation to a specific chart. Grouping by chart alone would
--   SUM ACROSS WEIGHT-VERSION GENERATIONS and give a FALSE PASS the moment a
--   second weights_version or field snapshot exists -- the aggregate identity
--   would balance across two fits that are each individually wrong.
--
-- INVARIANTS: SKILL -- per chart, (event_class, weights_version,
--   field_snapshot_id) distinct; every weights_version resolves to a
--   kala_field_weight_versions.version_id; field_snapshot_id='unpinned' IS USED
--   ONLY WHERE IT IS HONEST -- never while a non-null kala_field.field_snapshot_id
--   exists for that chart; n_events = n_prospective + n_backfill; skill_lo <=
--   skill_score <= skill_hi; bootstrap parameters present and positive.
--   AGGREGATE CLOSURE -- per (chart, weights_version, snapshot), at most one
--   event_class IS NULL row, and its n_events EQUALS the sum of the per-class
--   rows'.
--   GOF -- (event_class, weights_version, snapshot) distinct; weights version
--   resolves; gof.n equals the paired skill row's n_events; ks_band_95 =
--   1.36 / sqrt(n) (derived-value reproducibility); p-values in [0,1].
--
-- REWRITE-FLOOR TEST: `n_events = n_prospective + n_backfill` and the
--   aggregate-sum clause catch A SKILL SCORE PUBLISHED OVER A DIFFERENT EVENT
--   SET THAN THE ONE IT REPORTS -- e.g. a prospective/backfill reclassification
--   that changes what "skill" MEANS while the row count stays at 7.
--   `ks_band_95 = 1.36/sqrt(n)` catches a GoF band computed against a different
--   n than the one stored beside it: a KS test whose critical value no longer
--   matches its sample. `gof.n = skill.n_events` catches the two halves of the
--   same fit straddling different runs.
--
-- NOT VACUOUS: 7 skill rows (6 per-class + 1 aggregate; aggregate n_events 7 =
--   1+1+1+2+1+1) + 6 GoF rows; ks_band_95 reproduces on 6/6.
--
-- DROPPED -- AND THIS ONE PRODUCED A LIVE FINDING (see KNOWN GAPS #2):
--   * field_snapshot_id RESOLVING INTO kala_field for the same chart -- DROPPED,
--     IT FAILS TODAY ON ALL 13 ROWS (7 skill + 6 GoF). Both tables carry
--     kfs_87484404af9d6fe9dc66a3d78812f8bc, while kala_field for 482012f1
--     carries kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb (and 1c826d5a carries
--     kfs_b3bcf77a5a4c3ce5296254bac3809451). The published skill and
--     goodness-of-fit are pinned to a field snapshot that NO LONGER EXISTS in
--     kala_field for that chart -- exactly the straddled-build hazard W1 L5-F-26
--     named (the weights.py sub-rule-5 risk), live in production. The
--     'unpinned'-sentinel HALF of W1's proposal IS shipped and green; the
--     membership half cannot be until the fit is re-run or re-pinned.
--   * gof_state / skill_state vocabulary: only 'underpowered' exists live and
--     the other states are not enumerated anywhere readable.
--   * failing_statistic IS NOT NULL => gof_state is a failure state:
--     failing_statistic is NULL on all 6 rows, so the implication has no live
--     instance to validate against -- it would be an untested clause wearing a
--     tested one's clothes (§N.8).
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  NOT EXISTS (
    SELECT 1 FROM kala_field_skill s
    GROUP BY s.chart_id
    HAVING count(DISTINCT (s.event_class, s.weights_version, s.field_snapshot_id)) <> count(*)
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM kala_field_weight_versions v
                                               WHERE v.version_id = s.weights_version)) > 0
        OR count(*) FILTER (WHERE s.field_snapshot_id = 'unpinned'
                              AND EXISTS (SELECT 1 FROM kala_field f
                                           WHERE f.chart_id = s.chart_id
                                             AND f.field_snapshot_id IS NOT NULL)) > 0
        OR count(*) FILTER (WHERE s.n_events <> s.n_prospective + s.n_backfill
                              OR s.n_prospective < 0 OR s.n_backfill < 0) > 0
        OR count(*) FILTER (WHERE s.skill_lo > s.skill_score OR s.skill_score > s.skill_hi) > 0
        OR count(*) FILTER (WHERE s.null_replicates < 1 OR s.bootstrap_resamples < 1
                              OR s.bootstrap_seed IS NULL OR s.released_at IS NULL
                              OR btrim(coalesce(s.skill_state, '')) = ''
                              OR btrim(coalesce(s.field_snapshot_id, '')) = '') > 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_skill s
    GROUP BY s.chart_id, s.weights_version, s.field_snapshot_id
    HAVING count(*) FILTER (WHERE s.event_class IS NULL) > 1
        OR (count(*) FILTER (WHERE s.event_class IS NULL) = 1
            AND sum(s.n_events) FILTER (WHERE s.event_class IS NULL)
                <> coalesce(sum(s.n_events) FILTER (WHERE s.event_class IS NOT NULL), 0))
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_gof g
    GROUP BY g.chart_id
    HAVING count(DISTINCT (g.event_class, g.weights_version, g.field_snapshot_id)) <> count(*)
        OR count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM kala_field_weight_versions v
                                               WHERE v.version_id = g.weights_version)) > 0
        OR count(*) FILTER (WHERE g.n IS DISTINCT FROM
              (SELECT s2.n_events FROM kala_field_skill s2
                WHERE s2.chart_id = g.chart_id
                  AND s2.event_class IS NOT DISTINCT FROM g.event_class
                  AND s2.weights_version = g.weights_version
                  AND s2.field_snapshot_id = g.field_snapshot_id)) > 0
        OR count(*) FILTER (WHERE g.n < 1
                              OR g.ks_band_95 IS DISTINCT FROM 1.36 / sqrt(g.n)
                              OR (g.ks_p IS NOT NULL AND g.ks_p NOT BETWEEN 0 AND 1)
                              OR (g.ks_statistic IS NOT NULL AND g.ks_statistic < 0)
                              OR (g.ljung_box_p IS NOT NULL AND g.ljung_box_p NOT BETWEEN 0 AND 1)
                              OR g.computed_at IS NULL
                              OR btrim(coalesce(g.gof_state, '')) = ''
                              OR btrim(coalesce(g.field_snapshot_id, '')) = '') > 0
  )
$check$
 WHERE asset_id = 'mi_bhara';


-- ────────────────────────────────────────────────────────────────────────────
-- 14. mi_kula -- GLOBAL signal-family registry (`mimamsa_signal_families`) +
--     the negative-control battery (`mimamsa_negative_controls`). scope=global,
--     so a whole-table invariant is the correct D-CND-03 shape.
--
-- INVARIANTS: whole-table -- family_id distinct; family_class in {classical,
--   negative_control}; negative_control => prior_weight = 0 AND
--   default_state='CONTROL_ONLY' AND evidence_tier='NEGATIVE_CONTROL', and
--   conversely classical => prior_weight > 0 AND default_state <>
--   'CONTROL_ONLY'; citation_refs / binding_spec non-null and display_name /
--   soundness_basis / calibration_status / formula_version non-blank;
--   prior_weight REPRODUCES brahma_class_priors.class_prior for all 9 mapped
--   families, using the writer's own _FAMILY_TO_PRIOR_KEY
--   (mi_kula.py:30-40) transcribed inline as the prior_map CTE.
--   NEGATIVE-CONTROL BATTERY -- control_id distinct; tolerance > 0;
--   expected_score / known_false_basis non-blank; (last_harness_score IS NULL) =
--   (last_harness_status IS NULL).
--
-- REWRITE-FLOOR TEST: the prior-reproduction clause is the DIRECT detector for
--   W1 L5-F-04's named blind spot. mi_kula.py:71-77 wraps its
--   brahma_class_priors lookup in a bare `except` that DEGRADES SILENTLY TO THE
--   MODULE'S HARDCODED CATALOG DEFAULTS with only a logger.warning. If that path
--   fires, fam_graha_natal.prior_weight becomes 1.0 instead of the registry's
--   1.1 -- and because mi_gunanaka sets applied_multiplier = prior_weight for
--   every unpromoted family, and mi_adhilepa then stamps that figure onto
--   224,742 overlay rows, A SWALLOWED EXCEPTION SILENTLY RE-WEIGHTS THE ENTIRE
--   SERVED INSTRUMENT. The row count stays 11 through all of it. The
--   negative-control bi-conditional catches a harness STATUS appearing without a
--   SCORE -- a control battery reporting a verdict nothing measured (§N.8).
--
-- COUPLING NOTE: transcribing _FAMILY_TO_PRIOR_KEY into the check is not
--   invention -- it is the writer's own constant. It means ANY EDIT TO THAT MAP
--   MUST BE MIRRORED HERE OR THIS CHECK GOES RED. That is the correct coupling
--   for a value the whole layer multiplies by. `data_source_pin` is NULL on all
--   11 rows, so no DB-side family->prior link exists to join to instead.
--
-- NOT VACUOUS: 11 families (all 9 mapped prior_weights reproduce class_prior
--   exactly) + 4 negative controls.
--
-- DROPPED:
--   * apply_point non-null: NULL 11/11 (W1 L5-F-05a) -- would fail.
--   * interaction_value / interaction_status populated: NULL 11/11 -- same.
UPDATE asset_registry
   SET integrity_check_sql = $check$
WITH prior_map(family_id, stc, sub) AS (VALUES
    ('fam_graha_natal','position','*'),
    ('fam_dasha_period','dasha_period','*'),
    ('fam_yoga','yoga','*'),
    ('fam_divisional','varga_pattern','*'),
    ('fam_transit','time_window','*'),
    ('fam_convergence','composite_state','*'),
    ('fam_ashtakavarga','*','strength_ashtakavarga'),
    ('fam_msr_signal','configuration','*'),
    ('fam_anchor','time_window','*'))
SELECT
      (SELECT count(DISTINCT family_id) = count(*) FROM mimamsa_signal_families)
  AND NOT EXISTS (
        SELECT 1 FROM mimamsa_signal_families f
         WHERE (f.family_class = 'negative_control'
                AND NOT (f.prior_weight = 0 AND f.default_state = 'CONTROL_ONLY'
                         AND f.evidence_tier = 'NEGATIVE_CONTROL'))
            OR (f.family_class <> 'negative_control'
                AND NOT (f.prior_weight > 0 AND f.default_state <> 'CONTROL_ONLY'))
            OR f.family_class NOT IN ('classical','negative_control')
            OR f.citation_refs IS NULL OR f.binding_spec IS NULL
            OR btrim(coalesce(f.display_name, '')) = ''
            OR btrim(coalesce(f.soundness_basis, '')) = ''
            OR btrim(coalesce(f.calibration_status, '')) = ''
            OR btrim(coalesce(f.formula_version, '')) = '')
  AND NOT EXISTS (
        SELECT 1 FROM prior_map m
         WHERE NOT EXISTS (
           SELECT 1 FROM mimamsa_signal_families f
             JOIN brahma_class_priors p
               ON p.prior_version = '1.0' AND p.signal_tradition = '*' AND p.fact_kind = '*'
              AND p.signal_type_class = m.stc AND p.source_subsystem = m.sub
            WHERE f.family_id = m.family_id AND f.prior_weight = p.class_prior))
  AND NOT EXISTS (
        SELECT 1 FROM mimamsa_negative_controls c
         WHERE c.tolerance IS NULL OR c.tolerance <= 0
            OR btrim(coalesce(c.expected_score, '')) = ''
            OR btrim(coalesce(c.known_false_basis, '')) = ''
            OR c.citation_refs IS NULL OR c.binding_spec IS NULL
            OR btrim(coalesce(c.formula_version, '')) = ''
            OR (c.last_harness_score IS NULL) <> (c.last_harness_status IS NULL))
  AND (SELECT count(DISTINCT control_id) = count(*) FROM mimamsa_negative_controls)
$check$
 WHERE asset_id = 'mi_kula';


-- ────────────────────────────────────────────────────────────────────────────
-- 15. mi_vistara -- GLOBAL append-only export-integrity ledger
--     (`mimamsa_export_log`); the audit boundary for what LEAVES the instrument.
--     scope=global, so a whole-table invariant is the correct D-CND-03 shape.
--
-- INVARIANTS: whole-table -- THE DISCLOSURE-PRESENT GATE:
--   calibration_mode='empirical' implies a NON-EMPTY disclosures_attached;
--   closed vocabularies for calibration_mode and export_format (both transcribed
--   from 00_ARCHITECTURE/L5_SPECS/11_mi_vistara_SPEC_v1_0.md:42,46);
--   disclosures_attached / contribution_state / included_insight_ids non-null and
--   the last is a JSON array; payload_hash / lel_version /
--   export_formula_version non-blank; exported_at non-null; chart_id resolves to
--   `charts`; export_id distinct; every id in included_insight_ids resolves to a
--   mimamsa_insight_units row ON THE SAME CHART.
--
-- REWRITE-FLOOR TEST: the disclosure gate is THE ETHICAL BOUNDARY OF THE WHOLE
--   INSTRUMENT -- it catches an empirical calibration claim leaving the system
--   WITHOUT its n / confidence / leakage disclosure attached (spec §3.5.G). A row
--   count cannot distinguish a disclosed export from an undisclosed one: both are
--   one row. The included_insight_ids closure (an addition beyond W1's spec §6
--   version) catches an export manifest citing insight ids that no longer exist
--   after a mi_darshana rebuild -- an audit ledger that can no longer reconstruct
--   what it says it exported, which defeats the ledger's only purpose.
--   payload_hash non-blank catches an export logged without the hash that makes
--   it verifiable at all.
--
-- VACUITY CAVEAT -- FULLY VACUOUS. THIS SENTENCE MUST SHIP WITH THE CHECK:
--   "mimamsa_export_log holds 0 rows; this check passes vacuously, constrains
--   every future export, and attests nothing today. Zero rows is mi_vistara's
--   correctly terminal state -- asset_runner.py:1026-1032's
--   zero_rows_is_complete is satisfied on BOTH limbs (chart_id IS NULL and
--   target_floor = 0), so the 'lit' promotion is EARNED, not assumed."
--
-- DROPPED:
--   * recipient_ref non-null: nullable by design -- an export may have no named
--     recipient.
--   * Any assertion that exports HAVE OCCURRED: that is a volume claim about an
--     event-driven ledger, and it would fail.
UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT NOT EXISTS (
  SELECT 1 FROM mimamsa_export_log e
   WHERE e.calibration_mode NOT IN ('empirical','prior_only','structural_prior_only')
      OR e.export_format NOT IN ('pdf','json','mcp_bundle','portal_view')
      OR (e.calibration_mode = 'empirical'
          AND (e.disclosures_attached IS NULL
               OR e.disclosures_attached IN ('{}'::jsonb, '[]'::jsonb, 'null'::jsonb)))
      OR e.disclosures_attached IS NULL
      OR e.contribution_state IS NULL
      OR e.included_insight_ids IS NULL
      OR jsonb_typeof(e.included_insight_ids) <> 'array'
      OR btrim(coalesce(e.payload_hash, '')) = ''
      OR btrim(coalesce(e.lel_version, '')) = ''
      OR btrim(coalesce(e.export_formula_version, '')) = ''
      OR e.exported_at IS NULL
      OR NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = e.chart_id)
      OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(e.included_insight_ids) AS t(iid)
                  WHERE NOT EXISTS (SELECT 1 FROM mimamsa_insight_units u
                                     WHERE u.chart_id = e.chart_id AND u.insight_id = t.iid))
)
AND (SELECT count(DISTINCT export_id) = count(*) FROM mimamsa_export_log)
$check$
 WHERE asset_id = 'mi_vistara';


-- ════════════════════════════════════════════════════════════════════════════
-- KNOWN GAPS
-- ════════════════════════════════════════════════════════════════════════════
-- Four invariants that SHOULD hold are violated by live production data as of
-- 2026-09-05 and were therefore NOT shipped as clauses. A gate that starts red
-- is a broken gate, not a detector (C12). These are recorded here so the gaps
-- are known and deliberate, not oversights. DO NOT add the missing clauses
-- without first fixing the underlying defect -- doing so turns the build red and
-- fixes nothing.
--
-- GAP 1 -- mi_pramana: reliability binning is not reproducible from its own
--   calibration rows. WRITER FIXED ON THIS BRANCH; DATA STILL STALE.
--   Evidence (live 2026-09-05): strata 'domain_all|[0.5,0.6)' and
--   'domain_all|[0.6,0.7)' store n = 18 and 7; recomputing from
--   mimamsa_calibration by `composite_score >= lower(bin) AND < upper(bin)`
--   yields 17 and 8. The offending row is composite_score = 0.6 EXACTLY
--   (match_id pred_c0fa3e1e-68e5-4987-9cf3-cfd899040a4a_
--    56a1222d-8c88-5445-b2a2-1fd89d470719-corr-2021-04, verdict PARTIAL), filed
--   into a bin that excludes its own value.
--   Root cause: mi_pramana.py binned with `math.floor(score / bin_size)`, which
--   is wrong in IEEE-754 at every exact tenth whose quotient falls just under the
--   integer (0.6/0.1 -> 5.999999999999999; 0.7/0.1 -> 6.999999999999999;
--   0.3/0.1 -> 2.9999999999999996). CLAUDE.md §N.7 item 1 -- a derived value not
--   reproducible from its source.
--   STATUS: the writer is ALREADY FIXED at this branch's HEAD -- commit
--   14f8c0c94, "L5-W3: fix reliability-bin off-by-one at every exact tenth
--   (A-F-34)", which replaces the float floor with a Decimal bin index. That
--   fix's own analysis establishes the defect class is BROADER than this
--   verification first reported: 0.3 and 0.7 are affected too, not only 0.6.
--   Only 0.6 currently occurs in live data (verified: exactly 1 such row; no row
--   holds 0.1-0.5 or 0.7-0.9 exactly), which is why the observed damage is two
--   strata and one row.
--   The DATA remains stale until mi_pramana is re-run; that is why the clause is
--   still not shipped here. RE-ADD per-bin n and observed_rate reproducibility to
--   asset 4's check once the rebuild has landed.
--   Un-gated meanwhile: per-bin n and observed_rate reproducibility. Still
--   gated: sum(n) per chart = calibration count, bin non-overlap, and the n>=5
--   grade thresholds.
--
-- GAP 2 -- mi_bhara: published skill and goodness-of-fit are pinned to a field
--   snapshot that no longer exists.
--   Evidence: all 13 rows (7 kala_field_skill + 6 kala_field_gof) carry
--   field_snapshot_id = 'kfs_87484404af9d6fe9dc66a3d78812f8bc'; kala_field for
--   chart 482012f1-710e-4a25-994a-93821f5871aa carries
--   'kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb', and for
--   1c826d5a-41cb-4450-b4dc-59d440e5f75a carries
--   'kfs_b3bcf77a5a4c3ce5296254bac3809451'. This is the straddled-build hazard
--   W1 L5-F-26 named (the weights.py sub-rule-5 risk), live in production.
--   Un-gated: field_snapshot_id membership in kala_field. Still gated: the
--   'unpinned'-sentinel honesty clause, weights_version referential closure, the
--   n_events decomposition, the aggregate sum, gof.n = skill.n_events, and
--   ks_band_95 = 1.36/sqrt(n).
--
-- GAP 3 -- mi_sambandha: three confirmed defects in the live grammar table
--   (all 47 rows are grammar_formula_version='mi_sambandha_v1.0'; HEAD is v1.2,
--   PR #1439 / commit 44f42fe94, merged 2026-08-21 AFTER the last successful L5
--   build on 2026-08-12/13; the 2026-08-21 rebuild was BLOCKED).
--   3a. evidence_grade='empirical' with scored_count = 0 on 10 rows, all 10
--       carrying a non-NULL channel_propensity -- an unearned grade with nothing
--       measured behind it (W1 L5-F-14, §N.8).
--   3b. n_support <> scored_count on 13 rows -- n_support is not the count it is
--       named for.
--   3c. 34 rows (17 per chart) whose channel_id cannot exist in
--       mimamsa_manifestation_sets: _PRIOR_PROPENSITIES (mi_sambandha.py:90-99)
--       declares 20 channels while mi_bhavisya emits exactly 7, all
--       ch_<domain>_verbal (W1 L5-F-13).
--   Un-gated: the empirical=>scored, n_support=scored_count, and unconditional
--   channel-closure clauses. Still gated: the opportunity/propensity honest-null
--   bi-conditional, both derived-value reproductions, and channel closure
--   NARROWED to opportunity_count > 0.
--
-- GAP 4 -- mi_seva: registry-scope mismatch.
--   The asset is registered scope='per_chart', but `mimamsa_preferences` has no
--   chart_id column at all (user_id, channel_id, saved_state, updated_at;
--   migration 354:6-12). D-CND-03's chart-partitioned shape is structurally
--   inapplicable, which is why asset 11's check is whole-table. Either correct
--   the registry scope to match the table, or record the deviation as an
--   accepted disposition.
--
-- ────────────────────────────────────────────────────────────────────────────
-- Forward reversal (safe at any time -- these are additive value corrections on
-- a metadata column, not schema changes): re-run with integrity_check_sql reset
-- to NULL for the 15 asset_ids above.
