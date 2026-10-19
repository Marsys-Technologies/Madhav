---
artifact: J5S_SEAL_PREBUILD
version: 1.0
status: PREBUILD — built, waiting on gate; no operational acceptance
produced_on: 2026-10-16
changelog: "1.0: full-class local seal rehearsal, zero-grain completeness correction and disabled strict verifier launch preparation."
---

# J-5s local seal rehearsal and launcher preparation

This package prepares J-5s under A6 D-40/D-41. It emits no campaign operation
receipt, controller step receipt or acceptance verdict. It allocates no production
launcher, grants no privilege in production and switches no serving head.
A5.7/B5.4 qualification and J-5s-j2 acceptance remain outstanding.

The governing separation is in
`00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md:472`; the completeness and separately
dispatched verifier steps are in `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:243`.
The initial full-class attempt exposed a false refusal for `psychological_arc` and
`spiritual_turn`: both have zero included window grains and a valid independently
verified inventory. The server and workflow checker required a window row anyway.
Both now accept an empty grain list only with an inventory attestation matching
chart, generation, event class and inventory digest. The combined gate still must
be clean; a missing included grain still refuses. No payload schema changes.

The actual executable contracts are
`pipeline/orchestrator/verification_job.py` and `pipeline/orchestrator/seal_job.py`,
using `services/gochara_kernel/verification_job.py`, `seal_brief.py` and
`seal_flow.py`. The entry points, writer and orchestrator contract remain unchanged;
the brief library and workflow payload validator receive the completeness fix.

## Rehearsal boundary

`platform/python-sidecar/tests/l3/gochara/test_j5s_full_class_seal_db.py` runs the
writer's real plan as `data_plane_builder` over all 26 scored classes. The AM5
fixture supplies explicitly synthetic natal facts and linked periods, the real
migration chain, and fixture-local read grants. Every transit computation uses
the checksum-pinned Swiss corpus. No copied class population, geometry stand-in,
replication-role bypass or disabled database guard supplies the candidate.

**(I) INTERPRETATION:** the optional `J5S_SUBSTRATE_CACHE` restores a hash-checked
real candidate capture solely to reuse its substrate after proving the geometry
implementation digest is unchanged. The actual manifest and snapshot substeps
then replace the candidate and delete its old output chain; every inventory,
record and window is rebuilt under the corrected code. Repeated exact Swiss
probes are memoized through the real production function, retaining real return
flags and the pinned corpus. Alternative: recompute the unchanged full substrate
and every repeated probe; the initial full cold build already measured that
path. No production resume mode is added.

**(I) INTERPRETATION:** use the short record horizon `[2025-01-01, 2025-01-03)`
UTC with the unchanged full 1998–2085 substrate and `all_null_candidate/1` policy.
This exercises all classes and their included grains through the full seal
protocol within a local job. Alternative: run the entire final-rules century
record horizon. That production-volume/qualification evidence remains a gate;
this fixture cannot earn it.

The test requires actual SQLSTATE 42501 for the builder's attestation INSERTs,
executes the verifier entry point as the verifier LOGIN, checks full class and
included-grain coverage, corrupts a stored window and requires DISAGREE, restores
and re-verifies, and refuses a missing included attestation before briefing.
The complete canonical brief is reassembled from chunks and persisted by the
verifier. The real sealer LOGIN rejects foreign run, attempt, brief and execution
bindings, an incorrect manifest reference, and candidate state changed after
approval. A joined SQL readback checks publication/seal/approval/brief manifest
identity, both digests, producer execution, database-attested principals and the
exact run/attempt/commit after the successful seal. Both the real workflow payload checker and sealer entry point are exercised.
The fixture drops its own
database in `finally`, including after a failing assertion.

**(I) INTERPRETATION:** the immutable-image, execution, commit, workflow run and
approval labels in this fixture are local transport identities. Real database
logins and transactions are exercised. Alternative: contact the deployed job or
claim a deployed image; that is outside this pre-build and is not asserted.

Run from `platform/python-sidecar`, with the supplied `JOB_SCRATCH`:

```sh
mkdir -p "$JOB_SCRATCH/tmp"
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$JOB_SCRATCH/tmp"
export SE_EPHE_PATH=/Users/Dev/kalayantra/ephe GOCHARA_SE1_REQUIRE=1
export KALA_REQUIRE_DB=1
export KALA_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres
export GOCHARA_A53_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres
export GOCHARA_A53_REQUIRE_DB=1
export GOCHARA_RUNNER_COMMIT=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
python3 -B -m pytest tests/l3/gochara/test_j5s_full_class_seal_db.py \
  -v -s --tb=short -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest-j5s"
```

The optional `J5S_CANDIDATE_EXPORT` output path captures the complete candidate
inline before verification and teardown, accompanied by its SHA-256. Use a
`J5S_PG_DUMP` client matching the local server major version. For an optional substrate cache also set `J5S_PG_RESTORE` to the matching client.
No capture is required by CI; CI always builds its candidate from the real writer substeps.
A saved candidate is forensic test evidence, never production acceptance.

**(I) INTERPRETATION:** this baseline lacks the `ci_generated.py` coordinator.
The test uses the existing implementation-registry leaf generator to write a
fresh lock into pytest scratch and points the sealer self-check at that file.
The branch's machine-owned lock is untouched. Alternative: write generated bytes
into the branch; A5 D-33 forbids that. The cockpit must integrate the generated
CI overlay machinery before landing; ordinary baseline checks of the retained
root lock will correctly report it stale after this source correction. This
scratch overlay is local test evidence, never a production registration.

## Disabled launch binding

`platform/scripts/prepare_gochara_verifier_launch.py` validates supplied job
readbacks through the existing shared strict definition checker. It pins the
reviewed commit and immutable image, verifier runtime account, verifier-only
secret reference, verifier module entry point, resources, Cloud SQL attachment,
zero retries and one task. It emits the exact planned full-generation command
without `--class`, `--report-only` or `--brief`. It contains no transport call and
has no `--execute` option.

```sh
python3 -B platform/scripts/prepare_gochara_verifier_launch.py \
  --job-file supplied-job-readback.json \
  --reviewed-commit REVIEWED_40_HEX_SHA --image-digest sha256:IMAGE_64_HEX_DIGEST
```

A supplied v2 readback may be bound with `--v2-job-file`. The emitted descriptor
is `PREPARATION_ONLY`, `enabled=false`, `dry_run_passed=false`, and
`production_allocation=null`. `fleet/operation_dryrun.py` points to this prepared
binding; `executor_ops.json` stays unchanged, disabled and unallocated.

**(I) INTERPRETATION:** preparation binds the reviewed inputs and proposed argv,
while leaving the live launch/dry-run allocation to the controller's reviewed
child. Alternative: replace the executor's placeholder or add an executable
cloud transport now. No production allocation is authorized by this package.

## Exit gates and CI handoff

Before any real request, the controller must observe P06b's independently
accepted guarded completion and protected-apply/readbacks, plus G8: live exclusive
`campaign-coordination` lease, backup and verified restore, accepted dry run,
one build slot, and PARĪKṢAKA pre-acceptance of that same request/operation.
Allocate and independently review the real launcher and its execution-resource
readback before enabling anything. A verified candidate is then briefed and
sealed through the existing approval-gated workflow; its human environment
approval is still required. No local fixture or descriptor supplies these acts.

After execution, the executor must perform `readback_sql` for the recorded run,
not infer success from an exit code. The canonical future receipt remains
`/Users/Dev/kalayantra/run/ops/receipts/J-5s.json`. Independent acceptance must bind
its exact digest, item, request, operation, expected full manifest, verifier
execution, seal workflow run and attempt. SQL observation alone is insufficient.

**(I) INTERPRETATION:** this supplied baseline (`ef14167bc`) has the legacy CI
selection/coverage guard and does not contain `ci_discovery.py` or
`ci_test_suites.json`. Those paths exist on the separate in-flight
`kalayantra/ci-shard-samiksha` branch and are left untouched. This package adds a
mandatory dedicated local-Postgres job selected by `test_j5s_*_db.py`, adds its
result to the existing required Governance Tool Tests aggregate (failure,
cancellation and unexpected skip all refuse), and teaches
the existing coverage guard to expand that glob. Alternative: import or replace
the other branch's infrastructure. When integrating after that infrastructure,
the cockpit must move this glob into its discovery profile, retain the dedicated
job's runtime budget and generated-output restore requirements, and run
`ci_discovery.py guard` until it reports `current`. No explicit test-file path is
added to `ci.yml` by this package.

## Observed local evidence

Job `X-20261016T135700Z-pb-j5s-seal` built the cold full class chain and
independently verified all 26 classes before exposing the two zero-grain false
refusals. The corrected replay rebuilt every class output under the corrected
manifest, using the digest-matched real substrate; it passed in 978.59 seconds.
All 26 classes and 78 included grains were independently verified. The actual
workflow payload validator and sealer entry point passed, followed by SQL binding
of all four manifest references, both digests, verifier execution, database
principals, run and attempt. This is local fixture evidence.

380 combined preparation/contract tests and 36 CI wiring tests passed. Exact
source reverts of both completeness validators failed their regression tests.
Ten database semantic mutants failed and both fixed replays passed; preparation
and CI revert/mutation cases bring the total to 22. The job folder retains the
hash-bound captures, command scripts and logs. The initial failed full attempt
and the deliberately interrupted slow uncached rebuild remain recorded. The
suite's databases are removed on fixture exit; production and qualification
receipts are not produced by this package.
