# CERTIFIED_LIST
bar: strict (every criterion PASS or a ruled N/A); registry revision 30 (fingerprint b1acb3f678b5); layers L0,L1,L2; date 2026-10-13; tool 7e63cc872; 13 of 82 assets certified
Measured on: full census of an evaluation copy of production, backup 1791868791537 taken 2026-10-13T05:21:32.951Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.
ceilings: 11 of 13 certified assets are at a declared ceiling (Carr: single-derivation 5; D1: unverified transcription 5; both 0; Ldgr: unsourced (declared) 2; Ratified judgment (N-235) 1)
Carr.D2: ruled N/A (no per-witness values stored, N-156) on 76 of 82 assets; ruled N/A under another rule 6 on the rest
Build.completion counts only (no integrity statement): 0 of 82 assets

| asset | revision | census file | measured PASS | ruled N/A | date | ceilings | known limitations | known findings |
|---|---|---|---|---|---|---|---|---|
| bg_class_priors | 30 | census_L0.json#7f9c53786923 | 13 | 12 | 2026-10-13 | Ldgr: unsourced (declared); Ratified judgment (N-235) |  |  |
| bg_gochara_arcs | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_gochara_citation_resolution | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  | It has no writer: its 14 rows were seeded by migrations 565, 630 and 631, so a build cannot regenerate them. |
| bg_kota_chakra_rings | 30 | census_L0.json#7f9c53786923 | 11 | 14 | 2026-10-13 | D1: unverified transcription; Ldgr: unsourced (declared) |  | The ring partition is a secondary-source transcription not traced to a primary text, the source is not held in the corpus (owner deferral N-102), and dvara_assignment is never filled. |
| bg_kp_sublord_division | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | Carr: single-derivation |  |  |
| bg_nakshatra_medical | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_phaladeepika_latta | 30 | census_L0.json#7f9c53786923 | 16 | 9 | 2026-10-13 |  |  | The per-row source citation names page PG339 only on all 8 rows although the passage spans PG338 and PG339, and the text is OCR English that has not been checked against the printed book. |
| bg_sign_medical | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_transit_engine | 30 | census_L0.json#7f9c53786923 | 14 | 11 | 2026-10-13 | D1: unverified transcription |  |  |
| bg_vedha_malefic_scale | 30 | census_L0.json#7f9c53786923 | 18 | 7 | 2026-10-13 |  |  | All five rows carry an editorial note (page PG349 disambiguation) added to the effect description that is not in the book text, and the source chunk for page PG353 has not been exported for checking. |
| bo_cgm_paths | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_pramana_mapa | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  |  |
| bo_sangati | 30 | census_L2.json#c7b49c719c34 | 19 | 6 | 2026-10-13 | Carr: single-derivation |  | A count of one reads 1 shared signals and 1 signals because the plural is fixed. |

Known limitation, Build.completion: counts only (no integrity statement): 0 of 82 assets have a Build.completion PASS that rests on count equality alone (its measured text states no 'integrity_check_sql holds'). This is reporting only: no verdict changed.
- (none)
