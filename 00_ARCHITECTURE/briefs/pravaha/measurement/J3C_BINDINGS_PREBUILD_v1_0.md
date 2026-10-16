---
artifact: J3C_BINDINGS_PREBUILD
version: "1.0"
status: BUILT_WAITING_ON_GATE — no measuring operation executed or accepted
produced_on: 2026-10-16
changelog: Initial A6 D-40 disabled measuring launch/rollback and teardown preparation.
---

# Measuring bindings prepared for phase 5

The executor's existing `measuring_dispatch` placeholder now points to
`fleet/measuring_launch.py`. Three new kinds are allocated by this job:
`measuring_dispatch_dryrun`, `measuring_teardown_dryrun`, `measuring_teardown`.
**All four are disabled.** Existing enabled kinds retain their states. The
small-test `all_classes_full` refusal remains in place (W4-SAFETY-03).

**(I) INTERPRETATION:** the prompt allocates these measuring-specific names to
J-3c/J-3d; no tracker child or operational acceptance is invented. The alternative
is an unbound proposal awaiting a further naming decision. These bindings are
built now but may land only under the campaign gate, reviewed source and phase
enablement process. They do not earn any J-3c/J-3d step or A5.2/A5.3 residual.

## Launch and staging rollback

Requests carry `item_id=J-3c`, canonical chart and only
`args={"run":"all_classes_full","classes":"all"}`. Builder capability is
required for both; launch also requires gcloud capability. Executor admission
retains the live lease, reviewed merged commit, request-digest-bound independent
pre-acceptance, backup/restore, required checklist rows, expiry, idempotency and
single production fence. MB-4.1's accepted run-1/run-2 projection <=23,040 seconds
and actual task-timeout readback >28,800 seconds remain pre-acceptance obligations
(`decisions/MEASURING_BUILD_CONTRACT_v1_0.md:88`); this job supplies neither.

The new dispatcher accepts only the writer's exact 26-class, 31,446-day ruled
marker. It reuses the existing guarded staging transaction through an explicit
internal interface; no request flag changes the small-test policy. The registry
stays inactive and candidate/published separation is preserved.

A dry run performs those actual writes then confirms rollback, emitting one
`ky.measuring_staging/1` proof bound to operation/request, arguments, manifest and
digest. The executor records it under `staging`; an exit code or preparation
preview is insufficient. Launch must cite this receipt and independent acceptance
as `dryrun_receipt`/`dryrun_acceptance`. Source, args and newly constructed manifest
must equal the accepted rollback, and the rollback must precede launch acceptance.

The launch wrapper stages once, then uses the existing row-lock/database-clock
checks and durable O_EXCL claim, with `ky.measuring_launch/1` and a separate
`run/ops/measuring_launch` claim directory. It launches exactly the staged UUID.
Unknown commit, timeout, interruption or unknown launch outcome never restages or
retries. The executor retains the exact run/execution/digest as `launch`; staging
UUID/exit zero cannot become launch evidence. Completion requires independent
`readback_sql` for this run and MB-6 acceptance, never launch status.

**(I) INTERPRETATION:** reuse the reviewed staging/deletion SQL and durable launch
helper through explicit measuring entry points. Alternative: duplicate those
implementations. The FROZEN writer/orchestrator contract and L0–L2 code are untouched.

## Measuring teardown and absence

Requests carry `item_id=J-3d` and `measuring_scope`: canonical run UUID, chart,
asset, generation, `plan_manifest_digest`, candidate `manifest_id`,
`input_vector_sha256`, and SHA-256 references to `dispatch_receipt` and
`dispatch_acceptance`. Only an accepted J-3c `measuring_dispatch` receipt carrying
`ky.measuring_launch/1` authorizes this scope. A small-test receipt cannot substitute.
The surviving run's original marker must validate as `all_classes_full`. The
candidate's stored vector must prove the exact original run/manifest; no tag-based
ownership, reconstruction, additional run or coverage from another run is accepted.

Owner capability is required. The existing terminal-state, remote quiescence,
locks, bounded ownership, retained-run and immutable/published/sealed/serving guards
remain mandatory. Before requesting teardown, independently capture MB-3's goldens
and commit the required artifacts; place the commit hash in the sitting log
(`MEASURING_BUILD_CONTRACT_v1_0.md:84,138-139`). This preparation creates no golden
bytes, report measurements or commit hash.

Run the dedicated rollback kind first. Its `ky.measuring_teardown/1` proof binds
scope, source, operation/request digest and the full row-content digest. Execute
requires that independently accepted rollback for the identical scope and rowset.
Even a same-count content change refuses deletion. Committed deletion remains
`AWAITING_ABSENCE`; its transactional zero counts do not complete the lifecycle.

A separate `readback_sql` request executes
`v5_small_test_shared.absence_readback_sql(committed_receipt)` and returns the
common `ky.smalltest_independent_absence/1` readback schema. The verifier binds its
output bytes, complete zero census, inert registry, run/scope/rowset, committed
receipt digest and different operation id. The executor releases quiescence only
after this detector, emitting a separate `ky.measuring_completion/1` record;
the original commit receipt stays immutable. A later launch invalidates reuse of
an older absence. No publication/seal/authority operation is supplied.

**(I) INTERPRETATION:** measuring teardown requires a non-null candidate manifest
and vector. Alternative: allow the small-test paired-null staged-only cleanup.
A launch that fails before candidate creation needs separately reviewed cleanup
authority and is intentionally not claimed supported by this contract.

## Offline input and work left for the cockpit

Use `CANONICAL_L1_OFFLINE_FIXTURE_SPEC_v1_0.md`. The approved canonical export and
deployment-faithful builder-role fixture were not supplied. Exact measuring-shape
sink-all acceptance, accepted cap projection/runtime timeout, full-horizon build,
substrate and writer readbacks, golden capture/committed hashes, actual report,
production teardown and independent absence remain operational gates.
J-3c-a52 and J-3d-a53 cannot be satisfied by carrying this code merge. Their original
dependencies and independent acceptance remain unchanged.

New pure authority tests live under `platform/scripts/governance/__tests__` and
are discovered by the existing CI shard convention. Real SQL tests extend the
already mandatory `test_w4_launch_bridge.py` and `test_w4_smalltest_safety_db.py`
suites. No explicit CI paths, aggregates, digest lock, migration or activation
are added. Job evidence, fail-on-revert copies and result remain under JOB_SCRATCH;
the uncommitted worktree is retained for cockpit review/commit as instructed.

## Source anchors

- `platform/scripts/dispatch_v5_measuring_job.py:22`: exact marker;
  `:34`: accepted mode, actual rollback proof and manifest binding.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py:82`: row locks,
  database-clock budget and durable claim shared by the measuring wrapper.
- `platform/scripts/v5_small_test_shared.py:496`, `:532`, `:552`, `:722`, `:747`:
  staged scope, teardown rollback, independent absence, measuring admission and
  staging rollback evidence respectively.
- `platform/scripts/teardown_v5_small_test_job.py:530`: original run/marker,
  candidate manifest/vector and coverage ownership before deletion.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:109`, `:251`, `:346`:
  independent absence completion, typed receipts and G8 admission.
- `platform/scripts/gochara/canonical_l1_snapshot.py:32`: offline byte validation,
  without export, restoration or production acceptance.
