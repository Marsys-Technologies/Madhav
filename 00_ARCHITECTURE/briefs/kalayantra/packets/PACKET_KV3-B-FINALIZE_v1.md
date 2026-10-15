```json
{"id":"KV3-B-FINALIZE",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§12; §4a.2","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"KU-02","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/finalize.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/finalizer_cases.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_finalize_v3.py"],
"acceptance":{
"command":"python3 -B 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/finalizer_cases.py && python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_finalize_v3.py -q -p no:cacheprovider",
"expected_result":"exit 0: every case passes",
"negative_cases":[
"job group alive past its deadline or of unknown identity: DRAIN FAILED, nothing removed, no ky done",
"receipt changed after review, reviewer not independent or not stream V, boundary violated or unknown, or anything present at the recheck: no verdict",
"close exits 0 `container=handed_over`, or receipts gone but a database survives: FAILED",
"KU-02: wrong mount, stale READY receipt, ownership conflict, stop-without-removal: not ACCEPTED"]},
"packet_sha256":"9eb73c8d00dbe89ffe44120a5e14cd4eab56cd784d8fb4392e353196517242ec"}
```
# KV3-B-FINALIZE: `finalize.sh` v3

**Pins.** Plan v2.7 @ e709f60d7; base = the reviewed B-0c head (job header).

**Owns.** The `d1_paths`; `finalize.sh` is a delta (keep its two phases, `receipt()` keys, never-remove rules). Prohibited: FROZEN paths; any other path → `blocked`.

**Spec (verbatim).**
```excerpt plan §12
`finalize.sh` v3: stop new admissions; drain or terminate recorded job groups within
their deadlines, preserving dirty/unpushed work; verify process identity by recorded
PID/PGID + process-start identity; write `$KY_RUN/DRAIN_RECEIPT.json` from measured drain
facts; a finalizer-owned, bounded independent reviewer (headless Opus, different
identity) accepts its exact digest; then `KY_STREAM=S ky done C-3 --artifact-path
"$KY_RUN/DRAIN_RECEIPT.json"`. Remove eligible owned item worktrees and session DBs;
write `$KY_RUN/FINAL_RECEIPT.json` binding the accepted drain digest, close-report
evidence and physical-absence observations; one bounded independent close review
outside ordinary dispatch (bound external review where the V-owned item requires it);
after it exits, independently recheck process, worktree and DB absence; publish its
digest-bound verdict only if the receipt is unchanged; then `KY_STREAM=S ky done C-4
--artifact-path "$KY_RUN/FINAL_RECEIPT.json"`. The tracker stays available throughout.
Any survivor, changed receipt, missing close claim or failed cleanup prevents acceptance.
```
KU-02 (label `finalize-v3`):
Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.

Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.

**Contract.** R = $KY_RUN, F = $KY_FLEET, ky = $KY_ROOT/bin/ky.
- bash finalize.sh (an argument → exit 64). Run by executor.py execute() (op finalize) as ["bash", <temporary copy>], cwd $KY_ROOT, env = its CHILD_ENV_ALLOW + SE_EPHE_PATH + KY_ROOT only, 21600 s: no dirname "$0"; R, F default from $KY_ROOT; KY_SCRATCH, KY_SOURCE_REPO as kyctl.sh l.65–67. Exit 0 only after C-4's guarded completion, else 1. KY_* knobs kept.
- Each ky event and reviewer launch is a kyaction record (F/kyaction.py, actor {role: "finalizer", holder_kind: "supervisor", controller_id}); a re-run reconciles by observation.
- Steps; a failed one writes its receipt with result: "FAILED" and exits 1:
 1. bash F/kyctl.sh stop <loop> for dispatcher, planner, conductor, veto; 0 = confirmed.
 2. Each R/jobs/*/state.json with phase ≠ ended (keys job_id item slot worktree pid pgid process_start deadline. Time keys (deadline, renewed_at, ended_at): UTC text `YYYY-MM-DDTHH:MM:SSZ`; any other form is unknown and refuses.): wait for its end or deadline (cap KY_DRAIN_WAIT_MIN), then TERM → 20 s → KILL the group, only if kyaction.process_matches(pid, process_start) is True. Gone = leader False AND killpg(pgid, 0) → ESRCH. Unknown is never signalled, never gone: busy_kept.
 3. Each worktree (never $KY_SOURCE_REPO): absent | clean | dirty_kept | unpushed_kept | busy_kept.
 4. R/DRAIN_RECEIPT.json, write-then-rename: today's keys + schema, loops{}, jobs[]; lanes = {worktree basename: state}. ACCEPTED only if every loop stopped, every group gone, nothing kept.
 5. Reviewer: kyverdicts.py snapshot; write a job state (kind ARTIFACT, stream V, a verifier slot, max_turns 60, deadline ≤ 3600 s); run bash F/kyjob.sh <job_id> in its own process group; kill the group at the deadline; confirm gone. Publish only through python3 F/kyverdicts.py publish (C-3, phase artifact, the receipt's sha256 and path, --boundary = the JSON of bash F/kyboundary.sh check <job_id>, which must exit 0; 1 or 3: no verdict). ACCEPTED: §12's ky done C-3; else stop.
 6. Clean + pushed worktrees: git -C "$KY_SOURCE_REPO" worktree remove <path> (no --force, no rm -rf), worktree prune: removed | remove_failed. Then bash F/local_db.sh close --session <id> per session_id in R/local_db/*.json (none: once, its own session name).
 7. R/FINAL_RECEIPT.json: today's keys + schema, drain_sha256, close_report{path, sha256} (C-1), absence{processes, worktrees, databases} measured now; databases: absent only if a close ran now and each exits 0 with container=removed|absent|incompatible; handed_over, exit 1 or no call = survivor, FAILED.
 8. C-4 is V-owned: KY_STREAM=V KY_LANE=<vslot> ky claim C-4 --worker <vslot> --lease 10800; review as 5 (--external-review-path/-sha256 where required); after exit re-measure absence and the receipt, any change → no verdict; publish as 5; KY_LANE=<vslot> ky release; §12's ky done C-4; FINAL_MESSAGE.md as today.
- Kept: $KY_PRAVAHA_RUN/RUNNER_STOP_{A,B,C}; campaign checkout, branches, evidence never removed.
- INTERPRETATION: step 1 stops all four loops; dirty or unpushed fails the drain; "close claim" = step 8's V claim; a removal failure surfaces in FINAL.

**Depends on.** Wave 3; tests fake all. KV3-B-KYJOB, KV3-B-KYDJOBS (same wave): `kyjob.sh <job_id>` runs the model from the job state under the stream-V boundary; step 2's keys. KV3-B-KYBOUNDARY, KV3-B-KYVERDICTS (wave 2): as step 5. KV3-B-LOCALDB (wave 1), `close --session S`: exit 0 = S's databases gone and the container removed, handed over on record, absent, or incompatible and untouched (`container=removed|handed_over|absent|incompatible`); exit 1 = not proven.

**Acceptance.** finalizer_cases.py keeps its five cases on v3 inputs (job states + a live process group replace lane flocks; scratch: $JOB_SCRATCH): busy, dirty → rc ≠ 0, drain FAILED, no FINAL_RECEIPT, path kept; remove_failure → drain ACCEPTED, final FAILED remove_failed, path kept; v1_busy (reviewer group not gone) → final FAILED; accepted → rc 0, both ACCEPTED, worktree gone, campaign .git kept; RUNNER_STOP_A in all. test_finalize_v3.py: each negative case; no V claim on C-4; lone copy; crash between verdict and ky done, re-run. A result is measured in that run; unknown is FAILED.

**Evidence.** `result.json`: each command, exit code; the pushed 40-hex head.

**Branch and PR.** `kalayantra/kv3-b-finalize`; one PR to main "KĀLA-YANTRA v3 KV3-B-FINALIZE: finalize.sh v3"; never merged by the job.

**Do not.** Rebase or force-push; read credentials; touch production or docker. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
