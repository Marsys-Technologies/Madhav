---
artifact: W4_EXECUTOR_BINDINGS
version: 1.1
status: PREPARATION_ONLY — independent review, integration and phase enablement outstanding
produced_on: 2026-10-15
changelog: "v1.2 (2026-10-18): publish_head / rollback_head and their dry-run siblings are bound and enabled (J-6m / J-6r, SR-PREBUILD-ALL); v1.1 (2026-10-16): J3C-BINDINGS supersedes measuring proposal metadata with dedicated disabled bindings; v1.0: initial launch/preparation surfaces."
---

# Wave 4 step 7 — executable launch bridge and later preparation

> **2026-10-16 J3C-BINDINGS amendment:** the measuring-specific proposal and
> `staging_dry_run` metadata below are superseded by
> [J3C_BINDINGS_PREBUILD_v1_0.md](../../pravaha/measurement/J3C_BINDINGS_PREBUILD_v1_0.md).
> `measuring_dispatch`, `measuring_dispatch_dryrun`, `measuring_teardown_dryrun`
> and `measuring_teardown` now have real prepared bindings and remain DISABLED.
> The small-test dispatcher still refuses the measuring shape. P01's six
> small-test/backup kinds are now enabled on this source baseline; this amendment
> changes none of their enablement states. The remaining text records the earlier
> Wave 4 preparation and is not an activation or operational acceptance receipt.

Scope: the existing `smalltest_dispatch` kind now points to `smalltest_launch.py`.
All existing enablement states are preserved: only the four baseline read/local
kinds are enabled. This checkout does not contain the pending P01 six-kind
activation; cockpit integration must retain the reviewed P01 backup/teardown
bindings and explicitly review any activation. No operation has been executed
against the cloud or production by this job.

## Small-test launch contract

`smalltest_launch.py` accepts only the table's existing run/classes/horizon args.
It calls the existing dispatcher once, with its steward, settled-1 and execute
flags. The only stdout accepted from staging is one canonical UUID; printed shell
commands are never evaluated. Any staging exception, including COMMIT-unknown,
aborts without a launch or another staging attempt.

The wrapper reconstructs the exact manifest from the request and reviewed
checkout, reads that UUID's `build_runs` row `FOR UPDATE`, and checks chart, scope,
action, plan, trigger, planned state, unset start time, manifest bytes/digest and
exactly one queued asset at position zero. It checks the stored creation time
against `clock_timestamp()`, retaining the row locks until the launcher returns.
A second clock read follows durable claim persistence, immediately before launch.
The launcher has a timeout bounded by the remaining database-clock budget.

A per-run O_EXCL claim under `$KY_ROOT/run/ops/smalltest_launch/<UUID>.json` is
fsynced before the remote call. A duplicate claim, unknown outcome, timeout or
interruption never permits an automatic retry. No claim is automatically removed.
If stdout/receipt writing fails after launch, reconcile the durable claim, remote
execution and run under the existing production fence before any new request.
These claims cover this bridge's launch attempts; external/manual launches that
have not yet changed DB state cannot be inferred from a planned row. Operators
must use the governed single-executor path exclusively.

The fixed launcher invokes the existing build job asynchronously with exactly
`--args=--run-id,<UUID>`, fixed project/region, no shell and no arbitrary flags.
Only a matching job execution name yields `LAUNCHED`; the machine record binds
run, chart, asset, manifest digest and deadline to that execution. The executor
adds that record as `launch` in its request-digest-bound receipt, refusing to label
a staging-only zero exit as completed. This records launch acceptance; completion
still requires independent DB state, remote quiescence and semantic readback.

`smalltest_dispatch` requires **builder and gcloud**. The added `also_needs`
validation requires every listed additional capability. No additional credential
is passed to children. Unknown/disabled kinds, unlisted args, requester, lease,
merged source, backup/restore/dry-run acceptance and the production fence retain
their existing guards. The standalone small-test rollback kind now supplies the
existing dispatcher's two required steward flags as fixed args.

## Disabled preparation surfaces

`prepared_dry_run` metadata on the existing later kinds that are not yet bound (J-6m / J-6r have real siblings) describes an explicit
no-effect request preview via `operation_dryrun.py --dry-run --kind <kind>` and the
kind's bounded arguments. The executor never treats nested metadata as a kind.
The preview returns `PREPARATION_ONLY`, blockers and **dry_run_passed=false**.
A successful preview cannot support pre-acceptance. Its purpose is to make the
proposed request and its gaps reviewable now.

| Existing kind | Bounded args | Executor capability | Phase / missing real binding |
| --- | --- | --- | --- |
| measuring_dispatch | run=all_classes_full, classes=all | builder + gcloud | J-3a/J-3c; staging rollback and actual launch qualification |
| century_dispatch | classes=all | gcloud | J-4d/J-4e; final-rules 5.0 launcher; confirm any staging builder requirement |
| verification_job | generation=5.0 | gcloud | phase 10 after P06b; remote launcher and immutable job-definition readback |
| publish_head | ENABLED (SR-PREBUILD-ALL): generation, manifest-id, expected-head | builder | J-6m; `kala_gochara_cutover/publish_head.py --execute`, sibling `publish_head_dryrun` (`--dry-run`, read-only transaction); V-lane signer stays required (SR-MINIMAL-PROTECTION) |
| rollback_head | ENABLED (SR-PREBUILD-ALL): generation (the recorded previous head), expected-head | builder | J-6r; `kala_gochara_cutover/rollback_head.py --execute`, sibling `rollback_head_dryrun`; restores the retained head, never deletion-to-v1; V-lane signer stays required |

The additional disabled `measuring_dispatch.staging_dry_run` descriptor binds the
**real transaction rollback** path: the existing dispatcher with fixed steward,
settled-1, dry-run, all_classes_full and all-classes args, no request overrides.
This is staging evidence only; it cannot establish remote launch readiness.

`protected_apply`, `provision`, `seal` are **proposal labels**, absent from
`executor_ops.json.ops`. Their previews accept no request arguments and enumerate
allocation, immutable inputs, human approval and principal requirements. No IAM,
credentials, protected workflow dispatch or production deletion authority is
created. The intended credential-bearing identities remain the protected workflow
ownership admin and, for sealing, the sealer runtime; no builder login substitutes
for the verifier or sealer.

## Interpretations and cockpit decisions

- **(I) INTERPRETATION I1:** preserve current table enablement while this job prepares
  code. Reconcile the P01 landing before independently reviewing phase activation.
- **(I) INTERPRETATION I2:** where a dry-run kind or mutating wrapper has not been
  allocated by a real child, prepare disabled descriptors and honest no-effect
  previews, not a newly executable kind or a fabricated rollback PASS.
- **(I) INTERPRETATION I3:** invoking the remote verifier requires gcloud at the
  executor boundary; its own task holds GOCHARA_VERIFIER_DB_URL. The executor must
  not hand a builder connection to the verifier or acquire a verifier credential.
- **(I) INTERPRETATION I4:** freshness means strict age `<600s` with a whole-second
  request budget; future DB timestamps and the final subsecond budget refuse.
  The claim remains retained if the budget expires during local persistence.
- **(I) INTERPRETATION I6:** rollback preparation accepts no target and emits a null
  generation until the actual retained previous head and request contract are
  reviewed; a 5.0 target cannot be inferred from the forward publish request.
- **(I) INTERPRETATION I5:** allocation of the wrapper path is supplied by this bounded
  implementation job; no new tracker child id is invented. Cockpit must register
  the real child and bind review/source before this wrapper becomes executable.

Proposed future kind names, **not allocated or executable**:
`measuring_dispatch_dryrun`, `century_dispatch_dryrun`,
`verification_job_dryrun`,
`protected_apply`, `protected_apply_dryrun`, `provision`, `provision_dryrun`,
`seal`, `seal_dryrun`. Cockpit must decide names, child allocation, exact request
inputs, capabilities and enable-at-phase gates. Century, authority switching and
protected interfaces remain explicitly unbound; their existing placeholders
continue to fail closed even if accidentally enabled.

## Opened source contracts

- `CLAUDE.md:70` (§I) and `CLAUDE.md:139` (§N.8): scope and measured signals.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md:36`
  and `:74`: hard stops and external human protected-environment approval.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md:386`:
  request preparation, independent pre-acceptance, execute and semantic readback.
- `/Users/Dev/kalayantra/run/WAVE4_COMPLETION_PATH.md:75`: step 7 and no invented
  runnable interfaces; `:185`, `:281`, `:315`, `:357`: phase binding requirements.
- `platform/scripts/dispatch_v5_small_test_job.py:301`: canonical manifest;
  `:553`: stored creation time; `:603`: report and ten-minute launch requirement.
- `platform/scripts/dispatch_frozen_rebuild.py:149`: existing fixed async launch
  argv pattern. `.github/workflows/deploy.yml:939`: actual build job/project/region.
- `platform/python-sidecar/pipeline/orchestrator/verification_job.py:35` and `:74`:
  verifier-only runtime connection and actual report-only/brief entry points.
- `platform/python-sidecar/services/gochara_kernel/verification_job.py:554`:
  report-only does not become VERIFIED.
- `platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh:24`:
  legacy century generation is 4.1, not a final-rules 5.0 binding.
- `platform/scripts/gochara/rollback_authority.py:5`: legacy delete-to-v1 behavior.
- `.github/workflows/gochara-role-provisioning-oneshot.yml:20`:
  bounded one-shot stages, governed environment and approval boundary.
- `.github/workflows/gochara-seal-approved.yml:34` and `:42`: existing seal workflow,
  exact verifier/sealer identities and dispatch inputs; no wrapper may bypass it.

## Verification and cleanup

Fleet tests exercise the launcher only through injected local implementations.
The guarded Gochara suite supplies its own isolated databases on 127.0.0.1:55433;
its fixtures own their cleanup. Fail-on-revert copies, commands and measured exit
codes are retained under JOB_SCRATCH for independent review. Git-writing fleet
fixtures and process-group/daemon tests are outside this job's executable sandbox
and are reported separately, not claimed passing. No shared session-state edits
or independent campaign handshake were introduced; this is a cockpit child job.
The pre-existing worktree remains uncommitted for the cockpit, per the prompt.
