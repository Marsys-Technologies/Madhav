---
artifact: L0_WAVE_REBUILD_PLAN
version: "1.0"
status: "DRAFT for SS review - HELD; no production write, no rebuild, no migration is part of this document or of the PRs it lists"
produced_by: track-i-l0-data (Exec Suvarna worker)
produced_on: 2026-10-03
plan_item: "L0 data / rebuild items TI-L0-10, 11, 12, 13, 20, 23, 32 + served-ids item 14 + SS addition (bg_transit_rules.graha case), batched into the L0 WAVE REBUILDS after S-L1 (global L0 requests, ONE PLAN PER LEVEL)"
layer: "L0 Brahmagyan (bg_*)"
companion:
  - "L0_LAYER_INSTANCE_v3_1.md"
  - "assets/INDEX.md (section 7 answers Q1..Q22; section 8 Track I items)"
  - "assets/L0_FINDINGS_ADDENDUM_v1_0.md"
evidence_dir: "/Users/Dev/suvarna-evidence/TrackI/l0d/ (scripts, clone fixtures, mutation outputs, cell diffs, census JSON)"
prs:
  - {item: "SS-ADD graha case", pr: 3048, branch: "suvarna/land/TI-l0data-35-001"}
  - {item: "TI-L0-10", pr: 3049, branch: "suvarna/land/TI-l0data-10-001"}
  - {item: "TI-L0-11", pr: 3050, branch: "suvarna/land/TI-l0data-11-001"}
  - {item: "TI-L0-12", pr: 3051, branch: "suvarna/land/TI-l0data-12-001"}
  - {item: "TI-L0-13", pr: 3053, branch: "suvarna/land/TI-l0data-13-001"}
  - {item: "TI-L0-14", pr: 3054, branch: "suvarna/land/TI-l0data-14-001"}
  - {item: "TI-L0-20", pr: 3055, branch: "suvarna/land/TI-l0data-20-001"}
  - {item: "TI-L0-23", pr: 3056, branch: "suvarna/land/TI-l0data-23-001"}
  - {item: "TI-L0-32", pr: 3057, branch: "suvarna/land/TI-l0data-32-001"}
changelog:
  - "1.0 (2026-10-03): first issue."
---

# L0 wave rebuild plan (data items 10, 11, 12, 13, 20, 23, 32; served ids 14; SS graha-case addition)

**What this is.** The plan the SS asked for: the L0 data and rebuild items grouped by rebuild LEVEL in dependency order, one plan per level, with the migrations each level needs (drafted, **no number**), the pre-state read-back and post-state check of each level, rollback, the people-entered-data (N-46) proof, the order against S-L1/S-L2/S-L3, and what the served-id item changes and who must be told. Everything here was measured on **read-only** production reads (proxy 127.0.0.1:5433, forced read-only transactions, SELECT only) and on **disposable local PostgreSQL** copies of public L0 reference tables (the rebuild itself was simulated there by running the real, merged writer code). Nothing was written to production.

**Method note (how the numbers below were produced).** (1) Each PR is tests-first with a real-PG test, a recorded mutation run and a cell diff. (2) A scratch merge of all eight Python PRs (`scratch/l0d-merge-sim`; one trivial conflict, see section 8) was run over copies of the production tables (`clone.py`, `wave_sim_*.py`): the sealed integrity checks were evaluated on the copy **before** the run (TRUE on every copy: the copies are faithful, digests reproduce) and **after** it. (3) The extractor behind `bg_rules` was run read-only over the live corpus (`rules_dryrun.py`).

## 1 · The headline facts that shape the plan

1. **Every item that changes rows breaks a sealed integrity digest, and the orchestrator runs `integrity_check_sql` AFTER the write and rolls the rebuild back if it reads false** (`asset_runner.py` ~L1200, `_probe_asset`). So each affected asset needs a **reseal migration applied BEFORE its rebuild** (drafted below, computed from the post-state, verified TRUE on the post-state copy and FALSE on the old text). Between the reseal and the rebuild the asset's check reads false against the old rows (a short, expected window); rollback is re-applying the prior text kept in each draft's guard. This is the opposite of the order migration 1078 used; with the current orchestrator, writer-first would fail and roll back.
2. **A pre-existing defect on main changes the level-0 result by one row.** A `bg_ontology` rebuild with main's own code inserts `dasha_system|jaimini_chara` (static `ENTITIES` carries it; the catalogue id is `chara_jaimini`): 741 -> 742. It turns `bg_dasha_systems`' sealed check false until `bg_dasha_systems` is rebuilt. The plan therefore rebuilds `bg_dasha_systems` immediately after `bg_ontology` (level 1) and recommends a one-line fix (W-1, section 8). Not widened in these PRs.
3. **Known-red checks (CI, first and second pushes), by cause - none is a defect in the PR:**
   * all eight Python PRs (#3048-#3051, #3053, #3055-#3057): `provenance_inventory --check` ("writer digest inventory is stale") - `nirmana-writer-digests.json` is a file PR #2984 changes; one regeneration command after #2984 lands (precedent #3015/#3016). None of my files is in `git diff origin/main...origin/suvarna/land/TI-s-l1-integration-001 --name-only` (209 files at the last check, no overlap).
   * #3048 and #3049 additionally: DB Integration Tests - `platform/tests/unit/migrations/nirmana_l0_transit_integrity_contract.test.ts` runs the REAL `seed_transit_rules` on a throwaway PG and asserts migration 1078's sealed digest; it goes red by design until the reseal migration (M-A1, needs a number) exists and the test's migration list applies it.
   * #3054 (TS): the capability descriptor is embedded in `capability_estate_census.json` / `capability_knowledge.snapshot.json` / projections (regeneration touches #2984's census file).
   * #3055 additionally in live mode only: `test_has_writer_completeness` (needs DATABASE_URL; skipped in CI) until M-A2 is applied.
4. **Line-pinned evidence constrains every edit.** `asset_declarations.json` pins evidence as `path:line` (`l0_ontology.py:145,147,171,215,219,977,981,1152`; `l0_doshas.py:1972,1973,2003`; `resolve_entity.ts:65`) and `fact_category_pin_allowlist.json` pins by line (`source_query_availability.ts`); a governance test (`test_e6_1_declarations.py`) and the fact-category lint fail if anything above a pinned line moves; both files are #2984's. The first push of #3050/#3051/#3053/#3054 failed exactly that; the PRs were rewritten **line-neutral** (new logic in new modules `l0_ontology_normalise.py`, `l0_ontology_texts.py`, or appended after the pinned lines) and verified (`test_e6_1_declarations.py` 573 passed; targeted governance tests on the merged tree 1,367 passed). Two further declared claims bind: `l0_ontology.py` is declared to compose no text (so string-building code lives in the new modules) and the `bg_doshas` INSERT is declared to bind no computed value (so the aliases are a module constant, subscripted at the bind site).
5. **Two premises of the briefs are refuted by data:** (a) TI-L0-23: the extractor already reproduces the 3,002 live rows exactly (same ids, same every column), concept ids do not rise from 17 and `dasha_system_id` stays 0; the rebuild changes one column. (b) TI-L0-13: "differing by 3 each way" is right, but `jaimini_sutram` has consumers (17 catalogue citations) and must stay.


## 2 · Items -> PR -> level -> migration need

| item | what changes (rows) | PR | rebuild asset(s) | level | migrations needed (**needs number**) | blocked by / SS review |
|---|---|---|---|---|---|---|
| TI-L0-11 normalisation, ambiguous aliases, release id | none (new module `l0_ontology_normalise.py`; release id in the build result) | #3050 | bg_ontology | 0 | none (storing the release id in a column = optional later migration) | #2984 digest regeneration |
| TI-L0-13 text class from corpus | `brahma_ontology` text class: +3, -2 (new module `l0_ontology_texts.py`, import-time drift guard) | #3053 | bg_ontology | 0 | none | #2984 regen; SS: confirm removal of the 2 consumerless ids and keep of `jaimini_sutram` |
| TI-L0-10 re-source 24 citations | `bg_transit_rules.classical_citation` 24 cells | #3049 | bg_transit_rules | 0 | reseal M-A1 | #2984 regen; **acharya spot-check of every sloka mapping (OCR text); acharya decision on the Ketu equivalence and Ketu 12th**; TI-L0-09 (`attribution_state`) is separate |
| SS-ADD graha case | `bg_transit_rules.graha` 7 cells | #3048 | bg_transit_rules | 0 | same reseal M-A1 | #2984 regen |
| TI-L0-32 own-partition rows_written | build records only | #3057 | bg_medical_mappings (+2 riders), bg_transit_rules (+engine rider) | 0 | none | #2984 regen; declaring `bg_transit_moorti` a produced table = declarations file (#2984) |
| TI-L0-20b sarvatobhadra writer | none (asserts empty) | #3055 | bg_sarvatobhadra_grid | 0 | has_writer flip M-A2 | #2984 regen + seed literal; **SS confirms the native_confirmed scoping of Q21** |
| TI-L0-12 dosha aliases | `brahma_ontology.synonyms` 79 cells | #3051 | bg_doshas (+ bg_dasha_systems heal, W-1) | 1 | reseal M-B1 | #2984 regen; **SS REVIEW: 7 inputs flip yoga -> dosha (section 6)** |
| TI-L0-20a citation writer | none (14 rows identical) | #3055 | bg_gochara_citation_resolution (R9) | 1 | has_writer flip M-A2 | **R9: SS notifies Pravaha first**; #2984 regen + seed literal |
| TI-L0-23 confidence NULL | `sutravali_rules.confidence` 3,002 cells | #3056 | bg_rules | 2 | M-C1 nullable, reseal M-C2 | #2984 regen; **SS REVIEW: confirm no ranking reads confidence** (L2 readers checked: none) |
| TI-L0-14 resolve_entity class-aware | none (response shape) | #3054 | none (app deploy) | n/a | none | #2984 generated-artifact regeneration; **SS REVIEW of served ids (section 6)** |

Not built, with reasons: TI-L0-09 (migration + 4-asset rebuild; blocks the machine-readable half of 10), 21(a), 22(b), 25 prune (all listed in `IFL0_REPORT_1.md`), WAVE-1 (migration + SS choices; if it joins level 0 it changes the SAME composite digest as M-A1: re-run `make_reseal_drafts.py` on the merged code, one reseal per asset).

## 3 · Order relative to S-L1 / S-L2 / S-L3

* **All of it runs AFTER S-L1** (the writer-digest inventory and the census regeneration are #2984 artifacts; and no L0 wave should interleave with an L1 rebuild that reads `bg_ephemeris`/`brahma_ontology`).
* **Nothing here must wait for S-L2.** Verified readers: L2 `bo_grounding`/`bo_laksana`/`grounding_matcher` read `sutravali_rules` rows but not `confidence`; rule_ids are unchanged, so `bg_concordance` (level 3) needs **no** rebuild.
* **What must wait for S-L3 (later wave, not this one):** 61 `gochara_resonance_map` rows (15 source rules, 17 event classes) copy `bg_transit_rules.classical_citation` at L3 build time, so they carry the old text until `ka_gochara_resonance` is rebuilt. The 30 rows referencing the 7 graha-case rows do not change (target_ref is already lowercased). `ka_vedha_gochara` / `ka_sangam` read `favourable` rows with `vedha_house` only: unaffected. R9 notification: the wave touches neither `bg_ephemeris` nor `bg_texts`; it DOES dispatch `bg_gochara_citation_resolution` (R9) - SS notifies Pravaha first.
* Recommended order inside the wave: deploy PR #3054 (served `resolve_entity`) **before or with** level 0/1 so a winner flip arrives with its `ambiguous` flag.

## 4 · The per-level plans (one plan per level, in order)

Common pre-conditions for every level: #2984 merged and `nirmana-writer-digests.json` regenerated on the PR branches; SS-allocated migration numbers; SS approval of that level's dispatch; the previous level green. Pre-state read-back = the queries below run through the read-only proxy, saved to evidence, and compared with the expected values (any difference stops the level). Each level is ONE global L0 request.

### Level 0 - `bg_ontology`, `bg_transit_rules` (+`bg_transit_engine`), `bg_medical_mappings` (+`bg_nakshatra_medical`, `bg_sign_medical`), `bg_sarvatobhadra_grid`
PRs: #3050, #3053, #3049, #3048, #3057, #3055(b).
**Migrations first (needs number):** M-A1 = `DRAFT_NEEDS_NUMBER_bg_transit_rules_citations_and_case_reseal.sql` (appendix A); M-A2 = `DRAFT_NEEDS_NUMBER_l0_static_writers_has_writer.sql` (appendix D; flips both ids, so apply it with this level; the citation writer stays undispatched until level 1).
**Pre-state read-back (expected):**
* `SELECT count(*) FROM brahma_ontology` = 741; `... WHERE entity_class='text'` = 15 (ids incl. bhrigu_samhita, lal_kitab_text, jaimini_sutram); `... entity_class='dasha_system'` = 20; table fingerprint (jsonb of the 7 non-id columns, ordered `entity_class, canonical_id` COLLATE "C") = `f2964aea66b71f50...`; text-class fingerprint `78df7d511a5a1813...`.
* `SELECT count(*), count(*) FILTER (WHERE graha <> lower(graha)) FROM bg_transit_rules` = 76, 7; `count(*) FILTER (WHERE classical_citation LIKE 'BPHS Ch.29%')` = 19; `... = 'Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)'` = 5; sealed rules-section digest `1dbdd265cf0e...` (the registry check currently TRUE).
* `bg_medical_mappings` 21 / `bg_nakshatra_medical` 27 / `bg_sign_medical` 12; last build record `rows_written` = 60 for bg_medical_mappings, 105 for bg_transit_rules.
* `SELECT count(*) FROM bg_sarvatobhadra_grid` = 0 (and `count(*) FILTER (WHERE native_confirmed)` = 0).
* the registry `integrity_check_sql` of bg_transit_rules byte-equals the draft's `prior` text (the guard enforces it).
**Run:** apply M-A1, M-A2; dispatch one L0 request for the level-0 assets in this order (no intra-level edges): bg_ontology, bg_transit_rules (carries bg_transit_engine), bg_medical_mappings (carries the 2 riders), bg_sarvatobhadra_grid.
**Post-state check (expected, simulated on the copies):**
* `brahma_ontology`: 743 rows at the end of level 0 (741 +3 text -2 text +1 stray `dasha_system|jaimini_chara`, W-1; becomes 742 after level 1's `bg_dasha_systems`); text class 16 ids = 15 corpus + `jaimini_sutram`; no `bhrigu_samhita`/`lal_kitab_text`; the 12 legacy text rows byte-equal (uuid included); `bg_ontology` registry check TRUE; every dosha row still has `synonyms='{}'` (level 1 fills them).
* `bg_transit_rules`: 76 rows, 0 added/removed, same ids; **31 changed cells** (24 `classical_citation`, 7 `graha`); `count(*) FILTER (WHERE graha <> lower(graha))` = 0; zero rows with the two refuted/chapter-only citation strings; sealed digest `e401846964d3a9cf...` (engine `e2dafc84d7fe` and moorti `b411c02abb7f` unchanged); registry check TRUE; `gochara_resonance_map` FK rows (the 30) intact.
* build records: `rows_written` bg_medical_mappings 21, bg_nakshatra_medical 27, bg_sign_medical 12, bg_transit_rules 76, bg_transit_engine 9 (own partitions); no table cell of the medical tables changes; `bg_sarvatobhadra_grid` 0 rows and a measurable build record.
* every level-0 asset's `integrity_check_sql` evaluates TRUE (the orchestrator enforces this itself).
**Rollback (level 0):** re-apply the prior `integrity_check_sql` (kept in M-A1's guard); `UPDATE bg_transit_rules SET graha = initcap(graha) WHERE rule_type='double_transit'` (ids preserved) then revert the PR branches' code and rebuild (old code re-upserts the 24 old citations because the seed carries them; the old text class is re-created by the old ENTITIES list and the owned sweep removes the 3 corpus-derived ids). Before the run: save the pre-state fingerprints and a `COPY` of `bg_transit_rules` / the text and dosha ontology rows to evidence (read-only SELECT) so the old values are on disk.
**Tables written (N-46):** `brahma_ontology` (owned classes + the co-writer DO-NOTHING inserts), `bg_transit_rules`, `bg_transit_engine`, `bg_transit_moorti`, `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_sign_medical`, `bg_sarvatobhadra_grid` (only non-native-confirmed rows; 0 exist).

### Level 1 - `bg_doshas`, `bg_dasha_systems`, `bg_gochara_citation_resolution` (R9)
PRs: #3051, #3055(a). `bg_dasha_systems` has no PR: it is rebuilt unchanged to remove the W-1 stray row (it deletes and reinserts its own ontology class).
**Migrations first:** M-B1 = `DRAFT_NEEDS_NUMBER_bg_doshas_alias_sets_reseal.sql` (appendix B). The has_writer flip for the citation asset was applied with level 0 (M-A2).
**Gates:** level 0 green; SS REVIEW of the 7 yoga -> dosha flips accepted (or the alias sets amended: re-run `make_reseal_drafts.py`); **Pravaha notified before the citation writer is dispatched (R9)**.
**Pre-state read-back (expected):** `SELECT count(*) FILTER (WHERE cardinality(synonyms)=0) FROM brahma_ontology WHERE entity_class='dosha'` = 79; ontology-dosha section digest `ee5dedf6e993...` (= the sealed value); `count(*) FROM brahma_ontology WHERE entity_class='dasha_system'` = 21 after level 0 (W-1); `bg_gochara_citation_resolution` 14 rows, sealed digest `f87cfce86ed03e45...`, no build record at all (never built).
**Run:** apply M-B1; dispatch bg_dasha_systems, bg_doshas, then bg_gochara_citation_resolution (R9, only after Pravaha notice).
**Post-state check (expected):** dosha rows: 79 changed cells, only `synonyms`, all 79 non-empty (411 aliases, 3-9 each); `brahma_dosha_catalog` and `reference_doshas` digests unchanged; `bg_doshas` check TRUE with ontology-dosha digest `d036ad30c5734e4b...`; `brahma_ontology` dasha_system class back to 20, total 742; `bg_dasha_systems` check TRUE (simulated: FALSE at 21 rows, TRUE once it ran); citation table 14 rows, **0 changed cells**, digest still `f87cfce86ed03e45...`; a first build record now exists for it (state change by design: Build becomes measurable).
**Rollback:** re-apply the prior `bg_doshas` check; revert code and rebuild `bg_doshas` (old code writes `[]` again); the citation writer is idempotent and its rows equal the old ones, nothing to roll back but the registry flag (`has_writer=false`).
**Tables written (N-46):** `brahma_dosha_catalog`, `reference_doshas`, `brahma_ontology` (class dosha, dasha_system), the dasha tables (unchanged content), `bg_gochara_citation_resolution`.

### Level 2 - `bg_rules`
PR: #3056.
**Migrations first:** M-C1 = `DRAFT_NEEDS_NUMBER_sutravali_rules_confidence_nullable.sql` (appendix C; the writer refuses before it deletes anything if this is missing), then M-C2 = `DRAFT_NEEDS_NUMBER_bg_rules_confidence_not_scored_reseal.sql` (appendix E).
**Pre-state read-back (expected):** `sutravali_rules` 3,002 rows, all `extracted_by='python_regex_v2'`; `confidence IS DISTINCT FROM quality_score` = 0; confidence distribution 0.6 x2 / 0.8 x230 / 1.0 x2770; `yoga_canonical_id IS NOT NULL` = 17; `dasha_system_id IS NOT NULL` = 0; `transit_marker` true = 25; sealed digest `87b697041c73...`; `confidence` is NOT NULL.
**Run:** apply M-C1, M-C2; dispatch bg_rules (reads `classical_text_chunks`, `brahma_yoga_catalog`, `brahma_dasha_systems`: levels 0/1 first).
**Post-state check (expected, from the read-only dry run + the copy):** 3,002 rows, **identical rule_ids**, 0 rows added/removed; the single changed column `confidence` -> NULL on 3,002 cells; 17 / 0 concept ids unchanged; check TRUE with digest `bb72c32b6699e195...`; routers' result order unchanged (they rank on `quality_score`, equal to the old confidence on every row).
**Level 3 (`bg_concordance`):** no rebuild - `rule_ids` (UUID[]) are unchanged by construction (proved by the dry run).
**Rollback:** re-apply the prior check; `UPDATE sutravali_rules SET confidence = quality_score` (reader-verifiable equality) then `SET DEFAULT 0.0, SET NOT NULL`; or revert code and rebuild (the old writer writes confidence = quality).
**Tables written (N-46):** `sutravali_rules` only, and only rows with `extracted_by = 'python_regex_v2'` (all 3,002).

## 5 · People-entered-data invariant (N-46) - tables per level and the proof

N-46: agents never change or delete information people typed in; computed data may be rebuilt freely. The tables the wave writes (above) are all L0 reference tables written by registered L0 writers from git-held sources. Evidence:
* **No written table has a human-entry column except one.** Column scan (`out/n46_human_marker_columns.txt`; pattern confirm|entered|typed|user|author|reviewer|ratif|cosign|native|approved|created_by|updated_by|source_text|provenance) over all 12 written tables: only `bg_sarvatobhadra_grid` (`native_confirmed`, `source_text_id`). It has **0 rows live**, and its writer **never deletes a `native_confirmed` row** (tested, with a mutant that deletes them; this is the one deliberate deviation from the literal Q21 text, for SS to confirm).
* `sutravali_rules`: the writer's delete is scoped by `extracted_by='python_regex_v2'`, which is 3,002 of 3,002 rows (SELECT).
* `brahma_ontology`: the writers delete only classes they own (bg_ontology: owned classes; bg_doshas: `dosha`; bg_dasha_systems: `dasha_system`); no people-entered class exists.
* None of the INV people-entered/mixed tables named in the L5 instance (`life_events`, `mimamsa_*`, `kala_field_weight_versions`, `brahma_prospective_ledger`, `brahma_mimamsa_prediction_ledger`) is read or written by any changed code (the changed files are listed per PR; none references them).
* The reseal and has_writer migrations touch only `asset_registry` rows (registry metadata) and `sutravali_rules`' column definition (no row).

## 6 · Served ids (item 14) - what changes, and who must be told

PR #3054 changes **no served id**: same WHERE/ORDER BY, so the winner is the previous winner for every name (asserted for every name string of a copy of the production ontology); it adds `ambiguous`, `candidates` and an optional `entity_class` input. What changes served ids is the **data** (census of all 2680 distinct name strings of the pre- and post-wave ontology, `served_ids_census.py`, `out/served_ids_census.json`):

* **9 inputs change winner:**

| input | before (class, id) | after (class, id) | caused by |
|---|---|---|---|
| `Daridra` | ('yoga', 'daridra') | ('dosha', 'daridra') | TI-L0-12 |
| `Jaimini Sutram` | ('text', 'jaimini_sutram') | ('text', 'bphs_jaimini') | TI-L0-13 |
| `Kemadruma` | ('yoga', 'kemadruma') | ('dosha', 'kemadruma') | TI-L0-12 |
| `Rajju` | ('yoga', 'rajju') | ('dosha', 'rajju_dosha') | TI-L0-12 |
| `Sakata Yoga` | ('yoga', 'sakata') | ('dosha', 'shakata') | TI-L0-12 |
| `Sarpa Yoga` | ('yoga', 'sarpa') | ('dosha', 'sarpa_yoga_dosha') | TI-L0-12 |
| `daridra` | ('yoga', 'daridra') | ('dosha', 'daridra') | TI-L0-12 |
| `jaimini sutras` | ('text', 'jaimini_sutram') | ('text', 'bphs_jaimini') | TI-L0-13 |
| `kemadruma` | ('yoga', 'kemadruma') | ('dosha', 'kemadruma') | TI-L0-12 |

* **5 inputs stop resolving** (the two removed text ids, no consumer in source or in the L0 tables):

| input | before | after | cause |
|---|---|---|---|
| `Bhrigu Samhita` | ('text', 'bhrigu_samhita') | none | TI-L0-13 (removed text id) |
| `Bhṛgu Saṃhitā` | ('text', 'bhrigu_samhita') | none | TI-L0-13 (removed text id) |
| `bhrigu` | ('text', 'bhrigu_samhita') | none | TI-L0-13 (removed text id) |
| `bhrigu samhita` | ('text', 'bhrigu_samhita') | none | TI-L0-13 (removed text id) |
| `lal kitab text` | ('text', 'lal_kitab_text') | none | TI-L0-13 (removed text id) |

* **256 inputs newly resolve** (dosha aliases; additive). **11 inputs become ambiguous**: `Daridra`, `Jaimini Sutram`, `Kemadruma`, `Rajju`, `Sakata Yoga`, `Sarpa Yoga`, `daridra`, `dhaiya`, `jaimini sutras`, `kemadruma`, `sade_sati` (the flipped ones plus `dhaiya` and `sade_sati`, where concept still wins).
* Why the yoga -> dosha flips happen: the dosha's `canonical_id`/derived alias equals the yoga's, and the tie-break is `ORDER BY entity_class` (alphabetical: concept < dosha < yoga). The 7 colliding aliases are listed in PR #3051. **SS options:** (a) accept; (b) drop the 7 aliases from the dosha sets (re-run the generator; the reseal digest changes); (c) declare a tie preference in the resolver. This is the "REVIEW to SS if it changes served ids" of Q4, found by measurement.
* `Jaimini Sutram` / `jaimini sutras`: `bphs_jaimini` (the corpus text, has chunks) now outranks `jaimini_sutram` (cited by 12 yoga + 5 dasha catalogue rows, 0 chunks) by `canonical_id` order. The durable fix is to repoint those 17 citations to `bphs_jaimini` (separate item) and then retire `jaimini_sutram`.

**Consumers to tell:** `kala_sky_pattern.ts` `resolveGrahaName` (calls `resolve_entity`, reads the winner's `canonical_name_en`; graha/planet names are unaffected: planet names are reserved in the alias rule and the census shows no planet input moves); the MCP surface and tool-search index (descriptor gains `entity_class`, regenerated after #2984); `source_query_availability.ts` contract (updated in the PR); Kala/Pravaha are not readers of the changed names. `list_entities` consumers see `text` 15 -> 16 rows and `dasha_system`/`dosha` unchanged in count.

## 7 · Rollback summary and safety nets

| level | rollback | data lost on rollback |
|---|---|---|
| 0 | prior check text (guard) + initcap UPDATE for the 7 rows + old code rebuild | none (old values are in the PR diffs and the saved pre-state) |
| 1 | prior check text + old-code rebuild of bg_doshas | none |
| 2 | prior check text + `SET confidence = quality_score` (+ default/NOT NULL) or old-code rebuild | none (equal columns) |
Every reseal guard refuses to run if the registry text is not the expected prior text, and refuses a second run.

## 8 · Findings, surprises and limits

* **W-1 (pre-existing, main):** `ENTITIES` carries 5 co-writer dasha_system entries; `jaimini_chara` does not exist in the catalogue (`chara_jaimini`) and is inserted by every bg_ontology rebuild (DO NOTHING when absent). Proposed one-line fix (not in these PRs): remove entity_class in CO_WRITER_ENTITY_CLASSES from `ENTITIES`, since bg_ontology does not own them. Until then, rebuild `bg_dasha_systems` right after `bg_ontology`.
* **Cross-table convention split (reported, not widened):** only `bg_transit_rules.graha` mixes cases inside one column; the other L0 planet columns are uniformly Title case (`bg_combustion_orbs`, `bg_dignity_reference`, `bg_graha_*`, `bg_kp_sublord_division`, `bg_medical_mappings`, `bg_motion_state_thresholds`, `bg_phaladeepika_latta`, `bg_prashna_significators`, `bg_sky_calendar`, `bg_synthetic_cohort_md`, `bg_transit_av_gates` (Jupiter x4/Saturn x4), `bg_vastu_directions`, `bg_gochara_arcs.body`, `ephemeris_daily.body`) while `bg_transit_rules`/`bg_transit_engine` are lowercase. "Canonical lowercase" is therefore true of the transit pair and the ontology ids, not of L0 as a whole. scan: `out/mixedcase_scan.txt`.
* TI-L0-10: Appendix A of `WAVE_PLACEHOLDER_DISPOSITIONS.md` had Mars 8th as Sloka 16; the page text shows Sloka 15 (spans `PG326:C1`/`PG327:C1`). Corrected in the PR. OCR text: every mapping needs the acharya's spot-check.
* TI-L0-13 side finding: old `resolve()` crashed on any entity with `canonical_name_sa = None` (the new `nadi_navamsa_patel`); fixed. Merge note: PR #3053 and #3050 both edit the old `resolve` (3053 a one-line None guard, 3050 replaces the function by a shim) - take #3050's version; verified in the scratch merge, the only conflict among the 8 Python PRs.
* The sealed checks are the real gate: a wave that forgets a reseal fails and rolls itself back (safe, but wasteful). Every L0 check the wave can touch was evaluated on the copies (all TRUE before; faithful copies): after the level-0 run `bg_ontology` TRUE and `bg_yogas` TRUE (yoga rows untouched), `bg_dasha_systems` **FALSE** (W-1: 21 dasha ontology rows), then TRUE again after `bg_dasha_systems` ran (back to 20); after bg_doshas `bg_doshas`, after the transit run `bg_transit_rules`, and after the confidence change `bg_rules` read FALSE on the old text and TRUE on the drafted text. The medical trio (record-only, no row change), the citation table (14 identical rows; migration 631's digest proven TRUE in the real-PG test) and the grid (no check) need no reseal.
* Limits: the referrer text census covered `bg_*`, `brahma_*`, `reference_*`, `classical*`, `sutravali*`, `gochara*` tables; `bodha_*/kala_*/phala_*/mimamsa_*` were not text-scanned (source scan covers code). Simulations ran on copies, not on production; the real run's pre-state read-back is the guard. Live-mode `test_has_writer_completeness` stays red until M-A2.

## 9 · Reproduce

`/Users/Dev/suvarna-evidence/TrackI/l0d/`: `rq.sh` (read-only query helper), `clone.py` (read-only copy of public L0 tables into the disposable PG), `evalcheck.py` (evaluate a sealed check + recompute its digests), `wave_sim_ontology.py`, `wave_sim_transit.py`, `rules_dryrun.py`, `served_ids_census.py`, `make_reseal_drafts.py`, `mutate.py`/`mutate_ts.py`, `out/*` (cell diffs, census, mutation outputs), `drafts/*` (the SQL below).

## Appendix - DRAFT SQL (no migration numbers; NOT in `platform/migrations/`; SS allocates)

### A. M-A1 `DRAFT_NEEDS_NUMBER_bg_transit_rules_citations_and_case_reseal.sql`
```sql
-- DRAFT_NEEDS_NUMBER: SS allocates the migration number (block 1200-1299). NOT in platform/migrations/.
-- Reseal of bg_transit_rules.integrity_check_sql for the L0 data wave.
-- TI-L0-10 (24 citations re-sourced) + SS graha-case fix (7 rows lower-cased in place): the rules-section digest covers graha and classical_citation. bg_transit_engine / moorti sections are byte-identical.
-- ORDER: apply BEFORE the bg_transit_rules rebuild (the orchestrator runs integrity_check_sql AFTER the write and rolls the
-- rebuild back if it reads false). Between this migration and the rebuild the check reads FALSE against the old rows
-- (expected, a few minutes); roll back by re-applying the prior text (kept in the guard below).
-- Registry metadata only; transaction ownership belongs to migrate.ts.
DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  prior_check constant text := $prior$SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
  AND (SELECT count(*) = 76 FROM bg_transit_rules)
  AND (SELECT count(*) FILTER (WHERE rule_type = 'favourable') = 43
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       FROM bg_transit_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') =
    '1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d'
  FROM bg_transit_rules)
  AND (SELECT count(*) = 27 FROM bg_transit_moorti)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_offset,moorti_name,quality_tier,phala_brief,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY nakshatra_offset
  ),''),'UTF8')),'hex') =
    'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450'
  FROM bg_transit_moorti)
$prior$;
  new_check constant text := $new$SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
  AND (SELECT count(*) = 76 FROM bg_transit_rules)
  AND (SELECT count(*) FILTER (WHERE rule_type = 'favourable') = 43
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       FROM bg_transit_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') =
    'e401846964d3a9cf0416bbad5c408cd5041346300b6aa7786ff15079c5652d6b'
  FROM bg_transit_rules)
  AND (SELECT count(*) = 27 FROM bg_transit_moorti)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_offset,moorti_name,quality_tier,phala_brief,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY nakshatra_offset
  ),''),'UTF8')),'hex') =
    'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450'
  FROM bg_transit_moorti)
$new$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'reseal refuses: bg_transit_rules registry row missing';
  END IF;
  IF registry_row.integrity_check_sql IS DISTINCT FROM prior_check THEN
    RAISE EXCEPTION 'reseal refuses: bg_transit_rules integrity_check_sql is not the pre-wave contract (already resealed, or drifted)';
  END IF;
  UPDATE asset_registry SET integrity_check_sql = new_check WHERE asset_id = 'bg_transit_rules';
  IF NOT FOUND THEN RAISE EXCEPTION 'reseal expected 1 row'; END IF;
END $$;
```

### B. M-B1 `DRAFT_NEEDS_NUMBER_bg_doshas_alias_sets_reseal.sql`
```sql
-- DRAFT_NEEDS_NUMBER: SS allocates the migration number (block 1200-1299). NOT in platform/migrations/.
-- Reseal of bg_doshas.integrity_check_sql for the L0 data wave.
-- TI-L0-12: the 79 dosha ontology rows now carry closed alias sets (synonyms), which the sealed ontology-section digest covers.
-- ORDER: apply BEFORE the bg_doshas rebuild (the orchestrator runs integrity_check_sql AFTER the write and rolls the
-- rebuild back if it reads false). Between this migration and the rebuild the check reads FALSE against the old rows
-- (expected, a few minutes); roll back by re-applying the prior text (kept in the guard below).
-- Registry metadata only; transaction ownership belongs to migrate.ts.
DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  prior_check constant text := $prior$SELECT
  (SELECT count(*) = 79 FROM brahma_dosha_catalog)
  AND (SELECT count(*) = 79 FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT count(*) = 79 FROM reference_doshas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0
    AND cardinality(associated_remedies)=0) = 79 FROM brahma_dosha_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dosha_catalog AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='dosha') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_doshas AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,effects_text,severity_grades,cancellation_conditions,
      classical_citations,source_chunk_ids,associated_remedies,school)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'cfb21a5342bda3a911f55597cac3367b727a79953ccef3349ad7f49c98acfcd4'
   FROM brahma_dosha_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'ee5dedf6e9934f42883ff268c3e485648577c6e528bfb76b7b839937b4572984'
   FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '3fd442d6e8bfcb54fa5f4752907a2ef057ab1f49ec12aad9536a833b4e04d9a4'
   FROM reference_doshas)
$prior$;
  new_check constant text := $new$SELECT
  (SELECT count(*) = 79 FROM brahma_dosha_catalog)
  AND (SELECT count(*) = 79 FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT count(*) = 79 FROM reference_doshas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0
    AND cardinality(associated_remedies)=0) = 79 FROM brahma_dosha_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dosha_catalog AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='dosha') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_doshas AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,effects_text,severity_grades,cancellation_conditions,
      classical_citations,source_chunk_ids,associated_remedies,school)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'cfb21a5342bda3a911f55597cac3367b727a79953ccef3349ad7f49c98acfcd4'
   FROM brahma_dosha_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'd036ad30c5734e4bcd5e8313b0a9b27a9fb9b2504efc3a88185c2b4659dd58ce'
   FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '3fd442d6e8bfcb54fa5f4752907a2ef057ab1f49ec12aad9536a833b4e04d9a4'
   FROM reference_doshas)
$new$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_doshas' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'reseal refuses: bg_doshas registry row missing';
  END IF;
  IF registry_row.integrity_check_sql IS DISTINCT FROM prior_check THEN
    RAISE EXCEPTION 'reseal refuses: bg_doshas integrity_check_sql is not the pre-wave contract (already resealed, or drifted)';
  END IF;
  UPDATE asset_registry SET integrity_check_sql = new_check WHERE asset_id = 'bg_doshas';
  IF NOT FOUND THEN RAISE EXCEPTION 'reseal expected 1 row'; END IF;
END $$;
```

### C. M-C1 `DRAFT_NEEDS_NUMBER_sutravali_rules_confidence_nullable.sql`
```sql
-- DRAFT_NEEDS_NUMBER: SS allocates the migration number (block 1200-1299). NOT in platform/migrations/.
-- TI-L0-23 (SS Q9): bg_rules stores confidence = NULL ("not scored"). sutravali_rules.confidence is NUMERIC NOT NULL
-- DEFAULT 0.0 (migration 081). Relax it: drop NOT NULL and the 0.0 default (a default of 0.0 would itself be a fake score
-- for any insert that omits the column). The CHECK (confidence >= 0 AND confidence <= 1) already admits NULL.
-- ORDER: apply BEFORE the bg_rules rebuild; the writer's pre-flight refuses (before it deletes anything) if this has not run.
-- Additive/relaxing only; no row changes; the rebuild writes the NULLs. Rollback: UPDATE ... SET confidence = quality_score;
-- ALTER ... SET DEFAULT 0.0, SET NOT NULL (only after the rebuild is reverted).
DO $$
DECLARE
  col_nullable text;
BEGIN
  SELECT is_nullable INTO col_nullable FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'sutravali_rules' AND column_name = 'confidence';
  IF col_nullable IS NULL THEN
    RAISE EXCEPTION 'sutravali_rules.confidence missing';
  END IF;
  IF col_nullable = 'YES' THEN
    RAISE NOTICE 'sutravali_rules.confidence already nullable; nothing to do';
    RETURN;
  END IF;
  ALTER TABLE sutravali_rules ALTER COLUMN confidence DROP NOT NULL;
  ALTER TABLE sutravali_rules ALTER COLUMN confidence DROP DEFAULT;
END $$;
```

### D. M-A2 `DRAFT_NEEDS_NUMBER_l0_static_writers_has_writer.sql`
```sql
-- DRAFT_NEEDS_NUMBER: SS allocates the migration number (block 1200-1299). NOT in platform/migrations/.
-- TI-L0-20 (SS Q7 / Q21): bg_gochara_citation_resolution and bg_sarvatobhadra_grid now have @register writers; the plan
-- resolver gates on `is_active AND has_writer`, so the registry must say so (tests/test_has_writer_completeness.py documents this
-- two-step rule). Guarded by the old value so it cannot silently re-run; fails if either row is absent.
-- R9: flipping has_writer makes the asset DISPATCHABLE; bg_gochara_citation_resolution (R9) is not dispatched until SS has
-- notified Pravaha. The asset_registry seed literal (platform/scripts/seed/asset_registry_seed.ts) is a PR #2984 file and is
-- changed after #2984 lands.
DO $$
DECLARE
  n integer;
BEGIN
  UPDATE asset_registry SET has_writer = true
   WHERE asset_id IN ('bg_gochara_citation_resolution', 'bg_sarvatobhadra_grid') AND has_writer IS DISTINCT FROM true;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 2 THEN
    RAISE EXCEPTION 'expected to flip exactly 2 has_writer flags (both false), changed %', n;
  END IF;
END $$;
```

### E. M-C2 `DRAFT_NEEDS_NUMBER_bg_rules_confidence_not_scored_reseal.sql`
```sql
-- DRAFT_NEEDS_NUMBER: SS allocates the migration number (block 1200-1299). NOT in platform/migrations/.
-- Reseal of bg_rules.integrity_check_sql for the L0 data wave.
-- TI-L0-23: confidence is NULL by design (not scored); the sealed check asserted confidence = quality_score on every row. The clause becomes 'confidence IS NOT NULL = 0' and the digest covers the NULLs.
-- ORDER: apply BEFORE the bg_rules rebuild (the orchestrator runs integrity_check_sql AFTER the write and rolls the
-- rebuild back if it reads false). Between this migration and the rebuild the check reads FALSE against the old rows
-- (expected, a few minutes); roll back by re-applying the prior text (kept in the guard below).
-- Registry metadata only; transaction ownership belongs to migrate.ts.
DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  prior_check constant text := $prior$SELECT
  count(*) = 3002
  AND count(DISTINCT rule_id) = 3002
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002
  AND count(*) FILTER (WHERE confidence < 0.600 OR quality_score < 0.600) = 0
  AND count(*) FILTER (WHERE confidence IS DISTINCT FROM quality_score) = 0
  AND count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) = 17
  AND count(*) FILTER (WHERE dasha_system_id IS NOT NULL) = 0
  AND count(*) FILTER (WHERE transit_marker IS TRUE) = 25
  AND NOT EXISTS (
    SELECT 1 FROM sutravali_rules AS rule
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.text_id = rule.text_id
    )
       OR (rule.yoga_canonical_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_yoga_catalog AS yoga
         WHERE yoga.canonical_id = rule.yoga_canonical_id
       ))
       OR (rule.dasha_system_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_dasha_systems AS dasha
         WHERE dasha.canonical_id = rule.dasha_system_id
       ))
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,dasha_system_id,transit_marker)::text,
    E'\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') =
    '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
FROM sutravali_rules
$prior$;
  new_check constant text := $new$SELECT
  count(*) = 3002
  AND count(DISTINCT rule_id) = 3002
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002
  AND count(*) FILTER (WHERE quality_score < 0.600) = 0
  AND count(*) FILTER (WHERE confidence IS NOT NULL) = 0
  AND count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) = 17
  AND count(*) FILTER (WHERE dasha_system_id IS NOT NULL) = 0
  AND count(*) FILTER (WHERE transit_marker IS TRUE) = 25
  AND NOT EXISTS (
    SELECT 1 FROM sutravali_rules AS rule
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.text_id = rule.text_id
    )
       OR (rule.yoga_canonical_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_yoga_catalog AS yoga
         WHERE yoga.canonical_id = rule.yoga_canonical_id
       ))
       OR (rule.dasha_system_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_dasha_systems AS dasha
         WHERE dasha.canonical_id = rule.dasha_system_id
       ))
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,dasha_system_id,transit_marker)::text,
    E'\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') =
    'bb72c32b6699e1958ad3a7c8bd9ed70928b8de2792b5d5edb0a110bb90dcf948'
FROM sutravali_rules
$new$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'reseal refuses: bg_rules registry row missing';
  END IF;
  IF registry_row.integrity_check_sql IS DISTINCT FROM prior_check THEN
    RAISE EXCEPTION 'reseal refuses: bg_rules integrity_check_sql is not the pre-wave contract (already resealed, or drifted)';
  END IF;
  UPDATE asset_registry SET integrity_check_sql = new_check WHERE asset_id = 'bg_rules';
  IF NOT FOUND THEN RAISE EXCEPTION 'reseal expected 1 row'; END IF;
END $$;
```

