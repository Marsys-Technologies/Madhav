VERDICT: REJECT

Reviewed only `406a5090d007d8157554c2e32bb835d491a6e802...d8e8cf2fa540a387a1517531db28aa3d0f2b7c3e`. The original manifest/snapshot ownership hole is closed for the supported writer flow, and dry-run now rehearses the mutations. Remaining scope and reporting defects prevent production approval.

References below: **TD** = [teardown script](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/scripts/teardown_v5_small_test_job.py); **W** = [writer](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py); **UT** = [unit tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/scripts/__tests__/test_teardown_v5_small_test.py); **DBT** = [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py); **RB** = [runbook](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md).

**Findings**

1. **P2 — Deleting an owned run can still change unrelated audit records.**  
   **TD:355–372** checks attached provenance receipts, but **TD:512** deletes the parent run without checking its other incoming foreign keys.

   For example, `conversations.archived_by_run_id` references `build_runs(id) ON DELETE SET NULL` in [migration 1120:76–79](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/supabase/migrations/1120_jataka_conversation_archive_context.sql:76). Migrations **1122:92–95,126–129** and **1123:129–132,163–166,197–200** add equivalent links from event/prediction/ledger/calibration records.

   **Failure scenario:** an otherwise exclusively owned test run is referenced by a conversation or prediction, potentially on another chart. Every teardown guard passes; deleting the run clears that unrelated record’s audit link. Neither N-137 check detects it.

   This is a schema-permitted anomalous state; I did not establish that production contains it. **Before first production use: required**—refuse non-allowlisted references to selected runs, with coverage using these FKs.

2. **P2 — Some valid writer-produced stamps are rejected.**  
   **TD:224–233** reconstructs the marker from normalized component fields and recomputes its digest. However, **W:355–358** hashes the original marker, while **W:370–375** stores normalized class order and timestamp representations.

   **Failure scenario:** the writer accepts an `all_classes_1y` marker using `Z` timestamps or reversed class ordering, then stores its component normally. Teardown reconstructs a different digest preimage and refuses legitimate test output.

   I reproduced both cases offline: writer validation succeeded; teardown returned “not the writer’s component.” Canonical ordering and `+00:00` timestamps passed.

   **Before first production use: required**, unless the exact dispatch marker is independently demonstrated to satisfy an explicitly enforced canonical-input contract. Validate the original, verified marker preimage; do not weaken digest comparison.

3. **P2 — A committed execution can still report “No transaction was opened.”**  
   Commit is confirmed at **TD:564–566**, but the success print at **TD:594–596** is outside transaction-outcome handling. If it raises, **TD:632–633** calls `_safe_failure`, whose missing-outcome default at **TD:604** is `no_transaction`.

   **Failure scenario:** database commit succeeds, then writing the success report raises an output-stream error. The CLI reports failure and denies that a transaction opened.

   Offline reproduction: **one fake commit, exit 1, “No transaction was opened.”**

   **Before first production use: required.** Preserve the confirmed-commit outcome through reporting failures and test that boundary. The original close-error case and lost COMMIT acknowledgement are otherwise handled correctly.

4. **P2 — Recovery SQL does not bind its mutation to the receipt version whose origin was proved.**  
   **RB:25–32** records evidence, then restores/deletes receipts using only asset, chart, reusable partition keys and `build_id IS NULL`. Step 4 does not specify a transaction or rollback on mismatch.

   Receipt contents can be replaced under the same key: [provenance.py:255–267](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/python-sidecar/pipeline/orchestrator/provenance.py:255).

   **Failure scenario:** between evidence collection and recovery, a recorded partition is replaced by another unlinked receipt. The DELETE removes that newer evidence; the row count still matches. The UPDATE variant can misattribute it to the historical test run.

   **Before first production use:** required **before using recovery**, rather than the ordinary timely teardown. Recovery needs locks, full receipt-identity revalidation and transactional rollback on any mismatch. Independent historical proof must remain bound to the exact rows being changed.

5. **P3 — The proposed privilege recipe omits trigger-side privileges.**  
   **RB:39–44,52** proposes a dedicated role with the listed privileges, but restoring an active registry row invokes migration 596’s ordinary invoker-security function, which performs `UPDATE asset_freshness`—[596:56–80](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:56). The table lists only SELECT/DELETE for freshness.

   **Failure scenario:** a role created exactly from that recipe fails when restoring an active registry row, even after the pinned freshness rows have been deleted.

   **Before first production use: not blocking for a verified owner-role execution.** Correct the recipe before provisioning a narrower role.

**A. Disposition of the six round-2 findings**

| Round-2 finding | Round-3 disposition |
|---|---|
| Ownership proof | **Partly resolved.** Snapshot/vector comparison closes the destructive interrupted-replacement case; valid-marker compatibility remains finding 2. TD:211–237,405–453. |
| Dry-run fidelity | **Resolved.** Common mutation and validation path; rollback versus commit is the terminal difference. TD:547–566; UT:573–584. |
| Retention/recovery | **Partly resolved.** Correct 90-day warning, remaining-time output and unchanged NULL refusal. Recovery has finding 4; dispatch changes cannot be verified here. TD:379–385,474–486. |
| N-137 end state | **Resolved for the requested predicates.** Catalog status, dependents and asset-wide non-test evidence are checked before and after deletion. TD:252–286,468–470,556–558. |
| Cross-chart FK/trigger effects | **Partly resolved.** Both specifically requested guards exist. Other incoming run FKs remain finding 1. TD:364–372,457–467. |
| Transaction-outcome reporting | **Partly resolved.** Rollback and COMMIT uncertainty are distinguished; post-commit reporting remains finding 3. |

**B. Ownership walkthrough**

For canonical markers and the supported writer sequence:

| State | Result |
|---|---|
| **(i) Completed slice** | Removable when the remaining guards pass. Stamp, snapshot vector and existing inventory headers agree. TD:416–453. |
| **(ii) Failed after manifest, before snapshot** | A fresh stamped manifest with no output is removable. Existing output without a snapshot is refused; an older non-test snapshot is refused as an interrupted replacement. TD:429–440. |
| **(iii) Failed after snapshot, partway through output** | **Removable.** The check does not require all stamped classes, finalized inventories, completed records or windows. It validates only headers that exist. TD:441–453. |
| **(iv) Full non-test candidate; no slice ran** | Refused because the current manifest lacks a valid test stamp. TD:416–421. |
| **(v) Slice, then full build fails between manifest and snapshot** | Refused: the current manifest is unstamped, even though the surviving snapshot/chain is from the slice. TD:416–421. |
| **(vi) Sealed or published generation** | Refused by publication, seal and authority checks; non-candidate lifecycle states are also refused. TD:292–319,417. |

The reasoning depends on the writer’s snapshot substep replacing the chain and snapshot together, **W:818–842**, with successful substeps committed by [asset_runner.py:914–915](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td3/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:914).

I found no remaining path among these six supported states that deletes an older non-test **output chain**. Finding 2 can nevertheless strand a legitimate completed or partial slice. Findings 1 and 4 concern evidence outside that chain.

**C. Complete mutation scope**

All direct chart predicates use the pinned chart.

| Mutation | Scope |
|---|---|
| `asset_provenance_receipts`, `asset_freshness`, `asset_throughput` | Exact asset + chart; **all partitions, no generation predicate**. TD:509–510,513. |
| `build_run_assets`, `build_runs` | Selected exclusively owned run UUIDs. TD:511–512. Incoming run FKs remain significant. |
| `ka_gochara_eval_window`, `ka_gochara_relationship_record`, `ka_gochara_contact` | Exact chart + generation `5.0`. TD:106–109,514–515. |
| `kala_gochara_coverage` | Exact chart + `5.0` + `partition_kind='event_class'`. TD:110. |
| Search interval, obligation, path pin, inventory and input snapshot | Exact chart + `5.0`, in dependency order. TD:112–118. |
| `kala_gochara_publication` | Exact chart + `5.0`; last generation deletion. TD:119–120. |
| `asset_registry` | Global `ka_gochara_v5` row; sets only `is_active=false`. TD:554. |

Window memberships, record prerequisites and both verification tables cascade through chart/generation-bearing FKs. Legacy tables are guard-only. Global substrate/contact identities and Moon coverage remain; `body_target` coverage also falls outside the deletion predicate.

Thus “every other generation preserved” describes the generation tables, not a generation-specific bookkeeping filter.

**D–E. Dry-run and writer imports**

Dry-run fidelity is now real at the statement level: every DELETE, registry UPDATE and both validation phases run in both modes. No mutation is execution-only. Dry-run does not exercise COMMIT or any commit-time deferred checks.

Importing the writer **does register `ka_gochara_v5` in the process-local writer registry**—W:602 and `writers/__init__.py:177–196`. I verified import from the documented `platform` directory: no database driver was imported and no audited network/process operation was attempted. `--help` also runs there.

The script now depends on the sidecar dependency environment and private writer functions. Import failure refuses safely at TD:138–141. Future validator/component changes can affect historical teardown compatibility; finding 2 demonstrates an existing compatibility problem.

**F. Runbook and role conclusion**

The timely teardown procedure is consistent with the implementation. The manual recovery procedure needs finding 4 corrected.

Migration history supports `amjis_app` as the intended owner-role candidate; it does **not** prove current production ownership, role membership or the assertion that it is the only existing sufficient role. The builder’s missing freshness DELETE is explicitly confirmed by migration **1217:218–219**. The runbook correctly acknowledges that live ACLs were not inspected.

The dispatch script and migration 1304 are absent from this tree. Therefore, the claimed dispatch warning and registry parity remain unverified.

**G. Tests and verification**

Executed without database/network access or file writes:

- Offline suite: **82 passed, 1 skipped**.
- In-memory mutation removing the **before-delete** N-137 check: detected by **UT:763–768**.
- In-memory mutation removing the **after-delete** check: detected by **UT:771–776**.
- Valid-marker normalization and post-commit reporting probes reproduced findings 2 and 3.
- `git diff --check`: passed.

So **each N-137 check is individually covered somewhere**, despite the database tests’ admitted inability to distinguish their removal.

The database tests now use real writer substeps for the manifest/snapshot transition—DBT:103–146,498–508. However, bookkeeping remains simplified DDL—DBT:46–62—without migration 596’s invalidation trigger or the additional incoming run FKs. The populated test still stamps its fixture with guards disabled at `test_c38_teardown_populated.py:53–65`.

CI collects both teardown database suites and the unit suite. The census delta changes only its hash and source-revision fields.

**H. Remaining limits**

The advisory locks protect cooperating pinned-chart builders. They do not serialize watchdog pruning or every asset-wide registry/evidence mutation. Lock timeout also does not bound connection establishment or total query duration.

**Not verified:** PostgreSQL execution, actual concurrency, production data/schema/ACLs, CI results, dispatch integration, migration-1304 parity, or regenerated census reproducibility. No database or network was accessed. No files were modified.

