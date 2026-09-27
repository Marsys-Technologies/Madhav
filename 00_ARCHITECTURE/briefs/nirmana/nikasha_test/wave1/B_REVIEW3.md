---
artifact: NIKASHA_WAVE1_LANE_B_REVIEW3
reviewer: Opus gate review 3 (fresh context, read-only, not the implementer)
reviewed_on: 2026-09-27
packet: Nikaṣa wave 1, Lane B — "the catalog names its producers" (R85 / D5 rev. 2.1), third submission
packet_commits: 14d9b0125 (R1) · 0a1f8c30b (R2) · 81b34ed85 (R6 closure statement) · c5731c54c (report v2.1, R3/R4/R5 + §7/§12)
prior_reviews: wave1/B_REVIEW.md (REJECT) · wave1/B_REVIEW2.md (REJECT narrow; open items R1–R6 in its §4)
authority: NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4 B-4, §5 · CLAUDE.md §N.7, §N.8
verdict: REJECT
---

# Lane B gate review 3

## §1 — Verdict

**REJECT, narrow: one blocking item (R7) and its report wording (R8).**

All six items from review 2 are closed. Each was closed by a proof that could have failed, and I
re-ran every one:

- **R1.** `--check` now fails through the real `main(["--check"])` in all three cases:
  - `"scus": {}` → exit 1, with all 182 missing SCUs named.
  - The artifact minus `get_dignity` → exit 1, naming it.
  - The artifact plus an unknown SCU → exit 1, naming it.

  Deleting the coverage call reddens exactly the three real-entry-point tests.
- **R2.** Mutating `:707` reddens the new production-shaped test. Re-deriving production under that
  mutation sends all 7 `source_ref_out_of_range` to `no_relation_in_range` (18). Reverting brings the
  7 back.
- **R6 (closure statement).** The SQL the report states reproduces 63 → 111 against production.
- **R3/R4/R5.** The report edits are accurate.

**No regression.** The re-derived `producer_provenance.derived.json` is byte-identical apart from
`generated_at`, and `CLOSURE_REPORT.md` is identical. The suite passes 25/25. No untouchable file was
touched.

**Why it still fails: checklist item 6 found a coverage bypass.**

- `--check` accepts any producer whose disposition is `reviewed_output`, `route_evidence_only` or
  `derived_from_service_probe` if its `source_ref` is any non-empty string.
- I hand-edited a copy of the artifact:
  - I replaced all 75 NO_DETECTOR SCUs with a fabricated
    `{asset_id: "zz_fake", disposition: "route_evidence_only", source_ref: "x"}`.
  - The copy now claims **182/182 named**.
  - `--check` printed **PASS, exit 0**, stating that every SCU "ha[s] a valid producer".
- This is a green signal with no detector behind it (§N.8). It also contradicts B-4's own definition
  ("the detector that makes 'every unit names its producer' able to read false").
- The report states G as a limit. It justifies not fixing it as needing "per-SCU contract-awareness
  this lane's … script does not currently have" (§12 item 4), and calls `--check` a validator "that
  reads one committed JSON file with no DB access" (§7). Since R1, both statements are false:
  - `--check` already loads the catalog snapshot.
  - The script already has `get_reviewed_claims()` and `get_non_reviewed_producer_output_claims()`.
  - All 24 exemption producers in the committed artifact are backed one-for-one by a snapshot claim or
    service_probe requirement.
  - So a check with no DB access would pass today's artifact and fail the fabricated ones.
- Review 2 accepted G as "state the limit". R1 removed that premise: `--check` now has the evidence in
  hand and still doesn't use it.

The lane does **not** need re-running. R7 is a small change with no DB access, confined to
`validate_derived_artifact`/`main()` and its tests. R8 is four wording fixes. Everything else stands as
submitted.

## §2 — Per item

Setup:
- Scratch mirror of `catalog_provenance.py`, with `REPO_ROOT` pinned to the worktree and outputs sent to
  the scratchpad.
- Test file copied unchanged.
- Base mirror: 25 passed.
- DB: `SHOW default_transaction_read_only` → `on`.

### R1 — `--check` validates coverage against the 182-SCU catalog. **CLOSED.**

**Probes on a copy of the committed JSON, through the real `main(["--check"])`** (driver `rev3/gov/r1probe.py`):

```
unchanged:         exit 0 | --check PASS: all 182 SCUs … coverage matches the catalog exactly
empty:             exit 1 | --check FAIL: 182 problem(s) against the catalog's 182 SCUs | named=182
                   distinct missing named = 182, all catalog ids named = True
minus_get_dignity: exit 1 | FAIL: 1 problem(s) | - scu.catalog.get_dignity: in the catalog snapshot but missing from the artifact's scus map
plus_unknown:      exit 1 | FAIL: 1 problem(s) | - scu.test.unknown: in the artifact but not in the catalog snapshot (stale entry)
```

**Mutation.** `coverage_failures = validate_scu_coverage(...)` → `coverage_failures = []`:

```
FAILED test_check_fails_on_an_empty_artifact_through_the_real_entry_point
FAILED test_check_fails_when_the_artifact_is_missing_a_catalog_scu_through_the_real_entry_point
FAILED test_check_fails_when_the_artifact_carries_an_unknown_scu_through_the_real_entry_point
3 failed, 22 passed
```

- Under the mutation, all four probes print PASS with exit 0 (empty, minus-one and plus-one all
  regress).
- The direct unit test `test_validate_scu_coverage…` correctly stays green, because it targets the pure
  function.
- After reverting: 25 passed.
- These are exactly the three real-entry-point tests. This also closes review 2's note that "no test
  drives `main(["--check"])`".

**Docstrings.**
- `validate_derived_artifact` (now `:1435`) is scoped to "ENTRY validity only". It points to
  `validate_scu_coverage` for coverage, which is true.
- The new `main()` comment ("checked BEFORE per-entry validity…") is true.
- The older `main()` comment just above it (`:1548-1551`) still says a "hand-edited" artifact "must be
  able to fail this". That holds for shape defects only; §4 R7 shows a hand-edit that passes. See R8.

**Catch-all test docstring.**
- `test_producer_output_requirement_with_no_claims…` now states that restoring the catch-all does
  **not** redden it, and names what it does catch. That is accurate.
- I re-ran M10 at HEAD, restoring
  `sp.no_detector = "; ".join(...) or "NO_DETECTOR — no source_query requirement"`:
  - **25 passed**, as the report now says.
  - `classify_no_detector_reason("NO_DETECTOR — no source_query requirement")` → `unclassified`.
  - So the report's stated guard (the closed-set classifier) is the real mechanism. No test detects
    the restoration itself, and the report says so plainly (§2 C-1 row).

**Undisclosed test weakening (non-blocking).**
- 14d9b0125 also deleted `assert "50-60" in stale[0]` from
  `test_compute_segment_resolution_counts_distinguishes_full_partial_none`. The commit message doesn't
  mention it.
- I restored the assertion and it passes, because `compute_segment_resolution_counts` still yields
  `'s: b.ts:50-60 (b.ts has 1 lines, ref 50-60)'`. The deletion was unnecessary.
- The M1 bounds-guard mutation still reddens this test through the `(1,1,1)` assertion, so no guard
  was lost. Restore the line or note it (N1).

### R2 — production-shaped test for the `:707` branch. **CLOSED.**

The new test,
`test_out_of_range_handler_segment_wins_priority_over_a_still_resolving_migration_segment`:
- builds an OOB handler segment (`get_something.ts:50-60` on a 1-line file) plus a resolving
  `supabase/migrations/204_chart_facts.sql:1-1`;
- asserts the reason class is `source_ref_out_of_range`.

**Mutation.** `:707 if oob_reasons:` → `if False:` (second occurrence; the `:693` branch left intact):

```
FAILED test_out_of_range_handler_segment_wins_priority_over_a_still_resolving_migration_segment
1 failed, 24 passed
```

**Production under the mutation** (driver `rev3/gov/derive.py cp_m2 m2`, DB read-only):

```
m2 named 107 / 182 no_detector 75 {'no_contract': 28, 'relation_unowned_by_registry': 28, 'no_relation_in_range': 18, 'derived_kind_no_source_query': 1}
m2 oob []
changed reasons: 7   (each: source_ref_out_of_range -> no_relation_in_range)
  get_ashtakavarga, get_aspects, get_avasthas, get_dignity, get_eclipse_flags, get_panchanga, get_structural
```

**Reverted:**

```
revert … {'no_contract': 28, 'relation_unowned_by_registry': 28, 'no_relation_in_range': 11, 'source_ref_out_of_range': 7, 'derived_kind_no_source_query': 1}
revert oob [the same 7]
```

### R3 (review 2) — reason-class reconciliation, all 11 named. **CLOSED.**

I diffed per SCU between the v1 artifact (`4e586118d`) and HEAD.

v1 classes: `PRODUCER 108, no_contract 28, relation_unowned_by_registry 29, no_relation_in_range 16, derived_kind 1`.

```
relation_unowned_by_registry -> no_relation_in_range 2 ['chart_snapshot', 'judgment_query']
no_relation_in_range -> source_ref_out_of_range      7 [get_ashtakavarga, get_aspects, get_avasthas, get_dignity, get_eclipse_flags, get_panchanga, get_structural]
PRODUCER -> relation_unowned_by_registry             1 ['query_graha_naisargika_friendship']
HEAD no_relation_in_range 11: call_dasha_eligibility, call_priority_ranking, chart_snapshot, get_vichara,
  judgment_query, query_cdlm_summary, query_mantras, query_remedies_by_planet, query_remedies_for_chart,
  query_tantric_remedies, read_remedy
```

- Report §3.3 states all of this exactly: 16 = 9 + 7; 29 − 2 + 1 = 28; the 11 named, as 5 remedy
  handlers + cdlm + dasha_eligibility + priority_ranking + get_vichara + chart_snapshot +
  judgment_query. Every label matches.
- **Sub-claims checked:**
  - `chart_snapshot`'s v1 reason was `['charts'] matched no row`, from `get_chart_snapshot.ts:205-215 |
    002_ganita_divisionals.sql:31-65`. Its handler range 205-215 is SQL-free post-processing. ✔
  - `judgment_query`'s `source_ref` is two `#anchor` handler citations plus two migration ranges
    (`435_ga_vichara.sql:83-115`, `204_chart_facts.sql:10-29`). ✔
  - Its classification limit is stated in §3.3 and §8 item 9. ✔
  - The line counts `get_aspects` 86, `get_avasthas` 91, `get_dignity` 104 and `get_eclipse_flags`
    60 match `wc -l`. ✔

### R4 (review 2) — 36, not 37 files. **CLOSED.**

- The scan (repo paths, no write) → `76 36`.
- `grep -c '^## \`' BUILD_DEPENDENCIES_READER_SCAN.md` → 36.
- The c5731c54c diff of the scan file only moves line numbers (L294→L295, L1267→L1310 and so on) and
  the timestamp.

### R5 (review 2) — C-1 mutation record scope; `via_helper` / def-guard facts. **CLOSED.**

- The §2 C-1 row states plainly that the "1 failed, 12 passed" record "was true only at commit
  `a4fef0f7c` itself". It also says restoring the catch-all at HEAD leaves 25/25 green, "NOT a live
  guard at HEAD".
- So the record is scoped to `a4fef0f7c` only and not re-established at HEAD, and the report says
  exactly that. I confirmed 25/25 under M10 at HEAD.
- The C-3 row now states that all 294 `derived_from_source_query` rows are `via_helper: null` and that
  the def guard is not load-bearing in production. ✔

### R6 (review 2) — closure computation stated; E/F/G listed; §12 true. **Closure half CLOSED; §12 half: see R7/R8.**

**The closure statement.** `CLOSURE_REPORT.md` now has a "How this closure is computed" section:
- the seed sets (`reviewed_seed` 14, `all_seed` 94);
- the edges (`asset_registry.depends_on`, one SELECT);
- the traversal (`transitive_upstream_closure`, a worklist walk, which I read at `:970-982`, and it
  matches the prose);
- the population (`is_active AND dead_flag IS NOT TRUE`);
- the SQL.

**The report's own SQL against production**, with seeds extracted from the committed JSON (14 and 94
ids):

```
63
111
count(*)=129 | is_active AND dead_flag IS NOT TRUE = 127 | literal NOT dead_flag = 0
```

The 16 still-outside assets from the same CTE are identical to the report's list.

**Mutation.** I deleted the section from `write_closure_report_md`: 1 failed
(`test_write_closure_report_md_states_the_closure_computation`), 24 passed.

**Non-blocking (N2).** The seed counts "14 assets" and "94 assets" and "the documented population of
127" are string literals in `write_closure_report_md`. They are not read from `closure[...]`, which
already carries `named_producers`. The R6 test passes with a fixture whose population is 1. If the
catalog changes, the prose will state stale numbers next to computed ones (§N.7 item 3).

**The §12 list.**
- It names: compiler.ts wiring (out of scope by design); editorial.ts (read only); the 12 stale
  `source_ref`s (registered); `--check` E/F/G; judgment_query; and the `route_evidence_only`-only SCU.
  That is the true set of undone items.
- E, F and G are stated plainly in §7, including the constructed examples.
- **But** item 4's reason for not fixing G is false, and G hides a green signal. See §4 R7.

**Item 6 constructions.** Driver `rev3/gov/gprobe.py`: a copy of the committed JSON with one edit, run
through the real `main(["--check"])`.

| case | edit | `--check` | named |
|---|---|---|---|
| G1 | `get_dignity` (no reviewed claim in the snapshot) → `{zz_fake, reviewed_output, source_ref "x"}` | **PASS exit 0** | 108/182 |
| G2 | all 75 NO_DETECTOR SCUs → `{zz_fake, route_evidence_only, source_ref "x"}` | **PASS exit 0** | **182/182** |
| G3 | disposition value `"totally_bogus"` | FAIL exit 1 ✔ | — |
| G4 | exemption disposition with `source_ref ""` | FAIL exit 1 ✔ | — |
| E | `{zz_fake, table no_such_table_xyz, source_ref nope.ts:1-2, derived_from_source_query}` | **PASS exit 0** | 108/182 |
| F | `get_dignity.no_detector = "anything at all; contain no relation name"` | PASS exit 0 | 107 (mislabel, not coverage) |

**Can the exemption tier be checked from the snapshot `--check` already loads?**

```
committed exemption producers NOT backed by a snapshot claim: []            (15 reviewed_output + route_evidence_only)
9 service_probe rows; unbacked by snapshot service_probe requirement: []
```

**Answers to item 6:**
- A bogus disposition **value** fails (G3).
- A bogus **string** under a legitimate exemption disposition makes an SCU count as covered (G1, G2).
  That is a coverage bypass.
- F only mislabels an SCU; it is a real limit, stated plainly, and not a coverage bypass.
- E is also a coverage bypass. Fully detecting it needs the DB (table existence), so leaving that part
  as a stated limit is defensible. The report's reason for E holds; its reason for G does not.

## §3 — Items 7 and 8

**Item 7 — nothing untouchable touched. Clean.**

```
14d9b0125  CLOSURE_REPORT.md, producer_provenance.derived.json, test_catalog_provenance.py, catalog_provenance.py
0a1f8c30b  test_catalog_provenance.py
81b34ed85  CLOSURE_REPORT.md, producer_provenance.derived.json, test_catalog_provenance.py, catalog_provenance.py
c5731c54c  BUILD_DEPENDENCIES_READER_SCAN.md, CLOSURE_REPORT.md, producer_provenance.derived.json, B_REPORT.md
```

- `git diff --name-only 14d9b0125^ c5731c54c | grep -iE "migration|writer|orchestrator|editorial|compiler|ledger|STATE|register"`
  → nothing.
- The range `6a7c38e29..c5731c54c` also contains `ce5ab9ce9` (B_REVIEW2) and `d1a3988f4` (Lane A's
  A_REPORT.md). Neither is a packet commit.
- The script's DB access is SELECT-only, and the session was read-only.
- `manifest_fingerprint.py --check` → `MATCH f484f581767ad641`.
- `git status` is clean apart from the pre-existing `.agents/`. All my runs wrote only to the
  scratchpad.

**Item 8 — regression. None.**

- Full re-derivation at HEAD against production, into scratch:

  ```
  head named 107 / 182 no_detector 75 {'no_contract': 28, 'relation_unowned_by_registry': 28, 'no_relation_in_range': 11, 'source_ref_out_of_range': 7, 'derived_kind_no_source_query': 1}
  head closure before 63 after 111 pop 127 outside {'table_unregistered': 2, 'no_unit_names_it': 14}
  head check_completeness []
  JSON identical sans generated_at: True   (also byte-identical with the timestamp line removed)
  CLOSURE_REPORT identical (sans generated_at)
  ```

- Reader scan: 76 hits / 36 files. Suite: 25/25.
- Across `6a7c38e29 → c5731c54c`, the only change to `producer_provenance.derived.json` is
  `generated_at`, and `CLOSURE_REPORT.md` only gains the R6 section.
- **No R-item changed a derived producer or a reason class**, which matches the commit messages.
- The commit messages' own self-correction (R1's closing "24 passed" was really 23 at that commit,
  corrected in the R2 message) is accurate.

## §4 — Remaining findings

| # | finding | evidence | gate it blocks | correction |
|---|---|---|---|---|
| **R7** | **`--check` has no detector for the exemption tiers, so a fabricated producer makes an uncovered SCU pass** (§N.8). `reviewed_output`, `route_evidence_only` and `derived_from_service_probe` need only a non-empty `source_ref`. A copy with all 75 NO_DETECTOR SCUs given a fake `route_evidence_only` producer claims 182/182 and passes. Since R1, `--check` loads the snapshot that holds the ground truth for all three tiers, and all 24 committed exemption rows are backed by it. An SCU whose only producer is `route_evidence_only` also passes, against B-4's "neither a reviewed nor a derived producer" (§7 and §12 item 6 call this "latent"; it is the same missing detector). | §2 R6 table G1 and G2; `unbacked: []` for all 24 exemption rows | B-4 ("the detector that makes 'every unit names its producer' able to read false"); the R85 fold, which relies on `--check PASS` | In `validate_derived_artifact` (or a sibling run from `main()`), use the snapshot to require: each `reviewed_output` / `route_evidence_only` producer matches a snapshot `producer_output_claims` entry `(scu_id, asset_id, disposition)`; each `derived_from_service_probe` producer matches a `kind: service_probe` requirement's `asset_id` on that SCU; and an SCU whose only producers are `route_evidence_only` is not counted as covered, **or** get an explicit native ruling that it should be, recorded in the report. Add real-entry-point tests for G1 and G2 (exit 1, SCU named), plus a mutation that removes the check and reddens them. The committed artifact must still PASS. No DB access needed. E may remain a stated DB-bound limit. |
| **R8** | **Four wording defects overclaim what `--check` detects.** (a) §12 item 4 says G would need "per-SCU contract-awareness this lane's … script does not currently have", which is false (`get_reviewed_claims`, the loaded snapshot). (b) §7 calls `--check` a validator "that reads one committed JSON file", but since R1 it reads two. (c) §6 says "a stale/hand-edited entry — all now correctly fail", true only for shape defects. (d) The `main()` comment at `:1548-1551` says a hand-edited artifact "must be able to fail this". Also, the PASS line asserts "have a valid producer" where "valid" means only a non-empty string for exemption rows. | §2 R6; report §6, §7, §12 | Gate item 6 (report honesty) | Once R7 lands, restate (a)–(d) to match what the detectors check. If any part of G is left unfixed by ruling, the PASS line must say which tiers are shape-checked only. |
| N1 | 14d9b0125 silently deleted `assert "50-60" in stale[0]`, which still passes when restored. | §2 R1 | none (non-blocking) | Restore it, or state why it was removed. |
| N2 | The closure-report prose hardcodes 14 / 94 / 127 instead of reading `closure[...]`. | §2 R6 | none (non-blocking) | Interpolate from `closure`. |

## §5 — Fact spot-check (B_REPORT v2.1)

| # | claim | result |
|---|---|---|
| 1 | 107/182 named; 75 NO_DETECTOR; 28/28/11/7/1 (§3.3) | **VERIFIED** (re-derivation, byte-identical) |
| 2 | 16 = 9 + 7; 29 − 2 + 1 = 28; the 11 `no_relation_in_range` named (§3.3, R3) | **VERIFIED** (v1→HEAD per-SCU diff) |
| 3 | 7 `source_ref_out_of_range` named, line counts 86/91/104/60 (§3.3) | **VERIFIED** |
| 4 | R1: empty / missing / unknown each fail through the real `main(["--check"])`; removing coverage → 3 failed (§2b) | **VERIFIED** (3 failed, 22 passed at HEAD; 20 passed at the R1 commit) |
| 5 | R2: `:707 → if False` → 1 failed; production → 28/28/18/1, OOB 0 (§2b) | **VERIFIED** |
| 6 | R6: removing the closure section → 1 failed, 24 passed (§2b) | **VERIFIED** |
| 7 | the closure SQL in CLOSURE_REPORT.md gives 63 (14 seeds) and 111 (94 seeds) over 127 | **VERIFIED** (run verbatim against production) |
| 8 | 16 outside = 2 `table_unregistered` + 14 `no_unit_names_it` (§4) | **VERIFIED** (SQL list identical) |
| 9 | reader scan 76 hits / 36 files (§5, R4) | **VERIFIED** |
| 10 | restoring the catch-all at HEAD leaves 25/25 green; the C-1 record held only at `a4fef0f7c` (§2 C-1) | **VERIFIED** |
| 11 | all 294 derived rows `via_helper: null` (§2 C-3) | **VERIFIED** (review 2; unchanged artifact) |
| 12 | 25/25 tests pass (§6) | **VERIFIED** |
| 13 | JSON byte-identical to pre-R1 apart from `generated_at` (commit messages, §12) | **VERIFIED** |
| 14 | manifest fingerprint MATCH `f484f581767ad641` (§11) | **VERIFIED** |
| 15 | "a stale/hand-edited entry … all now correctly fail" (§6) | **PARTLY WRONG**: a shape-defective entry fails; a fabricated exemption producer passes (G1/G2) |
| 16 | G "would need per-SCU contract-awareness this lane's … script does not currently have" (§12 item 4) | **WRONG**: the snapshot is loaded by `--check` and `get_reviewed_claims()` exists; all 24 exemption rows are snapshot-backed |
| 17 | `--check` is "a structural validator that reads one committed JSON file with no DB access" (§7) | **STALE since R1**: it reads the JSON and the snapshot |
| 18 | only Lane B files touched across the four commits (§1, §10) | **VERIFIED** |
