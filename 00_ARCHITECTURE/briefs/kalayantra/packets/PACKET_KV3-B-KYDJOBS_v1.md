```json
{"id":"KV3-B-KYDJOBS",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§5 KT-08; §6","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_jobs.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_jobs.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/jobs.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_jobs.py -q -p no:cacheprovider",
"expected_result":"exit 0; every case of jobs.json ends in its expected state sequence",
"negative_cases":[
"a restart between result persistence and claim release: one ky release in all",
"the claim file names another claim_id: no release, slot kept",
"an unknown process state: never gone, never reaped"]},
"packet_sha256":"f49bd7a43abad08112dd3d7fb0d91acf6845bebd9cdbf4b43cd0662998a06a1b"}
```
# KV3-B-KYDJOBS v1: kyd_jobs.py

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The d1_paths only (new). Prohibited: FROZEN paths; installed trees; any other path → blocked.

**Spec.**
```excerpt plan §5
each job records `JOB_SCRATCH=$KY_SCRATCH/jobs/$JOB_ID`
  and absolute `prompt_path`, `stdout_path`, `stderr_path`, `tmp_path` beneath it, created
  before launch and used for stdin, logs and `TMPDIR`.
```
```excerpt plan §6
Recovery: jobs recorded live
whose process group (PID/PGID + start identity) is gone → release claim, `interrupted`,
re-queue once.
```
```excerpt plan §6
**Claims, locks, renewals.** Only the owning stream claims; the dispatcher renews only
jobs that hold claims (`KY_LANE=<slot> ky renew --lease 10800` every 20 min); timeout →
reap the process group (PID/PGID + start identity) → release → `timed_out`. Job identity
(`job_id`, provider `session_id` when observed — never invented before launch —, item,
kind, slot, head/digest, evidence-fp, failure-class fingerprint and attempt count) is
persisted in `run/jobs/<job_id>/state.json`. On adoption, legacy claims, PRs and
checkpoints are reconciled into job state (B-2).
**Terminal release (KT-07):** every terminal job path (success, blocked exit, timeout,
interruption) persists its result and checkpoint, confirms the recorded process group has
exited, and releases any held tracker claim **before** freeing the slot; successful
`ky review` registration is not claim release. Release is bound to the job's persisted
item, worker and `claim_id`: the controller verifies that `run/claims/<slot>.json`
matches the job before `KY_LANE="$SLOT" ky release`, serialises release with slot reuse,
and on mismatch keeps the slot unavailable and reports "reconciliation required".
Renewal stops once termination begins. Claimless verifiers release only their job/item
locks. Tests: three successive successful BUILD jobs on one slot; immediate REWORK after
review; blocked exit; restart between checkpoint persistence and claim release.
```
```excerpt plan §6
**Failure accounting:** failure-class fingerprints and attempt counts persist across
retries, escalation, restart and repacketisation; the third identical failure blocks
automatic attempts until a recorded changed condition permits retry.
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.
Time keys (deadline, renewed_at, ended_at): UTC text `YYYY-MM-DDTHH:MM:SSZ`; any other form is unknown and refuses.
job_id = `J-<UTC yyyymmddThhmmssZ>-<slot, else kind in lower case>[.<n>]` (I), created exclusively.

**Contract.** ctx: paths root run fleet scratch repo; controller_id; sh(argv, env=None, cwd=None, timeout=120) → (rc, out, err) (rc None: unknown); ky(*args, stream=None, lane=None); act(id, kind, inputs, target, effect, observer) → (done | failed | unknown, result); awaiting(slug, question, options, evidence, item, class_hint); journal(event, text).
Intent fields: kind item key stream role claim locks[] card packet header{}; launch keys in header go into the job state, overriding the fact of the same name (REGEN keeps its header base_sha). Result: {outcome, detail, failure_fp}.
ky calls pass stream, lane=slot.
- load(ctx) -> all job states, oldest first (install.sh's legacy-<n> too); unreadable -> raise JobsUnreadable.
- attempts(ctx, intent) -> {attempt, blocked} from $KY_RUN/jobs/failures.json {item: {failure_fp: {count, evidence_fp}}} (never reset; quota not counted): blocked at count ≥ 3 with an unchanged evidence_fp (I), or after two interrupted jobs of the key.
- open(ctx, intent, slot, facts) -> a prepared job, or None with all undone: lock job.<key> (kyaction.acquire_lock), then a fresh look ($KY_RUN/handled/job.<key>.json, or a job of that key or slot not ended -> None); locks[]; claim: ky claim <item> --worker <slot> --lease 10800, claim_id from stdout; worktree: with item.<item> in locks[], /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item, lower case> on branch kalayantra/<same> (I), added at facts.base_sha if absent; else repo; facts.migration not null: python3 fleet/kyalloc.py reserve --item I --branch B --repo R -> numbers[0]; scratch/jobs/<job_id>/ with prompt.md, stdout.jsonl, stderr.log, tmp/; prompt = card bytes, packet bytes, the line `--- job header ---`, one JSON object (the §7 header fields, header); facts.launch -> model … disallowed_tools, the other facts -> their keys; verifier pool -> boundary verifier.
- launch(ctx, job): in act("ACT-launch-<job_id>", …): persist pid "pending"; Popen(["/bin/bash", fleet/"kyjob.sh", job_id], stdin=DEVNULL, start_new_session=True); then pid pgid process_start, live. A stale "pending" is never gone, never relaunched.
- supervise(ctx) -> jobs now terminating. Per live job kyloop.job_state(pid, pgid, process_start): unknown, survivors -> awaiting only; renewal and timeout as quoted (TERM the group, 10 s, KILL); gone -> exit_code (null if adopted), result_path (a regular result.json valid as ky.job_result/1), provider_session_id (kyloop.provider_session), result_event; kyjob.refusal.json -> refused; kyloop.detect_quota -> failure_fp quota.
- recover(ctx), jobs of an earlier controller_id: prepared (pid null) -> close, outcome refused; terminating -> close; live: gone -> interrupted, close; live -> adopted; JOB-<job_id>-* action records settled as kyloop.py does.
- close(ctx, job, result) = the KT-07 paragraph in its order, each step persisted before the next (a restart resumes at the first unfinished); before the claim step, boundary -> bash fleet/kyboundary.sh release <job_id>; after the locks, done writes the handled record (I); then ended.

**Depends on.** Wave 3. KV3-B-KYJOB, KV3-B-KYBOUNDARY, KV3-B-KYALLOC; KV3-B-KYDADMIT: facts = {tier, launch{}, base_sha, prerequisites[], tests[], test_digests[], migration}.

**Acceptance.** ctx a recording double; fake kyjob.sh scripts are the jobs; jobs.json cases: the four KT-07 tests (a restart between each pair of close steps); the negative cases; recovery of a gone, live, unknown, prepared and terminating job; a refusal after open (closed refused, slot free); facts with and without tests[], test_digests[], migration; counts surviving restart; a REGEN intent whose header.base_sha differs from facts.base_sha.

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydjobs; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDJOBS: kyd_jobs.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude, ky, gh or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
