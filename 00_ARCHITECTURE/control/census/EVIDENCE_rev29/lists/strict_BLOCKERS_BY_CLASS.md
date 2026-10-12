# BLOCKERS_BY_CLASS
bar: strict (every criterion PASS or a ruled N/A)
Measured on: full census of an evaluation copy of production, backup 1791769727082 taken 2026-10-12T01:50:08.186Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.

69 assets are not certified. GENUINE DEFECT = writer / data / code wrong, a non-canonical value / placeholder / source gap found, or a FAIL; MISSING DECLARATION = an engine form exists and the declaration is not written; STRUCTURAL = no engine form or detector exists / an instrument limit / needs a stored aggregate, a keyed read or a build run.

| class | blockers | assets with at least one | assets blocked ONLY by this class |
|---|---|---|---|
| GENUINE DEFECT | 7 | 5 | 0 |
| MISSING DECLARATION | 2 | 1 | 0 |
| STRUCTURAL | 104 | 69 | 57 |
| UNCLASSIFIED | 10 | 9 | 0 |

| asset | class | criterion | verdict | why |
|---|---|---|---|---|
| bg_class_lifetime_counts | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bg_cohort | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_compendium_index | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bg_compendium_index | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_concordance | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_dasha_systems | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_dignity_reference | STRUCTURAL | Dens.served | PARTIAL | tier carriage / select attribution cannot be established by static code reading |
| bg_doshas | STRUCTURAL | Dens.served | PARTIAL | tier carriage / select attribution cannot be established by static code reading |
| bg_doshas | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_ephemeris | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bg_ephemeris_engine | STRUCTURAL | Earn.build_record | NO_DETECTOR | the cell is not measurable by the instrument |
| bg_formula_constants | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_ghatana | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_medical_mappings | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_muhurta_lattice | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_nakshatra | STRUCTURAL | Dens.served | PARTIAL | tier carriage / select attribution cannot be established by static code reading |
| bg_nakshatra | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_ontology | STRUCTURAL | Dens.served | NO_DETECTOR | the served surface is not attributable by code |
| bg_panchanga | STRUCTURAL | Earn.build_record | NO_DETECTOR | the cell is not measurable by the instrument |
| bg_parihara_rules | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bg_prashna_rules | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_reference | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_remedies | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_rules | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bg_rules | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_sky_calendar | UNCLASSIFIED | Carr.D3 | PARTIAL | no classification rule matches this blocker |
| bg_sky_calendar | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_text_index | STRUCTURAL | Dens.served | NO_DETECTOR | the served surface is not attributable by code |
| bg_text_index | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_texts | STRUCTURAL | Dens.served | NO_DETECTOR | the served surface is not attributable by code |
| bg_texts | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_transit_rules | STRUCTURAL | Dens.served | PARTIAL | tier carriage / select attribution cannot be established by static code reading |
| bg_vastu_directions | STRUCTURAL | Dens.served | PARTIAL | tier carriage / select attribution cannot be established by static code reading |
| bg_vidhi_floors | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_vidhi_primitives | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bg_yogas | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_anveshana | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_arudha | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_arudha | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_arudha | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_bimba | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_cdlm_summary | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_cgm_motifs | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_chart_gestalt | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bo_drishti | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_grounding | STRUCTURAL | Narr.checkable | PARTIAL | no row data was read / unknown or empty entries in the checkable-row count |
| bo_grounding | GENUINE DEFECT | Null.blank_rows | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_grounding | GENUINE DEFECT | Null.schema_default | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_grounding | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_karanajala | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_laksana | STRUCTURAL | Build.completion | NO_DETECTOR | a view / constant count_sql / shared multi-table count needs a stored aggregate or keyed read |
| bo_laksana | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_laksana | UNCLASSIFIED | Ldgr.source_presence | ERRORED | no classification rule matches this blocker |
| bo_laksana | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_laksana | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_laksana_rerank | STRUCTURAL | Dens.served | NO_DETECTOR | the served surface is not attributable by code |
| bo_laksana_rerank | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_nakshatra_semantic | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_nakshatra_semantic | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_nakshatra_semantic | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_pratijna | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bo_pratijna | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_pratijna | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_samskara | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_samskara | UNCLASSIFIED | Narr.agree | PARTIAL | no classification rule matches this blocker |
| bo_samskara | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_samskara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_samskara | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_samvada | STRUCTURAL | Build.completion | NO_DETECTOR | a view / constant count_sql / shared multi-table count needs a stored aggregate or keyed read |
| bo_samvada | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| bo_samvada | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_special_lagna | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_special_lagna | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_special_lagna | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_sudarshana | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_sudarshana | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_upaya | STRUCTURAL | Narr.checkable | PARTIAL | no row data was read / unknown or empty entries in the checkable-row count |
| bo_upaya | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| bo_upaya | GENUINE DEFECT | Null.blank_rows | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_upaya | GENUINE DEFECT | Null.schema_default | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_vargottama_dhana | STRUCTURAL | Build.dag | PARTIAL | the Build.dag static parse is incomplete beyond the closed shape (e.g. the SOFT-tier chart_facts producer note) |
| bo_vargottama_dhana | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| bo_yantra_mechanism | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_yantra_mechanism | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_yantra_mechanism | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_ayurdaya | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_condition | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_condition | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_condition | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_condition | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_dashas | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_fact_identity | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_medical | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_medical | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_nakshatra | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_panchanga | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_positions | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_prashna | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_prashna | STRUCTURAL | Ldgr.source_presence | NO_DETECTOR | the cell is not measurable by the instrument |
| ga_prashna | STRUCTURAL | Vocab.alias | NO_DETECTOR | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_prashna | STRUCTURAL | Vocab.identity | NO_DETECTOR | the cell is not measurable by the instrument |
| ga_sade_sati | UNCLASSIFIED | Narr.lint | PARTIAL | no classification rule matches this blocker |
| ga_sade_sati | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_sensitive | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_sensitive_degree | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_strength | STRUCTURAL | Dens.served | NO_DETECTOR | the served surface is not attributable by code |
| ga_strength | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_structural | MISSING DECLARATION | Ldgr.source_presence | NO_DETECTOR | the Ldgr target-table / applicability ruling is not written |
| ga_structural | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_structural | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_structural | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| ga_structural | MISSING DECLARATION | Vocab.identity | NO_DETECTOR | the identity key declaration is not written |
| ga_tajaka | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_transit_anchors | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_vargas | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_vastu | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_vichara | STRUCTURAL | Build.history | PARTIAL | nothing has exercised the current code and contract yet: a build run is needed |
| ga_vichara | STRUCTURAL | Dens.served | PARTIAL | the served surface is not attributable by code |
| ga_vichara | STRUCTURAL | Narr.checkable | PARTIAL | no row data was read / unknown or empty entries in the checkable-row count |
| ga_vichara | STRUCTURAL | Null.blank_rows | PARTIAL | no row data was read / unknown or empty entries in the checkable-row count |
| ga_vichara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_vichara | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
| ga_yoga | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
