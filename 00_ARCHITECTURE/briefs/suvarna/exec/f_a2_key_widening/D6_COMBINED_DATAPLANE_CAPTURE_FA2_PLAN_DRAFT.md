---
artifact: D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN
version: "0.12-DRAFT"
status: DRAFT_NOT_FROZEN (items 1-5 are in; the gate pins are BOUND (N-86); the plan hash is NOT computed: the plan freezes ONCE, when SS says)
date: 2026-10-02
lane: suvarna/land/TI-d6-dataplane-capture-fa2-001 (cut from #2858 head e81ed714e)
decision: owner N-84 (option A), SS Q-L1-01 (F-A2), owner/SS N-85 (patches B and C approved as design, in the SAME plan), SS N-86 (gate v2 revision 3 bound)
execution: NONE against any real system. Production was read only as suvarna_reader (catalog text, md5, ACL, attestation digests); every test ran on disposable local PostgreSQL 15 and 17 clusters with production-shaped roles, owners and ACLs and a fake administrator.
frozen_by: not frozen. The plan hash, the plan file and the independent review happen ONCE, on the complete hunk set.
changelog:
  - "0.12-DRAFT (2026-10-02): independent review (review-D6) accepted; edits only. M1: STEP 0 (migration 1255 live and verified) in the order of operations, a read-only executor precondition that refuses naming 1255 (owner SELECT on brahma_yoga_catalog; builder SELECT on the seven reference tables), the same rows in verify_before/after_apply.sql, external prerequisites (1255, 1219 category-ownership seeds) listed, and section 0 reworded: D6 repairs the capture path, it does not by itself make the rebuild succeed. LOWs: transient owner-role grants named in section 0 and in the authorisation sentence; chart_vichara also takes the exclusive lock, the statement bound (100) and the measured 63-65; production figures for item 2 labelled production, rehearsal figures labelled rehearsal; what the plan hash covers and does not (the verification SQL files are named by sha256 in the hashed plan text); operator procedure for commit_state_unknown (section 8a); freeze timing and the final sequence (section 9a); notes on owner-alone counts and floored facts. Tests: B and C against a database, the limits pinned independent of the sha pin, step 0 refusals."
  - "0.11-DRAFT (2026-10-02): SS: ITEM 5 = K1 joins the combined D6: the chart_vichara capture-trigger arguments gain constituent_fact_ids (nine), arguments only, no function hunk, only that table's trigger-attestation row re-attested. The executor's trigger leg is a data-driven list (chart_divisionals for F-A2, chart_vichara for item 5) with generated EXPECTED_DIFF, probes and rollback. The summary is five numbered items."
  - "0.10-DRAFT (2026-10-02): SS N-85: patches B and C moved from candidates into FUNCTION_PATCHES (items 2 and 3), each with its own live base md5, target md5, hunks, function-attestation row and tests; the owner summary is four numbered items (A, B, C, F-A2); a marked, unwritten slot for a possible item 5. SS N-86: GATE_PINS bound to GATE_V2 revision 3 (sha256 recomputed at #2938 head 7f0db55c3 before pinning); the deliberately red pin test is green."
  - "0.9-DRAFT (2026-10-02): first combined draft (option A + F-A2; B and C as candidates). Machinery is data-driven (a list of function hunks; EXPECTED_DIFF, the plan text, the generic rollback and the re-attestation are generated from it)."
---

# D6 owner-path plan (combined): L1 data-plane capture repair (option A, N-84) plus the F-A2 `ga_vargas` key widening

## 0. One-page summary for the owner (plain language)

**What and why.** Madhav keeps a protected, append-only history of every row the chart-building programs write. The machinery that records that history has five small defects in its capture path. This single plan repairs all five, in one all-or-nothing step. It changes rules and definitions only, never chart data. **It repairs the capture path; it does not by itself make the canonical chart's rebuild succeed.** The rebuild also needs migration 1255 (read permissions for the build job), migration 1219 (category-ownership seeds) and the other rebuild lanes; the plan refuses to run until 1255 is live (section 10).

**The five items**

1. **Option A (N-84), the recorder stores unusual rows honestly.** *What it changes:* the recorder function accepts facts that carry no value (recorded as "floored" or "unavailable", never as present) and facts that carry several kinds of value (it keeps one in the summary table: number, then text, then structured detail; says which it kept and set aside; the complete untouched row stays in the history table). *Serving effect:* rebuilds of the assets that write such rows stop aborting at the recording step; readers of the summary table see one value per fact plus the marker, and lose nothing.
2. **Patch B (N-85), the dasha recorder includes the `vimshottari_kp` rows.** *What it changes:* the function that records the dasha (planetary period) rows counts the `vimshottari_kp` rows that the `vimshottari` build has always written alongside its own, instead of ignoring them. In production, for the canonical chart, those are 1,170 / 1,170 / 1,080 / 1,080 / 1,170 rows (krishnamurti / lahiri / raman / surya_siddhanta / true_chitra) beside 9,194 / 9,205 / 9,063 / 8,998 / 9,204 `vimshottari` rows. *Serving effect:* the `ga_dashas` rebuild's `vimshottari` parts complete (in the rehearsal they failed with "reported 10427 rows but active build scope has 9347"), and those rows are now in the protected history.
3. **Patch C (N-85), the completion check counts the dasha post-pass rows.** *What it changes:* the function that closes a part of a build also counts the extra dasha row the `ga_dashas` post-pass writes. *Serving effect:* the `ga_dashas` post-pass part no longer aborts on a row-count mismatch (it also needs the category-ownership seed of migration 1219, which this plan does not apply).
4. **F-A2, the `ga_vargas` uniqueness rule is widened by one column.** *What it changes:* one uniqueness index on `chart_divisionals` is swapped for a wider one (same name), the recorder's trigger there is re-created listing the extra column, and one hunk of the recorder (at two sites) is updated to match. *Serving effect:* the `ga_vargas` rebuild keeps about 14,200 more rows per chart (the sign-by-sign strengths and house lords that look alike to the old rule); divisional pages gain those rows (about 58 percent more rows per chart).

5. **K1 (chart_vichara capture identity), the vichara recorder tells rows apart by their source facts.** *What it changes:* the recorder's trigger on `chart_vichara` gets one more argument, `constituent_fact_ids` (nine instead of eight), so rows that differ only in which source facts they rest on are recorded as separate rows. Arguments only: the recorder function itself is not edited, and only that table's seal record is updated. It is "grain plus source-fact provenance set", **not** a natural key (that table has none, and none is created). *Serving effect:* the `ga_vichara` rebuild can complete: today about 1,706 rows per ayanamsha collapse to about 836 recorded identities and the build would fail closed at completion; with the new argument and the writer's separate fix (sorting the fact list, dropping exact duplicates, a different lane) they are recorded as 1,556 distinct rows, and neither half alone can slip wrong data through.

**What changes in the production database.** Three stored procedures replaced by edited copies (the recorder, the dasha recorder, the completion function); one index swapped and two triggers re-created (`chart_divisionals`, `chart_vichara`); the three protective "seal" records for those procedures and the two for the triggers (the records the deploy gate compares against) updated to match, as the gate expects; two table descriptions replaced and five column descriptions added. **Transient permissions, part of the plan.** For the duration of the transaction the administrator account is granted membership of two roles, `GRANT data_plane_l1_owner, amjis_app TO CURRENT_USER` (each only if not already a member), and exactly what was granted is revoked in the SAME transaction; net role membership is identical before and after, and the plan refuses to commit otherwise.

**What is NOT done:** nothing is inserted into, changed in or deleted from any chart's data; no build is started; no other function, table, permission, role or setting is touched. The plan refuses, changing nothing, if any build is running on any chart, if the deploy gate is not green, or if any object is not exactly the state the plan was written against.

**What can go wrong.**
- *It stops by itself.* All checks run in one all-or-nothing transaction; any failure rolls everything back. Cost: a retry.
- *A few seconds of waiting, on two tables.* `chart_divisionals` (index swap and trigger) and `chart_vichara` (trigger) are both locked exclusively from their first `DROP` until the commit; readers and writers of those tables wait. The plan gives up rather than wait more than five seconds for a lock: in the rehearsal a concurrent reader of `chart_vichara` made the plan fail after 5.0 seconds and roll back clean. The statements issued while the locks are held are capped at 100 (the check refuses to commit above it) and measured 63 to 65 in the rehearsals.
- *It will not start until the read permissions exist.* Step 0 (section 6) refuses, changing nothing, if migration 1255 is not live.
- *The dry run cannot run the recorders end to end.* They run only inside a real build, so their first real use is the next rebuild (tested on disposable copies, not on production). If something unexpected appears the rebuild stops with a clear error and keeps no wrong data.
- *Rolling back after a rebuild needs a manual step.* Before any rebuild the rollback is automatic and exact. Once a rebuild has stored the extra `ga_vargas` rows the old narrow index cannot be re-created; the rollback refuses and says so, and those rows must be deleted first.

**How it is undone.** One command (`--rollback`) restores all three procedures, the old index, both old triggers, the old descriptions and every old seal record in one transaction. If the connection drops at the very moment of the commit, the run records `commit_state_unknown`; section 8a is the procedure (nothing else runs until the state is read and decided). It was **rehearsed** on disposable databases (apply, verify, roll back, verify identical to the starting state: every function fingerprint and every seal record) on PostgreSQL 15 and 17.

**What you are asked to approve**, after Strategic Suvarna approves the dry run: the sentence in section 1, which names the five items and the transient role grants. It authorises items 1 to 5 and those grants only, not a rebuild and not the writer-side fix of item 5, which is a separate lane.

## 1. The owner's authorisation (one line, exact)

> Authorization: run the D6 owner-path plan with hash `<PLAN_HASH>` on production (the L1 data-plane capture repair, option A / N-84; patch B and patch C, approved as design in N-85; the chart_vichara capture identity, K1; plus the F-A2 ga_vargas key widening; including the transient role grants `GRANT data_plane_l1_owner, amjis_app TO CURRENT_USER`, revoked in the same transaction, net membership unchanged), exactly as described in `<PLAN FILE PATH>` sha256 `<PLAN_FILE_SHA>`, after Strategic Suvarna has approved the dry run. No other change.

`<PLAN_HASH>`, `<PLAN FILE PATH>` and `<PLAN_FILE_SHA>` are filled in ONCE, at the freeze: the plan hash is computed from the plan text and the expected diff (section 5), which name the executor's sha256 and the three gate sha256, and it deliberately does **not** contain this file's own sha256 (that would be circular: the file's sha256 is quoted next to the hash, outside the file). The sentence names every item (A, B and C, K1, F-A2) so that none is approved by implication.

## 2. Status of the hunk set

| item | what | in this plan | who decided |
|---|---|---|---|
| 1 | option A: H1, H2, H3a, H3b (the capture function's typed projection) | **YES** | the owner (N-84) |
| 2 | patch B: `capture_l1_data_plane_dasha_partition` includes the `vimshottari_kp` rows | **YES** | the owner, via SS (N-85), as design |
| 3 | patch C: `complete_l1_data_plane_partition` counts the `ga_dashas` post-pass dasha rows | **YES** | the owner, via SS (N-85), as design |
| 4 | F-A2: index, trigger, and the F-A2 hunk of the capture function | **YES** | SS (Q-L1-01) |
| 5 | K1: the `chart_vichara` capture-trigger arguments gain `constituent_fact_ids` (arguments only, no function hunk) | **YES** | SS (K1 joins the combined D6) |

The plan is NOT frozen until the 19-lane rehearsal has finished all lanes and the hunk set is final. The executor, the plan text, EXPECTED_DIFF, the generic rollback and the re-attestation are generated from `FUNCTION_PATCHES`, so a further hunk is a data edit plus one `live_defs/<function>.LIVE.sql` file (`make_function_patch.py` derives the hunk list from a patched function text). Item 5 is not a function hunk: it is the `chart_vichara` entry of the executor's data-driven trigger-change list.

## 3. The numbered items (exact object list)

All in ONE transaction as `data_plane_l1_owner` (the administrator is granted `data_plane_l1_owner` and `amjis_app` transiently, each only if not already a member, `SET LOCAL ROLE`, and the transient grants are revoked in the same transaction; `lock_timeout` 5 s, `statement_timeout` 120 s, `search_path = pg_catalog, public, pg_temp`). Every patched function keeps its owner `data_plane_l1_owner`, SECURITY DEFINER, `search_path=pg_catalog, public, pg_temp` and ACL (checked before and after).

| item | object | change | live md5 (length) / sha256 to patched md5 / sha256; zero-context diff |
|---|---|---|---|
| 1 and the function half of 4 | function `public.l1_data_plane_capture_row()` | `CREATE OR REPLACE`, live text plus exactly six diff hunks (H1, H2, H3a, H3b; the F-A2 hunk at two sites) | `1e079261aa42eb97a1885a48035e7520` (19,780) / `0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8` to `b2f4242f034d1a3983edb08c625dc353` / `d65a6804508e964e0e92b6a507a12fc747aa69bb0f2bc34170c721e281d0728d`; diff `bca80fe61b88a0fcb2d2721c542a25893a4bc8cb77d0d094be31b4324056553f` |
| 2 | function `public.capture_l1_data_plane_dasha_partition(uuid,text,text,integer)` | `CREATE OR REPLACE`, live text plus six hunks (declare `v_systems`; set it to `{vimshottari, vimshottari_kp}` for the `vimshottari` partition, else the partition system; use `system_id = ANY(v_systems)` at the four scope sites) | `eee8d9d4f5fbbbbbd03a9abda7c62385` (5,357) / `166928dd4d72ef82ceafd6bc48c6b66784d70a8c4326f769237e9f3eef83276f` to `873ee5da411f4e6366ec3faed98c3ae2` / `b94208d44dc371a773414eed15c59478b36a9890a83aeb26c09e72a6fa6ec750`; diff `e59ec6b5ad90b6376265e5c7811c45937b5ac3903aeb19f9d0aa8669d7c34c85` |
| 3 | function `public.complete_l1_data_plane_partition(uuid,text,text,text,integer)` | `CREATE OR REPLACE`, live text plus one hunk (for `ga_dashas` and the `__concurrency_post_pass__` partition the observed row count also includes the dasha rows first seen in that partition) | `dcab40cf524c39efca628517c14fd9e8` (8,647) / `93bcb4afee1d568e885d83cc8eb58c1122dc429bfa201f90226b162a18cf5b4c` to `31d005e8ecacf40547f0537e24d717d5` / `21d297abdbc99d11c073dc1b9c57b85eb0ea662f0d6927b1faa3889b07043ac0`; diff `8c9d7d8dcfb5c6da760b36051e1e882562ea481503a5a23a7d3178f0dcf85c2f` |
| 4 | unique index `public.chart_divisionals_unique_idx` | create the 7-column index under a temporary name, drop the 6-column one, rename (same final name) | `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)` to `(…, fact_subject)`, NULLS NOT DISTINCT |
| 4 | trigger `l1_data_plane_capture` on `public.chart_divisionals` | drop and re-create, one more argument `'fact_subject'` | 6 to 7 arguments |
| 1 | comments on `l1_data_plane_row_snapshots` and `l1_data_plane_fact_snapshots` | 2 table comments replaced, 5 column comments added (the contract in `exec/DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md`) | removed 2 / added 7 |
| 1, 2, 3 | THREE function-attestation rows in `l1_data_plane_function_attestations` (one per patched function) | `definition_digest` updated to sha256(`pg_get_functiondef`), immutability trigger disabled and re-enabled around each, rowcount must be 1 | each digest equals the live sha256 above, then the patched sha256 above |
| 4 | trigger attestation row `chart_divisionals` / `l1_data_plane_capture` in `l1_data_plane_trigger_attestations` (ONE row) | `definition_digest` updated from the live trigger definition, immutability trigger disabled and re-enabled around it, rowcount must be 1 | `d0064f5ed31f7db91cb239967f783af3a885f21b39aa7c833877989a713768b0` to `ea1281cfcd1d2250e3a073dbb070a566da18cab1431a0547f6c10583a4f5fe83` |
| 5 | trigger `l1_data_plane_capture` on `public.chart_vichara` | drop and re-create with one more argument `'constituent_fact_ids'`, arguments only: no function hunk, no index, no constraint | 8 to 9 arguments (`chart_id, ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version`, then `constituent_fact_ids`) |
| 5 | trigger attestation row `chart_vichara` / `l1_data_plane_capture` (ONE row; the `chart_vichara` mutation-guard row and every other table's row untouched) | same re-attestation | `aa242e3b291de7460d09cbaed833cdf179e8f4f896f1bb0a931028c4708367a8` (read live as `suvarna_reader` 2026-10-02, equals sha256 of the live trigger text) to `f02569e953979bd1dee7118eafee431fe24bc2c20f46c432f9d0ba37b6136e19` |

Order inside the transaction: the transient role grants, preconditions (read only, including step 0), the three functions, comments, the three function attestations, the identity-probe fixtures (84 rows and 120 rows, loaded into session-local temp tables that are never persisted, BEFORE the lock window; they are read back after the DDL), then the index swap and trigger (the `ACCESS EXCLUSIVE` window starts at `DROP INDEX` and is bounded and measured), then the trigger attestations (one per changed table), then every commit condition (section 5). COMMIT only if all hold.

### Item 1 and item 4's function hunk: the five edits to `l1_data_plane_capture_row()` (the whole diff of that function, nothing else)

- **H1** declares two helper variables, `v_typed_col TEXT; v_companions TEXT[];`.
- **H2** a `chart_facts` row with no typed value at all (number, text and structured value all empty; a JSON null counts as empty) whose state would be `present` or `zero` becomes `floored` when the producer said `floored`, else `unavailable`. It is never recorded as `present`.
- **H3a** if more than one typed value is present, keep ONE by the fixed precedence number, then text, then structured (JSON), clear the others, remember which were cleared.
- **H3b** when something was cleared, the fact's `grain_jsonb` gains `typed_value_column` (the kept one) and `companion_value_columns` (the cleared ones). Only then; otherwise the `grain_jsonb` is byte-identical to today's.
- **F-A2** the dependency-identity expression used for `ga_condition` provenance gains `'fact_subject=' || COALESCE(cd.fact_subject,'<null>')` and the `ORDER BY` gains `cd.fact_subject`.

The complete row, every column, stays in `l1_data_plane_row_snapshots.source_row_jsonb`.

### Items 2 and 3: the dasha lifecycle functions

- **Item 2 (patch B).** In the `ga_dashas` `vimshottari` substep the writer has always also written the `vimshottari_kp` rows inside the `vimshottari` partition. **Production, canonical chart:** `vimshottari_kp` 1,170 / 1,170 / 1,080 / 1,080 / 1,170 and `vimshottari` 9,194 / 9,205 / 9,063 / 8,998 / 9,204 (krishnamurti / lahiri / raman / surya_siddhanta / true_chitra). The function scoped the partition to its own system only, so completion failed; **in the rehearsal** with "dasha partition vimshottari:lahiri reported 10427 rows but active build scope has 9347" (rehearsal numbers, not production's). `v_systems` is `{vimshottari, vimshottari_kp}` when the partition system is `vimshottari`, otherwise just the partition system; the four places that scope by system (the active-row count, the two sides of the completed-generation replay comparison and the snapshot INSERT) use `system_id = ANY(v_systems)`.
- **Item 3 (patch C).** The `__concurrency_post_pass__` partition of `ga_dashas` also INSERTS rows (the scope-cap dasha row) that the completion's observed-row count did not see. One block adds the dasha rows first seen in that partition (in `l1_data_plane_dasha_snapshots` for this partition and in no other partition of the generation).

Both were derived by `make_function_patch.py` from the rehearsal worker's patched texts (`rehearsal_inputs/`), and a test proves the shipped hunks reproduce those texts byte for byte.

## 4. Bound constants

| item | value |
|---|---|
| executor `d6_dataplane_capture_fa2_exec.py` sha256 | see `plan.txt` last line / `make_plan.py` (PROVISIONAL until the freeze: every executor edit changes it) |
| F-A2 module `d6_f_a2_key_widening_DRAFT.py` sha256 | `c911c239c7344976b0c223b4835f0417c1b9b44ba247e8a790e6e7fbca2d0565` |
| patch A module `d6_capture_patch_a.py` sha256 | `613553c1320ab3ed63bbb98ce7bc0f2468fe3d762b6daf06d27d3d85d6b79d81` |
| patches B and C module `d6_dasha_partition_patches.py` sha256 | printed by `make_plan.py` / last lines of `plan.txt` (NOT FINAL until the freeze) |
| live definition `live_defs/l1_data_plane_capture_row.LIVE.sql` sha256 | `0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8` |
| gate files (`exec/gate_v2`, PR #2938 head `7f0db55c371fe13ddccc493ac0730c8703a7e940`, GATE_V2 revision 3) **BOUND in `GATE_PINS` by SS N-86** (sha256 recomputed at that commit before pinning; `tests/gate_fixture` holds byte-identical copies and a test proves it) | `prerun_gate.py` `01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e`; `run_gated.sh` `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076`; `executor_standards.py` `bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135` |
| plan hash | NOT COMPUTED FINAL. It is `sha256(plan text + "\n" + json(EXPECTED_DIFF))` bound with `bind_gate_into_plan_hash` to the `prerun_gate.py` and `run_gated.sh` pins, computed ONCE at the freeze (every executor or hunk edit changes it; `python3 make_plan.py --gate-dir tests/gate_fixture` prints the current, non-final value) |

### What the plan hash covers, and what it does not

**Covered** (it is `sha256(plan text + "\n" + json(EXPECTED_DIFF))`, bound to the two gate pins): every statement and hunk; the executor's, the patch modules' and the three live definitions' sha256; the gate pins; the limits (`lock_timeout`, `statement_timeout`); the step 0 prerequisite text; the trigger changes; and the **sha256 of `verify_before_apply.sql`, `verify_after_apply.sql` and `s_l1_ga_vargas_acceptance_check.sql`**, which the hashed plan text names (so editing a verification file changes the plan hash; this does not touch the gate binding, which is only the two gate pins). **Not covered:** this plan file (its sha256 is quoted in the authorisation, outside the file), the contract document, the tests and `make_plan.py`.

The plan text (`plan.txt`) names the executor sha256, the three module/live-definition sha256, the gate pins and every hunk; the plan hash does not contain this file.

## 5. EXPECTED_DIFF (what the commit conditions prove)

Across a before/after snapshot of every public index, trigger, `l1_`/`l2_`data-plane and lifecycle function, both attestation tables and the table and column comments of the two snapshot tables:

- exactly ONE index changed, exactly TWO triggers and TWO trigger-attestation rows changed (`chart_divisionals` and `chart_vichara`, no other table's row: identity-checked, not only counted); exactly THREE entries changed in function and in function attestation (the three patched signatures); comments removed 2 / added 7;
- ACL, role membership, RLS, policy, per-chart row data of `chart_divisionals`, and the state of every append-only trigger identical;
- for EACH of the three functions: the live function body BEFORE equals the shipped pre-state byte for byte (md5 as bound, read live as `suvarna_reader`), the body AFTER equals the bound patched body, and the zero-context diff between them has the bound sha256 and hunk count: the function differs ONLY by the listed hunks;
- owner, SECURITY DEFINER, `proconfig` and ACL of the function unchanged;
- the new index is unique, valid, NULLS NOT DISTINCT on the 7 columns; every attestation row equals the live object under the deploy gate's own join and equals the bound digest; the gate's three queries are false AFTER the plan under `search_path public` and stored equals gate-side digests (attestation drift 0);
- the `chart_divisionals` identity probe lands 84 of 84 distinct identities (18 with the legacy 6 arguments); the `chart_vichara` identity probe (120 writer-shaped, whole-row-distinct fixture rows, sorted fact lists) has 120 distinct identities under the live 9 arguments and fewer under the legacy 8; the transient grants are revoked and membership equals the pre-state;
- `--expect-plan` equals the plan hash; `--expect-evidence` equals this run's evidence digest (apply).

The EXPECTED_DIFF JSON is generated from `FUNCTION_PATCHES` and is part of the hashed plan.

## 6. Order of operations and gate steps

**Step 0 (external prerequisite, before the dry run): migration 1255 is live and verified.** 1255 (PR #2962) grants the build job's identity `data_plane_builder` SELECT on seven reference tables (`yoga_family_members`, `reference_nakshatra`, `reference_nakshatra_pada`, `bg_shashtiamsha_deities`, `bg_graha_naisargika_friendship`, `bg_motion_state_thresholds`, `brahma_vichara_constants`) and the capture owner `data_plane_l1_owner` SELECT on `brahma_yoga_catalog`; it is applied by merge and deploy BEFORE the dry run (its own header: the grant must precede the D6 functions being exercised). Verify live, read only, as `suvarna_reader`: `verify_before_apply.sql` rows 60 and 61 read PASS. **On production today (read 2026-10-02) they read FAIL (false; 7 tables missing): 1255 is not applied.** The executor repeats the check as a read-only precondition and refuses, naming 1255, if it does not hold (it does not need the grants for `--rollback`).

HARD RULE (F-A2): **the `ga_vargas` writer deploys FIRST, then this plan**, never the reverse (an old writer on the 7-column index deletes rows silently). `--apply` requires `--writer-commit <40-hex sha>` and refuses unless the deployed image tag equals it and the `ga_vargas` writer digest equals the frozen one.

1. `exec/gate_v2/run_gated.sh python3 d6_dataplane_capture_fa2_exec.py --count --expect-plan <PLAN_HASH>`: read-only preconditions and pre-state, always rolled back.
2. Same launcher, `--dry-run --expect-plan <PLAN_HASH> --writer-commit <sha>`: applies everything, prints the exact catalog diff, runs every commit condition, rolls back. Prints the evidence digest. Strategic Suvarna approves the dry run.
3. Same launcher, `--apply --expect-plan <PLAN_HASH> --expect-evidence <digest from step 2> --writer-commit <sha>`.
4. Read-only afterwards, as `suvarna_reader`: `verify_after_apply.sql` (every row PASS), then after the S-L1 `ga_vargas` rebuild `s_l1_ga_vargas_acceptance_check.sql`.

The executor never starts directly: `main()` calls the launch check first and refuses (exit 93) without the launcher's verifying marker or while any gate pin is the unbound TBD marker; it refuses an under-test marker (exit 93) and a stray test variable (exit 95) outside pytest; it writes `outcome.json` (`dry_run`, `applied`, `failed` or `commit_state_unknown`) in every mode. `outcome.json` and `result.json` record the interpreter (`python_executable`, the full `python_version`) and the driver (`psycopg_version`, `libpq_version`), and the **evidence digest binds the same four values**: start both the dry run and the apply as `run_gated.sh /absolute/path/to/python3 <executor> ...` (never an ambient `python3`), and an apply or rollback under a different interpreter or driver refuses by itself (exit 92, distinct from every gate code, before the credential is fetched; a dry-run record that lacks the fields is refused as "cannot compare"). The administrator credential is fetched inside the process only after the plan hash matched, and is never printed or saved. The sequencing of the whole window (freeze timing, writers, migrations) is section 9a.

## 7. Verification SQL (reader-runnable, read only)

```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_before_apply.sql )   # every row PASS now
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_after_apply.sql )    # every row PASS after the apply
```

Both read catalog text, md5, ACL and the attestation tables only; rows 60 and 61 are the step 0 prerequisite rows (they read FAIL until 1255 is live, and PASS in both files afterwards). Tests prove they are read-only, PASS before on the replayed pre-state, PASS after on the applied state and FAIL on the wrong state. **Run against production as `suvarna_reader` on 2026-10-02 (this session, after B and C were added): `verify_before_apply.sql` returned PASS on every check, including the new B and C rows (live md5 and length; the function-attestation digest equals sha256 of the live definition; hunks absent)** (function md5 `1e079261…` / 19,780; attestation digest equal; 6-column index; 6-argument trigger with digest `d0064f5e…`; the two 1035 table comments; attestation drift 0 for functions and triggers; 11 of 11 append-only triggers enabled; the 12 other L1 functions and the existing L2 functions keep their md5; no build planned/running/paused on any chart). The plan is therefore still bound to the live state as read today.

## 8. The rollback (rehearsed)

`--rollback-dry-run` and `--rollback` apply the exact inverse generated from the same list: each of the three functions re-applied from its shipped live definition, the 1035 table comments restored and the five column comments set to NULL, the 6-column index (create temporary, drop, rename), the 6-argument trigger, and every function and the trigger re-attested. Preconditions: each function md5 equals its patched md5 and its attestation equals the patched digest; the 7-column index and 7-argument trigger; the patched comments; **no two `chart_divisionals` rows share the 6-column key** (after a rebuild that stored widened rows the old index is impossible: delete them first, the rollback refuses otherwise); no build in flight; gate green.

**Rehearsal (same test run, disposable PostgreSQL 15 and 17):** apply, verify (SQL passes), `--rollback-dry-run` (state unchanged), `--rollback`, verify: the state (every function md5 and full body, every attestation row, index, trigger, comments, ACL, RLS, row data) equals the pre-state exactly, the old shapes fail again, and the forward plan can be applied again. Test: `tests/test_combined_exec.py::test_the_rollback_is_rehearsed_apply_verify_rollback_verify_equal_to_the_pre_state`; the same rehearsal covers B and C in `tests/test_dasha_partition_patches.py` (dry run leaves everything identical; apply; rollback dry run; rollback; function md5s and attestation rows equal the pre-state).

## 8a. Operator procedure: `commit_state_unknown` (or a missing `outcome.json`)

`commit_state_unknown` means the connection failed AT the commit: the server may or may not have committed. Because the plan is ONE transaction, the database is in exactly one of two states. **Nothing else runs (no re-run, no rollback, no other change) until the state is read and decided**, in this order:

1. Read the run's `outcome.json` in its evidence directory (status, `evidence_digest`, the warning `commit_raised:<ExceptionClass>`) and the printed result. A MISSING `outcome.json` is handled the same way.
2. As `suvarna_reader`, run `verify_after_apply.sql` and `verify_before_apply.sql` (read only).
3. Read the catalog directly: the three function md5s (`l1_data_plane_capture_row()`, `capture_l1_data_plane_dasha_partition(...)`, `complete_l1_data_plane_partition(...)`), the capture-trigger arguments of `chart_divisionals` (7 or 6) and `chart_vichara` (9 or 8), the three function-attestation rows and the two trigger-attestation rows.
4. Decide:
   - **Applied** (`verify_after_apply.sql` every row PASS; md5s, arguments and attestation rows are the patched ones): the plan took effect. Record it, and go on to the post-apply checks (`verify_after_apply.sql` is the first; then the writer-side checks of the window).
   - **Not applied** (`verify_before_apply.sql` every row PASS; everything is the pre-state): nothing changed. Re-run through the gate from step 2 with a NEW dry run, a NEW evidence digest and a new Strategic Suvarna approval of that dry run (the old digest belongs to the old run).
   - **Partial** (some objects patched, others not): impossible by construction (one transaction, all-or-nothing). If it is ever seen, STOP, change nothing, and call the owner and Strategic Suvarna.
5. Only after the state is decided and recorded does anything else run.

## 9. Item 5 (K1): the `chart_vichara` capture identity

`chart_vichara` has no natural key (only its serial primary key); the capture trigger's arguments are the row identity that the partition completion counts against the writer's reported rows. With the eight live arguments rows that differ only in `constituent_fact_ids` collapse (about 836 identities for about 1,706 rows per ayanamsha, canonical chart, per the read-only vichara investigation, not recomputed here). Item 5 appends `constituent_fact_ids`: **"grain plus L1 source-fact provenance set", NOT a natural key** (contract: `exec/DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md` section 7). Arguments only, no function hunk, one trigger-attestation row. The writer half (sort `constituent_fact_ids`, whole-row exact dedupe, a collision assertion, the acceptance SQL) is a **separate lane**, not part of this plan. Counts (from the read-only investigation, canonical chart, per ayanamsha): 1,706 stored rows, 836 identities under the 8 arguments, **1,556** whole-row-distinct rows when the fact lists are sorted; the unsorted lists as stored give 1,562 for lahiri (set-order nondeterminism), which also fails closed. Each half fails closed alone, in either order (tests: owner alone with exact duplicates "reported 4 rows but protected capture contains 3"; writer alone, old arguments, "reported 3 rows but protected capture contains 1", driven through the real generation, guard, capture trigger and `complete_l1_data_plane_partition` as `data_plane_builder`).

## 9a. Freeze timing and the final sequence (ordering authority, SS ruling)

The plan is frozen ONCE, and only AFTER the integration (#2960, #2970 and the other integration pull requests) and #2858's `ga_vargas` writer are in main AND the deployed pipeline image is verified, so that the bound `ga_vargas` writer digest (`9212b478621c3572e75f606819e865de768b6212def695cf67bd368e0510e8a1`) is the one that will actually run. Shared-module churn in those pull requests can shift that digest; the executor then refuses at `--apply` (the writer-first check) and forces a re-freeze. The owner apply is ordered AFTER those writers and AFTER migrations 1255 and 1219. The final sequence, verbatim:

1255 merged and verified live → #2965/#2969/#2971 etc. into the integration → integration merged and deployed → clean no-shim 18-lane pass on that build → #2858 writer merged → short delta review of the edited D6 plan → SS says freeze → plan hash + plan-file sha → SS dry-run approval → dry run through the gate → owner's D6 line → SS apply approval → apply → W1.

## 10. External prerequisites, and what can still go wrong / what was NOT verified

**External prerequisites (not applied or checked by D6 except where stated).**
1. **Migration 1255** (PR #2962, grants only): `data_plane_builder` SELECT on seven reference tables, `data_plane_l1_owner` SELECT on `brahma_yoga_catalog`. A prerequisite of the D6 apply: the executor checks it read-only and refuses without it (step 0, section 6). Production today: not applied.
2. **Migration 1219** (category-ownership seeds): production's `fact_category_ownership` has no row for `dasha_scope_cap` (owner `ga_dashas`) or `panchanga_amrit_kaal` (owner `ga_panchanga`) and lacks the 172 seeds plus 2 the migration adds. A prerequisite of the S-L1 **rebuild**, not of the D6 apply: until it is applied the `ga_dashas` post-pass replay fails at the EXISTING ownership guard before AND after D6, so item 3's "post-pass part completes" cannot materialise from D6 alone. The disposable databases model the `dasha_scope_cap` row so that B and C themselves are what the tests measure.
3. **The other S-L1 lanes** (the writer fixes, the integration, the deployed pipeline image).

Section 0's claim is therefore: D6 repairs the capture path (items 1 to 5); the rebuild succeeds only together with 1255, 1219 and those lanes.


1. The executor was never run against Cloud SQL or any production database: only against disposable PostgreSQL 15 and 17 clusters with production-shaped roles, owners, ACLs and the real migration 1035, and a fake administrator (a non-superuser with CREATEROLE and no table privilege on PostgreSQL 15; the cluster superuser on 17).
2. The real administrator's ability to `GRANT data_plane_l1_owner` / `amjis_app` and the visibility of a hidden builder session (`pg_read_all_stats`) are not verified (a refusal would be harmless and early).
3. The capture function runs only inside a real build as `data_plane_builder`: its first production run is the S-L1 rebuild. The 18-shape probe and real-writer tests on the disposable database exercise it, but not on production data or volume.
4. Snapshot volume for `chart_divisionals` grows about 58 percent per generation (38,596 vs 24,392 rows per chart captured).
5. Whether any downstream reader assumes six-element `row_identity` values for `chart_divisionals`: a repository search found none; `l1_data_plane_row_snapshots` is not readable by the reader, so existing contents were not inspected.
6. B and C are approved as DESIGN (N-85); their behaviour inside a real `ga_dashas` build (partition counts 10,427 vs 9,347 resolved; the post-pass completing) was exercised by the 19-lane rehearsal, not by this lane: here they are proved as exact text transformations, as attested replacements and as a rehearsed rollback on disposable databases.
7. Item 5's numbers (836 / 1,706 / 1,556 identities and rows per ayanamsha, the 150 exact duplicates, the 330 groups) come from the vichara-design read-only investigation and were not recomputed here; the writer half of item 5 is a separate lane and is not exercised here beyond rows shaped like its output.
8. The F-A2 plan v1.3 (`F_A2_KEY_WIDENING_D6_PLAN_v1_0.md`) remains the reference for the F-A2 half (row-count expectations, the writer, 1222, S-L1 acceptance); this document supersedes only its execution wrapper.

## 11. Test evidence (disposable databases only)

`tests/` in this folder: plan and wiring (no database), the combined executor and the rollback rehearsal, the 18-shape capture probe, real `ga_vargas` and `ga_structural` writers on the replay, the second-function machinery, patches B and C, and `mutation_proof.py` (each rule neutered in a copy, the named tests must go red). `test_plan_and_wiring.py::test_gate_pins_are_bound` is green (the pins are bound, N-86). Counts and mutation results are in the pull request description.
