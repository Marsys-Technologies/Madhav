---
artifact: NIKASHA_WAVE1_LANE_B_REVIEW2
reviewer: Opus gate re-review (fresh context, read-only, not the implementer)
reviewed_on: 2026-09-27
packet: Nikaṣa wave 1, Lane B — "the catalog names its producers" (R85 / D5 rev. 2.1), re-submitted after REJECT
packet_commits: a4fef0f7c (C-1) · 6fa514fc5 (C-2+C-4) · 91658a6a9 (C-3) · f1e244c09 (C-5) · 875809a7b (C-6) · 6a7c38e29 (report v2.0)
prior_review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW.md (REJECT, packet 4e586118d)
authority: NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §2, §4, §6 · CLAUDE.md §N.7, §N.8
verdict: REJECT
---

# Lane B gate re-review

## §1 — Verdict

**REJECT, on a narrow basis.** Most of the corrections are real, and every headline figure reproduces.
I re-derived against production (read-only) and got the committed `producer_provenance.derived.json`
back byte-identical apart from `generated_at`. `CLOSURE_REPORT.md` is also identical. The key figures are
107/182, 75 NO_DETECTOR, 113/23/1, 63→111/127, 16 outside split 2/14, and a reader scan of 76.
C-3, C-5 and C-6 are closed by tests that fail when their guard is removed; I ran each mutation myself.
The four false producers are gone. No untouchable file was touched.

But the gate asks whether each correction survives an attempt to break it, and two don't. Both fail in the
same way the original findings 1 and 2 did (§N.8: a signal with no detector behind it).

1. **`--check` still passes with no detector on SCU coverage.** It validates only the entries present
   in the artifact. It never compares them against the catalog's 182 SCUs. An artifact with `"scus": {}`
   prints `--check PASS: all 0 SCUs … exit 0`, and an artifact missing `get_dignity` passes with 181. The
   function's own docstring says an SCU "simply absent from the artifact's `scus` map, is a failure"
   (`catalog_provenance.py:1374`). The `main()` comment says a stale artifact "left over from before a
   snapshot/registry change" must be able to fail (`:1474`). Neither claim has code behind it.
2. **The branch behind all 7 production `source_ref_out_of_range` outcomes has no test.** Removing the C-4
   priority branch (`catalog_provenance.py:707-711`) leaves **19/19 green**. Re-deriving production with
   that mutation turns all 7 back into `no_relation_in_range`, which is exactly finding 4's defect. The
   rewritten case-2 test only covers the "nothing resolved" branch, and no production SCU takes that branch.

The report also has four smaller accuracy defects (§4 R3–R6). None of them moves a headline.

**What would change the verdict to ACCEPT.** The derivation, the closure and C-3/C-5/C-6 are accepted as they
stand and don't need re-running. The re-submission only needs R1 and R2 in §4, each with a mutation that
reddens a named test, plus the report edits R3–R6. None of this needs a writer, the orchestrator, the
registry or a production write.

## §2 — Per finding

### C-1 — `--check` could not read false. **Closed for entries; not closed for coverage.**

- **The catch-all is gone.**
  - `grep -n 'no source_query requirement"' catalog_provenance.py` finds only the `kind: derived` branch
    (`:852`), which is a real named path. `derive_all` now leaves `no_detector=None` when no branch
    supplies a reason (`:866-876`).
- **`--check` reads the committed artifact.**
  - `main()` (`:1471-1497`) opens `DERIVED_OUTPUT_PATH` and calls `validate_derived_artifact`. It opens no
    DB connection and does not re-derive.
  - I confirmed this empirically by pointing `cp.DERIVED_OUTPUT_PATH` at scratch copies (driver
    `scratchpad/rev2/c1.py`).
- **Constructed cases, through the real `main(["--check"])`:**

| probe (scratch copy of committed JSON) | result |
|---|---|
| unmodified copy | `PASS: all 182 SCUs` exit 0 |
| A: add SCU `{producers: [], no_detector: null}` | `FAIL: 1 SCU(s) … scu.test.orphan_null` **exit 1** ✔ |
| B: add SCU whose reason is the old catch-all text | `FAIL … scu.test.orphan_freetext` **exit 1** ✔ (it classifies `unclassified`) |
| C: end-to-end. I injected 4 SCUs into the real snapshot, ran `_run_derivation` against production, wrote the result to scratch, then ran `--check` on it | the SCU with a producer_output requirement and an empty-disposition claim gets `no_detector=None` → `FAIL … scu.test.orphan_pipeline` **exit 1** ✔. Unclaimed producer_output → `producer_output_unclaimed`. Empty contract → `no_contract`. The review-1 orphan with only a `route_evidence_only` claim → carried as a producer (passes). |
| D: delete `scu.catalog.get_dignity` | `PASS: all 181 SCUs` **exit 0** ✘ |
| D2: `"scus": {}` | `PASS: all 0 SCUs` **exit 0** ✘ |
| E: set a derived producer's table/asset to `no_such_table_xyz`/`zz_fake` | PASS exit 0 (the table is not cross-checked; a limit, not stated) |
| F: set `get_dignity`'s reason to "no availability_contracts requirement" (wrong for that SCU, but in the closed set) | PASS exit 0 (the classifier matches substrings and never checks the reason against the SCU's actual contract; a limit, not stated) |
| G: replace `get_dignity` with a fake `route_evidence_only` producer, source_ref `"x"` | PASS exit 0 (an exemption disposition only needs a non-empty string) |

- **Tests:**
  - M11 (`validate_derived_artifact` accepts any non-empty reason) → 1 failed:
    `test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry`. ✔
  - M10 (restore the catch-all at HEAD) → **19 passed**.
  - The docstring of `test_producer_output_requirement_with_no_claims_gets_an_exact_reason_not_a_catchall`
    (`__tests__:370-373`) says this mutation fails it. It can't, because that SCU always has a
    per-requirement reason, so the `or` never fires.
  - The report's C-1 mutation record ("1 failed, 12 passed") is true at `a4fef0f7c`. I re-ran it there:
    `test_derive_all_leaves_a_genuinely_unclassified_scu…` failed. That test was rewritten in C-5, so the
    record is not true at HEAD.
  - The catch-all is still harmless at HEAD, because `--check` classifies its text as `unclassified`
    (probe B). But the test suite no longer guards it, and the report doesn't say that.
  - No test drives `main(["--check"])`. If `main` went back to re-deriving in memory, no test would fail.
- **Verdict on C-1:**
  - The checklist's constructed case exits non-zero, so the catch-all half is closed.
  - Validating "every SCU", and so detecting a stale artifact, is **not** closed. R1 blocks.

### C-2 / C-4 — the out-of-range reason class. **Guard proven; the load-bearing branch unproven.**

- **The split reproduces:**
  - `compute_segment_resolution_counts` → `113 23 1`, with 12 stale pieces. The list is identical to
    report §3.4, including actual line counts (for example `get_dignity.ts has 104 lines, ref 78-108`).
  - `no_detector_reason_counts`: `source_ref_out_of_range` = 7, exactly `get_ashtakavarga, get_aspects,
    get_avasthas, get_dignity, get_eclipse_flags, get_panchanga, get_structural`.
- **The two named mutations**, run on a scratch copy with the test file unchanged:

| mutation | result |
|---|---|
| M1 delete the OOB guard (`:309-310`) | **2 failed**: `test_unresolvable_range_yields_no_detector_with_reason`, `test_compute_segment_resolution_counts_distinguishes_full_partial_none`. That matches the report's record (2 failed), so it is 2 tests, not "exactly one". |
| M3 remove the reason fallback when nothing resolved (`:693` `if oob_reasons:` → `if False:`) | **1 failed**: `test_unresolvable_range_yields_no_detector_with_reason` ✔ |
| **M2** remove the C-4 priority branch when *another* segment resolved (`:707` `if oob_reasons:` → `if False:`) | **19 passed** ✘ |

- **M2 against production** (driver `scratchpad/rev2/m/a/b/gov/m2prod.py`):
  - Result: `{'no_contract': 28, 'relation_unowned_by_registry': 28, 'no_relation_in_range': 18,
    'derived_kind_no_source_query': 1}`, and **`source_ref_out_of_range` goes to 0**.
  - All 7 committed reasons contain "no relation name found in the remaining resolved handler-kind
    segment(s)", so all 7 come from the M2 branch. Each of the 7 carries a migration segment
    (`204_chart_facts.sql:10-29`) that resolves.
  - The tested branch (M3) produces **zero** production outcomes.
- The report's C-2 row claims the fix works "even when another segment in the same `source_ref` did
  resolve". Nothing proves that claim.
- **Verdict:** finding 2 (the case-2 test can't fail under the guard deletion) is closed. Finding 4's
  production outcome depends on an untested line. R2 blocks.

### C-3 — the four false producers. **Closed.**

- **Diff of the committed v1 JSON (`4e586118d`) against HEAD, per SCU:**
  - `get_ayurdaya` −`ga_dashas/chart_dashas`
  - `get_sensitive_degrees` −`ga_dashas/chart_dashas`
  - `query_compendium_index` −`bg_texts`, −`bg_text_index`
  - `query_graha_naisargika_friendship` −`bg_dignity_reference`, now `relation_unowned_by_registry` on
    `['bg_graha_naisargika_friendship']`
  - Also `get_chart_header` −6 `chart_facts` co-producers, now narrowed to `ga_positions`.
  - Nothing else changed.
- **The `get_chart_header` narrowing is correct.** `chart_header.ts:83-86` pins
  `fact_category = 'graha_position'`, and `ga_positions`' NKP is
  `IN (graha_position, graha_sign_attributes, …)`. No other `chart_facts` owner declares
  `graha_position`. The `ga_dashas`/`chart_dashas` row is a real read (`chart_header.ts:90`).
- **Mutations:**
  - M4 remove the def-header guard → 1 failed (`test_one_hop_follower_skips_a_definition_header_not_a_call`).
  - M5 remove the segment-kind exclusion → 2 failed (migration + writer tests).
  - M6 drop only the writer branch → 1 failed (writer test).
  - M7 drop only the migration branch → 1 failed (migration test).
  - Every cause has its own test that fails without its guard. ✔
- **Note (not blocking):**
  - In production, the `ga_dashas` removal is done by the *writer-kind* exclusion, because
    `_idempotency.py` lives under `ga_writers/` (`classify_segment_kind` → `writer`). The def guard is
    correct but not load-bearing today.
  - All 294 `derived_from_source_query` rows have `via_helper: null`, so the one-hop follower contributes
    no production producer. That is worth stating in the report (see R5).

### C-5 — report overstatements, and the route_evidence_only tier. **Closed in substance; new accuracy defects (R3, R4).**

- **15 vs 14.** All `producer_output_claims` give 15 assets (the extra is `ka_kalasutra`); reviewed only
  gives 14, across 12 SCUs. The off-by-one claim is retracted. Independent SQL closure: 14 seeds → 63,
  and 14 + `ka_kalasutra` → **63**. ✔
- **`route_evidence_only` is carried as its own tier.** `scu.kala.temporal_activation` has
  `('ka_kalasutra','kala_activation','route_evidence_only')` alongside the derived row. It is not in the
  reviewed seed. ✔
- **The service-probe disposition is named.** There are 9 rows with `table: null`. Their `source_ref` is a
  file path (`nirmana_probe_contracts.json`, migration 624), not a range. ✔
- **Figures:**
  - producer_output: 12 requirements across 11 SCUs ✔
  - 12 reviewed + 95 derived-only SCUs = 107 ✔
  - 14 + 80 = 94 assets ✔
  - 27 unowned tables ✔. The list matches the report. It is a different 27 from v1: `charts` dropped
    out and `bg_graha_naisargika_friendship` came in.
  - all 9 `ph_*` are direct `derived_from_source_query` producers ✔
  - `kala_activation` ✔
  - reader scan **76** with `WAVE1_DIR` excluded ✔. M12 (drop the exclusion) → 1 failed. M8 (drop the
    carry-through) → 1 failed.
- **Defects in the new text:** the files count (R4), and the reason-class reconciliation (R3).

### C-6 — table_unregistered vs no_unit_names_it. **Closed for the class; the "state the closure computation" half not landed (R6).**

- **Counts:** `still_outside_reason_class_counts` = `{'no_unit_names_it': 14, 'table_unregistered': 2}`,
  where the 2 are `bg_prashna_rules` and `ga_prashna`.
- **The link holds.** The six prashna SCUs are all `relation_unowned_by_registry` on the six tables
  named. `bg_prashna_rules` is at `pipeline/orchestrator/writers/bg_prashna_rules.py`.
- **Independent SQL:**
  - I ran the recursive CTE over `depends_on`, seeded with the 94 named assets, as SQL rather than
    through the packet's code. It gives 111, and the 16 outside are identical to the list.
  - The stem heuristic's limit (it doesn't give a 1:1 table assignment) is stated.
- **Mutation:** M9 (remove the branch) → 1 failed. ✔
- **Not landed:** review 1's C6 also asked for "the closure computation (not only the population query)"
  to be stated in `CLOSURE_REPORT.md`. The report still states only the population query, with no
  traversal description or SQL (R6).

## §3 — Checklist items 2–6

**Item 2 — nothing untouchable.**
- **Per-commit file lists:** across the six commits, the only files are `catalog_provenance.py`,
  `__tests__/test_catalog_provenance.py`, `nikasha_test/provenance/{producer_provenance.derived.json,
  CLOSURE_REPORT.md, BUILD_DEPENDENCIES_READER_SCAN.md}` and `wave1/B_REPORT.md`.
- **Why the range diff shows more:** `git diff b2a2a7920 6a7c38e29 --stat` also lists `asset_census.py`
  and two `test_a3_*` tests. Those come only from Lane A's interleaved commit `7ed870775`
  (`git log b2a2a7920..6a7c38e29 -- asset_census.py` → that commit alone), not from this packet.
  Excluding them, the diff is exactly the 6 Lane B files.
- **Nothing else touched:** no writer, orchestrator, `editorial.ts`, `compiler.ts`, migration, ledger or
  STATE file.
- **Read-only:** the script's only DB calls are two SELECTs (`:213`, `:238`), and the session was
  read-only (`SHOW default_transaction_read_only` → `on`).
- **Fingerprint:** `manifest_fingerprint.py --check` → `MATCH f484f581767ad641`.
- My own runs wrote only to the scratchpad. `git status` is clean apart from the pre-existing
  `.agents/`. **Clean.**

**Item 3 — honest tiers.**
- **Dispositions:** `derived_from_source_query` 294, `reviewed_output` 14, `derived_from_service_probe` 9,
  `route_evidence_only` 1.
- **Every derived row checks out:**
  - it has a non-null table and a range-shaped `source_ref`;
  - its table equals its asset's `target_table`;
  - its asset is active.
- **Tables:** 70 distinct derived tables, all in `information_schema.tables`, with no noise word
  (`today/the/one/unnest/refs`).
- **Limits:** the 9 service-probe rows and the 1 route-evidence row carry no range. They are declared
  exemptions, and the report now says so. **Clean, with one limit to state.** An SCU whose *only*
  producer is `route_evidence_only` passes `--check`, though §4 B-4 defines the gate as "a reviewed nor a
  derived producer". No production SCU is in that state today.

**Item 4 — figures reproduce.**
- Re-derivation: `named 107 of 182 · before 63 seeds 14 · after 111 seeds 94 · outside
  {no_unit_names_it 14, table_unregistered 2} · check_completeness [] · segres 113 23 1 (12 stale)`.
- Comparison: JSON `identical: True` apart from `generated_at`, and CLOSURE_REPORT identical apart from
  `generated_at`.
- Population: 129 rows; `is_active AND dead_flag IS NOT TRUE` = **127**; literal `NOT dead_flag` = 0.
- Independent SQL closure: 63 (14 seeds), 63 (15 seeds), 111 (94 seeds). ✔

**Item 5 — regression.**
- **Sampled derived producers that review 1 did not sample**, each read in its handler range:
  1. `get_chart_header` → `ga_positions`/`chart_facts` (`chart_header.ts:83`, graha_position pin)
  2. `get_chart_header` → `ga_dashas`/`chart_dashas` (`chart_header.ts:90`)
  3. `get_ayurdaya` → `ga_ayurdaya`/`chart_facts` (`get_ayurdaya.ts:85`)
  4. `query_compendium_index` → `bg_compendium_index`/`brahma_compendium_index` (`query_compendium_index.ts:79`)
  5. `query_muhurta_lattice` → `bg_muhurta_lattice` (`:141`)
  6. `query_domain_reading` → `bo_drishti`/`bodha_question_lenses` (real `FROM` at range lines 71/87, i.e. file ~750/766), plus `bo_sangati`/`bodha_cdlm_cells` (`:713`)
  7. `query_projections` → `ka_bhavishya_lekha`/`kala_bhavishya` (real `FROM kala_bhavishya` in range)
  8. `query_anomaly_flags` → `ph_sodhana`/`phala_sodhana` (`query_phala_calibration.ts:323`)
  9. `query_insights` → `mi_darshana`/`mimamsa_insight_units` (`:225`) and `mi_pramana`/`mimamsa_calibration` (`:247`)
  - **All real reads.**
- **Per-SCU diff v1→HEAD:** the only producer changes are the 4 removals, the `get_chart_header`
  narrowing and the `route_evidence_only` addition. No legitimate producer was lost to the writer or
  migration exclusion.
- **Newly misleading (R3):** two SCUs moved from the 29-class to `no_relation_in_range` because their
  only relation came from excluded migration segments. These are `chart_snapshot` (`charts` via migration
  002) and `judgment_query`.
  - `judgment_query`'s handler citations are all `#anchor` shapes, so **no handler range was ever
    resolved**.
  - It still reads "resolved source range(s) contain no relation name in any handler-kind segment", which
    classifies as `no_relation_in_range`. The honest class is closer to `source_ref_unresolvable_shape`
    for its handler segments. It is minor, but it is a C-3 side effect the report doesn't mention.

**Item 6 — honesty of the report.**
- All headline figures reproduce.
- Mutation excerpts: C-2, C-3, C-5 and C-6 match what I observed.
- C-1's excerpt is true only at `a4fef0f7c` (§2 C-1).
- §6's "a stale/hand-edited artifact entry … now correctly fail" is true for entries and false for
  missing SCUs.
- §12 "Nothing from the six corrections is left undone" is false in two places:
  - C-6's closure-computation statement (R6);
  - C-1's stale-artifact claim (R1).

## §4 — Remaining findings

| # | finding | evidence | gate it blocks | correction |
|---|---|---|---|---|
| R1 | `--check` never checks SCU coverage. An empty or partial artifact passes. The docstring (`:1374`) and `main()` comment (`:1474`) claim otherwise (§N.8). | probes D (`all 181 … exit 0`) and D2 (`all 0 SCUs … exit 0`) | §6 "`--check` runs and its figures reproduce"; the R85 fold; B-4 "exits non-zero when **any** SCU has neither…" | In `--check`, load the snapshot (a file read, no DB). Fail on any snapshot `scu_id` missing from the artifact, and on any artifact `scu_id` not in the snapshot. Add a test that drives `main(["--check"])` against a tmp artifact with one SCU removed and one with `scus: {}` (must exit 1). Show a mutation that deletes the coverage check and reddens it. |
| R2 | The C-4 priority branch (`:707-711`) produces all 7 production `source_ref_out_of_range` outcomes and has no test. Mutating it leaves 19/19 green and reverts production to 7 × `no_relation_in_range`. | M2: 19 passed; `m2prod.py` → `source_ref_out_of_range` 0 | §2.5 "each needs a test that fails without the change"; review-1 C4 | Add a fixture shaped like production: an OOB handler segment plus an in-bounds `supabase/migrations/…sql` segment. Assert the class is `source_ref_out_of_range`. Record the M2 mutation reddening it. |
| R3 | The reason-class accounting is not reconciled. "11 `no_relation_in_range` (down from 16)" and "28 … see §3.5 for the reconciliation" are both unexplained: §3.5 doesn't reconcile. The real path is 16 = 9 + 7, and 29 − 2 (`chart_snapshot`, `judgment_query` → `no_relation_in_range`) + 1 (`query_graha_naisargika_friendship`) = 28. The "remaining 11" explanation names only 8 (6 remedy + cdlm + dasha_eligibility); `chart_snapshot`, `judgment_query`, `get_vichara`/`call_priority_ranking` are unexplained. `judgment_query` is misclassified (§3 item 5). | the class-transition table from my v1→HEAD diff | gate item 6 (report honesty) | State the transitions exactly and name all 11. Either classify all-anchor handler refs as `source_ref_unresolvable_shape`, or state the limit. |
| R4 | "Same 37 files" (§5) is wrong: the re-run gives **76 hits across 36 files**, and the committed scan lists 36 headers. The 37th was `wave1/B_REPORT.md`, which is now excluded. | `scan_build_dependencies_readers()` → `76 36`; `grep -c '^## \`'` → 36 | gate item 6 | Correct to 36. |
| R5 | The C-1 mutation record and a test docstring overstate. At HEAD, restoring the catch-all leaves 19/19 green. `test_producer_output_requirement_with_no_claims…`'s docstring says that mutation reddens it, and it can't. Also unstated: all 294 derived rows have `via_helper: null`, and the def guard isn't load-bearing in production. | M10: 19 passed; `a4fef0f7c` re-run: 1 failed there | gate item 6; §2.5 | Correct the docstring and the report's C-1 row: the HEAD guard is the closed-set classifier (M11 → `test_validate_derived_artifact…`). State the `via_helper` / def-guard facts. |
| R6 | The C-6 half is not landed: `CLOSURE_REPORT.md` still states only the population query, not the closure computation. `--check`'s exemption and substring-classifier limits (probes E/F/G) are also unstated. | `grep -n "depends_on\|recursive" CLOSURE_REPORT.md` → only the prose reason lines | §4 B-2 "every query and population stated"; gate item 6 | Emit the traversal (seed sets + recursive `depends_on` walk, or the equivalent SQL) in `CLOSURE_REPORT.md`. List the E/F/G limits under B_REPORT §7. |

## §5 — Fact spot-check

| # | claim (B_REPORT v2.0) | result |
|---|---|---|
| 1 | 107/182 SCUs named; 75 NO_DETECTOR (§3.3) | **VERIFIED** (byte-identical re-derivation) |
| 2 | reason classes 28 / 28 / 11 / 7 / 1 (§3.3) | **VERIFIED** |
| 3 | 7 `source_ref_out_of_range` SCUs, named, with line counts (§3.3) | **VERIFIED** (all 7 come from the untested branch, R2) |
| 4 | 113 full / 23 partial / 1 none; 12 stale refs named (§3.4) | **VERIFIED** (the list is identical) |
| 5 | 4 false producers removed; `query_graha_naisargika_friendship` → relation_unowned (§3.5) | **VERIFIED** |
| 6 | 14 reviewed assets / 15 all-claim assets; 15 seeds also → 63 (§7) | **VERIFIED** (independent SQL CTE) |
| 7 | producer_output = 11 SCUs / 12 requirements (§7) | **VERIFIED** |
| 8 | 12 + 95 SCUs = 107; 14 + 80 = 94 assets (§7) | **VERIFIED** |
| 9 | 27 unowned tables, with the list (§3.3) | **VERIFIED** (the set differs from v1's 27: −`charts`, +`bg_graha_naisargika_friendship`) |
| 10 | before 63/127 (14 seeds) → after 111/127 (94 seeds) (§4) | **VERIFIED** (packet code and independent SQL) |
| 11 | 16 outside = 2 `table_unregistered` + 14 `no_unit_names_it`, named (§4) | **VERIFIED** |
| 12 | all 9 `ph_*` are direct `derived_from_source_query` producers (§4) | **VERIFIED** |
| 13 | temporal_activation / yoga SCU timing table is `kala_activation` (§4) | **VERIFIED** |
| 14 | reader scan 76 hits, stable, WAVE1 excluded (§5) | **VERIFIED** |
| 15 | "same 37 files" (§5) | **WRONG**: 36 |
| 16 | "11 no_relation_in_range (down from 16)", explained as remedy handlers + cdlm + dasha_eligibility (§3.3) | **WRONG** framing: 9 of the old 16 + 2 moved from the 29-class; the explanation covers 8 of 11 |
| 17 | 28 relation_unowned "reconciled in §3.5" (§3.3) | **WRONG**: §3.5 doesn't reconcile it (29 − 2 + 1) |
| 18 | 9 `derived_from_service_probe` rows, `table: null` (§7) | **VERIFIED** |
| 19 | 19/19 tests pass (§2) | **VERIFIED** |
| 20 | C-1: restoring the catch-all → 1 failed (§2) | **WRONG at HEAD** (19 passed); true at `a4fef0f7c` |
| 21 | C-2: removing the bounds guard → 2 failed; C-3 1 / 2; C-5 1 / 1; C-6 1 (§2) | **VERIFIED** |
| 22 | a stale / hand-edited artifact now fails `--check` (§6) | **PARTLY WRONG**: a hand-edited entry fails; a missing SCU or an empty `scus` passes |
| 23 | manifest fingerprint MATCH `f484f581767ad641` (§11) | **VERIFIED** |
| 24 | only Lane B files touched across the six commits (§1, §10) | **VERIFIED** (the extra files in the range diff are Lane A's `7ed870775`) |
