---
artifact: SCHEDULER_REAPER
version: "1.1"
status: REVIEW_CANDIDATE
produced_on: 2026-10-18
authority: owner-surrogate rulings SR-J3-REAPER-PAUSE and SR-J3-CANCEL-NULL 2(a) (DECISIONS_SURROGATE.jsonl)
changelog:
  - "1.1: `measuring_cancel` (fleet/measuring_cancel.py, SR-J3-CANCEL-NULL 2(a)) and `run.executions.cancel` added to the scheduler_readback permission test."
  - "1.0: five executor kinds (`scheduler_pause`, `scheduler_resume`, their `*_dryrun` twins, read-only `scheduler_readback`), fleet/scheduler_reaper.py, and the executor-owned deferred-resume backstop."
---

# Pausing the cockpit watchdog for a measuring run

The watchdog (`platform/src/app/api/cockpit/watchdog/route.ts`) terminalizes any `building` asset whose `last_built_at` is more than 15 minutes stale, so one long full-horizon `ka_gochara_v5` substep could kill the live J-3c build. Ruling: pause the whole Cloud Scheduler job `watchdog-reaper` (created by `platform/scripts/provision_watchdog_scheduler.sh`: project `madhav-astrology`, region `asia-south1`) around the run, read back, and resume it afterwards; the resume at lease end cannot be skipped.

## Kinds (`executor_ops.json`, enabled_by J-3c)

| kind | class | takes | does |
|---|---|---|---|
| `scheduler_readback` | read-only, `production:false`, mechanically accepted | `job`? | state + acting principal + permission test |
| `scheduler_pause_dryrun` | `production:false`, merged `reviewed_commit` | `job`?, `resume-by` | plans the calls, makes **none** |
| `scheduler_pause` | production, one signer (verifier acceptance), lease, `dry_run_passed` | `job`?, `resume-by` | arms the backstop, then pauses |
| `scheduler_resume_dryrun` | as above | `job`? | plans, makes none |
| `scheduler_resume` | production, one signer | `job`? | resumes; a verified resume cancels the backstop |

No kind is `remote_async`: none takes the production fence. A **`scheduler_resume` is never held by a retained fence** (it is the safe direction; `pause` and everything else still wait). Allow-list: the job is `watchdog-reaper` or the request is refused (admission, and again inside the script, before any cloud call).

## Requests the pack sends

All production requests carry the usual fields (`operation_id`, `idempotency_key`, `item_id`, `requested_by: adhikarin`, `kyd`, `chart_id`, `lease_id`, merged `reviewed_commit`, `expires_at`, `acceptance_receipt`).

* pause: `"kind": "scheduler_pause", "args": {"job": "watchdog-reaper", "resume-by": "<UTC, YYYY-MM-DDTHH:MM:SSZ or +00:00, in the future, <= the lease end>"}`
* resume: `"kind": "scheduler_resume", "args": {"job": "watchdog-reaper"}`
* readback: `"kind": "scheduler_readback", "args": {"job": "watchdog-reaper"}` (requesters adhikarin, v1, v2; no lease or acceptance)
* `job` may be omitted (default `watchdog-reaper`); the dry runs take the same args as their twin.

## Receipt

Every receipt carries `scheduler` = the `ky.scheduler_job/1` record the executor validated (bound to this operation id, request digest, action, project, region and job): `state_before`, `changed`, **`state` = the state read back AFTER the action** (`PAUSED` after a pause, `ENABLED` after a resume, anything Cloud Scheduler reports for a readback), `gcloud_calls`. A pause that reads back anything but `PAUSED`, a resume anything but `ENABLED`, or a record that does not bind the request, is `FAILED` whatever the exit status. Pausing a paused job / resuming an enabled one is success (`changed:false`).

`scheduler_readback` also reports `identity.principal` (the executor's active gcloud account e-mail; never a token) and `permissions` (with `capabilities` mapping each capability — pause, resume, get, cancel — to the permission tested): `cloudscheduler.jobs.pause`, `cloudscheduler.jobs.enable` (the permission Google documents for the `jobs.resume` method — [REST reference](https://docs.cloud.google.com/scheduler/docs/reference/rest/v1/projects.locations.jobs/resume); `cloudscheduler.jobs.resume` is not a permission and Google answers HTTP 400 for it), `cloudscheduler.jobs.get` and `run.executions.cancel` (needed by `measuring_cancel`) granted / missing. (I) INTERPRETATION: Cloud Scheduler has no job-level `testIamPermissions`, so the read-only test runs on the **project** (`cloudresourcemanager` v1 `projects/madhav-astrology:testIamPermissions`) with an access token held in memory for that call only. `status: UNAVAILABLE` (never a green) if it cannot be measured; `status: PARTIAL` with `state: null` if the job itself cannot be described (e.g. `jobs.get` missing) — the identity and permission lists are still given. Run it once right after landing; a missing permission is reported with the exact role and `identity.principal`. No IAM grant is made here.

## The backstop (resume whatever happens)

1. **Armed before the pause.** In `run_one`, after the last admission check and before the script runs, `arm_scheduler_backstop` writes `run/ops/scheduler_backstop/<operation_id>.json` (`ky.scheduler_backstop/1`, `status: ARMED`, `resume_by`, the reviewed commit; temp file + fsync + rename). If it cannot be written the pause does **not** run. A pause that then fails, times out or is interrupted leaves a harmless idempotent resume behind.
2. **Honoured on every loop turn.** `scheduler_backstop_tick()` runs at the top of each `main()` turn, **before** the sync, table and HOLD gates: HOLD, an unreachable origin or an unloadable table do not stop it. The executor then runs the reviewed `scheduler_reaper.py --action resume --job watchdog-reaper` itself, from the commit the pause named (local objects; no fetch needed), with no queue, lease or signer; the signed pause already bound `resume-by`, which admission bounds by the lease end. The receipt is `receipts/bs-<12 hex>-<attempt>.json`.
3. **Restart.** The record is on disk, so a fresh process finds it on its first turn (and logs `re-armed from disk` at start); an overdue `resume_by` fires on that first turn.
4. **Done when read back.** `FIRED` only if the state read back is `ENABLED`; otherwise the record stays `ARMED`, backs off 30 s doubling to 15 min, and retries without end. A verified `scheduler_resume` marks every armed record `SATISFIED` (the evidence stays).

Failure modes, stated plainly: (a) the executor is *down* at `resume_by` — the resume happens at its next start; (b) `STOP_executor` is set — the loop exits and does not tick; (c) gcloud/identity broken — retried until it works, each attempt is a FAILED receipt and a log line; (d) a corrupt record file is skipped and logged once (`BACKSTOP_UNREADABLE`), an unparseable `resume_by` counts as overdue; (e) a race between a verified resume and a tick can cost one extra idempotent resume. The backstop cannot resume a job someone re-paused by hand after it fired.

Not done here: the watchdog threshold fix (HYG-REAPER-LONG-SUBSTEP), any IAM grant or provisioning, the orchestrator.

## `measuring_cancel` (SR-J3-CANCEL-NULL 2(a); same PR, same review)

Cancels ONE running Cloud Run execution of the measuring build, for the ruled sequence cancel → read back `CANCELLED` → `scheduler_resume` → the existing watchdog terminalizes the orphan → teardown. No terminalizing code is added here.

* Kinds: `measuring_cancel` (production, `needs: gcloud`, `enabled_by: J-3c`, `allowed_args: ["execution"]`, requester `adhikarin`; one signer (verifier acceptance), lease, canonical chart, merged `reviewed_commit`, `dry_run_passed` as every production kind) and its twin `measuring_cancel_dryrun` (`production:false`; the same admission, **zero** cloud calls). (I) INTERPRETATION: the dry run needs the ABORT/stall verdict too, so it is issued at decision time together with the cancel (the executor loop turns every 10 s); the alternative, exempting the cancel from `dry_run_passed`, would have made the signer's generic checklist (`kyd_kinds_ops.required_checks`) attest a dry run that never happened. A cancel is never held by the production fence (the live measuring dispatch is what holds it).
* Request: `{"kind": "measuring_cancel", "item_id": "J-3c", "args": {"execution": "brahma-build-pipeline-job-<suffix>"}, "dispatch_receipt": {"name": "<dispatch op id>.json", "sha256": "<hex>"}, "verdict": {"name": "<file>.json", "sha256": "<hex>"}, …production fields}`; both references are in the request digest the verifier signs.
* Admission refuses unless (i) the file `run/ops/receipts/<name>` hashes to the cited sha256, is a `COMPLETED`, exit-0 `measuring_dispatch` receipt of J-3c named `<its operation_id>.json` with `launch.status: LAUNCHED`, and **`launch.execution_name` equals the target**; and (ii) `run/ops/verdicts/<name>` hashes to the cited sha256 and is an `ABORT` (`ky.reproject_verdict/<n>`, verdict `ABORT`) or stall (`ky.stall_verdict/<n>`, verdict `STALL`) verdict. CONTINUE, NULL, a missing file or altered bytes refuse. (I) INTERPRETATION: `reproject_gate.py` / `teardown_gate.py` (the J3C pack) are not in this repository, so the schema names, the `verdict` field and the `run/ops/verdicts/` folder are read from the ruling's wording; the one place to change is `measuring_cancel_problem` in `executor.py` if the pack names them differently.
* The script (`measuring_cancel.py`, `ky.measuring_cancel/1`) reads the execution, cancels it only if `RUNNING`, polls the read-back (12 × 10 s; cancel is asynchronous) and records **`state` = the state read back after the action**. `CANCELLED` (Execution.status `cancelledCount` ≥ 1, `runningCount` 0) is the only success; `RUNNING` after the polls, or an execution already `SUCCEEDED` / `FAILED`, is a FAILED record and a FAILED receipt with that state, whatever the exit status. Cancelling an already `CANCELLED` execution is success with `changed:false`.
* Receipt: `cancel` = that record, bound to the operation id, request digest, execution and the measuring job (`madhav-astrology` / `asia-south1` / `brahma-build-pipeline-job`).
* **Siblings (W3W4 pack verify E1).** The same engine, admission, proof and fence rule serve `century_cancel` (+ `_dryrun`; item J-4e; the `century_dispatch` receipt; script `century_cancel.py`, record `ky.century_cancel/1`; the century build runs on the same Cloud Run job) and `verification_cancel` (+ `_dryrun`; item J-5s; the `verification_job` receipt; script `verification_cancel.py`, record `ky.verification_cancel/1`; Cloud Run job `gochara-verification-job`, execution `gochara-verification-job-<suffix>`). Each table entry is `needs: gcloud`, `allowed_args: ["execution"]`, requester `adhikarin`; the executor's `CANCEL_FAMILIES` holds the per-family item, dispatch kind, schema, job and execution shape. All three cancels are **signed-only** (`SIGNED_ONLY_KINDS`: a lease, one verifier lane's acceptance and `dry_run_passed`; never the mechanical route) and never held by the production fence.
