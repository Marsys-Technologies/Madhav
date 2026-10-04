---
artifact: REPIN_TOOL_CODEX_PASS_PACKET
version: "1.0"
status: READY for the next Codex pass (steward 2026-10-04: prepare the improved re-pin tool Codex pass). Review request only; authorizes nothing.
date: 2026-10-04
author: Stream B (Śāstra), session madhav-8b
tool: platform/python-sidecar/scripts/gochara/repin_dasha_contract.py on branch pravaha/b6-am10-repin-tool-declared-shape
changelog:
  - "1.0 (2026-10-04): first version."
---

# Codex pass packet — AM-10 re-pin tool, head c383c2895

## 1. What to review
- **Head:** `c383c2895e8105767b5b16f2cbee84093698e043` (branch `pravaha/b6-am10-repin-tool-declared-shape`, pushed). **Delta since the head Codex last saw (v1.8 reviewed `99801a7fc`; the tool fixes answering v1.8 are in `4061d3608`):** `4061d3608` = the four v1.8 P1 fixes; `c383c2895` = **tests only** (see §3). The tool file is byte-identical between `4061d3608` and `c383c2895`.
- **PR 2903 (`5a46c9c97`) is not touched.** This branch is the improved tool; it becomes the tool of record only after a Codex APPROVE.
- **Purpose now:** the SETTLED-1 pin was applied by hand and reviewed (`decisions/DASHA_REPIN_SETTLED1_20261004.md`). The tool is the instrument for the NEXT re-pin (e.g. SETTLED-2 or a later S-L1) — nothing in this review gates the campaign.

## 2. The four v1.8 P1 blockers and where each is closed
| v1.8 | fix | regression (refusal before any write) |
|---|---|---|
| 1 evidence output collides with a source / input / destination | `io_collision_problems` runs in the validation phase | `test_v18_1_an_evidence_output_that_is_a_source_or_an_input_or_another_output_is_refused_before_any_write` |
| 2 existing non-identical generated test overwritten | write-plan validation refuses an existing destination that is not byte-identical, before any report | `test_v18_2_an_existing_nonidentical_generated_test_is_refused_before_anything_is_reported_or_written` |
| 3 natal longitude `-1e-9999` underflow passes the range check | exact `Decimal` range check, strict ASCII decimal text, a JSON float that underflowed to −0.0 refused | `test_v18_3_*` (three tests) |
| 4 non-UUID chart id accepted (CLI, W0, capture) | `chart_id_problem` at the CLI, W0 import and capture validation | `test_v18_4_chart_ids_are_canonical_uuid_text_on_the_cli_in_w0_and_in_capture_validation` |

The whole surface (inputs I1–I10, outputs, writes) is in `design/REPIN_TOOL_THREAT_LIST_v1_0.md`, written before this pass so the review can check completeness, not only the last counterexamples. **Please name any input or write NOT on that list.**

## 3. What `c383c2895` changed, and why it matters to the review
Running the tool's tests on a tree of **current main + the tool** (the main the tool will actually merge into; the branch base is 149 commits behind main, `git merge-tree` reports a clean merge) found **one failing test of 272**: the apply tests used the SETTLED-1 pinned instants (`2013-01-14T09:13:56Z`, `2014-01-11T14:11:56Z`) as their invented "new build" values; after the manual re-pin those ARE the live reference instants, so a test asserting "the old instant is gone, the new one is present" stopped testing a rewrite. Fix: the fixture "new" literals are now `2013-01-14T11:13:56` / `2014-01-11T16:11:56` (+2 h, in every spelling the tests use: `Z`, `+00:00`, non-offset, fractional), and `test_the_fixtures_new_instants_do_not_collide_with_the_live_pin` fails loudly if a future pin ever equals them. **No tool code changed.** Tests probing the tool's behaviour were not weakened: the same assertions run on shifted literals.

## 4. Evidence (run by Stream B, 2026-10-04)
- Main + tool tree: **270 passed, 2 skipped** (the two DB-backed tests need `GOCHARA_A51_TEST_DATABASE_URL`); with a disposable local PostgreSQL the DB-backed subset (**21 tests**, including both) passed. The database was stopped afterwards.
- Branch worktree (old base): 269 passed, 2 skipped before `c383c2895`.
- Nothing here touched production; no capture was taken; the gates are unchanged (ST-SL1-HOLD logic, `--apply` needs `--hold-lifted`).

## 5. Questions for Codex
1. Is there any input, output or write path that is not in the threat list, or one whose "must hold" is weaker than the code?
2. Does the all-or-restore apply (`write_all_or_restore`) leave any state where a partial write is reported CLEAN or where the restore itself can fail silently?
3. Is the tool, at this head, fit to become the tool of record (merge into the PR 2903 branch)? Name any blocker as a counterexample the way v1.7/v1.8 did, so a regression can be written first.
