---
artifact: SUN_REQUIRED_RUPA_INTENT
version: 1.1
status: DRAFT-FOR-REVIEW
produced_by: worker for exec-suvarna
date: 2026-10-02
lane: S-L1 mandatory (small) — the Sun's required shadbala (TI-l1-sun-required-rupa-001)
branch: suvarna/land/TI-l1-sun-required-rupa-001 (PR #2893, draft, never armed)
decision: SS S-L1 MANDATORY (Sun required rupa); CLAUDE.md N.5 (L1 authority), N.7 item 3 (no wrapper-local constant shadows an L1-computed or sourced value), N.7 item 6 (honest null), B.10
scope: L1 writer code + tests + generated governance artefacts + one attribution hook + this document. No migration, no seed edit, no TypeScript source, no database write (SELECT-only reads for the counts below).
changelog:
  - "1.1 (2026-10-02): independent-review fixes + SS additions. LOW-1 failed reads raise (both loaders); LOW-2 floor reason/citation name the real missing input(s); LOW-5 hook note corrected (required_rupa 5 is integral: one class-level value change per chart); LOW-4 chart_query.integration.test.ts:132 on the REBUILD CHECKLIST (section 12); SS (a) Rahu/Ketu composite rows are honest nulls (section 13); SS (b) ga_strength raises instead of defaulting to 5.0, and the total-rupa citation bug that the default masked is fixed (section 14); SS (c)/sweep: data-dependent assertions in DATA_DEPENDENT_ASSERTIONS_S_L1_v1_0.md."
  - "1.0 (2026-10-02): first version. Sources read and values, the shadow copies, the change, consumers, offline old-vs-new counts, digests moved, verification, not-verified."
---

# Sun required shadbala — intent document

## 1. Sources read, and the values they give

The Sun's classical minimum total shadbala is **390 virupa = 6.5 rupa**, not 5.0. Four sources were read by the worker (not taken on trust from the brief). They agree on all seven grahas.

| # | source | how it was read | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|---|---|
| 1 | BPHS ch.27 sl.32-33, R. Santhanam trans., repo file `00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt` lines 22841-22855 | read the text directly | verse: 390; note: 6.5 | verse: "3*0" (OCR); note: 6.0 | 300; 5.0 | verse: "42C" (OCR); note: 7.0 | 390; 6.5 | 330; 5.5 | 300; 5.0 |
| 2 | the same BPHS passage as served corpus chunk `bphs_pg0286_c01` (sha256 `3c616170...3b30d6`), table `classical_text_chunks`, read-only SELECT | read the chunk text | 390 / "6.5 Rupas" | "360" / "6.0" | 300 / 5.0 | "42C" / "7'0" | 390 / 6.5 | 330 / 5.5 | 300 / 5.0 |
| 3 | Phaladipika IV.22-23, V. Subrahmanya Sastri trans., corpus chunk `phaladeepika_pg0079_c01` (sha256 `05e2dd25...b230b`), read-only SELECT | read the chunk text ("The Sun is declared strong when his strength is 6J- Rupas ... Moon 6, Mars 5, Mercury 7, Jupiter ... 6j Rupas, Venus ... 5* ... Saturn 5") | "6J-" (OCR of 6 1/2) | 6 | 5 | 7 | "6j" (6 1/2) | "5*" (5 1/2) | 5 |
| 4 | Pravaha PR #2869 `sad_bala_sufficient v1.0` (commit 932cf3a01), `services/gochara_rules/registry.py` lines ~490-600 on origin/main (also `tests/l3/gochara_rules/test_f4_sad_bala_sufficient.py:88`) | read the file at origin/main | 6.5 | 6.0 | 5.0 | 7.0 | 6.5 | 5.5 | 5.0 |

Notes. The verse line of source 1 has OCR damage on Moon ("3*0") and Mercury ("42C"); both are resolved by the translator's explicit rupa note directly below it and by source 3, so there is no residual doubt on any of the seven values. Sources 1 and 2 are the same page (the repo text is the file the corpus chunk was cut from) and are one independent source for corroboration purposes; source 3 is a second, independent classical text; source 4 is Pravaha's own citation of 1 and 3 and carries the same seven thresholds. The seven values in source 4 equal the seven values in 1-3 and equal the current L1 table for every graha except the Sun. Earlier analysis files (`L1_STATE.md` ~990-1000, `L1_W1_ANALYSIS_BATCH_C.md` F-C1) were read: F-C1 is the weakest-graha selector defect, not the Sun's required value, and neither file addresses 5.0 vs 6.5. No source disagrees.

Stored L1 values read (SELECT-only, 3 charts x 7 grahas): `graha_shadbala_total|required_rupa`, ayanamsha_id `INVARIANT`, exactly one row per chart per graha: Sun 5, Moon 6, Mars 5, Mercury 7, Jupiter 6.5, Venus 5.5, Saturn 5. Only the Sun differs from the sources.

## 2. The shadow copies (before)

| location | what it held | role |
|---|---|---|
| `ga_writers/ga_strength_writer.py:94-100` `SHADBALA_REQUIRED` | Sun 5.0 | writer of the `required_rupa` fact (rows at :827+, stored under INVARIANT) and of the derived `ratio` (:854+, CR-18); also read at :161 for the `citation_human` of the `graha_shadbala_total` rows |
| `ga_writers/ga_structural_writer.py:3872-3945` `_COMPOSITE_SHADBALA_REQUIRED` | the same seven numbers, Sun 5.0, "kept as a separate module-local copy; no cross-import" | a second copy used to normalise the composite per-graha-per-house strength: `min(1.0, shadbala_rupa / required)` |
| `pipeline/orchestrator/writers/bo_upaya.py:189` | docstring text only: "Sun/Mars/Saturn=5.0 ..." | comment, no behaviour |
| `ga_writers/ga_yoga_writer.py:183-226` `_load_shadbala_map` | reads the L1 `required_rupa` fact (INVARIANT convention) | already correct; inherits the fix on rebuild |
| `platform-mcp/src/tools/registry_bridge.ts:4353-4400` | reads the L1 `required_rupa` fact at serve time | already correct; inherits the fix on rebuild |
| `services/gochara_rules/registry.py` (Pravaha) | its own CITED thresholds (Sun 6.5) and a recorded discrepancy note about L1's Sun | not touched (not this lane's file); the note becomes stale after the rebuild |

`git grep` for other copies (`SHADBALA_REQUIRED`, `required_rupa`, `_REQUIRED`, `Sun.*5.0` over `platform/python-sidecar platform/src platform-mcp`) found no other table. Test fixtures that embed the old Sun figure as a stored-value snapshot are listed in section 7.

## 3. The change

1. `ga_strength_writer.py`: the single table is now defined from the source figures in virupa (`SHADBALA_REQUIRED_VIRUPA`: 390 360 300 420 390 330 300) and `SHADBALA_REQUIRED = {g: v / 60.0}` (all seven quotients are exact in binary floating point). The comment cites chunk ids, chapter/verse and the virupa figures for both sources and Pravaha's PR. Sun is 6.5.
2. `ga_structural_writer.py`: the module-local copy is deleted. A new reader `_load_required_rupa_map(conn, chart_id)` reads the L1 fact: `fact_category='graha_shadbala_total'`, `fact_key='required_rupa'`, `ayanamsha_id='INVARIANT'`, pinned, `ORDER BY fact_subject, fact_id`. It mirrors `ga_yoga_writer._load_shadbala_map`'s INVARIANT convention. **v1.1 (LOW-1): a failed SELECT RAISES** (it is not a missing fact; the earlier `except Exception -> logger.warning -> {}` would have floored all seven classical grahas' composite rows on a database error); the same change is applied to the sibling `_load_shadbala_and_bhava_fact_ids`. Only a genuinely absent fact (successful SELECT, no row) is left out of the map and floors with a named reason. The composite builder takes the required value per classical graha from it, adds the required fact's `fact_id` to `constituent_facts_array` (B.3: the ratio now genuinely consumes that fact), and **floors** the row (`value_num=None`, reason `missing_l1_required_rupa_fact`; v1.1 LOW-2: the reason and the `citation_human` now name EVERY missing input, e.g. `missing_l1_required_rupa_fact+missing_ga3_shadbala_or_bhava_bala_fact` / "missing the L1 required_rupa fact and the GA3 shadbala fact", where the old text always said "missing real shadbala/bhava_bala GA3 fact") if the L1 fact is missing — never a substituted default (N.7 item 6).
3. `bo_upaya.py:189`: docstring text only (comment, two lines kept to two lines so no E6 line pin in that file moved).

**Why read the L1 fact rather than import the constant (the choice, and why it is least risky).** `asset_registry.depends_on` (read-only SELECT) lists `ga_strength` in ga_structural's dependencies (`{ga_dashas,ga_nakshatra,ga_panchanga,ga_positions,ga_sensitive,ga_strength,ga_vargas}`), so the INVARIANT row is guaranteed to exist before ga_structural runs, and ga_structural already reads this very category from `chart_facts` for the achieved `rupa` in the same function. Reading the fact (a) makes the stored fact the single authority at read time (N.5), so a future correction in ga_strength propagates without a second code edit, (b) adds no cross-import between L1 writers (the rule the old comment cited), (c) needs no new module, (d) is exactly the existing reader pattern in ga_yoga. An import of the constant from a new shared module would still leave two code paths free to disagree with the stored fact. The mutation test (section 6) proves ga_structural now follows the ga_strength table.

**Nodes (SS ruling 2026-10-02, section 13).** Rahu/Ketu carry a total-shadbala `rupa` fact but no classical minimum. The v1.0 behaviour (a named legacy 5.0 normaliser) is REMOVED: their composite rows are honest nulls with the reason `no_classical_required_value_for_node` (section 13).

## 4. What changes in stored facts for the Sun (rebuild effect)

Nothing changes until `ga_strength` (and its dependents) are rebuilt; the code change alone writes nothing. On rebuild, for the Sun only:

- `graha_shadbala_total|required_rupa` (INVARIANT, 1 row per chart): 5 -> 6.5.
- `graha_shadbala_total|ratio` (one row per ayanamsha): `old * 5 / 6.5`.
- `citation_human` of the Sun's `required_rupa` and `ratio` rows. **v1.1:** the `citation_human` of EVERY `graha_shadbala_total|rupa` row changes (all seven grahas and both nodes): it read a silent 5.0 default for every graha, see section 14.
- Rahu/Ketu `graha_in_house_composite_strength` rows: 120 `bphs_weighted` rows per chart become floored nulls and the 240 `simple_multiplication` / `cross_formula_divergence` rows disappear (section 13).
- Not changed: every achieved shadbala value (`rupa`, sthana, dig, kala, cheshta, drik, naisargika), every other graha's required and ratio, positions, tiers, the 7 FORENSIC anchors.

Downstream (writers that consume the Sun's required/ratio, traced by `git grep`):

| consumer | reads | what changes for the Sun |
|---|---|---|
| `ga_structural` composite (`graha_in_house_composite_strength`) | L1 `required_rupa` (now) + `rupa` | `bphs_weighted` and `cross_formula_divergence` of `SUN_IN_HOUSE_n`, only where `rupa < 6.5` (ratio is capped at 1.0); `constituent_facts_array` of every classical-graha composite row gains the required fact's id; Rahu/Ketu rows floor (section 13) |
| `ga_yoga` `ga_yoga_firings.strength` (constituent_bala_v1) | L1 `rupa`, `required_rupa` | strength of every yoga with the Sun among its `constituent_planets` |
| `bo_laksana` | L1 `ratio` clamped at 2.0 | `bodha_msr_signals.shadbala_norm` (and the salience built from it, bala_gate for yoga-class signals) on signals whose primary graha is the Sun |
| `bo_upaya` | L1 `ratio` (`_fetch_shadbala`) | `bodha_rm_resonances` Sun row (one per ayanamsha), and any group "weakest by ratio" comparison that includes the Sun |
| `registry_bridge.ts` (serve) | L1 `rupa` + L1 `required_rupa` at read time | the graha_portrait narration "X rupas vs 5.00 required" becomes "vs 6.50 required" after the rebuild; no code change |
| not affected (read `rupa` only) | | ga_vichara (`ga_vichara_writer.py:239`), ga_dashas, bo_samvada, `deriveShadbalaWeakestGraha` (query_ucd.ts), `register_d9_judgment.ts`, significator_condition, kala_permission, gochara_rules strength |

## 5. Offline OLD vs NEW on the three charts (stored facts, read-only; no database write)

Method: SELECT-only dumps of `chart_facts` (`graha_shadbala_total`, composite rows for the Sun, `house_bhava_bala_total`), `ga_yoga_firings`, and a fingerprint count on `bodha_msr_signals`; the formulas of the changed code were re-applied in a scratch script (not committed). Reproduction was checked first: the stored `ratio` equals stored `rupa / old required` on 105/105 rows.

**Sun ratio per ayanamsha (achieved rupa / required):**

| chart | ayanamsha | Sun rupa | stored ratio (old, /5.0) | new ratio (/6.5) | vs minimum |
|---|---|---|---|---|---|
| 482012f1 (native) | krishnamurti | 8.47 | 1.694 | 1.3031 | above -> above |
| | lahiri_chitrapaksha | 8.47 | 1.694 | 1.3031 | above -> above |
| | raman | 8.92 | 1.784 | 1.3723 | above -> above |
| | surya_siddhanta_classical | 8.93 | 1.786 | 1.3738 | above -> above |
| | true_chitra | 8.47 | 1.694 | 1.3031 | above -> above |
| 1c826d5a (Abhinandan) | krishnamurti / lahiri / surya_siddhanta / true_chitra | 7.2 | 1.44 | 1.1077 | above -> above |
| | raman | 6.9 | 1.38 | 1.0615 | above -> above |
| cb73cd3d | krishnamurti / lahiri / surya_siddhanta / true_chitra | 5.74 | 1.148 | 0.8831 | **above -> BELOW** |
| | raman | 5.98 | 1.196 | 0.9200 | **above -> BELOW** |

So the Sun's `ratio` changes on all 15 chart-ayanamsha rows and its `required_rupa` on 3 rows; **cb73cd3d flips from at/above to below the classical minimum on all five ayanamshas** (the one qualitative flip). Rank effects by ratio (rupa-based consumers are unaffected): on the native chart the Sun drops from strongest-by-ratio to second (Saturn 1.566 first) on all 5 ayanamshas; on Abhinandan from first to sixth (Venus strongest) on 4 ayanamshas and from second to seventh on raman (the Sun becomes the weakest by ratio there); on cb73cd3d from fourth to seventh on 4 ayanamshas (the Sun becomes the weakest by ratio, replacing Jupiter) and to sixth on raman.

**ga_structural composite, Sun rows (`SUN_IN_HOUSE_1..12`, 36 rows per ayanamsha = 180 per chart):**

| chart | rows whose value changes (bphs_weighted + cross_formula_divergence) | why |
|---|---|---|
| native | 0 / 180 | Sun rupa 8.47-8.93 >= 6.5, ratio capped at 1.0 both before and after |
| Abhinandan | 0 / 180 | Sun rupa 6.9-7.2 >= 6.5 |
| cb73cd3d | 120 / 180 (12 houses x 2 keys x 5 ayanamshas; `simple_multiplication` unchanged) | Sun rupa 5.74-5.98 < 6.5: composite ratio 1.0 -> 0.8831 (0.92 on raman). Note: the stored cb73cd3d composite rows pre-date the P0-N1 fact_key pin (they match `min(1, ratio/5)`, i.e. the unpinned ratio row), so a rebuild changes them regardless of this lane; the 120 is the fix-only effect against a fresh rebuild under the old table (also 120) |

Rahu/Ketu composite rows: 0 changes (legacy default preserved). The other six grahas: 0 changes. `constituent_facts_array` gains one element on every classical-graha composite row (all charts), a ledger change, not a value change.

**ga_yoga_firings.strength (constituent_bala_v1), by yoga with the Sun among constituents, all five ayanamshas:**

| chart | firings | with Sun | strength changes |
|---|---|---|---|
| native | 53 | 18 | 15 (the 3 others are `neecha_bhanga_raja_yoga`, whose strength is the rules-fired fraction 0.4/0.6, not shadbala) |
| Abhinandan | 69 | 29 | 29 |
| cb73cd3d | 80 | 40 | 35 (5 `neecha_bhanga_raja_yoga`, same reason) |

Reproduction check: the old stored strength is reproduced from stored `rupa` / old required on every constituent_bala_v1 row; non-reproduced rows are exactly the `neecha_bhanga_raja_yoga` rows (different derivation) and 4 Rahu-only rows (null both before and after). No yoga's `fired`, bhanga or family fields depend on the Sun's required value.

**bodha_msr_signals.shadbala_norm:** the number of stored rows whose `shadbala_norm` equals the Sun's stored ratio (the fingerprint of Sun-primary signals; zero collisions with another graha's ratio on any chart-ayanamsha) is, per chart: native 1,884; Abhinandan 1,989; cb73cd3d 1,927 (summed over 5 ayanamshas; per-ayanamsha 359-425). Each of those rows' `shadbala_norm` moves; how many of their salience/strength values then move is **not reproduced** (the salience formula was not re-implemented here). `bodha_rm_resonances`: one Sun row per chart-ayanamsha changes (15 rows total) — resonance score values **not reproduced**.

**Sun-related thresholds that compare strength to required:** no other writer compares the Sun's strength to its required value. Pravaha's `sad_bala_sufficient v1.0` carries its own cited threshold (6.5 for the Sun) and does not read L1's `required_rupa` (its registry note records the L1 discrepancy); after this lane's rebuild L1 and that factor agree. No count to report for it.

**Cannot reproduce:** exact post-rebuild values of bodha salience/strength/resonance; any value that a rebuild changes for reasons other than this lane (the cb73cd3d composite pre-pin staleness above); live production, which was only read, never rebuilt.

## 6. Tests (all offline, no database)

New `ga_writers/__tests__/test_ga_strength_required_rupa_source.py` (26 tests in v1.0; 47+ in v1.1: failed-read raise, floor-reason, node null, ga_strength default/mutation, citation tests): the seven values golden from the BPHS source (parametrised, fails if any differs); virupa/60; table has exactly the seven classical grahas; emitted `required_rupa` rows are the source values under INVARIANT; the Sun's ratio old vs new from stored achieved totals for all three charts (fixture) and the six other ratios unchanged; cb73cd3d flips below the minimum; ga_structural has no `_COMPOSITE_SHADBALA_REQUIRED` (no assignment, no `.get`, no per-graha literal table); composite reads the L1 fact (INVARIANT-scoped, ORDER BY, cites the required fact id); **mutation test**: `monkeypatch` the ga_strength table to 5.0 and to 8.0 and the composite follows (0.8831 -> 1.0000 -> 0.7175); a missing L1 required fact floors a classical row honestly; nodes keep the named legacy default.

Existing tests updated because they pinned the old Sun value: `tests/test_d1_5b_b5_completions.py` (required 6.5, ratio 7.5/6.5), `tests/l2/test_bo_laksana_p05_p06_shadbala_ratio.py` (golden fixture Sun required 6.5, ratio 8.47/6.5; the "strongest by ratio" assertion becomes Saturn, since Saturn's 1.566 now exceeds the Sun's 1.303; the Sun is still strongest by raw rupa). E6 declaration line pins re-pinned (ga_strength 845->874, 880->909, 1713->1742; ga_structural 4659->4720, 4871->4932, 4880->4941; no site count changed) in `asset_declarations.json` and `test_e6_1_declarations.py`, following commit 271290c25.

Left unchanged on purpose: `platform/src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts:132` asserts the **live** stored Sun `required_rupa` is 5 (DB integration test). It is data-dependent and goes red the moment the rebuild lands; see the REBUILD CHECKLIST (section 12) for what was decided about it. The mock-based TS tests (`chart_facts_query_wp13f.test.ts`, `registry_bridge_r5w3_judgment_and_portrait.test.ts`) feed their own stored-value fixtures and test the reading mechanism, so they stay valid. Comments citing "ratio 1.694" (`bo_upaya.py:204/501/647`, `query_ucd.ts:74`) describe the 2026-07 stored snapshot and will read stale after the rebuild (comment only).

## 7. Digests moved (`platform/src/generated/nirmana-writer-digests.json`)

Regenerated with `provenance_inventory`; a clean origin/main regenerates identically to its committed file (no pre-existing drift). Seven digests moved, all because the writer source hash covers each writer's local-import closure (including lazy imports): `ga_strength` (direct), `ga_structural` (direct), `bo_upaya` (direct, docstring), `ga_yoga` and `ga_sensitive_degree` (same closure as ga_structural: ga_yoga lazily imports ga_structural; ga_sensitive_degree imports ga_yoga), `ga_ayurdaya` (imports ga_sensitive_degree), and **`ka_vighnakara` (L3, flagged)** (imports ga_sensitive_degree). No L0 digest moved. The L3 digest moved by transitive import only; no Kala production file was edited. The L0/L3 analysis-layer pin tests are retired (`describe.skip`); the one live test in `src/generated/__tests__` passes. `capability_estate_census.json` was regenerated (only the digest file's sha and the content hash changed) with `--generated-at=2026-10-01T23:48:08.000Z --source-revision=5c93962d603315de0bb302241db2bf8ec539d59e` (the latest origin/main commit touching the census source sets).

## 8. Verification (commands and counts)

From `platform/python-sidecar`, `PYTHONPATH=.`, venv `/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 -m pytest`:
- new file: 26 passed.
- targeted set (ga_strength/ga_structural/ga_yoga/bo_* and every test file matching `required_rupa|SHADBALA_REQUIRED|ga_strength_writer|ga_structural_writer|_build_composite|graha_shadbala_total`, plus bo_upaya wiring and dict-row tests): 907 passed, 2 skipped.
- `ga_writers pipeline/orchestrator tests/l2`: 1878 passed, 121 skipped.
- `tests --deselect tests/l3`: 5389 passed, 208 skipped, 1 xfailed.
- `tests/l3`: 2548 passed, 137 skipped, 19 xfailed, **3 failed** (`test_wp10_cutover.py::test_step07_flip_gates`, `test_step08_flip_and_reverse`, `test_clear_windows_on_reversal_refusals`: "no kala_gochara_windows rows for this generation", a live-database precondition) — **the same 3 fail on a clean origin/main checkout**, unrelated to this lane.
- governance (`PYTHONPATH=platform/python-sidecar python -m pytest platform/scripts/governance/__tests__ -q`, repo root): 2293 passed, 43 skipped (after the E6 re-pin; before it, 6 E6 pin tests failed as expected).
- `check_fact_category_pinning.py`: 0 new violations (65 pre-existing, allowlisted), PASS.
- `provenance_inventory --check`: current. `npm run codegen:capability-estate-census:check`: OK.
- `flip_detector.py --validate-hooks --require-lanes sun_required_rupa,argala,gandanta` (from a scratch checkout of origin/suvarna/land/TI-ephemeris-flip-report-001 with this lane's hook added): valid.

## 9. Attribution hook

`00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/sun_required_rupa.json` (lane `sun_required_rupa`), v1.1: (1) `graha_shadbala_total|required_rupa`, ayanamsha `INVARIANT`, change type `value`, **`expected_count` exact 1** (the Sun's old 5 is integral, so the detector classifies it `class_num` and reports one class-level value change per chart; the v1.0 note claiming a predicted class-level count of 0 was wrong, review LOW-5); (2) `ratio` (continuous, no count: both sides non-integral); (3) `graha_in_house_composite_strength` `bphs_weighted` / `cross_formula_divergence` Sun houses (continuous); (4) the Rahu/Ketu composite rows (section 13): `bphs_weighted` / `simple_multiplication` / `cross_formula_divergence`, change types value / appeared / disappeared / tier, 120 tier changes per chart stated in prose (no machine count: a tier-honesty lane may also change tiers in this category). The REBUILD CHECKLIST item for `chart_query.integration.test.ts:132` is recorded in the first entry's note. Validated with `flip_detector.py --validate-hooks --require-lanes sun_required_rupa,argala,gandanta` (valid) and its 12 self-tests. Tables the detector does not read (`ga_yoga_firings`, `bodha_*`) are named in the description only.

## 10. Held for SS / the L1 owner

1. (DONE in v1.1, SS ruling: section 13) Nodes: honest null instead of the legacy 5.0 composite normaliser.
2. `chart_query.integration.test.ts:132`: see section 12 (REBUILD CHECKLIST).
3. After the rebuild, Pravaha's `l1_required_rupa_note` in `services/gochara_rules/registry.py` is stale (not this lane's file).
4. cb73cd3d's stored composite rows are stale relative to current code (pre-P0-N1); they are rewritten by any ga_structural rebuild.
5. The rebuild is not part of this lane: no row was written.

## 11. Not verified

- No database was written and no rebuild was run; every "after" figure is computed from stored facts with the changed formulas, not observed.
- bodha salience/strength and resonance values after the rebuild (counts of rows whose input moves are given; counts of rows whose output moves are not).
- The BPHS verse line's printed Moon and Mercury virupa digits ("3*0", "42C") are OCR-damaged; the values rest on the explicit rupa note and on Phaladipika (6 and 7).
- Phaladipika's half-rupa glyphs ("6J-", "6j", "5*") are OCR renderings; read as 6 1/2, 6 1/2, 5 1/2 on the strength of BPHS and Pravaha's reading, not independently from a print edition.
- The J1 print-edition check of BPHS ch.27 (a physical page) was not done; sources are the repository's R. Santhanam OCR text and the corpus chunk.
- TypeScript test suites (platform-mcp, vitest beyond `src/generated/__tests__`) were not run; no TypeScript source changed.
- CI was not run.

## 12. REBUILD CHECKLIST (v1.1, review LOW-4 and SS (c))

1. **`platform/src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts:132`** asserts the LIVE stored Sun `required_rupa` is 5 (`expect(sunPivot?.['required_rupa']).toBe(5)`, test at lines 114-136). It goes red the moment the rebuild lands; it is data-dependent and intentionally not edited in this PR. Flip it to 6.5 in the same step as the rebuild.
   * Where it runs (read from the repo, worker + read-only investigation): the file gates itself with `const INTEGRATION = process.env.INTEGRATION === 'true'` / `const describeIf = INTEGRATION ? describe : describe.skip` (lines 23, 28). The only CI workflow that collects it is `.github/workflows/ci.yml`, job `unit-tests` (lines 130-131), whose env (lines 140-141) is `NODE_ENV: test` only (no `INTEGRATION`, no `DATABASE_URL`); step line 221 `npm test -- --reporter=verbose` (`platform/package.json:11` = `vitest run`); `platform/vitest.config.ts:176-180` (project `node`) does not exclude it, so it is collected and skipped by its own `describe.skip` (CI run 34594715170 lists it as skipped). The only workflow that sets `INTEGRATION=true` is `judgment-integration-nightly.yml:121`, which runs only `register_d9_judgment.integration.test.ts`. `deploy.yml` runs no vitest. **Verdict: skipped in CI, never against live data; the rebuild cannot turn main or a deploy red through it**, so per the SS rule it is left unchanged and listed here instead.
2. Other data-dependent assertions across the eight S-L1 lanes: `DATA_DEPENDENT_ASSERTIONS_S_L1_v1_0.md` (this PR's `exec/` folder).
3. `platform/src/lib/pariprashna/corpus/fixtures.ts:567-585` (`remedial-005-rahu-weak-composite-lagna`) cites live Rahu composite values (0.0518, 0.414, 0.3622) that stop existing when the node rows become nulls (section 13). It is under the pariprashna deny pattern, so it is NOT touched here; refresh it (and bump its fixture/corpus version) in the Pariprashna lane. No test pins its values.
4. Pravaha's `l1_required_rupa_note` in `services/gochara_rules/registry.py` becomes stale (not this lane's file).
5. Rebuild L2-L5 after the L1 rebuild: `bo_laksana`, `bo_upaya` and the L3-L5 tables key off signal ids (section 13, downstream effect).

## 13. Rahu/Ketu composite rows: honest nulls (v1.1, SS ruling 2026-10-02)

`_NODE_LEGACY_COMPOSITE_REQUIRED = 5.0` (an invented normaliser for the nodes, CLAUDE.md N.7 item 6) is removed. For Rahu and Ketu `_build_composite_strength_rows` now emits ONE floored `bphs_weighted` row per house: `value_num` NULL, `verification_pass_status` `floored`, `fact_value_jsonb {"floored": true, "reason": "no_classical_required_value_for_node"}`, citation "no classical required shadbala value exists for the nodes", `constituent_facts_array` = the GA3 shadbala / bhava_bala fact ids that exist. The floor-set convention of this builder is kept (a floored (graha, house) emits the one floored row and not `simple_multiplication` / `cross_formula_divergence`); note that this also drops the nodes' `simple_multiplication`, which does not itself use a shadbala normaliser: a finer split (keep `simple_multiplication`) is possible but is not what the floor convention does and was not requested. A node's reason is ALWAYS exactly `no_classical_required_value_for_node` (no missing-fact suffix, even when its GA3 shadbala/bhava_bala fact is also absent; tested).

**Stored rows (SELECT-only, suvarna_reader, 2026-10-02), identical on 482012f1, 1c826d5a and cb73cd3d:** per chart 120 `bphs_weighted` (tier `single`), 120 `simple_multiplication` (`single`), 120 `cross_formula_divergence` (`computed_extension`) node rows (2 nodes x 12 houses x 5 ayanamshas); none integral, none NULL, none floored; category total 1620 per chart. After a rebuild: 120 floored `bphs_weighted` rows (120 tier changes `single` -> `floored`), the other 240 disappear, total 1620 -> 1380. The hook (`sun_required_rupa.json`) lists exactly these changes.

**Consumer read (read-only: grep + code + stored data; all consumers of `graha_in_house_composite_strength`): GO, no consumer breaks or silently coerces a NULL or the missing rows.**

| consumer (file:line) | handling | verdict |
|---|---|---|
| `bo_laksana.py:2268, 2416, 2427, 735-760` | null-guards `fact_value_num` into config / summary / headline; `floored`, `reason` land as inert config keys | handles null |
| `bo_laksana/formulas.py:538-554, 633-635` | `floored` is in `EXCLUDED_NO_VALUE_STATUSES`: rescale 0.0, salience 0.0 (live floored signals already exist, 210 per chart) | handles null |
| `bo_laksana.py:253-262, 310, 958, 3297-3300` | category list only / reads other categories / ranking | not affected |
| `bo_upaya.py`, `bo_karanajala.py`, `bo_bimba.py`, `ka_sangam.py`, `ka_yojaka.py`, `binder.py`, `mi_kula.py`, `ga_yoga_writer.py:153`, `ga_vichara_writer.py:98`, gates | other categories, or specific config keys; a NULL casts to NULL; LATERAL joins require plain-graha subjects that `*_IN_HOUSE_n` never matches | not affected |
| `migrations/904` live `integrity_check_sql` (d17)/(f17) | allows a group of 3 unfloored rows or exactly 1 floored row; NULL iff floored | handles null |
| `get_strength.ts:244-256` | active-house regex filter keeps the node's single floored row, `value_num` null passed through | handles null |
| `graha_portrait.ts`, `coverage_matrix.ts:197,379`, `register_p1_ganita.ts:439`, `grounding/resolver.ts`, `fact_identity_parser.py:560` | pass-through / names in a list / nothing queries the kind | not affected |
| `ga_structural` `count_sql` / `target_floor` 98446 | row total only; per chart 102037 -> 101797, 99082 -> 98842, 98866 -> 98626 (cb73cd3d margin 180 above the aspirational floor) | not affected |
| writer tests | `test_ga8_writer.py` (324 -> 276), `test_lane1_ga_structural_modularization.py` golden (324 -> 276, new digest), this lane's test file (nodes) | updated in this PR |
| `pariprashna/corpus/fixtures.ts:567-580` | stale narrative premise, no test pins it | see section 12 item 3 |

**Downstream effect on `bodha_msr_signals` (reasoned from the stored facts, not measured after a rebuild):** a `bo_laksana` composite signal's identity is built from `{fact_key, fact_value_num, fact_value_text}` with no subject or house, so identical configs collapse; the 24 floored node rows per ayanamsha become one anonymous floored `bphs_weighted` signal per ayanamsha. Composite signals per chart: 482012f1 990 -> 763 (-227, total 50,678, -0.45%), 1c826d5a 774 -> 563 (-211, -2.7%), cb73cd3d 1228 -> 1009 (-219, -2.6%). No bo_* count assertion is affected (the `bo_laksana` `count_sql` floor of 60000 is already unmet, aspirational). `kala_activation_predicates` and CGM/embedding/mimamsa tables key off signal ids, so removed node-valued signals leave dangling references until L2-L5 are rebuilt. **Pre-existing hazard, not caused by this lane:** `bo_laksana.py:3135` inserts with `ON CONFLICT DO NOTHING` and `bo_laksana.py:3602` raises "refusing a partial root generation" if `inserted != len(signal_rows)`; current data already collapses duplicates (e.g. 108 facts -> 78 distinct signals for raman on 482012f1), so a rebuild on current code may already raise: confirm before the S-L2 run (not run here).

## 14. ga_strength: no silent 5.0 default (v1.1, SS (b))

`ga_strength_writer.py` had `SHADBALA_REQUIRED.get(graha, 5.0)` at two sites. Reading the callers: the `required_rupa` / `ratio` loop (`_build_shadbala_rows`) iterates only the seven classical grahas, so nodes never reach it. The other site, `_citation_human_strength` for `graha_shadbala_total`, IS reached by the nodes (the nodal loop) AND by every classical graha, with `graha` being the SUBJECT display string ('SUN', 'MOON', 'MAR', ...), never a key of the Title-case table: the lookup therefore ALWAYS fell through to 5.0. Stored evidence (canonical chart, lahiri): `MOON total shadbala: 5.6500 rupa (surplus 0.65 vs required 5.00 rupa)` beside `Moon shadbala ratio: 0.942 (5.6500 achieved / 6.00 required; below classical minimum)`, `JUP ... vs required 5.00` (table 6.5), `MER ... 5.00` (7.0), `VEN ... 5.00` (5.5), `RAH_MEAN ... deficit 4.62 vs required 5.00`. So the default was not a harmless fallback: it masked a lookup that never matched, and after the Sun fix the Sun's own rupa citation would still have read 5.00 against an L1 required fact of 6.5.

Fix: new `required_rupa_for(graha)` raises `ValueError` for anything outside the seven; the `required_rupa` / `ratio` site uses it; the citation resolves the classical graha from the SUBJECT via `PLANET_TO_SUBJECT`, states the graha's own required value, states "no classical required minimum exists for the nodes" for RAH_MEAN / KET_MEAN, and raises for an unknown subject. Tests: raise for Rahu/Ketu/'SUN'/typos; seven citations carry their own required value; node text has no "vs required"; unknown subject raises; **mutation test**: the raise-check passes the real function and FAILS a mutant that reintroduces `.get(g, 5.0)`, plus a comment-stripped source scan for `SHADBALA_REQUIRED.get(`. Effect on stored data after a rebuild: `citation_human` text of the nine `graha_shadbala_total|rupa` rows per ayanamsha per chart (not a detector field, not a value); the achieved values are unchanged.

