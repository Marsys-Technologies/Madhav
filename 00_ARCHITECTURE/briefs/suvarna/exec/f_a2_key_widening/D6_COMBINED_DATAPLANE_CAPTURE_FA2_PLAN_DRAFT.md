---
artifact: D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN
version: "0.9-DRAFT"
status: DRAFT_NOT_FROZEN (hunk set not complete: patch B and patch C are candidates awaiting Strategic Suvarna review; gate pins TBD; no plan hash is frozen; nothing is applied)
date: 2026-10-02
lane: suvarna/land/TI-d6-dataplane-capture-fa2-001 (cut from #2858 head e81ed714e)
decision: owner N-84, option A (data-plane capture repair) + SS L1 decision Q-L1-01 (F-A2 ga_vargas key widening)
execution: NONE against any real system. Production was read only as suvarna_reader (catalog text, md5, ACL, attestation digests); every test ran on disposable local PostgreSQL 15 and 17 clusters with production-shaped roles, owners and ACLs and a fake administrator.
frozen_by: not frozen. SS decision (i): the plan hash, the plan file and the independent review happen ONCE, on the complete hunk set, after the 19-lane rehearsal has finished all lanes.
changelog:
  - "0.9-DRAFT (2026-10-02): first combined draft. Machinery is data-driven (a list of function hunks; EXPECTED_DIFF, the plan text, the generic rollback and the re-attestation are generated from it). Carries F-A2 (index, trigger, one function hunk) and option A (H1, H2, H3a, H3b) only. Replaces the predecessor's uncommitted work; gate fixture refreshed to GATE_V2 revision 3 (PR #2938 head 7f0db55c3), commit_state_unknown and the under-test refusal added to the executor."
---

# D6 owner-path plan (combined): L1 data-plane capture repair (option A, N-84) plus the F-A2 `ga_vargas` key widening

## 0. One-page summary for the owner (plain language)

**What and why.** Madhav keeps a protected, append-only history of every row the chart-building programs write. Two small defects in the machinery that records that history stop the canonical chart from being rebuilt cleanly:

1. **The recorder cannot store some rows the programs legitimately write**: facts with no value at all (honestly "floored" or "unavailable"), and facts carrying more than one kind of value (a number and a note, say). It refuses both, and the whole part of the build aborts. This is the repair you approved as **option A (N-84)**: the recorder stores such rows honestly. For a fact with several kinds of value it keeps **one** in the summary table (number, then text, then structured detail), records which it kept and which it set aside, and the **complete, untouched row stays in the history table**. Nothing is lost.
2. **The `ga_vargas` uniqueness rule is too coarse (F-A2).** It silently drops about 14,200 rows per chart. The rule is widened by one column and the recorder is told about it.

**What changes in the production database.** Rules and definitions only, never chart data: one stored procedure (the recorder) is replaced by a copy that differs by five small named edits; one uniqueness index on `chart_divisionals` is swapped for a wider one (same name) and the recorder's trigger there is re-created with the extra column; the two protective "seal" records the deploy gate compares against (one for the procedure, one for the trigger) are updated to match, as the gate expects; two table descriptions are replaced and five column descriptions added, writing the rule above into the database.

**What is NOT done.** Nothing is inserted into, changed in or deleted from any chart's data. No build is started. No other function, table, permission, role or setting is touched. The plan refuses, changing nothing, if any build is running on any chart, if the deploy gate is not green, or if any object is not exactly the state this plan was written against.

**What can go wrong.**
- *It stops by itself.* All checks run in one all-or-nothing transaction; any failure rolls everything back. Cost: a retry.
- *A few seconds of waiting.* While the index is swapped the `chart_divisionals` table is briefly locked; the plan gives up rather than wait more than five seconds for the lock.
- *The dry run cannot run the recorder end to end.* It runs only inside a real build, so its first real use is the next rebuild (tested on disposable copies with 18 realistic row shapes, not on production). If something unexpected appears, the rebuild stops with a clear error and keeps no wrong data.
- *This plan alone may not make every build pass.* The rehearsal found two more small defects nearby (candidates **B** and **C**, section 9). They are **not** in this plan and **not** covered by the authorisation below; if admitted they are named separately and need your separate approval.
- *Rolling back after a rebuild needs a manual step.* Before any rebuild the rollback is automatic and exact. Once a rebuild has stored the extra `ga_vargas` rows the old narrow index cannot be re-created; the rollback refuses and says so, and those rows must be deleted first.

**How it is undone.** One command (`--rollback`) restores today's recorder, the old index, the old trigger, the old descriptions and the old seal records in one transaction. It was **rehearsed** on disposable databases (apply, verify, roll back, verify identical to the starting state: every function fingerprint and every seal record) on PostgreSQL 15 and 17.

**What you are asked to approve**, after Strategic Suvarna approves the dry run: the sentence in section 1. It authorises this plan only, not B or C, a rebuild, or anything else.

## 1. The owner's authorisation (one line, exact)

> Authorization: run the D6 owner-path plan with hash `<PLAN_HASH>` on production (the L1 data-plane capture repair, option A / N-84, plus the F-A2 ga_vargas key widening), exactly as described in `<PLAN FILE PATH>` sha256 `<PLAN_FILE_SHA>`, after Strategic Suvarna has approved the dry run. No other change.

`<PLAN_HASH>`, `<PLAN FILE PATH>` and `<PLAN_FILE_SHA>` are filled in ONCE, at the freeze, by Strategic Suvarna's process: the plan hash is computed from the plan text and the expected diff (section 5), which name the executor's sha256 and the three gate sha256, and it deliberately does **not** contain this file's own sha256 (that would be circular: the plan file's sha256 is quoted next to the hash, outside the file). If patch B and/or patch C are admitted, the sentence gains, after "the F-A2 ga_vargas key widening", a separate clause naming each one ("plus patch B (<one-line description>)", "plus patch C (<one-line description>)"), so the owner approves each separately from option A.

## 2. Status of the hunk set

| hunk | what | in this plan | who decided |
|---|---|---|---|
| H1, H2, H3a, H3b | option A (N-84): the capture repair | **YES** | the owner (N-84) |
| F-A2 function hunk, F-A2 index, F-A2 trigger | `ga_vargas` key widening | **YES** | SS (Q-L1-01) |
| **B** | the capture function's dasha partition scope excludes the 1,080 `vimshottari_kp` rows that `ga_dashas` legitimately writes in the `vimshottari` partition | **NO, candidate** (section 9) | pending SS review of the rehearsal worker's file and design note |
| **C** | `complete_l1_data_plane_partition`'s post-pass counts only `chart_facts` | **NO, candidate** (section 9) | pending SS review |

The plan is NOT frozen until the 19-lane rehearsal has finished all lanes and every admitted hunk is in `FUNCTION_PATCHES`. The executor, the plan text, EXPECTED_DIFF, the generic rollback and the re-attestation are generated from that list, so admitting a hunk is a data edit plus one `live_defs/<function>.LIVE.sql` file (and `make_function_patch.py` derives the hunk list from the rehearsal worker's patched text).

## 3. The numbered items (exact object list)

All in ONE transaction as `data_plane_l1_owner` (the administrator is granted that role transiently only if not already a member, `SET LOCAL ROLE`, and the transient grant is revoked; `lock_timeout` 5 s, `statement_timeout` 120 s, `search_path = pg_catalog, public, pg_temp`).

| # | object | change | bound values |
|---|---|---|---|
| 1 | function `public.l1_data_plane_capture_row()` (owner `data_plane_l1_owner`, SECURITY DEFINER, `search_path=pg_catalog, public, pg_temp`, ACL `{data_plane_l1_owner=X/data_plane_l1_owner}`: all unchanged) | `CREATE OR REPLACE` with the live text plus exactly six zero-context diff hunks (H1, H2, H3a, H3b, and the F-A2 hunk at two sites) | live md5 `1e079261aa42eb97a1885a48035e7520` (19,780 chars, sha256 `0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8`) to patched md5 `b2f4242f034d1a3983edb08c625dc353` (sha256 `d65a6804508e964e0e92b6a507a12fc747aa69bb0f2bc34170c721e281d0728d`); diff sha256 `bca80fe61b88a0fcb2d2721c542a25893a4bc8cb77d0d094be31b4324056553f` |
| 2 | unique index `public.chart_divisionals_unique_idx` | create the 7-column index under a temporary name, drop the 6-column one, rename (same final name) | `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)` to `(…, fact_subject)`, NULLS NOT DISTINCT |
| 3 | trigger `l1_data_plane_capture` on `public.chart_divisionals` | drop and re-create, one more argument `'fact_subject'` | 6 to 7 arguments |
| 4 | comments on `l1_data_plane_row_snapshots` and `l1_data_plane_fact_snapshots` | 2 table comments replaced, 5 column comments added (`row_snapshots.source_row_jsonb`; `fact_snapshots.grain_jsonb`, `value_num`, `value_text`, `value_jsonb`): the contract in `exec/DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md` | removed 2 / added 7 |
| 5 | function attestation row for `l1_data_plane_capture_row()` in `l1_data_plane_function_attestations` (ONE row) | `definition_digest` updated to sha256(`pg_get_functiondef`), immutability trigger disabled and re-enabled around it, rowcount must be 1 | `0f8f42b6…b9b8` to `d65a6804…728d` |
| 6 | trigger attestation row `chart_divisionals` / `l1_data_plane_capture` in `l1_data_plane_trigger_attestations` (ONE row) | same, from the live trigger definition | `d0064f5ed31f7db91cb239967f783af3a885f21b39aa7c833877989a713768b0` to `ea1281cfcd1d2250e3a073dbb070a566da18cab1431a0547f6c10583a4f5fe83` |

Order inside the transaction: preconditions (read only), function, comments, function attestation, identity probe (84 fixture rows into a session-local temp table, never persisted), then the index swap and trigger (the `ACCESS EXCLUSIVE` window starts at `DROP INDEX` and is bounded and measured), then the trigger attestation, then every commit condition (section 5). COMMIT only if all hold.

### The five edits to the function (the whole diff, nothing else)

- **H1** declares two helper variables, `v_typed_col TEXT; v_companions TEXT[];`.
- **H2** a `chart_facts` row with no typed value at all (number, text and structured value all empty; a JSON null counts as empty) whose state would be `present` or `zero` becomes `floored` when the producer said `floored`, else `unavailable`. It is never recorded as `present`.
- **H3a** if more than one typed value is present, keep ONE by the fixed precedence number, then text, then structured (JSON), clear the others, remember which were cleared.
- **H3b** when something was cleared, the fact's `grain_jsonb` gains `typed_value_column` (the kept one) and `companion_value_columns` (the cleared ones). Only then; otherwise the `grain_jsonb` is byte-identical to today's.
- **F-A2** the dependency-identity expression used for `ga_condition` provenance gains `'fact_subject=' || COALESCE(cd.fact_subject,'<null>')` and the `ORDER BY` gains `cd.fact_subject`.

The complete row, every column, stays in `l1_data_plane_row_snapshots.source_row_jsonb`.

## 4. Bound constants (provisional while the gate pins are TBD)

| item | value |
|---|---|
| executor `d6_dataplane_capture_fa2_exec.py` sha256 | see `plan.txt` last line / `make_plan.py` (PROVISIONAL until the freeze: every executor edit changes it) |
| F-A2 module `d6_f_a2_key_widening_DRAFT.py` sha256 | `af5e6565d6e6c0b0d4906952bb7cf76ad5ea000147b43eeda2c2f4fcaa347215` |
| patch A module `d6_capture_patch_a.py` sha256 | `613553c1320ab3ed63bbb98ce7bc0f2468fe3d762b6daf06d27d3d85d6b79d81` |
| live definition `live_defs/l1_data_plane_capture_row.LIVE.sql` sha256 | `0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8` |
| gate files (`exec/gate_v2`, PR #2938) bound in `GATE_PINS` | **TBD** until Strategic Suvarna binds them after review |
| gate revision 3 as PROPOSED (PR #2938 head `7f0db55c3`; `tests/gate_fixture` holds byte-identical copies and a test proves it) | `prerun_gate.py` `01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e`; `run_gated.sh` `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076`; `executor_standards.py` `bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135` |
| plan hash | `sha256(plan text + "\n" + json(EXPECTED_DIFF))` bound with `bind_gate_into_plan_hash` to the `prerun_gate.py` and `run_gated.sh` pins; PROVISIONAL value printed by `python3 make_plan.py --gate-dir tests/gate_fixture`, which also prints the hash the plan would have if the proposed rev3 pins are bound by the one-line edit it names |

The plan text (`plan.txt`) names the executor sha256, the three module/live-definition sha256, the gate pins and every hunk; the plan hash does not contain this file.

## 5. EXPECTED_DIFF (what the commit conditions prove)

Across a before/after snapshot of every public index, trigger, `l1_`/`l2_`data-plane and lifecycle function, both attestation tables and the table and column comments of the two snapshot tables:

- exactly ONE index, ONE trigger, ONE trigger-attestation row changed; exactly ONE entry changed in function and in function attestation (the patched signature(s), `N` once B or C is admitted); comments removed 2 / added 7;
- ACL, role membership, RLS, policy, per-chart row data of `chart_divisionals`, and the state of every append-only trigger identical;
- the live function body BEFORE equals the shipped pre-state byte for byte (md5 as bound, read live as `suvarna_reader`), the body AFTER equals the bound patched body, and the zero-context diff between them has the bound sha256 and hunk count: the function differs ONLY by the listed hunks;
- owner, SECURITY DEFINER, `proconfig` and ACL of the function unchanged;
- the new index is unique, valid, NULLS NOT DISTINCT on the 7 columns; every attestation row equals the live object under the deploy gate's own join and equals the bound digest; the gate's three queries are false AFTER the plan under `search_path public` and stored equals gate-side digests (attestation drift 0);
- the identity probe lands 84 of 84 distinct identities (18 with the legacy 6 arguments); the transient grants are revoked and membership equals the pre-state;
- `--expect-plan` equals the plan hash; `--expect-evidence` equals this run's evidence digest (apply).

The EXPECTED_DIFF JSON is generated from `FUNCTION_PATCHES` and is part of the hashed plan.

## 6. Order of operations and gate steps

HARD RULE (F-A2): **the `ga_vargas` writer deploys FIRST, then this plan**, never the reverse (an old writer on the 7-column index deletes rows silently). `--apply` requires `--writer-commit <40-hex sha>` and refuses unless the deployed image tag equals it and the `ga_vargas` writer digest equals the frozen one.

1. `exec/gate_v2/run_gated.sh python3 d6_dataplane_capture_fa2_exec.py --count --expect-plan <PLAN_HASH>`: read-only preconditions and pre-state, always rolled back.
2. Same launcher, `--dry-run --expect-plan <PLAN_HASH> --writer-commit <sha>`: applies everything, prints the exact catalog diff, runs every commit condition, rolls back. Prints the evidence digest. Strategic Suvarna approves the dry run.
3. Same launcher, `--apply --expect-plan <PLAN_HASH> --expect-evidence <digest from step 2> --writer-commit <sha>`.
4. Read-only afterwards, as `suvarna_reader`: `verify_after_apply.sql` (every row PASS), then after the S-L1 `ga_vargas` rebuild `s_l1_ga_vargas_acceptance_check.sql`.

The executor never starts directly: `main()` calls the launch check first and refuses (exit 93) without the launcher's verifying marker or while the gate pins are TBD; it refuses an under-test marker (exit 93) and a stray test variable (exit 95) outside pytest; it writes `outcome.json` (`dry_run`, `applied`, `failed` or `commit_state_unknown`) in every mode. The administrator credential is fetched inside the process only after the plan hash matched, and is never printed or saved.

## 7. Verification SQL (reader-runnable, read only)

```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_before_apply.sql )   # every row PASS now
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_after_apply.sql )    # every row PASS after the apply
```

Both read catalog text, md5, ACL and the attestation tables only. Tests prove they are read-only, PASS before on the replayed pre-state, PASS after on the applied state and FAIL on the wrong state. **Run against production as `suvarna_reader` on 2026-10-02 (this session): `verify_before_apply.sql` returned PASS on every check** (function md5 `1e079261…` / 19,780; attestation digest equal; 6-column index; 6-argument trigger with digest `d0064f5e…`; the two 1035 table comments; attestation drift 0 for functions and triggers; 11 of 11 append-only triggers enabled; the 14 other L1 functions and the existing L2 functions keep their md5; no build planned/running/paused on any chart). The plan is therefore still bound to the live state as read today.

## 8. The rollback (rehearsed)

`--rollback-dry-run` and `--rollback` apply the exact inverse generated from the same list: each function re-applied from its shipped live definition, the 1035 table comments restored and the five column comments set to NULL, the 6-column index (create temporary, drop, rename), the 6-argument trigger, and every function and the trigger re-attested. Preconditions: each function md5 equals its patched md5 and its attestation equals the patched digest; the 7-column index and 7-argument trigger; the patched comments; **no two `chart_divisionals` rows share the 6-column key** (after a rebuild that stored widened rows the old index is impossible: delete them first, the rollback refuses otherwise); no build in flight; gate green.

**Rehearsal (same test run, disposable PostgreSQL 15 and 17):** apply, verify (SQL passes), `--rollback-dry-run` (state unchanged), `--rollback`, verify: the state (every function md5 and full body, every attestation row, index, trigger, comments, ACL, RLS, row data) equals the pre-state exactly, the old shapes fail again, and the forward plan can be applied again. Test: `tests/test_combined_exec.py::test_the_rollback_is_rehearsed_apply_verify_rollback_verify_equal_to_the_pre_state`; a three-function variant (B and C admitted in the test only) is `tests/test_candidate_hunks.py`.

## 9. Candidate hunks B and C (NOT in this plan; named separately)

Written by the 19-lane rehearsal; staged here as data only (`candidates/`), so that admission is cheap once Strategic Suvarna has reviewed each one. They are asserted NOT to be in the plan.

- **B** `capture_l1_data_plane_dasha_partition(uuid,text,text,integer)` (live md5 `eee8d9d4f5fbbbbbd03a9abda7c62385`): in the `vimshottari` partition the `ga_dashas` writer also writes 1,080 `vimshottari_kp` rows; the capture counts only the partition's own system, so completion fails with "reported 10427 rows but active build scope has 9347". The candidate widens the scope to `ANY(ARRAY['vimshottari','vimshottari_kp'])` for that one system (six sites).
- **C** `complete_l1_data_plane_partition(uuid,text,text,text,integer)` (live md5 `dcab40cf524c39efca628517c14fd9e8`): the `__concurrency_post_pass__` partition of `ga_dashas` also inserts a scope-cap dasha row, which the post-pass count (chart facts only) does not see. The candidate adds the dasha rows first seen in that partition to the observed count (one block).

Each is a pure hunk list over one function with its own function-attestation row; the executor's apply, checks, EXPECTED_DIFF, rollback and re-attestation handle it with no code change (proved by `tests/test_two_function_machinery.py` and `tests/test_candidate_hunks.py`). Whether each is right is for the rehearsal worker's design note and SS's review; this plan does not claim it.

## 10. What can still go wrong / what was NOT verified

1. The executor was never run against Cloud SQL or any production database: only against disposable PostgreSQL 15 and 17 clusters with production-shaped roles, owners, ACLs and the real migration 1035, and a fake administrator (a non-superuser with CREATEROLE and no table privilege on PostgreSQL 15; the cluster superuser on 17).
2. The real administrator's ability to `GRANT data_plane_l1_owner` / `amjis_app` and the visibility of a hidden builder session (`pg_read_all_stats`) are not verified (a refusal would be harmless and early).
3. The capture function runs only inside a real build as `data_plane_builder`: its first production run is the S-L1 rebuild. The 18-shape probe and real-writer tests on the disposable database exercise it, but not on production data or volume.
4. Snapshot volume for `chart_divisionals` grows about 58 percent per generation (38,596 vs 24,392 rows per chart captured).
5. Whether any downstream reader assumes six-element `row_identity` values for `chart_divisionals`: a repository search found none; `l1_data_plane_row_snapshots` is not readable by the reader, so existing contents were not inspected.
6. B and C (section 9) are not reviewed here; without them `ga_dashas` partitions may still abort in the rebuild.
7. The F-A2 plan v1.3 (`F_A2_KEY_WIDENING_D6_PLAN_v1_0.md`) remains the reference for the F-A2 half (row-count expectations, the writer, 1222, S-L1 acceptance); this document supersedes only its execution wrapper.

## 11. Test evidence (disposable databases only)

`tests/` in this folder: plan and wiring (no database), the combined executor and the rollback rehearsal, the 18-shape capture probe, real `ga_vargas` and `ga_structural` writers on the replay, the second-function machinery, the candidate hunks, and `mutation_proof.py` (each rule neutered in a copy, the named tests must go red). One test is **deliberately red** until Strategic Suvarna binds the gate pins: `test_plan_and_wiring.py::test_gate_pins_are_bound`. Counts and mutation results are in the pull request description.
