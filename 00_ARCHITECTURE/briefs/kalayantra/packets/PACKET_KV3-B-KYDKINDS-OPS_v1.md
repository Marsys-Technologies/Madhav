```json
{"id":"KV3-B-KYDKINDS-OPS",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§6 REQUEST-PREP to PLAN","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_kinds_ops.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_ops.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/kinds_ops.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kyd_kinds_ops.py -q -p no:cacheprovider",
"expected_result":"exit 0; kinds_ops.json cases yield their intents and argv",
"negative_cases":[
"an awaiting item handled at its fingerprint: no second job",
"PENDING_VETO or hard stop, evidence unchanged: no further job",
"a wrong receipt digest or a pre-acceptance record: nothing published"]},
"packet_sha256":"28f5a7b966d8eeb83f274a313881620da3e3298df397e1fbf14cd0c9e0961d09"}
```
# KV3-B-KYDKINDS-OPS v1: kyd_kinds_ops.py

**Pins.** Plan v2.7 @ e709f60d7; base: the job header's. (I) = INTERPRETATION.

**Owns.** The d1_paths only (new). Prohibited: FROZEN paths; installed trees; any other path → blocked.

**Spec** (verbatim).
```excerpt plan §6
| REQUEST-PREP | ready N-owned operation | script + PLAN where the request needs authoring | N actor | request binds the reviewed merged script, request digest, lease, expiry, backup/restore/dry-run evidence per `executor.py` and the approved operation table |
| PRE-ACCEPT | prepared request | Opus (independent V slot) | job lock | acceptance record the executor requires |
| EXECUTE | pre-accepted request | script (`executor.py`, authority boundary unchanged) | — | receipt in `run/ops/receipts/`; GitHub protected-window dispatch stays an owner-approved workflow action |
| POST-READBACK | (a) deployed `writes_data` code item; (b) receipted operation item | Opus after a readback request | (a) job lock (item, post_deploy, squash merge sha, evidence-fp); (b) job lock (item, operation id, receipt sha256, evidence-fp) | two typed exits: (a) propose `--phase post_deploy` at the squash merge commit; (b) review the completed executor receipt, operation/request identity, measured readback and quiescence evidence and propose `--phase artifact --artifact-digest <receipt sha256>`; the controller publishes only after independence, boundary and unchanged-evidence checks; operation COMPLETE then uses `--operation-receipt <that receipt> --operation-id <that id>` under the existing typed guard; negative fixtures: script-head verdict, pre-acceptance record, wrong receipt digest, executor exit without semantic readback — none completes the operation |
| MODEL | S-owned model/close work (triage, joins, PRIORITY, C-1/C-2 artifacts, REPIN) | Opus PLAN job | S actor | artifact + ARTIFACT review where required |
| RULING | `ky request D-…` pending (doctrine/charter) or N inbox unread | Opus | N actor | `ky decide … --as steward --delegated …`; `ky ack` |
```
```excerpt plan §6
SURROGATE | an unresolved `run/awaiting/<id>.json` with **no handled proposal for its current immutable target/evidence fingerprint**; handled state re-read under the lock before launch; `PENDING_VETO`, hard-stop and external-approval items launch no further SURROGATE job unless recorded material evidence changes | Opus (owner-surrogate charter) | steward actor; lock on the awaiting id
```
```excerpt plan §6
| PLAN | wave boundary or `run/REPACKET.txt` | Opus **xhigh** | S actor | packets + tests; ARTIFACT review of the packet set |
```

**Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
Launch keys: `job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp pr registered_head queue_authorised prerequisites[] test_digests[] migration_number loop max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags[] disallowed_tools[] job_scratch prompt_path stdout_path stderr_path tmp_path tests[] se_ephe_path swe_ephe_path card_path packet_path boundary regen fixture locks[] controller_id`.
Lifecycle keys: `phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path result_event checkpoint failure_fp attempt requeued ended_at`.
`phase`: `prepared` → `live` → `terminating` → `ended`. `outcome`: `done | blocked | failed | interrupted | timed_out | refused`.

**Contract.** ctx (engine-built; test double): paths `root run fleet scratch repo` (the campaign checkout); `sh(argv, env=None, cwd=None, timeout=120)` → `(rc, out, err)` (rc None: unknown); `ky(*args, stream=None, lane=None)`; `act(id, kind, inputs, target, effect, observer)` → `(done | failed | unknown, result)`, kyaction's record; `next` (fresh `ky next --json`); `events(item)`; `pr(item)` → the PR (`head`, `state`, `merge_commit`, …), None or `"unknown"`; `awaiting(slug, question, options, evidence, item, class_hint)`; `journal(event, text)`.
Intent: `{kind, item, key, stream, role, pool, runner, queue, claim, locks[], tier, not_slot, head, digest, verdict_phase, evidence_fp, card, packet, header{}}`; `role` = the kind in lower case; `pool` `builder | verifier | null`; `runner` `model | script`; `claim` `K | V | null`; `key` = `<kind>.<item>.<12 hex of sha256(head or digest, evidence_fp)>`, job lock `job.<key>`; launch keys in `header` go into the job state. Result: `{outcome, detail, failure_fp}`.
KINDS: the eight. The engine calls `intents(ctx)` (read-only), `start(ctx, job)` → a result, or None (launch), and `finish(ctx, job)` → a result.
- REQUEST-PREP: a ready N-owned operation item with no $KY_RUN/ops/prepared/<operation_id>.json (I). script: the request executor.py validate accepts, from brief.op and the table at origin/main; an underivable field → a model job.
- PRE-ACCEPT: a prepared request without acceptance. The job proposes $JOB_SCRATCH/acceptance.json; finish, after `bash fleet/kyboundary.sh check <job_id>` exits 0, the request digest unchanged, writes `$KY_RUN/ops/acceptance/<operation_id>.json` (`by` = the slot) through act (I).
- EXECUTE (script): an acceptance matching the prepared request's digest → act writes `$KY_RUN/ops/requests/<operation_id>.json` (the request plus acceptance_receipt); never starts executor.py, holds no credential, dispatches no workflow (I). A receipt not COMPLETED → ctx.awaiting, no resubmission.
- POST-READBACK: (a) needs pr.merge_commit and a COMPLETED readback receipt for the item (I: nothing is named to request it; none → journal). finish: kyboundary.sh check, then kyverdicts.py publish as KV3-B-KYDKINDS-BUILD calls it, with the row's phase (`--head <merge commit>`, or the receipt as `--artifact-path`).
- MODEL (PLAN limits): ready S-owned executable items except C-3, C-4; lock `item.<item>`. finish: a review or `blocked` event, else interrupted.
- RULING: one job per message of `ky inbox --stream N --json` (a list with msg_id); lock `msg.<msg_id>`; done once acked, then `$KY_RUN/handled/msg.<msg_id>.json`.
- SURROGATE: per `$KY_RUN/awaiting/<id>.json` (not `*.owner_decision.json`). Fingerprint (I): sha256 of canonical `{id, item, question, options, evidence, each evidence file's sha256}`. No intent while `$KY_RUN/handled/awaiting.<id>.json` carries it; lock `awaiting.<id>`; start reads that record again under the lock; finish writes it from the job's line in $KY_RUN/DECISIONS_SURROGATE.jsonl; a hard stop → journal `hard stop`. No `ky decide` here. Once kyveto.status() shows the decision EXECUTED, VETOED or FAILED, a script intent moves the item to awaiting/done/.
- PLAN: a non-empty $KY_RUN/REPACKET.txt, or, as the wave boundary (I), open items, none ready or `running` with an admitted packet.

**Depends on.** Wave 3. KV3-B-KYVERDICTS, KV3-B-KYBOUNDARY, KV3-B-EXECUTOR-TABLE (ops shapes), kyveto.py; faked in tests.

**Acceptance.** acceptance.command, ctx a recording double; kinds_ops.json: each case, its intents, argv: each kind and transition; negative cases; one SURROGATE job across ticks and restarts; POST-READBACK's four negative fixtures.

**Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-ops; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-OPS: kyd_kinds_ops.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh or executor; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
