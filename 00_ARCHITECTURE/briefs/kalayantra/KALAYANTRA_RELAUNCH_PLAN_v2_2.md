---
artifact: KALAYANTRA_RELAUNCH_PLAN_v2_2.md
status: DRAFT — for Astra's confirmation review, then native approval. Supersedes v2.1 (ASTRA_REVIEW v2.1: REWORK, KT-01…KT-08, all applied here with Astra's replacement text; v2.0 KS-01…KS-12 applied in v2.1). On approval this plan and its paired prompts and cards are the only operating rules of KĀLA-YANTRA v3; CHARTER v1.2 keeps §0 (goal) and its five hash-pinned specification documents; the VELOCITY AMENDMENT is retired; the strategy is historical rationale only.
version: 2.2
authored_by: Claude Code (Fable 5.1), worktree kalayantra/relaunch-plan
authored_on: 2026-10-11
audience: Astra (reviewer); native (approver); the planning session (KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md); the conductor session (KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_2.md)
paired_prompts:
  - KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md
  - KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_2.md
pairing_rule: >
  Plan, prompts, cards, schemas and manifests carry one version. Two non-circular
  trust anchors (KT-01): (1) the PLANNING paste supplies <APPROVED_SOURCE_COMMIT>, the
  full commit id the native approved; before writing any state the session verifies that
  the checked-out plan, both paired prompts and the strategy are byte-identical to their
  tracked blobs at that commit (`git cat-file -e <commit>:<path>` and `git diff --quiet
  <commit> -- <paths>`); any missing object, missing file or difference is STOP; it then
  loads the verified prompt and plan (a version label alone is insufficient) and records
  the commit in `run/VERSIONS.bootstrap.json`, which is a B-0c deliverable, never a paste
  prerequisite. (2) The CONDUCTOR paste supplies <APPROVED_MANIFEST_DIGEST>, the SHA-256
  of the approved final `run/VERSIONS.json` (not a prompt-file digest); the session
  verifies that manifest digest, verifies the prompt against its manifest entry, loads
  the verified prompt, and runs `kyversion.sh --expected-manifest-digest
  <APPROVED_MANIFEST_DIGEST>` before acquiring the conductor lock;
  `OWNER_RESUME.approved_bundle_digest` must equal the supplied digest. `kyversion.sh
  --bootstrap` (KT-03) validates `VERSIONS.bootstrap.json` plus a `mode: bootstrap`
  installation receipt and can never authorise campaign admission or READY_TO_PASTE;
  normal `kyversion.sh` accepts only the final manifest and the final installation
  receipt.
authority_precedence: root CLAUDE.md (§I, §N; read first, as always) > owner decisions (§15) > this plan > cards > packets > anything a job infers
evidence: 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md (audit worktree, 758e0dbb4); reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v1_0.md and _v2_0.md; scratch notes_ky_state.md, notes_suvarna_state.md, notes_workflow.md, KY_MECHANICS_CATALOGUE.md (2026-10-11)
---

# KĀLA-YANTRA v3 — relaunch plan v2.2 (Claude, event-driven, essential governance only)

## 0. Goal, definition of done, scope (KS-01)

**Goal (CHARTER §0, unchanged):** build the Kāla layer as one engine per PLAN v1.1 §9 /
ALGO v1.1 (21 cards), absorb Gochara 5.0 to its "5.0" flip, rebuild and serve the layer
for chart `482012f1`, ship certification mappings, close with a validated SESSION_CLOSE
and a finalizer receipt. Suvarṇa certifies the Kāla assets afterwards.

**Retained acceptance set (owner decision §15.4):** (i) Kāla serves `482012f1`
end-to-end — every published Kāla read model answers for that chart from a rebuilt
layer; (ii) the Gochara 5.0 flip is sealed; (iii) certification mappings exist for every
served Kāla asset; (iv) a guarded close.

**Closure procedure (B-0, reproducible):**
1. First commit `00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v2_1.json`: an
   acceptance-to-item mapping for (i)–(iii), each root citing the producing item's brief
   and detector. The old `JOIN-ALL`/C-chain is **not** a scope root; the mechanical close
   chain is regenerated afterwards from the retained set.
2. Compute prerequisites from those roots: `depends_on` supplies item edges; `steps`
   are intra-item obligations, not item IDs; joins use `done_by: join` consistently with
   `join`; `requires_outcome` supplies decision conditions, with explicit dependencies
   on unresolved decisions. Preserve `accepts_not_applicable_dependencies` and propagate
   skipped-input gaps: a skipped prerequisite can never silently satisfy a retained
   acceptance. Output `CLOSURE_v2_1.json` (deterministic; two runs give one hash).
3. Everything in the closure is **(a) critical path**. Outside it: **(b) deferred**
   (`ky park --as steward --detail "…; re-entry: …"`, never counted as closed) or
   **(c) dispositioned** (inherited Pravāha material, per an independently accepted
   `J0_DISPOSITION` artifact). A missing required column is never evidence that its
   consumer is deferrable: it becomes an Opus schema-prerequisite item (new namespaced
   id `KV3-SCHEMA-<n>`, additive migration, protected window if needed) or an explicit
   blocked contract decision.
4. Retirement by decision: register `D-RETIRE-B-K-INBOX` and `D-RETIRE-B-CLAIM-RECOVERY`
   in the model; map each unfinished item's `requires_outcome` to `approved`, and stage
   the owner-authorised `refused` decision to be published by the installation/model
   migration action (B-2), never by a test. Newly registered relaunch bootstrap work uses
   new namespaced ids (`KV3-B-*`).
5. Two reconciliation tests (checked in): **path-only migration** — identical item
   states from one hashed EVENTS prefix, one captured detector-result map and one fixed
   clock; **triage** — compared against a reviewed expected delta covering
   dependencies, dispositions, readiness and close membership, preserving earned
   guarded completions and their evidence.

**Deferral candidates examined first:** J-7 (optional Tier-2 Sudarśana, outside sealed
5.0), J-7b (documentation-only), D-T2 and L0-K (only if the closure shows their corpus
work is not needed for (i)–(iii)). No reduced count is claimed before the closure exists.
Partial failure closes `CLOSED-PARTIAL` with the (b) list attached.

## 1. Principles

1. Single-pointed: accurate, high-velocity implementation of the critical path;
   governance and security kept where they protect correctness, production or honesty.
2. Jobs, not lanes: a model runs only for a named job with a packet, then exits.
3. Deterministic first: scheduling, claims, locks, gates, routing, allocation, test
   installation, regeneration, metering are scripts with tests and negative fixtures.
4. Packets carry the truth the builder needs; immutable pins are separated from the
   checkout base and the migration allocator.
5. Every signal is earned (CLAUDE.md §N.8): detector + negative fixture, or WAIT/unknown.
6. Token economy by construction: no idle model turns, small fixed context per job,
   diff-first review with independent tests, bounded conductor, one accounting owner per
   session.

## 2. Starting point — what exists and is reused

| asset | state | reuse |
|---|---|---|
| Tracker `ky` (pravaha_tracker on 8767; EVENTS.jsonl) | lock-safe claims, guarded typed `ky done`, verdict identity, `ky next --json`, `ky inbox --wait`, steward override | the single ledger; wrappers re-pointed and made override-preserving (§5) |
| Live plan model (148 items; uncommitted mirror edits) | 39 guarded completions + 1 join + 6 decisions = 46 of 148 (31.1 % plain; 37.6 % weighted) | committed and reconciled in B-0 |
| 20 merged engine items, `kala_core`, CI canary, `Kāla DB Tests` job | on main | built upon; the DB job is retained as an admission check (§3) |
| 11 ACCEPTED-unmerged PRs | frozen by HOLD_MERGES | Wave 0 under the patch-proof inheritance rule (§6) |
| Five hash-pinned specification documents | hashes match | packet sources |
| Item briefs | 148 live | packet inputs after contract reconciliation (§8) |
| `fleet_live/*` helpers, `executor.py` + `executor_ops.json`, protected-window mechanism | work for the old topology | kept; re-pointed, extended and re-tested in B-1; executor authority boundary unchanged |
| Learned rules (KARAKA/PARIKSAKA) | written by the campaign | folded into cards |
| Token audit + baseline script (scratch source recorded in the audit) | audit worktree | imported into a merged repository path in B-1 before any v3 total is reported (§13) |
| Astra reviews v1.0, v2.0 | reviews/ | closure maps in §17 |

## 3. Essential governance and security — kept vs cut (KS-10)

**Kept:**
- Root CLAUDE.md §I and §N, carried into cards by COVERAGE (every applicable MUST of
  §I and §N, charter §0 and the retained acceptance contracts maps to a card line, a
  packet clause or an executable check; the ≤ 300-token summary in a card cannot
  substitute for an omitted binding rule).
- The FROZEN contract: one explicit manifest `fleet/FROZEN_PATHS.txt` shared by
  `precheck.sh` and `kyroute.py`, seeded from ORCHESTRATOR_CONVERGENCE_CLOSE §2 and
  precheck's existing prohibitions (`asset_runner.py`, `runner.py`, `staleness.py`,
  `writers/__init__.py`, …). New conforming writers remain permitted; a frozen change is
  STOP for native authorisation.
- The tracker as the only ledger; typed guarded completion; verdict identity with
  evidence-aware re-review and full history.
- Verification: independent verifier running the packet's applicable item tests, named
  mutations and compatibility checks itself (builder results are inputs, not
  substitutes); the required CI checks; **`Kāla DB Tests (throwaway Postgres)` for
  relevant code changes** — absent, skipped or failed DB evidence is not success; the
  semantic acceptance obligations of retained items (Gochara endpoint completeness,
  actual teardown where required).
- Production safety: protected-window flow (owner-approved GitHub action); request-bound
  pre-acceptance, backup/restore/dry-run and quiescence evidence for executor operations;
  migration allocation; no worker holds `DATABASE_URL`; no model merges or dispatches
  production.
- Frontier-by-rule routing with fixtures; escalation grants no authority.
- One governance record pair: the C-2 banner + SESSION_LOG entry, and the C-4 close.

**Cut (measured waste or ceremony without a detector):** standing lanes, heartbeats,
idle cycles, claim-renewal model turns; the ADHIKĀRIN standing lane and surrogate
charter (→ authority card + RULING jobs on `ky request`); NEW ITEM reports and the
reservation ceremony (replaced by the allocator for migration numbers and the item
lock for shared worktrees — not merely by a typed block); per-cycle digests; ledger
PRs and branches; SESSION_OPEN ceremony beyond B-5; charter §3/§5/§11 and the
amendment as operating text; whole-document reads per job; LLM "packet exits" where a
deterministic check suffices; the periodic claim-only LIVENESS job (its claimed
DB/worktree proof was unsupported — admission checks replace it, §6).

## 4. Roster and capacity (owner decisions)

| role | model / effort | mode |
|---|---|---|
| Planner | Opus 5.5 **xhigh** | interactive (PLANNING prompt); headless PLAN jobs at `--effort xhigh` |
| SŪTRADHĀRA | Opus 5.5 high | interactive (CONDUCTOR prompt), event-woken, bounded |
| PRAHARĪ (dispatcher) | script | background, 60 s tick, atomic instance lock |
| KĀRAKA | Sonnet 5.5 high | BUILD / REWORK |
| KĀRAKA-escalated | Opus 5.5 high | BUILD / REWORK (routing or escalation) |
| PARĪKṢAKA | Opus 5.5 high | VERIFY / PRE-ACCEPT / POST-READBACK / ARTIFACT, source-read-only |
| ADHIKĀRIN | Opus 5.5 high | RULING on demand |
| Bootstrap builder (Wave B) | Opus 5.5 high | control-plane packets under D-1 |

Capacity `KY_BUILDERS_MIN=3 / MAX=6`, `KY_VERIFIERS_MIN=2 / MAX=4`; `min(max, demand)`
per kind. No token caps (§15.6). Backoff 30 min only on a subscription refusal
(structured error in the stream **or** terminal log text), reported to the conductor.

## 5. Topology, paths, allocation (KS-02, KS-06)

- `KY_ROOT=/Users/Dev/kalayantra`, `KY_RUN=$KY_ROOT/run`, `KY_FLEET=$KY_ROOT/fleet_live`,
  `KY_SCRATCH=/Users/Dev/scratch.noindex/claude/madhav/<YYYYMMDD>-kalayantra-v3/`
  (dated per owner policy; temporary files, job logs, DB dumps, fixture trackers). Every
  path in scripts, prompts, cards and packets is absolute; persistent job records store
  the absolute paths they used.
- **Job and dispatcher I/O (KT-08):** each job records `JOB_SCRATCH=$KY_SCRATCH/jobs/$JOB_ID`
  and absolute `prompt_path`, `stdout_path`, `stderr_path`, `tmp_path` beneath it, created
  before launch and used for stdin, logs and `TMPDIR`. The dispatcher log lives under
  `$KY_SCRATCH/dispatcher/`, its absolute path recorded in persistent dispatcher state.
  `run/` keeps only durable control state, compact measured receipts and evidence
  references. Before removing finished session scratch, usage is reconciled and evidence
  required by retained receipts is preserved; at session close finished scratch is
  removed and unfinished material is reported with its reason.
- `CLAUDE_BIN=/Users/Dev/.local/bin/claude` (resolved on this host before any scrub,
  asserted executable, recorded in `run/INSTALL_RECEIPT.json`).
- **Campaign checkout:** branch `kalayantra/campaign` (upstream `origin/main`) at
  `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, created in B-2;
  fast-forwarded each tick.
- **Capacity reality:** 33 worktrees are registered under the Claude/Madhav policy root
  against a ceiling of 15. **No new copy is created until the owner has disposed of
  enough existing ones** (B-0 inventory → owner dispositions → `git worktree remove` +
  `prune`, preserving dirty/unpushed work by push or bundle). The planner works in the
  existing relaunch-plan checkout (branch switches, no new copy) until then.
- **Work worktrees:** `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item-id-lower>/`,
  one per item branch, created at claim; **one item lock** serialises every author and
  reviewer access to it; removed after guarded completion once pushed.
- **Base contract (KT-04):** each job record carries worktree, branch, `base_sha`, its test
  digests and, for each code prerequisite, the accepted final PR head and — once merged —
  the observed mapping from that head to `mergeCommit.oid` (squash). Admission requires
  either the accepted head or the verified corresponding merge commit to be contained in
  the job base; missing, changed or unverified mappings refuse admission. Artifact and
  schema prerequisites use their typed acceptance receipts, never invented Git heads.
  Tracker readiness alone does not prove code availability. Tests: accepted unmerged
  stacks, squash-landed prerequisites, missing code, incorrect head→merge mappings.
- **Migration allocator** (`kyalloc.py`): an atomic, persistent reservation keyed by
  item/branch against the repository-wide migration namespace and active reservations;
  all concurrent migration writers observe the same authority; until it is installed,
  the existing reservation procedure stays in force. Tests: concurrent allocation,
  restart/reuse, conflicting external reservation.
- **Slot DBs** `ky_b1..b6`, `ky_v1..v4` on `ky-pg:55433` via the repository `local_db.sh`
  (registry-inclusive seed; mandatory schema/ledger/registry hashes in each slot
  receipt), supported throughout DB guards, preflight, model worktree/branch
  authorisation, executor and cleanup. Negative fixture: the 1320 prerequisite failure
  and a missing registry are detected.
- **Preflight v3** derives expectations from configured slots, runs a Claude-only smoke,
  and is the install receipt's precondition. Model `streams[].worktrees[]`, detector and
  executor paths migrate in B-0/B-1.

## 6. Dispatcher — full lifecycle (KS-05, KS-08)

`$KY_FLEET/kydispatch.py`; atomic instance lock via `kylock.sh` (session identity +
PID/PGID + process-start identity); `--dry`, `--once`; fixtures under
`fleet/tests/dispatch/` with checked-in expected job lists.

**Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no admissions
of any kind (bootstrap included). `run/HOLD_MERGES` → no queue submission of any kind.
Release gate (§10): while WAIT, only bootstrap-tagged jobs. Recovery: jobs recorded live
whose process group (PID/PGID + start identity) is gone → release claim, `interrupted`,
re-queue once. Freshness: `ky next --json` must come from the live tracker (a snapshot
fallback is refused; `version` must advance or match the EVENTS prefix hash). Then
refresh the campaign checkout and compute.

**Admission checks (replace LIVENESS):** tracker freshness, assigned worktree present
and locked, disposable slot DB READY with bound hashes, packet admitted by `kypacket.py`
(§8), base contains prerequisite heads, routing recomputed, turn/time caps set.

**Item declaration:** every retained executable item declares `completion_kind:
code | artifact | packet | operation`, its producer stream, reviewer identity rule,
detector and required step evidence (B-0 adds the fields).

| kind | trigger | model | identity / claim | post-action (script) |
|---|---|---|---|---|
| BUILD (code) | K item ready, unclaimed, no open PR, PRIORITY order | by routing (§9) | `KY_STREAM=K KY_LANE=<slot> ky claim <ID> --worker <slot> --lease 10800`; item lock | must end in `ky review <ID> --detail "PR #n @ <head>"` or `ky block`; else `interrupted` |
| BUILD (artifact) | K-owned artifact item ready | by routing | K claim; author identity recorded before review | registers path + digest via `ky review`; schedules ARTIFACT |
| REWORK | REJECTED at head, or **code-class** CI failure (classified; infra/flaky → RETRY-CI without a model) | routing; loop +1; escalation §9 | same worktree, item lock | as BUILD; evidence history retained |
| STEP | a required `step` whose named detector passes | script | — | `ky step <ID> <step> --evidence <path>` only after the detector passes |
| VERIFY | item in review; PR head without a verdict at (item, pre_merge, head, evidence-fp); required checks green; `Kāla DB Tests` green where the diff is relevant | Opus | **no item claim**; job lock (item, phase, head); item lock | verifier writes a **proposed** result; controller publishes (below) |
| ARTIFACT | artifact/packet item registered by its author, or a MODEL artifact | Opus | reviewer slot ≠ author identity; V claim only for V-owned items; S-owned artifacts get no V claim | `KY_STREAM=V … ky verdict <ID> --artifact-digest <sha256> --phase artifact …` (external review binding where the V-owned item requires it) |
| REGEN | PR DIRTY/CONFLICTING confined to declared generated outputs | script, pinned generator | item lock | merge base; regenerate only declared outputs; run applicable tests; record hashes; push; **register `ky review … @ <new head>`**; inheritance only by the patch predicate (below), else VERIFY |
| MERGE | ACCEPTED at the **registered** head (head-match guard), required checks + DB job success, base correct, protected-window listing satisfied, no hold | script | — | `gh pr merge "$PR" --auto --squash --match-head-commit "$REGISTERED_HEAD"` after the checks; a head mismatch refuses submission; once queued, any head change cancels the queue/auto-merge authorisation and requires fresh admission; workers never push under an outstanding queue authorisation; branch/ref evidence retained until guarded completion |
| COMPLETE | merged (code) / accepted artifact / receipted operation | script | K completes K items; S completes S items and independently accepted N/V items | typed `ky done` (`--pr n --reviewed-head <final PR head>` \| `--artifact-path` \| `--operation-receipt … --operation-id …` \| `--packet-verdict`); deployment containment and post-deploy use the **squash merge commit**; refusals logged by code; `deps_open_strict` → wait |
| REQUEST-PREP | ready N-owned operation | script + PLAN where the request needs authoring | N actor | request binds the reviewed merged script, request digest, lease, expiry, backup/restore/dry-run evidence per `executor.py` and the approved operation table |
| PRE-ACCEPT | prepared request | Opus (independent V slot) | job lock | acceptance record the executor requires |
| EXECUTE | pre-accepted request | script (`executor.py`, authority boundary unchanged) | — | receipt in `run/ops/receipts/`; GitHub protected-window dispatch stays an owner-approved workflow action |
| POST-READBACK | (a) deployed `writes_data` code item; (b) receipted operation item | Opus after a readback request | (a) job lock (item, post_deploy, squash merge sha, evidence-fp); (b) job lock (item, operation id, receipt sha256, evidence-fp) | two typed exits: (a) propose `--phase post_deploy` at the squash merge commit; (b) review the completed executor receipt, operation/request identity, measured readback and quiescence evidence and propose `--phase artifact --artifact-digest <receipt sha256>`; the controller publishes only after independence, boundary and unchanged-evidence checks; operation COMPLETE then uses `--operation-receipt <that receipt> --operation-id <that id>` under the existing typed guard; negative fixtures: script-head verdict, pre-acceptance record, wrong receipt digest, executor exit without semantic readback — none completes the operation |
| MODEL | S-owned model/close work (triage, joins, PRIORITY, C-1/C-2 artifacts, REPIN) | Opus PLAN job | S actor | artifact + ARTIFACT review where required |
| RULING | `ky request D-…` pending or N inbox unread | Opus | N actor | `ky decide … --as steward --delegated …`; `ky ack` |
| PLAN | wave boundary or `run/REPACKET.txt` | Opus **xhigh** | S actor | packets + tests; ARTIFACT review of the packet set |

**Claims, locks, renewals.** Only the owning stream claims; the dispatcher renews only
jobs that hold claims (`KY_LANE=<slot> ky renew --lease 10800` every 20 min); timeout →
reap the process group (PID/PGID + start identity) → release → `timed_out`. Job identity
(`job_id`, provider `session_id` when observed — never invented before launch —, item,
kind, slot, head/digest, evidence-fp, failure-class fingerprint and attempt count) is
persisted in `run/jobs/<job_id>/state.json`. On adoption, legacy claims, PRs and
checkpoints are reconciled into job state (B-2).
**Terminal release (KT-07):** every terminal job path (success, blocked exit, timeout,
interruption) persists its result and checkpoint, confirms the recorded process group has
exited, and releases any held tracker claim **before** freeing the slot; successful
`ky review` registration is not claim release. Release is bound to the job's persisted
item, worker and `claim_id`: the controller verifies that `run/claims/<slot>.json`
matches the job before `KY_LANE="$SLOT" ky release`, serialises release with slot reuse,
and on mismatch keeps the slot unavailable and reports "reconciliation required".
Renewal stops once termination begins. Claimless verifiers release only their job/item
locks. Tests: three successive successful BUILD jobs on one slot; immediate REWORK after
review; blocked exit; restart between checkpoint persistence and claim release.

**Verdict publication (controller-owned).** After a VERIFY/ARTIFACT job exits the
controller checks: exit status, reviewed HEAD unchanged, `git status --porcelain` clean,
tracked-file hash set unchanged, boundary evidence (§7). Only then does it publish
`KY_STREAM=V KY_LANE=<vslot> ky verdict …`. A boundary failure never publishes
ACCEPTED. If a published acceptance is later invalidated, an explicit REJECTED is
appended before any queue action.

**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head. Applied to every inherited Wave 0 head. After every
head change the owning stream registers `ky review <ID> --detail "PR #<n> @ <new-head>"`.

**Failure accounting:** failure-class fingerprints and attempt counts persist across
retries, escalation, restart and repacketisation; the third identical failure blocks
automatic attempts until a recorded changed condition permits retry.

**Messaging:** the dispatcher messages the conductor only for escalation failure,
block/park, verdict invalidation, gate change, wave complete, quota backoff,
dispatcher error, ceiling hit, unclassifiable CI failure.

**Tests (B-1):** fixtures for every kind and transition, recovery, timeout reaping, hold
precedence, gate WAIT with bootstrap exemption, ceiling refusal, stale-snapshot refusal,
duplicate instance refusal, head-match guard, inheritance predicate (substantive
resolution fixture), failure fingerprint persistence.

## 7. Worker launch (`$KY_FLEET/kyjob.sh <job_id>`) (KS-02, KS-06, KS-08)

```
# all values from $KY_RUN/jobs/<job_id>/state.json; every path absolute
cd "$WORKTREE" || exit 70
exec env -i HOME="$HOME" PATH="$KY_ROOT/bin:$NODE_BIN:/opt/homebrew/bin:/usr/bin:/bin" \
  LANG=en_US.UTF-8 TERM=dumb USER="$USER" TMPDIR="$TMP_PATH" \
  ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \
  KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \
  SE_EPHE_PATH="$SE_EPHE_PATH" SWE_EPHE_PATH="$SWE_EPHE_PATH" TESTS="$TESTS_NEWLINE_LIST" \
  "$CLAUDE_BIN" -p --bare --permission-mode bypassPermissions \
    --model "$MODEL" --effort "$EFFORT" --max-turns "$MAX_TURNS" \
    --strict-mcp-config --mcp-config "$MCP_CONFIG" $DISALLOWED \
    --output-format stream-json --verbose --add-dir "$KY_ROOT" \
    < "$PROMPT_PATH" > "$STDOUT_PATH" 2> "$STDERR_PATH"
```
- `EFFORT` is role-specific: `xhigh` for PLAN, `high` otherwise.
- `kyjob.sh` exits 78 if `DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY` is set
  in its own environment; `no_wrappers` behaviour preserved (tested). For fixture runs it
  forwards the validated `PRAVAHA_*` fixture configuration (§14 B-3).
- `MCP_CONFIG` (KT-02): bootstrap jobs use the independently reviewed, manifest-hashed
  empty configuration `{"mcpServers":{}}` staged in the bootstrap source tree
  (`fleet/mcp.none.json`), recorded per job as an absolute path; campaign jobs use the
  installed configuration whose hash is in the installation receipt (`mcp.none.json`
  unless the packet declares `needs_chart_data: true` → `mcp.marsys-only.json`).
- Bootstrap (B-1) launches do **not** go through `kyjob.sh` or the dispatcher: the planner
  prepares and validates the absolute worktree, executable `CLAUDE_BIN`, admitted bootstrap
  prompt, job state, scratch input/output/TMPDIR paths, environment values and deadline
  (missing inputs refuse launch), launches and supervises the process directly, records
  its process-group identity and termination result, and obtains independent review.
- CLAUDE.md under `--bare` is unknown: cards carry the applicable §I/§N rules per
  COVERAGE; B-3 includes a fixture job that reports whether the project CLAUDE.md is in
  context; the result is recorded in the install receipt.
- `precheck.sh` is fixture-aware through `KY_RUN`; the launcher writes the manifest
  precheck actually consumes **or** passes newline-delimited test paths in `TESTS`.
- **Verifier boundary** (enforced, not claimed): the launcher provides a read-only
  source/Git-metadata boundary (a sandboxed verifier worktree whose tracked files and
  `.git` are owned by a separate non-writable mapping — implemented and proven in B-1;
  same-user `chmod` alone is **not** accepted as the boundary), with writes limited to
  declared evidence, caches, `TMPDIR` and the slot DB; acceptance fixtures attempt Bash
  edits, chmod/replace, Git-index changes and shared-control writes and must all fail.
- Turn caps: BUILD 150, REWORK 100, VERIFY 60, PRE-ACCEPT/POST-READBACK 40, RULING 30,
  PLAN 300.
- Session persistence stays on (reconciliation evidence, §13).
- Prompt file = role card (≤ 1.5 k tokens) + packet (≤ 4 k) + job header (job id, slot,
  worktree, branch, `base_sha`, prerequisite heads, allocated migration number if any,
  loop, max loops, deadline). Oversized packets are rejected at admission, not at launch.

## 8. Packets (KS-07)

`00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md`, ≤ 4 k tokens; schema
`fleet/schemas/packet.json`; admitted by `kypacket.py check` (schema, hashes, size, test
availability, excerpt and reconciliation claims validated against pinned sources; a
failure names its reason). `packet_sha256` is computed over canonical content excluding
that field.

Front matter: `id, kind (feature | artifact | operation | schema-prerequisite |
bootstrap), wave, build_tier + routing_reason, needs_chart_data, max_loops (3),
plan_version, spec_sources[] (path, revision, section range, sha256),
schema_receipt_id, intended_schema (schema-prerequisite packets only),
original_failing_base (feature packets), test_commits[] (sha, digest, path),
expected_failing_assertion, pw_mechanism_version, release_pins (`not_applicable:
bootstrap` for Wave B packets), packet_sha256`.

Sections, inline:
1. **Immutable pins** — specification revisions/hashes; the build snapshot id
   (`dash_build`, `registry_revision`) from `run/RELEASE_RECEIPT.json` (bootstrap
   packets: `not_applicable`). Never `main_sha`, never a migration number (allocated at
   job start). A later L1 rebuild triggers a REPIN MODEL job that revalidates packets.
2. **Owns (floor) + allowed classes** — exact paths plus: declared generated outputs,
   tests, exports, direct consumers of a changed signature (disclosed in the PR).
   Prohibited: `FROZEN_PATHS.txt`, cross-campaign files, and — for **campaign** builders —
   control-plane code; **bootstrap** packets enumerate the D-1 control-plane source paths
   they may change. A prohibited path → `ky block --detail "freeze: <path>"` → STOP.
3. **Spec excerpt** — verbatim with path/revision/section/hash, plus the planner's
   contract-reconciliation line (e.g. protected-window steps now use
   `kala_protected_migrations.txt` + the deploy job, not `migrate.ts`/`deploy.yml`).
4. **Signatures / contract** — real columns from the admitted schema receipt;
   schema-prerequisite packets declare both the admitted existing schema and the intended
   additive contract; consumers wait for that prerequisite's verified schema receipt.
5. **Migration metadata** — `brief.migration` and `brief.op` populated consistently
   with the tracker's `writes_data` classifier (normalised values; prose or the string
   `NONE` is never truthy production metadata); `migration_class` and window batch id.
6. **Acceptance** — feature packets: the immutable original failing base, exact test
   digests and the observed failing assertion. **At admission** the dispatcher installs
   missing tests idempotently into the item branch and classifies the current result:
   expected-red → new implementation; already-green → an independent already-satisfied
   assessment (ARTIFACT), never automatic rejection or completion; REWORK and inherited
   heads keep their evidence history and run the relevant regression checks. Artifact and
   operation packets state explicit semantic acceptance and negative fixtures (no
   invented red test). Plus `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`.
7. **Evidence template** — `run/jobs/<job_id>/inspection.json` keys; readback request
   template for `writes_data`.
8. **PR template** — title (`[PROTECTED-WINDOW]` when required), body sections, then
   `ky review <ID> --detail "PR #<n> @ <40-hex head>"`.
9. **Do-not list** — no ledger PRs, no control-plane edits (campaign builders), no
   rebase/force-push, merge `origin/main` only when DIRTY outside generated files (else
   REGEN), one PR per item, no credential reads, no production access.

Verifier packet = the same file + `gh pr diff` + the independent test run the verifier
performs itself + gate outputs.

## 9. Routing and escalation (KS-10, KS-12)

`kyroute.py` normalises `owns`/`shared`/diff paths to repository-relative; prose entries
are resolved by the planner or routed to Opus. Opus is forced by: a migration file or
non-NONE migration metadata; any path under
`platform/python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
`platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**`,
`platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py`, `**/*ephemeris*`,
`platform/scripts/temporal/**`, `platform/scripts/migrate.ts`, `platform/migrations/**`,
`platform/src/proxy.ts`, `platform/src/lib/{auth,security,share,limits,mcp}/**`,
`platform/src/app/api/{auth,admin,db}/**`, `.github/workflows/**`, `infra/**`,
`platform/scripts/governance/**` (including `platform/scripts/governance/pravaha_tracker/**`),
`00_ARCHITECTURE/briefs/kalayantra/fleet/**`; any diff line touching `'lit'` state or
writing `verification_pass_status`; an import of `swisseph`/`jhora`. Paths in
`FROZEN_PATHS.txt` are not routed: STOP for native authorisation. Routing runs on the
packet and again on the actual diff before VERIFY: a Sonnet diff that hits an Opus rule
is **preserved** and re-queued as an Opus REWORK that assesses it (not discarded).
Fixtures: KA-1e, K1-2, K6-4 → Opus; a `platform/src/lib/auth/**` diff → Opus.

Escalation: Sonnet red after `max_loops` → Opus REWORK; one REJECTED on a Sonnet head →
Opus REWORK; Opus REJECTED twice → `ky block` → conductor → RULING or PLAN.

## 10. Release gate and the N-467 resume (KS-04)

`run/RELEASE_RECEIPT.json` (schema `fleet/schemas/release_receipt.json`): one
`release_id`, schema version, digest; every condition binds its evidence to that
release: certification → coordination commit/record id; pins → rebuild producer and run;
regeneration → main commit, generator version, output digest; PR dispositions → an
exhausted paginated API traversal with `{merged|parked|closed, owner, re_entry}`;
coordinator closure → SS's enumerated hand-off records. Missing or inconsistent evidence
is WAIT. Condition 5 has no producer today and stays WAIT until SS publishes it.

Both gate modes also require **final Wave B acceptance** (KT-03): the final
`run/VERSIONS.json` and a final installation receipt binding that manifest, the loaded
tracker revision, B-3's tested component hashes and measured rehearsal results, B-4's
independently accepted coverage and admitted packet hashes, and the validated B-5
governance backfill. `kygate.sh --pre-resume` validates the five release conditions and
that acceptance, and prints `READY_TO_PASTE` only when every prerequisite is satisfied
and the sole missing launch authorisation is the matching N-467 resume record; it
authorises no campaign job. Negative fixtures: bootstrap-only installation, absent
rehearsal, stale tested hashes, missing coverage, changed final manifest. The owner pastes the conductor after Wave B installation and
`READY_TO_PASTE`. The conductor, after version validation and exclusive instance
acquisition, writes `run/OWNER_RESUME.json` binding `N-467`, the release-receipt digest,
`approved_bundle_digest` (= the supplied <APPROVED_MANIFEST_DIGEST>), its session id and
timestamp, then runs the full gate. That
is the D-3 owner act; nothing further is required. The recorded certification-hold owner
releases `HOLD_MERGES` when its documented condition is met; the conductor never removes
a hold it did not set. STOP and global HOLD dominate bootstrap and campaign admission;
HOLD_MERGES blocks every queue submission. Negative fixtures: stale resume, mixed
release ids, each surviving hold, each missing field.

## 11. Conductor (KS-11) — see the paired prompt

Setup only exports paths and changes directory — **no checkout mutation** (`git pull`)
before verification and locking; campaign refresh belongs to the dispatcher under its
serialised checkout ownership (KT-01). Atomic instance acquisition (`kylock.sh acquire
conductor <session_id>`: `mkdir`-atomic, records session identity, PID/PGID and
process-start identity; a transient tool-shell PID is never the identity). Start-up:
manifest digest → `kyversion.sh --expected-manifest-digest` → lock → session state →
`OWNER_RESUME.json` → full gate. **Session state (KT-06):** on entry compare the observed
session identity with `CONDUCTOR_STATE.json`; re-entry into the same session preserves
`started_at` and counters; a different session preserves validated checkpoints,
deferred messages and campaign decisions, archives the previous session summary, and
initialises the new session's `started_at` and counters to zero; campaign failure
fingerprints and attempt counts are never reset by rollover (the same rule governs
`PLANNER_STATE.json`). Idempotent dispatcher start by the same helper
(detached stdin, managed logs; no extra owner question — the paste authorises it);
reconcile **both** inboxes (`ky ack <id>` for S, `ky ack <id> --steward` for steward,
after action or durable deferral). Wait: `ky inbox --stream S --wait 540 --json`;
`wakeups` incremented after **every** return; elapsed time and thresholds checked before
waiting again. Hand-off at 60 wake-ups, 8 h, `handoff`, or a harness context warning:
`run/HANDOFF_CONDUCTOR_<ts>.md` + `_latest`, release the lock, stop.

## 12. Finalisation (KS-09) — outside the ordinary dispatcher

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

## 13. Measurement (KS-12; owner: no caps)

- The reviewed baseline implementation is imported from its recorded scratch source
  into `scripts/token_economy/token_baseline.py` (merged) **before** any measured v3
  total is reported. Missing source or coverage is reported as unknown, never zero.
- Accounting ownership is defined for every provider session and child session;
  repeated result events are de-duplicated; transcript usage is used only for uncovered
  calls; whether parent usage includes children is proven before child totals are added.
  Fixtures: normal completion, duplicate results, killed job, parent/child sessions,
  interactive planner/conductor sessions, bootstrap jobs, missing records.
- Reported separately: distinct guarded-completed item ids, decision completions, joins,
  accepted heads, weighted progress — each with its scope denominator and observation
  boundary (historical 46 = 39 guarded + 1 join + 6 decisions).
- Persistent failure fingerprints and attempt counts (§6); `no_progress_jobs`;
  escalations; rejection rate; CI-infra retries; lead time p50/p90; four-class tokens by
  role, kind and per guarded completion.
- Savings and throughput remain **cannot be estimated** until comparable completed work
  and reconciled four-class usage exist; the audit's 64 % is an upper bound on historical
  addressable classes, not a forecast.

## 14. Waves (KS-01, KS-02, KS-03, KS-10)

**Wave B — bootstrap (during the hold; D-1 applies; nothing installed before the
owner's merge).** Order is mandatory.

| id | work | by | acceptance |
|---|---|---|---|
| B-0a | **Capacity inventory**: `git worktree list --porcelain` → `WORKTREE_DISPOSITIONS_v2_1.md` (keep / remove / archive per copy, dirty and unpushed state noted); **owner disposes**; no new copy before the count is ≤ 14 | planner → owner | registration count ≤ 14 before B-1 |
| B-0b | **Reconcile the model** per §0: commit the mirror edits; `ACCEPTANCE_ROOTS`; `CLOSURE`; triage; completion_kind/producer/reviewer/step fields; namespaced bootstrap ids; D-RETIRE decisions registered (staged refusal); `streams[].worktrees[]`, detector and executor paths migrated; schema receipt admitted; joins regenerated; both reconciliation tests | planner (in the relaunch-plan checkout, branch switch) | validator green; path-only test identical; triage test equals the reviewed expected delta; closure hash reproducible |
| B-0c | **Bootstrap prerequisites**: BOOTSTRAP card, fixture builder/verifier cards, `fleet/schemas/packet.json` (bootstrap kind), `fleet/schemas/release_receipt.json`, the staged empty MCP configuration `fleet/mcp.none.json` (`{"mcpServers":{}}`), the bootstrap launch-input template (worktree, `CLAUDE_BIN`, prompt, job state, scratch paths, environment, deadline), and the bootstrap version manifest `run/VERSIONS.bootstrap.json` recording <APPROVED_SOURCE_COMMIT>; one independent review | planner + reviewer session | reviewed; hashes recorded |
| B-1 | **Implement, one packet each** (bootstrap kind; release pins `not_applicable`; enumerated D-1 paths): `kydispatch.py`, `kyjob.sh` (+ verifier boundary), `kylock.sh`, `kyalloc.py`, `kyverdicts.py` (+ the shared inheritance predicate, also applied to the tracker), `kyroute.py` + `FROZEN_PATHS.txt`, `kypacket.py`, `kygate.sh` (+ `--pre-resume`), `kyregen.sh`, `kyreport.py` + baseline import, `kyversion.sh`, override-preserving `ky`/`kybrief` wrappers, `local_db.sh` (repository, registry seed, slots), `preflight.sh` v3, `finalize.sh` v3, `install.sh`, tracker semantic changes (declaration fields, inheritance predicate, decision staging), executor table additions (incl. K9-23's), `precheck.sh` fixture-awareness | Opus bootstrap jobs launched and supervised **directly** by the planner (CLAUDE_BIN, cwd = bootstrap worktree, `--mcp-config` = the staged `mcp.none.json`; process-group identity and termination recorded; no `kyjob.sh`, no dispatcher) | each packet names its command, expected result and negative cases; fixtures per §5–§12; tests and review independent of the not-yet-built dispatcher |
| B-2 | **Review → owner merge → install**: independent review per PR in a separate session; owner merges; `install.sh` installs only reviewed, owner-merged source (fleet, tracker, wrappers, **and** the approved plan, prompts, cards, manifest) → `run/INSTALL_RECEIPT.json` (installed hashes, merge commit, `CLAUDE_BIN`, the running tracker's loaded revision); proves the old supervisor/sweep cannot dispatch (`STOP_*` + process absence); creates the campaign checkout; publishes the staged D-RETIRE decisions; reconciles legacy claims/PRs/checkpoints into job state; the receipt is marked `mode: bootstrap` | Opus job + owner | receipt hashes equal the merged tree; `preflight.sh launch` green; `kyversion.sh --bootstrap` green |
| B-3 | **Isolated rehearsal** on the installed, version-checked bundle: fixture wrapper preserving validated `PRAVAHA_HOME/EVENTS/PLAN_MODEL/REPO/HOLD/URL/TRACKER_PORT`; a **second tracker** on a reserved unused loopback port with HOME, model, EVENTS, claims, snapshots and backups under `$KY_SCRATCH/fixture/`; no production DB configuration; fixture-local detectors only (`/api/verify` included); a fixture backend for Git pushes, PR creation/read/checks/merge, deploy observations and executor submission (local fixture remotes; production executor and credentials denied); the real CLI, claim, verdict and typed completion paths against the fixture tracker; includes the CLAUDE.md-visibility fixture and the verifier-boundary fixtures | dispatcher + jobs | live EVENTS size/hash unchanged; no fixture connection to port 8767; zero external PR/queue/production requests; expected fixture transitions; fixture server, DBs and worktrees cleaned up; **tested component hashes and measured rehearsal results recorded** for the final receipt |
| B-4 | **Cards + packets**: KARAKA, PARIKSAKA, ADHIKARIN cards with `COVERAGE.md` (§I + §N + charter §0 + retained acceptance contracts); one independent card-coverage review; packets + tests for Wave 0 and Wave 1, `kypacket.py check` green | planner | coverage review ACCEPTED; packets admitted; **accepted coverage and admitted packet hashes recorded** for the final receipt |
| B-5 | **Governance backfill and final acceptance**: CURRENT_STATE §2 banner + SESSION_LOG entry (validated); the campaign handshake from Codex to Claude; the final `run/VERSIONS.json`; a **final installation receipt** binding that manifest, the loaded tracker revision, B-3 evidence, B-4 evidence and the validated backfill. Any changed component afterwards requires reviewed installation and the affected acceptance checks before a new final receipt | planner | `schema_validator.py` green; normal `kyversion.sh` green against the final manifest and receipt |

**Wave 0 — after `READY_TO_PASTE` and the conductor's resume.** In order: the necessary
`J-0c → J-0d → J-0 → J-0m` chain (artifact BUILD exits + ARTIFACT reviews, respecting
earned completions); `J-4p` after `K0-SV`; then pin-consuming work: the 11 ACCEPTED PRs
under the inheritance predicate (K4-2a #3379 [PW] → K4-2aw → K4-2b → K4-3 → K6-5a [PW] →
K6-5 → K6-123 [PW]; K7-1a #3333 (REGEN) → K7-1b → K7-2; K-CERT-2 #3426 in the Suvarṇa
window); protected migrations 1351–1356 (+1362) in **one** owner-approved window; retire
#3283/#3275 by decision; #3272 refresh-or-close; K7-3 repacketed.

**Wave 1 — the computed closure**, in dependency order (owed steps of K3-1 and L0-M,
KA-3a/3b after J-0m, K3-2 after J-5s, KA-4b, K7-3/K7-4, the K5/VC/K6-4/K8-REG/K9/KR
members, schema prerequisites). DB-touching items in ≤ 2 windows.

**Wave 2 — Gochara 5.0 sealing prerequisites and Pravāha disposition** (accepted
`J0_DISPOSITION` artifact; the 37 inherited PRs merged/parked/closed by decision).

**Wave 3 — certification mappings and close**: K-CERT re-packeted against the admitted
schema (after KYD-150's tier column), V-track exits as deterministic checks or
ARTIFACT jobs, N decisions, `finalize.sh` v3 (§12), SESSION_CLOSE validated.

## 15. Owner decisions and delegated calls (unchanged from v2.0)

1 planner xhigh · 2 3+2 scaling on demand · 3 re-scope to the critical path · 4 the
five-part gate · 5 no token caps · 6 ADHIKĀRIN on demand · 7 all Claude · 8 launch by
paste. **D-1** control-plane changes in Wave B under review + install receipt (campaign
builders keep the prohibition). **D-2** rework from scratch, then Astra. **D-3** the
owner's paste of the conductor prompt is the N-467 resume, recorded by the conductor
(§10) — no further approval.

## 16. Owner steps

1. Now: new Antigravity session in
   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan`, Opus 5.5 /
   xhigh → paste **KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md**. Dispose of worktrees when it
   asks (B-0a); merge its PRs when their independent reviews are green (B-2).
2. After `kygate.sh --pre-resume` prints `READY_TO_PASTE`: new Antigravity session in
   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, Opus 5.5 / high →
   paste **KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_2.md**. The paste is the N-467 resume.
   Restart with the same prompt whenever it posts a hand-off.

## 17. Closure maps

**KS-01…KS-12 (review v2.0) → v2.1**

| finding | closed by |
|---|---|
| KS-01 | §0 closure procedure (roots first; field semantics; two tests; D-RETIRE decisions; namespaced ids); Wave 0 J-chain → J-4p after K0-SV |
| KS-02 | §5 capacity (33 > 15 → owner dispositions first; planner works by branch switch); B-0c prerequisites before B-1; bootstrap packets with `release_pins: not_applicable` and enumerated D-1 paths; `CLAUDE_BIN` + `cd "$WORKTREE"` in §7; implementation packets incl. `install.sh`, allocator, tracker changes; B-2 installs plan/prompts/cards/manifest and records the loaded tracker revision; B-3 on the installed bundle; new receipt after any change |
| KS-03 | B-3 isolation contract (override-preserving wrapper; second tracker on a reserved port under the dated scratch root; fixture detectors; fixture backend for git/PR/deploy/executor; acceptance incl. live EVENTS hash unchanged) |
| KS-04 | §10 (`--pre-resume` → `READY_TO_PASTE`; release_id/digest binding; resume written after version validation + lock, then full gate; hold ownership; negative fixtures); §11 and §16 ordering |
| KS-05 | §6 (completion_kind declarations; artifact BUILD; STEP; author identity; REQUEST-PREP / PRE-ACCEPT / EXECUTE / POST-READBACK; K9-23 → B-1; legacy reconciliation; renew only claim holders; item lock) |
| KS-06 | §5 (base contains prerequisite heads; `kyalloc.py`; dated scratch root; registry seed; slots everywhere); §7 (`CLAUDE_BIN`, cwd, role-specific `--effort`, precheck via `KY_RUN`, `TESTS` newline list) |
| KS-07 | §8 (original failing base; admission classification incl. already-green assessment; artifact/operation semantic acceptance; schema-prerequisite dual declaration; `brief.migration`/`op` consistency; canonical `packet_sha256`; reasons on admission failure) |
| KS-08 | §6 verdict publication by the controller; enforced verifier boundary (§7); explicit REJECTED on invalidation; one inheritance predicate; `ky review` after every head change; head-match guard; final PR head vs squash merge commit |
| KS-09 | §12 finalisation outside the dispatcher; `DRAIN_RECEIPT.json` for C-3; PID/PGID + start identity; bounded independent reviewers; `FINAL_RECEIPT.json` for C-4 |
| KS-10 | §3 (Kāla DB Tests retained; COVERAGE includes §I; `FROZEN_PATHS.txt` manifest shared with precheck); §9 `platform/`-prefixed security and tracker globs; LIVENESS deleted → admission checks; B-4 extra sign-off wording removed |
| KS-11 | pairing rule (manifest digest named in each paste; `kyversion.sh` scope stated); `kylock.sh`; idempotent detached dispatcher start without an extra question; state init and all-return counting; planner checkpoints; `ky ack --steward`; strategy v1.2 §§2–4 made historical |
| KS-12 | §13 (baseline import before totals; session/child ownership and fixtures; separate completion measures with denominators; failure fingerprints; structured quota errors; Sonnet diff preserved on reroute) |

**KT-01…KT-08 (review v2.1) → v2.2**

| finding | closed by |
|---|---|
| KT-01 | pairing rule (source-commit anchor for planning; final-manifest digest for the conductor); planning read item 2 qualified; conductor setup has no `git pull` (§11); `OWNER_RESUME.approved_bundle_digest` = supplied digest (§10) |
| KT-02 | B-0c staged `fleet/mcp.none.json` + launch-input template; §7 `MCP_CONFIG` per job; planner launches/supervises B-1 directly |
| KT-03 | `kyversion.sh --bootstrap` for B-2/B-3; B-3/B-4 evidence recorded; B-5 final manifest + final receipt; both gate modes require final Wave B acceptance; negative fixtures (§10, §14) |
| KT-04 | §5 base contract with head→merge-commit mapping; §6 MERGE with `--match-head-commit`, queue cancellation on head change, no pushes under queue authorisation |
| KT-05 | §6 POST-READBACK two typed exits; operation COMPLETE via receipt + operation id; identity and negative fixtures |
| KT-06 | §11 session-state rule (same-session re-entry vs new-session reset; fingerprints never reset); applied to planner state; acceptance with consecutive hand-offs (B-1 tests) |
| KT-07 | §6 terminal release bound to item/worker/claim id; serialised with slot reuse; renewal stops at termination |
| KT-08 | §5 job scratch paths and dispatcher log under the dated scratch root; §7 launch I/O paths; cleanup rules |

**KR-01…KR-12 (review v1.0):** KR-01/03/08/10 closed directly; KR-02/04/05/06/07/09/11/12
closed through the KS and KT replacements above (Astra v2.1 Part 1).

## 18. Risks
One subscription, headroom unreadable (backoff-and-report; one conductor; owner checks
twice daily) · Sonnet on L3 logic (routing, tests-first, Opus verifier, escalation) ·
dispatcher defects (fixtures per transition, `--dry` in CI, admission checks,
`no_progress_jobs`) · Suvarṇa slips (Wave B proceeds; the gate waits for the receipt) ·
scope creep (closure committed; additions need a MODEL job) · worktree ceiling (owner
dispositions precede any copy).

## Changelog
- v2.2 (2026-10-11): KT-01…KT-08 applied (non-circular paste anchors; staged MCP config and
  direct B-1 supervision; bootstrap vs final version modes; squash-aware prerequisite
  containment and head-bound queueing; typed operation readback; session-state rollover;
  terminal claim release; scratch-root I/O).
- v2.1 (2026-10-11): all KS-01…KS-12 replacements applied; LIVENESS removed; verifier
  boundary made enforceable; finalisation moved outside the dispatcher; gate pre-resume
  mode; closure procedure made reproducible.
- v2.0 (2026-10-11): rebuilt from scratch after Astra v1.0. v1.0 withdrawn.
