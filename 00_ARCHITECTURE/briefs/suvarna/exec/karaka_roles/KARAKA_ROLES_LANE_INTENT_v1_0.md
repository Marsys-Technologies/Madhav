---
artifact: KARAKA_ROLES_LANE_INTENT
version: 1.1
status: DRAFT-FOR-REVIEW
produced_by: worker for exec-suvarna
date: 2026-10-02
lane: S-L1 mandatory — karaka roles (TI-l1-karaka-roles-001)
branch: suvarna/land/TI-l1-karaka-roles-001 (local commits only; not pushed)
decision: SS N-69 (binding rulings, section 3)
scope: L1 writer code + tests + generated governance artefacts + this intent document. No migration, no seed edit, no TypeScript, no database write.
changelog:
  - "1.1 (2026-10-03): id-change correction (N-91 condition 6). 'The kn_rao PUTRAKARAKA / GNATIKARAKA / DARAKARAKA ids are unchanged' held only against the writer formula, not against stored production ids, which all change once at S-L1. One bullet of section 8 corrected; nothing else changed."
  - "1.0 (2026-10-02): first version. Facts, rulings, exact code changes, registry-edge intent (file not written), consumer trace, held items, rebuild effect, verification, not-verified."
---

# Karaka roles lane — intent document

## 1. What this lane fixes

1. `ga_sensitive` labelled the ranks of the **kn_rao_rahu_included** (8-karaka) school with the 7-scheme list plus STRIKARAKA. Ranks 5-8 were therefore mislabelled on every chart and ayanamsha (verified in stored data on all 15 chart x ayanamsha sets, by the lane brief).
2. `ga_vargas` carried its **own** karaka derivation (`_compute_jaimini_karakas`) that ranked Rahu by plain degree-in-sign (ga_sensitive reckons Rahu as `30 - long % 30`) and used a shifted name list (`PK GK DK SK`). It disagreed with ga_sensitive on Rahu's rank and on every label from rank 5.

## 2. Verified facts

Verified by reading the code at `origin/main` 932cf3a01 and by running it:

- `ga_sensitive_writer._build_karaka_rows` emitted `karaka_chara_position` for `parashari_rahu_excluded` (7 grahas) and `kn_rao_rahu_included` (8 grahas) with ONE label list for both: ATMAKARAKA AMATYAKARAKA BHRATRIKARAKA MATRIKARAKA PUTRAKARAKA GNATIKARAKA DARAKARAKA STRIKARAKA. The 7-scheme labels were right; the kn_rao ranks 5-8 were not.
- Canonical chart 482012f1, Lahiri, kn_rao (rank, graha, degree-in-sign): 1 Moon 27.055230, 2 Saturn 22.431986, 3 Sun 21.962617, 4 Venus 19.172696, 5 Mars 18.519188, 6 Rahu 19.033044 (sorted as 30 - 19.033044 = 10.966956), 7 Jupiter 9.787497, 8 Mercury 0.838754. Correct 8-scheme roles: AK Moon, AmK Saturn, BK Sun, MK Venus, PiK Mars, PK Rahu, GK Jupiter, DK Mercury. Parashari 7-scheme: AK Moon, AmK Saturn, BK Sun, MK Venus, PK Mars, GK Jupiter, DK Mercury (Matrikaraka doubles as Pitrikaraka).
- Corroboration found in the repo (not relied on): the legacy forensic extraction `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` section 10.3 rows 5-8 lists the 8-karaka system for the native as Putrakaraka = Rahu ("DIFFERS from 7-karaka; Mars was PK"), Pitrukaraka = Mars ("NEW role"), Gnatikaraka = Jupiter, Darakaraka = Mercury. This matches the ruled order exactly.
- `ga_vargas` registry dependency is `{ga_positions}`; `ga_sensitive` is `{ga_positions, bg_reference}` (seed `platform/scripts/seed/asset_registry_seed.ts`, read only). `ga_sensitive` does not read `chart_divisionals` or any `ga_vargas` output (grep of `ga_sensitive_writer.py` for `chart_divisionals` / `ga_vargas` finds only a docstring I added), and its ancestors (`ga_positions` with no deps, `bg_reference` -> `bg_ontology`) do not reach `ga_vargas`.
- BPHS 32.13-17 as the source of the 8-scheme order is **sourced_ocr_unverified**; the J1 print-edition check is pending. The role order is therefore ruled, not print-verified.

## 3. Rulings (SS N-69, binding)

- Headline school = `kn_rao_rahu_included`; `parashari_rahu_excluded` stays the named variant.
- 8-scheme list = `[ATMAKARAKA, AMATYAKARAKA, BHRATRIKARAKA, MATRIKARAKA, PITRIKARAKA, PUTRAKARAKA, GNATIKARAKA, DARAKARAKA]`. The 7-scheme list is unchanged.
- STRIKARAKA is a labelled **alias fact_key on the DARAKARAKA subject** (same graha), not a ninth subject row, not a STRIKARAKA subject.
- `ga_vargas` READS ga_sensitive's kn_rao assignments (no recomputation; this also fixes its Rahu reckoning); names `AK AmK BK MK PiK PK GK DK`.

## 4. Exact code changes (branch commits, in order)

All paths under `platform/python-sidecar/` unless stated.

1. `ga_writers/_karaka_roles.py` (new, vocabulary only, no computed value): school ids, `KARAKA_ROLES_7`, `KARAKA_ROLES_8`, `KARAKA_ALIAS_SUBJECT='DARAKARAKA'`, `KARAKA_ALIAS_FACT_KEY='strikaraka_alias'`, `KARAKA_ALIAS_LABEL='STRIKARAKA'`, `KARAKA_ABBREVIATIONS_8`. A shared module so the two writers cannot drift on names (N.7 item 3). The writer-digest inventory follows local imports, so it is covered by the writers' digests.
2. `ga_writers/ga_sensitive_writer.py::_build_karaka_rows`: per-school role list and per-school `formula_provenance_text` ("Jaimini Sutram 7-karaka system" for parashari; "Jaimini Sutram 8-karaka system; role order per BPHS 32.13-17 (sourced_ocr_unverified, print-edition check pending)" for kn_rao; the old text said "8-karaka" for the 7-karaka school). Sort logic, ranks, longitudes, degrees, signs, houses untouched. New row: `karaka_chara_position / DARAKARAKA / strikaraka_alias`, `fact_value_text='STRIKARAKA'`, `formula_id='kn_rao_rahu_included'`, tier = the builder's default `TWO_PASS_VERIFIED` via `_make_row` (see 10, decision D1). A size-mismatch guard raises if a scheme's graha count and role-list length ever disagree. `_build_karakamsa_rows` and the AK-divergence block (about lines 1081-1112, `_build_brahma_vishnu_shiva_rows`) were checked and left alone: they read rank 1, which is ATMAKARAKA in both schools and unchanged. (Karakamsa and Brahma/Vishnu/Shiva pick AK by the same logic as before; that a 7-grahas-only AK feeds karakamsa while a kn_rao AK exists is pre-existing and out of scope.)
3. `ga_writers/CHART_FACTS_SCHEMA.json` (the ga_writers copy that enumerates `karaka_chara_position`): `applies_to_subjects` STRIKARAKA -> PITRIKARAKA (re-ordered), new `subject_note`, new allowed key `strikaraka_alias`; `karaka_per_varga` note updated. The other `CHART_FACTS_SCHEMA.json` at `platform/scripts/governance/` has a stale, unrelated `karaka_chara_position` entry (subject `GRAHA`, keys `graha`/`karaka_designation`/`graha_longitude`...) that matches no writer today; it was NOT edited (see 10).
4. `brahmagyan/fact_identity_parser.py`: `KNOWN_KARAKA_ROLES += PITRIKARAKA`. `STRIKARAKA` stays recognised during the transition because stored pre-rebuild rows still carry that subject (otherwise they become an unclassified `real_gap`); drop it once every chart is rebuilt.
5. `ga_writers/ga_vargas_writer.py`: `_compute_jaimini_karakas` removed. New `_read_jaimini_karakas(conn, chart_id, ayanamsha_id)` runs one `chart_facts` SELECT: `fact_category = 'karaka_chara_position'`, `fact_key IN ('assigned_graha','karaka_rank')`, `formula_id = 'kn_rao_rahu_included'`, `ORDER BY fact_subject, fact_key, fact_id`, on the writer's own connection (tuple row cursor). The pure core `_karakas_from_rows` maps `karaka_rank` to `AK AmK BK MK PiK PK GK DK` (rank, not subject-name parsing, so pre-rebuild mislabelled rows still map correctly). Absent rows, NULL/duplicate rows, mismatched subject sets or ranks that are not a 1..8 permutation raise `KarakaDependencyMissing` (a `RuntimeError`) naming ga_sensitive as the missing dependency: no silent recompute (N.7 item 6). `_resolve_karakas_in_varga` places each assigned graha in a varga (sign, dignity). `_build_karaka_rows` now takes the assignment map instead of D1 longitudes. `JAIMINI_KARAKA_NAMES` / `JAIMINI_KARAKA_FULL` updated (PiK Pitri_Karaka, PK Putra_Karaka, GK Gnati_Karaka, DK Dara_Karaka; SK / Saptama_Karaka removed). The read happens once per ayanamsha at the top of the per-ayanamsha connection block in `build_ga_vargas`. `formula_provenance_text` for the rows now reads `Jaimini_8_karaka_kn_rao_rahu_included_read_from_ga_sensitive`.
6. Tests: `tests/test_ga5_writer.py` (new `TestKarakaRolesGolden`: canonical Lahiri degrees through the real `_build_karaka_rows`, both schools, alias key, no STRIKARAKA subject, no PITRIKARAKA in the 7-scheme, row counts 49 and 57, no numeric drift on Rahu, schema consistency), `tests/test_ga6_writer.py` (reader mapping golden with a stubbed cursor, old-label rows, query pins, loud failures; builder tests updated), `tests/test_fact_identity_parser.py`, `tests/test_ga8_writer.py` (fixture role list only; ga_structural source is unchanged).
7. Generated/governance artefacts: `platform/src/generated/nirmana-writer-digests.json` (asset ids moved: `ga_sensitive`, `ga_vargas`, nothing else), `platform/src/generated/capability_estate_census.json` (writer-digest sha, content sha, `generated_at`; `source_revision` left at the committed value), E6 line pins (`platform/scripts/governance/asset_declarations.json` evidence text and `platform/scripts/governance/__tests__/test_e6_1_declarations.py` CITATION_DECISIONS: ga_sensitive 246 -> 255 and 2963 -> 3009; ga_vargas 1202 -> 1287, 1651 -> 1736, 2609 -> 2698, 2638 -> 2727; AST site counts unchanged), and the attribution hook `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/karaka_roles.json`.

## 5. Registry-edge intent (migration NOT written; owner hold)

- **Edge:** `ga_vargas depends_on += ga_sensitive`.
- **DAG check:** no cycle. `ga_sensitive` reads only `ga_positions` and `bg_reference`; neither depends on `ga_vargas`; `ga_sensitive` does not read `chart_divisionals`. The edge is also not a back-read: no asset on a path from `ga_sensitive` depends on `ga_vargas`. (`ga_structural` already depends on both, so its ordering is unchanged.) I did not run the live registry graph; this is from the seed and the code. The existing `tests/test_migration_1210_direct_edges.py` cycle checker (`dag_edge_guard`) is the right tool to re-run on the edges migration.
- **Rides:** the edges migration, number to be allocated by SS. File not written. The TypeScript seed (`depends_on: ['ga_positions']` for `ga_vargas`) is bootstrap-only (a re-seed never rewrites an existing row) and was not edited; the migration must carry the live change and the seed should be kept in step in the same PR (`asset_registry_seed_dag_parity.test.ts` and `test_migration_1210_direct_edges.py` model that pairing).
- **Why it is needed even though no check is red today:** the census reads-match detector and `dag_edge_guard` treat `chart_facts` as a SOFT table (satisfied by ANY `chart_facts` producer in the declared transitive closure; `ga_positions` already is one), so neither flags the new read. The wave-parallel scheduler can therefore run `ga_vargas` and `ga_sensitive` in the same wave. With this branch's reader that fails loudly (`KarakaDependencyMissing`) instead of silently mis-deriving, but only the edge makes the order deterministic. **Landing order: land the edge before, or with, any rebuild that runs `ga_vargas` on a chart whose `ga_sensitive` has not been built.** For already-built charts the reader works without the edge (it needs the rows to exist, not to be fresh).
- **Registry volume fields (aspirational, not a gate):** `ga_sensitive` gains exactly 1 row per (chart, ayanamsha): `expected_volume_formula '1755 * AYANAMSHAS'` becomes `1756 * AYANAMSHAS` and `target_floor 8775` becomes `8780` per chart (5 ayanamshas), if SS wants them kept equal to the achieved count (floors-aspirational rule). `karaka_per_varga` row count is unchanged (8 karakas x 3 keys per varga).

## 6. Consumer trace

### 6a. `karaka_per_varga` (chart_divisionals)

`git grep karaka_per_varga` over py/ts/json/sql (excluding docs, archive, evals) finds: the writer, its tests, `CHART_FACTS_SCHEMA.json`, `platform/src/generated/harvest/e3_fact_category_reconciliation.json` (a category list), and eval transcripts under `evals/omega7/` (historical tool output). **No code consumer outside ga_vargas.** Generic readers of `chart_divisionals` by `fact_category` (checked file list: `get_divisionals.ts`, `address_resolver.ts`, `get_chart_snapshot.ts`, `get_argala.ts`, `register_d9_judgment.ts`, `register_d7_channel.ts`, `reading_checklist.ts`, `query_mechanisms.ts`, platform-mcp `registry_bridge.ts`, pariprashna `scope.ts`/`lexicon.ts`/`citation_resolver.ts`) were checked by a `karaka` / `ATMAKARAKA` grep: none selects or names `karaka_per_varga` rows or the `SK`/`PK` subjects. A generic `get_divisionals` page would simply serve the renamed subjects. Not verified at runtime (no database).

### 6b. Karaka role LABELS (`karaka_chara_position` subjects)

| consumer | what it does with labels | effect of this lane | action |
|---|---|---|---|
| `ga_structural_writer._build_karaka_web_rows` (about 5664-5775) | reads kn_rao `assigned_graha` rows (formula pinned); `role_a`/`role_b` strings in `value_jsonb`/`citation_human` come from the stored subject | planet set is label independent; strings change on the next ga_structural rebuild | none in code; must be rebuilt after ga_sensitive. NOTE a pre-existing order dependence, section 7 |
| `bo_upaya._fetch_chara_roles` (line 393) | `fact_key.split(':')[0]` is always `assigned_graha` etc., never a graha, so it returns `{}` and `chara_role` is always `None` in every resonance | none today (always empty) | L2 batch, section 7. NOT fixed here |
| `bo_laksana` (lines 294, 536, 1545) | whole category by name; resolves a graha by `_infer_graha_from_text(fact_value_text)` | the alias row's text `STRIKARAKA` infers no graha (`None`, checked by running it); assigned_graha rows unchanged | none; rebuild L2 after L1 (fact_ids, section 8) |
| `address_resolver.ts` `KARAKA_CODE_TO_SUBJECT` (146-154) and `fetchKarakaRow` (577-600) | code -> subject map; reads value rows with NO school pin | PiK missing; SK maps to a subject that will no longer exist; the "schools agree" comment is false (section 7) | HELD PR #2866 |
| `get_karakas.ts` | serves `karaka_chara_position` by category; no per-label logic found | will serve the new subjects and the alias key as rows | tool-text batch: mention alias key |
| `chart_reader_v4.special_points(kind='karaka')` | returns every `karaka_chara_position` row of both schools; its live test asserts DARAKARAKA carries both `karaka_school` values | still true after the fix (DARAKARAKA exists in both schools) | none |
| `brahmagyan/fact_identity_parser.py` | recognised role tokens | PITRIKARAKA added; STRIKARAKA kept for transition | done (commit 1) |
| `platform-mcp/src/resources/school_conventions.ts` (47-48) | prose: "7-karaka: AK AmK BK MK PiK PK GK ... 8-karaka: adds DK" | text is wrong against the ruling | tool-text batch, section 7 |
| `platform-mcp/resources/chart-overview.md` (31-33, 69) | static table "Putrakaraka (PK) Mars ... Darakaraka Mercury" (7-scheme reading) | under the headline school PK is Rahu and Mars is PiK | tool-text batch |
| `platform/scripts/governance/registry_parity_gate.py` (409) | comment only | none | none |
| `tests/test_chart_reader_v4.py:212` (DB), `tests/test_ga8_writer.py`, `tests/test_l1_sensitive_points.py` | label-based assertions | pass | none |
| `ga_dashas_writer._JAIMINI_KARAKAS` (646) and `_vimshottari_independent_verifier` copy | hard-coded graha -> role map ("FORENSIC chart": Sun AK, Mars AmK, Mercury BK, Saturn MK, Jupiter PK, Venus GK, Moon DK) applied to EVERY chart for `karaka_role_at_period` | independent of this lane, but see section 7 | report to SS |
| `brahmagyan/l0_reference.py` (569-575, 1172-1175), `l0_ontology.py` (381-391), `l0_rules.py` (90) | L0 reference rows: putrakaraka "5th-highest", darakaraka "7th-highest", strikaraka "8th-highest" | encode the OLD ranks (7-scheme ranks plus a Strikaraka as 8th); not edited (L0 seed, migration territory) | report to SS |

## 7. What stays for held work

**Held PR #2866 (address resolver / reader contract):**
- `KARAKA_CODE_TO_SUBJECT` gets `PIK: 'PITRIKARAKA'` (codes are upper-cased before lookup, so `PIK`); `PK`, `GK`, `DK` keep their subjects; `SK` must stop resolving to a `STRIKARAKA` subject (resolve it to the DARAKARAKA subject as the alias, or reject with a pointer to `strikaraka_alias`).
- `fetchKarakaRow` must pin `formula_id` to the requested school (default headline `kn_rao_rahu_included`). Its comment claims the two schools agree for every shared karaka; that was already false on the canonical chart before this lane (GNATIKARAKA was Jupiter under parashari and Rahu under kn_rao) and stays false after it (PUTRAKARAKA: Mars parashari, Rahu kn_rao). With no pin and no ORDER BY, which row wins is undefined. A request for PiK under the parashari school should return an honest "not a role in this scheme (the Matrikaraka doubles as Pitrikaraka)", not fall through to kn_rao.
- `address_resolver.test.ts` fixtures follow.

**Tool-text batch:** `school_conventions.ts`: 7 = AK AmK BK MK PK GK DK (MK doubles as PiK); 8 = AK AmK BK MK PiK PK GK DK, with Rahu; Strikaraka is an alias of the Darakaraka. `chart-overview.md` static table. `get_karakas.ts` description: mention the `strikaraka_alias` key.

**L2 batch item (J1 name: "bo_upaya karaka roles were always empty"):** `bo_upaya._fetch_chara_roles` parses `fact_key.split(':')[0]` and so never matches a graha; it returns `{}` and `chara_role` has been `None` in every resonance. A fix must read `fact_subject` + `assigned_graha` pinned to one school (it currently selects the whole category; there is a fact-category-pin allowlist entry for this query in `platform/scripts/governance/fact_category_pin_allowlist.json` that the fix should retire) and map `PITRIKARAKA/...` to the role abbreviation it wants. NOT fixed in this lane.

**Found while tracing, not fixed (report to SS):**
1. `ga_structural._build_karaka_web_rows` reads the kn_rao `assigned_graha` rows with no ORDER BY and tests aspect only from the earlier planet of each pair to the later one, so aspect rows depend on the (unspecified) row order. A ga_structural rebuild can flip aspect rows independently of this lane. The attribution hook lists the category for that reason.
2. `ga_dashas_writer._JAIMINI_KARAKAS` is a hard-coded native-chart map presented as the chara karakas (Sun AK, Mars AmK, Mercury BK, Saturn MK, Jupiter PK, Venus GK, Moon DK) and is applied to every chart; it also disagrees with L1's stored AK (Moon) for the native. A wrapper-local constant shadowing an L1 value (N.7 item 3). Out of scope here.
3. L0 reference/ontology rows for the Jaimini karakas encode the old ranks (table above).
4. The `platform/scripts/governance/CHART_FACTS_SCHEMA.json` `karaka_chara_position` entry is stale and unrelated to the writer.
5. Alias tier: see D1 below.

## 8. What a rebuild changes (15 chart x ayanamsha sets)

Per (chart, ayanamsha), after rebuilding ga_sensitive, ga_vargas, ga_structural:

- `karaka_chara_position` (chart_facts): kn_rao: PITRIKARAKA subject appears (7 keys), the STRIKARAKA subject disappears (7 keys), PUTRAKARAKA / GNATIKARAKA / DARAKARAKA take the next rank's graha (assigned_graha, sign, karaka_rank, house_d1 change); `strikaraka_alias` appears once on DARAKARAKA. Parashari rows unchanged. Row count 105 -> 106. Nothing numeric moves for any graha (golden test asserts Rahu's stored longitude 49.033044 and degree-in-sign 19.033044 unchanged).
- Canonical Lahiri, simulated offline (old origin/main builder vs this branch, through the committed `flip_detector.compare_states`, with this lane's hook loaded): 23 class changes (12 value, 6 appeared, 5 disappeared), 0 unattributed. The simulation script is not committed.
- `karaka_per_varga` (chart_divisionals): subjects renamed (`D1.PK/GK/DK/SK` become `D1.PiK/PK/GK/DK`), Rahu's rank follows ga_sensitive's reckoning. Row count unchanged. The detector keys these rows by assigned graha, so it sees no change (hook entry with `expected_count exact 0`).
- `karaka_web_per_varga`: role strings in `value_jsonb` / `citation_human` follow the stored labels on the ga_structural rebuild. ga_structural's own digest does NOT move in this branch (its source is unchanged), so nothing marks it stale: it must be rebuilt explicitly, after ga_vargas (it already depends on both).
- fact_ids: ga_sensitive ids hash `(category, subject, key, chart, ayanamsha, formula_id)` (no `build_id`). THIS lane does not change the hash of any surviving natural key: the kn_rao PUTRAKARAKA / GNATIKARAKA / DARAKARAKA natural keys keep the id the writer formula gives them, and now carry a different graha; STRIKARAKA ids are orphaned; PITRIKARAKA ids are new. This is NOT a statement about the ids STORED in production: stored `karaka_chara_position` ids are sha256(...|build_id|formula_id) (525 of 525 canonical rows), so ALL of them, kn_rao included, change once at S-L1 together with every other non-`ga_positions` id (142,094 of 143,299 `chart_facts` ids on the canonical chart), and are stable from the second build (`/Users/Dev/suvarna-evidence/FactId/FACTID_IMPACT_REPORT.md` P4; `S_L1_BETWEEN_STATE_v1_0.md`). Corrected 2026-10-03 (v1.1). Any L2+ row that cited those ids (for example bo_* evidence chains) keeps pointing at the same id with a changed value: rebuild L2 after L1. I did not quantify L2 citations.
- Generated census snapshots that carry a measured count for the category (`platform/src/generated/census/chart_facts_categories_authoritative_v1.json` `karaka_chara_position: 1050`) will be one row per rebuilt set higher; not edited here (a measured snapshot).

## 9. Verification performed

All commands from `platform/python-sidecar` with `PYTHONPATH=.` and the repo venv unless stated.

- `python -m pytest tests/test_ga5_writer.py tests/test_ga6_writer.py tests/test_fact_identity_parser.py` and the wider related set (ga_writers/__tests__, test_l1_sensitive_points, test_chart_reader_v4, test_ga8/9, conformance and vocabulary tests): 1017 passed, 21 skipped.
- The CI python command from `.github/workflows/ci.yml` (plus `ga_writers/__tests__` and `pipeline/orchestrator/writers/__tests__`): 8825 passed, 198 skipped, 21 xfailed, **3 failed**, all three in `tests/l3/gochara/test_wp10_cutover.py` (`test_step07_flip_gates`, `test_step08_flip_and_reverse`, `test_clear_windows_on_reversal_refusals`: Kāla cutover rehearsal against a disposable localhost:55434 database that happened to be reachable on this machine; CI has no such database and these skip there). Nothing in this branch touches Kāla files or those scripts; whether the three also fail on `origin/main` was not established. Those tests write to that disposable local database, not to production (no DATABASE_URL/PG* was set; the test refuses non-loopback DSNs).
- `python platform/scripts/governance/check_fact_category_pinning.py` (0 new violations; 65 pre-existing allowlisted) and `--self-test`; `check_fact_subject_wellformedness.py`.
- `python -m pytest platform/scripts/governance/__tests__` (repo root): 2249 passed, 87 skipped after the line-pin update (2 failures before it, both the pins).
- `python -m pipeline.orchestrator.provenance_inventory --check`: OK after regeneration (moved: `ga_sensitive`, `ga_vargas`).
- `npm run codegen:capability-estate-census:check` (from `platform`, with `node_modules` symlinked to the main checkout's, git-ignored): OK after regeneration.
- Hook validated with the detector committed on `origin/suvarna/land/TI-ephemeris-flip-report-001` (`flip_detector.py --validate-hooks --require-lanes argala,gandanta,karaka_roles`; `test_flip_detector.py` 12 passed), run from a scratch copy; offline attribution simulation described in section 8.

## 10. Decisions and Not verified

**D1 (decision for review):** the `strikaraka_alias` row carries the builder's default tier `TWO_PASS_VERIFIED`, like every other row of `_build_karaka_rows`, because `tests/test_ga5_writer.py::test_all_two_pass_verified` requires zero single-pass rows. By N.8 that default is itself unearned for the karaka rows (no second derivation exists); the alias adds no value of its own (it is a label on `DARAKARAKA.assigned_graha`). If SS prefers the honest tier for the alias, use `UNVERIFIED_DEFAULT` and relax that test for this one row; I did not change a test invariant on my own.

Not verified:
- No database access: every stored-data statement is from the lane brief or from running the builders on the stated degrees. I did not re-measure the 15 sets, the live registry graph, or live `depends_on`.
- Runtime of `ga_vargas` end to end (the DB read is exercised through a stubbed cursor only; the SQL text is asserted, not executed).
- BPHS 32.13-17 print edition (J1 pending). The legacy extraction agreement in section 2 is corroboration, not a print check.
- The wave scheduler's actual ordering of `ga_vargas` vs `ga_sensitive` on a fresh chart.
- `validate_data_plane_l1_contract.py` reports verdict FAIL on its own finding ("producer history migration does not cover 11 row-trigger tables plus set-based chart_dashas"); that finding is about migrations, not these writers, and I did not establish whether it also fails on `origin/main`.
- The full CI python suite result is reported in the final report with the exact command.
- The TypeScript side: nothing in `platform/src` or `platform-mcp` was edited or run.
