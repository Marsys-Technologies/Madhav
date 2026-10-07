VERDICT: REJECT

Reviewed `9c1f429702181f135d6f265c2950c9d6c08f6e0a...4ff511cfa9336662d76683f5b4255d614d61c754`. The v5 deletion order matches the kernel, but ownership checks can admit non-test data, and preflight checks are not synchronized with deletion.

1. **P1 — Refusal checks can become stale before deletion.**  
   [teardown_v5_small_test_job.py:312](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:312) calls plain SELECT checks, followed by broad DELETEs at line 321, without acquiring the orchestrator exclusion lock or Gochara chart lock first.

   **Failure:** a non-test build commits its receipt after the foreign-receipt check; line 294 subsequently deletes that receipt. A full candidate written before the teardown acquires a trigger-level chart lock can also be removed without repeating attribution checks. A concurrent published-but-unsealed status is likewise not rechecked.

   The checked-in sealed-generation triggers **do provide a backstop**: migration 1240’s `ka_gochara_boundary_write_guard` takes the chart lock and refuses sealed mutations. This is not evidence that sealed output can simply be deleted. It does not make the script’s run, receipt, or publication preflight race-free. Synchronize with competing operations before checking ownership and retain that protection through commit.

2. **P1 — Non-test and active runs are identified by the wrong scope predicate.**  
   [teardown_v5_small_test_job.py:213](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:213) checks active runs only for `scope='asset_set'` and exact `scope_target=ASSET_ID`. Line 227 also uses exact `scope_target` to detect non-test runs. Neither examines `build_run_assets`.

   **Failure:** a running or failed layer build containing v5 has `scope_target='kala'`; a multi-asset run has a comma-separated target. Both bypass these checks. If the run has written candidate output but has not produced a successful receipt, the receipt guard does not rescue it. An older test run then authorizes deletion.

   These are supported run shapes: `platform/src/app/api/cockpit/runs/route.ts:62` documents comma-separated asset sets. Refusal must examine actual v5 run membership, including non-test `build_run_assets` evidence.

3. **P1 — A historical test run or current slice stamp does not prove ownership of everything deleted.**  
   [teardown_v5_small_test_job.py:247](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:247) counts any test-triggered run for the chart. It does not bind that run to the current manifest, generation output, or even this asset. Line 259 accepts this count **OR** the manifest stamp.

   **Failure:** an old test run remains while a full, unstamped candidate replaces its output. If the full run is missed by finding 2 or its bookkeeping is gone, teardown accepts the full candidate. **It should refuse.** The unit test at `test_teardown_v5_small_test.py:270` explicitly enshrines acceptance without a stamp.

   Independently, line 265 accepts **all NULL-linked receipts** when the current manifest is stamped. A NULL-linked receipt from a pruned non-test run is indistinguishable here from a test receipt and gets deleted. A current manifest stamp cannot retrospectively establish that receipt’s origin. Preserve ambiguous evidence unless durable provenance establishes its ownership.

4. **P1 — Test-run deletion can destroy another asset’s bookkeeping and orphan its receipts.**  
   [teardown_v5_small_test_job.py:295](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:295) deletes every child asset row of runs selected by trigger and chart alone; line 296 deletes those entire runs. `_TEST_RUNS`, at line 121, has no asset or generation restriction.

   **Failure:** a test-tagged run also contains `ga_positions` or another asset. Its child bookkeeping is deleted, while its receipt survives because line 294 deletes only v5 receipts. Deleting the parent run then sets the other receipt’s `build_id` to NULL through migration 596’s FK—the exact orphaning problem this script promises to prevent.

   Validate that selected runs are exclusively owned by this teardown, including their dependent receipts, before deleting them.

5. **P1 — Optional legacy cleanup deletes data the v5 writer does not own.**  
   [teardown_v5_small_test_job.py:111](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:111) includes `kala_gochara_windows` and `kala_gochara_contacts`; line 300 deletes their pinned-chart, `5.0` rows without checking their build ownership.

   **Failure:** an earlier legacy writer or diagnostic operation left `5.0` rows for this chart. An unrelated qualifying test run causes those rows to be erased. The script itself states at line 117 that the v5 writer does not write these tables. `services/gochara_kernel/candidate_boundary.py:12` likewise treats their presence as unexpected.

   Rows labelled `3.0` or `4.x` survive the generation predicate. Nevertheless, unexpected legacy-table `5.0` rows should cause refusal unless separately proven to be this test’s output. The integration test at `test_c38_teardown_real_db.py:165` currently expects deletion of rows inserted before the test build.

6. **P2 — Connection errors can print credentials.**  
   [teardown_v5_small_test_job.py:308](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:308) connects outside the exception handler; `main()` provides no sanitized error boundary.

   **Failure:** a password containing malformed URI percent-encoding produces a libpq/psycopg parsing exception containing the password token. I reproduced this using only the DSN parser and a synthetic credential marker—no connection. The uncaught exception would print it. Handle failures with credential-safe diagnostics rather than raw exception text.

7. **P2 — Destruction requires no explicit execution flag, and DSN selection is not environment-only.**  
   [teardown_v5_small_test_job.py:345](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:345) makes `--dry-run` optional; invoking the script without flags executes deletion. [Line 70](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:70) silently imports `.env.local`.

   **Failure:** an operator omits `--dry-run` and has no exported DSN, but a checkout’s `.env.local` supplies production credentials. The command deletes immediately. Require explicit execution intent and obtain the DSN solely from the supplied process environment.

8. **P2 — Freshness bookkeeping survives removal of its receipt and output.**  
   [teardown_v5_small_test_job.py:293](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/teardown_v5_small_test_job.py:293) omits `asset_freshness`. The orchestrator persists that row alongside successful receipts in `pipeline/orchestrator/provenance.py:274`.

   **Failure:** teardown removes the receipt and output while retaining their freshness projection. If the registry is already inactive, the unchanged `is_active=false` update does not fire migration 596’s invalidation trigger (`WHEN OLD IS DISTINCT FROM NEW`). Existing freshness, potentially `fresh`, survives. Clean up or explicitly invalidate the corresponding chart-and-asset projection.

9. **P3 — The claimed chain drift guard does not inspect the writer’s chain deletion.**  
   [test_teardown_v5_small_test.py:199](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td/platform/scripts/__tests__/test_teardown_v5_small_test.py:199) compares `CHAIN_TABLES` with another hardcoded list. Only the inventory portion imports the kernel’s order constant.

   **Failure:** the writer adds another output-table deletion and this test remains green. I replaced `RecordStore.delete_generation_chain` in memory with a function that always raises; the advertised drift test still passed. Exercise the real helper against a recording connection and compare its statements.

The complete mutation scope is:

| Statement | Actual restriction and assessment |
|---|---|
| Receipt DELETE, line 294 | Exact v5 asset and pinned chart; no generation/partition restriction. Linked non-test receipts are refused only if visible during preflight. |
| Run-assets DELETE, line 295 | All assets belonging to trigger-and-chart-selected runs; insufficient ownership restriction. |
| Runs DELETE, line 296 | Trigger and pinned chart only; dependent FK effects can reach other assets. |
| Throughput DELETE, line 297 | Exact v5 asset and pinned chart; no generation or test ownership restriction. |
| Chain DELETEs, lines 98 and 300 | Windows → relationship records → contacts → event-class coverage, each pinned chart and `5.0`. |
| Inventory DELETEs, lines 104 and 300 | Intervals → obligations → path pins → inventory → snapshot, each pinned chart and `5.0`. |
| Legacy/manifest DELETEs, lines 111 and 300 | Legacy windows → legacy contacts → manifest, pinned chart and `5.0`; no writer-asset check. |
| Registry UPDATE, line 325 | Global registry row for v5 only. Intentionally not chart-scoped. An actual activation change also invokes the registry freshness-invalidation trigger. |

The chain and inventory orders match `record_store.py:595` and `inventory_store.py:103`. Memberships and prerequisites cascade; inventory and window verification rows cascade through inventory/path-pin FKs. **I found no missing table or FK-order error relative to those two kernel helpers.** Shared reference tables and Moon coverage are preserved. Legacy windows/contacts are genuinely optional; publication is effectively required because refusal checks query it before optional-table discovery.

The registry operation restores `is_active=false` and validates ten declared fields. A dispatch crash leaving only `is_active=true` is recoverable. Other field drift causes rollback rather than repair. **Exact migration-1304 parity remains unverified:** neither that migration nor the dispatch script exists at this HEAD, and the equality test skips.

Transaction handling uses one commit after validation and rollback on caught failures. Dry-run performs SELECTs, calls rollback, and makes **zero commits or DELETEs**. However, it skips registry validation: a missing registry row passes dry-run and fails execution. It also returns before closing the connection. Empty-output/repeat execution is supported by inspection provided required tables and the expected registry row remain; an actual integration rerun is not tested. Exit behavior is ordinary success `0`, uncaught failure `1`, argparse error `2`.

I ran the offline unit suite: **26 passed, 1 skipped**. The new integration suite uses real Gochara migrations but simplified bookkeeping tables. Its `_World.build()` stops at record steps, so teardown is not exercised against populated windows, memberships, or both verification tables. Missing coverage includes concurrent operations, layer/multi-asset non-test runs, mixed-asset test runs, non-test NULL-linked receipts, full-candidate attribution, restoration from an active registry row, and failure after partial deletion. The active-registry unit case is misleading: its fake does not apply UPDATEs and expects refusal instead of testing recovery.

**Not verified:** PostgreSQL execution, live schema/permissions, concurrency behavior, migration 1304, dispatch behavior, or CI results. No database or network access was used; no files were modified.

