VERDICT: REJECT

Reviewed `5d9e712799336958e5a82bce74b57859a2944f44...c58b0331aa530370b68c4c01b143f0aa3bcdba81`. The reference-locking fix is sound for the normal worker path. A catchable interruption still loses the commit-outcome report, and D3 does not enforce its requirement for another surviving owned run.

File references: **TD** = [teardown script](platform/scripts/teardown_v5_small_test_job.py); **S** = [shared module](platform/scripts/v5_small_test_shared.py); **UT** = [unit tests](platform/scripts/__tests__/test_teardown_v5_small_test.py); **DBT** = [database tests](platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py); **RB** = [runbook](00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md).

1. **P2 — Ctrl-C escapes without reporting the known commit outcome.**  
   **TD:502–524, 539–541, 571–579.**

   The inner handler catches `BaseException` and records `commit_unknown` or `committed`, but `main()` catches only `Exception`. `KeyboardInterrupt` therefore escapes without displaying that outcome. Interruptions during cleanup can also escape without an outcome attribute.

   Offline fault injection produced:

   | Interruption point | Fake COMMIT calls | Outcome attached | Outcome printed |
   |---|---:|---|---|
   | Inside `commit()` | 1 | `commit_unknown` | None |
   | Immediately after confirmed commit | 1 | `committed` | None |
   | Connection close after commit | 1 | None | None |

   This no longer falsely reports rollback, but it fails requirement E. Preserve the transaction outcome through cleanup and report catchable interruptions at the CLI boundary. The new test at **UT:1242–1259** covers `MemoryError`, which subclasses `Exception`; it misses this distinction.

   **Blocks single production use: yes, under the requested outcome-reporting requirement.** Owner privileges and a successful dry run do not exercise this boundary.

2. **P2 — Both D3 proofs can use the same surviving run.**  
   **S:139–153, 279–284, 315–332.**

   `prove_stamp()` finds any matching marker among the supplied runs. Its caller does not retain or compare the matched run identities.

   **Failure scenario:** A produced test output. B uses the identical slice marker, but another vector component changed—for example, the implementation identity. B commits its manifest and stops before replacing A’s snapshot. A’s run is subsequently pruned, with no NULL-linked receipt remaining to trigger the earlier refusal. B’s marker then proves both stamps.

   I reproduced acceptance with **one surviving owned run**, differing manifest/snapshot vectors and identical slice components: exit 0, one fake COMMIT. This violates D3’s “another owned test run” condition and the requested unconditional refusal in case (iv). The current regression uses different markers and consequently misses it: **UT:1292–1314; DBT:878–911**.

   Return the matched run identity and require distinct surviving run evidence for this interrupted-state exception, or refuse the ambiguous case and point to the runbook.

   **Blocks single production use: only if that use relies on this ambiguous interrupted-state exception.** It does not block an ordinary timely teardown with consistent output and manifest.

3. **P3 — FK exemptions cover entire tables before checking the FK shape.**  
   **S:228–235; TD:163,344,371–372; UT:1223–1228.**

   Complete catalog discovery now works, but an allowlisted table bypasses every shape check.

   **Failure scenario:** a later migration adds a secondary composite audit FK from `asset_provenance_receipts` to `build_runs`, with `CASCADE`. A receipt outside the teardown’s deletion scope references an owned run through that secondary FK. The existing ownership checks inspect `build_id`; catalog validation skips the table; deleting the run can delete that unrelated receipt.

   An offline catalog-response probe confirmed that such an unsupported FK is silently accepted. Exempt only understood relationships whose referencing rows are demonstrably covered by the deletion scope.

   **Blocks single production use: no, against the nine relationships documented in RB:30, provided the required live readback confirms that catalog.** This is a limitation of the broader fail-closed claim.

The requested dispositions are:

| Item | Disposition | Evidence |
|---|---|---|
| **T1 — Reference race** | **Resolved** for the supported relationships. Parent locks precede validated reference reads and remain through deletion. | TD:281–288,344; S:270–272; DBT:817–857 |
| **T2 — Composite FKs / `confkey`** | **Partly resolved.** Complete ordered column lists and named refusals exist; table-wide exemptions remain finding 3. | S:202–243 |
| **T3 — Post-commit reporting** | **Partly resolved.** Original allocation failure fixed; catchable interruptions remain finding 1. | TD:497–516; UT:1242–1259 |
| **T4 — Reconstruction bypass** | **Resolved.** Failed surviving-run proof cannot fall back to reconstruction, including canonical stamps. | S:155–160; UT:1268–1283 |
| **T5 — Recovery digest** | **Resolved as requested.** `output_digest_spec_sha256` is recorded and compared; recovery remains NOT FOR USE. | RB:32–44 |
| **TB1 — Chain classes** | **Resolved for class-bearing rows:** windows, records and event-class coverage. | S:338–353 |
| **TB2 — Builder privileges** | **Resolved in documentation.** Corrected production grant account and shortfalls are recorded. | RB:62–65 |
| **TB3 — Recovery evidence source** | **Resolved in documentation.** Writer digest at dispatch and chart configuration replace the incorrect manifest-vector comparison. | RB:37–44 |
| **TB4 — Actual FK columns/readback** | **Resolved.** Correct ledger column names and the catalog readback are recorded. | RB:29–30; DBT:761–776 |
| **TB5 — Symmetric interrupted-state proof** | **Partly resolved.** Same validator and digest proof; distinct-run requirement remains finding 2. | S:115–175,284,316 |

For **D3**, the two stamps use the same writer validator, original-marker digest comparison and normalized-component equality. The manifest’s separate horizon is checked at **S:178–186**. The snapshot has no separate horizon column; its inventory headers must match its proved marker’s horizon and its `input_digest` at **S:325–331**.

| Requested state | Actual result |
|---|---|
| **(i)** A completed; B committed its manifest, then crashed before snapshot | **Removable**, once both runs are terminal and both proofs and inventory checks pass. |
| **(ii)** Non-test output, then test manifest | **Refused:** the older snapshot lacks a valid test stamp. S:316–322. |
| **(iii)** Test output, non-test manifest | **Refused:** current manifest proof fails. S:284–291. |
| **(iv)** A’s owning run pruned | **Refused for distinct markers; not guaranteed for repeated markers**, as finding 2 demonstrates. A NULL-linked receipt independently causes refusal at TD:329–335. |
| **(v)** Both runs survive; first run’s output, second run’s manifest | **Removable as intended**, subject to both proofs and the snapshot-based inventory/class checks. |

I found no supported writer path through this exception that deletes an **unstamped non-test output chain**. The writer replaces the entire chain and inventory before inserting the new snapshot in the snapshot substep: `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:827–842`. Contacts have no `event_class` column; their attribution depends on that replacement boundary, rather than an individual class check.

The **dispatch script is absent from this checkout**, so I could not verify its “any prior candidate/output means teardown first” admission rule. The interrupted-snapshot refusal points to the runbook through **TD:365–367 and S:318–322**, not back to dispatch.

The **lock order** is:

1. Session-level orchestrator chart advisory lock.
2. Transaction-level Gochara chart advisory lock, with a 10-second lock timeout.
3. Selected `build_runs` rows, `FOR UPDATE`, ordered by ID.
4. The pinned chart’s generation-5.0 publication row, `FOR UPDATE`.

Evidence: **TD:215–228,281–285; S:270–272**. The runner acquires the same session lock before claiming work (`runner.py:1313–1334`); the writer takes the Gochara lock before reading its slice and writing (`ka_gochara_v5.py:720–723`). A running conforming worker therefore makes teardown refuse before these row locks are reached; I found no worker lock-order deadlock.

`FOR UPDATE` does not mutate the frozen run manifest. It blocks competing updates/deletes and FK key-share checks. A reference committed before lock acquisition is subsequently detected. A new reference attempted after acquisition waits; after a dry-run rollback it can proceed, while after deletion it fails its FK check. That preserves data integrity, although it does not promise success to every concurrent actor. The watchdog likewise cannot prune an already-locked run; **RB:27 still describes the older, pre-row-lock behavior**.

For **FK discovery**, both column arrays are read in ordinal order, with composite and alternate-target keys refused by constraint name outside the exemptions noted above. A referencing-table SELECT failure propagates and rolls back. My offline error probe produced zero deletes and zero commits. RLS-hidden references are a separate concern; production RLS and owner bypass were not verified.

For **one production use**, **fix finding 1 first**. Finding 2 additionally blocks ambiguous interrupted-state recovery. Finding 3 does not block the documented current catalog after its readback is confirmed.

Verification performed: **124 offline tests passed, 2 dispatch-dependent tests skipped**; targeted recording-connection probes; `git diff --check` passed. No files were modified.

**Not verified:** database execution or concurrency, production schema/data/ACLs/RLS/search path, live FK readback, CI results, sibling dispatch integration, migration-1304 parity, recovery execution, or census regeneration. No database or network was accessed.

