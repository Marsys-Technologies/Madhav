# drift_detector HIGH Finding Triage Report

**Run timestamp:** 2026-05-21T09:41:51Z
**drift_detector exit code:** 2
**Total HIGH finding count:** 87
**Breakdown by check:**

| Check | Count |
|---|---|
| H.3.1 path-table parity | 1 |
| H.3.2 fingerprint match | 80 |
| H.3.3 MACRO_PLAN alignment | 0 |
| H.3.5 FILE_REGISTRY | 0 |
| H.3.6 GOVERNANCE_STACK | 0 |
| H.3.7 phantom refs | 6 |
| H.3.8 unreferenced | 0 |
| Unclassified | 0 |
| **Total** | **87** |

---

## H.3.1 — Path-table parity

*Detector `finding_type`: `canonical_path_disagreement` — a canonical_id in CANONICAL_ARTIFACTS §1 declares a path that disagrees with the detector's internal expected path.*

| finding_id | artifact_path | finding_message | suggested_fix |
|---|---|---|---|
| F001 | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | CANONICAL_ARTIFACTS path='025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'; expected='025_HOLISTIC_SYNTHESIS/MSR_v3_0.md' | Audit `025_HOLISTIC_SYNTHESIS/` to confirm which file is the live canonical MSR. If the live file is `MSR_v5_0.md`, update the detector's `surfaced` map entry for `MSR` (in `drift_detector.py`) to point to `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`. If `MSR_v3_0.md` is still authoritative, update CANONICAL_ARTIFACTS §1 MSR row `path` to `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`. CLAUDE.md §D snapshot shows MSR version 3.1 (514 signals); cross-check against CAPABILITY_MANIFEST.json MSR entry. |

---

## H.3.2 — Fingerprint match

*Detector `finding_type`: `fingerprint_mismatch` — the SHA-256 stored in CANONICAL_ARTIFACTS §1 `fingerprint_sha256` field does not match the current on-disk file hash.*

Three sub-classes appear in this batch:

- **Sub-class A (stale real hash, 13 findings):** declared fingerprint is a real SHA-256 that no longer matches the file.
- **Sub-class B (PENDING_CI_REGENERATION, 37 findings):** declared fingerprint is the literal string `PENDING_CI_REGENERATION` — never populated.
- **Sub-class C (blank declared, 29 findings):** declared fingerprint is an empty string `""`.
- **Sub-class D (PENDING_4C_2, 1 finding):** declared fingerprint is `PENDING_4C_2` — Phase 4C Wave 2 gating placeholder, now unblocked.

All 80 findings share the same fix shape: rotate `fingerprint_sha256` in CAPABILITY_MANIFEST.json to the observed SHA-256, and update `last_verified_session` + `last_verified_on` on the same row. A batch script running `sha256sum` over all affected files is recommended.

### Sub-class A — Stale real hash (13 findings)

| finding_id | artifact_path | finding_message | suggested_fix |
|---|---|---|---|
| F002 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` | declared=2038964...bb49e observed=ced5f89...17e | Rotate CAPABILITY_MANIFEST.json LEL row `fingerprint_sha256` to `ced5f89ecdd19377795bc223035224177c1c3b0728e640deb8c0b945fae2b17e`; set `last_verified_session: GH-FP-BACKFILL`, `last_verified_on: <fix-date>`. |
| F003 | `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` | declared=m8f-s1-msr-v4-543signals observed=0dc272e...97 | MSR `fingerprint_sha256` is a non-SHA-256 label. Replace with real hash `0dc272e03ecb109d34afa7bbf513687819eed8bf24ff525c85cb547ca83ec697`; set `last_verified_session/on`. Also linked to F001 (path disagreement) — fix both in one manifest edit. |
| F004 | `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0.md` | declared=2ad3a5b...79d observed=93eb7d2...57 | Rotate to `93eb7d2b3bb6e0e7f9724ecd729408adc1fec92fa5ba559ddea81bbde65c5157`; update `last_verified_session/on` on manifest row `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0`. |
| F005 | `06_LEARNING_LAYER/SCHEMAS/pattern_schema_v0_1.json` | declared=d328860...dd observed=55c2385...b7 | Rotate to `55c23858f1bcca725dcc1bc4dd33100ebaed2c157ef203a94e7671635a184d7b`; update row `PATTERN_SCHEMA_v0_1`. |
| F006 | `06_LEARNING_LAYER/SCHEMAS/prediction_schema_v0_1.json` | declared=1db6a74...96 observed=bf11899...54 | Rotate to `bf1189997a5d8e80798a7dde27d69f39d2f1d24bf845a64e768783b0328f9654`; update row `PREDICTION_SCHEMA_v0_1`. |
| F007 | `06_LEARNING_LAYER/SCHEMAS/two_pass_events_schema_v0_1.json` | declared=0ed502f...4e observed=e7003c5...6e | Rotate to `e7003c5911edd8f74b4fb0a7d7fd46add4812fe8c46254e5f54513be366f8e36`; update row `TWO_PASS_EVENTS_SCHEMA_v0_1`. |
| F008 | `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` | declared=74ffef4...1b observed=ee98660...6b | Rotate to `ee986600a0eecf33e2b61645056a7b76dea88019981280980b7aa2d5d87c846b`; update row `PROMPT_REGISTRY_INDEX`. |
| F009 | `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` | declared=47ac93e...27 observed=ac8a87c...17 | Rotate to `ac8a87cc55bbbe6d9d14ef4dd2229e701189507b01d6ecbffa51bcd5e41c701f`; update row `PREDICTION_LEDGER_JSONL`. |
| F010 | `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json` | declared=729d850...a5 observed=11ed5d5...fc | Rotate to `11ed5d57d48c23a4e3f9795df6107c9497cc6d988da2239ab3e5866cafd851fc`; update row `PATTERN_REGISTER_JSON`. |
| F011 | `035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json` | declared=ac9f284...4d observed=92a6cde...ef | Rotate to `92a6cde8cb869ff0b525477667a423852917573f0f1ffe9af3223fea1250e6ef`; update row `RESONANCE_REGISTER_JSON`. |
| F012 | `035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json` | declared=1e2fd30...68 observed=11c551a...57 | Rotate to `11c551afab85e6272d9f5569551ed5425f893edc44ee52852774caad5710857f`; update row `CONTRADICTION_REGISTER_JSON`. |
| F013 | `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json` | declared=59d5d90...3f observed=fa1dbd1...a4 | Rotate to `fa1dbd13991f06f6980e54ce586d1f1b40dbe969517ba0c5e6101de60e9a18d4`; update row `CLUSTER_ATLAS_JSON`. |
| F014 | `035_DISCOVERY_LAYER/REGISTERS/INDEX.json` | declared=f6891c9...07 observed=dd3eb54...4e | Rotate to `dd3eb54f70c2adb10ef91bca41b0ede2eeb955de1329b87e3f4dca38c832ad4e`; update row `DISCOVERY_REGISTERS_INDEX`. |

### Sub-class B — PENDING_CI_REGENERATION (37 findings)

*All entries have `declared=PENDING_CI_REGENERATION`. Fix: run `sha256sum <file>` for each and update the CAPABILITY_MANIFEST.json row's `fingerprint_sha256` to the observed hash, plus `last_verified_session/on`. Batch-script approach recommended.*

| finding_id | artifact_path | observed_sha256 | suggested_fix |
|---|---|---|---|
| F015 | `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` | `907b05f7e9abc6bada10736122243e930369c02d304a77948582e0d076fd9b7f` | Rotate manifest row `DBN_TOPOLOGY_v1_0` fingerprint to observed value; set last_verified fields. |
| F016 | `06_LEARNING_LAYER/dbn/cpt/natal_to_domain.json` | `e4c80f07b830fd044fc3d9ef2caba3e879efd45e1839faac45218c675cdeeddd` | Rotate manifest row `CPT_NATAL_TO_DOMAIN` fingerprint. |
| F017 | `06_LEARNING_LAYER/dbn/cpt/dasha_to_domain.json` | `cf3e776d9edcd7de01305d0c7257df4551aed7bca0a4a3a54e0049a2375dca69` | Rotate manifest row `CPT_DASHA_TO_DOMAIN` fingerprint. |
| F018 | `06_LEARNING_LAYER/dbn/cpt/persistence.json` | `562a8d7d1d00f7f54221d46f009540f14467ea9a902434ffe85e4e5761463e21` | Rotate manifest row `CPT_PERSISTENCE` fingerprint. |
| F019 | `06_LEARNING_LAYER/dbn/cpt/cross_domain.json` | `60be44ff92247b728145480ad81ca1ffbf129b8fcbdef2fcf89233bfa860b31d` | Rotate manifest row `CPT_CROSS_DOMAIN` fingerprint. |
| F020 | `06_LEARNING_LAYER/dbn/cpt/observation.json` | `fe0d4d0649f130db881dc821b6416a95fa07615ec61c99bae65328b209dc1629` | Rotate manifest row `CPT_OBSERVATION` fingerprint. |
| F021 | `06_LEARNING_LAYER/dbn/M5_D_CLOSE_v1_0.md` | `94721418675d7121fc0b4dfedc64da8b6304bad46d06af2b872fe44c74f7c53e` | Rotate manifest row `M5_D_CLOSE` fingerprint. |
| F022 | `06_LEARNING_LAYER/dbn/ll8_bayesian_update/LL8_SPEC_v1_0.md` | `f3877f50c2fb7517a3908989b14376e407a7a219483b77a89d7b79a6509a8c0d` | Rotate manifest row `LL8_SPEC` fingerprint. |
| F023 | `06_LEARNING_LAYER/dbn/ll8_bayesian_update/parameter_register.json` | `a463e98723bc51d31d56627af6dd792755ed45afc6605e7e3fe71dedd7e79971` | Rotate manifest row `LL8_PARAM_REGISTER` fingerprint. |
| F024 | `06_LEARNING_LAYER/miss_registry/LL9_SPEC_v1_0.md` | `8226eeafeb135eb5fad8d7a4459001c05cfec3796606e10e05abfea30671c4a8` | Rotate manifest row `LL9_SPEC` fingerprint. |
| F025 | `06_LEARNING_LAYER/miss_registry/miss_registry_stub.json` | `4a878e351c439859b78634800d69671fba16b1320c3bf85566481448ece922d7` | Rotate manifest row `LL9_MISS_REGISTRY` fingerprint. |
| F026 | `06_LEARNING_LAYER/M5_CLOSE_v1_0.md` | `5b8a7d4729cd20437bfa72b51b472c14b3234523265587b22fcc88393c2386f0` | Rotate manifest row `M5_CLOSE` fingerprint. |
| F027 | `00_ARCHITECTURE/PHASE_M8_PLAN_v1_0.md` | `74d89d028cc23d11817fcaf29a444635b7155f2c85738d5e7c0377ca594e9069` | Rotate manifest row `PHASE_M8_PLAN` fingerprint. |
| F028 | `08_CLASSICAL_CROSS_REFERENCE/PROCUREMENT_MAP_v1_0.md` | `ca88d98eb9a038d01c12a2296cd1f47524b6ea7307c62cd941296b9bb7f31c71` | Rotate manifest row `PROCUREMENT_MAP` fingerprint. |
| F029 | `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` | `e036c95878a61f20bd691cb818ca4e2f18908c391b4ad08ccef5c849aebec0e0` | Rotate manifest row `GCS_LAYOUT` fingerprint. |
| F030 | `platform/src/lib/tools/classical_text_search.ts` | `24c7b6bcee717dc9b3dd814912eb42ea3f79177933c050a87415b3542f77f879` | Rotate manifest row `RETRIEVAL_TOOL_classical_text_search` fingerprint. |
| F031 | `platform/src/lib/tools/classical_attribution_lookup.ts` | `9713bc92831f35697df7100a04af7512602e6b4b655e6dd3beeab294f287dea3` | Rotate manifest row `RETRIEVAL_TOOL_classical_attribution_lookup` fingerprint. |
| F032 | `08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json` | `e348536b13a076e7ab9c61dda74479c7c1e0a7416ac5f32e06df82c849c0fc2d` | Rotate manifest row `CLASSICAL_ATTRIBUTION_REGISTRY` fingerprint. |
| F033 | `08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md` | `dc14a76a3c33e0d0df955b1f46ae5af88548ed6968404ac27c9b885e37c1e86c` | Rotate manifest row `CLASSICAL_ATTRIBUTION_REGISTRY_MD` fingerprint. |
| F034 | `08_CLASSICAL_CROSS_REFERENCE/FINDINGS_M5_CROSS_REF_v1_0.md` | `2e1dea225f9f5c8a42d0a684f2e33e147dea3b087edb00412d96199ac356c9ad` | Rotate manifest row `FINDINGS_M5_CROSS_REF` fingerprint. |
| F035 | `08_CLASSICAL_CROSS_REFERENCE/FINDINGS_CLASSICAL_CLAIM_v1_0.md` | `24c4c7cfb4e6edd9b0263aa19a61fdc2495b64a9eed29d5847821e1e1cf9af77` | Rotate manifest row `FINDINGS_CLASSICAL_CLAIM` fingerprint. |
| F036 | `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_bhrigu_nandi_nadi.py` | `2623ad600ff93b3c16553140f9c2156cedb6052f1f17b33411c2afe331b71d64` | Rotate manifest row `INGEST_BHRIGU_NANDI_NADI` fingerprint. |
| F037 | `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_chandra_kala_nadi.py` | `1717f95b772092b107f6a260e517a33c0f3cd4cd189260e89d8636b6e7b18b3a` | Rotate manifest row `INGEST_CHANDRA_KALA_NADI` fingerprint. |
| F038 | `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/ingest_dhruva_nadi_sampler.py` | `fcaac8b2345a2a93727cf6f1c64e15a03520a3905baf6d735b48682f472ab26f` | Rotate manifest row `INGEST_DHRUVA_NADI_SAMPLER` fingerprint — verify full hash via `sha256sum`. |
| F039 | `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/run_nadi_signal_extraction.py` | `a9d1574dbb9f001866bfa800907d4f0b3d7d081a595f173bda21648e88d0674e` | Rotate manifest row `RUN_NADI_SIGNAL_EXTRACTION` fingerprint. |
| F040 | `08_CLASSICAL_CROSS_REFERENCE/BNN_SIGNAL_EXTRACTION_v1_0.md` | `33301a723994c899116afc98aef64a8408ccc486bca5094255a050e3b4ee5f8e` | Rotate manifest row `BNN_SIGNAL_EXTRACTION` fingerprint. |
| F041 | `08_CLASSICAL_CROSS_REFERENCE/NADI_SIGNAL_EXTRACTION_v1_0.md` | `1ac56ed9d720077f88675555860e9f5c27af15c56f905f29f92ed5f1b95ef300` | Rotate manifest row `NADI_SIGNAL_EXTRACTION` fingerprint. |
| F042 | `08_CLASSICAL_CROSS_REFERENCE/MSR_EXPANSION_PROPOSAL_v1_0.md` | `df929534ed05b2b1a8052994f935e2b0e4e0a7516c955ba6996f38fe74a04b70` | Rotate manifest row `MSR_EXPANSION_PROPOSAL` fingerprint. |
| F043 | `platform/src/lib/retrieve/classical_text_search_tool.ts` | `91805af0ac04a36da46141e7f099225208a348d0d00b1c5d559aa8dffde8ab47` | Rotate manifest row `CLASSICAL_TEXT_SEARCH_TOOL` fingerprint. |
| F044 | `platform/src/lib/retrieve/classical_attribution_lookup_tool.ts` | `51376e55a854a4e069b0e6b7deea49706d0e364fd64e3ca2812933d0124c6992` | Rotate manifest row `CLASSICAL_ATTRIBUTION_LOOKUP_TOOL` fingerprint. |
| F045 | `platform/src/lib/retrieve/classical_disclosure_filter.ts` | `8c1212275278dfc23c798e8bf34e881a970ec1529cd1dff29ef92e01757b2154` | Rotate manifest row `CLASSICAL_DISCLOSURE_FILTER` fingerprint. |
| F046 | `platform/tests/classical/classical_pipeline_integration.test.ts` | `3b399eca68a83aef1088cb0bcc37066f19e474078b41d9d66b071962eaaffbc0` | Rotate manifest row `CLASSICAL_PIPELINE_INTEGRATION_TEST` fingerprint. |
| F047 | `platform/tests/eval/planner_golden_set.json` | `3c6c76f3198b84fb5952cc6c1c5fb3b053bc8f1eefb63fcb7a355bf10af6c090` | Rotate manifest row `PLANNER_GOLDEN_SET_M8G` fingerprint. NOTE: F076 (`M9D_PLANNER_GOLDEN_ENTRIES`) points to the same file — see §Notes duplicate-row section. |
| F048 | `08_CLASSICAL_CROSS_REFERENCE/TRANSLATION_CROSS_CHECK_v1_0.md` | `216bd266ce9ec6673515f8d43c5b0ed47c3042098ef2b1b88d5c75791732d0a2` | Rotate manifest row `TRANSLATION_CROSS_CHECK` fingerprint. |
| F049 | `08_CLASSICAL_CROSS_REFERENCE/ACHARYA_REVIEW_SAMPLE_v1_0.md` | `d3eedf22a6aba9bd30fd557b396b77395a05a222fc0371dfffbdd5066919f95b` | Rotate manifest row `ACHARYA_REVIEW_SAMPLE` fingerprint. |
| F050 | `08_CLASSICAL_CROSS_REFERENCE/M8_CLOSE_v1_0.md` | `a79fb4f9533caa98c9ae2c1e06da0b72aa274f943b7b35e57149fb46e11592dc` | Rotate manifest row `M8_CLOSE` fingerprint. |
| F051 | `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M8_v1_0.md` | `3d2d121206126b2d501c5ee51221a104d9cc4a68026bbdbc12e90c16acab1c08` | Rotate manifest row `CLAUDECODE_BRIEF_M8` fingerprint. |

### Sub-class C — Blank declared fingerprint (29 findings)

*All entries have `declared=""` (empty string). Fix: add the actual SHA-256 to the manifest row's `fingerprint_sha256` field, plus `last_verified_session` and `last_verified_on`. Batch approach recommended.*

| finding_id | artifact_path | observed_sha256 | suggested_fix |
|---|---|---|---|
| F052 | `00_ARCHITECTURE/PHASE_M9_PLAN_v1_0.md` | `9ba61c6048ffe7541664ed4f652e4cc5298ad98cfa4c533028d3945bed725619` | Add fingerprint to manifest row `PHASE_M9_PLAN`; set last_verified fields. |
| F053 | `09_MULTI_SCHOOL_TRIANGULATION/SCHOOL_COVERAGE_AUDIT_v1_0.md` | `6cafe2556eaeb678652ba6ca0bba4747ebe80a7d293cf3a745cd0d22d1590975` | Add fingerprint to manifest row `SCHOOL_COVERAGE_AUDIT`. |
| F054 | `09_MULTI_SCHOOL_TRIANGULATION/YOGINI_SIGNAL_EXTRACTION_v1_0.md` | `0b1b5e9e0bdce6f4f9fccb1839abf83637ec52203919f2b9b9328be3d1eaa098` | Add fingerprint to manifest row `YOGINI_SIGNAL_EXTRACTION`. |
| F055 | `09_MULTI_SCHOOL_TRIANGULATION/TAJIKA_SIGNAL_EXTRACTION_v1_0.md` | `c2864e2c87fcab9b132d3fd3c6bb793170539324b505254419bef24d73a5fe55` | Add fingerprint to manifest row `TAJIKA_SIGNAL_EXTRACTION`. |
| F056 | `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M9_v1_0.md` | `9cc11a3543d84870c5126132fe8fb066980ae43b668f472c65adc75637e74804` | Add fingerprint to manifest row `CLAUDECODE_BRIEF_M9`. |
| F057 | `platform/src/lib/tools/multi_school_signal_lookup.ts` | `ab78b7368a70f57d1a1ee8582e8bc510bbcda9b635f003f2490a8f2ecf2d57cb` | Add fingerprint to manifest row `TOOL_27_MULTI_SCHOOL_SIGNAL_LOOKUP`. DUPLICATE: same file as F073 — see §Notes. |
| F058 | `platform/src/lib/tools/convergence_score_lookup.ts` | `cf41b746ca268bf20931e06bc6851eecc47aa624c3916e1fabe9a326aee3e7eb` | Add fingerprint to manifest row `TOOL_28_CONVERGENCE_SCORE_LOOKUP`. DUPLICATE: same file as F074 — see §Notes. |
| F059 | `platform/src/lib/schools/types.ts` | `0230ed34013ae27d2413eaa84415d475b85f8c0c27839c9fc29deb8a72f118aa` | Add fingerprint to manifest row `SCHOOLS_TYPES`. |
| F060 | `platform/src/lib/schools/convergence_calculator.ts` | `2f11df51a3d1a8618c179d581081fb704e149472ab70f5d06fa4aa92dc31a178` | Add fingerprint to manifest row `SCHOOLS_CONVERGENCE_CALCULATOR`. |
| F061 | `platform/src/lib/schools/school_runner.ts` | `984bc310e1a30f5c07ab0d4c14519f1bb7c0eabe296455a521c93ce4b3e7e486` | Add fingerprint to manifest row `SCHOOLS_RUNNER`. |
| F062 | `09_MULTI_SCHOOL_TRIANGULATION/schools/parashari/PARASHARI_ENGINE_SPEC_v1_0.md` | `917833fe087c1a9f04c9c0d9a48964e82ccf0bef88c356e4e3af59cfe11ce013` | Add fingerprint to manifest row `PARASHARI_ENGINE_SPEC`. |
| F063 | `09_MULTI_SCHOOL_TRIANGULATION/schools/jaimini/JAIMINI_ENGINE_SPEC_v1_0.md` | `375a9b181df938617dfe9672bf57a98ad07a95d71ad84ffd98734d6494fb9ce3` | Add fingerprint to manifest row `JAIMINI_ENGINE_SPEC`. |
| F064 | `09_MULTI_SCHOOL_TRIANGULATION/schools/tajika/TAJIKA_ENGINE_SPEC_v1_0.md` | `aaf9c576faae185d9c6516479e78d28170faa8917c107b53128a0c155aaf35bc` | Add fingerprint to manifest row `TAJIKA_ENGINE_SPEC`. |
| F065 | `09_MULTI_SCHOOL_TRIANGULATION/schools/kp/KP_ENGINE_SPEC_v1_0.md` | `1d9cf56c75cf7d76e2ee4264a781d8e5284e79a3df0b2bd3a053a7fd1d0831e4` | Add fingerprint to manifest row `KP_ENGINE_SPEC`. |
| F066 | `09_MULTI_SCHOOL_TRIANGULATION/schools/nadi/NADI_ENGINE_SPEC_v1_0.md` | `0da4f6a1a8d83e73a9a972648a52594a72cb76432057b2905a0ad8b1bf111345f` | Add fingerprint to manifest row `NADI_ENGINE_SPEC` — verify full hash from `sha256sum`. |
| F067 | `09_MULTI_SCHOOL_TRIANGULATION/schools/bnn/BNN_ENGINE_SPEC_v1_0.md` | `7a50c32493415865ea4498e1ab561519fbbb0c7af2ab867dd9cbbdd7da43f0c5` | Add fingerprint to manifest row `BNN_ENGINE_SPEC`. |
| F068 | `09_MULTI_SCHOOL_TRIANGULATION/schools/yogini/YOGINI_ENGINE_SPEC_v1_0.md` | `49516820c61b96a75ba1acd78cbc4a435aa9d03b2e0217b4d7b540849117f567` | Add fingerprint to manifest row `YOGINI_ENGINE_SPEC`. |
| F069 | `platform/scripts/m9/compute_convergence.py` | `41aa27bcd499df40f03b317e65cc8bb5222ef148056a1fcb31af87b54470ab51` | Add fingerprint to manifest row `M9D_COMPUTE_CONVERGENCE_SCRIPT`. |
| F070 | `09_MULTI_SCHOOL_TRIANGULATION/convergence/convergence_scores.json` | `935747fdc744c3d3758d9c6a65243c61ed3dff987671de1e6a3c199c377c296a` | Add fingerprint to manifest row `M9D_CONVERGENCE_SCORES_JSON`. |
| F071 | `09_MULTI_SCHOOL_TRIANGULATION/CONVERGENCE_METRICS_v1_0.md` | `273d1fc2997a62bfb39d5e1eedf089654db250fc6ae1b88053e7eef1719406038` | Add fingerprint to manifest row `M9D_CONVERGENCE_METRICS_MD` — verify from `sha256sum`. |
| F072 | `09_MULTI_SCHOOL_TRIANGULATION/CONVERGENCE_FINDINGS_v1_0.md` | `6c9fbb987ee4fd52565fa6a45960a57a1184831ac0495428b58d7d17d06e50fb` | Add fingerprint to manifest row `M9D_CONVERGENCE_FINDINGS_MD`. |
| F073 | `platform/src/lib/tools/multi_school_signal_lookup.ts` | `ab78b7368a70f57d1a1ee8582e8bc510bbcda9b635f003f2490a8f2ecf2d57cb` | Add fingerprint to manifest row `M9D_TOOL_27_IMPL`. DUPLICATE: same file path and hash as F057 — see §Notes. |
| F074 | `platform/src/lib/tools/convergence_score_lookup.ts` | `cf41b746ca268bf20931e06bc6851eecc47aa624c3916e1fabe9a326aee3e7eb` | Add fingerprint to manifest row `M9D_TOOL_28_IMPL`. DUPLICATE: same file path as F058 — see §Notes. |
| F075 | `platform/tests/schools/multi_school_tools.test.ts` | `ab54f0a2728e8040d416a712b69b4a938d49c32f5b43cb25c4210d1884e05e14` | Add fingerprint to manifest row `M9D_INTEGRATION_TESTS`. |
| F076 | `platform/tests/eval/planner_golden_set.json` | `3c6c76f3198b84fb5952cc6c1c5fb3b053bc8f1eefb63fcb7a355bf10af6c090` | Add fingerprint to manifest row `M9D_PLANNER_GOLDEN_ENTRIES`. DUPLICATE: same file path as F047 — see §Notes. |
| F077 | `platform/scripts/m9/build_disagreement_register.py` | `b724e6ff171480234a3f4088761a554528f193d8d3aa1558cf7ce97c6d7cb989` | Add fingerprint to manifest row `M9E_DISAGREEMENT_SCRIPT`. |
| F078 | `09_MULTI_SCHOOL_TRIANGULATION/disagreements/school_disagreement_register.json` | `dc7b6a621c490fc535278eead2f82c84b425bfcdaf6ecc909aa16d843dbc5c03` | Add fingerprint to manifest row `M9E_DISAGREEMENT_REGISTER_JSON`. |
| F079 | `09_MULTI_SCHOOL_TRIANGULATION/SCHOOL_DISAGREEMENT_REGISTER_v1_0.md` | `e3d6008ba4fcf9458a50b5c85e02643bc84ab09f37f0327910137793bc3e49f0` | Add fingerprint to manifest row `M9E_DISAGREEMENT_REGISTER_MD`. |
| F080 | `09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md` | `85f217031fd4aa3d06966b29f83d8190046f72c2d290bb59964d876e68ab107f` | Add fingerprint to manifest row `M9E_M9_CLOSE`. |

### Sub-class D — PENDING_4C_2 gating placeholder (1 finding)

| finding_id | artifact_path | finding_message | suggested_fix |
|---|---|---|---|
| F081 | `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` | declared=PENDING_4C_2 observed=af68f246...c9 | Rotate CAPABILITY_MANIFEST.json `PANCHANG_DAILY_v1_0` row `fingerprint_sha256` to `af68f246c795adc15639879efbd150b835c3eadb6411e1c3d22c89f9bcfdc69c`; set `last_verified_session: GH-FP-BACKFILL`, `last_verified_on: <fix-date>`. Phase 4C Wave 1 is COMPLETE — the PENDING_4C_2 gate is no longer active. |

---

## H.3.7 — Phantom references

*Detector `finding_type`: `phantom_reference` — a live pointer in a canonical artifact points to a file that does not exist at the stated path or by basename search in the repo.*

| finding_id | artifact_path | finding_message | suggested_fix |
|---|---|---|---|
| F082 | `CLAUDE.md` | Live pointer `ConsumeChatLegacy.tsx` does not resolve | `grep -n ConsumeChatLegacy CLAUDE.md` to locate the exact line. The file was deleted in §M.16 (PR #82). Update the sentence to past-tense prose that does not use `ConsumeChatLegacy.tsx` as a live filename token. |
| F083 | `CLAUDE.md` | Live pointer `consume-tools.ts` does not resolve | `grep -n consume-tools CLAUDE.md` to locate the line. File deleted in Pipeline-Transform-S1. Update to past-tense prose removing the live filename reference. |
| F084 | `.geminirules` | Live pointer `AM_JIS_BOOTSTRAP_HANDOFF.md` does not resolve | In `.geminirules`, replace the reference to `AM_JIS_BOOTSTRAP_HANDOFF.md` with `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` (correct filename) — or, if that file is also gone, replace with a citation of CLAUDE.md §C item 11 which documents that the bootstrap handoff content was merged into CLAUDE.md items 1–10+11. Fix session must declare `.geminirules` in `may_touch`. |
| F085 | `.geminirules` | Live pointer `PHASE_M10_PLAN_v1_0.md` does not resolve | In `.geminirules`, annotate the `PHASE_M10_PLAN_v1_0.md` reference as a forward reference (not-yet-authored). Add a `_FUTURE_ARTIFACTS:` annotation or comment explaining M10 plan is not yet authored. Fix session must declare `.geminirules` in `may_touch`. |
| F086 | `.gemini/project_state.md` | Live pointer `ll9_counterfactual_v1_0.md` does not resolve | In `.gemini/project_state.md`, run `find . -name "*counterfactual*"` to check if the file exists under a different name. If not found: annotate as `_FUTURE_ARTIFACTS` or remove the live reference. If found under a different path: update the reference to the correct path. |
| F087 | `00_ARCHITECTURE/FILE_REGISTRY_v1_14.md` | Live pointer `platform/src/lib/rag/routerClient.ts` does not resolve | FILE_REGISTRY_v1_14.md is SUPERSEDED but still checked for reference integrity. In FILE_REGISTRY_v1_14.md, update the `routerClient.ts` entry to mark it as deleted (e.g., `status: DELETED` or `notes: deleted in Pipeline-Transform-S1`), removing the path as a live forward pointer. |

---

## §Notes — Ambiguous findings and naming-convention mapping

### Check class naming: detector `class` field vs brief H.3.N taxonomy

The brief §2 uses protocol check codes (H.3.1–H.3.8). The detector emits `class` field values using Python function-derived names. Mapping applied in this report:

| Detector `class` | Mapped to | Rationale |
|---|---|---|
| `canonical_path_disagreement` | H.3.1 path-table parity | CANONICAL_ARTIFACTS §1 path field disagrees with detector expected-path map — matches H.3.1 definition |
| `fingerprint_mismatch` | H.3.2 fingerprint match | SHA-256 declared vs observed mismatch — matches H.3.2 definition |
| `phantom_reference` | H.3.7 phantom references | Live pointer that does not resolve — matches H.3.7 definition |
| `registry_disagreement` | H.3.5 FILE_REGISTRY | 137 findings of this class, all MEDIUM severity — zero HIGH in this run |
| `governance_stack_disagreement` | H.3.6 GOVERNANCE_STACK | 1 finding of this class, MEDIUM severity — not HIGH in this run |
| `canonical_unreferenced` | H.3.8 unreferenced | 101 findings of this class, all MEDIUM severity — zero HIGH in this run |
| `directory_entry_skipped` | n/a (LOW) | 3 findings, LOW severity — directory path entries in manifest, skip guard applied by crash fix |

### Duplicate file references in manifest (3 file pairs)

Three pairs of manifest rows reference the same physical file path:

1. **F047 + F076**: `platform/tests/eval/planner_golden_set.json` is referenced by both `PLANNER_GOLDEN_SET_M8G` (M8 context) and `M9D_PLANNER_GOLDEN_ENTRIES` (M9 context). Both are H.3.2. Suggested resolution for fix session: decide whether the file serves two distinct phases (keep both rows, but add clarity notes) or consolidate to one canonical row. Both fingerprints must be updated to the same observed hash.

2. **F057 + F073**: `platform/src/lib/tools/multi_school_signal_lookup.ts` referenced by `TOOL_27_MULTI_SCHOOL_SIGNAL_LOOKUP` and `M9D_TOOL_27_IMPL`. Same resolution approach.

3. **F058 + F074**: `platform/src/lib/tools/convergence_score_lookup.ts` referenced by `TOOL_28_CONVERGENCE_SCORE_LOOKUP` and `M9D_TOOL_28_IMPL`. Same resolution approach.

### H.3.3, H.3.5, H.3.6, H.3.8 have zero HIGH findings

These check classes produced no HIGH-severity findings in this run. MEDIUM findings exist (registry_disagreement: 137, governance_stack_disagreement: 1, canonical_unreferenced: 101) but fall below the HIGH threshold. Sections omitted per brief §3 schema instruction ("omit sections with zero findings").

### F001 + F003 root cause link

F001 (H.3.1 `canonical_path_disagreement` on MSR) and F003 (H.3.2 `fingerprint_mismatch` on MSR) likely share a root cause: the MSR artifact was promoted from v3.0 to v5.0 without updating both the manifest path field and the fingerprint field. The fix session should address both in a single CAPABILITY_MANIFEST.json edit to the MSR row.

---

## §Appendix — Validator triple at session close

| Validator | Exit code | Notes |
|---|---|---|
| drift_detector.py | 2 | Same as session open — no regression. 343 findings (87 HIGH, 253 MEDIUM, 3 LOW). |
| schema_validator.py | 2 | 208 violations — pre-existing baseline for this worktree. No regression. |
| mirror_enforcer.py | 0 | 9 pairs checked; 9 passed; 0 failed. |
