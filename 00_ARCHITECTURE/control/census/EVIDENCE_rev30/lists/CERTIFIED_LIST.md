# CERTIFIED_LIST
bar: N-268 (named ceilings and disclosure gaps); registry revision 30 (fingerprint b1acb3f678b5); layers L0,L1,L2; date 2026-10-13; tool 7e63cc872; 77 of 82 assets certified
Measured on: full census of an evaluation copy of production, backup 1791868791537 taken 2026-10-13T05:21:32.951Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.
ceilings: 69 of 77 certified assets are at a declared ceiling (Carr: single-derivation 45; D1: unverified transcription 20; both 0; Ldgr: unsourced (declared) 3; Ratified judgment (N-235) 4)
Carr.D2: ruled N/A (no per-witness values stored, N-156) on 76 of 82 assets; ruled N/A under another rule 6 on the rest
Build.completion counts only (no integrity statement): 0 of 82 assets

| asset | revision | census file | measured PASS | ruled N/A | date | ceilings | known limitations | known findings |
|---|---|---|---|---|---|---|---|---|
| bg_class_lifetime_counts | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Ratified judgment (N-235) |  |  |
| bg_class_priors | 30 | census_L0.json#7f9c53786923 | 13 | 12 | 2026-10-13 | Ldgr: unsourced (declared); Ratified judgment (N-235) |  |  |
| bg_cohort | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_compendium_index | 30 | census_L0.json#7f9c53786923 | 18 | 5 | 2026-10-13 | Carr: single-derivation |  | 1602 of 9571 rows have no chapter number and 7969 have no topic id, so the only usable key is the expression index with COALESCE defaults. |
| bg_concordance | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_dasha_systems | 30 | census_L0.json#7f9c53786923 | 14 | 10 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_dignity_reference | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_doshas | 30 | census_L0.json#7f9c53786923 | 13 | 10 | 2026-10-13 | D1: unverified transcription |  | 53 of 79 rows carry a placeholder citation; decision OS-2026-10-05-CITATIONS (not yet applied in the seed) sources 14 to a verified text, relabels 18 as modern practice, removes 13, and leaves 8 marked 'classical source claimed, not verified in our library'. |
| bg_ephemeris | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_ephemeris_engine | 30 | census_L0.json#7f9c53786923 | 5 | 19 | 2026-10-13 |  |  |  |
| bg_formula_constants | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Ratified judgment (N-235) |  |  |
| bg_ghatana | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Ratified judgment (N-235) |  |  |
| bg_gochara_arcs | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_gochara_citation_resolution | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  | It has no writer: its 14 rows were seeded by migrations 565, 630 and 631, so a build cannot regenerate them. |
| bg_kota_chakra_rings | 30 | census_L0.json#7f9c53786923 | 11 | 14 | 2026-10-13 | D1: unverified transcription; Ldgr: unsourced (declared) |  | The ring partition is a secondary-source transcription not traced to a primary text, the source is not held in the corpus (owner deferral N-102), and dvara_assignment is never filled. |
| bg_kp_sublord_division | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_medical_mappings | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_muhurta_lattice | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_nakshatra | 30 | census_L0.json#7f9c53786923 | 12 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_nakshatra_medical | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_ontology | 30 | census_L0.json#7f9c53786923 | 12 | 12 | 2026-10-13 | D1: unverified transcription |  | 53 of 741 rows carry a placeholder source citation (the dosha rows); decision OS-2026-10-05-CITATIONS (not yet applied) sources 14, relabels 18 modern, removes 13, leaves 8 'classical source claimed, not verified'; all 79 dosha rows have an empty alias set. |
| bg_panchanga | 30 | census_L0.json#7f9c53786923 | 5 | 19 | 2026-10-13 |  |  |  |
| bg_parihara_rules | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_phaladeepika_latta | 30 | census_L0.json#7f9c53786923 | 16 | 9 | 2026-10-13 |  |  | The per-row source citation names page PG339 only on all 8 rows although the passage spans PG338 and PG339, and the text is OCR English that has not been checked against the printed book. |
| bg_prashna_rules | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_reference | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_remedies | 30 | census_L0.json#7f9c53786923 | 19 | 5 | 2026-10-13 | D1: unverified transcription |  | 101 of 341 rows carry a placeholder citation; decision OS-2026-10-05-CITATIONS (not yet applied) sources 30 to BPHS, relabels 45 modern practice, removes 25, leaves 1 'classical source claimed, not verified'; 167 prescription sentences are fixed text. |
| bg_rules | 30 | census_L0.json#7f9c53786923 | 16 | 7 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_sign_medical | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_sky_calendar | 30 | census_L0.json#7f9c53786923 | 14 | 10 | 2026-10-13 |  |  |  |
| bg_text_index | 30 | census_L0.json#7f9c53786923 | 12 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_texts | 30 | census_L0.json#7f9c53786923 | 12 | 11 | 2026-10-13 | D1: unverified transcription |  | content_en is a machine translation (SS ruling 2026-10-06, not recorded by the writer, which stores the PDF chunk text), the chunk text is cut by character budget without a passage-level check, and verse_ref, content_sha256 and tradition_school are composed fields, so the extraction is declared an unverified transcription. |
| bg_transit_engine | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_transit_rules | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  | Six Rahu/Ketu house-vedha rows: vedha partner unsourced, pending owner ruling ND-NODE-VEDHA (transit result cites Phaladeepika XXVI); 19 rows cite BPHS Ch.29, which the corpus cannot resolve; 7 double_transit rows come from a migration. |
| bg_vastu_directions | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 | D1: unverified transcription |  | 1 of 8 rows carries a placeholder citation (decision OS-2026-10-05-CITATIONS sources it to Muhurta Chintamani v.9, not yet applied); the 7 sibling rows cite Mayamata Ch.6, a text not in the corpus. |
| bg_vedha_malefic_scale | 30 | census_L0.json#7f9c53786923 | 18 | 7 | 2026-10-13 |  |  | All five rows carry an editorial note (page PG349 disambiguation) added to the effect description that is not in the book text, and the source chunk for page PG353 has not been exported for checking. |
| bg_vidhi_floors | 30 | census_L0.json#7f9c53786923 | 13 | 11 | 2026-10-13 |  |  |  |
| bg_vidhi_primitives | 30 | census_L0.json#7f9c53786923 | 12 | 12 | 2026-10-13 |  |  |  |
| bg_yogas | 30 | census_L0.json#7f9c53786923 | 14 | 10 | 2026-10-13 | D1: unverified transcription |  | 1 of 233 rows carries a placeholder citation: decision OS-2026-10-05-CITATIONS labels kala_sarpa_yoga modern practice (not yet applied); it duplicates the dosha-form authority in ga_structural. |
| bo_anveshana | 30 | census_L2.json#c7b49c719c34 | 19 | 5 | 2026-10-13 | Carr: single-derivation |  | The constituent_refs key is called signal_ids but also holds L1 fact ids after the signal id, so the key is mislabelled for those entries. |
| bo_arudha | 30 | census_L2.json#c7b49c719c34 | 18 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_bimba | 30 | census_L2.json#c7b49c719c34 | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | On the native chart some yoga and dosha node names are computed status words, such as Dosha node: afflicted and Yoga node: true, standing as names. |
| bo_cdlm_summary | 30 | census_L2.json#c7b49c719c34 | 19 | 5 | 2026-10-13 | Carr: single-derivation |  | The summary sentence is the same fixed text for every chart, and a count of one reads over 1 cells. |
| bo_cgm_motifs | 30 | census_L2.json#c7b49c719c34 | 19 | 5 | 2026-10-13 | Carr: single-derivation |  | The motif definition sentences are identical on every row and not derived from the row. |
| bo_cgm_paths | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_chart_gestalt | 30 | census_L2.json#c7b49c719c34 | 18 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_drishti | 30 | census_L2.json#c7b49c719c34 | 14 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_grounding | 30 | census_L2.json#c7b49c719c34 | 15 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_karanajala | 30 | census_L2.json#c7b49c719c34 | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | Argala sentences use a fixed th suffix, so the second house reads 2th instead of 2nd. |
| bo_nakshatra_semantic | 30 | census_L2.json#c7b49c719c34 | 18 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_pramana_mapa | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_pratijna | 30 | census_L2.json#c7b49c719c34 | 17 | 5 | 2026-10-13 | Carr: single-derivation; Ldgr: unsourced (declared) |  | Some gap sentences are fixed text: no KaryatvaMap registered, no D1 house data, and yoga catalog or firings not exposed. |
| bo_samvada | 30 | census_L2.json#c7b49c719c34 | 10 | 12 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_sangati | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  | A count of one reads 1 shared signals and 1 signals because the plural is fixed. |
| bo_special_lagna | 30 | census_L2.json#c7b49c719c34 | 18 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_sudarshana | 30 | census_L2.json#c7b49c719c34 | 19 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_upaya | 30 | census_L2.json#c7b49c719c34 | 17 | 4 | 2026-10-13 | Carr: single-derivation |  | Gap sentences are fixed text, and a count of one reads 1 prescriptions in bundle and pattern citations. |
| bo_vargottama_dhana | 30 | census_L2.json#c7b49c719c34 | 19 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_yantra_mechanism | 30 | census_L2.json#c7b49c719c34 | 18 | 4 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_ayurdaya | 30 | census_L1.json#f4a3131036ef | 14 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_condition | 30 | census_L1.json#f4a3131036ef | 17 | 4 | 2026-10-13 | Carr: single-derivation |  | Baladi avastha ignores sign parity, so a graha in an even sign can get the wrong bala to mrita state, and the sayanadi, lajjitadi and deepta/swastha mappings are simplified with a doubtful citation. |
| ga_dashas | 30 | census_L1.json#f4a3131036ef | 14 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_fact_identity | 30 | census_L1.json#f4a3131036ef | 12 | 12 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_medical | 30 | census_L1.json#f4a3131036ef | 13 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_nakshatra | 30 | census_L1.json#f4a3131036ef | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | citation_human holds a machine template that restates the row rather than human prose. |
| ga_panchanga | 30 | census_L1.json#f4a3131036ef | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | The inauspicious tithi set is compared with the 1-30 tithi number, so Krishna tithis 4, 6, 8, 9, 12 and 14 are never flagged inauspicious while the Shukla ones are. |
| ga_positions | 30 | census_L1.json#f4a3131036ef | 19 | 5 | 2026-10-13 |  |  | 10 of 530 Rahu and Ketu rows store retrograde_flag as direct although the mean-node longitude moves backward, and the two CHART_FACTS_SCHEMA.json copies disagree on 8 of 27 nakshatra spellings. |
| ga_prashna | 30 | census_L1.json#f4a3131036ef | 11 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_sade_sati | 30 | census_L1.json#f4a3131036ef | 19 | 4 | 2026-10-13 | Carr: single-derivation |  | Saturn in Gemini is stored as neutral while Virgo (also a Mercury sign) is friend, and sentences read Mars aspect to Saturn during ...: None when the upstream value is missing. |
| ga_sensitive | 30 | census_L1.json#f4a3131036ef | 19 | 5 | 2026-10-13 | Carr: single-derivation |  | citation_human holds a machine template that restates the row rather than human prose. |
| ga_sensitive_degree | 30 | census_L1.json#f4a3131036ef | 14 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_strength | 30 | census_L1.json#f4a3131036ef | 18 | 5 | 2026-10-13 | Carr: single-derivation |  | Shadbala sentences print raw subject codes such as SAT, MOON and JUP in some places and full names elsewhere. |
| ga_tajaka | 30 | census_L1.json#f4a3131036ef | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | Panchavargiya bala takes D2 and D3 signs from a plain multiplicative division, not the Parashari rules, so the Panchavargiya winner and the methods-diverge flag can be wrong. |
| ga_transit_anchors | 30 | census_L1.json#f4a3131036ef | 14 | 10 | 2026-10-13 | Carr: single-derivation |  |  |
| ga_vargas | 30 | census_L1.json#f4a3131036ef | 20 | 4 | 2026-10-13 | Carr: single-derivation |  | The Moon is always Exalted anywhere in Taurus, friend and enemy factors in vimsopaka are unreachable, and the D81 gap sentence is fixed text. |
| ga_vastu | 30 | census_L1.json#f4a3131036ef | 14 | 10 | 2026-10-13 | D1: unverified transcription |  |  |
| ga_yoga | 30 | census_L1.json#f4a3131036ef | 20 | 4 | 2026-10-13 | Carr: single-derivation |  |  |

## Named ceilings and disclosure gaps (64 of 77 certified assets); the cells stay PARTIAL / NO_DETECTOR in the counts, only the certification verdict is the bar: N-268 (named ceilings and disclosure gaps)
- bg_class_lifetime_counts
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L0_brahmagyan/query_class_priors.ts
- bg_cohort
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bg_synthetic_cohort.positions, bg_synthetic_cohort.source_citation; bounded sample only: bg_synthetic_cohort.positions; unread: bg_synthetic_cohort.positions
- bg_compendium_index
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L0_brahmagyan/query_compendium_index.ts
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in brahma_compendium_index.summary_text, brahma_compendium_index.topic_id); no non-canonical value found
- bg_concordance
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in classical_attributions.topic_canonical_name); no non-canonical value found
- bg_dasha_systems
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in brahma_dasha_systems.computation_pseudocode, brahma_dasha_systems.conditions_for_use, brahma_dasha_systems.sequence_jsonb
- bg_dignity_reference
  - Dens.served [gap] (dens-not-attributable): served; per file: platform-mcp/src/tools/kala_views/now.ts: attribution not established: select in a different top-level declaration (static-reading limit); platform-mcp/src/tools/register_p1_reference.ts: attribution not established: select in a different capability entry (static-reading limit)
- bg_doshas
  - Dens.served [gap] (dens-not-attributable): served; per file: L0_brahmagyan/query_dosha_catalog.ts: no tier column in the served select (known absence); L0_brahmagyan/query_parihara_graph.ts: tier carriage not established: run-time select list (static-reading limit)
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in brahma_dosha_catalog.classical_citations, brahma_dosha_catalog.formation_rule_jsonb, brahma_dosha_catalog.severity_grades
- bg_ephemeris
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_graha_yuddha.ts
- bg_ephemeris_engine
  - Earn.build_record [ceiling] (not-measurable:Earn.build_record:receipt-overwritten): not measurable: the named run's receipt was overwritten by a newer one (destroyed by design, not contradicted)
- bg_formula_constants
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in brahma_formula_constants.citation_or_ratification, brahma_formula_constants.value_jsonb); no non-canonical value found
- bg_ghatana
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in brahma_event_ontology.citations, brahma_event_ontology.signature_model, brahma_activity_ontology.significators
- bg_medical_mappings
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bg_medical_mappings.graha, bg_medical_mappings.classical_citation
- bg_muhurta_lattice
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bg_muhurta_lattice.detail, bg_muhurta_lattice.sampling_method, bg_muhurta_lattice.source_citation; bounded sample only: bg_muhurta_lattice.detail
- bg_nakshatra
  - Dens.served [gap] (dens-not-attributable): served; per file: platform-mcp/src/tools/register_p1_reference.ts: attribution not established: select in a different capability entry (static-reading limit) + tier carriage not established: run-time select list (static-reading limit)
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in reference_nakshatra.degree_in_rashi_ranges, reference_nakshatra.deity_domain, reference_nakshatra.shakti
- bg_ontology
  - Dens.served [ceiling] (not-measurable:Dens.served:shared-table): not measurable: only a shared table is referenced: the served surface cannot be attributed to it by code
- bg_panchanga
  - Earn.build_record [ceiling] (not-measurable:Earn.build_record:receipt-overwritten): not measurable: the named run's receipt was overwritten by a newer one (destroyed by design, not contradicted)
- bg_parihara_rules
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L0_brahmagyan/query_parihara_graph.ts
- bg_prashna_rules
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bg_prashna_significators.quesited_planet, bg_prashna_tajik_yogas.formation_rule_jsonb, bg_prashna_lagna_methods.derivation_rule_jsonb
- bg_reference
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in reference_planets.source_citation, reference_aspects.notes, reference_aspects.source_citation, reference_houses.classical_doctrine_jsonb, reference_houses.name_en, reference_strength_systems.classical_interpretation, reference_strength_systems.formula_text, reference_karakas.classical_significations, reference_karakas.name_en, reference_upagrahas.computation_method, reference_upagrahas.significations, reference_constants.classical_context, reference_constants.name, reference_constants.value_text, reference_topic_tags.description, reference_topic_tags.name, reference_glossary.definition, reference_glossary.term_en, reference_glossary.term_id, reference_glossary.term_sa; bounded sample only: reference_glossary.term_en, reference_glossary.term_id, reference_glossary.term_sa
- bg_remedies
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in brahma_remedy_corpus.classical_attestation_text, brahma_remedy_corpus.classical_ref, brahma_remedy_corpus.contraindications, brahma_remedy_corpus.deity, brahma_remedy_corpus.ingredients_jsonb, brahma_remedy_corpus.source_citation, brahma_remedy_corpus.timing_rules_jsonb
- bg_rules
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of register_d7_channel.ts
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in sutravali_rules.antecedent_jsonb, sutravali_rules.extraction_pass_log, sutravali_rules.predicate_jsonb, sutravali_rules.prediction_jsonb; bounded sample only: sutravali_rules.antecedent_jsonb, sutravali_rules.prediction_jsonb
- bg_sky_calendar
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: bounded sample only: bg_sky_calendar.detail
- bg_text_index
  - Dens.served [ceiling] (not-measurable:Dens.served:shared-table): not measurable: only a shared table is referenced: the served surface cannot be attributed to it by code
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in classical_text_chunks.content_en, classical_text_chunks.ocr_review_note, classical_text_chunks.topic_tag); no non-canonical value found
- bg_texts
  - Dens.served [ceiling] (not-measurable:Dens.served:no-served-select): not measurable: no served SELECT of its table was found: whether it is served cannot be told by code
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in classical_text_chunks.ocr_review_note, classical_text_chunks.topic_tag); no non-canonical value found
- bg_transit_rules
  - Dens.served [gap] (dens-not-attributable): served; per file: platform-mcp/src/tools/register_p1_reference.ts: no tier column in the served select (known absence) + attribution not established: select in a different capability entry (static-reading limit)
- bg_vastu_directions
  - Dens.served [gap] (dens-not-attributable): served; per file: L0_brahmagyan/query_vastu_directions.ts: no tier column in the served select (known absence); L1_ganita/get_vastu_directions.ts: tier carriage not established: run-time select list (static-reading limit)
- bg_vidhi_floors
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in vidhi_floor_items.args_override; bounded sample only: vidhi_floor_items.args_override
- bg_vidhi_primitives
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in vidhi_primitives.tool_args); no non-canonical value found
- bg_yogas
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in brahma_yoga_catalog.canonical_id, brahma_yoga_catalog.formation_rule_jsonb, brahma_yoga_catalog.formation_text, brahma_yoga_catalog.name_en, brahma_yoga_catalog.name_sa, brahma_yoga_catalog.significations_text, reference_yogas.canonical_id, reference_yogas.name_en, brahma_ontology.canonical_id, brahma_ontology.canonical_name_en, brahma_ontology.canonical_name_sa, brahma_ontology.description, brahma_ontology.synonyms; bounded sample only: brahma_yoga_catalog.formation_rule_jsonb
- bo_anveshana
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in bodha_anomalies.subject_ref_jsonb, bodha_discoveries.ayanamsha_id, bodha_discoveries.hypothesis_text, bodha_discoveries.meaningfulness_basis, bodha_anomalies.ayanamsha_id); no non-canonical value found
- bo_arudha
  - Build.dag [ceiling] (dag-parse-incomplete): dependency graph acyclic and every declared edge exists; the read parse is incomplete at 3 dynamic site(s) of the shared helper (not resolvable by static parse)
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 3 site(s))
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_msr_signals.citation_ref, bodha_msr_signals.classical_sources_jsonb, bodha_msr_signals.configuration_jsonb
- bo_bimba
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_cgm_nodes.node_subject, bodha_cgm_nodes.citation_ref, bodha_cgm_nodes.node_label_human, bodha_cgm_nodes.position_in_chart_jsonb; bounded sample only: bodha_cgm_nodes.position_in_chart_jsonb
- bo_cdlm_summary
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in bodha_cdlm_pattern_clusters.ayanamsha_id); no non-canonical value found
- bo_cgm_motifs
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_cgm_motifs.ayanamsha_id, bodha_cgm_sub_graphs.ayanamsha_id, bodha_cgm_sub_graphs.representative_path_jsonb, bodha_cgm_sub_graphs.subgraph_label
- bo_chart_gestalt
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L2_bodha/query_chart_gestalt.ts
- bo_drishti
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in bodha_question_lenses.all_relevant_ranked_jsonb, bodha_question_lenses.citation_ref); no non-canonical value found; unread: bodha_question_lenses.template_element_ids_jsonb, bodha_question_lenses.all_relevant_ranked_jsonb
- bo_grounding
  - Narr.checkable [ceiling] (narr-checkable-unknown-or-empty): checkable-row count unknown or zero for derivation_chain: nothing found, but those entries were not checked
  - Null.blank_rows [gap] (null-blank-constant-write): no blank or placeholder row among the checkable prose rows; every constant_write literal the scan lists states an absence explicitly: honest absence statement: no sutravali_rules antecedent (full or per-component) matched this firing's constituent_planets/constituent_houses (bodha_writers/grounding_matcher.py:183); honest absence statement: no classical_sources_jsonb citations for this signal (bodha_writers/grounding_matcher.py:238)
  - Null.schema_default [gap] (null-default-constant-write): no schema default on the declared prose columns; every constant_write literal the scan lists states an absence explicitly: honest absence statement: no sutravali_rules antecedent (full or per-component) matched this firing's constituent_planets/constituent_houses (bodha_writers/grounding_matcher.py:183); honest absence statement: no classical_sources_jsonb citations for this signal (bodha_writers/grounding_matcher.py:238)
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in bodha_grounding_matches.grounding_evidence_jsonb, bodha_grounding_matches.matched_rule_id, bodha_grounding_matches.target_id); no non-canonical value found
- bo_karanajala
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_cgm_nodes.node_subject, bodha_cgm_edges.citation_ref, bodha_cgm_edges.edge_properties_jsonb, bodha_cgm_edges.relationship_basis, bodha_cgm_edges.relationship_class, bodha_cgm_edges.semantic_path_class, bodha_cgm_nodes.citation_human, bodha_cgm_nodes.citation_ref, bodha_cgm_nodes.node_label_human, bodha_cgm_nodes.position_in_chart_jsonb; bounded sample only: bodha_cgm_edges.edge_properties_jsonb, bodha_cgm_nodes.position_in_chart_jsonb
- bo_nakshatra_semantic
  - Build.dag [ceiling] (dag-parse-incomplete): dependency graph acyclic and every declared edge exists; the read parse is incomplete at 3 dynamic site(s) of the shared helper (not resolvable by static parse)
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 2 site(s))
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_msr_signals.citation_ref, bodha_msr_signals.classical_sources_jsonb, bodha_msr_signals.configuration_jsonb
- bo_pratijna
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L2_bodha/query_pratijna.ts
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 2 site(s))
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_pratijna.derivation, bodha_pratijna.varga_confirmation; bounded sample only: bodha_pratijna.derivation; unread: bodha_pratijna.derivation
- bo_samvada
  - Build.completion [ceiling] (not-measurable:Build.completion:view-object): not measurable: a view: completion consistency is not measurable for a view
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L2_bodha/query_ucd.ts
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in vw_chart_digest.ayanamsha_id
- bo_special_lagna
  - Build.dag [ceiling] (dag-parse-incomplete): dependency graph acyclic and every declared edge exists; the read parse is incomplete at 3 dynamic site(s) of the shared helper (not resolvable by static parse)
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 2 site(s))
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_msr_signals.citation_ref, bodha_msr_signals.classical_sources_jsonb, bodha_msr_signals.configuration_jsonb, bodha_msr_signals.engine_version, bodha_msr_signals.producer_asset_id, bodha_msr_signals.relationship_classification, bodha_msr_signals.signal_type_class, bodha_msr_signals.source_subsystem
- bo_sudarshana
  - Build.dag [ceiling] (dag-parse-incomplete): dependency graph acyclic and every declared edge exists; the read parse is incomplete at 3 dynamic site(s) of the shared helper (not resolvable by static parse)
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_msr_signals.citation_ref, bodha_msr_signals.classical_sources_jsonb, bodha_msr_signals.configuration_jsonb
- bo_upaya
  - Narr.checkable [ceiling] (narr-checkable-unknown-or-empty): checkable-row count unknown or zero for counter_indications_array, prescription_detail_jsonb.$.maraka_contraindication_verdict.reason: nothing found, but those entries were not checked
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 3 site(s))
  - Null.blank_rows [gap] (null-blank-constant-write): no blank or placeholder row among the checkable prose rows; every constant_write literal the scan lists states an absence explicitly: honest absence statement: INR market pricing requires an external, time-varying market-price source not present in the classical-text corpus this system computes from — B.10 forbids inventing a figure. See cost_tier for the qualitative (free/low/medium/high) classification, which IS corpus-derived. (bo_upaya.py:1677); honest absence statement: L1 ayurdaya.maraka_grahas fact not found for this chart/ayanamsha — cannot compute a maraka verdict without it (never guessed). (bo_upaya.py:991)
  - Null.schema_default [gap] (null-default-constant-write): no schema default on the declared prose columns; every constant_write literal the scan lists states an absence explicitly: honest absence statement: INR market pricing requires an external, time-varying market-price source not present in the classical-text corpus this system computes from — B.10 forbids inventing a figure. See cost_tier for the qualitative (free/low/medium/high) classification, which IS corpus-derived. (bo_upaya.py:1677); honest absence statement: L1 ayurdaya.maraka_grahas fact not found for this chart/ayanamsha — cannot compute a maraka verdict without it (never guessed). (bo_upaya.py:991)
- bo_vargottama_dhana
  - Build.dag [ceiling] (dag-parse-incomplete): dependency graph acyclic and every declared edge exists; the read parse is incomplete at 3 dynamic site(s) of the shared helper (not resolvable by static parse)
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in bodha_msr_signals.citation_ref, bodha_msr_signals.configuration_jsonb
- bo_yantra_mechanism
  - Null.blank_rows [gap] (null-blank-unresolved-write-path): no blank or placeholder row among the checkable prose rows; the writer scan could not resolve 1 listed write path(s) (instrument limit); no literal problem is listed
  - Null.schema_default [gap] (null-default-unresolved-write-path): no schema default on the declared prose columns; the writer scan could not resolve 1 listed write path(s) (instrument limit); no literal problem is listed
  - Vocab.alias [ceiling] (vocab-embedded-only): no whole value is a term (embedded text only, spelling unchecked, in bodha_mechanisms.citation_ref); no non-canonical value found
- ga_ayurdaya
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.ayanamsha_id, chart_facts.fact_value_jsonb, chart_facts.fact_value_text
- ga_condition
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_condition_composite.ts
  - Null.blank_rows [gap] (null-blank-unresolved-write-path): no blank or placeholder row among the checkable prose rows; the writer scan could not resolve 1 listed write path(s) (instrument limit); no literal problem is listed
  - Null.schema_default [gap] (null-default-unresolved-write-path): no schema default on the declared prose columns; the writer scan could not resolve 1 listed write path(s) (instrument limit); no literal problem is listed
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in ga_condition_composite.peak_dasha_periods, ga_condition_composite.weak_dasha_periods, ga_condition_composite.varga_dignity_spread, chart_facts.ayanamsha_id, chart_facts.citation_human, chart_facts.citation_ref
- ga_dashas
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_dashas.ayanamsha_id, chart_dashas.citation_human, chart_dashas.karakas_active_during_period, chart_dashas.period_deity_or_marker; bounded sample only: chart_dashas.concurrent_system_lords_jsonb, chart_dashas.period_deity_or_marker
- ga_fact_identity
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_fact_identity.parsed_from; bounded sample only: chart_fact_identity.graha_code
- ga_medical
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_medical_indications.ts
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in ga_medical.classical_citation
- ga_nakshatra
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.ayanamsha_id, chart_facts.citation_ref, chart_facts.fact_value_text, chart_facts.source_calculation; bounded sample only: chart_facts.fact_value_text
- ga_panchanga
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.fact_subject, chart_facts.ayanamsha_id, chart_facts.citation_ref, chart_facts.fact_category, chart_facts.fact_key, chart_facts.fact_value_jsonb, chart_facts.fact_value_text
- ga_positions
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.ayanamsha_id, chart_facts.citation_ref
- ga_prashna
  - certified, empty by design: prashna questions (prashna_charts rows) for this chart recorded: none (writer ran to completion on the current code; the zero-row convention is verified against prashna_charts.chart_id)
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_prashna_lagna.ts
  - Ldgr.source_presence [ceiling] (empty-by-design:ga_prashna): empty by design: prashna questions (prashna_charts rows) for this chart recorded: none (writer ran to completion on the current code; the zero-row convention is verified against prashna_charts.chart_id)
  - Vocab.alias [ceiling] (empty-by-design:ga_prashna): empty by design: prashna questions (prashna_charts rows) for this chart recorded: none (writer ran to completion on the current code; the zero-row convention is verified against prashna_charts.chart_id)
  - Vocab.identity [ceiling] (empty-by-design:ga_prashna): empty by design: prashna questions (prashna_charts rows) for this chart recorded: none (writer ran to completion on the current code; the zero-row convention is verified against prashna_charts.chart_id)
- ga_sade_sati
  - Narr.lint [ceiling] (narr-lint-allowlisted): only allowlisted narration lint violations (fact-category-pin; 3 site(s))
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.fact_subject, chart_facts.ayanamsha_id, chart_facts.citation_ref, chart_facts.fact_category, chart_facts.fact_key, chart_facts.fact_value_jsonb, chart_facts.source_calculation
- ga_sensitive
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.fact_subject, chart_facts.ayanamsha_id, chart_facts.citation_ref, chart_facts.fact_category, chart_facts.fact_value_text, chart_facts.formula_id, chart_facts.formula_provenance_text; bounded sample only: chart_facts.fact_value_text
- ga_sensitive_degree
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.ayanamsha_id, chart_facts.fact_value_jsonb; bounded sample only: chart_facts.fact_value_jsonb
- ga_strength
  - Dens.served [ceiling] (not-measurable:Dens.served:no-served-select): not measurable: no served SELECT of its table was found: whether it is served cannot be told by code
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_facts.fact_subject, chart_facts.ayanamsha_id, chart_facts.citation_human, chart_facts.citation_ref
- ga_tajaka
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in l1_tajik_varsha_year_lords.candidate_lord_jsonb, l1_tajik_varsha_year_lords.citation_ref, l1_tajik_varsha_year_lords.muntha_position_jsonb; bounded sample only: l1_tajik_varsha_year_lords.candidate_lord_jsonb, l1_tajik_varsha_year_lords.ephemeris_audit_jsonb, l1_tajik_varsha_year_lords.muntha_position_jsonb; unread: l1_tajik_varsha_year_lords.candidate_lord_jsonb
- ga_transit_anchors
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_transit_anchors.ts
- ga_vargas
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in chart_divisionals.fact_subject, chart_divisionals.ayanamsha_id, chart_divisionals.citation_ref, chart_divisionals.fact_category, chart_divisionals.fact_key, chart_divisionals.fact_value_text, chart_divisionals.formula_provenance_text, chart_divisionals.source_calculation, chart_divisionals.source_citation; bounded sample only: chart_divisionals.fact_value_text
- ga_vastu
  - Dens.served [gap] (dens-no-tier-column): served but does not state its verification level: no tier column in the served select of L1_ganita/get_vastu_directions.ts
- ga_yoga
  - Vocab.alias [ceiling] (vocab-canonical-with-caveats): every whole value found is canonical; not verified: embedded text, spelling unchecked, in ga_yoga_firings.bhanga_rule_fired, ga_yoga_firings.citation_ref, ga_yoga_firings.grounds_jsonb

Known limitation, Build.completion: counts only (no integrity statement): 0 of 82 assets have a Build.completion PASS that rests on count equality alone (its measured text states no 'integrity_check_sql holds'). This is reporting only: no verdict changed.
- (none)
