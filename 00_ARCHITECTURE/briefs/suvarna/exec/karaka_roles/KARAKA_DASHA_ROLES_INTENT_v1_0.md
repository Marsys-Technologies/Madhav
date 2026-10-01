---
artifact: KARAKA_DASHA_ROLES_INTENT
version: 1.0
status: DRAFT-FOR-REVIEW
produced_by: worker for exec-suvarna
date: 2026-10-02
lane: S-L1 mandatory — chart_dashas karaka role columns (TI-l1-dashas-karaka-001)
branch: suvarna/land/TI-l1-dashas-karaka-001 (local commits only; not pushed). Created from origin/suvarna/land/TI-l1-karaka-roles-001 (PR #2878), so the branch also carries #2878's commits.
decision: SS ruling MANDATORY (hard-coded karaka constant in ga_dashas), building on SS N-69 (kn_rao_rahu_included headline school)
scope: L1 writer code + verifier + tests + generated writer-digest inventory + attribution hook + this document. No migration, no seed edit, no TypeScript, no database write.
changelog:
  - "1.0 (2026-10-02): first version. Facts, fix, verifier decision, NULL cases, counts, edge addendum, digests, not-verified."
---

# Dasha karaka roles — intent document

## 1. The defect (verified)

`ga_writers/ga_dashas_writer.py` carried a module constant `_JAIMINI_KARAKAS` (Sun AK, Mars AmK, Mercury BK, Saturn MK, Jupiter PK, Venus GK, Moon DK; comment "based on degree-ordering — FORENSIC chart") and applied it to every chart. It fed:

- `karaka_role_at_period` = `_JAIMINI_KARAKAS.get(lord)`;
- `karakas_active_during_period` = `'Graha:role'` strings for the lord and the parent lord (`_get_karakas_active`, iterating the dict).

Consequences: the stored values were identical on all three charts (canonical 482012f1, 1c826d5a, cb73cd3d), about 169,000 non-null role rows per chart, regardless of each chart's own degree order. On the canonical chart / Lahiri the real kn_rao_rahu_included roles by stored rank are AK Moon, AmK Saturn, BK Sun, MK Venus, PiK Mars, PK Rahu, GK Jupiter, DK Mercury (read live, section 6); the constant said AK Sun and DK Moon, gave Jupiter "PK" (retired 7-scheme name) and had no entry for Rahu. This violates CLAUDE.md N.5 (L1 is the authority: ga_sensitive owns `karaka_chara_position`) and N.7 item 3 (no wrapper-local constant may shadow an L1 value).

The verifier `ga_writers/_vimshottari_independent_verifier.py` carried a transcribed copy of the same dict (`_JAIMINI_KARAKAS`, `_derive_karaka_role`, `_derive_karakas_active`) and listed both columns in `EXTENDED_VERIFIED_COLUMNS`: a copy of the constant, not an independent detector (N.8).

## 2. The fix (writer)

All paths under `platform/python-sidecar/`.

- `ga_writers/ga_dashas_writer.py`: `_JAIMINI_KARAKAS` is gone. New `_read_karaka_roles(conn, chart_id, ayanamsha_id)` runs one SELECT on `chart_facts` mirroring `ga_vargas_writer._read_jaimini_karakas`: `fact_category = 'karaka_chara_position'`, `fact_key IN ('assigned_graha','karaka_rank')`, `formula_id = 'kn_rao_rahu_included'` (the constant from `ga_writers/_karaka_roles.py`), `ORDER BY fact_subject, fact_key, fact_id`, for the exact (chart, ayanamsha) being built, on the caller's connection with a tuple-row cursor. The pure core `_karaka_roles_from_rows` maps each stored `karaka_rank` to `KARAKA_ABBREVIATIONS_8` (AK AmK BK MK PiK PK GK DK; vocabulary module, no list duplicated) and returns `{graha: role}`. Mapping is by the stored rank, not by subject-name parsing, so pre-rebuild rows with the old labels still map correctly (golden test).
- Failure modes are loud: absent rows, NULL/duplicate rows, assigned_graha and karaka_rank subject sets that differ, ranks that are not a 1..8 permutation, or a non-graha assignment raise `KarakaDependencyMissing` naming the ga_sensitive dependency. Nothing is recomputed. A genuine database error propagates (it is not swallowed the way the natal-context loader swallows its own).
- State handling: `_KARAKA_ROLE_CACHE[(chart_id, ayanamsha_id)]`, looked up by the explicit ids every `_build_row()` call already carries (no "current context" global as `_NATAL_CONTEXT_CACHE` uses), so per-ayanamsha builds, interleaved systems and parallel/forked workers cannot read each other's roles. `build_system()` calls `_activate_karaka_roles()` once per call (one tiny SELECT per system x ayanamsha sub-step) and ALWAYS reloads that key, so a ga_sensitive rebuild between two builds in one long-lived process is picked up. Absent/malformed rows are recorded as an error message and raised lazily, only when a row actually needs a role: yogini / chara_karaka / kalachakra / narayana sub-steps (no graha lord) still build without ga_sensitive. `set_karaka_roles()` is the explicit seed for DB-free unit tests, mirroring `set_natal_context()`.
- `_build_row()`: `karaka_role_at_period` = the chart's role of `lord` or NULL. `karakas_active_during_period` = `'Graha:role'` for the lord and parent lord from the SAME read, in the fixed graha order `Sun Mars Mercury Saturn Jupiter Venus Moon Rahu` (the legacy dict's insertion order, Rahu appended), a convention kept so rows whose roles do not change keep byte-identical arrays; NULL when neither carries a role. `[Mercury:DK, Moon:AK]` is the golden for (lord Mercury, parent Moon).
- Provenance (existing columns only, no migration): on rows that carry a role claim (non-NULL role or non-empty active list) `citation_human` gets the suffix `; karaka_school=kn_rao_rahu_included (ga_sensitive karaka_chara_position)`. Rows that claim no role keep their citation byte-identical. `citation_ref` is not touched (it is a reference key built in seven separate sites).
- `build_system()` activates the roles next to the natal context, inside the same `with` block, only when `skip_db` is false.

### Role abbreviations

The stored text used `AK AmK BK MK PK GK DK` (7-scheme names). The 8-scheme adds `PiK` (Pitrikaraka, rank 5) and shifts `PK` (Putrakaraka) to rank 6, `GK` rank 7, `DK` rank 8. The writer uses the vocabulary module's abbreviations, so the strings match `ga_vargas`'s `karaka_per_varga` names. Consequence for readers: the string `PK` meant Jupiter before and now means the rank-6 graha (Rahu on the canonical chart).

## 3. The NULL cases (why NULL is correct, no invention)

- **Ketu**: no role in the 8-scheme (the rank permutation covers seven grahas plus Rahu).
- **chara_karaka, kalachakra, narayana**: the lord is a zodiac SIGN. A sign is not a graha and cannot hold a chara-karaka role. Stored values were already NULL (0 non-null rows on every chart).
- **yogini**: the lord is a yogini name (Mangala, Pingala, ...). The deity -> graha alias used for `lord_natal_*` is deliberately NOT applied to roles: a yogini period is not a graha period. Already NULL on every chart.
- Stated in the code comment above `_KARAKAS_ACTIVE_GRAHA_ORDER`; the golden tests assert it (also with roles loaded).

## 4. The verifier decision

**Chosen: drop the two columns from what the verifier claims.** Moved from `EXTENDED_VERIFIED_COLUMNS` to `NOT_INDEPENDENTLY_CHECKABLE_COLUMNS` with a reason each; the constant and both `_derive_*` helpers are deleted; `derive_extended_columns` and the `fetch_engine_rows` SELECT no longer carry them. Bookkeeping: `TOTAL_CHART_DASHAS_COLUMNS` stays 42 (the columns still exist in the table); `INDEPENDENTLY_VERIFIED_COLUMNS` 20 -> 18, `EXTENDED_VERIFIED_COLUMNS` 17 -> 15, `NOT_INDEPENDENTLY_CHECKABLE_COLUMNS` 17 -> 19, `QUERY_GUARANTEED_COLUMNS` 5; the import-time partition self-test and `test_h2_column_coverage_partitions_all_42_columns_honestly` still pass.

Why the smaller option: the alternative (verify against ga_sensitive rows read by the verifier's own query) would need a DB read inside an in-memory comparison path that today runs with `skip_db=True` (the writer calls `compare_row` with lord/start/end only; the extended columns are checked only by the standalone diagnostic `verify_chart_vimshottari`), and the rank -> abbreviation step would be a second hand-written copy of the same lookup by the same author: it would verify "the same table read twice", not an independent derivation. An honest not-checkable is better than a green that cannot go red (N.8). The writer's own golden tests (`tests/test_ga_dashas_karaka_roles.py`) now carry the behavioural assertion. If SS wants the independent query later it is a separate lane.

## 5. Tests

- New `tests/test_ga_dashas_karaka_roles.py` (golden, stubbed cursor, no DB): the 8 graha -> role pairs from stored ranks (Rahu rank 6 = PK); role for Moon AK, Mercury DK, Rahu PK, Ketu NULL; `karakas_active` for (Mercury, Moon) = `['Mercury:DK','Moon:AK']` and the stated order; lord == parent appears once; Ketu with parent Moon gives `['Moon:AK']`; raises when ga_sensitive rows are absent / never loaded / malformed; role-less systems (yogini, sign lords) stay NULL even with roles loaded and need no ga_sensitive read; roles differ per chart and per ayanamsha and interleaved builds do not cross-contaminate; every build reloads its key; DB errors propagate; provenance suffix only on role-bearing rows; an end-to-end `compute_vimshottari` check that every row carries the chart's roles.
- Updated: `ga_writers/__tests__/test_vimshottari_independent_verifier.py` (karaka assertions replaced by "not claimed, no constant copy remains"), and the DB-free tests that build rows directly now seed the roles via `set_karaka_roles` (`tests/test_ga7_writer.py`, `tests/test_ga_writer_generalization.py`, `tests/test_ga_dashas_copy_upsert.py`, `ga_writers/__tests__/test_ga_dashas_vimshottari_wiring.py`). `tests/test_ga_dashas_f_a17_bare_tier_literals.py` pins three prose line numbers (992/993/997 -> 1176/1177/1181) because the new block shifted them.

## 6. Counts: OLD (stored) vs NEW, offline from live read-only data

Method. For each chart, each stored `chart_dashas` row was joined to its parent row (`parent_row_id`) for the parent lord, and to the stored kn_rao `karaka_rank` -> `assigned_graha` assignments of the same (chart, ayanamsha). NEW = the writer's rule applied to those inputs. OLD = the stored value. First the OLD constant was re-applied to the same join and compared with the stored values: 0 mismatches for both columns in every system on all three charts (so the join recovers the writer's own `parent_lord`, and the counts are not an artefact of it). Counts are summed over the 5 ayanamshas (lahiri_chitrapaksha, krishnamurti, raman, surya_siddhanta_classical, true_chitra); the stored ranks are those of the live (pre-#2878-rebuild) ga_sensitive rows, which #2878 keeps numerically identical. Everything else on a row (lord, dates, durations, natal context, tiers) is unchanged by construction; `citation_human` changes only by the suffix on role-bearing rows (not counted separately: it follows the non-NULL rows of the two columns). chara_karaka, kalachakra, narayana, yogini and scope_cap: 0 rows change.

Per chart (all systems):

| chart | rows | role changed | value to other value | equal by coincidence | NULL to value | value to NULL | active changed |
|---|---|---|---|---|---|---|---|
| 482012f1 (canonical) | 483,870 | 185,883 | 159,175 | 9,630 | 26,708 | 0 | 205,157 |
| 1c826d5a | 471,767 | 154,981 | 127,928 | 42,585 | 27,053 | 0 | 195,639 |
| cb73cd3d | 505,348 | 192,473 | 161,620 | 30,440 | 30,853 | 0 | 228,957 |

(NULL to value = rows whose lord is Rahu: the old dict had no Rahu. No value goes to NULL: every one of the seven classical grahas has a role in the 8-scheme.)

Per chart and system (non-null-capable systems only; the five role-less systems are all zero):

| chart | system | rows | role: value to other | role: equal | role: NULL to value | role changed | active: value to other | active: equal | active: NULL to value | active changed |
|---|---|---|---|---|---|---|---|---|---|---|
| 482012f1 | vimshottari | 45,664 | 33,519 | 2,019 | 5,143 | 38,662 | 42,733 | 670 | 1,721 | 44,454 |
| 482012f1 | vimshottari_kp | 5,670 | 4,170 | 240 | 630 | 4,800 | 5,308 | 80 | 214 | 5,522 |
| 482012f1 | ashtottari | 32,960 | 27,177 | 1,653 | 4,130 | 31,307 | 32,225 | 210 | 525 | 32,750 |
| 482012f1 | mudda | 102,375 | 76,153 | 4,649 | 14,085 | 90,238 | 96,611 | 1,211 | 3,993 | 100,604 |
| 482012f1 | naisargika | 21,945 | 18,156 | 1,069 | 2,720 | 20,876 | 21,492 | 118 | 335 | 21,827 |
| 1c826d5a | vimshottari | 49,768 | 28,796 | 9,956 | 5,629 | 34,425 | 43,081 | 4,240 | 1,882 | 44,963 |
| 1c826d5a | vimshottari_kp | 6,210 | 3,580 | 1,250 | 690 | 4,270 | 5,370 | 534 | 232 | 5,602 |
| 1c826d5a | ashtottari | 33,120 | 21,502 | 7,468 | 4,150 | 25,652 | 30,818 | 1,782 | 520 | 31,338 |
| 1c826d5a | mudda | 100,231 | 60,004 | 18,977 | 13,904 | 73,908 | 89,252 | 6,420 | 4,009 | 93,261 |
| 1c826d5a | naisargika | 21,660 | 14,046 | 4,934 | 2,680 | 16,726 | 20,155 | 1,185 | 320 | 20,475 |
| cb73cd3d | vimshottari | 46,257 | 30,795 | 5,213 | 5,217 | 36,012 | 42,249 | 1,733 | 1,740 | 43,989 |
| cb73cd3d | vimshottari_kp | 5,760 | 3,840 | 640 | 640 | 4,480 | 5,254 | 220 | 212 | 5,466 |
| cb73cd3d | ashtottari | 33,080 | 24,800 | 4,140 | 4,140 | 28,940 | 32,030 | 525 | 525 | 32,555 |
| cb73cd3d | mudda | 130,110 | 85,015 | 17,542 | 18,016 | 103,031 | 119,232 | 4,983 | 5,170 | 124,402 |
| cb73cd3d | naisargika | 22,915 | 17,170 | 2,905 | 2,840 | 20,010 | 22,190 | 370 | 355 | 22,545 |

"Active: equal" counts rows whose stored array already equals the new one (both lord and parent roles, and Rahu absent), by coincidence. Live roles read for the record (Lahiri): canonical 1 Moon 2 Saturn 3 Sun 4 Venus 5 Mars 6 Rahu 7 Jupiter 8 Mercury (matches the golden); 1c826d5a 1 Mercury 2 Mars 3 Venus 4 Sun 5 Moon 6 Jupiter 7 Saturn 8 Rahu; cb73cd3d 1 Venus 2 Moon 3 Mercury 4 Jupiter 5 Rahu 6 Saturn 7 Sun 8 Mars. The counts are of the live row sets as they stand; a rebuild (ephemeris flip) can move a few rows at the window edges, so the post-rebuild numbers can differ by a small amount. The query files are in the worker scratchpad (`scratchpad/dk/`), not in the repo.

**Detector blind spot (stated):** `flip_detector.py` reads `chart_dashas` only as (lord path, start, end) rows, so it cannot see these column changes. The attribution hook `00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/karaka_dasha_roles.json` is valid (`flip_detector.py --validate-hooks`) and declares the lane's detector-visible footprint as a zero-second start shift for the five field-carrying systems (so it masks no unattributed row-set change or shift), and carries the column-level expectation and the counts above in its text. A post-rebuild check of these two columns has to be a SQL comparison against the stored kn_rao ranks (the join in the method above), not a detector run.

## 7. Registry edge (migration 1226, formerly numbered 1220): addendum text for the intent document

`00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1220_EDGES_INTENT_v1_0.md` is not on this branch's base (it lives on the local branch `suvarna/exec`), so it was not edited. Paste-ready replacement for the evidence cell of row 6 and an acyclicity line:

> | 6 | `ga_dashas.depends_on += ga_sensitive` | N-69 dashas karaka roles (S-L1 mandatory) | `ga_dashas_writer.py` READS ga_sensitive's `kn_rao_rahu_included` `karaka_chara_position` assignments (`assigned_graha`, `karaka_rank`) via `_read_karaka_roles` (branch `suvarna/land/TI-l1-dashas-karaka-001`, `ga_dashas_writer.py:694`; called from `build_system` at `:3340`, consumed in `_build_row` at `:1238-1269`), replacing the hard-coded `_JAIMINI_KARAKAS`. Live `asset_registry` read 2026-10-02: `ga_dashas {ga_positions}`, `ga_sensitive {ga_positions, bg_reference}`, `ga_vargas {ga_positions}`. Without the edge the failure is loud, not silent: a role-bearing row built before ga_sensitive raises `KarakaDependencyMissing`; role-less systems (yogini, chara_karaka, kalachakra, narayana) are unaffected. |
>
> Acyclicity (re-read live): `ga_sensitive -> {ga_positions, bg_reference}`, `ga_positions -> {}`, `bg_reference -> bg_ontology -> {}`. No path leads from `ga_sensitive` (or its ancestors) to `ga_dashas`; `ga_dashas`'s live dependents (`ga_condition`, `ga_sade_sati`, `ga_structural`, `ga_tajaka`, `ga_vichara`, `ga_yoga`) are not ancestors of `ga_sensitive`. After the six edges the graph stays acyclic: `ga_dashas -> {ga_positions, ga_vargas, ga_sensitive}`, `ga_vargas -> {ga_positions, ga_sensitive}`. Edge count in the file header and the "Migration shape" line (still says "five") should read six. One-time consequence as for the other edited assets: `compute_upstream_hash` changes for `ga_dashas`, and its frozen manifest goes to `plan_adaptation_required`.

Landing order: the writer reads ga_sensitive rows that already exist on all three charts (15 chart x ayanamsha sets read live), so it works before the edge lands; the edge makes S-L1's order deterministic (`ga_sensitive` before `ga_dashas`). The scheduler treats `chart_facts` as a soft table (see the karaka-roles intent doc section 5), so no census or DAG guard flags this read today.

## 8. Generated and governance artefacts

- `platform/src/generated/nirmana-writer-digests.json`, regenerated with `PYTHONPATH=. .venv/bin/python3 -m pipeline.orchestrator.provenance_inventory --output ../src/generated/nirmana-writer-digests.json` from `platform/python-sidecar`. Exactly one asset moved: `ga_dashas` `670784893e3bbcaae95b908ccd57baba7acf0fe8bb6240b2bdc1b9463ecb493b` -> `465b6c3eeb06ba47193d22b609287143793a493d54d16081f7622649d3083128`. No other writer's closure includes `ga_dashas_writer.py` or `_vimshottari_independent_verifier.py` (the verifier is imported only by ga_dashas); `_karaka_roles.py` was not edited, so `ga_sensitive` / `ga_vargas` digests did not move again; `probe_digest` unchanged.
- E6 pins, `platform/scripts/governance/__tests__/test_e6_1_declarations.py` (CITATION_DECISIONS for `ga_dashas`): the AST census of the writer's `citation_human` sites moved `[composed, const, passthrough, other]` from `[29, 2, 1, 0]` to `[30, 2, 0, 0]` (the `"citation_human"` dict value is now `citation_human + suffix`, composed, instead of a forwarded parameter) and the cited line `human = f"Vimshottari ..."` moved 1160 -> 1345. The `decline` decision for `ga_dashas` (prose_fields null) is KEPT: the new composed site appends a fixed provenance token (`karaka_school=<constant> (ga_sensitive karaka_chara_position)`), it states no graded or computed claim about the dasha. That judgement is flagged for SS review (the census is pure syntax; the caller decides which composed sites state a value).
- `platform/src/generated/capability_estate_census.json`: `npm run codegen:capability-estate-census:check` demanded regeneration (writer-digest inventory sha moved). Regenerated with `--generated-at=2026-10-02T09:00:00.000Z --source-revision=4feb5c19343562cab548ae1c68ec662721758e80` (the same two provenance values the committed file and the #2878 census commit carry, as that commit did; a fresh source revision would be the commit that contains this very change); only `content_sha256` and the `writer_digest_inventory` source sha changed. Re-check: OK.
- `tests/test_ga_dashas_f_a17_bare_tier_literals.py`: three prose-line pins 992/993/997 -> 1176/1177/1181.
- `platform/scripts/generate/nirmana_analysis_layer_pins.py --check` and 9 tests in `platform/scripts/__tests__/test_nirmana_analysis_layer_pins.py` fail in this worktree on ancestry of frozen-capsule commits ("must be an ancestor of HEAD"); the same 9 fail with the digest file at the branch base (checked), so they are not caused by this change. The layer pins were not regenerated.

## 9. Verification run

All from `platform/python-sidecar` with `PYTHONPATH=.` and `/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3`, except governance (repo root).

- `-m pytest tests/test_ga7_writer.py tests/test_ga_dashas_*.py ga_writers/__tests__/test_ga_dashas_*.py ga_writers/__tests__/test_vimshottari_independent_verifier.py tests/test_dasha_*.py tests/test_ga_writer_generalization.py tests/test_ga_orchestrator_conformance.py tests/test_verification_pass_status_vocab.py tests/test_swiss_state_boundary.py tests/test_l1_bypass_guard.py tests/test_ga_condition_f_c8_varga_dignity_composite.py tests/l3/test_ka_dasha_kala.py -q`: 263 passed, 6 skipped.
- `-m pytest ga_writers/__tests__ -q` (rest of the directory): 180 passed, 1 skipped (wiring file deselected, it is in the run above).
- `-m pytest pipeline/orchestrator/tests/test_provenance.py tests/test_nirmana_campaign_wave_dispatch.py -q`: 83 passed.
- `PYTHONPATH=platform/python-sidecar python -m pytest platform/scripts/governance/__tests__ -q`: 2249 passed, 87 skipped (after the E6 re-pin; before it 2 `ga_dashas` E6 tests failed, as described in section 8).
- `check_fact_category_pinning.py`: 0 new violations (65 pre-existing, allowlisted), PASS.
- `flip_detector.py --validate-hooks --require-lanes karaka_roles,karaka_dasha_roles` (detector taken from `origin/suvarna/land/TI-ephemeris-flip-report-001`, run against this branch's hook directory): valid, exit 0.
- Census: `npm run codegen:capability-estate-census:check` OK after regeneration (temporary `platform/node_modules` symlink, removed).

## 10. Not verified

- No live rebuild was run and no database was written. The reader SQL was executed read-only against live data through psql as the reader (same predicates; 8 rows per (chart, ayanamsha), ranks 1..8, canonical Lahiri matches the golden), but `build_system()` itself was not run against a live connection; the unit tests stub the cursor.
- The OLD-vs-NEW counts apply the rule to stored rows; they were not produced by running the new writer, and a rebuild may differ at window edges (section 6).
- BPHS 32.13-17 as the source of the 8-scheme role order remains sourced_ocr_unverified (J1 print-edition check pending), as in the karaka-roles lane.
- The independent-verifier question is closed by dropping the claim, not by adding a second derivation (section 4).
- `ga_vargas_writer._read_jaimini_karakas` and this writer's `_read_karaka_roles` are two copies of one parser (same query, same checks, different return shape and exception class). I did not refactor `ga_vargas` (its tests pin its SQL text and error prefix). A follow-up could move the pure core into `_karaka_roles.py`; it would move the `ga_sensitive`, `ga_vargas`, `ga_dashas` digests together.
- A `rebuild_kp_suryasiddhanta_dashas.py` backfill script calls `build_system()`; it now needs ga_sensitive rows for the chart (they exist today).
- The shared scratchpad file `q.sh` was overwritten by this worker early in the task (it had held another session's helper); it was recreated as a plain read-only psql wrapper taking the SQL as `$1`.
