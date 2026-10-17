---
artifact: KV3_B_OPS_CONTRACT
version: 1.0
status: PREPARATION_ONLY
produced_on: 2026-10-16
changelog: Reconcile PR 3485 with current main and Wave 4 bindings; remove dispatcher dependencies.
---

# Executor operation-adapter contract

`operation_adapters.py` is a standard-library helper for reviewed operation scripts.
It enables no kind, launches no process itself, and imports no dispatcher module.
The fake-remote harness calls the actual executor validation, execution and receipt
functions with in-process substitutes for Git, child processes and remote transport.
No executor daemon or production/cloud operation runs in these tests.

## Interfaces and evidence

- `add_mode_arguments`, `resolve_mode`, `parse_request_args`: named arguments and
  explicit execution; omitted execution defaults to dry-run. Duplicate, unknown,
  positional and conflicting mode arguments refuse.
- `launch_argv`: the executor's existing fixed args followed by request args,
  including Python-module, Python-script and shell-script forms.
- `remote_launch`: compare non-secret job-definition principal and secret-reference
  names with existing builder/verifier bindings. Only the build job has a launch
  contract. Its project, region, async flag and execution-name format match
  `smalltest_launch.py:38`; an alternate project refuses. Dry-run and execution
  share one planned argv; dry-run never submits. Local exit zero proves submission
  only, with terminal outcome left unknown.
- `remote_env`, `secret_refusal`, `emit`: allow-listed remote environment and
  refusal of credential-shaped values in argv or exported evidence. Builder and
  owner connections never pass to the remote transport.
- `rehearse`: actual supplied statements, probe hashes/counts and head comparison
  before/during/after rollback, bound to script and input hashes. The SQLite tests
  exercise DB-API mechanics only; they do not qualify any production SQL operation.
  An operation still owes its guarded PostgreSQL rehearsal and semantic readback.
- `scope_record`: backup/restore preflight and scope only; restore verification
  remains unknown until separately measured.
- `completion`: read the executor's receipt format (`executor.py:224`) directly;
  require COMPLETED, integer exit zero, matching item/operation/request, nonempty
  complete output matching its digest, a successful terminal observation bound to
  the actual receipt bytes, and the latest ACCEPTED artifact verdict for the same
  item and receipt digest. Staging, running, missing observations, rejected or
  mismatched verdicts cannot complete. No helper releases the production fence.

`ky.op_adapter/1` is script output, not an executor receipt.
`ky.op_observation/1` binds operation_id, request_sha256, receipt_sha256, terminal,
outcome and source. The verifier owns the semantic observation and independently
published verdict; this helper does not grant authority to create either.

## Merge disposition and interpretations

**(I) INTERPRETATION I1:** A4 D-28's instruction to drop dispatcher-only work means
restore conflicted dispatcher/control/packet files to current main, preserving its
already-merged implementation and history. Delete the stale branch's dispatcher
coupling from this helper and harness. Deleting main's retired-but-preserved code
would contradict A4 §2.3(c).

**Added read-only kind (J-2a M6/M7):** `cloudrun_job_readback` is a fifth enabled non-production
kind; it is measurement only and is specified in `CLOUDRUN_READBACK_v1_0.md`. It does not widen
I2: no production, dispatch or teardown kind changes.

**(I) INTERPRETATION I2:** “Every op stays disabled” means every production or newly
prepared operation stays disabled. Preserve main's four existing enabled
read/local kinds (`readback_sql`, `migration_readback`, `local_schema_seed`,
`finalize`) and its entire `executor_ops.json` unchanged. Wave 4's
`smalltest_launch.py`, `operation_dryrun.py` and all prepared descriptors remain
main's exact bytes. `BOOTSTRAP_COMPONENTS.txt` adds these executor sources,
tests and review notes to the packaging census without installing them. No activation, install, restart or remote call is included.

The original packet remains a historical source pin. Its snapshot checks and
retired dispatcher admission/publication tests are replaced with executor
behavior checks. Already-merged dispatcher tests stay untouched.

## Review command

```sh
GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 TMPDIR="$JOB_SCRATCH" \
  python3 -B -m pytest \
  00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_operation_adapters.py \
  -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest-adapters"
```

Fail-on-revert evidence and the complete suite/aggregate results live in the
cockpit job's `result.json` and its referenced scratch files. Git staging and the
merge commit are cockpit actions; this child changes working-tree contents only.
