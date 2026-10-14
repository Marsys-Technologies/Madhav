```json
{"id":"KV3-B-KYDKINDS-BUILD",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§6 BUILD to ARTIFACT, verdict publication","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_kinds_build.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_build.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/kinds_build.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_build.py -q -p no:cacheprovider",
"expected_result":"exit 0; kinds_build.json cases yield their intents and argv",
"negative_cases":[
"boundary check not intact: nothing published",
"a BUILD with neither review nor block: interrupted",
"a step detector null or false: no ky step"]},
"packet_sha256":"23a35aafdbeb3ae833a3afa850f465f8161cda5cb4e2ea14114cd2e30d589d6c"}
```
# KV3-B-KYDKINDS-BUILD v1: kyd_kinds_build.py

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The d1_paths only (new). Prohibited: FROZEN paths; installed trees; any other path → blocked.

**Spec** (verbatim).
```excerpt plan §6
| BUILD (code) | K item ready, unclaimed, no open PR, PRIORITY order | by routing (§9) | `KY_STREAM=K KY_LANE=<slot> ky claim <ID> --worker <slot> --lease 10800`; item lock | must end in `ky review <ID> --detail "PR #n @ <head>"` or `ky block`; else `interrupted` |
| BUILD (artifact) | K-owned artifact item ready | by routing | K claim; author identity recorded before review | registers path + digest via `ky review`; schedules ARTIFACT |
| REWORK | REJECTED at head, or **code-class** CI failure (classified; infra/flaky → RETRY-CI without a model) | routing; loop +1; escalation §9 | same worktree, item lock | as BUILD; evidence history retained |
| STEP | a required `step` whose named detector passes | script | — | `ky step <ID> <step> --evidence <path>` only after the detector passes |
| VERIFY | item in review; PR head without a verdict at (item, pre_merge, head, evidence-fp); required checks green; `Kāla DB Tests` green where the diff is relevant | Opus | **no item claim**; job lock (item, phase, head); item lock | verifier writes a **proposed** result; controller publishes (below) |
| ARTIFACT | artifact/packet item registered by its author, or a MODEL artifact | Opus | reviewer slot ≠ author identity; V claim only for V-owned items; S-owned artifacts get no V claim | `KY_STREAM=V … ky verdict <ID> --artifact-digest <sha256> --phase artifact …` (external review binding where the V-owned item requires it) |
```
```excerpt plan §6
**Verdict publication (controller-owned).** After a VERIFY/ARTIFACT job exits the
controller checks: exit status, reviewed HEAD unchanged, `git status --porcelain` clean,
tracked-file hash set unchanged, boundary evidence (§7). Only then does it publish
`KY_STREAM=V KY_LANE=<vslot> ky verdict …`. A boundary failure never publishes
ACCEPTED. If a published acceptance is later invalidated, an explicit REJECTED is
appended before any queue action.
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.

**Contract.** ctx (engine-built; test double): paths `root run fleet scratch repo` (the campaign checkout); `sh(argv, env=None, cwd=None, timeout=120)` → `(rc, out, err)` (rc None: unknown); `ky(*args, stream=None, lane=None)`; `act(id, kind, inputs, target, effect, observer)` → `(done | failed | unknown, result)`, kyaction's record; `next` (fresh `ky next --json`); `events(item)`; `pr(item)` → `{number, head, base, title, state, mergeable, merge_state, checks{name: {status, run_id, attempt}}, merge_commit, files[], auto_merge}`, None or `"unknown"`; `accepted(item)` → `{head, via}`, None or `"unknown"`; `verify(item, step)` → True, False or None; `priority[]`; `journal(event, text)`.
Intent: `{kind, item, key, stream, role, pool, runner, queue, claim, locks[], tier, not_slot, head, digest, verdict_phase, evidence_fp, card, packet, header{}}`; role = the kind in lower case; `pool` `builder | verifier | null`; `runner` `model | script`; `claim` `K | V | null`; `key` = `<kind>.<item>.<12 hex of sha256(head or digest, evidence_fp)>`, job lock `job.<key>`; launch keys in `header` go into the job state. Result: `{outcome, detail, failure_fp}`.
KINDS = ("BUILD", "REWORK", "STEP", "VERIFY", "ARTIFACT"). The engine calls `intents(ctx)` (read-only; order STEP, VERIFY, ARTIFACT, REWORK, BUILD (I)), `start(ctx, job)` → a result, or None (launch), and `finish(ctx, job)` → a result (its group is gone).
- BUILD: ready K items in `ctx.priority` order (absent from it: none), `ctx.pr` None; lock `item.<item>`, card `fleet/cards/KARAKA.md`, packet `repo/00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md` (highest n). `$KY_RUN/admission/<item>.json` saying `already_green`: no BUILD, but an ARTIFACT intent (`header.assessment` `already_satisfied`).
- REWORK, CI classes (I): a check FAILURE at `attempt` ≥ 2 is code-class; at `attempt` 1 a script intent (`header.action` `retry_ci`) runs `gh run rerun <run_id> --failed`; any other failed state → journal `unclassifiable CI failure`. `tier` by `python3 -B fleet/kyroute.py escalate --tier T --red-loops N --max-loops M --rejected K`: `OPUS_REWORK` → opus; `BLOCK` → a script intent running `ky block <ID>`.
- `finish` (BUILD, REWORK): the row's post-action, read from `ctx.events(item)` (the job's lane, after launch).
- STEP (script): an unrecorded step with `ctx.verify(item, step)` True (null detector: none; ruling P18); `start` writes it to `$KY_RUN/jobs/<job_id>/step.json`, the row's `--evidence`.
- VERIFY: `pr.head` = the registered head H; `ctx.accepted(item)` None; `evidence_fp` = sha256 of `{packet sha256, checks}`; `Kāla DB Tests` SUCCESS, and present when `files[]` touch `platform/migrations/` (I). First `python3 -B fleet/kyroute.py diff --repo R --base B --head H --built-tier T`: 1 → an opus REWORK intent; 3 → `ky block <ID> --detail "freeze: <path>"`. Lock `item.<item>`, card `fleet/cards/PARIKSAKA.md`; `start` writes `gh pr diff <n>` to `$JOB_SCRATCH/pr.diff`.
- ARTIFACT: the latest `review` event registers a path and sha256, no artifact verdict at that digest; `not_slot` = the author's slot.
- `start` (VERIFY, ARTIFACT): `python3 -B fleet/kyverdicts.py snapshot --worktree W --out $JOB_SCRATCH/snapshot.json`.
- `finish` (VERIFY, ARTIFACT): `bash fleet/kyboundary.sh check <job_id>`, then `python3 -B fleet/kyverdicts.py publish --job-id J --item I --phase P (--head H | --artifact-digest D --artifact-path A) --vslot V --author-id AU --reviewer-id RV --worktree W --snapshot $JOB_SCRATCH/snapshot.json --job-exit N --result <result_path> --boundary $JOB_SCRATCH/boundary.check.json --as <controller_id>`; AU = the actor of the latest `review` event, RV = `stream-V:<slot>`. 0 → `done`; else `failed`, nothing published.

**Depends on.** Wave 3. KV3-B-KYVERDICTS, KV3-B-KYBOUNDARY, KV3-B-KYROUTE, KV3-B-TRACKER; faked in tests.

**Acceptance.** acceptance.command, ctx a recording double; kinds_build.json: each case, its intents, argv: each kind and transition; the negative cases; a Sonnet diff on an Opus rule; each escalation; a retried, then code-class CI failure; already-green.

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-build; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-BUILD: kyd_kinds_build.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky or gh; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
