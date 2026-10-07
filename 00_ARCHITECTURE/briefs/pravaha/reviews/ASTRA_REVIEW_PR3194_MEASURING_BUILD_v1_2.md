VERDICT: REJECT

**Not mergeable yet.** B3 and B4 are resolved. The implementation-identity changes and unconditional state guard are accepted under the steward rulings. The remaining blockers are the two required regression tests: neither actually compares HEAD’s behavior with main.

Reviewed local `origin/main` **`2c117ba1a` → HEAD `01c181cc0`**, including `57c45f598..HEAD`. No files modified; no database or network access.

**Blockers**

1. **B1’s test compares HEAD with HEAD, not main.**  
   [test_mb_horizon_shape_guard.py:476](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/tests/l3/gochara/test_mb_horizon_shape_guard.py:476) calls the current `assemble_vector` for both vectors. The only input difference is two synthetic module hashes. Although line 479 compares every non-implementation component, both sides share any regression in HEAD’s assembly. Line 469’s window-module assertion is also a self-comparison.

   **Concrete replay:** using its existing `_mutate("base")` input, I changed HEAD’s assembler **in memory only** to return `stored_scope="WRONG_ORDINARY_SCOPE"`. The new test still passed.

   **Required correction:** compare against an independently frozen main result or main’s actual implementation, using identical ordinary inputs and each revision’s real implementation hashes.

2. **B2’s healthy-build test proves only guard transparency for mocked `rules` at HEAD.**  
   [test_mb_horizon_shape_guard.py:503](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/tests/l3/gochara/test_mb_horizon_shape_guard.py:503) models “main” by removing HEAD’s guard. Both executions otherwise use HEAD, stub rule persistence, and execute only `rules`.

   **Concrete replay:** markerless configuration, real birth-parameter shape, throughput `building`; I appended `[ORDINARY REGRESSION]` to the writer’s returned notes **in memory only**. Both sides changed together and the new test still passed. Changes in manifest, snapshot, record, window or verification execution are outside this test altogether.

   **Required correction:** use main-derived expected operations/results for the ordinary execution paths. Retain the useful separate tests proving dry-run skipping, absent-row tolerance and refusal before rule seeding.

These are **test defects introduced this round**, not renewed objections to the ruled implementation changes.

**B3 and B4 replays**

| Finding | Result and evidence |
|---|---|
| **B3(a): station instant** | **Resolved.** With checksum-verified local ephemeris files, Mercury’s February 2026 sink and the station row prepared by the real storage path both contain **`2026-02-26T06:47:30.707813+00:00`**. The spline instant remains `06:47:43.801163`, confirming the former **13.093350-second** discrepancy is removed. See [ka_gochara_v5.py:474](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:474), `substrate.py:299` and `substrate.py:572`. This captured would-be INSERT parameters, not database rows. |
| **B3(b): full extent** | **Resolved for the reported input.** `120 − 0.5 + 0.02d²`, horizon starting February 28: `full_interval` now starts **`2026-02-20T08:09:14.589844+00:00`**, while `horizon_interval` starts February 28 and clipping is `["start"]`. See [contact_certify.py:229](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/services/gochara_kernel/contact_certify.py:229) and `stretch_sink.py:149`. A separate constant-`120.3°` replay produced `full_interval=null`, `detail="exceeds_1500_days"`, clipping `["start","end"]`, without mocking the extent detector. |
| **B4: birth without LEL ID** | **Resolved.** Original `birth-no-id` row plus the valid 1998 event returns `rows_without_lel_id=[{"event_id":"birth-no-id","event_date":"1984-02-05"}]`; the horizon remains the ruled pair. [horizon.py:323](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/services/gochara_kernel/horizon.py:323) now reports from all rows. |

I found no additional production-code defect introduced by the round-3 changes.

**Ordinary builds: actual main comparison**

My independent comparison loaded main’s actual serializer and hashed each revision’s actual module sources. Differences were **exactly**:

```text
implementation.evaluation
implementation.geometry
```

Every non-implementation component matched; neither vector contained `horizon_basis`. `implementation.window` matched. The newly included modules are `stretch_sink` under geometry and `horizon` under evaluation.

The actual ordinary plans matched at **298 substeps**, with horizon **`[1998-01-01, 2026-04-17)`** and no LEL reads. Actual main-versus-HEAD `rules` results matched, with the guard query added at HEAD.

| Changed path with no slice marker | Behavior at HEAD |
|---|---|
| Writer imports/constants/caches, `ka_gochara_v5.py:58`, `:154`, `:470` | Additional modules and definitions load; no horizon derivation or station computation. Implementation identity changes as intended. |
| Marker parsing/validation, `:304`, `:333`, `:411` | `_test_slice` still returns `None` before the new shape logic. |
| Horizon helpers, `:585`, `:628`, `:641`, `:652` | Derivation is unreachable; ordinary default and explicit-horizon behavior remain unchanged. |
| State guard, `:533`, `:1052` | Deliberate additional read/savepoint handling and non-building refusal. |
| Manifest, `:1124`, `:1139` | Measuring-domain check is skipped; basis argument is `None`. |
| Live input check, `:813`, `:843` | No LEL derivation; absent basis remains absent. |
| Certification/logging, `:1303` | Both sinks are `None`, policy is `raise`; no structured sink emission, added note is empty. |
| Certifier, `contact_certify.py:303`, `:380` | Default-policy validation executes; collection and full-extent work are skipped. Six main-versus-HEAD cases matched in both problems and position-call sequences: matching, omitted, half-covered, shifted, invented-extra and overlapping episodes. |
| Vector assembly/build/replay/live, `input_vector.py:223`, `:449`, `:518`, `:537` | Optional basis remains absent; implementation identity changes as ruled. |
| Station reporting helper, `substrate.py:299` | Not called by ordinary builds; existing station storage calculation is unchanged. |

**No other markerless behavioral difference found in these paths and replays.** This is not evidence of a completed database-backed ordinary build.

**State guard against the real runner**

The normal lifecycle is compatible with the guard:

| Runner stage | Throughput state |
|---|---|
| Before writer entry | `run_asset` upserts `building` and commits: [asset_runner.py:1552](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1552), `:1579`. |
| Every healthy substep | `_drive_substeps` calls the writer at `:895`; heartbeat at `:909` updates timestamps/counts, **not state**; heavy-writer commit at `:915`. |
| Error/timeout committed | Error helpers commit `error`: `asset_runner.py:585`, `runner.py:502`, `:522`. A subsequent guard refuses. |
| Successful finish | Final state changes after substeps finish, at `asset_runner.py:1350`; there is no subsequent legitimate substep to refuse. |
| Probe/delta skip | Successful skip paths return without running writer substeps. |

I found **no false refusal caused by this normal lifecycle**. The guard does not commit or lock the throughput row. Dry runs skip it; absent rows proceed; present non-building states refuse before persistence.

Its limits remain:

- An error committed after the SELECT cannot stop that already-running substep.
- A timeout during the final substep leaves no next guard; the unconditional finish update can still overwrite `error`. This is the contract’s acknowledged finish race.
- It checks `(chart_id, asset_id)`, **not run ownership**. If a successor prematurely resets the row to `building`, an old worker can pass; a late old-worker error can also disrupt the successor. MB-4.5’s process-exit requirement remains necessary.
- Missing connection/table/row paths fail open as implemented. The real runner normally supplies the connection and row.

These are limitations of the approved guard, not grounds to scope it back to measuring builds.

**Teardown, validator and dispatch**

The requested two-file diff is empty. Git blob identities also match:

- `teardown_v5_small_test_job.py`: `73ce875cc715…` on both revisions.
- `v5_small_test_shared.py`: `cd6d2215f643…` on both revisions.

Every change to [dispatch_v5_small_test_job.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA4x/platform/scripts/dispatch_v5_small_test_job.py) is:

| Lines | Change |
|---|---|
| 67–79 | Documents the third shape, its horizon and default classes. |
| 116 | Adds measuring-build usage example. |
| 228–230 | Adds `SLICE_MARKER_KEY` and the third run choice. |
| 263–264 | Updates marker-builder documentation. |
| 278–283 | Defaults `all_classes_full` to `MEASURING_HORIZON`; preserves the older default and both-or-neither bound validation. |
| 352–358 | Updates CLI help. |
| 621–631 | Adds the dry-run horizon explanation. |

No direct changes to admission, ownership, locking, transaction handling, registry-cap checks or refusal predicates. Dispatch itself has **no round-3 delta**.

**Follow-ups**

- `dispatch_v5_small_test_job.py:622` still prints the database-derivation sentence for older shapes. Concrete input: `--run one_class_full --classes marriage`. That writer path does not derive its horizon from LEL.
- `ka_gochara_v5.py:643` still says ordinary vectors are byte-identical to main; update that comment to the restated requirement.
- The source documents the unconditional guard at `:1048`. The required **PR-body** wording was not available locally and was not verified.
- The supplied steward ruling retains the Suvarna merge hold; its release was not checked.

**Verification and limits**

**539 local tests passed; five database-backed tests skipped before connection under the offline guard.** Independent replays covered the original B3/B4 inputs, actual main vectors/plans/rules, default certification, and in-memory mutations exposing both test weaknesses. `git diff --check` passed; working-tree status remained unchanged.

Not verified: database concurrency or permissions, actual stored production rows, complete ordinary/measuring builds, Linux CI portability, deployed refusal gates, verifier agreement, golden capture, PR metadata, deployment or operational teardown. The source-rewriting mutation harness was not run.

