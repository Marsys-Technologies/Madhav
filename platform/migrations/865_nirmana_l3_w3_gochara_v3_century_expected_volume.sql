-- 865_nirmana_l3_w3_gochara_v3_century_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_gochara_v3_century_materialize`: this asset was
-- deferred in the immediately preceding cycles as "too large for one bounded unit" (2480-line
-- writer). This migration is the result of investing the reading this cycle: the writer's own
-- ROW-COUNT shape is genuinely tractable even though its intensity-scoring internals are not --
-- the two are separable, and only the former is this migration's concern. `expected_volume_formula`
-- / `expected_volume_inputs` / `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (914, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-864's convention for this range).
--
-- Derived from `services/gochara_v3/resolution_hierarchy.py` directly (the shared peak-anchoring
-- module this writer calls), not guessed. **Correction, self-caught during this migration's own
-- authoring:** a first draft wrongly generalised the flat (era/point-canonical) tier's row count
-- to a uniform "10 per class" from an incomplete first query; re-running the FULL, untruncated
-- per-(event_class, resolution) breakdown live showed the flat tier is genuinely per-class
-- variable (10, 30, or 40), not a constant -- caught before committing, corrected here with the
-- real numbers:
--
--   FLAT tier (R8.12 shape gate: event classes whose brahma_event_ontology.temporal_shape is
--   'point', i.e. NOT interval/chain) -- "the PRE-MR-11(b) flat production: one row per
--   find_threshold_crossings interval, resolution column NULL" (writer.py module docstring,
--   R8.12). Row count per class = however many threshold-crossing intervals THAT class's own
--   transit pattern produces over the century horizon for THIS chart -- genuinely class- and
--   chart-specific, not a fixed cap. 18 of the 27 canonical event classes take this path for the
--   canonical chart; live counts observed range 10-40 per class (see below).
--
--   ERA/MONTH/DAY hierarchy (the other 9 classes, temporal_shape 'interval'/'chain'): ERA tier is
--   the SAME "one row per find_threshold_crossings interval" as the flat tier above (just also
--   carrying `resolution='era'` and feeding the next stage) -- coincidentally exactly 10 for all
--   9 of these classes on this chart, not a hard-coded constant (no `MAX_ERA_WINDOWS`-style
--   constant exists in resolution_hierarchy.py; left honestly unresolved whether this uniformity
--   is structural or chart-specific coincidence, per §N.7). For EACH era window, up to
--   `MAX_PEAKS_PER_ERA_WINDOW = 3` (resolution_hierarchy.py:105) local-maximum peaks are admitted
--   (gated on that era window's OWN P90, `ADMISSION_PERCENTILE = 90.0`) and greedily retained,
--   pooled across all era windows per MR-44 (min separation `MIN_PEAK_SEPARATION_DAYS = 90.0`, so
--   the same real-world peak is never double-counted from two sibling era windows).
--   `_emit_retained_peaks` (resolution_hierarchy.py:680-712) then emits "exactly one month row +
--   one day row per peak" (quoted from its own docstring) -- so month_rows = day_rows =
--   SUM_OVER_ERA_WINDOWS(peaks retained, capped at 3 each). 8 of the 9 hierarchy classes hit the
--   full 10x3=30 month/day cap; `psychological_arc` retains only 27 of 30 possible slots (an
--   honest under-cap result -- fewer real peaks cleared admission/separation for that class, not
--   an error).
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM kala_gochara_windows_v2 WHERE chart_id=... AND generation LIKE 'g3_%'
-- GROUP BY event_class, resolution` (27 event classes, 45 distinct groups):
--   FLAT tier, 18 classes: 13 classes x 10, 4 classes x 30, 1 class (education_milestone) x 40
--     = 130 + 120 + 40                                                                     = 290
--   HIERARCHY, 9 classes: era 10 x 9 = 90; month+day: 8 classes x (30+30)=480, plus
--     psychological_arc (27+27)=54                                                          = 624
--   -----------------------------------------------------------------------------------------
--   TOTAL                                                                                    914
--   (matches target_floor and count_sql -- which filters generation LIKE 'g3_%' -- exactly)
--
-- Per migration 690/852-864's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation is shape-gated per event class
-- and threshold-crossing/peak-detection-dependent per class and era window. This migration does
-- not touch the seed; the row is DB-authoritative and seed-divergent in the same documented,
-- already-flagged way migration 690's six rows (and migrations 852-864's rows) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_27_EVENT_CLASSES(threshold_crossing_intervals, shape_gated month/day refinement for 9 of them), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'peak_anchored_era_month_day_hierarchy_count',
         'chart_scoped', true,
         'shape_gate', 'R8.12: month/day tiers produced ONLY for event classes whose temporal_shape is interval or chain (9 of 27 for this chart). The other 18 get the flat, pre-hierarchy production instead',
         'flat_and_era_tier', jsonb_build_object(
           'per_row', 'one row per find_threshold_crossings interval for that event class over the century horizon, genuinely class- and chart-specific, not a fixed count',
           'observed_range_2026_09_07', '10 to 40 rows per class',
           'note', 'the 9 hierarchy classes'' era-tier count happens to be uniformly 10 on this chart. Not traced to a hard-coded cap, left honestly unresolved whether that is structural or coincidental'
         ),
         'month_and_day_tiers', jsonb_build_object(
           'gate', 'MAX_PEAKS_PER_ERA_WINDOW = 3 (resolution_hierarchy.py:105), admission on ADMISSION_PERCENTILE = 90.0 per era window, pooled greedy retention at MIN_PEAK_SEPARATION_DAYS = 90.0 (MR-44)',
           'per_row', '_emit_retained_peaks emits exactly one month row and one day row per retained peak (quoted from its own docstring)',
           'cap_per_class', 'up to era_row_count x 3 month rows and the same number of day rows. Not every class hits the full cap (psychological_arc retains 27 of a possible 30)'
         ),
         'derivation', 'derived from services/gochara_v3/resolution_hierarchy.py directly, not guessed, and not reducible to one closed-form arithmetic expression because both the flat/era interval count and the peak admission/retention are genuinely chart- and class-data-dependent',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'flat_classes', 18, 'flat_rows', 290,
             'hierarchy_classes', 9, 'hierarchy_era_rows', 90,
             'hierarchy_month_rows', 267, 'hierarchy_day_rows', 267,
             'total', 914
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: 18 of 27 event classes serve one row per find_threshold_crossings interval only (chart- and class-specific, observed 10-40 rows per class). The other 9 (interval/chain-shaped) additionally get up to 3 peak-anchored month rows and 3 day rows per era window (MAX_PEAKS_PER_ERA_WINDOW), genuinely data-dependent per era window (one class retains fewer than the cap). 914 is the live-measured count for the canonical chart (290 flat + 90 era + 267 month + 267 day), matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_gochara_v3_century_materialize'
   AND expected_volume_formula IS NULL;
