```json
{"id":"KV3-B-KYLOCK",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source under fleet/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§4a.2, §6, §11, §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"clauses.KU-02","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kylock.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kylock.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kylock.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; a second live instance is refused with exit 75",
"negative_cases":[
"a live holder is never displaced (75; cockpit 76)",
"a reused pid with another start time is not the holder",
"an unknown owner is never taken over (77)",
"release without proven database removal keeps the lock (74)"]},
"packet_sha256":"58d404dc12f009ba45f32938d9ab66dc4e5ee2befc619b9884e20326b91a9838"}
```
**Pins.** Plan v2.7 @ `e709f60d7`; base = the reviewed B-0c head (job header).

**Owns.** The two `d1_paths`: `kylock.sh` (git mode 100755, `#!/bin/bash`, bash 3.2; the logic may be one embedded stdlib `python3 -I -B` program importing no sibling) and its tests. Prohibited: FROZEN paths.

**Spec (verbatim).**
```excerpt plan §6
atomic instance lock via
`kylock.sh` (session identity + PID/PGID + process-start identity)
```
```excerpt plan §11
`kylock.sh acquire conductor <controller identity>`: `mkdir`-atomic, records PID/PGID and
process-start identity; a transient tool-shell PID is never an identity
```
```excerpt plan §4a.2
The controller holds the role lock with its own and its
   child's PID/PGID/start identities
```
```excerpt plan §4a.2
closing a cockpit neither
   adopts nor deletes another session's databases.
```
KU-02 (label `kylock`), verbatim:
<!--KU-02-->
Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.

Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.
<!--/KU-02-->
Ruling R2, restated (binding; as kyloop.py `process_matches`, `lock_create`, `lock_bury` at base): liveness is True | False (POSITIVELY gone: no such process, a zombie, another start identity) | None (unknown). Take over ONLY on False; unknown is never taken over, never removed by age. A lock never exists without its owner: `owner.json` is built in a private directory and renamed onto the lock path exclusively. Takeover is verify-after-rename under `flock` on `locks/.takeover.guard`: grave, re-read, remove only if id, pid and start are those judged, else put back. A gone owner's `child` is gone only if its leader is positively gone AND `killpg(pgid, 0)` finds none; `"pending"` or unidentified never is.

**Contract.** Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`), `KY_FLEET` (default: the script's directory). Lock = directory `$KY_RUN/locks/<role>`, role `^[a-z][a-z0-9_]{0,31}$`; identity `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else 70.
`owner.json` keys, exactly (kyloop.py `owner_doc`): `session_or_run_id`, `holder_kind` (`controller` | `cockpit`), `pid`, `pgid`, `process_start` (`LC_ALL=C /bin/ps -o lstart=` text), `acquired_at` (UTC `…Z`), `child` (null | `"pending"` | `{run_id, pid, pgid, process_start}`). An existing owner without `holder_kind` or `child` (kyaction.py writes neither) reads as non-cockpit, no child.
Holder (INTERPRETATION of §11's last clause): the nearest ancestor of kylock.sh that is not a shell (command basename, leading `-` dropped: sh, bash, zsh, dash, ksh). An identity `CTL-…-<pid>` (kyloop.py's form) is a `controller` and `<pid>` must be the holder pid; any other identity is a `cockpit` session id.
One stdout line per call, `kylock: <verb> role= state= holder= pid=`; reasons on stderr.
- `acquire <role> <identity>`: 0 `acquired` (+ `took_over=<old id>`); 75 live non-cockpit owner or lost race; 76 live cockpit; 77 owner unknown, untouched; 70 holder unidentifiable or identity/pid disagree, nothing written; 64 usage.
- `release <role> <identity>`: the caller must be the recorded owner (id, holder pid, start), else 73. Then the KU-02 step `/bin/bash "$KY_FLEET/local_db.sh" close --session <identity>` (900 s; needs `KY_SCRATCH`). Only its exit 0 buries the lock (ruling P26): 0 `released`. Missing, non-zero or timed out: 74, lock KEPT, naming the session whose databases remain. A takeover never runs this step.
- `child <role> <identity> pending|none|<JSON>`: owner only (73); atomic rewrite of `child` (INTERPRETATION from §4a.2 and the B-0c loops review's carried obligation).
- `status <role>`: `state=free|live|cockpit|gone|unknown`; exit 0; changes nothing.
Tests-only hook `KY_LOCK_PS` (absolute path replacing `/bin/ps`): the line ends `test_hook=ps`; refused when `KY_RUN` is `/Users/Dev/kalayantra/run`.
Existing call forms: kyloop.py `acquire_lock`: `subprocess.run([str(kylock), "acquire", self.role, self.controller_id], …)` (only if executable; 0 = acquired); `release_lock`: the same with `"release"`, exit ignored (no `child` call yet: B-0c part 2). kycommands.py `holds_role_lock(run_dir, role, applier_id)` (kyveto.py `tick` too): id equal, `process_matches(pid, process_start)` True, pid = the caller or an ancestor. Cockpit prompt: `kylock.sh acquire planner <your session id>`.

**Depends on.** Wave 1; nothing. Assumed of KV3-B-LOCALDB (same wave; tests use a double): `local_db.sh close --session S`: exit 0 = S's databases gone and the container removed, handed over on record, absent, or incompatible and untouched (`container=removed|handed_over|absent|incompatible`); exit 1 = not proven.

**Acceptance.** The front-matter command; tests first, real script, temp `KY_RUN` / `KY_FLEET`:
1. `acquire` called as kyloop.py does writes exactly those keys, pid = the calling non-shell process; the real `kycommands.holds_role_lock` is `(True, None)` there, False in an unrelated process; through `sh -c` still the non-shell ancestor; `CTL-…-<pid>` with another pid: 70; identity empty, `..`, slash or quote: 70.
2. Second live instance 75, live cockpit 76, lock bytes unchanged; N concurrent acquirers: exactly one 0.
3. Reused pid with another start: taken over; a lock changing hands between judgement and rename is put back.
4. 77, nothing removed, however old: a bare `mkdir` lock, unreadable owner.json, null pid, ps failing or hanging, gone owner with a pending, alive or unidentified child.
5. Release: non-owner 73; database step failing, missing or hanging 74, lock kept (KU-02 "stop-without-removal"); success: the double ran once with the identity, lock gone; never on takeover.
6. `child` and `status` as specified.
KU-02's wrong-mount, stale-READY and ownership-conflict tests: KV3-B-LOCALDB. Every printed state comes from the R2 detector or the database step's observed exit; unknown never reads `free`, `gone` or `released`.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): each command, exit code, summary; branch; pushed 40-hex `head_sha`; `pr_number`.

**Branch and PR.** `kalayantra/kv3-b-kylock`; one PR to main, "KĀLA-YANTRA v3 KV3-B-KYLOCK: kylock.sh"; never merged, queued or approved by the job (hold).

**Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the tracker, the real `local_db.sh`. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time; signal-0 probes only.
