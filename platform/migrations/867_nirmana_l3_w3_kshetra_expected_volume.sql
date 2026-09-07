-- 867_nirmana_l3_w3_kshetra_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_kshetra`, the LAST of the 20 originally-NULL L3
-- assets: `expected_volume_formula`, `expected_volume_inputs` and `volume_explanation` were all
-- NULL, leaving the already-correct `target_floor` (8,599,775, an achieved-count floor per §N.4,
-- unchanged by this migration) an undocumented constant rather than a derived, auditable figure
-- (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-866's convention for this range).
--
-- `ka_kshetra` (services/ka_kshetra/, 14,000+ lines across ~25 files: stage0_kinematics through
-- stage8_spec, submodular selection, hazard, uncertainty, dhara sweep/matrix/null modules) is the
-- layer's largest and most numerically complex asset by a wide margin. Its ROW-COUNT shape,
-- though, turned out to be far simpler than its scoring internals -- the same "separate the count
-- from the computation" split that closed `ka_gochara_v3_century_materialize` (migration 865) and
-- `ka_sangam` (migration 866):
--
--   `kala_field` stores a PIECEWISE-LINEAR log-hazard field per (chart, event_class), one row per
--   SEGMENT. Segment boundaries are the `breakpoints()` of an `EnvelopeIndex`
--   (services/ka_kshetra/stage4_field.py:668-666) -- "every envelope knot. Placing a breakpoint at
--   each is what makes the stored log-linear field FAITHFUL to the piecewise-linear covariates
--   rather than an approximation of them" (quoted from the method's own docstring). `build_segments`
--   then optionally subdivides further via adaptive refinement (`integrator.build_segments`,
--   `max_depth`/`tau` parameters) -- but **live-verified: `refinement_depth` is 0 for EVERY one of
--   the 8,599,775 rows for this chart** -- the adaptive refinement pass never actually subdivided
--   anything; the served segmentation IS the raw breakpoint set for every event class.
--
--   **The key structural finding**: segment count is IDENTICAL across every one of this chart's 25
--   discovered event classes (25, not the full 27 -- `_discover_event_classes`,
--   writer.py:314, is itself chart-specific dynamic discovery, per the shared MR-16 convention
--   already documented for `ka_gochara_v3_century_materialize`) -- exactly 343,991 rows each,
--   confirmed live via `GROUP BY event_class`. This means the breakpoint set (`self.supportive +
--   self.obstructive` primitive knots) is effectively CHART-WIDE, not event-class-specific: the
--   same underlying transit/dasha/yoga knot structure over the `HORIZON_DAYS = 36525.0` (100-year)
--   window feeds every domain's field, and only the alpha/gamma/lambda VALUES at each segment (not
--   the segment BOUNDARIES) differ by event_class. So:
--
--     row_count(ka_kshetra) = 25 (this chart's discovered event classes) x 343,991 (breakpoint-
--     derived segments, chart-wide, class-invariant)
--
--   The internal mechanics of WHY 343,991 breakpoints exist (which specific primitives' knot
--   density over 100 years produces that exact figure) are NOT further decomposed in this
--   migration -- doing so honestly would require enumerating every constituent primitive's own
--   knot generation across the full stage0-stage8 pipeline, a substantially larger undertaking
--   than this migration's own F-L3-4 scope. What IS established, live-verified rather than
--   guessed: the multiplication itself is exact and the per-class uniformity is real, not
--   coincidental (confirmed via all 25 classes, not a sample).
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_field WHERE chart_id=... GROUP BY event_class` (25 distinct
-- classes, each exactly 343,991, `refinement_depth` 0 for all rows):
--   25 x 343,991 = 8,599,775   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852-866's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the per-class segment count is itself a numerical
-- consequence of the chart's own primitive knot density over a 100-year horizon, not an
-- arithmetic identity the seed's grammar could express. This migration does not touch the seed;
-- the row is DB-authoritative and seed-divergent in the same documented, already-flagged way
-- migration 690's six rows (and migrations 852-866's rows) are.

UPDATE asset_registry
   SET expected_volume_formula = 'discovered_event_class_count x chart_wide_breakpoint_segment_count (class-invariant, refinement_depth=0 for every row)',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'class_invariant_breakpoint_segmentation_count',
         'chart_scoped', true,
         'event_classes', jsonb_build_object(
           'source', '_discover_event_classes (writer.py:314), chart-specific dynamic discovery per the MR-16 convention (shared with ka_gochara_v3_century_materialize)',
           'observed_count', 25
         ),
         'segments_per_class', jsonb_build_object(
           'source', 'EnvelopeIndex.breakpoints() (stage4_field.py), union of every supportive/obstructive primitive knot over HORIZON_DAYS=36525.0 (100 years)',
           'class_invariant', true,
           'note', 'identical across all 25 discovered event classes for this chart (343991 each), confirmed live for every class, not a sample. Indicates the breakpoint set itself is chart-wide/transit-derived, and only the alpha/gamma/lambda VALUES at each segment differ by class, not the segment boundaries',
           'adaptive_refinement', 'build_segments supports further subdivision (max_depth/tau), but refinement_depth=0 for every one of this chart''s 8,599,775 rows. No adaptive subdivision actually fired',
           'observed_count', 343991
         ),
         'derivation', 'derived from services/ka_kshetra/stage4_field.py directly, not guessed. The multiplication (25 x 343991) is exact and live-verified. The internal mechanics of why 343991 breakpoints exist are not further decomposed in this migration, since that would require enumerating every constituent primitive''s own knot generation across the full stage0-stage8 pipeline',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'event_classes', 25, 'segments_per_class', 343991, 'total', 8599775
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'A class-invariant multiplication: 25 discovered event classes (chart-specific, MR-16 dynamic discovery) x 343991 breakpoint-derived segments each (identical across every class, confirmed live, not a sample). The segment BOUNDARIES are chart-wide/transit-derived, only the field VALUES differ by domain. refinement_depth is 0 for every one of the 8,599,775 rows, confirming the served segmentation is the raw breakpoint set with no adaptive subdivision. The internal knot-density mechanics behind 343991 are not further decomposed here. 8,599,775 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_kshetra'
   AND expected_volume_formula IS NULL;
