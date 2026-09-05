-- 670_nirmana_l3_w3_integrity_contracts.sql
--
-- NIRMĀṆA L3 Kāla — W3 IMPLEMENT. Discharges W2 findings M2 (19 integrity contracts),
-- M6 (ka_gochara count_sql), N8 (volume expectations + floors) and N9 (stale DRAFT labels).
--
-- Standard: D-CND-03 (Conductor ruling on #1723/#1727) — chart-partitioned, attribution-preserving
-- invariants in preference to whole-table aggregates, because a corruption confined to one chart
-- can be numerically swamped in a whole-table aggregate and missed. C12/D-126: no bare count(*)=N
-- equality pins; a count may appear only as a conjunct of something that can fail on corruption a
-- count cannot see.
--
-- Every contract below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each conjunct was re-run against a corruption injected inside a CTE and shown to return false.
-- A conjunct that survived its mutation was rewritten, not shipped. Full per-asset evidence
-- (contract result, mutation table, volume derivation) is in the W3 record.
--
-- Also verified: all 19 pass nirmanaReadOnlyDetectorSqlAcceptable() and carry NO bind parameters —
-- the defect ruled on #1723, where every per-chart layer's count_sql is $1-bound and therefore
-- cannot serve as a detector.
--
-- FIVE OF THE NINETEEN RETURN FALSE TODAY. That is deliberate and is the point of the exercise:
-- they are true positives against real defects, and installing a contract that passes over known-
-- bad data would be the gate-weakening the hard floor forbids. The affected assets cannot reach
-- integrity_verified until the underlying data is corrected — which is the correct consequence.
--   ka_avadhi            lord_condition_fact_refs empty on 100% of rows (writer fixed in W3 M4;
--                        red until a rebuild lands) + 3,087 unresolvable pratijna ids
--   ka_yojaka            49,730 stale signal refs; 27,681 undatable predicates with no reason
--   ka_kalasutra         56 windows citing an L1 period that no longer contains them; 49,730
--                        predicates with zero activations
--   ka_gochara_v3_...    5 red conjuncts incl. pre-birth windows (writer fixed in W3 M5)
--   ka_bhavishya_lekha   all 100 projections share one peak_date — a degeneracy detector firing
--
-- FOUR OF THE FIVE localise to chart cb73cd3d, which L3 has shown is cascade-damaged (see the
-- disposition request filed alongside this migration). That localisation is exactly what
-- D-CND-03's chart-partitioning requirement exists to produce and what a whole-table aggregate
-- would have hidden.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.


-- ── 1. Integrity contracts (19) ──────────────────────────────────────────────


-- ka_avadhi  -- returns FALSE today: true positive, see header
UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_avadhi integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_avadhi. Its natural key (chart_id, system_id, level_n, period_start)
  -- is already a DB UNIQUE constraint, so no distinctness conjunct appears here (D-CND-03 item 4).
  -- (a) §N.5 L1-authority: kala_avadhi INHERITS its period spine from chart_dashas and must
  -- never restate it. Every served period must match an L1 row exactly on
  -- (system, level, start, end, lord) at the canonical ayanamsha. This is the machine form of
  -- the CR-110 double-dasha-spine defect: a boundary sourced from a NON-canonical ayanamsha,
  -- or a stale row surviving the writer's upsert, fails here.
  NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_dashas d
      WHERE d.chart_id     = a.chart_id
        AND d.ayanamsha_id = 'lahiri_chitrapaksha'
        AND d.system_id    = a.system_id
        AND d.level_n      = a.level_n
        AND d.start_date   = a.period_start
        AND d.end_date     = a.period_end
        AND d.lord_graha   = a.lord_graha
    )
  )
  -- (b) §N.5 coverage (the other direction): for every chart the asset has built, every
  -- canonical MD/AD period of the seven declared systems must be present. Detects a partial
  -- build, a dropped dasha system, or a chart-scoped truncation that (a) alone cannot see.
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas d
    WHERE d.ayanamsha_id = 'lahiri_chitrapaksha'
      AND d.level_n IN (1, 2)
      AND d.system_id = ANY (ARRAY['vimshottari','yogini','ashtottari',
                                   'chara','naisargika','mudda','kalachakra'])
      AND EXISTS (SELECT 1 FROM kala_avadhi k WHERE k.chart_id = d.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_avadhi a
        WHERE a.chart_id     = d.chart_id
          AND a.system_id    = d.system_id
          AND a.level_n      = d.level_n
          AND a.period_start = d.start_date
      )
  )
  -- (c) B.3 / §N.5 grounding function is live, not void. The asset's whole stated purpose is
  -- lord_condition_fact_refs. Every period whose lord is one of the nine grahas (the only
  -- lords chart_facts can describe -- chara/yogini lords are signs and yogini names) must
  -- carry at least one ref. This conjunct is RED today by design: the writer queries
  -- fact_subject='Sun' while L1 stores 'SUN', so the array is [] on 100.00% of rows
  -- (W2 M4). A contract that passed both before and after that fix would measure nothing.
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    WHERE a.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter',
                                    'Venus','Saturn','Rahu','Ketu'])
      AND jsonb_array_length(COALESCE(a.dossier->'lord_condition_fact_refs','[]'::jsonb)) = 0
  )
  -- (d) §N.5 refs must RESOLVE and must name their own lord. Every emitted fact ref must
  -- point at a real chart_facts row of the SAME chart, and its fact_subject must be the
  -- period's own lord (case-insensitive -- the exact axis the M4 defect sits on).
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    CROSS JOIN LATERAL jsonb_array_elements(
      COALESCE(a.dossier->'lord_condition_fact_refs','[]'::jsonb)) AS r
    WHERE upper(r->>'fact_subject') IS DISTINCT FROM upper(a.lord_graha)
       OR NOT EXISTS (
         SELECT 1 FROM chart_facts f
         WHERE f.chart_id = a.chart_id AND f.fact_id = r->>'fact_id')
  )
  -- (e) the second attribution array must resolve too: every activated_pratijna_id must be a
  -- real bodha_pratijna row of the same chart (B.3 -- no claim without a resolvable source).
  AND NOT EXISTS (
    SELECT 1 FROM kala_avadhi a
    CROSS JOIN LATERAL jsonb_array_elements_text(
      COALESCE(a.dossier->'activated_pratijna_ids','[]'::jsonb)) AS p
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_pratijna bp
      WHERE bp.chart_id = a.chart_id AND bp.pratijna_id::text = p)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_avadhi';


-- ka_bhavishya_lekha  -- returns FALSE today: true positive, see header
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_bhavishya_lekha integrity contract  (target table: kala_bhavishya)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
SELECT
  -- (a) §N.3 cross-build accretion detector. kala_bhavishya has ONLY a surrogate id PK and no
  -- natural-key UNIQUE. The writer emits one row per rank 1..n and one row per source
  -- kala_darshana window (ka_bhavishya_lekha.py:76-128), so both are natural keys and both
  -- are asserted -- either alone would miss half of an accretion pattern.
  NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    GROUP BY chart_id, projection_rank
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    GROUP BY chart_id, convergence_id
    HAVING count(*) > 1
  )
  -- (b) projection_rank is the artifact's serving order and its only addressable key, so it must
  -- be a dense 1..n per chart or a consumer paging the projections silently skips one.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    GROUP BY chart_id
    HAVING min(projection_rank) <> 1
        OR max(projection_rank) <> count(*)
        OR count(DISTINCT projection_rank) <> count(*)
  )
  -- (c) §N.5 upstream authority: a projection never restates a window value as its own truth
  -- -- peak_date / window_start / window_end / effective_score / signal_id are copied
  -- verbatim off the source kala_darshana row (:110-124). Pinned on (convergence_id,
  -- chart_id) because the FK nulls the reference on cascade and enforces neither chart agreement nor
  -- survival.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya b
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_darshana d
      WHERE d.convergence_id = b.convergence_id
        AND d.chart_id = b.chart_id
        AND d.peak_date IS NOT DISTINCT FROM b.peak_date
        AND d.window_start IS NOT DISTINCT FROM b.window_start
        AND d.window_end IS NOT DISTINCT FROM b.window_end
        AND d.effective_score IS NOT DISTINCT FROM b.effective_score
        AND d.signal_id IS NOT DISTINCT FROM b.signal_id
    )
  )
  -- (d) §N.7 item 1 + item 5: probability_tier is a restatement of (effective_score,
  -- net_label), not an independent judgment -- _assign_tier (:148-157). Re-derived in full,
  -- together with the writer's own intake filter (a severely obstructed window is excluded,
  -- :48), so a tier that drifts from the numbers it grades fails.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya b
    JOIN kala_darshana d
      ON d.convergence_id = b.convergence_id AND d.chart_id = b.chart_id
    WHERE d.net_label = 'obstructed_severe'
       OR b.probability_tier IS DISTINCT FROM (
            CASE
              WHEN b.effective_score IS NULL THEN 'tier_3_speculative'
              WHEN b.effective_score >= 0.70
                   AND d.net_label NOT IN ('obstructed','obstructed_severe','neutral')
                   THEN 'tier_1_high'
              WHEN b.effective_score >= 0.45 THEN 'tier_2_moderate'
              ELSE 'tier_3_speculative'
            END)
  )
  -- (e) §N.7 item 1: the falsifiability hook and the source chain are narration over this
  -- row's own facts. The hook must be evaluable on the date the row projects, must carry the
  -- +/-21 day window it names in prose, and the chain must point at the window the row was
  -- actually built from -- otherwise the L5 outcome loop scores a claim against the wrong day.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    WHERE (falsifiability->>'evaluation_date') IS DISTINCT FROM peak_date::text
       OR (falsifiability->>'evaluation_window_days')::int <> 21
       OR (source_chain->0->>'convergence_id') IS DISTINCT FROM convergence_id::text
  )
  -- (f) forward-only horizon: the writer selects peak_date between today and today+5y
  -- (:36-51). A projection dated before its own build, or beyond the horizon it claims, is a
  -- retrodiction wearing a projection's clothes. One day of slack covers the writer's
  -- date(year+5, month, day) construction across a leap day.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    WHERE peak_date IS NULL
       OR peak_date < computed_at::date
       OR peak_date > (computed_at::date + interval '5 years' + interval '1 day')
  )
  -- (g) DEGENERACY DETECTOR -- the direct F-BHAV-1 invariant (§N.6 item 3, B.10). Every row
  -- ships its own independently-falsifiable hook ("Observable within +/-21 days of <date>").
  -- A projection set whose rows all name ONE day is not N claims, it is one claim repeated N
  -- times: a single real-world observation would resolve all of them at once and any L5
  -- calibration statistic computed over them would be corrupt. A constant projection set
  -- carries no information, so requiring more than one distinct projected day wherever there
  -- is more than one projection is an information invariant, not a taste judgement.
  -- This conjunct currently FAILS on chart 482012f1 (100 projections, 1 distinct peak_date)
  -- and PASSES on 1c826d5a (100 projections, 2 distinct peak_dates) -- it is a genuinely
  -- two-valued detector on live data, and its red is a true positive. See the volume file.
  AND NOT EXISTS (
    SELECT 1 FROM kala_bhavishya
    GROUP BY chart_id
    HAVING count(*) > 1 AND count(DISTINCT peak_date) < 2
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_bhavishya_lekha';


-- ka_gochara
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_gochara integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
--
-- SCOPE — read this before changing anything. The `asset_registry` row for `ka_gochara` names
-- `kala_gochara_windows` as its target_table and counts generation '3.0' there — the WRITER does
-- neither. `pipeline/orchestrator/writers/ka_gochara.py` writes exclusively to
-- `kala_gochara_windows_v2` at generation '2.0', and the protected-table name does not appear
-- anywhere in that module (a statically-guarded absence). This contract is written for the asset
-- AS THE WRITER BEHAVES, so every conjunct that asserts content is scoped to
-- `kala_gochara_windows_v2` at generation '2.0'. The registry mismatch is a real defect and is
-- recorded in ka_gochara.volume.md — it is not encoded here as if it were true.
--
-- `kala_gochara_windows_v2` DOES carry a natural-key UNIQUE
-- (chart_id, event_class, window_start, peak_date, coalesce(milestone_id,''),
--  coalesce(resolution,''), generation) — measured on the live DB, contrary to the W3 brief's
-- "surrogate id only" listing — so a plain natural-key distinctness conjunct would be redundant
-- (D-CND-03 rule 4). The accretion detector this asset actually needs is (a)+(b) below: the
-- writer's replacement key is (chart_id, event_class, generation), which the UNIQUE cannot see.
SELECT
  -- (a) §N.3 attribution: every served row of this writer's generation must be covered by this
  -- writer's own bookkeeping for the same (chart, event_class, generation), with a real
  -- fingerprint behind it. A row whose class was later removed from the resonance map survives
  -- the natural key but has no build-state parent, and shows up here.
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_v2_build_state b
        WHERE b.chart_id = w.chart_id AND b.event_class = w.event_class
          AND b.generation = '2.0' AND b.class_fingerprint IS NOT NULL
      )
  )
  -- (b) §N.4 cockpit truth / §N.8 earned signal: the build-state counter is not taken on trust —
  -- it must equal the rows actually present for that (chart, event_class, generation), and a
  -- class recorded as an honest skip must have written nothing. This is the exact defect class
  -- already observed on this asset's `asset_throughput` row (a stale counter presented as a
  -- build fact) — here it is made permanently checkable at the grain the writer owns.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_v2_build_state b
    WHERE b.generation = '2.0'
      AND ((SELECT count(*) FROM kala_gochara_windows_v2 w
            WHERE w.chart_id = b.chart_id AND w.event_class = b.event_class
              AND w.generation = '2.0') <> b.rows_written
        OR (b.skipped_reason IS NOT NULL AND b.rows_written <> 0))
  )
  -- (c) §N.5: a window may only exist for an event class this chart's resonance map declares.
  -- The targets are the upstream authority — a window for an undeclared class is ungrounded.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND NOT EXISTS (
        SELECT 1 FROM gochara_resonance_map g
        WHERE g.chart_id = w.chart_id AND g.event_class = w.event_class
      )
  )
  -- (d) window well-formedness for the generation this writer owns: the peak instant lies inside
  -- the window it is the peak OF. Deliberately scoped to generation '2.0' rather than applied
  -- table-wide, because 16 rows elsewhere in this family (15 in the v1 archive, 1 at generation
  -- '3.0', both other assets' output) violate containment today — a whole-family conjunct would
  -- make THIS asset's health signal red for another writer's defect, which is exactly the
  -- mis-attribution the registry already commits. The detector for those rows is handed to their
  -- owning assets in ka_gochara.volume.md.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0'
      AND (w.window_end < w.window_start
        OR w.peak_date < w.window_start
        OR w.peak_date > w.window_end)
  )
  -- (e) D-TIME horizon disclosure: every served row must lie inside the progressive horizon its
  -- own build-state discloses. A row outside it is an undisclosed claim about a span this build
  -- never scanned — and it is what a stale near-horizon cache looks like from the outside.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    JOIN kala_gochara_v2_build_state b
      ON b.chart_id = w.chart_id AND b.event_class = w.event_class AND b.generation = w.generation
    WHERE w.generation = '2.0'
      AND (w.window_start < b.horizon_start_date OR w.window_end > b.horizon_end_date)
  )
  -- (f) THE UNTOUCHABLE-DATA RAIL, asserted rather than assumed: this writer's generation must
  -- never appear in the protected `kala_gochara_windows` relation. The absence is enforced today
  -- by construction (the writer cannot name that table), and this conjunct is what would notice
  -- if that ever stopped being true.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows p WHERE p.generation = '2.0'
  )
  -- (g) §N.3 generation hygiene: this writer's replacement key is (chart, event_class,
  -- generation) and it never stamps an era slice, so an era-stamped row inside generation '2.0'
  -- came from a different writer sharing the table — the cross-generation contamination the
  -- shared `kala_gochara_windows_v2` relation makes possible.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = '2.0' AND w.era_slice_key IS NOT NULL
  )
  -- (h) HARD-FLOOR CORPUS PRESENCE (§N.4, and the writer's own module docstring point 3, which
  -- names the v1 corpus as this writer's frozen validation benchmark). For every chart this
  -- writer has materialized, the irreplaceable v1 corpus for that same chart must still be
  -- present in `kala_gochara_windows`, and must remain strictly larger than this writer's
  -- ±3-year near-horizon layer for that chart — v1 is a birth→+100y daily sweep, so a v1 group
  -- that has shrunk to the size of the near-horizon layer has lost rows that cannot be
  -- regenerated (the retired writer's registration was removed). This conjunct is the reason
  -- the contract can NEVER be satisfied by the corpus being emptied: emptying it makes the
  -- contract FALSE, per chart.
  AND NOT EXISTS (
    SELECT 1 FROM (SELECT DISTINCT chart_id FROM kala_gochara_windows_v2 WHERE generation = '2.0') c
    WHERE (SELECT count(*) FROM kala_gochara_windows p
           WHERE p.chart_id = c.chart_id AND p.generation = 'v1')
          <= (SELECT count(*) FROM kala_gochara_windows_v2 w
              WHERE w.chart_id = c.chart_id AND w.generation = '2.0')
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_gochara';


-- ka_gochara_resonance
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_gochara_resonance integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
SELECT
  -- (a) §N.7 honesty: the uncitedness flag must agree with the citation it describes.
  NOT EXISTS (
    SELECT 1 FROM gochara_resonance_map
    WHERE uncited_extension IS DISTINCT FROM (classical_citation IS NULL)
  )
  -- (b) §N.5 L0-authority: every event_class must resolve in the L0 ontology.
  AND NOT EXISTS (
    SELECT 1 FROM gochara_resonance_map m
    WHERE NOT EXISTS (
      SELECT 1 FROM brahma_event_ontology o WHERE o.event_class_id = m.event_class
    )
  )
  -- (c) §N.5: a mechanism_node's source_rule_id must resolve in bg_transit_rules.
  AND NOT EXISTS (
    SELECT 1 FROM gochara_resonance_map m
    WHERE m.target_type = 'mechanism_node'
      AND (m.source_rule_id IS NULL
           OR NOT EXISTS (SELECT 1 FROM bg_transit_rules t WHERE t.id = m.source_rule_id))
  )
  -- (d) the salience prior stays inside its declared range.
  AND NOT EXISTS (SELECT 1 FROM gochara_resonance_map WHERE weight IS NULL OR weight < -1 OR weight > 1)
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_gochara_resonance';


-- ka_gochara_sweep
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_gochara_sweep integrity contract (D-CND-03).
-- This asset is RETIRED and snapshot-only: its writer's @register was removed at retirement, so
-- the build system cannot regenerate these rows. The corpus is therefore irreplaceable, and the
-- only honest thing an integrity check can assert about it is THAT IT IS STILL ALL THERE.
-- Since migration 588 removed the protection triggers (by native instruction, replaced by a
-- logical dump), this check is the corpus's only in-database detector of loss.
SELECT
  -- (a) §N.5 / cross-table FULL-JOIN consistency: every row of the verified 2026-08-05 archive
  --     snapshot must still be present in the live table under generation='v1'. This is the real
  --     invariant — it detects deletion, generation re-labelling, and id churn alike, which no
  --     count could. Deliberately NOT a count: a count is satisfied by deleting one row and
  --     inserting another.
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_archive_20260805 a
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_gochara_windows w
      WHERE w.id = a.id AND w.generation = 'v1' AND w.chart_id = a.chart_id
    )
  )
  -- (b) the chart the archive does NOT cover still carries its corpus. Achieved-count floor per
  --     §N.4 (measured 2,667), not an equality pin: growth is impossible for a retired writer, so
  --     a floor detects exactly the failure that can happen — loss.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, count(*) AS n
      FROM kala_gochara_windows WHERE generation = 'v1'
      GROUP BY chart_id
    ) g
    WHERE g.chart_id = 'cb73cd3d-9eba-4220-9902-0de91566e980'::uuid AND g.n < 2667
  )
  -- (c) every chart that has any v1 row must still have all three of them present overall — the
  --     corpus spans exactly 3 charts and a retired writer can never add a fourth.
  AND (SELECT count(DISTINCT chart_id) FROM kala_gochara_windows WHERE generation = 'v1') = 3
  -- (d) §N.3 generation hygiene: a v1 row must never carry an era_slice_key, which belongs to the
  --     gen-3.0 era-scoped delete path. A v1 row acquiring one would make it deletable.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows WHERE generation = 'v1' AND era_slice_key IS NOT NULL
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_gochara_sweep';


-- ka_gochara_v3_century_materialize  -- returns FALSE today: true positive, see header
UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_gochara_v3_century_materialize integrity contract
  -- (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_gochara_windows_v2 (staging surface) -- the writer ALSO dual-writes the
  -- production surface kala_gochara_windows, so conjunct (f) covers that side, generation-scoped.
  -- NO bare natural-key distinctness conjunct appears here: (chart_id, event_class, window_start,
  -- peak_date, coalesce(milestone_id,''), coalesce(resolution,''), generation) is ALREADY a DB
  -- UNIQUE index (uq_kala_gochara_windows_v2_natural_key), so asserting it could never fail.
  -- (a) B.10 / §N.5 birth-epoch authority. The writer hardcodes BIRTH_JD = 2445736.5 and
  -- BIRTH_YEAR = 1984 as module constants and never reads ctx.config['birth_params'], so every
  -- chart is materialised over the NATIVE'S century. No window may begin before its own
  -- chart's birth. RED today: 43 windows for chart 1c826d5a, born 1985-03-02, start on or
  -- after 1984-02-05 — another person's birth epoch. Chart-partitioned: the native's own 914
  -- rows are clean, so only the wrong chart's group violates.
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    JOIN charts c ON c.id = w.chart_id
    WHERE w.window_start < c.birth_date
  )
  -- (a2) the same defect at the PLAN level, and the sharper form of it: the decade grid the
  -- writer recorded for the run must start at the chart's own birth, not someone else's.
  -- RED today: 27 kala_gochara_v2_build_state rows for chart 1c826d5a carry
  -- horizon_start_date = 1984-02-05 against a birth_date of 1985-03-02.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_v2_build_state b
    JOIN charts c ON c.id = b.chart_id
    WHERE b.generation = 'g3_utkarsha' AND b.horizon_start_date < c.birth_date
  )
  -- (a3) the era LABELS must agree with the chart's own birth year. build_decade_slices()
  -- labels slices 'g3_{BIRTH_YEAR + 10i}_{BIRTH_YEAR + 10(i+1)}', so the earliest label of a
  -- correctly-anchored chart is exactly g3_{birth year}_{birth year + 10}. RED today for
  -- 1c826d5a (min label g3_1984_1994 against birth year 1985).
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT w.chart_id, min(w.era_slice_key) AS first_era, max(c.birth_date) AS birth_date
      FROM kala_gochara_windows_v2 w JOIN charts c ON c.id = w.chart_id
      WHERE w.generation = 'g3_utkarsha'
      GROUP BY w.chart_id) g
    WHERE g.first_era <> 'g3_' || extract(year FROM g.birth_date)::int::text
                       || '_'  || (extract(year FROM g.birth_date)::int + 10)::text
  )
  -- (b) every window must sit inside the decade slice its own label names. Detects a slice
  -- whose rows were written under the wrong era key (the label is the only thing the
  -- era-scoped production removal statement keys on, so a mislabelled row is also unreplaceable).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2
    WHERE generation = 'g3_utkarsha'
      AND extract(year FROM window_start) NOT BETWEEN split_part(era_slice_key,'_',2)::int
                                                  AND split_part(era_slice_key,'_',3)::int
  )
  -- (c) window sanity: the peak must lie inside the window it peaks. RED today on exactly one
  -- row (chart 482012f1, major_gain, window 1994-02-05..1994-02-28, peak 1994-02-04).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2
    WHERE peak_date < window_start OR peak_date > window_end OR window_end < window_start
  )
  -- (d) slice tiling. plan_substeps emits one substep per (event_class x decade) over exactly
  -- DECADE_SLICES = 10 slices, so every event class that produced rows must carry all ten era
  -- labels, none NULL, and all classes of a chart must carry the SAME ten. A gap means a
  -- substep silently produced nothing -- an extra means a stale label survived a rebuild.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2
    WHERE generation = 'g3_utkarsha' AND era_slice_key IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 WHERE generation = 'g3_utkarsha'
    GROUP BY chart_id, event_class HAVING count(DISTINCT era_slice_key) <> 10
  )
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, event_class, era_slice_key FROM kala_gochara_windows_v2
      WHERE generation = 'g3_utkarsha' GROUP BY 1,2,3) s
    JOIN (SELECT chart_id, era_slice_key FROM kala_gochara_windows_v2
          WHERE generation = 'g3_utkarsha' GROUP BY 1,2) t USING (chart_id)
    GROUP BY s.chart_id, s.event_class
    HAVING count(DISTINCT t.era_slice_key) <> count(DISTINCT s.era_slice_key)
  )
  -- (e) resolution hierarchy. A month or day row is a refinement OF an era row, so it must
  -- carry a parent that exists, belongs to the same chart, the same event class and the same
  -- era slice, and whose own window contains it.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.resolution IN ('month','day')
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_windows_v2 p
        WHERE p.id            = w.parent_window_id
          AND p.chart_id      = w.chart_id
          AND p.event_class   = w.event_class
          AND p.era_slice_key IS NOT DISTINCT FROM w.era_slice_key
          AND p.window_start <= w.window_start
          AND p.window_end   >= w.window_end)
  )
  -- (f) §N.3 accretion on the PRODUCTION surface. This writer's production removal statement is scoped
  -- '… AND generation = 3.0 AND era_slice_key = <slice>', so a generation-3.0 row with a NULL
  -- era_slice_key can never be replaced by any rebuild — it accretes permanently. Scoped to
  -- generation '3.0' on purpose: all 38,287 protected v1 rows are correctly NULL there and
  -- must not be swept in. RED today on 54 rows (W2 M12).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows
    WHERE generation = '3.0' AND era_slice_key IS NULL
  )
  -- (g) plan/output agreement. Every (chart, event_class, era) that produced rows must have the
  -- substep ledger row that claims to have produced them, fingerprinted. §N.8: output with no
  -- ledger entry is a build whose completeness nothing can attest.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT DISTINCT chart_id, event_class, era_slice_key
      FROM kala_gochara_windows_v2 WHERE generation = 'g3_utkarsha') z
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_gochara_v2_build_state b
      WHERE b.chart_id          = z.chart_id
        AND b.generation        = 'g3_utkarsha'
        AND b.event_class       = z.event_class || '::' || z.era_slice_key
        AND b.class_fingerprint IS NOT NULL)
  )
  -- (h) the writer's own MR-45 row-count bound, per substep: a decade slice may hold at most
  -- N_era + 2 * min(3 * N_era, ceil(3652.5 / 90)) rows, because each era window contributes at
  -- most MAX_PEAKS_PER_ERA_WINDOW = 3 peaks and the pooled MIN_PEAK_SEPARATION_DAYS = 90
  -- retention caps the total. A refinement explosion breaks it. (Derived per group from that
  -- group's own era count — not a count pin.)
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT count(*) FILTER (WHERE resolution = 'era')             AS n_era,
             count(*) FILTER (WHERE resolution IN ('month','day'))  AS n_sub
      FROM kala_gochara_windows_v2 WHERE generation = 'g3_utkarsha'
      GROUP BY chart_id, event_class, era_slice_key) z
    WHERE z.n_sub > 2 * LEAST(3 * z.n_era, 41)
  )
  -- (i) every materialised event class must trace to the chart's own resonance map, which is
  -- where plan_substeps discovers the class list (MR-16 dynamic classes).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows_v2 w
    WHERE w.generation = 'g3_utkarsha'
      AND NOT EXISTS (
        SELECT 1 FROM gochara_resonance_map g
        WHERE g.chart_id = w.chart_id AND g.event_class = w.event_class)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_gochara_v3_century_materialize';


-- ka_jivana_parva
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_jivana_parva integrity contract  (target table: kala_jivana_parva)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- NOTE on the level dimension: this table mixes MD (level 1), AD (level 2) and PD (level 3)
-- rows with NO level column (F-PARVA-1). The level is recoverable ONLY from source_citation
-- ('...:MD=X' / '...:MD=X:AD=Y' / '...:PD=Z', ka_jivana_parva.py:189/:249/:318), so this
-- contract re-derives it there. That re-derivation is itself pinned by conjunct (b).
SELECT
  -- (a) §N.3 identity key. NOT redundant with the one UNIQUE this table carries. That index
  -- (idx_kala_jivana_parva_chart_index, UNIQUE (chart_id, parva_index)) pins a LOOP COUNTER
  -- incremented across three separate emit loops (:172, :237, :306) -- it guarantees only
  -- that two rows got different counter values, which is true of two rows that are the same
  -- chapter written twice. The real natural key is (chart_id, source_citation, start_year):
  -- source_citation is the ONLY place the MD/AD/PD level and the parent MD are recorded
  -- (F-PARVA-1 -- there is no level column), and start_year separates the same lord recurring
  -- in a later Vimshottari cycle. Two rows can satisfy the index and violate this.
  NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva
    GROUP BY chart_id, source_citation, start_year
    HAVING count(*) > 1
  )
  -- (b) §N.7 item 2: the level/lord pin the whole contract rests on must actually hold --
  -- dasha_planet must equal the lord token in its own citation, and the citation must carry
  -- this writer's version prefix. Without this, (c)-(f) could be re-deriving levels off a
  -- string that no longer means what it says.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva
    WHERE source_citation NOT LIKE 'ka_jivana_parva:v2.0:%'
       OR (source_citation LIKE '%:AD=%'
           AND dasha_planet <> split_part(source_citation, ':AD=', 2))
       OR (source_citation LIKE '%:PD=%'
           AND dasha_planet <> split_part(source_citation, ':PD=', 2))
       OR (source_citation NOT LIKE '%:AD=%' AND source_citation NOT LIKE '%:PD=%'
           AND dasha_planet <> split_part(source_citation, ':MD=', 2))
  )
  -- (c) §N.5 L1 authority: a life chapter never invents its own span -- every parva must
  -- resolve to a real chart_dashas period at its own level, in the scoped system + ayanamsha
  -- the writer pins (vimshottari / lahiri_chitrapaksha, :74-79). end_year must match the L1
  -- period exactly, while start_year may sit inside the L1 span because the T-9 clip
  -- legitimately raises a straddling start to the birth year.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva p
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_dashas d
      WHERE d.chart_id = p.chart_id
        AND d.system_id = 'vimshottari'
        AND d.ayanamsha_id = 'lahiri_chitrapaksha'
        AND d.level_n = (CASE WHEN p.source_citation LIKE '%:AD=%' THEN 2
                              WHEN p.source_citation LIKE '%:PD=%' THEN 3
                              ELSE 1 END)
        AND d.lord_graha = p.dasha_planet
        AND extract(year FROM d.end_date)::int = p.end_year
        AND p.start_year BETWEEN extract(year FROM d.start_date)::int
                             AND extract(year FROM d.end_date)::int
    )
  )
  -- (d) the machine test of the T-9 pre-birth clip the writer implements in prose
  -- (module docstring: "a 1984 native has no lived experience of a chapter that began in
  -- 1950"). §N.8 -- the clip is a claim, and this is its detector.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva p
    JOIN charts c ON c.id = p.chart_id
    WHERE p.start_year < extract(year FROM c.birth_date)::int
  )
  -- (e) per-level tiling: the mahadasha chapters of one chart must tile the life without gap
  -- or overlap (each MD's end_year is the next MD's start_year), and every parva must be
  -- forward in time. The DB has no CHECK on either.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, end_year,
             lead(start_year) OVER (PARTITION BY chart_id ORDER BY start_year) AS nxt
      FROM kala_jivana_parva
      WHERE source_citation NOT LIKE '%:AD=%' AND source_citation NOT LIKE '%:PD=%'
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt IS DISTINCT FROM t.end_year
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva WHERE end_year IS NULL OR end_year < start_year
  )
  -- (f) every antardasha chapter must sit inside a served mahadasha chapter of the parent
  -- lord its own citation names -- the AD loop only walks ADs whose start falls inside the
  -- MD span (:193-197), so a nested row with no parent is a broken life arc.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva a
    WHERE a.source_citation LIKE '%:AD=%'
      AND NOT EXISTS (
        SELECT 1 FROM kala_jivana_parva m
        WHERE m.chart_id = a.chart_id
          AND m.source_citation = 'ka_jivana_parva:v2.0:MD='
              || split_part(split_part(a.source_citation, ':MD=', 2), ':AD=', 1)
          AND a.start_year BETWEEN m.start_year AND m.end_year)
  )
  -- (g) §N.7 item 6: high_convergence_count is counted from the same window set
  -- avg_effective_score is averaged over (:167-171). A chapter that claims high-convergence
  -- windows while reporting no average has no window set behind the claim -- the honest
  -- shape of "no windows in span" is 0 and NULL together, never a count with a null mean.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva
    WHERE (high_convergence_count > 0 AND avg_effective_score IS NULL)
       OR high_convergence_count < 0
       OR array_length(theme_keywords, 1) IS NULL
  )
  -- (h) parva_index is this table's only UNIQUE key and its serving order, so it must be dense
  -- 1..n per chart, or a consumer paging the life arc silently skips a chapter.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jivana_parva
    GROUP BY chart_id
    HAVING min(parva_index) <> 1
        OR max(parva_index) <> count(*)
        OR count(DISTINCT parva_index) <> count(*)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_jivana_parva';


-- ka_kala_darshana
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_kala_darshana integrity contract  (target table: kala_darshana)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. Every conjunct groups by
-- chart_id or evaluates a row carrying its own chart_id. No bare count equality pin (C12).
SELECT
  -- (a) §N.3 cross-build accretion detector. kala_darshana has ONLY a surrogate id PK. A
  -- partial UNIQUE (idx_kala_darshana_convergence) covers convergence_id WHERE NOT NULL and
  -- is not chart-scoped, so the load-bearing halves here are the NOT NULL guard that closes
  -- the hole that partial index leaves, and the chart-scoped grouping. The writer emits
  -- exactly one display row per convergence window (ka_kala_darshana.py:56-105).
  NOT EXISTS (
    SELECT 1 FROM kala_darshana WHERE convergence_id IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana
    GROUP BY chart_id, convergence_id
    HAVING count(*) > 1
  )
  -- (b) §N.5 L3-internal authority: the display row NEVER restates an upstream computed
  -- value as its own truth -- the writer copies peak_date / window_start / window_end /
  -- signal_id straight off kala_convergence (:94-100). The FK enforces existence but not
  -- chart agreement, so the join is pinned on both keys.
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_convergence c
      WHERE c.convergence_id = d.convergence_id
        AND c.chart_id = d.chart_id
        AND c.peak_date IS NOT DISTINCT FROM d.peak_date
        AND c.window_start IS NOT DISTINCT FROM d.window_start
        AND c.window_end IS NOT DISTINCT FROM d.window_end
        AND c.signal_id IS NOT DISTINCT FROM d.signal_id
    )
  )
  -- (c) §N.7 item 6 -- the direct F-DARSH-1 detector. effective_score is defined as
  -- convergence_score * (1 - max override), clamped (_compute_effective_score, :117-125).
  -- The writer currently passes `conv_score or 0.5`, so a genuinely computed 0.0 falls to a
  -- favourable mid-scale literal. That substitution makes effective_score exceed the
  -- convergence_score it claims to net down, and this recompute catches it exactly. An
  -- honest null beats an invented judgment.
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d
    JOIN kala_convergence c
      ON c.convergence_id = d.convergence_id AND c.chart_id = d.chart_id
    WHERE abs(
            d.effective_score
            - least(1.0, greatest(0.0,
                c.convergence_score * (1.0 - COALESCE(
                  (SELECT max((e->>'override_score')::float8)
                   FROM jsonb_array_elements(d.obstruction_summary) e), 0.0))))
          ) > 1e-9
  )
  -- (d) §N.7 item 1: net_label is a restatement of (effective_score, obstruction severities),
  -- not an independent grade -- _compute_net_label (:128-147). Re-derived here in full so a
  -- label that drifts from the numbers it summarises fails.
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d
    WHERE d.net_label IS DISTINCT FROM (
      CASE
        WHEN d.obstruction_summary @> '[{"severity":"severe"}]' THEN 'obstructed_severe'
        WHEN d.obstruction_summary @> '[{"severity":"moderate"}]' AND d.effective_score < 0.4
             THEN 'obstructed'
        WHEN d.effective_score >= 0.70 THEN 'auspicious_strong'
        WHEN d.effective_score >= 0.45 THEN 'auspicious_moderate'
        WHEN d.effective_score >= 0.20 THEN 'auspicious_speculative'
        WHEN jsonb_array_length(d.obstruction_summary) > 0 THEN 'obstructed'
        ELSE 'neutral'
      END)
  )
  -- (e) §N.6 item 1 + §N.7 item 1: the served obstruction_summary must mirror the actual
  -- ka_vighnakara rows for the same window (same chart), entry-for-entry, and the caution
  -- sentence must name an obstruction that is really present at moderate-or-severe. This is
  -- the machine-decidable half of F-DARSH-3: it catches narration that has drifted from its
  -- own grounding. (It deliberately does NOT assert that a caution and an auspicious_* label
  -- cannot co-occur -- see ka_kala_darshana.volume.md for why that judgement is not encoded.)
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d
    WHERE jsonb_array_length(d.obstruction_summary) <> (
      SELECT count(*) FROM kala_obstruction o
      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d, jsonb_array_elements(d.obstruction_summary) e
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_obstruction o
      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id
        AND o.obstruction_type = e->>'type'
        AND o.severity = e->>'severity'
        AND abs(o.override_score - (e->>'override_score')::float8) < 1e-9)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana d
    WHERE ((d.narrative->>'caution') IS NOT NULL)
          <> (d.obstruction_summary @> '[{"severity":"moderate"}]'
              OR d.obstruction_summary @> '[{"severity":"severe"}]')
       OR ((d.narrative->>'caution') IS NOT NULL
           AND NOT EXISTS (
             SELECT 1 FROM jsonb_array_elements(d.obstruction_summary) e
             WHERE e->>'severity' IN ('severe','moderate')
               AND (d.narrative->>'caution') LIKE '%' || (e->>'type') || '%'))
  )
  -- (f) range guard: kala_darshana carries no CHECK on its dates at all, so nothing but this
  -- stops a display row from being dated outside its own window.
  AND NOT EXISTS (
    SELECT 1 FROM kala_darshana
    WHERE peak_date IS NULL OR window_start IS NULL OR window_end IS NULL
       OR peak_date < window_start OR peak_date > window_end
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_kala_darshana';


-- ka_kalasutra  -- returns FALSE today: true positive, see header
UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_kalasutra integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_activation.
  -- NO bare natural-key distinctness conjunct appears here: (chart_id, signal_id, ayanamsha_id,
  -- source_citation) is ALREADY a DB UNIQUE index. Conjunct (b) instead asserts the SEMANTIC key
  -- the writer actually means, (chart, signal, ayanamsha, period index) — which that index cannot
  -- enforce, because source_citation also embeds `src=<resolution_source>` and an optional
  -- `always_on=` suffix, so two rows for the same period can differ in the citation and be
  -- accepted (F-KALA-4).
  -- (a) §N.5 / B.10 dating authority. The writer's own headline claim is "no fabricated dates:
  -- every date traces to a chart_dashas row". Machine form: every dated window must lie inside
  -- a real vimshottari MD or AD period of the SAME chart and the SAME ayanamsha — the exact
  -- timeline load_dasha_timeline() reads (system_id='vimshottari', level_n <= 2, own ayanamsha).
  -- RED today on 56 rows, all on chart cb73cd3d, all stamped src=dasha_timeline: windows that
  -- claim an L1 provenance no current L1 period supports.
  NOT EXISTS (
    SELECT 1 FROM kala_activation a
    WHERE a.activation_start IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM chart_dashas d
        WHERE d.chart_id     = a.chart_id
          AND d.ayanamsha_id = a.ayanamsha_id
          AND d.system_id    = 'vimshottari'
          AND d.level_n     <= 2
          AND d.start_date  <= a.activation_start
          AND d.end_date    >= a.activation_end)
  )
  -- (b) §N.3 accretion detector on the SEMANTIC key. period index is this build's own
  -- enumerate() position, unique per (chart, signal, ayanamsha) by construction -- two rows
  -- sharing one means two builds' output coexisting, which the per-chart clear-then-write discipline of §N.3 forbids.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation
    GROUP BY chart_id, signal_id, ayanamsha_id,
             split_part(split_part(source_citation, ':period=', 2), ':', 1)
    HAVING count(*) > 1
  )
  -- (b2) the period index must actually be parseable, or (b) degenerates into grouping on an
  -- empty string. Every citation must carry its period marker.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation
    WHERE source_citation NOT LIKE '%:period=%'
       OR split_part(split_part(source_citation, ':period=', 2), ':', 1) = ''
  )
  -- (c) window coherence. Start and end are populated together or not at all -- the window is
  -- not inverted -- the peak lies inside it -- and no activation precedes the native's own birth
  -- (the writer's §8.4 birth-forward rule — pre-birth cycles are not life-indexable).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation a
    JOIN charts c ON c.id = a.chart_id
    WHERE (a.activation_start IS NULL) <> (a.activation_end IS NULL)
       OR a.activation_end < a.activation_start
       OR (a.activation_peak_date IS NOT NULL
           AND (a.activation_peak_date < a.activation_start
                OR a.activation_peak_date > a.activation_end))
       OR a.activation_start < c.birth_date
  )
  -- (d) upstream agreement with ka_yojaka, both directions. Every activation must stand on a
  -- live predicate, and every predicate must have produced at least one activation row (the
  -- CR-109 fallback guarantees an all-NULL row even when nothing resolves, so zero rows for a
  -- predicate means the pair is out of step). RED today: 49,730 of chart cb73cd3d's predicates
  -- have no activation at all — its rows were removed by the signal_id foreign key's cascade
  -- when L2 re-issued its signals, leaving a silently gutted table (1,055 rows against a
  -- sibling chart's 335,403).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation a
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_activation_predicates p
      WHERE p.chart_id = a.chart_id AND p.signal_id = a.signal_id
        AND p.ayanamsha_id = a.ayanamsha_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    WHERE EXISTS (SELECT 1 FROM kala_activation q WHERE q.chart_id = p.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_activation a
        WHERE a.chart_id = p.chart_id AND a.signal_id = p.signal_id
          AND a.ayanamsha_id = p.ayanamsha_id)
  )
  -- (e) §N.5 signal identity. The table's foreign key checks only that signal_id exists
  -- SOMEWHERE -- it cannot check that the signal belongs to this chart and this ayanamsha.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation a
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.signal_id = a.signal_id AND s.chart_id = a.chart_id
        AND s.ayanamsha_id = a.ayanamsha_id)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_kalasutra';


-- ka_kota_chakra
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_kota_chakra integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
SELECT
  -- (a) N.5 L1/L0-authority: the served ring must equal what the L0 partition says for that count.
  NOT EXISTS (
    SELECT 1 FROM kala_kota_chakra k
    JOIN bg_kota_chakra_rings r ON r.ring_position = k.count_from_janma
    WHERE r.ring_name IS DISTINCT FROM k.kota_ring
  )
  -- (b) per (chart, graha) run tiling: no gap and no overlap between consecutive windows.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, graha, window_end,
             lead(window_start) OVER (PARTITION BY chart_id, graha ORDER BY window_start) AS nxt
      FROM kala_kota_chakra
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt <> t.window_end + 1
  )
  -- (c) every window is non-degenerate, and every chart present carries all 9 grahas.
  AND NOT EXISTS (SELECT 1 FROM kala_kota_chakra WHERE window_end < window_start)
  AND NOT EXISTS (
    SELECT 1 FROM kala_kota_chakra
    GROUP BY chart_id HAVING count(DISTINCT graha) <> 9
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_kota_chakra';


-- ka_kshetra
UPDATE asset_registry SET integrity_check_sql = $ck$
WITH
-- ka_kshetra integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
-- Target table kala_field (11,012,657 rows / ~5.0 GB across two charts).
-- Its natural key (chart_id, event_class, segment_index) is already a DB UNIQUE constraint and
-- t_end > t_start is already a CHECK, so neither is restated here (D-CND-03 item 4).
-- COST DISCIPLINE: every conjunct below is served by an existing index. `span` and `snap` are
-- computed ONCE and reused -- the tiling conjunct rides idx_kala_field_lookup
-- (chart_id, event_class, t_start, t_end) so the window function needs no sort -- the segment
-- density conjunct rides kala_field_natural_key. Measured runtimes are in the evidence file.
span AS (
  SELECT chart_id, event_class, min(t_start) AS t0, max(t_end) AS t1, count(*) AS n_seg
  FROM kala_field GROUP BY chart_id, event_class),
snap AS (
  SELECT chart_id, field_snapshot_id, weights_version, x_schema_version
  FROM kala_field GROUP BY chart_id, field_snapshot_id, weights_version, x_schema_version)
SELECT
  -- (a) horizon completeness. Section 5.2's horizon is birth -> birth + 100 Julian years, so
  -- stage 4 must lay every event class's segments across exactly [0, HORIZON_DAYS = 36525].
  -- A class whose segments stop short is a substep that produced nothing and was never noticed
  -- (stages 0-3 write no build_substep_progress rows at all, so the §N.8 plan-completeness
  -- detector cannot see them -- this conjunct is the data-side detector for that gap).
  NOT EXISTS (SELECT 1 FROM span WHERE t0 <> 0 OR t1 <> 36525)
  -- (b) segment tiling. Consecutive segments of one (chart, event_class) must abut exactly:
  -- the next segment's t_start IS the previous segment's t_end. A gap means a lost segment -- an
  -- overlap means two decade chunks wrote the same interval, which the natural key cannot see
  -- because their segment_index values differ. Together with (a) this asserts that the class's
  -- segments partition the full century with no gap and no overlap.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT t_end,
             lead(t_start) OVER (PARTITION BY chart_id, event_class ORDER BY t_start, t_end)
               AS nxt
      FROM kala_field) z
    WHERE z.nxt IS NOT NULL AND z.nxt <> z.t_end)
  -- (c) segment_index encoding. The writer encodes (decade, local ordinal) as
  -- decade * SEGMENT_INDEX_DECADE_STRIDE + ordinal with DECADES = 10, precisely so that a
  -- chunk's ordinals never depend on dispatch order. So the decade must be one of the ten
  -- planned slices, and within each (chart, class, decade) the ordinals must run dense from 0.
  -- A half-written stage4 chunk breaks the density -- a stale chunk from an older plan breaks
  -- the decade range.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT segment_index / 1000000 AS decade, count(*) AS n,
             min(segment_index % 1000000) AS lo, max(segment_index % 1000000) AS hi
      FROM kala_field GROUP BY chart_id, event_class, segment_index / 1000000) z
    WHERE z.decade < 0 OR z.decade > 9 OR z.lo <> 0 OR z.hi <> z.n - 1)
  -- (d) §N.5 single-snapshot consistency. Every row of a chart must belong to ONE pinned build
  -- (field_snapshot_id / weights_version / x_schema_version), and that pin must be REGISTERED
  -- in kala_field_snapshots with the same weights and schema versions. The writer upserts
  -- rather than deleting, so a partial rebuild would otherwise leave two snapshot generations
  -- silently interleaved in one served field -- the cross-table check is the only detector.
  AND NOT EXISTS (SELECT 1 FROM snap GROUP BY chart_id HAVING count(*) <> 1)
  AND NOT EXISTS (
    SELECT 1 FROM snap q WHERE NOT EXISTS (
      SELECT 1 FROM kala_field_snapshots s
      WHERE s.chart_id         = q.chart_id
        AND s.field_snapshot_id = q.field_snapshot_id
        AND s.weights_version   = q.weights_version
        AND s.x_schema_version  = q.x_schema_version))
  -- (e) the weights version every row was computed under must be a registered version
  -- (kala_field_weight_versions), not a free-text label. B.3: no computed value without a
  -- resolvable source for the weights that produced it.
  AND NOT EXISTS (
    SELECT 1 FROM snap q WHERE NOT EXISTS (
      SELECT 1 FROM kala_field_weight_versions v WHERE v.version_id = q.weights_version))
  -- (f) cross-table family agreement, the highest-value conjunct here: kala_field_windows is
  -- the only surface of this family the serving plane actually reaches, and it is derived FROM
  -- the segments. Every window must belong to a class the field actually has, must lie inside
  -- that class's own segment span, and must carry the chart's current snapshot pin. A window
  -- surviving from an older snapshot, or naming a class stage 4 never built, fails here.
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_windows w
    LEFT JOIN span s ON s.chart_id = w.chart_id AND s.event_class = w.event_class
    WHERE s.chart_id IS NULL OR w.t_start < s.t0 OR w.t_end > s.t1)
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_windows w WHERE NOT EXISTS (
      SELECT 1 FROM snap q
      WHERE q.chart_id = w.chart_id AND q.field_snapshot_id = w.field_snapshot_id))
  -- (g) window <-> salience bijection. kala_field_salience is the one surface with a live
  -- serving consumer (kala_priority_get). Every window must have its salience row and every
  -- salience row must have its window, per chart -- a dangling salience row would be served as
  -- a priority for a window that no longer exists.
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_windows w WHERE NOT EXISTS (
      SELECT 1 FROM kala_field_salience sa
      WHERE sa.chart_id = w.chart_id AND sa.window_id = w.window_id))
  AND NOT EXISTS (
    SELECT 1 FROM kala_field_salience sa WHERE NOT EXISTS (
      SELECT 1 FROM kala_field_windows w
      WHERE w.chart_id = sa.chart_id AND w.window_id = sa.window_id))
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_kshetra';


-- ka_moorti_nirnaya
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_moorti_nirnaya integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
-- Target table: kala_moorti_nirnaya. Its natural key (chart_id, ayanamsha_id, graha,
-- window_start) is ALREADY a DB-level UNIQUE, so no distinctness conjunct appears here
-- (D-CND-03 rule 4 — a redundant check cannot fail and fails the rewrite floor test).
-- Every conjunct below is a correlated NOT EXISTS over rows / per-chart groups, so a corruption
-- confined to one chart makes that chart's rows violate.
SELECT
  -- (a) §N.5 L0-authority: the served moorti grade IS bg_transit_moorti's row for that
  -- nakshatra_offset, read verbatim. A writer that re-derives the grade rather than citing it
  -- diverges here. This is the invariant a future writer refactor is most likely to break.
  NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    JOIN bg_transit_moorti b ON b.nakshatra_offset = m.nakshatra_offset
    WHERE m.moorti_computed
      AND (m.moorti_name IS DISTINCT FROM b.moorti_name
        OR m.quality_tier IS DISTINCT FROM b.quality_tier
        OR m.phala_brief IS DISTINCT FROM b.phala_brief
        OR m.moorti_classical_citation IS DISTINCT FROM b.classical_citation)
  )
  -- (b) §N.5: every graded row's offset key must RESOLVE upstream. A graded row whose key is
  -- absent from the L0 table is an ungrounded grade, not an honest gap.
  AND NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    WHERE m.moorti_computed
      AND NOT EXISTS (
        SELECT 1 FROM bg_transit_moorti b WHERE b.nakshatra_offset = m.nakshatra_offset
      )
  )
  -- (c) §N.7 item 1: nakshatra_offset is a deterministic restatement of the two indices the row
  -- itself stores — ((moon-at-ingress minus janma) mod 27) + 1 — never an independent quantity.
  AND NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    WHERE m.moorti_computed
      AND m.nakshatra_offset IS DISTINCT FROM
          ((((m.moon_nakshatra_idx_at_ingress - m.janma_nakshatra_idx) % 27) + 27) % 27) + 1
  )
  -- (d) §N.5 L1-authority: janma_nakshatra_fact_id must resolve to THIS chart's own chart_facts
  -- row at the same ayanamsha, and the stored janma index must equal the nakshatra of that L1
  -- longitude. L1 owns the value — L3 may only reference it.
  AND NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    LEFT JOIN chart_facts f
      ON f.fact_id = m.janma_nakshatra_fact_id
     AND f.chart_id = m.chart_id
     AND f.ayanamsha_id = m.ayanamsha_id
    WHERE f.fact_id IS NULL
       OR f.fact_value_num IS NULL
       OR m.janma_nakshatra_idx IS DISTINCT FROM (floor(f.fact_value_num / (360.0 / 27.0))::int % 27)
  )
  -- (e) §N.3 replace-not-accrete: per (chart, graha) the sign-runs must tile the scanned horizon
  -- with no gap and no overlap. A run left behind by a partial rebuild, or a horizon roll that
  -- only partly replaced a graha's runs, breaks contiguity here.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, graha, window_end,
             lead(window_start) OVER (PARTITION BY chart_id, graha ORDER BY window_start) AS nxt
      FROM kala_moorti_nirnaya
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt <> t.window_end + 1
  )
  -- (f) §N.8 earned signal: moorti_computed is NOT taken as a self-report. It is re-derived from
  -- the horizon edge: a run beginning on the chart's first scanned day has no observed ingress
  -- instant and MUST be ungraded — every other run MUST be graded. A grade on a horizon-edge run
  -- is invented precision (B.10) — an ungraded interior run means an ephemeris hole nothing named.
  AND NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    JOIN (
      SELECT chart_id, min(window_start) AS h_start FROM kala_moorti_nirnaya GROUP BY chart_id
    ) h ON h.chart_id = m.chart_id
    WHERE m.moorti_computed = (m.window_start = h.h_start)
  )
  -- (g) §N.3 cardinality per group: within one chart every graha was scanned over the SAME
  -- horizon, so each (chart, graha) has exactly one run touching the horizon's first day and
  -- exactly one touching its last. A graha whose runs came from an older, differently-anchored
  -- build violates this even though its own runs tile.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT m.chart_id, m.graha,
             count(*) FILTER (WHERE m.window_start = h.h_start) AS n_first,
             count(*) FILTER (WHERE m.window_end = h.h_end) AS n_last
      FROM kala_moorti_nirnaya m
      JOIN (
        SELECT chart_id, min(window_start) AS h_start, max(window_end) AS h_end
        FROM kala_moorti_nirnaya GROUP BY chart_id
      ) h ON h.chart_id = m.chart_id
      GROUP BY m.chart_id, m.graha
    ) g
    WHERE g.n_first <> 1 OR g.n_last <> 1
  )
  -- (h) §N.7 item 3: the served sign label restates reference_signs, never a wrapper-local list
  -- that can drift from its source.
  AND NOT EXISTS (
    SELECT 1 FROM kala_moorti_nirnaya m
    JOIN reference_signs s ON s.sign_id = m.target_sign_idx + 1
    WHERE s.canonical_name_en IS DISTINCT FROM m.target_sign_name
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_moorti_nirnaya';


-- ka_sangam
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_sangam integrity contract  (target table: kala_convergence)
-- D-CND-03: chart-partitioned, attribution-preserving. Every conjunct below is either
-- grouped BY chart_id or evaluated row-wise (a row carries its own chart_id), so a
-- corruption confined to one chart makes that chart's rows/group violate. No bare count pin.
SELECT
  -- (a) §N.3 cross-build accretion detector. kala_convergence has ONLY a surrogate
  -- convergence_id PK and no natural-key UNIQUE, so this is the layer's only detector of
  -- rebuild-accretion. Natural key read off the writer: _dedupe_windows keys on
  -- (mode, peak_date, signal_id) and _insert_windows is scoped per horizon_tier per chart
  -- (ka_sangam.py:880 / :888, replace-per-chart at :433/:526/:536/:577).
  NOT EXISTS (
    SELECT 1 FROM kala_convergence
    GROUP BY chart_id, horizon_tier, mode, peak_date, signal_id
    HAVING count(*) > 1
  )
  -- (b) §N.7 item 1 + §N.5: a Mode C score must be re-derivable from the two catalog
  -- constants its own ledger persists -- engine.py:1351 cscore = round(dignity_score *
  -- severity, 4) -- and the severity constant must come from the ratified doctrine set
  -- (derive_sade_sati_severity 0.70/1.00, _AYUR_SIGNS_MARS 0.85, fallback 0.70).
  -- A narration/serving layer must never restate a value the ledger cannot reproduce.
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE mode = 'C'
      AND (
        NOT (constituent_factors ? 'dignity_score' AND constituent_factors ? 'severity_score')
        OR (constituent_factors->>'severity_score')::numeric NOT IN (0.70, 0.85, 1.00)
        OR abs(convergence_score
               - round((constituent_factors->>'dignity_score')::numeric
                       * (constituent_factors->>'severity_score')::numeric, 4)) > 1e-9
      )
  )
  -- (c) §N.7 item 1 + §N.5: same re-derivation for Mode D -- engine.py mode_d_av_bindhu
  -- score = (sav_bindhu / 56) * dignity_score -- plus the classical admission gate the mode
  -- claims for itself (Phaladeepika Ch.26 / BPHS Ch.66: sav_bindhu >= sav_threshold).
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE mode = 'D'
      AND (
        NOT (constituent_factors ? 'sav_bindhu' AND constituent_factors ? 'sav_threshold'
             AND constituent_factors ? 'dignity_score')
        OR (constituent_factors->>'sav_bindhu')::int < (constituent_factors->>'sav_threshold')::int
        OR abs(convergence_score
               - round((constituent_factors->>'sav_bindhu')::numeric / 56.0
                       * (constituent_factors->>'dignity_score')::numeric, 4)) > 1e-9
      )
  )
  -- (d) PER-MODE SCORE-RANGE DISCIPLINE (the F-SANGAM-1 incommensurability, made detectable).
  -- convergence_score is written by four modes on four incommensurable scales and every
  -- consumer ranks ORDER BY convergence_score DESC. This conjunct pins each mode inside the
  -- range its OWN arithmetic can produce, so a mode drifting onto another mode's scale is a
  -- contract failure rather than an invisible ranking inversion:
  --   A/B  saturating funnel 1 - PROD(1 - w_i*s_i) over SUPPORTING_WEIGHTS (engine.py:40,
  --        sum 1.0) has a hard ceiling of 0.6524176 -- and the TRIGGER term composes as
  --        net = pre + suppressive with suppressive <= 0 (kala_trigger/trigger.py:674),
  --        so it can only lower the score. Ceiling therefore holds strictly.
  --   C    score = dignity * severity with severity in [0.70, 1.00]
  --        => 0.70*dignity <= score <= dignity.
  --   D    score = (sav/56) * dignity with sav in [sav_threshold, 56]
  --        => (sav_threshold/56)*dignity <= score <= dignity.
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE (mode IN ('A','B') AND (convergence_score < 0.0 OR convergence_score > 0.6524176))
       OR (mode = 'C' AND (
              convergence_score < 0.70 * (constituent_factors->>'dignity_score')::numeric - 1e-9
           OR convergence_score > (constituent_factors->>'dignity_score')::numeric + 1e-9))
       OR (mode = 'D' AND (
              convergence_score < ((constituent_factors->>'sav_threshold')::numeric / 56.0)
                                  * (constituent_factors->>'dignity_score')::numeric - 1e-9
           OR convergence_score > (constituent_factors->>'dignity_score')::numeric + 1e-9))
  )
  -- (e) §N.8 earned-signal: Mode C and Mode D consult no point transit and no second current,
  -- so the writer hard-sets orb_strength = 1.0 (engine.py:1355 / mode_d) and
  -- independent_current_count floors at 1. A C/D row carrying agreement-looking evidence
  -- markers would be a fabricated density claim, which this conjunct forbids.
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE mode IN ('C','D')
      AND (orb_strength IS DISTINCT FROM 1.0 OR independent_current_count IS DISTINCT FROM 1)
  )
  -- (f) §N.7 item 3: confidence_score is not an independent number -- the writer sets it to
  -- round(min(1.0, icc/13), 4) (ka_sangam.py:957). A stored value that disagrees with the
  -- current count it claims to summarise is a wrapper-local constant shadowing its source.
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE abs(confidence_score
              - round(least(1.0, independent_current_count / 13.0)::numeric, 4)) > 1e-9
  )
  -- (g) range guard the DB CHECK cannot make: kala_convergence_valid_range asserts only
  -- window_end >= window_start, and says nothing about the peak the whole row is dated on.
  AND NOT EXISTS (
    SELECT 1 FROM kala_convergence
    WHERE peak_date IS NULL OR signal_id IS NULL
       OR peak_date < window_start OR peak_date > window_end
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_sangam';


-- ka_sudarshana_varsha
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_sudarshana_varsha integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
-- Target table: kala_sudarshana_varsha. Its natural key (chart_id, ayanamsha_id, varsha_year) is
-- ALREADY a DB-level UNIQUE, and the 0..11 sign-index ranges / varsha_year 1..120 / window
-- ordering are ALREADY DB CHECKs, so none of those is restated here (D-CND-03 rule 4).
-- The asset is pure calendar arithmetic over three natal sign facts, so every conjunct below is
-- a re-derivation of that arithmetic from what the row itself cites — the strongest form of
-- check available for a writer with no ephemeris of its own.
SELECT
  -- (a) §N.3 replace-not-accrete: the 120 year-windows must tile the lifespan exactly — each
  -- year's window_end is the next year's window_start, with no gap and no overlap. A year row
  -- surviving from an earlier build with a different birth anchor breaks the chain here.
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, window_end,
             lead(window_start) OVER (PARTITION BY chart_id ORDER BY varsha_year) AS nxt
      FROM kala_sudarshana_varsha
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt <> t.window_end
  )
  -- (b) §N.7 item 1 — the technique's defining arithmetic, pinned rather than a row count: each
  -- reference point advances from its own natal sign by (varsha_year - 1) mod 12 signs.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha v
    WHERE v.jl_active_sign_idx <> (v.jl_natal_sign_idx + (v.varsha_year - 1) % 12) % 12
       OR v.cl_active_sign_idx <> (v.cl_natal_sign_idx + (v.varsha_year - 1) % 12) % 12
       OR v.sl_active_sign_idx <> (v.sl_natal_sign_idx + (v.varsha_year - 1) % 12) % 12
  )
  -- (c) §N.8 earned signal: tri_lagna_convergence must equal the condition it claims to report,
  -- re-derived from the three active signs the row itself stores. (The flag is constant per
  -- chart because all three references share one offset — a known, recorded finding — this
  -- conjunct is what keeps it an honest restatement instead of an unmoored boolean.)
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha v
    WHERE v.tri_lagna_convergence
          <> (v.jl_active_sign_idx = v.cl_active_sign_idx
              AND v.cl_active_sign_idx = v.sl_active_sign_idx)
  )
  -- (d) §N.7 item 3: the three served sign labels restate reference_signs, never a
  -- wrapper-local list that can drift from its source.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha v
    WHERE (SELECT s.canonical_name_en FROM reference_signs s WHERE s.sign_id = v.jl_active_sign_idx + 1)
            IS DISTINCT FROM v.jl_active_sign_name
       OR (SELECT s.canonical_name_en FROM reference_signs s WHERE s.sign_id = v.cl_active_sign_idx + 1)
            IS DISTINCT FROM v.cl_active_sign_name
       OR (SELECT s.canonical_name_en FROM reference_signs s WHERE s.sign_id = v.sl_active_sign_idx + 1)
            IS DISTINCT FROM v.sl_active_sign_name
  )
  -- (e) §N.5 L1-authority: all three natal fact ids must resolve to THIS chart's own
  -- chart_facts rows, for the right subjects, and each stored natal sign index must equal the
  -- sign those L1 facts name. L1 owns the natal signs — this writer may only reference them.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha v
    LEFT JOIN chart_facts fl ON fl.fact_id = v.lagna_fact_id AND fl.chart_id = v.chart_id
    LEFT JOIN chart_facts fm ON fm.fact_id = v.moon_fact_id  AND fm.chart_id = v.chart_id
    LEFT JOIN chart_facts fs ON fs.fact_id = v.sun_fact_id   AND fs.chart_id = v.chart_id
    WHERE fl.fact_id IS NULL OR fm.fact_id IS NULL OR fs.fact_id IS NULL
       OR fl.fact_subject <> 'LAGNA' OR fm.fact_subject <> 'MOON' OR fs.fact_subject <> 'SUN'
       OR v.jl_natal_sign_idx IS DISTINCT FROM
          (SELECT s.sign_id - 1 FROM reference_signs s WHERE s.canonical_name_en = fl.fact_value_text)
       OR v.cl_natal_sign_idx IS DISTINCT FROM
          (SELECT s.sign_id - 1 FROM reference_signs s WHERE s.canonical_name_en = fm.fact_value_text)
       OR v.sl_natal_sign_idx IS DISTINCT FROM
          (SELECT s.sign_id - 1 FROM reference_signs s WHERE s.canonical_name_en = fs.fact_value_text)
  )
  -- (f) §N.3 cardinality per group: a built chart's year set is a contiguous run starting at
  -- year 1 — no hole, no year beyond the run. This is a range/coverage assertion, not a
  -- `count(*) = N` pin (C12/D-126): it holds for any horizon the writer's own constant sets.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha
    GROUP BY chart_id
    HAVING min(varsha_year) <> 1 OR count(*) <> max(varsha_year) - min(varsha_year) + 1
  )
  -- (g) §N.3 accretion detector: one chart has exactly one natal anchor. Rows from two
  -- different builds — or from two different L1 fact generations — would show two natal triples
  -- or two fact ids under one chart, which the natural key alone cannot see.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha
    GROUP BY chart_id
    HAVING count(DISTINCT (jl_natal_sign_idx, cl_natal_sign_idx, sl_natal_sign_idx)) <> 1
        OR count(DISTINCT lagna_fact_id) <> 1
        OR count(DISTINCT moon_fact_id) <> 1
        OR count(DISTINCT sun_fact_id) <> 1
  )
  -- (h) §N.7 item 1: every window is the plain calendar anniversary of the chart's own year-1
  -- start — window N runs [birth + (N-1) years, birth + N years). This is the day-grade
  -- labelling convention the writer discloses, made checkable without a birth date of our own.
  AND NOT EXISTS (
    SELECT 1 FROM kala_sudarshana_varsha v
    JOIN (SELECT chart_id, min(window_start) AS anchor FROM kala_sudarshana_varsha GROUP BY chart_id) k
      ON k.chart_id = v.chart_id
    WHERE v.window_start <> (k.anchor + make_interval(years => v.varsha_year - 1))::date
       OR v.window_end   <> (k.anchor + make_interval(years => v.varsha_year))::date
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_sudarshana_varsha';


-- ka_taranga
UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_taranga integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_taranga. Its natural key (chart_id, month, scope_kind, scope_id) is already
  -- a DB UNIQUE constraint, so no distinctness conjunct appears here (D-CND-03 item 4).
  -- W2 §3 ruled this asset a SPLIT: the scope_kind='domain' half is the genuine independent
  -- witness and is KEPT -- the scope_kind='event_class' half is degenerate and is to be retired.
  -- Conjuncts (d) and (e) therefore assert the DOMAIN half's real structure specifically, rather
  -- than averaging a claim over a half that cannot vary.
  -- (a) §N.5 L1-authority. Every month's stamped dasha_lord must be the lord chart_dashas
  -- actually reports for that month, at the canonical ayanamsha, vimshottari MD. The writer
  -- reads chart_dashas WITHOUT an ayanamsha filter, so this conjunct is also the CR-110
  -- double-spine detector for this asset: a lord picked from a non-canonical ayanamsha's
  -- boundary drift fails here.
  NOT EXISTS (
    SELECT 1 FROM kala_taranga t
    WHERE NOT EXISTS (
      SELECT 1 FROM chart_dashas d
      WHERE d.chart_id     = t.chart_id
        AND d.ayanamsha_id = 'lahiri_chitrapaksha'
        AND d.system_id    = 'vimshottari'
        AND d.level_n      = 1
        AND d.lord_graha   = t.components->>'dasha_lord'
        AND d.start_date  <= t.month
        AND d.end_date    >= t.month)
  )
  -- (b) waveform tiling, interior. Per (chart, scope_kind, scope_id) the months must form an
  -- unbroken monthly run: the row count must equal the whole-month span between that group's
  -- own first and last month. A dropped interior month or a duplicated build fragment breaks
  -- it. (Not a count pin: the expected value is derived per group from its own endpoints.)
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT count(*) AS n, min(month) AS mn, max(month) AS mx
      FROM kala_taranga GROUP BY chart_id, scope_kind, scope_id) g
    WHERE g.n <> ((extract(year FROM g.mx) - extract(year FROM g.mn)) * 12
                  + (extract(month FROM g.mx) - extract(month FROM g.mn)) + 1)
  )
  -- (b2) waveform tiling, endpoints. (b) alone cannot see a truncated head or tail -- removing
  -- an endpoint month shrinks the span and the count together. The writer walks ONE month
  -- range for every scope, so within a chart all scopes must share the same first and last
  -- month. This is the detector for a partially-written or partially-cleared scope.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, min(month) AS mn, max(month) AS mx
      FROM kala_taranga GROUP BY chart_id, scope_kind, scope_id) g
    GROUP BY g.chart_id
    HAVING count(DISTINCT g.mn) <> 1 OR count(DISTINCT g.mx) <> 1
  )
  -- (c) every month key is a real month start, and every activation is a present, bounded
  -- amplitude. kala_taranga carries NO CHECK constraint on activation, so this guards the
  -- served number itself (§N.7 item 6 -- no silent out-of-band or absent value).
  AND NOT EXISTS (
    SELECT 1 FROM kala_taranga
    WHERE month <> date_trunc('month', month)::date
       OR activation IS NULL OR activation < 0 OR activation > 1
  )
  -- (d) the domain half's stated formula is a real function of its inputs. The writer defines
  -- dasha_contribution = 1.0 when the scope's domain is in the month lord's natural
  -- significations else 0.15, so within a chart it must be uniquely determined by
  -- (dasha_lord, scope_id). Any (chart, scope_id, lord) group showing two values means the
  -- doctrine table drifted mid-build or a foreign row landed. Doctrine-free: no lord->domain
  -- constant is restated here (§N.7 item 3).
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT count(DISTINCT components->>'dasha_contribution') AS k
      FROM kala_taranga WHERE scope_kind = 'domain'
      GROUP BY chart_id, scope_id, components->>'dasha_lord') z
    WHERE z.k <> 1
  )
  -- (e) the domain half is not degenerate. W2 §3's own falsifier for the SPLIT, applied as a
  -- machine check to the half being kept: its dasha term must take at least two distinct
  -- values per chart (the event_class half's takes exactly one across 48,924 rows -- the
  -- reason that half is retired). Also, all scopes of one chart-month must agree on the lord.
  AND NOT EXISTS (
    SELECT 1 FROM kala_taranga WHERE scope_kind = 'domain'
    GROUP BY chart_id
    HAVING count(DISTINCT components->>'dasha_contribution') < 2
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_taranga
    GROUP BY chart_id, month
    HAVING count(DISTINCT components->>'dasha_lord') <> 1
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_taranga';


-- ka_tithi_pravesha
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_tithi_pravesha integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
-- Target table: kala_tithi_pravesha. Its natural key (chart_id, ayanamsha_id, pravesha_year) is
-- ALREADY a DB-level UNIQUE, and the verification vocabulary / lagna-field pairing / year range /
-- window ordering are ALREADY DB CHECKs, so none of those is restated here (D-CND-03 rule 4).
-- This asset is the one L3 quality overlay carrying a genuinely earned verification signal, so
-- the contract's centre of gravity is making that signal re-derivable from its own stored audit.
SELECT
  -- (a) §N.3 replace-not-accrete, and the root-find's own consistency: the END root-find of year
  -- N and the START root-find of year N+1 are the same computed instant, so the lifetime tiles
  -- exactly. This is what a root-find regression, or a year row left over from an earlier build
  -- with a different natal anchor, breaks first.
  NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, window_end,
             lead(window_start) OVER (PARTITION BY chart_id ORDER BY pravesha_year) AS nxt
      FROM kala_tithi_pravesha
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt <> t.window_end
  )
  -- (b) §N.8 earned signal / §N.7 item 4 — the stored verification status must be re-derivable
  -- from the stored audit, in BOTH directions: 'two_pass_verified' exactly when the root-find
  -- converged AND the annual chart's independently-recomputed Moon longitude agrees with the
  -- natal target within the writer's own LUNAR_RETURN_TOL_DEG (0.01 deg). A status that cannot
  -- be re-derived from the evidence beside it is a flag with no detector behind it.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    WHERE (t.verification_pass_status = 'two_pass_verified')
          <> (t.start_converged
              AND (t.ephemeris_audit_jsonb->>'annual_chart_moon_cross_check_diff_deg')::float8 <= 0.01)
  )
  -- (c) §N.7 item 1: the two convergence booleans are restatements of the audit sub-objects they
  -- summarise, never separately-maintained values. A missing audit sub-object surfaces here as a
  -- NULL mismatch rather than passing as a silent absence.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    WHERE t.start_converged IS DISTINCT FROM (t.ephemeris_audit_jsonb->'start'->>'converged')::boolean
       OR t.end_converged   IS DISTINCT FROM (t.ephemeris_audit_jsonb->'end'->>'converged')::boolean
  )
  -- (d) §N.5 L1-authority: the root-find target is the natal Moon longitude L1 computed. The
  -- cited fact must resolve for THIS chart at the same ayanamsha and the stored value must equal
  -- it to the six places the writer rounds to. A drifted target silently re-anchors 120 charts.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    LEFT JOIN chart_facts f
      ON f.fact_id = t.moon_fact_id
     AND f.chart_id = t.chart_id
     AND f.ayanamsha_id = t.ayanamsha_id
    WHERE f.fact_id IS NULL
       OR f.fact_value_num IS NULL
       OR t.natal_moon_longitude_deg IS DISTINCT FROM round(f.fact_value_num, 6)::float8
  )
  -- (e) §N.3 accretion detector: one chart has exactly one natal anchor. Rows from two builds
  -- against two L1 fact generations would show two anchors under one chart — something the
  -- natural key alone cannot see.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha
    GROUP BY chart_id
    HAVING count(DISTINCT moon_fact_id) <> 1 OR count(DISTINCT natal_moon_longitude_deg) <> 1
  )
  -- (f) B.10 / §N.6: the annual chart is a real cast, not an empty envelope — a JSON array of at
  -- least the nine grahas, each carrying a name, an in-range sign index and an in-range
  -- longitude. A truncated or placeholder payload is caught here rather than served.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    WHERE jsonb_typeof(t.graha_positions_jsonb) <> 'array'
       OR jsonb_array_length(t.graha_positions_jsonb) < 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t, jsonb_array_elements(t.graha_positions_jsonb) g
    WHERE (g->>'name') IS NULL
       OR (g->>'sign_idx')::int NOT BETWEEN 0 AND 11
       OR (g->>'longitude_deg')::float8 NOT BETWEEN 0 AND 360
  )
  -- (g) §N.7 item 3: the praveśa lagna label restates reference_signs, and its degree lies
  -- inside the sign it names.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    WHERE (SELECT s.canonical_name_en FROM reference_signs s
           WHERE s.sign_id = t.pravesha_lagna_sign_idx + 1)
            IS DISTINCT FROM t.pravesha_lagna_sign_name
       OR t.pravesha_lagna_degree < 0
       OR t.pravesha_lagna_degree >= 30
  )
  -- (h) §N.3 cardinality per group: a built chart's praveśa years form a contiguous run from
  -- year 1 — no hole, no year past the run. A coverage assertion, not a `count(*) = N` pin
  -- (C12/D-126): it holds for whatever horizon the writer's own constant sets.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha
    GROUP BY chart_id
    HAVING min(pravesha_year) <> 1 OR count(*) <> max(pravesha_year) - min(pravesha_year) + 1
  )
  -- (i) D-TIME sanity bound, derived not invented: a lunar-return year is one solar year
  -- (365.25 d) displaced by at most one lunar sidereal month (27.32 d) at each end, so every
  -- window spans between ~338 and ~393 days. The 180-degree false-root failure this writer's
  -- bracket strategy exists to avoid lands outside that band.
  AND NOT EXISTS (
    SELECT 1 FROM kala_tithi_pravesha t
    WHERE (t.window_end - t.window_start) < interval '338 days'
       OR (t.window_end - t.window_start) > interval '393 days'
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_tithi_pravesha';


-- ka_vedha_gochara
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_vedha_gochara integrity contract (D-CND-03: chart-partitioned, attribution-preserving).
-- Target table: kala_vedha_gochara. Its natural key (chart_id, ayanamsha_id, vedha_kind, graha,
-- window_start) is ALREADY a DB-level UNIQUE and the vedha_kind vocabulary / grid-field scoping
-- are ALREADY DB CHECKs, so none of those is restated here (D-CND-03 rule 4).
-- This is the one asset in its batch whose rows modulate a served number (the quality_gates
-- factor of the gochara_v3 lambda product), so its grounding labels and its classical geometry
-- are both load-bearing, not decorative.
SELECT
  -- (a) §N.7 item 4 — the honesty label must have a detector behind it. A sarvatobhadra row is
  -- uncited EXACTLY when its pair came from the algorithmic approximation rather than an
  -- ingested school grid. This is the invariant a future grid ingest is most likely to break.
  NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'sarvatobhadra'
      AND v.uncited_extension IS DISTINCT FROM (v.grid_basis = 'algorithmic_approximation')
  )
  -- (b) §N.6 — uncitedness stays confined to the approximated mechanism. house_vedha and latta
  -- are verse-cited by construction — an uncited row of either kind would be a cited-looking
  -- suppressor flagged as uncited, or the reverse, and either way mis-tiers the served row.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind <> 'sarvatobhadra' AND v.uncited_extension
  )
  -- (c) §N.5 L0-authority: every house_vedha row must correspond to a real, vedha-checkable
  -- bg_transit_rules row for that graha and primary house, and must restate that rule's own
  -- vedha_house and phala verbatim. A house_vedha row with no upstream rule is an invented
  -- suppressor — one that disagrees with its rule is L3 arbitrating over L0.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_transit_rules r
      ON r.rule_type = 'favourable' AND r.vedha_house IS NOT NULL
     AND r.graha = lower(v.graha)
     AND r.primary_house = (v.detail->>'primary_house')::int
    WHERE v.vedha_kind = 'house_vedha'
      AND (r.graha IS NULL
        OR (v.detail->>'vedha_house')::int IS DISTINCT FROM r.vedha_house
        OR (v.detail->>'phala') IS DISTINCT FROM r.phala)
  )
  -- (d) §N.5 L1-authority: the house geometry is re-derived from the natal Moon longitude fact
  -- the row itself cites. primary_house counts from the Moon's sign — vedha_sign_idx is the
  -- vedha house counted from that same sign. The fact id must resolve for THIS chart.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN chart_facts f
      ON f.fact_id = v.janma_reference_fact_id
     AND f.chart_id = v.chart_id
     AND f.ayanamsha_id = v.ayanamsha_id
    WHERE f.fact_id IS NULL
       OR f.fact_value_num IS NULL
       OR (v.vedha_kind = 'house_vedha'
           AND ((v.detail->>'primary_house')::int IS DISTINCT FROM
                 (((((v.detail->>'primary_sign_idx')::int - (floor(f.fact_value_num / 30.0)::int % 12))
                     % 12) + 12) % 12) + 1
             OR (v.detail->>'vedha_sign_idx')::int IS DISTINCT FROM
                 (((floor(f.fact_value_num / 30.0)::int % 12) + (v.detail->>'vedha_house')::int - 1) % 12)))
  )
  -- (e) §N.5 L1-authority, nakshatra axis: the sarvatobhadra target nakshatra and the latta
  -- janma nakshatra are the SAME single L1 Moon fact read two ways, never a second natal-Moon
  -- concept of the writer's own.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    JOIN chart_facts f
      ON f.fact_id = v.janma_reference_fact_id
     AND f.chart_id = v.chart_id
     AND f.ayanamsha_id = v.ayanamsha_id
    WHERE (v.vedha_kind = 'sarvatobhadra'
           AND (v.detail->>'target_nakshatra_idx')::int
               IS DISTINCT FROM (floor(f.fact_value_num / (360.0 / 27.0))::int % 27))
       OR (v.vedha_kind = 'latta'
           AND (v.detail->>'janma_nakshatra_idx')::int
               IS DISTINCT FROM (floor(f.fact_value_num / (360.0 / 27.0))::int % 27))
  )
  -- (f) §N.7 item 1 — the writer's stated construction rule for latta, made checkable: a latta
  -- row exists ONLY where the graha's latta point lands ON the janma nakshatra. The gochara_v3
  -- suppression path short-circuits its malefic-count branch on latta rows, so a latta row that
  -- is not a real janma hit mis-suppresses a served score.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'latta'
      AND (v.detail->>'latta_nakshatra_idx') IS DISTINCT FROM (v.detail->>'janma_nakshatra_idx')
  )
  -- (g) §N.5 L0-authority: a latta row restates bg_phaladeepika_latta's own counting parameters
  -- and citation for that graha. Ketu is absent from the L0 table by disclosed classical gap, so
  -- a Ketu latta row would surface here as an unresolved rule rather than pass silently.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_phaladeepika_latta l ON l.graha = v.graha
    WHERE v.vedha_kind = 'latta'
      AND (l.graha IS NULL
        OR (v.detail->>'count_from_graha')::int IS DISTINCT FROM l.count_from_graha
        OR (v.detail->>'direction') IS DISTINCT FROM l.direction
        OR v.classical_citation IS DISTINCT FROM l.source_citation)
  )
  -- (h) §N.7 item 1: malefic_count is a restatement of the array it summarises, not a second,
  -- independently-maintained number. The consumer grades off this count.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'house_vedha'
      AND (v.detail->>'malefic_count')::int
          IS DISTINCT FROM jsonb_array_length(v.detail->'malefic_obstructing_grahas')
  )
  -- (i) §N.5 + §N.7 item 6: the malefic effect grade is bg_vedha_malefic_scale's row for that
  -- count, verbatim, and it is present EXACTLY when the scale covers the count — never a
  -- plausible-sounding default standing in for a count the cited scale does not grade.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_vedha_malefic_scale s ON s.malefic_count = (v.detail->>'malefic_count')::int
    WHERE v.vedha_kind = 'house_vedha'
      AND (((v.detail->>'malefic_effect_grade') IS NOT NULL) <> (s.malefic_count IS NOT NULL)
        OR ((v.detail->>'malefic_effect_grade') IS NOT NULL
            AND ((v.detail->>'malefic_effect_grade') IS DISTINCT FROM s.effect_grade
              OR (v.detail->>'malefic_scale_citation') IS DISTINCT FROM s.source_citation)))
  )
  -- (j) classical vedha requires SIMULTANEOUS occupancy, so a recorded obstruction sub-window
  -- must lie inside the primary transit window it obstructs. A sub-window escaping its parent
  -- means the overlap arithmetic, not the astrology, is wrong.
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.detail->>'obstruction_window_start' IS NOT NULL
      AND ((v.detail->>'obstruction_window_start')::date < v.window_start
        OR (v.detail->>'obstruction_window_end')::date > v.window_end
        OR (v.detail->>'obstruction_window_end')::date < (v.detail->>'obstruction_window_start')::date)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_vedha_gochara';


-- ka_vighnakara
UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_vighnakara integrity contract  (target table: kala_obstruction)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. Each conjunct groups by
-- chart_id or evaluates a row that carries its own chart_id, so a corruption confined to one
-- chart makes that chart violate. No bare count equality pin anywhere (C12 / D-126).
SELECT
  -- (a) §N.3 cross-build accretion detector. kala_obstruction has ONLY a surrogate id PK and
  -- no natural-key UNIQUE, so this is its only accretion detector. The writer emits two row
  -- families with two natural keys (ka_vighnakara.py:236 and :275):
  --   convergence-anchored -> (chart_id, convergence_id, obstruction_type)
  --   dasha-anchored       -> (chart_id, signal_id, obstruction_type, detail peak_date)
  -- _detect_all returns at most one row per detector per peak, so both keys are unique.
  NOT EXISTS (
    SELECT 1 FROM kala_obstruction
    WHERE convergence_id IS NOT NULL
    GROUP BY chart_id, convergence_id, obstruction_type
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction
    WHERE convergence_id IS NULL
    GROUP BY chart_id, signal_id, obstruction_type, obstruction_detail->>'peak_date'
    HAVING count(*) > 1
  )
  -- (b) §N.5 upstream authority + the F-VIGHNA-4 cascade detector. The FK on convergence_id
  -- enforces existence but NOT chart agreement, so a row can point at another chart's window
  -- and the DB will accept it. Separately, kala_convergence's cascading FK action silently
  -- empties this table when ka_sangam re-runs, while asset_throughput still reports success
  -- (§N.8: the state flag's detector never checked that the rows survived). Second clause
  -- makes that emptying visible: every chart that has convergence windows must have
  -- obstruction rows.
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction o
    WHERE o.convergence_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM kala_convergence c
        WHERE c.convergence_id = o.convergence_id AND c.chart_id = o.chart_id
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM (SELECT DISTINCT chart_id FROM kala_convergence) k
    WHERE NOT EXISTS (SELECT 1 FROM kala_obstruction o WHERE o.chart_id = k.chart_id)
  )
  -- (c) §N.7 item 1: severity is a restatement of severity_score, not an independent grade --
  -- _SEVERITY_THRESHOLDS = [(0.70,'severe'), (0.40,'moderate'), (0.0,'mild')]
  -- (ka_vighnakara.py:81, applied at :106). A label that disagrees with the number it claims
  -- to summarise is exactly the grade-off-a-proxy defect §N.7 forbids.
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction
    WHERE severity IS DISTINCT FROM (
      CASE WHEN severity_score >= 0.70 THEN 'severe'
           WHEN severity_score >= 0.40 THEN 'moderate'
           ELSE 'mild' END)
  )
  -- (d) range guard the DB CHECKs cannot make: both columns are independently bounded to
  -- [0,1], but every detector derives override_score as severity_score times a factor in
  -- (0,1) (e.g. round(score * 0.45, 3) for malefic transit, ka_vighnakara.py:516). An
  -- override that exceeds its own severity, or is zero, is a suppression claim with no
  -- detector behind it (§N.8).
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction
    WHERE override_score <= 0.0 OR override_score > severity_score
  )
  -- (e) §N.7 item 2 + §N.5 attribution: each row must name, in its own provenance, which
  -- anchor path produced it, and a convergence-anchored row's detector must have run on the
  -- peak date of the window it is attributed to. The writer stamps
  -- 'ka_vighnakara:v2.0:conv=<id>' vs 'ka_vighnakara:v2.0:dasha_anchor' and sets
  -- detail.anchor='dasha_timeline' only on the second family (:273-284).
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction
    WHERE NOT (obstruction_detail ? 'peak_date')
       OR (convergence_id IS NOT NULL
           AND (source_citation <> 'ka_vighnakara:v2.0:conv=' || convergence_id::text
                OR (obstruction_detail->>'anchor') IS NOT NULL))
       OR (convergence_id IS NULL
           AND (source_citation <> 'ka_vighnakara:v2.0:dasha_anchor'
                OR (obstruction_detail->>'anchor') IS DISTINCT FROM 'dasha_timeline'))
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_obstruction o
    JOIN kala_convergence c
      ON c.convergence_id = o.convergence_id AND c.chart_id = o.chart_id
    WHERE (o.obstruction_detail->>'peak_date') IS DISTINCT FROM c.peak_date::text
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_vighnakara';


-- ka_yojaka  -- returns FALSE today: true positive, see header
UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_yojaka integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_activation_predicates.
  -- NO distinctness conjunct appears here: (chart_id, signal_id, ayanamsha_id) is ALREADY a DB
  -- UNIQUE index (idx_kap_chart_signal_ayan), so asserting it again could never fail and would
  -- breach C12's rewrite floor. Conjuncts (a) and (b) instead assert the two-way cardinality
  -- agreement with the L2 signal inventory, which no index can enforce.
  -- (a) §N.5 upstream authority. Every predicate must name a signal that still exists, for the
  -- SAME chart and the SAME ayanamsha. The table carries no foreign key, so a bo_laksana
  -- rebuild that re-issues signal_ids leaves the whole predicate set pointing at dead rows and
  -- nothing notices. Chart-partitioned by construction: today chart cb73cd3d violates this on
  -- 49,730 of its 49,875 rows while the other two charts are clean.
  NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.signal_id    = p.signal_id
        AND s.chart_id     = p.chart_id
        AND s.ayanamsha_id = p.ayanamsha_id)
  )
  -- (b) §N.5 coverage, the other direction. ka_yojaka's contract is one predicate per MSR
  -- signal, so for every chart it has built, every L2 signal must have a predicate. Detects a
  -- partial bind pass or a build that ran against a smaller signal set than the live one.
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s
    WHERE EXISTS (SELECT 1 FROM kala_activation_predicates q WHERE q.chart_id = s.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_activation_predicates p
        WHERE p.chart_id     = s.chart_id
          AND p.signal_id    = s.signal_id
          AND p.ayanamsha_id = s.ayanamsha_id)
  )
  -- (c) §N.6 item 3 / §N.7 item 6: an honest UNDATED must be REPORTED, not merely be empty.
  -- A predicate with no constituent_lords cannot ever be dated by any downstream engine, so it
  -- must carry the CR-37 always_on_reason saying why. RED today by design: 27,681 of 150,150
  -- rows are structurally undatable with no reason given (the discipline was implemented for
  -- 20 distribution-yoga rows and never generalised). A contract that passed before and after
  -- that fix would measure nothing.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE jsonb_array_length(
            COALESCE(dasha_eligibility_rule_jsonb->'constituent_lords','[]'::jsonb)) = 0
      AND (dasha_eligibility_rule_jsonb->>'always_on_reason') IS NULL
  )
  -- (d) §N.5 provenance: a predicate that DID resolve lords must say where they came from.
  -- A lord list with no constituent_lords_source is an unattributable claim (B.3).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE jsonb_array_length(
            COALESCE(dasha_eligibility_rule_jsonb->'constituent_lords','[]'::jsonb)) > 0
      AND (dasha_eligibility_rule_jsonb->>'constituent_lords_source') IS NULL
  )
  -- (e) B.3 derivation ledger must resolve and must not drift from the row it sits on.
  -- Every bg_transit_rules id the ledger cites must be a real L0 rule row -- the ledger must
  -- carry its ratified_by and template_version -- and that template_version must equal the
  -- row's own column (a wrapper-local copy that can drift from its source is §N.7 item 3).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    CROSS JOIN LATERAL jsonb_array_elements_text(
      COALESCE(p.derivation_ledger_jsonb->'bg_transit_rules_ids','[]'::jsonb)) AS r
    WHERE NOT EXISTS (SELECT 1 FROM bg_transit_rules b WHERE b.id::text = r)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE (derivation_ledger_jsonb->>'ratified_by') IS NULL
       OR (derivation_ledger_jsonb->>'template_version') IS DISTINCT FROM template_version
  )
  -- (f) payload presence guard: all four jsonb payloads are NOT NULL at the schema level but
  -- nothing stops an empty object, which serves as a populated-looking hollow envelope
  -- (§N.6 item 3). Every predicate must actually carry its four declarations.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE dasha_eligibility_rule_jsonb   = '{}'::jsonb
       OR transit_trigger_jsonb          = '{}'::jsonb
       OR strength_affliction_hook_jsonb = '{}'::jsonb
       OR derivation_ledger_jsonb        = '{}'::jsonb
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_yojaka';


-- ── 2. Achieved-count floors (§N.4) ──────────────────────────────────────────
-- Measured on the canonical chart 482012f1 this session. Floors are ACHIEVED counts,
-- never aspirations, and never fabricated upward. Deliberately NOT taken from chart
-- cb73cd3d, whose L3 tables are cascade-damaged — using it would set floors far below
-- what the writers actually produce.

UPDATE asset_registry SET target_floor = 1169 WHERE asset_id = 'ka_avadhi';
UPDATE asset_registry SET target_floor = 100 WHERE asset_id = 'ka_bhavishya_lekha';
UPDATE asset_registry SET target_floor = 83 WHERE asset_id = 'ka_gochara';
UPDATE asset_registry SET target_floor = 762 WHERE asset_id = 'ka_gochara_resonance';
UPDATE asset_registry SET target_floor = 16297 WHERE asset_id = 'ka_gochara_sweep';
UPDATE asset_registry SET target_floor = 914 WHERE asset_id = 'ka_gochara_v3_century_materialize';
UPDATE asset_registry SET target_floor = 100 WHERE asset_id = 'ka_jivana_parva';
UPDATE asset_registry SET target_floor = 750 WHERE asset_id = 'ka_kala_darshana';
UPDATE asset_registry SET target_floor = 335403 WHERE asset_id = 'ka_kalasutra';
UPDATE asset_registry SET target_floor = 588 WHERE asset_id = 'ka_kota_chakra';
UPDATE asset_registry SET target_floor = 8599775 WHERE asset_id = 'ka_kshetra';
UPDATE asset_registry SET target_floor = 72 WHERE asset_id = 'ka_moorti_nirnaya';
UPDATE asset_registry SET target_floor = 14868 WHERE asset_id = 'ka_sangam';
UPDATE asset_registry SET target_floor = 120 WHERE asset_id = 'ka_sudarshana_varsha';
UPDATE asset_registry SET target_floor = 92412 WHERE asset_id = 'ka_taranga';
UPDATE asset_registry SET target_floor = 120 WHERE asset_id = 'ka_tithi_pravesha';
UPDATE asset_registry SET target_floor = 176 WHERE asset_id = 'ka_vedha_gochara';
UPDATE asset_registry SET target_floor = 536 WHERE asset_id = 'ka_vighnakara';
UPDATE asset_registry SET target_floor = 50104 WHERE asset_id = 'ka_yojaka';


-- ── 3. Volume expectations (D-CND-01) ────────────────────────────────────────
-- Set where a formula is genuinely DERIVABLE from the writer's own arithmetic. Where it
-- is not — because the fan-out multiplier is an ephemeris search result rather than a
-- countable row set — the honest record is the achieved-count floor above plus a stated
-- reason, NOT a curve fitted to three charts. D-CND-01 requires a derived formula where a
-- count equality is the volume assertion; none of these contracts uses one.

UPDATE asset_registry
   SET expected_volume_formula = $ck$
rows_per_chart = DEFAULT_MAX_VARSHA_YEAR * ayanamshas
$ck$,
       expected_volume_inputs  = $ck$
{
  "DEFAULT_MAX_VARSHA_YEAR": 120,
  "ayanamshas": 1,
  "source": "services/ka_sudarshana_varsha/logic.py"
}
$ck$::jsonb,
       volume_explanation      = $ck$
Derived constant, not a count pin: the writer loops range(1, DEFAULT_MAX_VARSHA_YEAR+1) at a single canonical ayanamsha, with no ephemeris, no rolling horizon and no chart-dependent gating. Raising the horizon would keep the contract green, which a count(*)=120 pin would not (C12/D-126).
$ck$
 WHERE asset_id = 'ka_sudarshana_varsha';

UPDATE asset_registry
   SET expected_volume_formula = $ck$
rows_per_chart = DEFAULT_MAX_PRAVESHA_YEAR * ayanamshas
$ck$,
       expected_volume_inputs  = $ck$
{
  "DEFAULT_MAX_PRAVESHA_YEAR": 120,
  "ayanamshas": 1,
  "source": "services/ka_tithi_pravesha/logic.py"
}
$ck$::jsonb,
       volume_explanation      = $ck$
Derived constant, not a count pin, on the same basis as ka_sudarshana_varsha: one row per pravesha year over a full lifespan at a single canonical ayanamsha. Each row costs two lunar-return root-finds plus one annual chart cast.
$ck$
 WHERE asset_id = 'ka_tithi_pravesha';

UPDATE asset_registry
   SET expected_volume_formula = $ck$
rows(chart) = months * (n_domains + n_event_classes), months = 12 * (year(_WAVEFORM_END) - year(_WAVEFORM_START)) + 12
$ck$,
       expected_volume_inputs  = $ck$
{
  "months": 1812,
  "_WAVEFORM_START": "1950-01-01",
  "_WAVEFORM_END": "2100-12-01",
  "n_domains": "|GRAHA_DOMAINS union brahma_event_ontology.domain for this chart's bodha_pratijna rows|",
  "n_event_classes": "|distinct bodha_pratijna.event_class_id for this chart at lahiri_chitrapaksha|",
  "measured_canonical": "1812 * (24 + 27) = 92412"
}
$ck$::jsonb,
       volume_explanation      = $ck$
Derived and exact on the canonical chart. NOTE the L3-W2 SPLIT verdict: the event_class half is a degenerate duplicate of kala_field's axis (its dasha term takes ONE distinct value across 48,924 rows, re-measured on all three charts), so n_event_classes contributes volume without contributing information.
$ck$
 WHERE asset_id = 'ka_taranga';


-- ── 4. M6 — ka_gochara's count_sql counts another writer's rows ───────────────
--
-- count_sql counted 943 gen-3.0 rows in kala_gochara_windows. ka_gochara's writer targets
-- kala_gochara_windows_v2 at generation '2.0' and produced 83 rows on the canonical chart; the
-- gen-3.0 rows belong to ka_gochara_v3_century_materialize. The cockpit's stats route reads
-- count_sql (the L1 trap, CLAUDE.md §N.4 cockpit-truth), so this asset has been reporting a
-- volume it never wrote, attributed from a sibling.
UPDATE asset_registry
   SET count_sql = 'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation=''2.0'''
 WHERE asset_id = 'ka_gochara';

-- ── 5. N9 — stale DRAFT labels ───────────────────────────────────────────────
--
-- 11 L3 assets carry catalog_status='DRAFT' (7 artifact + 4 service) while CLAUDE.md §E records
-- L3 as CLOSED and real serving code depends on them. The cockpit filters on catalog_status
-- (migration 294's own root-cause note), so three sealed layers are invisible in the operator
-- surface. Cross-layer measurement and mechanism: issue #1753 (L2).
--
-- TEN of the eleven flip. ka_graha_sancara deliberately does NOT: its probe genuinely fails
-- (two real defects fixed in W3 M3, not yet deployed), and marking a broken service CURRENT in a
-- hygiene sweep would be exactly the unearned green signal §N.8 forbids — introduced, ironically,
-- by a tidiness pass. It flips when M3 deploys and its probe is green.
UPDATE asset_registry
   SET catalog_status = 'CURRENT'
 WHERE asset_id IN (
   'ka_bhavishya_lekha','ka_jivana_parva','ka_kala_darshana','ka_kalasutra','ka_sangam',
   'ka_vighnakara','ka_yojaka',            -- the 7 artifact assets
   'ka_dasha_kala','ka_muhurta_seva','ka_tulana'  -- 3 of the 4 services
 );
