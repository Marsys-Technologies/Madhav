-- 861_nirmana_l3_w3_gochara_resonance_expected_volume.sql
--
-- NIRMĀṆA L3 Kāla — W3. Closes F-L3-4 for `ka_gochara_resonance`: `expected_volume_formula`,
-- `expected_volume_inputs` and `volume_explanation` were all NULL, leaving the already-correct
-- `target_floor` (762, an achieved-count floor per §N.4, unchanged by this migration) an
-- undocumented constant rather than a derived, auditable figure (C12: "derive, never pick").
--
-- No self-transaction wrapper (transaction ownership belongs to platform/scripts/migrate.ts,
-- matching migration 670/850/852-860's convention for this range).
--
-- Scoped strictly to the F-L3-4 volume-documentation task: this migration does NOT touch this
-- asset's W4 dispatch, which remains correctly HELD per D-CND-26 (true closure includes unfrozen
-- L1 ancestors -- see L3_STATE.md Held items), and does NOT touch `depends_on` (campaign-wide
-- IMMUTABLE per D-CND-09/#1744 -- see `DAG_CORRECTIONS_REGISTER_v1_0.md`, where L3's audit is
-- already ✅ COMPLETE). Documenting row volume is independent of both.
--
-- `ka_gochara_resonance` (services/ka_gochara_resonance/writer.py) is NOT a flat count. Derived
-- here from the writer's own module docstring + code, not guessed: one row per (event_class,
-- target_type, matched instance) across 27 canonical `brahma_event_ontology` event classes x 8
-- `target_type` values, each computed by a DIFFERENT method:
--
--   bhava / lord / karaka        -- read straight from brahma_event_ontology.signature_model per
--                                   event class (BPHS-cited, uncited_extension=False). "Sparse
--                                   signature_models produce fewer rows, not fabricated ones"
--                                   (writer.py:99) -- these three counts are exactly as rich as
--                                   the 27 classes' own seeded signature depth, not a fixed count
--                                   per class.
--   mechanism_node                -- bg_transit_rules rows whose (graha, house) match an event
--                                   class's karaka(s)/house(s) (uncited_extension=False, citation
--                                   copied verbatim from bg_transit_rules).
--   sensitive_degree / arudha /
--   yoga_constituent /
--   dasha_lord_portfolio           -- THIS WRITER'S OWN SYNTHESIS, connecting an event_class to a
--                                   chart-specific L1 primitive (chart_facts sensitive-degree/
--                                   arudha rows, ga_yoga_firings, chart_dashas MD lords) that is
--                                   not itself keyed to that event_class in the source data --
--                                   uncited_extension=True for all four, deliberately no
--                                   classical_citation (B.10: never dress an inferred linkage up
--                                   as classically cited just because the underlying primitive
--                                   happens to carry a citation elsewhere for itself).
--
-- The row count is therefore native-chart-specific across all four synthesis target_types (how
-- many sensitive-degree/arudha/yoga-firing/dasha-lord rows THIS chart happens to have, matched
-- against 27 event classes' relevance criteria) and seed-depth-dependent for the three
-- signature_model-sourced types -- not reducible to one closed-form arithmetic identity.
--
-- Live-measured for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa), re-verified this
-- cycle via `count(*) FROM gochara_resonance_map WHERE chart_id=... GROUP BY target_type`:
--   yoga_constituent        220
--   sensitive_degree        176
--   mechanism_node           93
--   arudha                   68
--   bhava                    68
--   lord                     49
--   dasha_lord_portfolio     44
--   karaka                   44
--   ---------------------------
--   TOTAL                   762   (matches target_floor and count_sql exactly)
--
-- Per migration 690/852-860's own recorded practice: this formula is intentionally
-- prose+structured-inputs, not a `COUNT()`/`ACTUAL()`/arithmetic literal the seed's
-- `validateFormulas` parser accepts, because the real computation spans 8 independently-derived
-- target_types across 27 event classes and is chart- and seed-data-dependent throughout. This
-- migration does not touch the seed; the row is DB-authoritative and seed-divergent in the same
-- documented, already-flagged way migration 690's six rows (and migrations 852-860's rows) are.

UPDATE asset_registry
   SET expected_volume_formula = 'SUM_OVER_27_EVENT_CLASSES_AND_8_TARGET_TYPES(matched instances), not a flat count',
       expected_volume_inputs = jsonb_build_object(
         'kind', 'multi_source_event_class_resonance_count',
         'chart_scoped', true,
         'event_class_count', 27,
         'target_types', jsonb_build_object(
           'from_signature_model', jsonb_build_array('bhava', 'lord', 'karaka'),
           'from_bg_transit_rules', jsonb_build_array('mechanism_node'),
           'writer_own_synthesis_uncited', jsonb_build_array('sensitive_degree', 'arudha', 'yoga_constituent', 'dasha_lord_portfolio')
         ),
         'per_row', 'one row per (event_class, target_type, matched instance). signature_model-sourced types are as rich as each class''s own seeded depth, synthesis types are as rich as this chart''s own matching L1 rows',
         'derivation', 'derived from services/ka_gochara_resonance/writer.py directly, not guessed, and not reducible to one closed-form arithmetic expression because 4 of the 8 target_types are chart-specific synthesis counts and the other 3 depend on each event class''s own seeded signature_model depth',
         'observed_2026_09_07', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', jsonb_build_object(
             'yoga_constituent', 220, 'sensitive_degree', 176, 'mechanism_node', 93,
             'arudha', 68, 'bhava', 68, 'lord', 49, 'dasha_lord_portfolio', 44, 'karaka', 44, 'total', 762
           )
         ),
         'supersedes', 'NULL (F-L3-4)'
       ),
       volume_explanation = 'Not a flat count: one row per (event_class, target_type, matched instance) across 27 canonical event classes and 8 target_types. 3 target_types (bhava/lord/karaka) are as rich as each class''s own seeded brahma_event_ontology signature_model depth. 1 (mechanism_node) matches bg_transit_rules. 4 more (sensitive_degree/arudha/yoga_constituent/dasha_lord_portfolio) are this writer''s own uncited synthesis, chart-specific counts against this native''s own L1 data. 762 is the live-measured count for the canonical chart, matching target_floor and count_sql exactly, not an invented figure.'
 WHERE asset_id = 'ka_gochara_resonance'
   AND expected_volume_formula IS NULL;
