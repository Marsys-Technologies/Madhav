VERDICT: REJECT

Reviewed `cc7190dc7bcecf3b8710642a4d127143699afd9a...80b99557a682aef886a761eae8dae6c78ff365b3`. The locking and several refusal rules are substantially improved. Ownership proof and dry-run fidelity still need correction.

Below, **TD** means [teardown_v5_small_test_job.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/scripts/teardown_v5_small_test_job.py), **UT** means [test_teardown_v5_small_test.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/scripts/__tests__/test_teardown_v5_small_test.py), and **DBT** means [test_c38_teardown_real_db.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py).

**Remaining findings**

1. **P1 — The manifest check does not prove ownership of the existing output.**  
   **TD:176–193, 310–325** checks a stamp’s superficial shape, without comparing the current manifest vector with the stored input snapshot.

   **Concrete failure:** an unsuccessful non-test candidate leaves output but no successful receipt; its run is eventually pruned. A later small test commits its stamped manifest, then fails before replacing the old output. Teardown sees only the test run and stamped manifest and deletes the older non-test output.

   This boundary exists in the reviewed source: [ledger.py:550](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/python-sidecar/services/gochara_kernel/ledger.py:550) updates the manifest in place; [ka_gochara_v5.py:484](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:484) does that before the snapshot step’s deletes at line 514; [asset_runner.py:914](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:914) commits each successful substep.

   Independently, the validator ignores the supplied stamp contract’s **schema and marker digest** and accepts empty class names and arbitrary horizon strings. Offline, a stamp with neither schema nor digest, `classes=[""]`, and `horizon=["bogus","backwards"]` passed and reached all 15 DELETE statements and one fake commit.

   **Required:** validate the complete producer stamp and establish that existing output belongs to that stamped candidate. Refuse mismatched snapshot/manifest identities and interrupted replacements whose ownership remains ambiguous.

2. **P2 — Dry-run does not rehearse execution.**  
   **TD:369–376** counts and returns before **TD:377–381** executes DELETEs, the registry UPDATE, and post-update validation. **UT:462** explicitly requires zero DELETEs.

   **Concrete failure:** the operator’s role can SELECT but cannot DELETE `asset_freshness`; dry-run succeeds, execution fails. The checked-in builder grants specifically exclude that DELETE privilege—[migration 1217:218](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/migrations/1217_suvarna_builder_freshness_and_transit_moorti_grants.sql:218). Trigger, FK, and registry-update failures are similarly invisible.

   I reproduced the divergence offline: an injected DELETE failure produced dry-run exit `0`, execution exit `1`. Execute the same mutation and validation path in both modes, then roll back dry-run, with zero explicit commits.

3. **P2 — Routine retention can make teardown permanently unavailable through this script.**  
   **TD:285–290** correctly refuses NULL-linked receipts. However, the [watchdog:462–476](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/src/app/api/cockpit/watchdog/route.ts:462) routinely deletes terminal runs after **90 days**, and [migration 596:26](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:26) sets their receipt links to NULL.

   **Concrete failure:** a normal successful small test remains for 90 days. Pruning removes its attribution; teardown thereafter refuses, and N-137 considers the receipt non-test. **DBT:261–269** tests this refusal but provides no recovery.

   **Safe resolution:** retain these run identities until teardown completes, or preserve durable attribution before pruning. For existing orphans, restore a link only from independently verifiable historical evidence through an audited steward recovery. Without that evidence, preserve the receipt and its blocking classification. Do not weaken the NULL rule or use the current manifest as retrospective proof.

4. **P2 — Successful execution does not establish the N-137 end state.**  
   **TD:127–150** validates ten registry fields but not `catalog_status`, dependents, or runtime evidence outside the pinned chart.

   **Concrete failure:** another asset acquires a dependency on v5 while the test is staged. Teardown deletes the candidate and reports success, but N-137 still includes v5 because it has a dependent. A `RETIRED` registry row or non-test evidence on another chart also escapes this validation.

   The actual conditions are in [definitions.ts:210–241](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/src/lib/nirmana-elevation/definitions.ts:210); its receipt/run-assets evidence query is **asset-wide**, without a chart predicate, at lines 288–292. Validate the applicable monitor conditions before deletion and before claiming the staged state was restored.

5. **P2 — Production FK/trigger effects can escape the pinned chart.**  
   **TD:272–273** rejects receipts of another asset attached to an owned run, but does not reject receipts of the **same asset on another chart**. Deleting the parent at **TD:352** would NULL those surviving receipts’ links. The production FK constrains `build_id`, without enforcing chart equality.

   Separately, restoring an active registry row at **TD:380** fires migration 596’s invalidation trigger, which updates freshness for that asset **across all charts**—[migration 596:61–80](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:61).

   **Concrete failure:** another chart has a v5 freshness row; restoring this test’s active registry row changes that other chart’s freshness. The promise at **TD:49–50** that every other chart is preserved is therefore unconditional beyond what the code enforces. Refuse conflicting out-of-scope state, and test these production effects.

6. **P2 — Failure reporting can falsely assert that no commit happened.**  
   **TD:394–399** always says “Nothing was committed,” including errors after **TD:382**.

   **Concrete failure:** COMMIT succeeds, then connection cleanup fails; the operator receives a failure message denying the completed deletion. I reproduced this offline with an injected close failure: **one fake commit**, exit `1`, and “Nothing was committed.” A lost COMMIT acknowledgement also leaves the outcome uncertain.

   Track transaction phase and distinguish confirmed rollback, confirmed commit, and unknown commit outcome while retaining credential-safe diagnostics.

**A. Round-1 disposition**

| Finding | Round-2 status | Evidence |
|---|---|---|
| P1-1: stale checks/no locks | **Resolved for cooperating orchestrator/writer paths** | TD:153–163, 366–388 |
| P1-2: wrong run-scope predicates | **Resolved** | All active chart runs: TD:237; membership: TD:245–252 |
| P1-3: ownership and NULL receipts | **Partly resolved** | Historical-run-only acceptance removed; NULL refused at TD:285. Remaining ownership defect above |
| P1-4: other assets’ bookkeeping | **Resolved for the original mixed-asset cases** | TD:261–278; cross-chart dependent-reference gap remains |
| P1-5: legacy deletion | **Resolved** | Guard-only at TD:297–308; absent from deletion list |
| P2-6: credentials in connection errors | **Resolved for CLI invocation** | TD:418–425 catches connection failures and suppresses exception text |
| P2-7: execution intent/environment source | **Resolved** | TD:408–419; environment-only connection at TD:362 |
| P2-8: surviving freshness | **Resolved for pinned chart/asset** | TD:350 |
| P3-9: ineffective drift guard | **Resolved for deletion-table order** | UT:585–618 executes real helpers and detects an added table |

**B. Locks and transaction**

The order is consistent:

- Scheduler takes the session-level `hashtext(chart)` exclusion lock before dispatching workers: [runner.py:1313](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/python-sidecar/pipeline/orchestrator/runner.py:1313).
- Workers take the distinct Gochara transaction lock before chart writes: `ka_gochara_v5.py:419, 873–879`.
- Teardown takes scheduler exclusion first, then Gochara: **TD:157–163**. The first attempt is non-blocking; the second has a 10-second lock timeout.
- The database helper also refuses non-READ-COMMITTED transactions: [migration 1153:430–456](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td2/platform/migrations/1153_gochara_sky_event_substrate.sql:430).

All execution-path ownership checks, DELETEs, registry UPDATE, and validation occur within those locks and one transaction. There is one explicit commit. Exceptions roll back; connection cleanup releases the session lock.

I found no lock-order inversion with the normal scheduler/writer path. This is **not a universal deadlock guarantee**: migration 1240 documents tuple-before-trigger lock hazards for other callers, and watchdog pruning does not take these advisory locks. Lock timeout bounds lock waits, not connection establishment or total query runtime.

**C. Complete direct mutation scope**

All chart predicates below use `482012f1-710e-4a25-994a-93821f5871aa`.

| Mutation | Scope and assessment |
|---|---|
| Receipts, TD:349 | Exact chart + `ka_gochara_v5`; every partition, no generation column |
| Freshness, TD:350 | Exact chart + asset; every partition |
| Run-assets, TD:351 | Selected owned run UUIDs; exclusivity checked first |
| Runs, TD:352 | Same UUIDs; surviving dependent FKs can be SET NULL |
| Throughput, TD:353 | Exact chart + asset |
| Windows → records → contacts, TD:91–94, 354–355 | Exact chart + `5.0`; memberships/prerequisites cascade |
| Coverage, TD:95 | Exact chart + `5.0` + `event_class` only |
| Intervals → obligations → path pins → inventory → snapshot, TD:97–102 | Exact chart + `5.0`; verification rows cascade |
| Manifest, TD:104 | Exact chart + `5.0`, after candidate/stamp checks |
| Registry, TD:380 | Global v5 row; `is_active=false`; cross-chart freshness trigger applies |

No direct legacy-table DELETE remains. Published, sealed, and authoritative `5.0` are refused at **TD:207–234**; other manifest lifecycle states are refused at **TD:321**. Sealed-write triggers provide an additional backstop. I found no normal cooperating path through these guards that deletes sealed output.

**D–G. End state, fidelity, and operator safety**

For the intended valid fixture, successful execution removes receipts, freshness, throughput, selected test runs and children, the listed output/inventory chain, and **the manifest itself**. It retains the registry row and makes it inactive. Other registry drift causes refusal rather than repair.

This does **not** mean every `5.0` row disappears: on-demand coverage and global substrate remain intentionally; `body_target` coverage is also outside this script’s deletion/count set.

N-137 accepts **zero evidence or exclusively linked test evidence**—it does not require complete absence. This script aims for zero evidence on the pinned chart, but finding 4 prevents an unconditional monitor-conformance claim.

Dry-run closes its connection and makes zero explicit commits, but fails the requested same-statements rehearsal. CLI intent and environment-only DSN handling are corrected. Credential suppression is corrected; commit-outcome reporting is not.

**H. Tests and verification limits**

I ran the offline suite: **54 passed, 1 skipped**. `git diff --check` passed. Additional in-memory probes demonstrated malformed-stamp acceptance, dry-run/execution divergence, and incorrect post-commit reporting.

The added database tests contain useful discriminating cases for locks, a receipt committed while waiting, mixed runs, NULL receipts, rollback, active-registry restoration, repeat execution, and populated cascades. **I did not execute them.**

Material gaps remain:

- **DBT:41–55** substitutes simplified bookkeeping tables and omits the production registry invalidation trigger and other run-reference FKs.
- **DBT:76–81** and the populated test stamp manifests manually with triggers disabled; they do not exercise the real stamped producer or the manifest/snapshot crash boundary.
- Migration **1304** and the dispatch script are absent here; **UT:416–421** skips their parity check.
- Missing cases include complete stamp validation, mismatched snapshot ownership, global N-137 conditions, cross-chart effects, intended steward-role privileges, and commit-outcome uncertainty.

**Not verified:** PostgreSQL execution, production schema/grants/data, actual concurrent behavior, related main-branch slice implementation, migration-1304 parity, or CI results. No database or network access was used. No files were modified.

