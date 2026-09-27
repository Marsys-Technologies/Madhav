---
artifact: NIKASHA_WAVE1_LANE_B_REPORT
canonical_id: NIKASHA_WAVE1_LANE_B_REPORT
version: "2.3"
status: SUBMITTED — corrections after gate review 4 REJECT (narrow basis), packet v2.2 commits a171addc7 + 61ff5a09d, reviewed 2026-09-27
produced_on: 2026-09-26/27 (v1.0) / 2026-09-27 (v2.0 corrections) / 2026-09-27 (v2.1 re-review corrections) / 2026-09-27 (v2.2 review-3 corrections) / 2026-09-27 (v2.3 review-4 corrections)
lane: B (the catalog names its producers) — R85, D5 rev. 2.1
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4
builder: Claude (Sonnet), Lane B sub-agent
gate_review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW.md (verdict REJECT; corrections C-1..C-6)
gate_re_review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW2.md (verdict REJECT, narrow; corrections R1-R6 in its §4)
gate_review_3: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW3.md (verdict REJECT, narrow; correction R7 + wording R8 + non-blocking N1/N2 in its §4)
gate_review_4: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REVIEW4.md (verdict REJECT, narrow; B1/B2/B3 + test gap T1 + N3/N4 in its §5)
builder_v2_3: Claude (Opus 5.5), Lane B corrections builder
native_confirmation_requested: B1 — route_evidence_only never counts as coverage is an EXECUTOR application of D5 rev. 2.1's wording, not a recorded native ruling (§2d)
---

# Nikaṣa wave 1 — Lane B report (the catalog names its producers)

**This version (2.3) adds §2d, the corrections after gate review 4 (B1, B2, B3, T, F, N),
and restates §6, §7, §8 item 8 and §12 to match the code as it now stands.** Review 4
(`B_REVIEW4.md`) REJECTED v2.2 narrowly: a route-evidence-only SCU still counted as
covered (B1); 75 fake `derived_from_source_query` producers still passed 182/182, while
§7/§12 wrongly said that was not a coverage bypass and needed the DB (B2); the check stopped
at the first valid producer per SCU, while §2c/§12 said "every producer" (B3); no test
pinned per-SCU binding (T1); the reason classifier matched substrings (F); and one literal
was left in the closure prose (N3). §2d also discloses a commit-attribution incident: most
of this pass's code reached the branch inside Lane A's commit `cbc8b6724`. Everything
below §2d that v2.2 wrote is kept as the record of that pass, with in-place corrections
where v2.2 overclaimed.

**v2.2's lead, kept for the record:** this version (2.2) states only what reproduces as of
the R7/R8/N1/N2 corrections below, layered on top of v2.1's C-1..C-6 and R1–R6. The
original submission (packet_commit
`4e586118d`) was REJECTED at the gate (`B_REVIEW.md`). The v2.0 resubmission (commit
`6a7c38e29`) was REJECTED AGAIN, narrowly (`B_REVIEW2.md`: R1–R6). The v2.1 resubmission
(commit `c5731c54c`) was REJECTED a THIRD time, narrowly (`B_REVIEW3.md`): the reviewer
confirmed R1–R6 all closed by proofs that could have failed, confirmed no regression
(byte-identical re-derivation, identical closure, 25/25 tests), and confirmed no
untouchable file was touched — but found one new coverage bypass (R7): `--check` accepted
any producer whose disposition was `reviewed_output`, `route_evidence_only` or
`derived_from_service_probe` as long as `source_ref` was any non-empty string, so a
fabricated producer on every uncovered SCU made the artifact read 182/182 and PASS. R7
closes that gap by cross-checking every such producer against the snapshot the script
already loads (since R1) [v2.3 correction: at v2.2 this "every" was false — the loop
stopped at the first valid producer per SCU (B_REVIEW4 B3); true since B3, §2d]. R8 restates four places in this report (and one code comment)
that overclaimed what `--check` detects before R7 landed. Every figure in this document
was re-verified against the pipeline as it stands after R7/R8/N1/N2, not carried over from
the v2.1 text — where a v2.1 figure or claim changed, that is stated explicitly.

## 0 — Scope discipline note (read before anything else)

The root `CLAUDECODE_BRIEF.md` in this worktree (`/Users/Dev/madhav-nikasha`) governs a
DIFFERENT, unrelated, still-ACTIVE campaign ("L3 Kāla data-plane elevation", authored
2026-09-20). Per `CLAUDE.md` §C item 0 its `may_touch`/`must_not_touch` would normally
override all other scope guidance for this session. It does not name this Nikaṣa wave-1
task, the D5/R85 provenance work, or any file this lane touches — the branch's own commit
history shows this worktree has in fact been running the Nikaṣa campaign for many
cycles, so the root brief reads as a stale pointer left over from a different
worktree/branch context, not a live constraint on this work. I did not edit it (editing
`CLAUDECODE_BRIEF.md` is itself gated and out of my lane). I proceeded with the explicit,
detailed, native-authorized Lane B assignment (`NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md`)
and, for this corrections pass, the gate's own `B_REVIEW.md`. **Registering this, not
fixing it or the brief file** — a native/executor call on which governing-scope pointer
is live in this worktree is outside my lane.

## 1 — Files touched, and why

| File | Status | Reason |
|---|---|---|
| `platform/scripts/governance/catalog_provenance.py` | modified (across the C-1..C-6, R1/R2/R6 and R7 commits; review-4 code in `cbc8b6724` (swept in, §2d.0), `26a601b58`, `6af57f6d4`, `3ebbe08bf`) | All corrections through review 4, each below. |
| `platform/scripts/governance/__tests__/test_catalog_provenance.py` | modified (same commits, plus the R2/test-only commit; review-4 tests in `cbc8b6724` (swept in) and every §2d commit) | New/rewritten tests per correction, each with recorded mutation evidence; 56 tests. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json` | regenerated | B-1 output, re-derived after every correction. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/CLOSURE_REPORT.md` | regenerated | B-2 output, re-derived after every correction; states the closure computation itself (R6), now interpolated not hardcoded (N2). |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/BUILD_DEPENDENCIES_READER_SCAN.md` | regenerated | B-3 output; now excludes this lane's own wave1/ prose (C-5); 36 files, not 37 (R4). |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REPORT.md` | rewritten (this file) | v2.3, review-4 corrections pass (v2.2 text kept as the record, corrected in place where it overclaimed). |

Not touched: any writer, the orchestrator, `editorial.ts`, `compiler.ts`, the
register/plan/decisions/STATE files, `asset_census.py`, `asset_elevation_tracker.py`,
`00_ARCHITECTURE/control/*.jsonl`, `nikasha_test/harness/**`, `wave1/A_REPORT.md`,
`wave1/a2_t3_proof/**` (Lane A's territory).

## 2 — Corrections after gate review (C-1 … C-6)

Each correction below maps to one commit on `campaign/nikasha-test`, its own test(s), and
a recorded mutation run (the mutation applied, the exact tests that failed under it, then
reverted and reconfirmed green). C-2 and C-4 share one commit because they are the same
underlying code fix (`resolve_segment_text`'s out-of-range honesty) reached from two
different gate-blocking findings; every other correction is its own commit.

| # | commit | what it fixes | test(s) | mutation run |
|---|---|---|---|---|
| C-1 | `a4fef0f7c` | Removed the catch-all NO_DETECTOR fallback in `derive_all`; `--check` now reads the committed `producer_provenance.derived.json` via new `validate_derived_artifact()` against a closed `NO_DETECTOR_REASON_CLASSES` set, instead of re-deriving in memory. **Correction (R5): this closes only ENTRY validity, not SCU coverage — see R1 in §2b.** | `test_producer_output_requirement_with_no_claims_gets_an_exact_reason_not_a_catchall` (its docstring was wrong until R5 fixed it — see §2b), `test_producer_output_claim_with_non_reviewed_disposition_is_carried_through` (renamed in C-5 from the interim test named here in v2.0), `test_classify_no_detector_reason_is_a_closed_set`, `test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry` | **Restoring the catch-all at HEAD leaves 19/19 (now 30/30) green — this is NOT a live guard at HEAD** (the re-review's own finding; v2.0's "1 failed, 12 passed" record was true only at commit `a4fef0f7c` itself, on the interim test that C-5 later rewrote). What DOES guard a restored catch-all at HEAD: its text classifies as `"unclassified"` via `classify_no_detector_reason`, which `test_validate_derived_artifact_fails_on_a_stale_hand_edited_entry` / `test_classify_no_detector_reason_is_a_closed_set` cover. |
| C-2 + C-4 | `6fa514fc5` | `resolve_segment_text` now returns `(text, out_of_range_reason)` distinguishing missing-file / out-of-bounds / genuinely-resolved. New `source_ref_out_of_range` reason class. **Correction (R2): the priority branch that fires when another segment in the same `source_ref` still resolved (the shape behind ALL 7 production outcomes) had no test until R2 — see §2b.** New `compute_segment_resolution_counts()` recounts every source_query SCU's declared pieces bounds-checked. | `test_unresolvable_range_yields_no_detector_with_reason` (rewritten to assert 3 distinct exact classes; covers only the "nothing resolved" branch), `test_compute_segment_resolution_counts_distinguishes_full_partial_none` | Removed the bounds-check guard (`if a < 1 or b > n or a > b: return None, ...`) → 2 failed (both tests above), 12 passed. Reverted; 14 passed. This mutation does NOT exercise the production-load-bearing branch — R2 adds the test that does. |
| C-3 | `91658a6a9` | (a) `one_hop_helper_texts` skips any call match immediately preceded by `def`/`function` — a definition header is not a call. (b)/(c) new `classify_segment_kind()` excludes migration- and writer-path segments from producing relation candidates (they still count toward "resolved" for out-of-range purposes, never toward producers). Producer gained `via_helper` for auditability. **Fact (R5): in production, `ga_dashas`'s removal is done entirely by the writer-kind exclusion — `_idempotency.py` lives under `ga_writers/` — not by the def guard. The def guard is correct but not load-bearing today: all 294 `derived_from_source_query` rows carry `via_helper: null`, so the one-hop follower contributes no production producer at all.** | `test_one_hop_follower_skips_a_definition_header_not_a_call`, `test_migration_segment_is_never_a_producer_source`, `test_writer_segment_input_read_is_never_a_producer_source` | Removed the def-prefix guard → 1 failed, 16 passed (`ga_decoy` reappeared via `via_helper='unrelated_function'`). Removed the segment-kind exclusion → 2 failed, 15 passed (`bg_decoy`/`bg_texts`/`bg_text_index` reappeared). Reverted each; 17 passed. |
| C-5 | `f1e244c09` | New `get_non_reviewed_producer_output_claims()` carries a claim whose disposition is anything other than `reviewed_output` (today: `route_evidence_only` for `ka_kalasutra`) through `derive_all` under its OWN disposition — never dropped, never relabeled. New `WAVE1_DIR` exclusion in the reader scan, alongside the existing `PROVENANCE_DIR` one. | `test_producer_output_claim_with_non_reviewed_disposition_is_carried_through` (renamed/rewritten from C-1's interim test), `test_reader_scan_excludes_its_own_wave1_report_and_review` | Removed the non-reviewed carry-through loop → 1 failed, 16 passed (regressed to `producers=[]`). Removed the `WAVE1_DIR` exclusion → 1 failed, 17 passed (20 synthetic prose lines reappeared as hits). Reverted each; 18 passed. |
| C-6 | `875809a7b` | New `_domain_stem()` + `compute_closure_report`'s `reason_class_and_text()`: a still-outside asset sharing a domain stem with a `relation_unowned_by_registry` table now reports `table_unregistered (<tables>)`, distinct from the generic `no_unit_names_it`. | `test_still_outside_asset_with_a_same_domain_unowned_table_reads_table_unregistered` | Removed the `table_unregistered` branch → 1 failed, 18 passed (`bg_prashna_rules` misreported as the generic reason). Reverted; 19 passed. |

State after C-1..C-6 (before R1/R2): 19/19 tests pass, but the gate re-review (`B_REVIEW2.md`)
found two of those 19 never exercised the load-bearing code — see §2b.

## 2b — Corrections after re-review (R1 … R6)

`B_REVIEW2.md` REJECTED v2.0 on a narrow basis: every headline figure and C-3/C-5/C-6
reproduced under independent re-derivation, but C-1 and C-2/C-4 each had one path with no
test. R1 and R2 are real code + test fixes, each its own commit. R3–R6 are report-accuracy
corrections (per the coordinator's own framing, "report v2.1"); R6 also required a small
code addition (stating the closure computation in `CLOSURE_REPORT.md`) and so carries its
own commit, test and mutation run too. R3, R4 and R5 are prose-only and are folded
directly into §3–§7 below, with no separate commit (nothing executable changed for them).

| # | commit | what it fixes | test(s) | mutation run |
|---|---|---|---|---|
| R1 | `14d9b0125` | `--check` validated only artifact ENTRIES, never SCU coverage: `{"scus": {}}` printed `PASS: all 0 SCUs` and a missing SCU printed `PASS: all 181 SCUs`, both exit 0. New `validate_scu_coverage(payload, snapshot)` compares the artifact's `scus` map against the catalog's own SCU id set (a file read of the snapshot, no DB); `main()`'s `--check` branch runs it before per-entry validation and merges failures. | `test_validate_scu_coverage_detects_missing_and_extra_scus` (direct unit test), `test_check_fails_on_an_empty_artifact_through_the_real_entry_point`, `test_check_fails_when_the_artifact_is_missing_a_catalog_scu_through_the_real_entry_point`, `test_check_fails_when_the_artifact_carries_an_unknown_scu_through_the_real_entry_point` (all three drive the REAL `main(["--check"])` entry point) | Reverting `main()`'s --check branch to skip `validate_scu_coverage` → 3 failed (all three real-entry-point tests), 20 passed. Reverted; 23 passed at that commit (19 from C-1..C-6 + 4 new R1 tests; R2 adds a 24th test in the next commit, R6 a 25th in the one after that). |
| R2 | `0a1f8c30b` | No production code change — the branch at `:707-711` (fires when a migration segment still resolves alongside an out-of-range HANDLER segment; the exact shape of all 7 production `source_ref_out_of_range` outcomes) was already correct, just untested. New fixture-based test reproduces that exact shape. | `test_out_of_range_handler_segment_wins_priority_over_a_still_resolving_migration_segment` | Changing `:707`'s `if oob_reasons:` to `if False:` → 1 failed (this test), 23 passed. Independently re-derived PRODUCTION under the same mutation (scratch driver, DB read-only): `no_detector_reason_counts` collapses to `{'no_contract': 28, 'relation_unowned_by_registry': 28, 'no_relation_in_range': 18, 'derived_kind_no_source_query': 1}` — `source_ref_out_of_range` goes to exactly 0, all 7 folding into `no_relation_in_range` (18 = 11 + 7). Reverted; 24 passed. |
| R6 | `81b34ed85` | `CLOSURE_REPORT.md` stated only the population query, never the closure computation itself. `write_closure_report_md()` now emits a "How this closure is computed" section: the two seed-set definitions, the edge source (`asset_registry.depends_on`), the traversal algorithm, and the equivalent recursive SQL CTE. | `test_write_closure_report_md_states_the_closure_computation` | Removing the new section → 1 failed, 24 passed. Reverted; 25 passed. |

R3, R4, R5 (report-accuracy; folded into §3–§7, no separate commit):

- **R3** — the reason-class transitions are fully reconciled in §3.3 below: the old 16
  splits into 9 (unaffected) + 7 (moved to `source_ref_out_of_range`); the 29-class
  (`relation_unowned_by_registry`) becomes 28 via `29 − 2 + 1`: `chart_snapshot` and
  `judgment_query` LEAVE the 29-class and land in `no_relation_in_range` instead (their
  only previously-matched relation came from an excluded migration segment);
  `query_graha_naisargika_friendship` ENTERS the 29-class (it lost its false
  `bg_dignity_reference` producer and its real, unregistered read took its place). All 11
  current `no_relation_in_range` SCUs are named, and `judgment_query`'s
  classification limit is stated (its handler citations are all `#anchor` shapes that
  never resolve at all — closer to `source_ref_unresolvable_shape` than the message it
  currently reads; not changed in code because the underlying message is still an honest
  description of what the current segment-kind-exclusion logic actually does, and R3 is
  scoped to the report, not a seventh code correction).
- **R4** — "same 37 files" corrected to **36** (§5): the 37th file in v2.0's own scan was
  `wave1/B_REPORT.md` itself, which C-5's `WAVE1_DIR` exclusion now correctly removes.
- **R5** — folded into the C-1 and C-3 rows above (the C-1 mutation record now states it
  held only at `a4fef0f7c`; the C-3 row states the `via_helper`/def-guard facts).

## 2c — Corrections after review 3 (R7, R8, N1, N2)

`B_REVIEW3.md` confirmed R1–R6 all closed (each by a proof that could have failed, re-run
by the reviewer independently), confirmed byte-identical re-derivation and identical
closure (no regression), and confirmed no untouchable file was touched. It REJECTED again
on one new, narrow finding: **R7**, a coverage bypass in `--check` itself.

| # | commit | what it fixes | test(s) | mutation run |
|---|---|---|---|---|
| R7 | `a171addc7` | `--check` accepted any `reviewed_output` / `route_evidence_only` / `derived_from_service_probe` producer whose `source_ref` was any non-empty string — the reviewer replaced all 75 NO_DETECTOR SCUs with a fabricated `{asset_id: "zz_fake", disposition: "route_evidence_only", source_ref: "x"}` and the artifact read 182/182, PASS, exit 0; a fake `reviewed_output` on `get_dignity` (which has no reviewed claim at all) also passed. New `snapshot_producer_output_claim_keys(snapshot)` and `snapshot_service_probe_asset_ids(snapshot)` give `validate_derived_artifact(payload, snapshot)` — now snapshot-aware — the ground truth to check against: a `reviewed_output`/`route_evidence_only` producer must match a snapshot `producer_output_claims` entry `(asset_id, disposition)` for that SCU; a `derived_from_service_probe` producer must match a `kind: service_probe` requirement's `asset_id` on that SCU. `main()` passes the already-loaded snapshot through. `derived_from_source_query` and the coverage check (R1) are unaffected. | `test_check_fails_when_all_no_detector_scus_get_a_fake_route_evidence_only_producer` (probe G2, real `main(["--check"])`, all 75 fakes named), `test_check_fails_when_get_dignity_is_given_a_fake_reviewed_output_producer` (probe G1), `test_check_fails_on_a_service_probe_producer_for_an_unprobed_asset` (probe c), `test_check_passes_on_the_real_committed_artifact_unmodified` (probe d), `test_all_committed_exemption_producers_are_snapshot_backed` (direct count) | Reverting the three snapshot-backing branches to the old "any non-empty `source_ref`" logic → exactly the three fabrication tests fail (3 failed, 27 passed) — the unmodified-artifact test and the count test stay green, because the mutation only matters when a producer ISN'T actually snapshot-backed. Reverted; full suite green again (30 passed). |

**The exemption-producer count, confirmed (R7's own requirement):** the real committed
artifact carries **24** exemption-tier producers — **14** `reviewed_output` + **1**
`route_evidence_only` + **9** `derived_from_service_probe` — and **all 24 are
snapshot-backed, 0 unbacked**, confirmed by `test_all_committed_exemption_producers_are_
snapshot_backed` reading the real artifact and the real snapshot directly (no fixture).
This is exactly the count the gate review's own probe found, and it is why the unmodified
artifact still PASSes under the new, stricter check.

**R8 (wording; no code beyond what R7 already changed):**

- **(a)** §12 item 4 (v2.1) said fixing G would need "per-SCU contract-awareness this
  lane's … script does not currently have" — false, since the script already had
  `get_reviewed_claims()`/`get_non_reviewed_producer_output_claims()` and `--check` already
  loaded the snapshot (since R1). §7 and §12 below now describe R7 as done, not as a
  stated-but-unfixable limit; G is removed from the "not fixed" itemization.
- **(b)** §7 (v2.1) called `--check` a validator "that reads one committed JSON file with
  no DB access" — stale since R1, which added the snapshot file read. §7 below says two
  files: the artifact and the snapshot.
- **(c)** §6 (v2.1) said "a stale/hand-edited entry — all now correctly fail" — true only
  for shape-defective entries before R7; now genuinely true for BOTH shape defects and
  fabricated exemption producers (R7 closes exactly that second class), so §6 below states
  it as accomplished rather than partial. [v2.3 correction (B_REVIEW4 §3 R8c/R8d): only
  partly true at v2.2. A fabricated producer placed beside or before a valid one still
  passed; it fails since B3 (§2d).]
- **(d)** The `main()` `--check` comment (the block just above the artifact-open branch)
  said a hand-edited artifact "must be able to fail this" without qualifying which kind of
  hand-edit — corrected in the R7 commit itself to scope the claim to malformed/
  shape-defective entries and to name R7's snapshot cross-check as the mechanism that
  closes the fabricated-exemption class specifically.

**N1 (non-blocking, fixed):** commit `14d9b0125` had silently deleted
`assert "50-60" in stale[0]` from `test_compute_segment_resolution_counts_distinguishes_
full_partial_none` without mentioning it. Restored in the R7 commit; it passes
unmodified (the underlying function still yields the exact stale-piece string), and the
`M1` bounds-guard mutation still reddens this test via its `(1, 1, 1)` tuple assertion
regardless, so no guard was ever actually lost — this was purely an unexplained,
consequence-free deletion, now undone.

**N2 (non-blocking, fixed):** `CLOSURE_REPORT.md`'s "How this closure is computed"
prose hardcoded `14` / `94` / `127` as string literals instead of reading
`closure['before']['named_producers']` / `closure['after']['named_producers']` /
`closure['population_active_count']`. Fixed in the R7 commit — the prose now interpolates
the same values the closure computation itself produced, so it cannot drift from them if
the catalog changes.

## 2d — Corrections after review 4 (B1, B2, B3, T, F, N)

`B_REVIEW4.md` confirmed R7 closed and the per-SCU binding correct, but REJECTED on three
narrow findings (B1, B2, B3), a missing test (T1) and two non-blocking items (N3, N4).
This section maps each item to its commits, tests and mutation evidence.

### 2d.0 — Commit-attribution incident (read first)

The v2.3 pass started in an earlier session. That session wrote most of the code for
B1, B2, B3, T, F and N, plus 8 tests, into the working tree but did not commit it. Lane A's
commit **`cbc8b6724`** ("Lane A gate correction F5 …") then committed those uncommitted Lane
B files together with its own change:
`catalog_provenance.py` (±312 lines), `test_catalog_provenance.py` (+280), and the three
regenerated provenance artifacts. Nothing was lost, and Lane B never touched Lane A's
files. But this lane's code sits under a hash whose message describes a different lane's
fix, and it was not committed one item at a time as the brief requires.

This pass did **not** rewrite history, because Lane A commits to the same branch
concurrently. Instead:

1. It audited what was swept in. The audit found two real defects that shipped in
   `cbc8b6724`, both fixed below:
   - B1: `derive_all` wrote a route-evidence reason that `--check` then rejected.
   - F: a reviewed claim could be demoted beside derived producers and still pass.
2. It gave each item its own commit carrying whatever was still missing (a code fix, a
   pinning test, or both).
3. It re-ran every item's mutation against the final tree, not against `cbc8b6724`.

The "code landed" column below names where each piece of code actually entered history.
The same-file rule (prompt §2.4) was breached by the staging step of a Lane A commit,
not by any edit. It is recorded here and is not this lane's to fix.

### 2d.1 — Item map

Mutation method, same for every row. `scratchpad/mut/<name>/` mirrors the repo layout: a
copy of `catalog_provenance.py` and its test file, plus symlinks to `00_ARCHITECTURE/` and
`platform/src/` (read-only use). The mutation is applied to the copy. Then
`python3 -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -q`
runs inside the mirror. The real tree is never mutated. Mirror baseline: **56 passed**.
Every figure below is from the final tree (56 tests).

| item | code landed | this pass's commit(s) | tests (through the real `main(["--check"])` unless noted) | mutation → result (final tree) |
|---|---|---|---|---|
| **B1** route evidence never counts as coverage | `cbc8b6724` (`scu_has_covering_producer`; new closed-set class `route_evidence_only_not_a_producer`; `validate` never sets covers for route evidence) | `26a601b58`: fixes a real defect found on resumption. The F2 guard treated ANY snapshot claim as proof a producer belonged, so an honest route-evidence-only SCU failed `--check` even with the reason `derive_all` wrote for it. The class must also agree with the producers present, both ways, and it is now the class token (first). `028872b56`: an isolated test. | `test_check_fails_on_a_route_evidence_only_scu_carrying_no_reason` (isolated); `test_honest_route_evidence_only_scu_round_trips_through_the_real_check`; `test_check_fails_when_a_route_evidence_only_scu_is_relabelled_with_another_class`; `test_check_fails_on_a_route_evidence_reason_with_no_route_evidence_producer`; `test_check_fails_when_temporal_activation_is_cut_to_route_evidence_with_the_honest_reason`; plus `cbc8b6724`'s `…reduced_to_only_its_route_evidence_producer` and `test_derive_all_gives_a_route_evidence_only_producer_an_explicit_no_detector_reason` (derive-level) | gate only (`validate`: route evidence covers) → **2 failed, 54 passed** (isolated + relabel); gate + derive → **4 failed**; a reason excuses only claim-free SCUs (route-evidence claims count as proof) → **2 failed** (round-trip, relabel); drop agreement check → **1 failed**; drop reverse check → **1 failed** |
| **B2** bind each `derived_from_source_query` producer to a same-SCU `source_query` requirement | `cbc8b6724` (`snapshot_source_query_refs`; `source_ref in source_query_refs`; the 75-fake test; the 294-bound count test) | `2ee3e8430`: pins that each failure line names BOTH the SCU and the unbound producer, for all 75. This closes the **citation** half only; a fake table/asset that reuses a real `source_ref` still passes (46 SCUs, §7) | `test_check_fails_when_all_no_detector_scus_get_a_fake_source_query_producer`; `test_all_committed_source_query_producers_are_snapshot_bound` (294/294, direct read) | drop the binding (shape-only, the pre-B2 check) → **2 failed, 54 passed** |
| **B3** check every producer, not the first valid one | `cbc8b6724` (the per-producer loop: any unbound producer fails its SCU, named; the appended-fake test) | `6af57f6d4`: placed-first fake plus a second fake on a derived-tier SCU, both named; module docstring's B-4 line corrected (it still described the pre-R7 gate) | `test_check_fails_when_a_fake_producer_is_appended_beside_a_real_one`; `test_check_fails_when_a_fake_producer_is_placed_first_and_every_fake_is_named` | restore the first-valid short-circuit (unbound ignored, break at first covering) → **4 failed, 52 passed** |
| **T** real claim / real probe on the wrong SCU | `cbc8b6724` (the claim half) | `c43ae5c39`: the probe half (`ka_graha_sancara`, probed only on `call_ephemeris_at_t`, copied to `assess_career`) | `test_check_fails_when_a_real_claim_is_copied_onto_the_wrong_scu`; `test_check_fails_when_a_real_service_probe_is_copied_onto_the_wrong_scu` | **narrow** (only the per-producer binding comparisons global) → **2 failed, 54 passed**, exactly the two wrong-SCU tests. B_REVIEW4 §2.4's own mutation (both lookups global) → **2 failed** (probe test + unmodified-artifact PASS). Under that broad mutation the claim test stays green: the global union also feeds the new presence check (F), which then fails the artifact for a different reason. That is why the narrow mutation is the evidence for T. |
| **F** exact class token; declared producers must be present | `cbc8b6724` (prefix + exact match on the first `": "`; every generated reason reformatted to `NO_DETECTOR — <class>: <detail>`; an F2 guard that fired only when an SCU had no covering producer) | `3ebbe08bf`: split on the first `":"` as the brief says. The F2 guard is replaced by a presence check that subsumes it: every `producer_output_claims` pair and every service-probe asset the snapshot declares for an SCU must be present in the artifact, else fail naming the missing producer. Before this, removing `temporal_activation`'s two reviewed claims while its derived producers kept it "covered" PASSED. | `test_check_fails_on_a_prefixed_reason_whose_class_token_is_not_exact` (7 forged strings); `test_check_fails_on_a_no_detector_reason_containing_a_trigger_substring_but_no_exact_prefix`; `test_classify_splits_on_the_first_colon_and_exact_matches` (unit); `test_check_fails_when_a_reviewed_scus_producers_are_erased_and_replaced_with_a_fake_reason`; `test_check_fails_when_a_reviewed_claim_is_demoted_beside_derived_producers`; `test_all_snapshot_declared_producers_are_present_in_the_committed_artifact` (15/15 + 9/9) | classifier restored verbatim from `a171addc7` (substring) → **9 failed, 47 passed**; drop the presence check → **3 failed** (erased-reviewed, demoted-beside-derived, temporal cut); split on `": "` → **1 failed**. **Stated plainly:** the brief asked that restoring substring matching redden BOTH F cases. It reddens the forged-reason case but not the erased-reviewed case, because that case's reason is well-formed, so no classifier can reject it. The erased case is caught by the presence check (mutation F-b). |
| **N** the `111/127 … 16` literal | `cbc8b6724` (interpolated from `closure[...]`) | `01bf88cd9`: a fixture closure of 5/9 with 3 outside must print **5/9** and **3** | `test_closure_traversal_prose_reads_computed_numbers_not_a_literal` (calls `write_closure_report_md` directly) | restore the literal → **1 failed, 55 passed** |

Artifacts re-derived after the last code change: `320999b75` (§2d.3).

### 2d.2 — Every probe, through the real `main(["--check"])`

Driver: `scratchpad/probe.py`. Each case writes a modified copy of the committed artifact
to scratch, points `cp.DERIVED_OUTPUT_PATH` at it, and calls `cp.main(["--check"])`.

| probe | edit | exit |
|---|---|---|
| (d) | unmodified | **0**, PASS |
| (a) | 75 NO_DETECTOR SCUs → fake `route_evidence_only` | **1**, 75 problems |
| (b) | `get_dignity` → fake `reviewed_output` | **1** |
| E×75 | 75 NO_DETECTOR SCUs → fake `derived_from_source_query` (`no_such_table_xyz`, `nope.ts:1-2`) | **1**, 75 problems (was PASS 182/182) |
| B1 cut | `temporal_activation` → only its `route_evidence_only` producer | **1** |
| B1 cut + honest reason | same, plus an exact-format `route_evidence_only_not_a_producer` reason | **1** |
| B3 appended | fake `reviewed_output` appended to `scu.bodha.mechanism.network` | **1** (was PASS) |
| B3 placed first | the same fake placed first | **1** (was PASS) |
| T claim | real `(bo_yantra_mechanism, reviewed_output)` on `assess_career` | **1** |
| T probe | real `ka_graha_sancara` probe on `assess_career` | **1** |
| F1 | `get_dignity` reason → `"zzz kind: derived zzz"` | **1** (was PASS) |
| F1b | → `"NO_DETECTOR — zzz kind: derived zzz"` | **1** |
| F2 | `scu.bodha.mechanism.network` producers erased, reason `"NO_DETECTOR — no_contract: fabricated"` | **1** (was PASS) |
| F3 | `temporal_activation`'s two `reviewed_output` claims removed, derived producers kept | **1** (was PASS before `3ebbe08bf`) |
| **E residual (OPEN)** | the 46 NO_DETECTOR SCUs that carry a `source_query` requirement → fake `{zz_fake, no_such_table_xyz}` reusing the SCU's **real** `source_ref` | **0, PASS, 153/182** — table existence and asset ownership are DB facts `--check` cannot see (§7, §12 item 4) |

### 2d.3 — Recount (B1's "state the deltas")

Re-derived against production, read-only (`SHOW default_transaction_read_only` = `on`),
with `--derive --closure --reader-scan`. `producer_provenance.derived.json` is
**byte-identical apart from `generated_at`**, and `CLOSURE_REPORT.md` likewise.
`BUILD_DEPENDENCIES_READER_SCAN.md` changed only `generated_at` and 12 self-referential
line numbers (76 hits / 36 files, unchanged).

- **Named: 107/182, delta 0.** B1 moved nothing, because no production SCU has route
  evidence as its only producer. `scu.kala.temporal_activation` carries the one
  route-evidence claim (`ka_kalasutra`) beside two reviewed and several derived producers.
  `route_evidence_only_not_a_producer` = **0**.
- **NO_DETECTOR: 75, delta 0.** `no_contract` 28 · `relation_unowned_by_registry` 28 ·
  `no_relation_in_range` 11 · `source_ref_out_of_range` 7 · `derived_kind_no_source_query`
  1. The reason TEXT did change in `cbc8b6724`: all 75 were reformatted to
  `NO_DETECTOR — <class>: <detail>` for the exact-match classifier. The classes and counts
  did not change.
- **Closure: 63 → 111 of 127, unchanged.** 16 still outside = `no_unit_names_it` 14 +
  `table_unregistered` 2. **111 of 127 did not move.**
- **Bound producers per tier (all 318):**
  - `derived_from_source_query`: **294/294** bound to a same-SCU `source_query` requirement.
  - `reviewed_output`: **14/14** bound to a `producer_output_claims` pair.
  - `route_evidence_only`: **1/1** bound (never covering).
  - `derived_from_service_probe`: **9/9** bound to a same-SCU `service_probe` requirement.
- **Declared producers present:** all 15 `producer_output_claims` pairs and all 9
  service-probe pairs.

### 2d.4 — B1 is an executor application, flagged for native confirmation

D5 rev. 2.1 part 2 says "every catalog unit names the asset(s) that **produce or
part-produce** it". This pass reads route evidence (the handler reads a table the asset
writes) as evidence, not production. So a route-evidence claim is carried and must be
snapshot-bound, but it never counts toward coverage, and an SCU with nothing else reads
`NO_DETECTOR — route_evidence_only_not_a_producer`. **This is the executor's reading of
the ruling's wording, not a recorded native ruling.** It is flagged for native confirmation
at the R85 fold. If the native rules the other way, the change is one predicate
(`scu_has_covering_producer`, plus the matching `covers` line in `validate_derived_artifact`),
and the isolated B1 test states the behaviour to flip. Today it moves no production number
(§2d.3).

### 2d.5 — Test count

38 at the start of this pass: the 30 from v2.2, plus 8 swept in with `cbc8b6724`.
**56** at the end: +4 in B1 (`26a601b58`), +1 in the B1 follow-up (`028872b56`), +1 in
B3, +1 in T, +10 in F (7 of them parametrized cases of one test), +1 in N. The B2 commit
strengthened an existing test and added none. Full governance `__tests__/` directory
(measured after the last commit): 171 passed, 5 skipped, 2 failed. That total includes Lane A's tests,
which change concurrently. The 2 failures are in `test_drift_detector_h35_h38.py`
(`test_f163_current_row_flagged_predecessor_row_is_not`,
`test_h35_critical_when_canonical_artifacts_missing`). **Both fail identically at the
review-4 base `644bf3299` in a clean temporary worktree**, so they pre-date this pass and
are not Lane B's. Not touched.

## 3 — B-1: the derivation (post-corrections)

### 3.1 — Read-only DB verification

```
$ source .../pgenv.sh   # pre-resolved read-only DSN, port 5433
$ psql -Atc "SHOW default_transaction_read_only"
on
```

### 3.2 — Population (R220), unchanged from v1.0

`SELECT count(*) FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE` → **127**.
`dead_flag` is `NULL` on every row today, so the literal `is_active AND NOT dead_flag`
reads **0** (three-valued-logic trap; `dead_flag IS NOT TRUE` is correct and is what
`active_population()` uses throughout). Registered as a finding, not fixed outside this
lane's files.

### 3.3 — `--derive` against production

```
$ python3 platform/scripts/governance/catalog_provenance.py --derive
[B-1] 107/182 SCUs have a named producer -> .../provenance/producer_provenance.derived.json
```

```json
{
  "total_scus": 182,
  "scus_with_producers": 107,
  "scus_no_detector": 75,
  "no_detector_reason_counts": {
    "no_contract": 28,
    "relation_unowned_by_registry": 28,
    "no_relation_in_range": 11,
    "source_ref_out_of_range": 7,
    "derived_kind_no_source_query": 1
  }
}
```

**107, not 108** (v1.0's figure). The one SCU that moved is
`scu.catalog.query_graha_naisargika_friendship`, whose only v1.0 producer
(`bg_dignity_reference`) was a false positive from a migration segment (C-3(b)); it now
correctly reports `NO_DETECTOR — relation_unowned_by_registry` (its handler's actual read,
`bg_graha_naisargika_friendship`, is a real but unregistered table). Every other SCU
affected by C-3 still has ≥1 producer, just fewer/correct ones — the named-SCU count only
moves by the one SCU that lost its sole (wrong) producer.

Reason classes, exactly as C-2/C-4 and C-3 leave them:

- **28 `no_contract`** — no availability_contracts entry at all, no reviewed claim.
  Honest: nothing to derive from.
- **28 `relation_unowned_by_registry`** (the "29-class" from v1.0's own recount, now
  net-adjusted by C-3's fixes — **reconciled exactly (R3): `29 − 2 + 1 = 28`.** The 2
  leaving are `chart_snapshot` and `judgment_query` (§3.3a below, both moved INTO
  `no_relation_in_range` because C-3 excludes migration segments, and their only
  previously-matched relation came from one); the 1 arriving is
  `query_graha_naisargika_friendship` (§3.5, moved IN because its wrongly-matched
  `bg_dignity_reference` producer was removed and its real, unregistered read
  `bg_graha_naisargika_friendship` took its place). 29 − 2 + 1 = 28, confirmed against
  the regenerated artifact) — a real relation name
  was found, exists in `information_schema.tables`, but no `asset_registry` row claims it
  as `target_table`. **27 distinct tables** (not "~20" — v1.0's figure was a rough
  estimate; C-5(iv) computes it exactly by parsing every `relation_unowned_by_registry`
  message: `asset_registry`, `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_graha_dik`,
  `bg_graha_naisargika_friendship`, `bg_motion_state_thresholds`,
  `bg_prashna_fructification_rules`, `bg_prashna_lagna_methods`, `bg_prashna_significators`,
  `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_shashtiamsha_deities`,
  `bg_transit_av_gates`, `bg_transit_moorti`, `bg_transit_vedha`,
  `bg_vastu_direction_remedials`, `bodha_rm_chart_summary`,
  `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`,
  `bodha_rm_pattern_remedies`, `bodha_rm_remedy_prescriptions`, `bodha_triangulation`,
  `brahma_vichara_constants`, `ga_prashna_lagna`, `kala_paddhati_profile`,
  `mimamsa_attribution`, `mimamsa_discoveries`).
- **11 `no_relation_in_range`** (down from 16 in v1.0) + **7 `source_ref_out_of_range`**
  (new class) — v1.0's single "resolved source range(s) contain no relation name" bucket
  of 16 conflated two different causes; C-2/C-4 split it. **Full reconciliation (R3):**
  the old 16 splits **9 (unaffected by any correction) + 7 (moved to
  `source_ref_out_of_range`)**. The 7: `get_aspects` (declared 55-91, file has 86 lines),
  `get_avasthas` (71-100, 91 lines), `get_dignity` (78-108, 104 lines), `get_eclipse_flags`
  (38-62, 60 lines), `get_ashtakavarga`, `get_panchanga`, `get_structural` (each loses its
  one handler segment to an out-of-bounds ref while a migration segment happens to still
  resolve — see R2 in §2b for the branch this depends on). The 9 unaffected:
  `query_mantras`, `query_remedies_by_planet`, `query_remedies_for_chart`,
  `query_tantric_remedies`, `read_remedy` (**5** remedy handlers whose declared range is
  pure input-schema prose with no SQL at all — v1.0's "six" was itself off by one),
  `query_cdlm_summary` (`FROM ${table}` via a `TIER_TABLE` map), `call_dasha_eligibility`
  and `call_priority_ranking` (both: the declared range is comment/prose describing a fix,
  the real query sits elsewhere in the same file — an annotation gap, not a derivation
  bug), and `get_vichara` (declared range is parameter-building JS with no `FROM`/`SELECT`
  in it — same annotation-gap class). **Current 11 = these same 9, plus 2 NEW arrivals**
  from the 29-class once C-3 excluded migration segments: `chart_snapshot` (its only
  previously-matched relation, `charts`, came from migration `002_ganita_divisionals.sql`,
  now excluded; its handler range `get_chart_snapshot.ts:205-215` is itself SQL-free
  post-processing logic) and `judgment_query` (below).
  - **`judgment_query`'s classification is a stated limit, not a fix (R3):** ALL of this
    SCU's handler-kind citations (`register_d9_judgment.ts#judgmentQueryCapability.handler`,
    `reading_checklist.ts#getOperativeVargaConstants`) are `#anchor` shapes that never
    resolve to a numeric range at all — no handler segment for this SCU has EVER been
    attempted, let alone found empty. Its only resolving segments are two migration
    pieces, both excluded by C-3. The message it reads
    ("resolved source range(s) contain no relation name in any handler-kind segment")
    therefore classifies as `no_relation_in_range`, but the more honest class for its
    handler citations specifically would be `source_ref_unresolvable_shape`. Left
    unchanged in code (R3 is a report-accuracy item, not a seventh correction) — stated
    here as the exact limit it is.
- **1 `derived_kind_no_source_query`** — `scu.catalog.query_current_transit_snapshot`,
  correctly routed by spec.

### 3.4 — `source_ref` resolution recount (C-4, replaces v1.0's 125/11/1)

v1.0 reported "125 fully resolved / 11 partial" under the definition "file exists, range
in-bounds" — but that 125 was actually the SHAPE-VALID count (137 − 12 non-numeric-range
citations), never bounds-checked. `compute_segment_resolution_counts()` now resolves
EVERY declared `|`-joined piece of every `source_query` SCU's `source_ref` and checks
bounds on each:

```
113 full (every declared piece is a real, in-bounds range)
 23 partial (some pieces in-bounds, at least one stale/OOB or non-numeric)
  1 none (scu.catalog.query_classical_texts — both its pieces are #anchor/:name citations)
```

**12 SCUs carry at least one stale (out-of-bounds) or missing numeric piece** — registered
here as an outside-scope finding for whoever owns `source_query_availability.ts`'s
annotations; none of these 12 refs were edited by this lane:

`get_ashtakavarga`, `get_aspects`, `get_avasthas`, `get_database_schema`, `get_dignity`,
`get_eclipse_flags`, `get_medical_indications`, `get_panchanga`, `get_structural`,
`get_vastu_directions`, `query_contradictions`, `query_question_lenses`.

(7 of these — `get_ashtakavarga`, `get_aspects`, `get_avasthas`, `get_dignity`,
`get_eclipse_flags`, `get_panchanga`, `get_structural` — are the ones whose stale segment
actually changes their NO_DETECTOR reason class, per §3.3; the other 5 have a working
segment elsewhere in the same `source_ref` and are unaffected in outcome, only in this
stricter count.)

### 3.5 — The 4 false producers (C-3), and the closure impact

| SCU | wrong producer (v1.0) | cause | now |
|---|---|---|---|
| `scu.catalog.get_ayurdaya` | `ga_dashas` / `chart_dashas` | C-3(a): one-hop follower matched `def replace_prior_chart_dashas(` (a definition header, the LAST line of the `_idempotency.py:54-78` range) as a call, then ingested that function's body | producer removed; `ga_ayurdaya`/`chart_facts` (the handler's real query) unaffected |
| `scu.catalog.get_sensitive_degrees` | `ga_dashas` / `chart_dashas` | same cause, same shared helper file | producer removed; the 7 real `chart_facts` co-producers unaffected |
| `scu.catalog.query_compendium_index` | `bg_texts`/`bg_text_index` / `classical_text_chunks` | C-3(c): the writer's own INPUT read (`bg_compendium_index.py` reading `classical_text_chunks` to build its index) was taken as the SCU's query | producers removed; `bg_compendium_index`/`brahma_compendium_index` (the handler's real query) unaffected |
| `scu.catalog.query_graha_naisargika_friendship` | `bg_dignity_reference` | C-3(b): migration 606's own unrelated integrity-check SQL was taken as the SCU's query | now correctly `NO_DETECTOR — relation_unowned_by_registry` (the handler's real read, `bg_graha_naisargika_friendship`, is unregistered) |

**Closure headline does not move**: `bg_dignity_reference` was never load-bearing for the
111 figure (reached via another path already) — confirmed by re-running `--closure` after
the fix and getting the same 111/127.

An incidental, positive side effect noticed while verifying: `scu.catalog.get_chart_header`
previously reported ALL 7 `ga_*` co-producers of `chart_facts` as `shared: true`, because
`query_pins` extraction was reading pin literals out of excluded migration segments too,
diluting the real pin. With migration/writer segments excluded from literal extraction,
the handler's own `fact_category = 'graha_position'` pin now correctly narrows this SCU to
its single real owner, `ga_positions` (plus the equally-real `ga_dashas`/`chart_dashas`
producer from the SAME handler's own `chart_dashas` query — a genuine read, not a false
positive, verified by reading `chart_header.ts:72-94` directly).

## 4 — B-2: the necessity closure

```
$ python3 platform/scripts/governance/catalog_provenance.py --closure
[B-2] necessary before=63, after=111 (of 127) -> .../provenance/CLOSURE_REPORT.md
```

**Before** (14 reviewed-seed assets — unchanged from v1.0 and from the D5 ruling's own
baseline): **63/127** necessary, 64 not reachable, split 21 brahmagyan / 4 bodha / 6
ganita / 9 kala / **24** phala+mimamsa (9 phala + 15 mimamsa — the ruling's own stated "23"
undercounts by one; the ruling's total of 64 is only internally consistent with 24, not
23; registered, not corrected in `DECISIONS_RECOMMENDATIONS_v2_0.md`).

**After** (all reviewed ∪ derived ∪ route-evidence producer assets): **94 distinct named
assets** (not 95 — one fewer than v1.0's figure, because `bg_dignity_reference` no longer
appears anywhere in the seed set once C-3 removed its one false-positive citation) →
**111/127** necessary, **16** not reachable. This is unchanged from v1.0 — the closure
headline does not move on any of the six corrections.

The 16 still outside, now split by C-6's two distinct reason classes:

| reason class | count | assets |
|---|---|---|
| `table_unregistered` | 2 | `bg_prashna_rules`, `ga_prashna` — both share the `prashna` domain stem with 6 unregistered tables (`bg_prashna_fructification_rules`, `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `ga_prashna_lagna`) that real catalog SCUs (`query_prashna_*`, `get_prashna_lagna`) DO query. These two assets likely DO produce a unit; the registry, not the catalog, has the gap. Under D5 part 3 this is a merge/retire candidate, never a true closure failure. Honest limit: the stem heuristic correlates by shared domain word, not by parsing each writer's actual `INSERT`/`COPY` targets, so it lists all 6 same-domain tables as candidates for BOTH assets rather than asserting a precise 1:1 assignment. |
| `no_unit_names_it` | 14 | `bg_cohort`, `bg_concordance`, `bg_gochara_arcs`, `bg_gochara_citation_resolution`, `bg_vidhi_floors`, `bg_vidhi_primitives`, `bo_grounding`, `ka_kshetra`, `ka_tulana`, `lel_events`, `mi_bhara`, `mi_sankalpa`, `mi_seva`, `mi_vistara` |

**Phala, corrected (C-5(v)):** zero phala assets are outside the closure — but NOT
"chiefly via service_probe-derived chains reaching L4" as v1.0 wrongly stated. Verified
directly from the regenerated artifact: all 9 `ph_*` assets
(`ph_muhurta`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`, `ph_pratikara`,
`ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`) are **direct**
`derived_from_source_query` producers of some catalog SCU. No service_probe chain is
involved, and an L0 service probe could not pull an L4 asset into the seed set that way in
any case (L4 depends on lower layers, not the reverse).

**The yoga SCU's timing route (C-5(v)):** `scu.kala.temporal_activation`'s `source_query`
requirement resolves to `kala_activation` (via `ka_kalasutra`), **not**
`kala_gochara_windows` as v1.0 stated. Verified directly from the regenerated artifact —
the producer entry's `table` field reads `kala_activation`. `scu.yoga.firing_and_cancellation`
(the SCU that carries BOTH the `producer_output` claim for `ga_yoga` and, separately, a
`source_query` route through `bo_laksana`/`ka_kalasutra`) is unaffected by this correction;
only the table name in the narrative was wrong.

## 5 — B-3: `build_dependencies` reader scan

```
$ python3 platform/scripts/governance/catalog_provenance.py --reader-scan
[B-3] build_dependencies reader scan: 76 hits -> .../provenance/BUILD_DEPENDENCIES_READER_SCAN.md
```

**76, stable (C-5(iv))** — not 80, and not the 81 the gate review found on re-running
v1.0's script. v1.0 already excluded `PROVENANCE_DIR` (this lane's own generated JSON/MD
output) after finding a 67→144 self-referential runaway; what it did NOT exclude was
`wave1/` (this lane's own `B_REPORT.md`/`B_REVIEW.md`), which discuss
"build_dependencies" at length while describing the scan itself — a real, if
non-runaway, source of drift (observed 80→81 the moment `B_REPORT.md` gained one line).
`WAVE1_DIR` is now excluded the same way `PROVENANCE_DIR` is, and the figure is now stable
across repeated runs (confirmed twice consecutively).

**36 files, not 37 (R4)** — v2.0 wrongly carried over v1.0's "37" file count. The 37th
file in the pre-`WAVE1_DIR`-exclusion scan was `wave1/B_REPORT.md` itself; C-5's
`WAVE1_DIR` exclusion correctly removes it, so the count is now 36
(`grep -c '^## \`' BUILD_DEPENDENCIES_READER_SCAN.md` → 36). Same conclusion as v1.0: the only LIVE code that actually queries the
table is `platform/python-sidecar/pipeline/dispatcher.py` (`_load_dep_graph()` /
`rebuild_asset()`), and `pipeline.dispatcher` is imported nowhere else in the repo —
observed fact, not a recommendation to drop anything (B-3 is read-only; the table is
untouched). Everything else is comments on already-repointed TS routes, historical
migrations, governance docs, and one unapplied teardown script.

## 6 — B-4: `--check`

```
$ python3 platform/scripts/governance/catalog_provenance.py --check
[B-4] --check PASS: all 182 SCUs in .../provenance/producer_provenance.derived.json have every producer bound to the snapshot (derived_from_source_query to a same-SCU source_query requirement's source_ref; reviewed_output/route_evidence_only to a producer_output_claims entry; derived_from_service_probe to a service_probe requirement), at least one NON-route_evidence_only covering producer where any producers exist, or a no_detector reason exact-matching the closed reason set — and the artifact's SCU coverage matches the catalog exactly.
```

**What `--check` does, as of v2.3 (C-1 + R1 + R7 + review 4).** `--check` reads TWO files:
the committed artifact and the catalog snapshot. It never re-derives and never touches the
database.

- **Coverage (R1).** `validate_scu_coverage()` compares the artifact's `scus` map with the
  catalog's own SCU id set. It names any SCU missing from the artifact and any extra SCU no
  longer in the catalog.
- **Entry validity (`validate_derived_artifact(payload, snapshot)`).** For every SCU
  present, **every producer of every tier** is checked (B3; before review 4 the loop
  stopped at the first valid producer). A producer counts as bound only if what the
  snapshot declares for **that same SCU** backs it:
  - `derived_from_source_query`: a non-null `table`, a range-shaped `source_ref`, AND that
    exact `source_ref` is one this SCU's own `kind: source_query` requirement declares
    (B2; before review 4 shape alone was enough).
  - `reviewed_output` / `route_evidence_only`: a non-empty `source_ref` AND a matching
    `(asset_id, disposition)` pair in this SCU's `producer_output_claims` (R7).
  - `derived_from_service_probe`: a non-empty `source_ref` AND `asset_id` named by this
    SCU's own `kind: service_probe` requirement (R7).

  Any unbound producer fails its SCU, and the failure line names both the SCU and the
  producer. This holds whether the fake is beside the real producers, before them, or in
  place of them.
- **Declared producers present (F).** Every `producer_output_claims` pair and every
  service-probe asset the snapshot declares for an SCU must be present among that SCU's
  producers. Erasing or demoting one fails, naming it, whatever reason string sits
  beside it.
- **Coverage per SCU.** An SCU needs ≥1 **covering** producer. `route_evidence_only` is
  never covering (B1, §2d.4). Without one, it needs a `no_detector` reason whose class
  token, the text after `NO_DETECTOR — ` and before the first `:`, **exact-matches** the
  closed `NO_DETECTOR_REASON_CLASSES` set (F; before review 4 the classifier matched
  substrings).
- **Route-evidence agreement (B1).** The class `route_evidence_only_not_a_producer` is
  accepted only when a bound route-evidence producer is present. An SCU whose only
  producers are bound route evidence must carry exactly that class.

The gate's own constructed cases all fail: an empty artifact, a missing SCU, an extra SCU,
a stale entry, and every forgery probe in §2d.2. The unmodified artifact passes.

```
$ python3 -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -q
56 passed
```

Full test list and per-correction mutation evidence: §2, §2b, §2c and §2d above.

## 7 — Honest limits (every reason class, with counts) — post-corrections

Of 182 SCUs: **107 have a named producer** (12 reviewed SCUs / 14 reviewed assets + **95**
derived-only SCUs / **80** derived-only assets = **94** distinct assets total, not the
v1.0 figures of "14+94=108 SCUs" / "14+81=95 assets" — both corrected downward by exactly
the one false-producer SCU C-3 removed). **75 are `NO_DETECTOR`** (up from 74 — the same
one SCU), broken down exactly as in §3.3.

**The `producer_output` requirement count is 11 SCUs, not 12** (C-5(iv)) — 12 is the
requirement COUNT (`scu.finance.prosperity_assessment` carries two, one per co-producer),
11 is the distinct-SCU count.

**"15 assets" is not an off-by-one (C-5(i)) — both 14 and 15 are correct, for different
sets.** `{c['asset_id'] for scu in scus for c in scu['producer_output_claims']}` (every
claim, any disposition) → **15**, because `ka_kalasutra` enters via
`scu.kala.temporal_activation`'s `route_evidence_only` claim. Filtering to
`disposition == 'reviewed_output'` only → **14**. The D5 ruling counted claims ("naming 15
assets"); v1.0 counted only reviewed claims and then wrongly called the ruling's 15 an
off-by-one. **v1.0's "the 63/127 calibration corroborates 14" claim is retracted**: seeding
the closure with the 15-asset set (adding `ka_kalasutra`) also gives 63, because
`ka_kalasutra` is already upstream of `ka_yojaka`/`ka_bhavishya_lekha` — the baseline
cannot distinguish 14 from 15 seeds, so it corroborates neither over the other.

**A third disposition, `derived_from_service_probe` (C-5(ii)):** 9 rows, `table: null`,
an anchor (`service_probe:...` or the requirement's own `source_ref`) instead of a numeric
range. These are read directly off a `kind: service_probe` requirement's own `asset_id` —
no SQL parsing attempted or needed. `validate_derived_artifact` treats this disposition as
a declared exemption from the table+range requirement, same as `reviewed_output` and
`route_evidence_only` — and, since R7, all three are exempted from the table+range shape
check ONLY, not from verification altogether: each must still match something the
snapshot itself declares (§6).

**The `route_evidence_only` claim is carried, not dropped (C-5(iii)):**
`scu.kala.temporal_activation` now carries `ka_kalasutra` twice in its `producers[]` — once
via the carried `route_evidence_only` claim (evidence: "query_temporal_activation handler
reads kala_activation") and once via the independently-derived `derived_from_source_query`
route (table `kala_activation`) — both correct at once, neither overwrites the other.

**Calibration set:** unchanged in substance from v1.0 — 5 of 12 reviewed SCUs are directly
comparable (carry a `source_query` contract); 3 agree (2 as an honest superset via a
correctly-flagged shared table), 2 "disagree" (one genuinely unresolvable, one covering a
different producing route than the reviewed claim — both correct, nothing lost in the
merged output).

**`--check`'s limits as of v2.3 — restated after review 4.** v2.2 was wrong about E and
understated F (B_REVIEW4 B2, N4). Its closing claim that "neither is a coverage bypass"
was false for E. What is true now:

- **G — DONE (R7).** Every exemption-tier producer must match what the snapshot declares
  for that SCU.
- **E, citation half — DONE (B2).** Before review 4, E was a coverage bypass the same size
  as G: 75 fake `derived_from_source_query` producers (`no_such_table_xyz`, `nope.ts:1-2`)
  read **PASS, 182/182**. Now every such producer's `source_ref` must equal a same-SCU
  `kind: source_query` requirement's `source_ref`, so that probe exits 1. v2.2's "fixing E
  needs a DB round-trip" was false for this half: the snapshot alone decides it.
- **E, table/asset half — STILL OPEN, and still a coverage bypass. Measured, not
  estimated.** `--check` cannot tell whether a producer's `table` exists, or whether its
  `asset_id` owns that table (`asset_registry.target_table`); both are database facts. 46
  of the 75 NO_DETECTOR SCUs carry a `source_query` requirement: `relation_unowned_by_registry`
  28, `no_relation_in_range` 11, `source_ref_out_of_range` 7. Giving each of the 46 a fake
  producer (`zz_fake`, `no_such_table_xyz`) that reuses the SCU's **real** `source_ref`
  reads **PASS, exit 0, 153/182**. Closing it means either:
  - a DB-backed check of ownership and existence, which is a design change to `--check`
    (C-1 fixed it as a file-only gate); or
  - partly, without the DB, re-parsing the cited range and requiring `table` to be one of
    its relation names. That would catch the 18 whose ranges have no usable relation
    (11 + 7), but not the 28 whose ranges do name real, unowned tables.

  Neither was done in this pass (§12 item 4).
- **F — classifier DONE; one residual stated.** The class token is exact-matched: the
  text after `NO_DETECTOR — ` and before the first `:` must be a closed-set member, and a
  class name elsewhere in the string counts for nothing. Every producer the snapshot
  declares must be present. So a false reason can **no longer demote or erase** a declared
  producer (v2.2's "only mislabels" was an understatement, N4; F2/F3 in §2d.2 now fail).
  **Residual:** where the snapshot declares no claim or probe for an SCU, an exact-format,
  closed-set but **wrong** class still passes. Example: `no_contract` on an SCU that does
  have requirements. That mislabels an uncovered SCU; it does not create coverage.
  Checking a class against the SCU's own contract (e.g. `no_contract` ⇒ no requirements)
  is feasible from the snapshot but was not in review 4's list. It is stated here, not
  done.
- **Route evidence — DONE (B1).** An SCU whose only producers are `route_evidence_only`
  is not covered. It reads `NO_DETECTOR — route_evidence_only_not_a_producer`, which is
  accepted only when that is literally true. This is an executor application of D5 rev.
  2.1's wording, flagged for native confirmation (§2d.4). It is 0 SCUs in production
  today.

## 8 — Findings outside scope (registered, not fixed)

1. `dead_flag` is `NULL` on every production row; `is_active AND NOT dead_flag` silently
   reads 0 rows. `dead_flag IS NOT TRUE` is correct. (§3.2)
2. The D5 ruling's per-layer "23 Phala/Mīmāṃsā" sums to 24 by direct count (9 phala + 15
   mimamsa); the ruling's own total of 64 is internally consistent only with 24. (§4)
3. 12 SCUs carry a stale (out-of-bounds) or non-numeric `source_ref` piece — named
   individually in §3.4 — a `source_query_availability.ts` annotation-drift finding, not a
   derivation bug. None of the 12 refs were edited by this lane.
4. **27** real, queried tables have no owning `asset_registry` row at all (§3.3's full
   list) — a genuine registry-coverage gap. Two of them (the `bg_prashna_*` family and
   `ga_prashna_lagna`) are flagged `table_unregistered` in the closure report (§4) because
   they share a domain stem with a still-outside asset; the other 25 have no such
   correlated asset and are registered here as a flat list.
5. `pipeline/dispatcher.py` (the one live reader of `build_dependencies`) is imported
   nowhere else in the repo — may itself be dead code, independent of the
   `build_dependencies` retirement question.
6. The `table_unregistered` correlation (C-6) is a same-domain-stem heuristic, not a
   parse of each writer's actual `INSERT`/`COPY` targets — it lists candidate tables, not
   a precise 1:1 assignment. Stated in §4, not hidden.
7. `producer_provenance.derived.json` records `via_helper` (C-3) but does not separately
   report an aggregate "N producers found via helper vs. directly" count — a future pass
   could add this if the provenance is valuable at that granularity. All 294
   `derived_from_source_query` rows carry `via_helper: null` today (§7's C-3 note).
8. `--check`'s remaining limits (§7, restated in v2.3). **E, table/asset half:** a
   producer's table existence and asset ownership are DB facts `--check` cannot see. This
   is still a coverage bypass: 46 SCUs, **153/182 PASS** when measured. **F residual:** a
   wrong but exact-format class passes on an SCU where the snapshot declares no claim or
   probe; it mislabels but cannot demote a declared producer. G, E's citation half (B2),
   F's classifier and demotion (F), and route-evidence coverage (B1) are CLOSED.
9. `judgment_query`'s `no_relation_in_range` classification is a stated limit (R3, §3.3):
   its handler citations are all unresolvable-shape anchors, so the more honest class
   would be `source_ref_unresolvable_shape`. Not changed in code.

None of these were fixed silently; all are visible in this report and the generated
artifacts.

## 9 — Stop conditions

Not triggered, in either the original pass or this corrections pass. No writer,
orchestrator, or sealed-tier change was needed; no production write occurred; no
migration was applied. §0 (the stale `CLAUDECODE_BRIEF.md` pointer) was registered rather
than treated as a stop condition, per the reasoning given there.

## 10 — Not in this lane (confirmed untouched)

`compiler.ts` was not read or modified. `editorial.ts` was read only, never edited. Lane
A's files (`asset_census.py`, `asset_elevation_tracker.py`, `00_ARCHITECTURE/control/
*.jsonl`, `nikasha_test/harness/**`, `wave1/A_REPORT.md`, `wave1/a2_t3_proof/**`) were
neither staged nor reverted at any point in this corrections pass. v2.3: the same holds for the review-4
pass. Every commit used explicit Lane B paths (`git log --name-only a171addc7..HEAD` for the
§2d commits lists only `catalog_provenance.py`, its test file, `nikasha_test/provenance/**`
and this report). The reverse did happen: Lane A's `cbc8b6724` staged Lane B's uncommitted
files (§2d.0).

## 11 — Governance checks (constraint §2.7)

Re-run for v2.3 after the last code commit:

```
$ python3 platform/scripts/governance/manifest_fingerprint.py --check
fingerprint observed: f484f581767ad641
MATCH
```
No rotation needed: `catalog_provenance.py` and its test file are not registered in
`CAPABILITY_MANIFEST.json`.

```
$ source .../pgenv.sh      # read-only; SHOW default_transaction_read_only = on
$ python3 platform/scripts/governance/drift_detector.py
drift_detector: 1 findings; exit=3
```
Exit **3** (sanctioned: "exit 0 or 3 only"). The one finding is unchanged since v1.0:
`a3_category_not_yet_populated`, LOW severity (73 `CHART_FACTS_SCHEMA.json` categories not
yet written to `chart_facts`). Nothing this lane touched can cause it.

## 12 — What is NOT done

Restated for v2.3 (review 4 found v2.2's items 4 and 6 false). The exact list:

1. **`compiler.ts` wiring is out of scope, by the wave1 prompt's own design.** Not
   touched.
2. **`editorial.ts` was read only, never edited.**
3. **The 12 stale `source_ref` annotations (§3.4) are registered, not fixed.** They are not
   this lane's file.
4. **`--check` limit E, table/asset half — open, and still a coverage bypass (§7).**
   B2 bound every `derived_from_source_query` citation to a same-SCU `source_query`
   requirement; 294/294 committed producers are bound. v2.2's "fixing E would need a DB
   round-trip" was false for that half, and it is fixed. What only the database can
   answer is whether the producer's `table` exists and whether its `asset_id` owns that
   table. A fake producer that reuses an SCU's real `source_ref` still passes. Measured:
   46 SCUs, PASS at 153/182. Not closed, because that needs a DB-backed `--check`, a
   design change to C-1's file-only gate that no review asked for. A file-only re-parse
   would close 18 of the 46 at most.
5. **`--check` limit F, residual (§7).** An exact-format, closed-set but wrong class
   passes on an SCU where the snapshot declares no claim or probe. Checking the class
   against the SCU's own contract is feasible from the snapshot but was not asked for.
6. **`judgment_query`'s classification limit (§3.3, §8 item 9) is stated, not fixed.**
7. **B1 awaits native confirmation (§2d.4).** "Route evidence never counts as coverage" is
   the executor's application of D5 rev. 2.1's wording, not a recorded ruling. v2.2's
   item 6 said this gap was left "per the gate's own framing". That was false (B_REVIEW4
   B1), and the gap is now closed in code.
8. **One-commit-per-item was not achieved for the code (§2d.0).** Most review-4 code
   entered history inside Lane A's `cbc8b6724`, and history was not rewritten. Each item
   has its own commit for what was still missing, plus mutation evidence re-run on the
   final tree.

Everything else is committed, each item with a test that fails without it and recorded
mutation evidence (§2, §2b, §2c, §2d): C-1..C-6, R1/R2/R6, R7, and B1/B2 (citation
half)/B3/T/F/N. The full pipeline (`--derive --closure --reader-scan`, then `--check`, then
the test suite) was re-run against production after the last correction.
