VERDICT: ACCEPT_WITH_AMENDMENTS

**No remaining dispatch defect blocks the requested two-run sequence under the stated conditions.** One non-blocking P3 reporting gap remains. The restricted builder suffices for **dispatch staging**; teardown requires its separately authorized role and privileges.

Reviewed `b159f259217141d117e37d7afe36834f1bf7ffe6...9fdcd77d422243e39a7380ce06a4f0b8f9ce5a05`. No files modified; no database or network access.

1. **P3 — One interrupt boundary still loses the known outcome and run ID. Blocks production use: no, provided the steward uses `--list-runs` before retrying.**

   At [dispatch_v5_small_test_job.py:573](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp4/platform/scripts/dispatch_v5_small_test_job.py:573), the nested `try` begins at an instruction outside the enclosing exception-handler range.

   Injecting `KeyboardInterrupt` there on Python 3.14.6 produced **one successful commit, zero rollbacks, exit 130, empty stdout, and no attempted run ID**. Python 3.13.7 bytecode has the same uncovered boundary.

   Crucially, [line 654](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp4/platform/scripts/dispatch_v5_small_test_job.py:654) now prints the honest **“transaction was NOT recorded”** fallback and directs recovery through lookup/listing. It does **not** claim that nothing committed. Thus the round-3 blocker is fixed, although “the attempted run ID on any failure” remains overstated.

   Recommended amendment: retain outcome/run ID in caller-visible state, or eliminate this nested-handler boundary, and add the corresponding interruption test.

**Round-3 disposition**

| Item | Disposition | Evidence |
|---|---|---|
| P2: report preparation after commit could falsely report no commit | **Resolved as a production blocker.** The broader every-interrupt guarantee remains partial because of P3 above. | `dispatch_v5_small_test_job.py:563` prepares the report before commit at `:570`; outcome handling is at `:578–599`. Tests at `test_dispatch_v5_small_test.py:1032–1068` cover preparation, printing, ordering and the honest fallback. |
| P3: migration-parity test silently passed when absent and checked only `count_sql` | **Resolved in the test implementation; actual migration parity remains unverified here.** | [test_dispatch_v5_small_test.py:162](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp4/platform/scripts/__tests__/test_dispatch_v5_small_test.py:162) parses 14 migration-controlled fields, including all five routing fields. Lines 192–203 compare them and explicitly skip absent 1304. `scope` is explicitly attributed to migration 1243. |
| Dispatch-role and operating-documentation gaps | **Resolved.** | [Runbook:73](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp4/00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md:73) through line 78 now cover builder sufficiency, matching image, database results, lookup, readbacks and refusal over prior output. |
| Round-3 writer/kernel items 3 and 4 | **Excluded as requested.** | Their separate fixes were not reassessed. |

**Exit paths after COMMIT is attempted**

References below are to `platform/scripts/dispatch_v5_small_test_job.py`.

| Path | Output and exit |
|---|---|
| Commit returns; reporting succeeds (`:570–577`, `:627–646`) | Staging confirmation, launch command, deadlines, image/digest and database-result instructions on stderr; run ID on stdout; **0**. |
| `commit()` raises; or interruption occurs before `phase="committed"` is recorded (`:570–571`, `:582–583`) | **COMMIT OUTCOME UNKNOWN**, attempted ID and lookup instructions; **1**, or **130** for Ctrl-C. No rollback attempted. |
| After confirmation, `_AFTER_COMMIT()` or report emission fails (`:572`, `:577`, `:584–585`) | **COMMIT CONFIRMED**, attempted ID and “do not dispatch again”; **1**, or **130** for Ctrl-C. No rollback attempted. |
| Ordinary `Exception` from the first `close()` (`:573–576`) | Suppressed; normal report follows. **0** if reporting succeeds. |
| Ctrl-C inside that `close()` (`:574`) | **COMMIT CONFIRMED** with attempted ID; **130**. |
| Ctrl-C at the uncovered boundary (`:573`) | Honest unrecorded-outcome fallback, **no run ID**, lookup/list instructions; **130**. P3 above. |
| Cleanup `close()` fails while another exception propagates (`:595–598`) | Secondary failure suppressed; original outcome/reporting path retained. |
| `SystemExit` reaches the boundary (`:665–666`) | Its exit code is returned without an outcome diagnostic. Other non-`KeyboardInterrupt` `BaseException` types escape. There is no normal explicit post-commit source path raising these; injection confirmed this limitation. |
| Forced termination, or failure while printing the final error diagnostic (`:668`, `:673`, `:676`) | No guaranteed complete output. Recover with `--list-runs`; silence is not rollback evidence. |

I found **no admission or mutation regression**. The companion teardown change only accepts empty probe/check strings as equivalent to NULL, consistent with the runner’s boolean routing checks.

**Operating notes for the steward**

1. Use a **direct connection**, with `DATABASE_URL` supplied through the process environment. Complete the supplied predispatch readbacks and a successful dry run using the actual dispatch role. Confirm migration-1304 registry shape, inactive status, fresh/lit dependencies, and absence of conflicting runs, receipts or generation output.
2. Use a clean checkout and the job image built from the **same commit**, including the separately reviewed writer/kernel fixes. Confirm the job’s pinned ephemeris provisioning.
3. Run 1: `all_classes_1y`, all **26** classes, with explicit timezone-aware bounds spanning the approved year. Run 2: `one_class_full`, exactly one scored class; omitted bounds select **1998-01-01 through 2026-04-17 UTC**, end-exclusive.
4. Rehearse each slice, then add `--execute --i-am-steward --after-settled-1`. Launch the **committed** run ID—not the dry-run ID—before its printed ten-minute deadline.
5. On confirmed commit, do not redispatch. On unknown/missing reporting, use `--lookup ID`, or **`--list-runs` when no ID was printed**, before retrying. A never-started active run must become terminal before teardown/restaging.
6. Read `build_runs.state`, `build_run_assets.state/error`, and the slice’s database results. Cloud Run success is insufficient.
7. Follow **run 1 → reviewed teardown → run 2 → reviewed teardown**. Perform teardown’s own dry run using its authorized role. The documented builder lacks required teardown grants: [runbook:64](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp4/00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md:64). A builder-only lifecycle remains blocked.
8. Keep both runs unsealed/unpublished, retain their evidence, and teardown well before the **90-day retention deadline**. Do not bypass ownership or NULL-receipt refusals.

**Verification:** 118 dispatch tests passed; one explicitly skipped because migration 1304 is absent. The changed teardown regression test passed. Independent in-memory fault injection verified the reporting outcomes above.

**Not verified:** migration 1304’s actual contents/application, production grants/RLS or registry state, real-database suites/CI, deployed image and ephemeris, live concurrency/watchdog behavior, actual network commit uncertainty, runtime limits, or successful completion of either production slice. The accepted teardown baseline and separate writer/kernel fixes were not re-reviewed.