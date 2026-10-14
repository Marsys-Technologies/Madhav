```json
{"id":"KV3-B-KYBOUNDARY",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§7 verifier boundary; §6 verdict publication","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyboundary.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyboundary.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyboundary.py -q -p no:cacheprovider",
"expected_result":"exit 0; every attack fixture fails inside the boundary and every declared write succeeds",
"negative_cases":[
"Bash edit, chmod-then-write, replace-by-rename, delete-and-recreate of a tracked file: each fails, bytes unchanged",
"git add, commit, update-index, checkout, stash, a write to .git/index, HEAD, config or hooks: each fails",
"a write under $KY_RUN, $KY_FLEET, $KY_ROOT/bin, the item worktree or another job's scratch: each fails",
"control: against a view protected by same-user chmod only the attacks succeed: mechanism rejected",
"a tool child ignoring TERM inside the boundary survives the group kill: the test fails"]},
"packet_sha256":"c8499dd72ad0a9114ff19a01a1316ea7fdb3a6d1de33691a8f8ba3a356e80310"}
```
# KV3-B-KYBOUNDARY v1: `kyboundary.sh` (the enforced verifier boundary)

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's.

**Owns.** The `d1_paths` only (new files). Prohibited: FROZEN paths; `kyjob.sh` (KV3-B-KYJOB); any other path → `blocked`.

**Spec** (verbatim).
```excerpt plan §7
- **Verifier boundary** (enforced, not claimed): the launcher provides a read-only
  source/Git-metadata boundary (a sandboxed verifier worktree whose tracked files and
  `.git` are owned by a separate non-writable mapping — implemented and proven in B-1;
  same-user `chmod` alone is **not** accepted as the boundary), with writes limited to
  declared evidence, caches, `TMPDIR` and the slot DB; acceptance fixtures attempt Bash
  edits, chmod/replace, Git-index changes and shared-control writes and must all fail.
```
```excerpt plan §6
**Verdict publication (controller-owned).** After a VERIFY/ARTIFACT job exits the
controller checks: exit status, reviewed HEAD unchanged, `git status --porcelain` clean,
tracked-file hash set unchanged, boundary evidence (§7). Only then does it publish
`KY_STREAM=V KY_LANE=<vslot> ky verdict …`. A boundary failure never publishes
ACCEPTED. If a published acceptance is later invalidated, an explicit REJECTED is
appended before any queue action.
```
A qualification PASS is not this boundary (kyqualify.py `BOUNDARY`: "not sandboxed — the enforced verifier boundary is a B-1 deliverable"); its review carries to B-1 two proofs: the supervisor's timeout on a job with a live tool child, and the enforced boundary.

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.

**Contract.** F = `$KY_FLEET`, S = `job_scratch`. Read only from the state: `worktree`, `head`, `slot`, `job_scratch`, `tmp_path`.
- `kyboundary.sh prepare <job_id>` builds the verifier's VIEW of the job's worktree at the reviewed head (a null `head`: its HEAD): every tracked file and the Git metadata readable, and not writable by the job through any means its user has. Same-user `chmod` (or `chflags`) alone is NOT a boundary. The view lives under S (a scratch checkout: never a registered worktree, never `/tmp`). Writes `S/boundary.json` `{schema: "ky.boundary/1", mechanism, view, writable[], head, tracked_sha256, prepared_at}`. `writable[]` is exactly: S, named cache directories, `TMPDIR` (`tmp_path`), and what the model program itself must write (named paths, e.g. its session store); the slot DB is reached over loopback (`ky_<slot>`, port 55433), not a path. Exit 0 ready · 1 not established (a partial boundary is never ready) · 64 usage.
- `kyboundary.sh exec <job_id> -- <argv…>`: `cd` to the view and replace itself with argv inside the boundary, in the caller's process group and session; every descendant (each Bash tool child) inherits it. Exit 70 when the prepared boundary is absent or altered. Called by kyjob.sh: `exec F/kyboundary.sh exec <job_id> -- env -i … "$CLAUDE_BIN" …`.
- `kyboundary.sh check <job_id>` (after the job's group is gone) prints one JSON object, the boundary evidence of §6, and writes the same to `S/boundary.check.json`: `{job_id, mechanism, head_unchanged, status_clean, tracked_hashes_unchanged, mechanism_intact, result}` for the view AND the item worktree; `tracked_sha256` = sha256 over the sorted (path, work-tree file sha256) list of tracked files. Exit 0 `result` `intact` · 1 `violated` · 3 `unknown` (anything unobservable). The controller publishes only on 0, passing that file to `kyverdicts.py publish --boundary`.
- `kyboundary.sh release <job_id>`: remove the view; idempotent; 0 only when it is verifiably absent.
- **The mechanism is yours to choose and prove.** The fixtures are the only judge. First, alone and combined, those needing no administrator action (ruling P20); the script's header comment records what you tried, each fixture result and why:
  1. a clone or copy of the head on a read-only mount (APFS snapshot, or disk image attached read-only): writes fail whatever the mode bits, but paths outside the view stay unprotected;
  2. a `sandbox-exec` (Seatbelt) profile around the job: `file-write*` denied except `writable[]`, inherited by descendants; deprecated on macOS, so the tests must show its behaviour on this host.
  If only a dedicated OS user (owning the view, or running the job) passes the fixtures: report `blocked`, naming the exact owner action; creating a user, `sudo` and system settings are an owner hard stop (ruling P20).
- No `sudo`, no system or security setting, no credential. The real program's sign-in and own writes under the boundary are proven at B-2 requalification and B-3; here a fake program stands in.
- INTERPRETATION: the four verbs and both files; the view under S; `check` also covers the item worktree.

**Depends on.** Wave 2; nothing built first. KV3-B-KYJOB calls `prepare`, then `exec`. KV3-B-KYDKINDS-BUILD, KV3-B-KYDKINDS-OPS (and finalize.sh) call `check` once the group is gone; KV3-B-KYDJOBS calls `release` in its terminal path.

**Acceptance.** `acceptance.command`. The plan's fixtures, each a command a Bash tool would run inside `exec`, each asserting that it failed AND the bytes are unchanged (hash) AND `check` exits 0: the three attack classes of the negative cases plus writes to `~/Library/LaunchAgents`. Ruling P28: every attack target is a stand-in under the pytest base (temporary KY roots, HOME redirected there); the suite refuses to run when a target resolves outside it; the control never touches a real path. Detector controls (no result may be a proxy): with the boundary disabled the same attacks succeed and `check` exits 1; the chmod-only view is defeated. Positive: writes to S, a cache directory and `TMPDIR`, a loopback TCP connection, `git log`, `git diff` and reading every tracked file all work. Timeout: a fake program starts `sleep 600` and ignores TERM inside `exec`; a test supervisor sends TERM then KILL to the group and observes `killpg(pgid, 0)` → ESRCH and the child gone by pid and start identity. A fixture that cannot run on this host is `unknown`: acceptance fails.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16), the chosen mechanism and each candidate's fixture results in `notes`. **Branch and PR.** `kalayantra/kv3-b-kyboundary`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYBOUNDARY: verifier boundary"; never merged by the job. **Do not.** Run the real `claude`; leave a mount, image or view behind; force-push. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
