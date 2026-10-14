```json
{"id":"KV3-B-KYDISPATCH",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§4 capacity; §6","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kydispatch.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kydispatch.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/engine.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kydispatch.py -q -p no:cacheprovider",
"expected_result":"exit 0; --dry prints each engine.json case's checked-in job list",
"negative_cases":[
"STOP_dispatcher or the global HOLD: no admission, bootstrap included",
"HOLD_MERGES: no queue submission; gate WAIT: only KV3-B-* items",
"a snapshot fallback of ky next: nothing admitted; a second instance: exit 75"]},
"packet_sha256":"6fd3308a7758edf0f8614e3040ba664c51e37a6cdc345e87d8c35aea05c2dd4f"}
```
# KV3-B-KYDISPATCH v1: `kydispatch.py`

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's, already holding the five `kyd_*.py` modules (absent → `blocked`). (I) = INTERPRETATION.

**Owns.** The `d1_paths` only (new). Prohibited: FROZEN paths; installed trees; any other path → `blocked`.

**Spec** (verbatim).
```excerpt plan §6
`$KY_FLEET/kydispatch.py` (launchd `KeepAlive`, 30 s tick); atomic instance lock via
`kylock.sh` (session identity + PID/PGID + process-start identity); `--dry`, `--once`;
fixtures under
`fleet/tests/dispatch/` with checked-in expected job lists.
```
```excerpt plan §6
**Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no admissions
of any kind (bootstrap included). `run/HOLD_MERGES` → no queue submission of any kind.
Release gate (§10): while WAIT, only bootstrap-tagged jobs. Recovery: jobs recorded live
whose process group (PID/PGID + start identity) is gone → release claim, `interrupted`,
re-queue once. Freshness: `ky next --json` must come from the live tracker (a snapshot
fallback is refused; `version` must advance or match the EVENTS prefix hash). Then
refresh the campaign checkout and compute.
```
```excerpt plan §4
Capacity `KY_BUILDERS_MIN=3 / MAX=6`, `KY_VERIFIERS_MIN=2 / MAX=4`; `min(max, demand)`
per kind; the surrogate may raise the maxima when ready work exceeds live builders. No
token caps (§15.6). On a subscription refusal (structured error in the stream **or**
terminal log text) the dispatcher backs off adaptively (5 → 10 → 20 → 30 min), reports it,
and resumes automatically
```
```excerpt plan §6
**Messaging:** the dispatcher routes every owner-wait to a SURROGATE job first; it
writes to the conductor/cockpit journal (and notifies the owner) only for surrogate
decisions, hard stops, verdict invalidation, gate change, wave complete, quota backoff,
dispatcher error, ceiling hit, unclassifiable CI failure.

**Tests (B-1):** fixtures for every kind and transition, recovery, timeout reaping, hold
precedence, gate WAIT with bootstrap exemption, ceiling refusal, stale-snapshot refusal,
duplicate instance refusal, head-match guard, inheritance predicate (substantive
resolution fixture), failure fingerprint persistence.
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`): the engine reads and writes it only through kyd_jobs, whose packet pins the keys, and reads job state only through kyd_jobs' return values (`outcome`: `done | blocked | failed | interrupted | timed_out | refused`).

**Contract.** `/opt/homebrew/bin/python3 -u $KY_FLEET/kydispatch.py` · `--once`, `--dry`: one tick (`--dry`: no lock, read-only; stdout `{"schema": "ky.dispatch_plan/1", "jobs": [{kind, item, key, pool, decision}]}`; decision (I): `launch`, `park`, `refused:<code of the refusing step>` or `wait:<hold|gate|backoff|slot|stale>`). Exit 0 clean stop · 75 no lock · 78 a credential variable name set · 64 usage. Modules: its directory; scripts: $KY_FLEET.
Instance: controller_id = `CTL-dispatcher-<UTC yyyymmddThhmmssZ>-<pid>`; `bash fleet/kylock.sh acquire dispatcher <controller_id>` must exit 0; release only at a stop with no job live (I).
Loop file $KY_RUN/loops/dispatcher.json (kyloop.py's loop_state, update_loop_state; enabled is kyloop.py admin's): last_iteration_at, controller{id, pid}, waiting, log_path; its own backoff, tracker, priority.
A tick (J = kyd_jobs, A = kyd_admit):
1. STOP_dispatcher, or enabled not true → exit 0.
2. kycommands.pending(run, "dispatcher"), each via kycommands.apply: `status`; `loops stop dispatcher` → STOP_dispatcher, enabled false; `priority <item>`; `builders|verifiers <n>` (1–8) → the pool file; else Reject.
3. J.recover, J.supervise; per job returned: its kind's finish if it ended by itself; J.close.
4. Global HOLD, or (I) an owner pause (kycommands.owner_paused(run); unknown counts) → tick ends.
5. Freshness (I): `ky next --json` has an integer version (none in the snapshot fallback) above the last tick's, or equal with $KY_RUN/EVENTS.jsonl unchanged (size, sha256); else ctx.next is None.
6. git fetch in repo; fast-forward to origin/main only while HOLD_MERGES is absent (I).
7. Gate: `bash fleet/kygate.sh` exit 0 → OPEN; else WAIT: only KV3-B-* items (I).
8. intents of kyd_kinds_land, kyd_kinds_ops, kyd_kinds_build; under HOLD_MERGES a queue intent goes to kyd_kinds_land.park only.
9. Per intent, until a step says no: J.attempts; backoff (model runners); a free slot of its pool (b1..bN, v1..vM, never not_slot); A.precheck (slot_not_ready → A.provision, one slot a tick); J.open; A.admit; the kind's start; J.launch for a model runner without a result, else J.close. After J.open, any refusal or failed start → J.close, outcome refused.
Capacity: N, M = integers 1–8 in $KY_RUN/KY_WORKERS, $KY_RUN/KY_VERIFIERS (kyveto.py's; maxima 8 (I): owner direction of 2026-10-12, recorded in PLANNER_STATE active.owner_directions_20261012; not yet in the owner decisions file); absent → 6, 4; unreadable → 0. limits.copies = 10 (I). Ready work above a maximum → ctx.awaiting("capacity-above-max", …).
Backoff, as quoted: after a job ending with failure_fp quota, no model launch; a model job ending without it resets.
Messaging: journal appends to $KY_RUN/JOURNAL_DISPATCHER.md; for the quoted events also `bash fleet/kynotify.sh "<text>" --level …` inside act, once per changed condition. awaiting writes a ky.awaiting/1 item.
A tick's exception is caught: journal dispatcher error.
ctx, intents: the module packets'. Built here:
- repo: $KY_SOURCE_REPO, else the plan §5 campaign checkout; model: the plan model's absolute path in repo; now(): UTC.
- sh: environment HOME USER LANG TERM PATH TMPDIR, the four KY_ paths, env; ky (I): sh of ky; act: over kyaction's begin, complete, fail, reconcile.
- events(item): its lines of $KY_RUN/EVENTS.jsonl.
- verify(item, step): the tracker's /api/verify result, None when unreachable or the detector is null; None never permits `ky step`.
- pr(item): `gh pr view <n> --json number,headRefOid,baseRefName,title,state,mergeable,mergeStateStatus,statusCheckRollup,mergeCommit,files,autoMergeRequest` for the last review event's PR, else `gh pr list --head kalayantra/<item, lower case>`; mapped to the shape KV3-B-KYDKINDS-BUILD's module documents (`checks{name: {status, run_id, attempt}}`: run_id, attempt from the check's detailsUrl `…/actions/runs/<run_id>[/attempts/<attempt>]`, else null); no PR → None; any gh failure → `"unknown"`.
- accepted = kyd_kinds_land.accepted_head; priority: owner priority commands, then $KY_RUN/PRIORITY.txt.

**Depends on.** Wave 4: the five module packets; KV3-B-KYLOCK; KV3-B-KYGATE; B-0c kycommands, kyaction, kyloop, kynotify.sh. Tests: real modules, fake commands.

**Acceptance.** `acceptance.command`: the quoted "Tests (B-1)" as engine.json cases (a run directory, the replies of ky, gh, git and the fleet scripts → the expected --dry job list and exit, or commands and states): at least one per listed item, negative case and refusal after J.open (closed refused, slot free).

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydispatch; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDISPATCH: kydispatch.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `claude`, `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
