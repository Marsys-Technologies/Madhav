```json
{"id":"KV3-B-KYJOB-ENGINES","kind":"bootstrap","wave":"B","build_tier":"opus",
"routing_reason":"D-1 fleet control plane",
"needs_chart_data":false,"max_loops":3,"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§6 registration/release; §7 launch; §8 packets","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,"pw_mechanism_version":null,"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyjob.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_jobs.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyjob_engines.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/cards/KARAKA.md",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyjob.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyjob_engines.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_jobs.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyjob_engines.py -q -p no:cacheprovider --basetemp=$JOB_SCRATCH/pytest",
"expected_result":"exit 0; fixtures/regressions pass",
"negative_cases":[
"test_unknown_engine_or_mixed_config",
"test_claude_bytes_changed",
"test_full_without_explicit_selection",
"test_full_argv_or_record_changed",
"test_builder_commit_or_push",
"test_git_pointer_redirect",
"test_result_schema_or_identity",
"test_exit_turn_or_group_not_clean",
"test_scope_or_queue_authorisation",
"test_locked_socket_job_failure",
"test_stall_term_ignoring_child",
"test_restart_each_finish_step",
"test_origin_main_conflict_no_merge",
"test_claim_actor_head_pr_mismatch"]},
"packet_sha256":"5c244a7bf65d92b19e499e30eb323960b89fac5f4640f55548d1df3554170a79"}
```
# KV3-B-KYJOB-ENGINES v1: engine-aware campaign jobs

**Pins.** Plan v2.7 @ e709f60d7; base: job header. F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; E = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/` + F; S = `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3`; C = S + `/engines/launchers/cockpit`; R = S + `/reviews/b0c-engines`; P = `/Users/Dev/kalayantra/run/PLANNER_STATE.json`. E/C/R not runtime imports.

**Owns.** d1_paths only; other edits block; boundary/build-kind/schemas/E unchanged.

**Spec** (plan §7:504).
```excerpt plan §7
- Session persistence stays on (reconciliation evidence, §13).
```
**Authority.** CLAUDE.md §I/§N; cockpit records `P:761,806`, active.owner_directions_engines and active.owner_direction_lean_20261012T1620Z, supersede owner-decisions file decision 7 ("all Claude", `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md:16`); do not edit it. 2026-10-12 owner direction: wrong actions/lost work only. Codex: no receipt/companion evidence/live-qualification gate. Claude receipts unchanged. This job's eight rulings apply.

**Job state.** facts.launch / intent.header (`F/kyd_jobs.py:115-132,452-467,625-637`); persist/hash inputs. (I) INTERPRETATION: names engine, absolute launch_config_path, sandbox_mode locked/full, stall_seconds; header precedence unchanged. Absent engine = claude, legacy bytes unchanged; null/unknown refuses before launch, no fallback/inference. Codex BUILD/REWORK/VERIFY; pools/claims/locks unchanged. Locked default; controller sandbox_mode=full alone admits full, only for process tools/loopback/local test DB. (I) INTERPRETATION: checkpoint guards/activity/finish progress (`:1066-1080`); Codex state/every record: engine/mode; full says `sandbox: full (owner direction 2026-10-12)`, locked says locked. Annotate controller observations; raw result intact.

**Contract.**
- Claude byte-identical argv/env/prompt/stdin/cwd/PID/PGID/receipts/refusals/parsing (`F/kyjob.sh:129-146,730-756`; `F/kyd_jobs.py:778-825,904-917`). (I) INTERPRETATION: baseline/new byte comparisons, legacy/explicit-Claude; schema unchanged.
- Codex engine_of/validate_codex_config/build_argv(cfg, job_scratch), never retype argv (`E/kyqualify.py:616-618,663-775,820-864`). Locked base/config engine match; gpt-6.1-sol/high, never-approval/disabled features/sign-in/deadline, no turn cap. Reject credentials/mixed fields (`:442-448,663-668`); keep no_wrappers/exec (`F/kyjob.sh:129-146,730-751`).
- Locked workspace-write/network off: source/scratch, no writable Git dirs; verifier job-rooted/absolute reads (`E/kyqualify.py:649-702`). Socket denial = job failure, not launcher failure; no upgrade.
- Full: base/build_argv; change only -s workspace-write to danger-full-access and remove the two -c sandbox_workspace_write.network_access / sandbox_workspace_write.exclude_slash_tmp pairs (`E/kyqualify.py:833-838`; `C/kyengine.py:153-170`). Other bytes unchanged; invalid -s refuses; schema unchanged (`E/kyqualify.py:182,680-685`); job field admits full. Same footing as unsandboxed Claude: no new OS profile, prompt forbids commit/push/gh; landing guards below.
- Both verifier engines retain boundary prepare/exec/check/release (`F/kyboundary.sh:6-12,508-518`; `F/kyd_kinds_build.py:774-825`); full never bypasses it.
- Codex builder result unchanged: ky.job_result/1 + commit_message (nonempty done, nullable blocked/failed); branch/head_sha/pr_number forbidden even null (`E/schemas/job_result_launcher_commit.json:7-16,61-68,101-118`). Correct KARAKA:28; VERIFY: `F/schemas/job_result.json:8-18,34-37`, null head/pr + proposed_verdict. Keep nofollow/regular-file/identity (`F/kyd_jobs.py:787-808`); no fallback/field stripping.
- Collect first_thread_id/final_codex_turn → provider_session_id/result_event; codex_guards/git_guard_changes (`E/kyboot.py:1614-1632,473-479,411-428`). (I) INTERPRETATION: require exit 0 + turn.completed + valid done + group gone; unknown/changed guards refuse (N1: `R/jobs/review-engines-r4/result.json:53-58`). Partial done refuses.
- Finisher after collection, before finish/release, item/claim fence (`F/kyd_jobs.py:904-917,1085-1115`). Check .git pointer BEFORE Git, git directory/guards, launch branch/HEAD, packet hash, clean initial index; changed/untracked/rename endpoints within d1_paths (`C/kyfinish.py:8-28,296-330`). Self-commit/push, branch/HEAD/pointer drift, outside path → refuse landing; retain work. (I) INTERPRETATION: launch/pre-push remote-head comparison detects self-push without HEAD movement (`C/kyfinish.py:204-206`); unknown holds. No queued push; message/body files, argv commands; item branch/observed remote/one PR; no force/merge/queue.
- Durable ctx.act commit/push/PR/registration intent/observers (`F/kyd_jobs.py:5-11`; `F/kyaction.py:20-25,39-45`); resume first unobserved step, including commit-before-record crash. (I) INTERPRETATION: observer matches tree/parent/branch/message + packet/diff; reuse proven commit, unknown holds; never second commit of same tree. Raw result intact; controller head/pr/registered_head/checkpoint (`F/kyd_jobs.py:115-116`). Recheck claim/queue/head each effect. ky review detail "PR #<n> @ <40-hex head>", owning lane after claim; observe event; unchanged finish returns done (`F/kyd_kinds_build.py:288-297,750-771`). Blocked → ky block; finisher failure → failed.
- Origin/main conflict blocks with clear reason → controller rework; launcher never merges. Correct KARAKA:17 Codex clause; Claude unchanged.
- Stall: controller positive seconds/default 300; stdout OR stderr growth counts, polling/touches do not. (I) INTERPRETATION: checkpoint launch/last-growth times/counts across restart; threshold silence → terminating/failed/failure_fp codex_stalled, stop renewal, identity-safe TERM/KILL (`F/kyd_jobs.py:936-949,977-1015`). Record activity/duration/reason/logs/deadline; group gone before end/claim/lock release, ordinary failure order (`:34-45,1085-1115`); unknown/survivors hold/report. Leave working tree as-is.

**Depends on.** Accepted KYJOB 16565d549c390753d7e454aac56ccad2c8fe94b0; KYDJOBS 4806af74770c3b9b0c548f062f96f4b5d44f3424; KYBOUNDARY 9a43d357ef57d9d027fbd0dbe0e536ca6ae8ef96; KYDKINDS-BUILD c68548d7069a4affe548bf7503e30286a5ade696 (`P:683,686,691,694`). E e4693d8ee1ea46697e18bcaf28cb948039c2f811 (`R/jobs/review-engines-r4/result.json:47-50`): helpers/schemas in base; absent functions block. Cockpit stamps/confirms base; review/install, separate dispatcher.

**Acceptance.** acceptance.command + KYJOB/KYDJOBS/KYDKINDS-BUILD/cards regressions. (I) INTERPRETATION: fake tools/scratch targets; reload/Claude bytes/full argv/records/verifier/landing/release/restart positives and named negatives; crash between effect and recording; stall with TERM-ignoring child. Full process/loopback: DB stand-in socket.

**Evidence.** $JOB_SCRATCH/result.json, tests/interpretations/questions. **PR.** (I) INTERPRETATION: kalayantra/kv3-b-kyjob-engines; one item PR/review/install. **Do not.** Outside d1_paths; real model/gh/launchctl/tracker/DB; foreign signals; credentials/force-push/merge/installed/production/owner-policy writes.
