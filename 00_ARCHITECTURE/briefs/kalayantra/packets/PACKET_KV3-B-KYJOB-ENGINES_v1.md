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
"expected_result":"exit 0; fixtures/regressions pass; unknown enforcement fails",
"negative_cases":[
"test_unknown_engine_or_mixed_config",
"test_receipt_engine_or_bind_changed",
"test_full_without_mode_evidence",
"test_git_write_or_pointer_redirect",
"test_result_schema_or_identity",
"test_exit_turn_or_group_not_clean",
"test_scope_or_queue_authorisation",
"test_stall_term_ignoring_child",
"test_restart_each_finish_step",
"test_claim_actor_head_pr_mismatch"]},
"packet_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}
```
# KV3-B-KYJOB-ENGINES v1: engine-aware campaign jobs

**Pins.** Plan v2.7 @ e709f60d7; base: job header. F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; E = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/` + F; S = `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3`; C = S + `/engines/launchers/cockpit`; R = S + `/reviews/b0c-engines`. Citations expand these real roots.

**Owns.** d1_paths only: accepted KYJOB/KYDJOBS/tests/KARAKA; new adapter/test. Other required edits → blocked. Boundary/build-kind/schemas/E unchanged; dispatcher absent.

**Spec** (pinned §7:504).
```excerpt plan §7
- Session persistence stays on (reconciliation evidence, §13).
```
Engine authority: `R/RULINGS_E.md:3,8,18-20`; `F/cards/KARAKA.md:17,28`. Cockpit records later direction before activation.

**Job state.** `F/kyd_jobs.py:115-132,439-484,625-637`. (I) INTERPRETATION: facts.launch/intent.header selects persisted engine, absolute launch_config_path/full_mode_evidence_path, sandbox_mode locked/full, positive stall_seconds; hash inputs. No ambient/fallback switching. Legacy absent engine = Claude; null/unknown refuses. Codex BUILD/REWORK/VERIFY, unchanged pools/locks/claims; VERIFY claimless. (I) INTERPRETATION: guards/activity/finish progress in checkpoint (`:1066-1080`).

**Contract.**
- Claude: byte-identical argv/env/prompt/stdin/cwd/PID/PGID/receipts/refusals/parsing for equivalent inputs (`F/kyjob.sh:114-146,380-389,618-652,730-756`; `F/kyd_jobs.py:778-825,904-916`). (I) INTERPRETATION: compare baseline/new observation bytes; old schema unchanged.
- Codex: call engine_of/validate_codex_config/build_argv(cfg, job_scratch), never retype argv (`E/kyqualify.py:616-618,663-775,820-864`). Config `E/schemas/launch_config_codex.json:8-23`; patterns `E/templates/LAUNCH_CONFIG.bootstrap-builder.codex.json:2-31`, `LAUNCH_CONFIG.bootstrap-reviewer.codex.json:2-32`. gpt-6.1-sol/high, never-approval/disabled features/sign-in/deadline, no turn cap (`R/RULINGS_E.md:7-8`). Reject credentials/mixed fields (`E/kyqualify.py:442-448,663-668`); preserve prompt/no-wrappers/exec (`F/kyjob.sh:6-16,588-615,730-756`).
- Locked: workspace-write/network off; builder source/scratch, no writable Git dirs; verifier scratch-rooted/absolute reads (`E/kyqualify.py:649-702`). Engine-matching launchd PASS binds binary/version/hash/config/permissions/env/argv: check_receipt/portable_codex_argv (`E/kyqualify.py:3340-3380`; `E/kyboot.py:1258`); unknown/missing refuses.
- Full: supplied fact: locked cannot ps/bind loopback/access slot DB; those needs require full. Controller selects explicitly. Transform build_argv as `C/kyengine.py:153-170`: -s danger-full-access, omit sandbox_workspace_write settings. (I) INTERPRETATION: reviewed/hash-bound exact-mode authorization/qualification binds final argv/config/binary/env/role/deadline and process/DB/boundary proofs. Full is refused by locked validation (`E/kyqualify.py:182,680-685`; `E/schemas/launch_config_codex.json:63-68`): validate base then mode evidence; no locked PASS/no-receipt inheritance (`C/kyengine.py:140-145`). Until cockpit binds evidence format/producer, refuse full.
- (I) INTERPRETATION: full builder needs inherited OS confinement: source/scratch writes allowed; .git pointer/Git/control/other jobs denied; process/loopback allowed. Hash guards alone fail E7. Pattern: `F/kyboundary.sh:18-40,287-294`. VERIFY retains prepare/exec/check/release (`:6-12,508-518`; `F/kyd_kinds_build.py:774-825`); sign-in/store proof required, unknown blocks.
- Builder: unchanged `E/schemas/job_result_launcher_commit.json:7-16,61-68,101-118`: ky.job_result/1 + commit_message, nonempty done/nullable blocked-failed; branch/head_sha/pr_number forbidden even null. (I) INTERPRETATION: correct KARAKA:28. VERIFY: `F/schemas/job_result.json:8-18,34-37`, null head/pr + proposed_verdict. Keep nofollow/regular-file/identity (`F/kyd_jobs.py:787-808`), no final_message fallback.
- Collect observed first_thread_id/final_codex_turn, provider_session_id/result_event; compare codex_guards/git_guard_changes (`E/kyboot.py:1614-1632,473-479,411-428`); unknown/changed fails. (I) INTERPRETATION: exit 0 + turn.completed + valid done + proven group gone before finisher (N1: `R/jobs/review-engines-r4/result.json:53-58`).
- Controller finishes after collection/before build-kind finish/release under item/claim fence (`F/kyd_jobs.py:904-917,1085-1115`). `C/kyfinish.py:8-28,192-201,296-330`: pointer before Git, guards, launch branch/HEAD, packet hash, clean initial index, changed/untracked/rename endpoints within scope. No queued push; message/PR body files, argv commands; item branch only, observe remote head/one PR, no merge/queue.
- (I) INTERPRETATION: ctx.act journals/reconciles commit/push/PR/registration (`F/kyd_jobs.py:5-11`; `F/kyaction.py:20-25,39-45`); resume each step, even commit-before-record; unknown holds. Preserve raw result; state head/pr/registered_head + checkpoint (`F/kyd_jobs.py:115-116`). Controller ky review detail "PR #<n> @ <40-hex head>", owning stream/lane after matching claim; observe event. Unchanged registration/finish (`F/kyd_kinds_build.py:288-297,750-771`) must return done. Blocked → ky block; finisher failure → failed. Recheck claim/queue/head each effect. Codex origin/main conflicts launcher-owned (KARAKA:17); outside scope blocks.
- Stall (I) INTERPRETATION: Codex stall_seconds >0, recommend N=5 minutes. Persist stdout OR stderr byte-growth time from launch across restart/adoption; polling never activity. N silent/live → terminating/failed/failure_fp codex_stalled; stop renewal, identity-safe TERM/KILL (`F/kyd_jobs.py:936-949,977-1015`). Record activity/duration/reason/logs/checkpoint; retain deadline. Unknown holds/reports; group absence before close/release (`:33-43,1085-1115`); partial done cannot commit.

**Depends on.** Accepted KYJOB 16565d549c390753d7e454aac56ccad2c8fe94b0; KYDJOBS 4806af74770c3b9b0c548f062f96f4b5d44f3424; KYBOUNDARY 9a43d357ef57d9d027fbd0dbe0e536ca6ae8ef96; KYDKINDS-BUILD c68548d7069a4affe548bf7503e30286a5ade696 (`/Users/Dev/kalayantra/run/PLANNER_STATE.json:683,686,691,694`). E engines e4693d8ee1ea46697e18bcaf28cb948039c2f811 (`R/jobs/review-engines-r4/result.json:47-50`): unchanged helpers/schemas in base; absent functions block. Cockpit stamps hash/confirms base. Activation: reviewed install/role qualifications/full-mode contract/dispatcher wiring.

**Acceptance.** acceptance.command + original KYJOB/KYDJOBS/KYDKINDS-BUILD/cards regressions. (I) INTERPRETATION: fake tools/scratch targets; engine reload/schema/verifier/commit→remote/PR→registration→finish→release/restart/Claude-byte positives; named negatives above. Full proves argv/source/temp/Git-control denial/process/loopback (DB stand-in socket); unavailable proof fails. Live qualification before activation.

**Evidence.** $JOB_SCRATCH/result.json, tests/interpretations/questions. **Branch and PR.** (I) INTERPRETATION: kalayantra/kv3-b-kyjob-engines; one main PR "KĀLA-YANTRA v3 KV3-B-KYJOB-ENGINES", independent review/install. **Do not.** Outside d1_paths; real model/gh/launchctl/tracker/DB; foreign signals; credentials/force-push/merge/installed/production/owner-policy writes.

