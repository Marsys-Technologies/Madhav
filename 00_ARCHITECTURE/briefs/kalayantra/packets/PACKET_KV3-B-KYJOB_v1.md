```json
{"id":"KV3-B-KYJOB",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§7 except the verifier boundary","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyjob.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyjob.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyjob.py -q -p no:cacheprovider",
"expected_result":"exit 0; the fake program sees exactly the quoted argv and allowed names",
"negative_cases":[
"a credential variable name set, or a wrapper in $KY_ROOT/bin: exit 78, nothing launched",
"turn limit or deadline missing, --bare, a receipt missing, not PASS or with one bind unequal: exit 65",
"a tool child that ignores TERM survives the supervisor's group kill: the test fails"]},
"packet_sha256":"443bf430cbe0039bc172accd5f4d21d1539354958d430ca32da53911f527b083"}
```
# KV3-B-KYJOB v1: kyjob.sh

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The d1_paths only (new). §7's verifier boundary is KV3-B-KYBOUNDARY's. Prohibited: FROZEN paths; installed trees; any other path → blocked.

**Spec** (verbatim).
```excerpt plan §7
# all values from $KY_RUN/jobs/<job_id>/state.json; every path absolute
cd "$WORKTREE" || exit 70
exec env -i HOME="$HOME" PATH="$KY_ROOT/bin:$NODE_BIN:/opt/homebrew/bin:/usr/bin:/bin" \
  LANG=en_US.UTF-8 TERM=dumb USER="$USER" TMPDIR="$TMP_PATH" \
  ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \
  KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \
  SE_EPHE_PATH="$SE_EPHE_PATH" SWE_EPHE_PATH="$SWE_EPHE_PATH" TESTS="$TESTS_NEWLINE_LIST" \
  "$CLAUDE_BIN" -p --setting-sources project --permission-mode "$PERMISSION_MODE" \
    --model "$MODEL" --effort "$EFFORT" --max-turns "$MAX_TURNS" $EXTRA_LEAN_FLAGS \
    --strict-mcp-config --mcp-config "$MCP_CONFIG" $DISALLOWED \
    --output-format stream-json --verbose --add-dir "$KY_ROOT" \
    < "$PROMPT_PATH" > "$STDOUT_PATH" 2> "$STDERR_PATH"
```
```excerpt plan §7
- `EFFORT` is role-specific: `xhigh` for PLAN, `high` otherwise. `PERMISSION_MODE` is always
  passed explicitly (`bypassPermissions` for builders and bootstrap jobs; never inherited —
  the host's user settings default to it). **P-1:** `--bare` never reads the stored sign-in
  and accepts only an API key, which §7 forbids, so no `--bare` job can start
```
```excerpt plan §7
**Launch qualification (KV-06):** a launch configuration is usable only with a
  passing qualification receipt (`run/QUALIFICATIONS/<role>-<model>.json`) bound to the
  resolved executable path and hash, version, exact argv, model/effort, role permissions,
  working directory, environment policy and prompt/configuration hashes. Missing or
  non-positive turn limits or wall-clock deadlines refuse launch for every role, SURROGATE
  and both loop roles included.
```
```excerpt plan §7
- `kyjob.sh` exits 78 if `DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY` is set
  in its own environment; `no_wrappers` behaviour preserved (tested). For fixture runs it
  forwards the validated `PRAVAHA_*` fixture configuration (§14 B-3).
- `MCP_CONFIG` (KT-02): bootstrap jobs use the independently reviewed, manifest-hashed
  empty configuration `{"mcpServers":{}}` staged in the bootstrap source tree
  (`fleet/mcp.none.json`), recorded per job as an absolute path; campaign jobs use the
  installed configuration whose hash is in the installation receipt (`mcp.none.json`
  unless the packet declares `needs_chart_data: true` → `mcp.marsys-only.json`).
```
```excerpt plan §7
- Turn caps: BUILD 150, REWORK 100, VERIFY 60, PRE-ACCEPT/POST-READBACK 40, RULING 30,
  PLAN 300.
- Session persistence stays on (reconciliation evidence, §13).
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.
Time keys (deadline, renewed_at, ended_at): UTC text `YYYY-MM-DDTHH:MM:SSZ`; any other form is unknown and refuses.

**Contract.** R = $KY_RUN, F = $KY_FLEET, S = job_scratch.
- bash F/kyjob.sh <job_id> reads the launch keys of R/jobs/<job_id>/state.json, writes no state, and execs the quoted line: no fork, no background, no new session, so its caller's process-group kill reaches every tool child. Its caller (kyd_jobs.py; finalize.sh) starts it in a new session and owns the deadline.
- TESTS = tests[] joined by newlines (the manifest precheck.sh consumes); argv as kyboot.py build_launch; NODE_BIN as kyloop.py child_path. A null key omits its variable or flag.
- Environment (I), extending the quoted line: KY_SCRATCH and JOB_SCRATCH (= S = $KY_SCRATCH/jobs/<job_id>), and KY_RUN_ID (= job_id), KY_ROLE (= role), KY_CONTROLLER_ID (= controller_id). Fixture runs add the validated PRAVAHA_* from fixture{}. Nothing else survives.
- Refusals precede any launch; each writes S/kyjob.refusal.json {job_id, code, reason, at} and one stderr line:
  - 64 usage · 70 cd "$WORKTREE" failed.
  - 78: a name matching the quoted pattern in its own environment (names only); no_wrappers (as kalayantra_fleet.sh): a file in $KY_ROOT/bin other than ky, kybrief.
  - 65 (I) + reason: state (unreadable, a launch key absent, a relative path) · limits (max_turns ≤ 0 or above the kind's cap; ARTIFACT 60, SURROGATE 30, MODEL and REQUEST-PREP 300 (I); deadline missing or past) · flags (--bare, a launcher-owned flag in extra_lean_flags, effort not xhigh for PLAN, MODEL, REQUEST-PREP and high otherwise, no permission mode) · program (not executable, version < 2.1.296) · mcp (lookup: the components[] entry of R/INSTALL_RECEIPT.json whose installed_path equals mcp_config, its sha256 equal to the file's; no entry, or two → refuse) · prompt (not the bytes of card_path, then packet_path, then a header) · boundary · qualification.
- Qualification gate (kyboot.py's receipt check): R/QUALIFICATIONS/<role>-<model>.json is a ky.qualification/1, result exactly "PASS", context "launchd" (I), this role and model, binds equal to this launch for every name in kyboot.py's BOUND_FACTS and the launch line flag for flag (portable_argv); deadline ≤ now + binds.deadline_seconds. A missing bind or unobservable value refuses.
- boundary verifier: F/kyboundary.sh prepare <job_id> (non-zero → 65 boundary), then exec F/kyboundary.sh exec <job_id> -- env -i … "$CLAUDE_BIN" …; never an unsandboxed fallback.
- Just before exec: S/kyjob.launch.json {job_id, cwd, argv, env_names, qualification_sha256, at} (I).

**Depends on.** Wave 3. KV3-B-KYDJOBS (the state); KV3-B-KYBOUNDARY (prepare: 0 = ready; exec becomes argv inside the boundary); KV3-B-INSTALL (the receipt). Tests fake all.

**Acceptance.** acceptance.command. The test's fake program records argv, environment names, cwd, stdin, pid: the quoted order, exactly the allowed names, stdin = the prompt, cwd = the worktree, pid = kyjob.sh's. One test per refusal and negative case. Qualification review's obligation: the fake starts sleep 600 and ignores TERM; a test supervisor starts kyjob.sh in a new session, sends TERM then KILL to the group, and must see killpg(pgid, 0) → ESRCH and the child gone by pid and start identity. Unknown refuses.

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kyjob; one PR to main "KĀLA-YANTRA v3 KV3-B-KYJOB: kyjob.sh"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude; force-push; read credentials or print a variable's value. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
