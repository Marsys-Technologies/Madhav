VERDICT: REJECT

Reviewed `2703c6723..4f9ccfafc1f43adf304ed7ad10c93bd0cd1e7bd9`, restricted to the requested changes. The binding contract and correction govern this verdict.

The inspected stamp, verification, publication and serving protections remain intact. The blockers concern changes to ordinary builds, incomplete collection of defects, incorrect measurement records, horizon rules and teardown compatibility.

**Blockers**

1. **The horizon change escapes the measuring-build boundary.**  
   [ka_gochara_v5.py:598](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:598) replaces the non-slice fallback with database derivation. The real runner supplies only `chart_id` and `birth_params`, so this affects its ordinary build path: [asset_runner.py:1119](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1119).

   **Concrete input:** no slice marker; normal runner configuration; birth `1984-02-05`; first fully dated event `1998-02-16`. Previously the horizon ended `2026-04-17`; now it ends `2084-02-05`, depends on `life_events`, and gains `horizon_basis`. An unusable log now prevents an ordinary build.

   **Answer to the DEFAULT_HORIZON question:** no, an unconfigured non-slice build no longer uses it. The constant is now primarily the staging validator’s bound. MB-1 authorizes the measuring horizon and changes to slice validation; it does not settle the general horizon question expressly left open in OO-1. Isolate the measuring behavior or obtain a separate ruling for ordinary builds.

2. **`sink_all` still aborts on invented contacts and anomalies, sometimes without recording the defect.**  
   [contact_certify.py:200](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/services/gochara_kernel/contact_certify.py:200) expressly excludes anomalies from collection. Lines 243–246 classify any ledger-touched stretch as `contact`; lines 273–284 generate mismatch strings without corresponding invented/boundary-anomaly records; lines 325–326 raise under both policies.

   **Concrete input, reproduced:** Venus conjunction `point:120.0`, constant longitude `180°`, no reconstructed intervals, and a ledger contact `[2026-02-28, 2026-03-02)`. Under `sink_all`, the result contains an invented-contact problem and **zero stretch records**, then certification raises.

   A ledger episode covering only half a reconstructed interval likewise becomes `contact` and subsequently raises. MB-2.1 requires `invented` and `anomaly` to be recorded and the class to continue. The writer’s `finally` cannot emit a record the certifier never created.

3. **The emitted record schema, IDs and vocabulary contradict MB-2.2–2.3.**  
   [stretch_sink.py:77](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/services/gochara_kernel/stretch_sink.py:77) uses float interpolation rather than `%.3f`. Lines 83–89 omit required `stretch_ordinal` and `station_at`; lines 103–104 use `None` for residence rather than the prescribed `0.000` ID component.

   **Concrete input, independently recomputed:**  
   `near_miss | venus | conjunction | point:120.0 | orb 1 | ruled horizon | ordinal 1`

   - Contract ID: `407dbb76-bd2c-8990-82fd-08a51dcf1497`
   - Actual ID: `308a7c71-e53c-815a-a35e-a4bfc44a10d0`

   The table also emits `arc_index_station_inside_stretch` and `two_or_more_ledger_episodes`, whereas the contract requires `arc_index_station_inside` and `multiple_ledger_episodes`. It lacks `invented/ledger_contact_not_reconstructed` and `anomaly/boundary_pairing_mismatch`. Extension detail is an object rather than the prescribed closed string value.

   An independent implementation of the written recipe cannot agree with these records.

4. **Station-seam counts include stretches with no ledger contact.**  
   [stretch_sink.py:108](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/services/gochara_kernel/stretch_sink.py:108) emits a seam whenever the station callback returns anything. It neither requires an overlapping contact nor supplies the required station/full-interval evidence.

   **Concrete input, reproduced:** longitude `120.3 + 0.02 × d²`, where `d` is days from `2026-03-01`; target `120°`; no ledger contacts; station at the minimum. Output contains both `near_miss` and `station_seam`, with `episode_count=0`, `full_interval=null`, and no `station_at`.

   MB-2.3 requires at least one overlapping contact. This inflates a number the build specifically exists to measure.

5. **Birth identification remains broader than your domain-only requirement.**  
   [horizon.py:242](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/services/gochara_kernel/horizon.py:242) accepts either `domain == other/birth` **or** provenance subcategory `birth`.

   **Concrete input, reproduced:** a row dated `1984-02-05` with `domain="other/other"` and `provenance_subcategory="birth"`, plus the valid 1998 event. Derivation succeeds and records `column_used="provenance.subcategory"`.

   The original contract allowed this alternative; your stated boundary and the patch narrow identification to `other/birth` pending the production read. The test at `test_horizon_derivation.py:151` currently preserves the broader behavior.

6. **The required mid-build horizon-change refusal is bypassed on the pinned chart.**  
   [ka_gochara_v5.py:584](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:584) always applies the ruling guard during derivation. `_test_slice` invokes that before `_live_basis_for_check` can compare the pinned basis.

   **Concrete input:** create the manifest with the 1998 first event, then remove that event so 2007 becomes first. The next substep refuses `horizon_derivation_disagrees_with_ruling`, not the required `horizon_basis_horizon_changed`.

   This remains fail-closed, but violates the named operational interface in MB-1.5. The test reaching the required token uses an **unpinned chart**, which the actual writer rejects: [test_mb_horizon_shape_guard.py:196](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/tests/l3/gochara/test_mb_horizon_shape_guard.py:196).

7. **The shared validator changes teardown eligibility for previously accepted candidates.**  
   Teardown’s stamp proof calls the current writer validator at [v5_small_test_shared.py:148](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/scripts/v5_small_test_shared.py:148), including its reconstruction fallback at line 167.

   **Concrete input:** an owned, unsealed `one_class_full` candidate with a valid original marker and matching digest, horizon `[1998-01-01, 2026-04-17)`, and otherwise satisfied teardown preconditions. The new validator rejects that formerly valid marker because it now requires the 2084 endpoint.

   This does not widen deletion, but it changes a previously accepted teardown precondition and can strand an older small-test candidate. Preserve historical stamp validation for teardown while validating new dispatches against the new horizon.

**Clause-by-clause assessment**

“Outside A” means the clause belongs to the verifier/steward and is not an implementation omission in this builder PR.

| Clause | Assessment |
|---|---|
| MB-1.1 ruled pair | **Implemented** for measuring validation; ordinary-build isolation is contradicted by blocker 1. |
| MB-1.2 detector + patch | **Partly.** Correct real columns, chart filter, `datetime_iso`, conjunction, no `event_id` fallback, empty-log distinction and named edge refusals. Birth predicate remains too broad. |
| MB-1.3 dispatch/writer | **Implemented** for new markers: all 26 classes, exact full horizon, shared pure validator, dry-run sentence. Historical teardown compatibility fails. |
| MB-1.4 pinned basis | **Implemented.** Thirteen consumed fields, deterministic ordering, canonical digest and optional vector component. |
| MB-1.5 drift | **Partly.** Same-horizon edits report changed IDs and retain the pinned vector; changed-horizon refusal has the wrong token on the actual chart. |
| MB-2.1 collection policy | **Contradicted** for invented contacts/anomalies and touched mismatches. Environment exceptions remain exceptions. |
| MB-2.2 record | **Contradicted:** fields, ID formatting and ordering protection. |
| MB-2.3 closed table/count semantics | **Contradicted:** missing entries, wrong words and station false positives. |
| MB-2.4 logging | **Partly.** Logging levels, per-record lines, summary digest and `finally` exist; some required records never exist. Steward export is outside A. |
| MB-2.5 agreement | **Not established.** Independent recount belongs to B; emitted IDs cannot meet it. |
| MB-3.1–3.4 regression capture | **Outside A; not verified.** No golden capture or teardown authorization established. |
| MB-4.1 cap | **Implemented in dispatch/teardown expectations:** 28,800 seconds. Migration readback, projection and Cloud Run timeout unverified. |
| MB-4.2 fired cap | **Partly evidenced by test design**, with limitations below; not executed. |
| MB-4.3 state guard | **Implemented by source inspection** and pure tests. |
| MB-4.4 lit-over-error | **Preserved known residual.** B’s run-first verdict remains necessary. |
| MB-4.5 terminal teardown | **Outside A; not verified operationally.** |
| MB-4.6 restart from zero | **Preserved.** Production caller supplies no completed-key set. |
| MB-4.7 success census | **Outside A’s verdict responsibility; full success not demonstrated.** |
| MB-5.1 reader refusal | **Implemented in the inspected existing paths.** |
| MB-5.2–5.3 share conventions/P4 | **Outside A; no measurement validation performed.** |
| MB-5.4 all-null policy | **Preserved.** No numerical scoring qualification established. |
| MB-5.5 scope statement | **Outside A’s report responsibility.** |
| MB-6 acceptance | **Outside A**, but missing sink categories prevent its required counts. |
| MB-7 report | **Outside A; not verified.** |
| MB-8 sitting sequence | **Not executed.** Current builder defects prevent readiness; launch/capture/teardown gates remain outstanding. |

All 15 horizon refusal codes are present and exercised by the pure detector tests: the six horizon boundary/anniversary codes, birth identification, confidence, shape, missing date, chain resolution, shape sensitivity, missing candidate-first `lel_id`, nonempty-undated log, and ruling disagreement. `lel_dating_rules_disagree` is correctly withdrawn.

`asset_not_building` is present and reachable. The exception is the actual pinned-chart route to `horizon_basis_horizon_changed`, described above.

`stretch_sink_unparseable` and `stretch_sink_summary_digest_mismatch` are reachable. `unknown_kind_or_reason` is absent from the supplied sink helper: parsing `{"schema":"stretch_sink/1","kind":"banana","reason":"banana"}` succeeds. `sink_disagreement`, golden, acceptance, report and run-verdict refusals belong to B/S; their absence here is not an A blocker.

**Stamp protection and behavior boundaries**

A correctly staged `all_classes_full` run receives both `stored_scope="test_slice"` and the marker component at [ka_gochara_v5.py:1082](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1082). Scope normalization creates a separate in-build copy; it does not overwrite the stored stamp.

I found no new bypass in:

- `verification_job.py:178–184`: rejects either stamp.
- `ledger.py:623–636, 741–742`: explicit refusal and conditional publication update.
- `seal_flow.py:57–72`: publication precedes sealing.
- `register_gochara_contact_ledger.ts:315–354`: rejects the slice before serving contacts.

Literal vector identity across revisions is not demonstrated. Configured **non-slice** horizons retain the optional-component behavior—no `horizon_basis` is added—but implementation hashes necessarily change. Existing slices with real birth parameters now acquire a basis and use derived outer bounds; MB-1.3 expressly requires the latter.

One baseline distinction matters: **the other two slice shapes already tolerated certified grazes**. This PR preserves that behavior; non-slice grazes and ordinary-policy unresolved stretches/omissions still refuse. The new `sink_all` selection itself is confined to `all_classes_full` at writer line 1250, although structured logging is added to every slice.

**State guard and fired-cap evidence**

The guard uses `ctx.db_conn`, performs a plain `SELECT`, skips dry runs and absent rows, and writes no throughput state. It adds no throughput row lock. Its savepoint protects the caller from a failed read; the Python refusal occurs after that read completes.

The runner’s `writer_exec` savepoint remains available: [asset_runner.py:888–898](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:888) rolls back to it, then the outer failure handler rolls back and marks the asset error. I found no writer commit, close, connection ownership change or throughput write. Database deadlock behavior was not experimentally verified.

The fired-cap test at [test_mb_real_db.py:162](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA2x/platform/python-sidecar/tests/l3/gochara/test_mb_real_db.py:162) checks **post-process** `failed/error/error` states and an incomplete substep prefix. It does **not** prove:

- that the evicted worker reached another substep;
- that this substep raised `asset_not_building`;
- that throughput was never transiently lit.

Removing the guard could still leave this test passing because process exit kills the daemon worker. Its fixture is `one_class_full`, a 23-step plan, despite the “298+” docstring. Verdict assertions use states, but an additional assertion depends on the scheduler’s `TIMEOUT` message; stored error text is not used as the verdict.

The frozen finish path can still overwrite error after a timeout during the final in-flight substep. That is the acknowledged MB-4.4 residual, not a new PR defect.

**Every direct dispatch/teardown change**

| Change | Judgment |
|---|---|
| Dispatch documentation and expected registry cap: 7,200 → 28,800 | Authorized by MB-4.1; live migration parity unverified. |
| New `SLICE_MARKER_KEY` constant | Appropriate extraction for report lookup. |
| Add `all_classes_full` to supported runs | Required. |
| Extend default classes/full-horizon handling to the new shape | Required; still passes through the writer validator. |
| Update marker documentation, usage example, argument help and missing-horizon error text | Appropriate descriptions of the new shape. |
| Add the dry-run horizon explanation | Required by MB-1.3; no detector/database derivation added to dispatch. |
| **Teardown’s sole direct change:** expected cap 7,200 → 28,800 at line 127 | Authorized. No direct deletion, ownership, locking or refusal logic changed. |

The indirect teardown validator change is blocker 7. Migration 1304 is absent from this checkout; its parity test explicitly skips when absent.

**Tests and follow-up hardening**

I ran the three new pure suites—horizon derivation, horizon/shape guard and stretch sink—with bytecode, cache and plugin loading disabled and `--noconftest`: **98 passed**. No database was used.

Useful tests cover the corrected dating conjunction, refusal inputs, consumed-row digest, same-horizon drift, marker shape and basic state guard. However:

- `test_mb_stretch_sink.py:206–209` asserts the **wrong `1.0` ID recipe**.
- Lines 237–268 assert the wrong vocabulary and require behavior contrary to collection mode.
- Lines 283–289 inspect source strings; they do not execute a whole class through the writer.
- The reversal test reverses records **after ordinals are assigned**. Reversing two reconstructed intervals before `compare_contact_sets` swaps their ordinals and IDs. The real reconstruction currently returns sorted intervals, masking this helper weakness.
- The A53 fixture now injects `horizon` at line 136, which the production runner never supplies, concealing the ordinary-build regression. The invented `birth_date` key is fixed.
- C47 correctly uses the real runner shape, but asserts only an initial successful prefix and explicitly does not prove a completed slice.
- The new C38 test manually constructs error and lit-over-error states. It tests teardown handling, not whether the runner can produce those states.

The mutation harness was **read, not run**. Its baseline check and restoration logic are useful, but any nonzero pytest result counts as a killed mutation—including unrelated errors. Some mutations merely produce an `AttributeError`/`IndexError`; others enforce the incorrect anomaly policy. Mutation survival statistics would not establish contract conformance.

Follow-up hardening can add deterministic worker synchronization for the timeout test, distinguish assertion failures from broken mutants, and make the local sink parser validate complete records and summary counts.

The owner question decided prematurely is the ordinary-build horizon behavior. I found no new decision on numerical scoring, DVI, publication authority or unresolved-stretch acceptance.

**Not verified:** databases, production birth vocabulary, deployed registry/migrations, real ephemeris execution, CI results, live grants, runtime timeout races, independent B recounts, golden capture, deployment or teardown execution. No network or database access occurred, and no files were modified.

