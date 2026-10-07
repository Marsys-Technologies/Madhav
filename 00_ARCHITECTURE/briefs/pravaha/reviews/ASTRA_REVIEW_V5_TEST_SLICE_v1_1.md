VERDICT: REJECT

Reviewed `9c1f429702181f135d6f265c2950c9d6c08f6e0a...fdafa1c694ff1f25efdbc3eb42e7220262ec2541`. The four round-1 defects are addressed, but publication exclusion is incomplete and an existing required CI test now fails.

**P1 — Direct publication does not reject a sliced candidate.**

[ledger.py:625](platform/python-sidecar/services/gochara_kernel/ledger.py:625) checks the manifest’s status, then [line 663](platform/python-sidecar/services/gochara_kernel/ledger.py:663) changes it to `published`. It never reads `stored_scope` or `test_slice`, checks verification, or requires a seal.

The database boundary guard does not close this path: [1240_gochara_window_verification_gate.sql:965](platform/migrations/1240_gochara_window_verification_gate.sql:965) applies its refusal only when a seal already exists. Migration [1216:104](platform/migrations/1216_gochara_contract_builder_grants.sql:104) grants the builder publication-table UPDATE.

**Failure scenario:** after a successful test slice, a caller uses the existing `ledger.publish(conn, chart, "5.0")` helper directly. It publishes the slice without invoking the protected seal flow. Subsequent full rebuilds also refuse because the manifest is no longer a candidate.

I reproduced the Python path using an in-memory connection: it returned successfully and changed `candidate → published` without querying the stamp or seal. Database-trigger conclusions are source inspection, not database execution.

**Required:** reject sliced vectors at the publication boundary independently of the seal workflow, with a regression through `ledger.publish`. This is an existing boundary that the new mode’s exclusion contract must cover.

**P1 — The required replacement-chain CI suite has a deterministic regression.**

The new unconditional marker lookup at [ka_gochara_v5.py:565](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:565) reaches `ctx.db_conn.execute()` even for connection-free dry-run planning.

The existing [test_a55_replace_chain.py:184](platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:184) passes `db_conn=None, dry_run=True`. It now fails with:

```text
AttributeError: 'NoneType' object has no attribute 'execute'
```

The supplied base returns the expected 298-step plan for that same context. [ci.yml:1188](.github/workflows/ci.yml:1188) explicitly runs this test.

**Required:** reconcile the planning test with the new database-backed marker lookup—preferably supply a marker-free fake connection while retaining the snapshot-order assertion.

**P2 — The registered contact-ledger reader omits the slice designation.**

[register_gochara_contact_ledger.ts:272](platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:272) accepts an explicitly requested generation without resolving authority. Its manifest query at line 304 omits the input vector; its coverage query at line 414 reads the shared coverage table; line 446 returns `status: "ok"`.

**Failure scenario:** an authorized caller requests `gochara_contact_ledger_get` with `generation: "5.0"` after a slice. The response includes slice coverage without `stored_scope`, the marker digest, or a test-slice refusal. It retains `manifest.status: "candidate"`, but cannot distinguish this candidate from an ordinary full-build candidate.

I reproduced that response with the actual TypeScript function and a mocked transport. No network was used. This does **not** demonstrate v5 contact-row leakage: this reader queries the legacy contact table and returns an empty contact list alongside the slice’s coverage.

**Required:** reject test slices here, or expose them through an explicitly labelled diagnostic response that cannot represent normal build coverage.

**A. Round-1 disposition**

| Finding | Disposition | Evidence |
|---|---|---|
| Slice contacts survive a full rebuild | **Resolved under whole-build replay** | [Writer:759](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:759) unconditionally replaces the chain at snapshot. [RecordStore:577](platform/python-sidecar/services/gochara_kernel/record_store.py:577) deletes all generation contacts, including shared contacts and orphans; line 758 compares conflicting contact rows. |
| Marker not bound to live-input checking | **Resolved** | [Writer:431](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:431) derives explicit expectations from the validated run marker. Normalisation at line 339 requires the exact scope/schema/digest pair. |
| Malformed manifest/timestamp overflow | **Resolved** | [Writer:217](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:217) refuses malformed containers; line 253 catches UTC-conversion overflow. |
| Explicit null horizon changes default behaviour | **Resolved** | [Writer:351](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:351) preserves an explicit `None` without a marker and refuses it under a marker. |

The database-backed transition tests were inspected, not executed.

**B/F. Default-path equivalence**

With a usable connection and no marker, the 298-step plan matches the supplied base exactly, including labels. Default and explicitly supplied horizons retain main’s behaviour. The frozen default vector’s canonical JSON also matches the base’s serializer, with either an absent or `None` `test_slice` input.

Literal production vector/digest equality across commits is **not** preserved: the writer belongs to the implementation digest, so its changed source moves `implementation.evaluation` and downstream identities. The aggregate implementation pin changes from `8c08a6fd…` to `71b7cf87…`.

No row, SQL/JSON-null manifest, or absent marker key selects the default. A **present marker with null or garbage content refuses**. A malformed non-null manifest container also refuses. The connection-free planning regression above is another exception to the blanket “byte-for-byte behaviour” claim.

**C. Marker trust**

The writer reads the marker exclusively from `build_runs.plan_manifest` using `ctx.build_id` ([writer:195](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:195)); configuration cannot inject it.

The runner validates the whole manifest digest before execution ([runner.py:243](platform/python-sidecar/pipeline/orchestrator/runner.py:243)). [Migration 595:39](platform/supabase/migrations/595_nirmana_frozen_run_manifest.sql:39) prevents subsequent mutation of a non-null manifest, plan, or digest.

Validation enforces the exact four-field schema, named run, scored-class membership and uniqueness, timezone-aware ordered bounds inside `DEFAULT_HORIZON`, and the two permitted shapes ([writer:264](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:264)). `all_classes_1y` permits a positive interval **up to 366 days**; `one_class_full` requires the full default horizon. The component binds SHA-256 of the marker’s canonical JSON.

There is no owner signature in that component. Ownership approval remains a dispatch/DB-access responsibility. This diff adds no production marker-writing interface; the ordinary server-side manifest construction omits it (`runPreparation.ts:338`). Live grants and owner approval were not verified.

**D. Verification, sealing, publication and serving**

| Path | Result |
|---|---|
| Verification job | Refuses intact slice scope through [verification_job.py:204](platform/python-sidecar/services/gochara_kernel/verification_job.py:204) → `input_vector_verifier.py:318`. |
| In-build class verification | `inventory_verifier.py:66` rejects unknown scope; the writer returns `UNVERIFIED` without an attestation at `ka_gochara_v5.py:835`. |
| Seal brief | Requires complete, current attestations (`seal_brief.py:350`). **No direct candidate-scope check:** the SQL scope arm selects only published manifests (`1232…sql:105`). Honest slices cannot obtain the required verifier attestations. |
| Approved seal flow / SQL seal | Approval is recomputed before publication (`seal_flow.py:37`). Published-scope checking rejects `test_slice` through the seal’s completeness gate (`1232…sql:108`); transaction failure rolls publication back. |
| Direct publication | **Unchecked: P1 above.** |
| Python coverage-response helper | Labels unknown scope as refused (`scope_response.py:229`), but this helper is not used by the TypeScript ledger reader. |
| Registered ledger reader | **Unchecked: P2 above.** |
| Authority-based legacy window reader | Filters by authority (`register_gochara_windows.ts:707`). This writer neither flips authority nor writes the legacy window projection; the reader itself has no slice check. |

**E/I. Transitions and production-data integrity**

Successful whole replays retain the same head, including exactly one snapshot before every class-writing step. The runner supplies no `completed_keys` (`asset_runner.py:1179`). Consequently, slice→full, full→slice and slice→different-slice all reach the same generation-wide cleanup. Sealed and non-candidate generations are refused before deletion.

The horizon guard correctly compares the manifest against the **effective marker horizon** ([writer:411](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:411)); I found no legitimate-slice mismatch or accepted mixed-horizon continuation.

“Always consistent” needs qualification: manifest and snapshot commit separately (`asset_runner.py:915`). A failure between them can leave the new manifest beside the previous chain. Snapshot-vector and inventory-horizon comparisons reject that state at the combined candidate gate (`verification_job.py:490–503`). A successful retry replaces it. This interrupted boundary deserves an explicit regression, particularly given the unchecked reader.

I found no additional deletion of L1 data or global identities. The intended deletion remains the unsealed chart×generation output chain.

**G/H. Tests and generated artifacts**

The new production-caller stamp tests are discriminating. Transition coverage is narrower than the author’s wording: `test_c46_slice_transitions.py:64` executes inventory, coverage and records for two classes; its slice helper always uses `all_classes_1y`. It does not exercise class-A→class-B `one_class_full` transitions, window execution, or complete stored-row/stamp equality. The reused comparison checks selected contact columns, record counts and coverage horizons. The default verification control also accepts unrelated early refusals (`test_c46_slice_transitions.py:155`).

The implementation lock, writer digest, census content/source hashes and brief transport goldens checked consistently. Decoded golden changes concern identities, digests and execution metadata; substantive geometry did not change. No unrelated source changes were found. CI includes both new suites, but has the reproduced failure above.

**Validation limits:** 78 slice cases and 72 ancillary offline cases passed; one existing test failed. Database, real-ephemeris and temporary-file-dependent tests were excluded or blocked. I did not verify deployed migrations/grants, live CI, production dispatch, or database enforcement. No files were modified; no database or network access occurred.

