```json
{"id":"KV3-B-KYDADMIT",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§5 base contract; §6 admission; §8.6","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"KU-02","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_admit.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_admit.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/admit.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_admit.py -q -p no:cacheprovider",
"expected_result":"exit 0; every case of admit.json yields its expected refusal codes",
"negative_cases":[
"no fresh tracker reading this tick: every intent refused, code stale",
"a READY receipt of another session, a stale one, a wrong mount: slot refused",
"missing code, or a changed head→merge mapping: base refused"]},
"packet_sha256":"ddedd7276b8c73682f6dff6d1ac3a6818abeae17d13d2b089095fb2277a859ec"}
```
# KV3-B-KYDADMIT v1: kyd_admit.py

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The d1_paths only (new). Prohibited: FROZEN paths; installed trees; any other path → blocked.

**Spec** (verbatim).
```excerpt plan §6
**Admission checks (replace LIVENESS):** tracker freshness, assigned worktree present
and locked, disposable slot DB READY with bound hashes, packet admitted by `kypacket.py`
(§8), base contains prerequisite heads, routing recomputed, turn/time caps set.
```
```excerpt plan §5
- **Base contract (KT-04):** each job record carries worktree, branch, `base_sha`, its test
  digests and, for each code prerequisite, the accepted final PR head and — once merged —
  the observed mapping from that head to `mergeCommit.oid` (squash). Admission requires
  either the accepted head or the verified corresponding merge commit to be contained in
  the job base; missing, changed or unverified mappings refuse admission. Artifact and
  schema prerequisites use their typed acceptance receipts, never invented Git heads.
  Tracker readiness alone does not prove code availability. Tests: accepted unmerged
  stacks, squash-landed prerequisites, missing code, incorrect head→merge mappings.
```
```excerpt plan §8.6
**At admission** the dispatcher installs
   missing tests idempotently into the item branch and classifies the current result:
   expected-red → new implementation; already-green → an independent already-satisfied
   assessment (ARTIFACT), never automatic rejection or completion; REWORK and inherited
   heads keep their evidence history and run the relevant regression checks.
```
KU-02, label `dispatcher-ready-receipts`, verbatim:
```
Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.

Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.
Time keys (deadline, renewed_at, ended_at): UTC text `YYYY-MM-DDTHH:MM:SSZ`; any other form is unknown and refuses.

**Contract.** ctx: paths root run fleet scratch repo; model; controller_id; now(); sh(argv, env=None, cwd=None, timeout=120) → (rc, out, err) (rc None: unknown); next (fresh ky next --json); pr(item) → the PR (head, state, merge_commit, …); accepted(item) → {head, via}; both also None or "unknown"; limits{builders, verifiers, copies}; awaiting(slug, question, options, evidence, item, class_hint).
Intent fields used: kind item role pool tier packet runner locks[]. Each returns {admitted, refusals[{code, detail}], facts}; unknown refuses.
- precheck(ctx, intent, slot): read-only, all checks run:
  - stale: ctx.next is None.
  - packet (intents with one; others: opus): python3 -B fleet/kypacket.py check <packet> --repo <repo> is not 0. facts.tests[], facts.test_digests[]: its test_commits[] path and digest strings.
  - routing (the same intents): python3 -B fleet/kyroute.py packet --packet P --model M --repo R (M: ctx.model); 0 → facts.tier, the higher of its tier and the intent's; 3 → freeze: <path>. facts.migration: the item's brief.migration in M; null if absent or NONE.
  - launch (model runners; I): $KY_RUN/QUALIFICATIONS/<role>-<model>.json (claude-sonnet-5-5 for tier sonnet, else claude-opus-5-5) is PASS, context launchd; facts.launch = the launch keys model … disallowed_tools: from its binds (extra_flags), but deadline (now + deadline_seconds), mcp_config (fleet/mcp.none.json, or mcp.marsys-only.json for chart data; the bound sha256); max_turns > 0, ≤ the kind's §7 cap (ARTIFACT 60, SURROGATE 30, MODEL and REQUEST-PREP 300).
  - base: the base contract; facts.base_sha = the worktree's HEAD, else repo HEAD; heads from ctx.accepted, the mapping from ctx.pr; facts.prerequisites[].
  - slot_not_ready, slot_foreign (KU-02): $KY_RUN/local_db/<slot>.json is READY, three seed hashes, session_id = controller_id, and bash fleet/local_db.sh check <slot> exits 0 now.
  - ceiling: a new worktree would exceed limits.copies own copies or 14 in all (git worktree list --porcelain).
- provision(ctx, slot), for a slot with no receipt or this session's non-READY one: bash fleet/local_db.sh up --session <controller_id>, then db <slot> --session <controller_id>. Another session's database is never adopted, reset or removed (awaiting).
- admit(ctx, job), after kyd_jobs.open: worktree, for a job holding item.<item> (registered, on the job's branch, that lock owned by controller_id); then (BUILD, feature packet; §8.6): missing test_commits[] files added and committed; KY_ITEM=<item> TESTS=<paths> bash fleet/precheck.sh --item in the worktree: 0 → already_green (refused; ARTIFACT: KV3-B-KYDKINDS-BUILD), 1 with expected_failing_assertion in the output → expected_red, else unclassified (refused) (I); $KY_RUN/admission/<item>.json = {item, base_sha, test_digests, result}.

**Depends on.** Wave 3. KV3-B-KYPACKET, KV3-B-KYROUTE, KV3-B-LOCALDB, KV3-B-PRECHECK: commands above.

**Acceptance.** ctx a double over throwaway repositories; admit.json cases: an admitted intent per pool; each code alone; the four base tests; KU-02's wrong mount, stale READY receipt, ownership conflict; the classifications; those three facts present, absent.

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydadmit; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDADMIT: kyd_admit.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh, docker or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
