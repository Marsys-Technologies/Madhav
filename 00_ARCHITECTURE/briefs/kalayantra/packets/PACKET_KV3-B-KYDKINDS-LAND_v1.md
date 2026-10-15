```json
{"id":"KV3-B-KYDKINDS-LAND",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§6 REGEN, MERGE, COMPLETE, inheritance; §14 B-2","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_kinds_land.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_land.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/kinds_land.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_land.py -q -p no:cacheprovider",
"expected_result":"exit 0; each case of kinds_land.json yields its intents and argv",
"negative_cases":[
"HOLD_MERGES present: no gh call, one parked request",
"the PR head differs from the registered head: no submission",
"a substantive conflict resolution: not inherited, no MERGE"]},
"packet_sha256":"3486423dbfcbe0acce9545840ec7dfd97dbd6ac02fc403f906dab49ae874b20d"}
```
# KV3-B-KYDKINDS-LAND v1: `kyd_kinds_land.py`

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The `d1_paths` only (new). Prohibited: FROZEN paths; installed trees; any other path → `blocked`.

**Spec** (verbatim).
```excerpt plan §6
| REGEN | PR DIRTY/CONFLICTING confined to declared generated outputs | script, pinned generator | item lock | merge base; regenerate only declared outputs; run applicable tests; record hashes; push; **register `ky review … @ <new head>`**; inheritance only by the patch predicate (below), else VERIFY |
| MERGE | ACCEPTED at the **registered** head (head-match guard), required checks + DB job success, base correct, protected-window listing satisfied, no hold | script | — | `gh pr merge "$PR" --auto --squash --match-head-commit "$REGISTERED_HEAD"` after the checks; a head mismatch refuses submission; once queued, any head change cancels the queue/auto-merge authorisation and requires fresh admission; workers never push under an outstanding queue authorisation; branch/ref evidence retained until guarded completion |
| COMPLETE | merged (code) / accepted artifact / receipted operation | script | K completes K items; S completes S items and independently accepted N/V items | typed `ky done` (`--pr n --reviewed-head <final PR head>` \| `--artifact-path` \| `--operation-receipt … --operation-id …` \| `--packet-verdict`); deployment containment and post-deploy use the **squash merge commit**; refusals logged by code; `deps_open_strict` → wait |
```
```excerpt plan §6
**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head. Applied to every inherited Wave 0 head.
```
```excerpt plan §14 B-2
Under `HOLD_MERGES` merge intentions remain durable local requests with no GitHub queue submission; the surrogate executes them after certification-done
```
**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.

**Contract.** ctx (engine-built; test double): paths `root run fleet scratch repo` (the campaign checkout); `controller_id`; `sh(argv, env=None, cwd=None, timeout=120)` → `(rc, out, err)` (rc None: unknown); `ky(*args, stream=None, lane=None)`; `act(id, kind, inputs, target, effect, observer)` → `(done | failed | unknown, result)`, kyaction's record; `next` (fresh `ky next --json`); `model`; `events(item)`; `pr(item)` → `{number, head, base, title, state, mergeable, merge_state, checks{name: {status, run_id, attempt}}, merge_commit, files[], auto_merge}`, None or `"unknown"`; `awaiting(slug, question, options, evidence, item, class_hint)`; `journal(event, text)`.
Intent: `{kind, item, key, stream, role, pool, runner, queue, claim, locks[], tier, not_slot, head, digest, verdict_phase, evidence_fp, card, packet, header{}}`; `role` = the kind in lower case; `pool` `builder | verifier | null`; `runner` `model | script`; `claim` `K | V | null`; `key` = `<kind>.<item>.<12 hex of sha256(head or digest, evidence_fp)>`, job lock `job.<key>`; launch keys in `header` go into the job state. Result: `{outcome, detail, failure_fp}`.
`KINDS` = `("REGEN", "MERGE", "COMPLETE")`, all `runner` `script`. The engine calls `intents(ctx)` (read-only), `start(ctx, job)` → result and `park(ctx, intent)`, and serves `accepted_head(ctx, item)` as `ctx.accepted`. Added to the rows:
- `accepted_head`: H = the head in the item's latest `review` event. `{head: H, via: "direct"}` if the latest pre_merge verdict at H is ACCEPTED; `{head: H, via: H0}` if the latest ACCEPTED is at an older H0, no REJECTED follows and `python3 -B fleet/kyverdicts.py inherit --repo <worktree> --old-head H0 --new-head H` exits 0; exit 1 → None; else `"unknown"`.
- REGEN: `pr.mergeable` CONFLICTING or `merge_state` DIRTY, every conflicted path of `git merge-tree --write-tree --name-only origin/main <head>` in `regen.outputs` (`regen` = the model item's `brief.regen` (I)); else journal `dirty_outside_generated`. Lock `item.<item>`; `header` = `{pr, registered_head, base_sha, queue_authorised, regen}`. `start`: `bash fleet/kyregen.sh <job_id>` with `KY_RUN_ID=<job_id> KY_ROLE=dispatcher KY_CONTROLLER_ID=<controller_id>`; 0 → `done`; 3, 4 → `blocked`; 5, 6 → `failed`; else `refused`.
- MERGE (`queue` true: a GitHub queue submission): `accepted_head` gives `pr.head` (head-match guard); all checks SUCCESS, `Kāla DB Tests` among them; `pr.base` `main`; no hold; under a `[PROTECTED-WINDOW]` title each added migration is named in `platform/scripts/kala_protected_migrations.txt` at the head (I). `start` reads `ctx.pr` again, then `act("ACT-merge-<job_id>", "merge", …)` around the row's `gh pr merge`. A queued PR whose head changed → intent `header.action` `cancel`: `gh pr merge <n> --disable-auto`, then, unless the new head inherits, `python3 -B fleet/kyverdicts.py invalidate --item I --phase pre_merge --head <old head> --vslot V --reason TEXT --as <controller_id>`; journal `verdict invalidation`.
- `park`, for a `queue` intent under `HOLD_MERGES` (owner decision D-6 revised) in place of admission: `$KY_RUN/merge_requests/<item>.json` `{schema: "ky.merge_request/1", item, pr, registered_head, recorded_at}`; no GitHub call. After the hold a parked request waits for the surrogate (I; D-5): `ctx.awaiting("merge-<item>", …)`, then an EFFECTIVE or EXECUTED decision for that id in `$KY_RUN/DECISIONS_SURROGATE.jsonl`, the parked head still `pr.head`.
- COMPLETE: the row's typed `ky done` by `completion_kind` (code: `pr.state` MERGED; artifact: ACCEPTED at its digest; operation: COMPLETED receipt ACCEPTED at its sha256); exit 2 → `blocked`, `failure_fp` = the refusal code; `deps_open_strict` → wait. Then, code items: `git worktree remove` if clean and pushed.

**Depends on.** Wave 3. KV3-B-KYVERDICTS, KV3-B-KYREGEN, KV3-B-TRACKER, as called above; tests fake them.

**Acceptance.** `acceptance.command`; `ctx` is a recording double; `kinds_land.json` holds each case with its intents and argv: each kind and transition; the negative cases; a head change after queueing (cancel, then REJECTED); a parked request across a restart; each typed completion and refusal.

**Evidence.** `$JOB_SCRATCH/result.json`. **Branch and PR.** `kalayantra/kv3-b-kydkinds-land`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-LAND: kyd_kinds_land.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
