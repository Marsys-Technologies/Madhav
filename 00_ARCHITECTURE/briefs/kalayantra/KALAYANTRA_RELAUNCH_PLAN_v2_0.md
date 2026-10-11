---
artifact: KALAYANTRA_RELAUNCH_PLAN_v2_0.md
status: DRAFT — for Astra's second review, then native approval. Replaces v1.0 entirely (v1.0 withdrawn after ASTRA_REVIEW_KALAYANTRA_RELAUNCH v1.0: REWORK, KR-01…KR-12). On approval this plan is the single operating document of KĀLA-YANTRA v3; CHARTER v1.2 keeps only §0 (goal) and its five hash-pinned specification documents; the VELOCITY AMENDMENT v2.0 is retired.
version: 2.0
authored_by: Claude Code (Fable 5.1), worktree kalayantra/relaunch-plan
authored_on: 2026-10-11
audience: Astra (reviewer); native (approver); the planning session (KALAYANTRA_V3_PLANNING_PROMPT_v2_0.md); the conductor session (KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_0.md)
paired_prompts:
  - KALAYANTRA_V3_PLANNING_PROMPT_v2_0.md
  - KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_0.md
pairing_rule: plan, prompts and cards carry the same version; `kyversion.sh` compares versions AND sha256 of plan/prompts/cards recorded in `run/VERSIONS.json` before any launch; a mismatch refuses to run (KR-12).
authority_precedence: root CLAUDE.md (§I, §N) > owner decisions (§15) > this plan > role cards > packets > anything a job infers
strategy: KALAYANTRA_RELAUNCH_STRATEGY_v1_0.md (operative passages corrected in v1.1)
evidence: 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md (audit worktree, 758e0dbb4); reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v1_0.md; scratch notes_ky_state.md, notes_suvarna_state.md, notes_workflow.md, KY_MECHANICS_CATALOGUE.md (2026-10-11)
---

# KĀLA-YANTRA v3 — relaunch plan v2.0 (Claude, event-driven, essential governance only)

## 0. Goal, definition of done, scope

**Goal (CHARTER §0, unchanged):** build the Kāla layer as one engine per PLAN v1.1 §9 /
ALGO v1.1 (21 cards), absorb Gochara 5.0 to its "5.0" flip, rebuild and serve the layer
for chart `482012f1`, ship certification mappings, close with a validated SESSION_CLOSE
and a finalizer receipt. Suvarṇa certifies the Kāla assets afterwards.

**Retained acceptance set (the re-scope anchor, owner decision §15.4):**
(i) Kāla serves `482012f1` end-to-end — every published Kāla read model answers for
that chart from a rebuilt layer; (ii) the Gochara 5.0 flip is sealed; (iii) certification
mappings exist for every served Kāla asset; (iv) a guarded close.

**Scope rule (KR-03).** The planner computes the **transitive prerequisites** of (i)–(iv)
from the 148-item model's `depends_on`, `steps`, `join` and `requires_outcome` fields
and the item briefs — *before* assigning waves. Everything in that closure is **(a)
critical path**. Items outside it are **(b) deferred** (parked in the tracker with
`re-entry:` text; never counted as closed) or **(c) dispositioned** (inherited Pravāha
material: merged / parked / closed per an accepted `J0_DISPOSITION` packet). A missing
required column is **never** evidence that its consumer is deferrable: it becomes an
Opus schema-prerequisite item (additive migration, protected window if needed) or an
explicit blocked contract decision (`ky request D-…`). Cancelled control items
(B-K-INBOX, B-CLAIM-RECOVERY) are retired by a recorded decision
(`ky decide … --outcome refused --as native --detail "retired by relaunch plan v2.0"`);
no invented tracker commands. `JOIN-ALL` and C-1..C-4 are regenerated after the triage
is committed to the model so that deferred items are not inside the close join.
Partial failure closes `CLOSED-PARTIAL` with the (b) list attached.

**Deferral candidates the planner must examine first** (from the briefs; Astra Part 1):
J-7 (optional Tier-2 Sudarśana, outside sealed 5.0), J-7b (documentation-only),
D-T2 and L0-K (only if the closure shows their corpus work is not needed for (i)–(iii)).
An honest reduced count exists only after the closure is computed; none is claimed here.

## 1. Principles (what "elevated" means here)

1. **Single-pointed:** accurate, high-velocity implementation of the critical path.
   Governance and security are kept where they protect correctness, production, or
   signal honesty; everything else is cut (§3).
2. **Jobs, not lanes.** A model runs only for a named job with a packet; it exits.
   Nothing polls with a model. Waiting is a script's job.
3. **Deterministic first.** Scheduling, claims, renewals, locks, gates, routing, test
   installation, regeneration, metering and liveness are scripts with tests. Models
   build, verify, rule and plan.
4. **Packets carry the truth the builder needs, and nothing stale.** Immutable spec
   pins are separated from the mutable checkout base and the migration allocator.
5. **Every signal is earned (CLAUDE.md §N.8).** A gate line, a verdict, a "done", a
   token figure, a progress percentage — each has a detector and a negative fixture, or
   it is reported as WAIT/unknown.
6. **Token economy by construction:** no idle model turns; small fixed context per job;
   diff-first review; bounded conductor; metered per job with one source of truth.

## 2. Starting point — what exists and is reused (grounded)

| asset | state | reuse |
|---|---|---|
| Tracker `ky` (pravaha_tracker, port 8767, EVENTS.jsonl) | live, lock-safe claims (`lease_s ≤ 10800`, `expires_at`), guarded `ky done`, verdict identity (item, phase, head\|digest), merge-only inheritance, `ky next --json`, `ky inbox --wait`, steward override | kept as the single ledger; wrappers re-pointed (§5) |
| 148-item live plan model (`wt/campaign/.../plan_model.json`, **uncommitted** edits) | 46 done (31.1 % plain; 37.6 % weighted), 15 open PRs, 102 remaining | committed in B-0; triage written into the model, joins regenerated |
| 20 merged engine items + `kala_core`, CI canary, `kala-db-tests` | on main | built upon |
| 11 ACCEPTED-unmerged PRs (#3379, #3385, #3390, #3393, #3399, #3402, #3404, #3333, #3335, #3336, #3426) | frozen by HOLD_MERGES; 6 at exact head, 5 moved by merge-only pushes | Wave 0 |
| Five hash-pinned specification documents | hashes match (Astra) | packet sources |
| Item briefs (`spec/owns/shared/tests/compat/contract/migration_class/op/g8`) | 148 live | packet inputs, after contract reconciliation (§8) |
| `fleet_live/{precheck.sh --item, local_db.sh, preflight.sh, verify_specs.sh, finalize.sh, readback_sql.sh, executor.py}` | work for the old topology | kept; re-pointed and re-tested in B-1 (local_db gains the registry seed; preflight derives from slots; finalizer rewritten) |
| Protected-window mechanism (`kala_protected_migrations.txt`, deploy job, `verifier_principal`) | live, owner-approved | kept unchanged; windows batched |
| Learned rules (KARAKA.md / PARIKSAKA.md) | written by the campaign | folded into the cards |
| Token audit + corrected baseline script | audit worktree 758e0dbb4 | `kyreport.py` builds on it (§13) |
| Astra review KR-01…KR-12 | reviews/ | every finding has a closure line in §17 |

## 3. Essential governance and security — kept vs cut

**Kept (each protects correctness, production or honesty):**
- Root CLAUDE.md §I and §N (facts/interpretation separation; FROZEN orchestrator §N.2 —
  a freeze violation is STOP-and-native, never "route to Opus"; idempotency §N.3; honest
  tiers §N.4; earned signals §N.8).
- The tracker as the only ledger: claims, `ky review` with `PR #n @ <head>`, verdicts,
  guarded `ky done` with typed evidence, decisions. No ledger PRs, no digests-as-PRs.
- Verification: independent verifier, one verdict per identity with evidence-aware
  re-review, required CI checks (`TypeScript (src only)`, `Unit Tests`, `Secret Scan`,
  `Governance Gates`, `Governance Tool Tests`), item tests + named mutations + compat
  checks, post-deploy readback for `writes_data` items.
- Production safety: protected-window flow; migration-number allocator; no worker ever
  holds `DATABASE_URL` (env scrub, exit 78); readback-only production SQL via the
  executor; no merge by a model (dispatcher queues with `--auto` under branch protection;
  the owner can hold with one file).
- Frontier-by-rule routing with fixtures; escalation never grants authority.
- One governance record pair for the campaign: the C-2 CURRENT_STATE banner +
  SESSION_LOG entry, and the C-4 validated close.

**Cut (measured as waste, or ceremony without a detector):**
- Standing lanes and their heartbeats, idle cycles, claim-renewal model turns
  (57 % of 3,946 cycles; 70 % of events were heartbeat/note/ack).
- The ADHIKĀRIN standing lane and the owner-surrogate charter (3,677 tokens) → a
  one-page authority card and on-demand RULING jobs; rulings only on `ky request`.
- NEW ITEM reports and the §2 reservation ceremony (153 reports, 93 parks) → the
  dispatcher's `ky block --detail` with a typed reason; packets name allowed classes.
- Per-cycle DIGEST.md, Codex blocks files, ledger branches, SESSION_OPEN ceremony
  (one handshake record in B-5), charter §3/§5/§11 and the amendment as operating text.
- Whole-document reads of the 70 KB charter and 115 KB plan by every job → cards +
  packets.
- V-track "packet exits" as LLM reviews where a deterministic check suffices
  (ARTIFACT jobs remain where a judgment is genuinely required).

## 4. Roster and capacity (owner decisions §15.1–15.3, 15.7)

| role | model / effort | mode |
|---|---|---|
| Planner | Opus 5.5 xhigh | interactive, owner-launched (PLANNING prompt); per-wave packet refresh as a headless PLAN job |
| SŪTRADHĀRA (conductor) | Opus 5.5 high | interactive, owner-launched (CONDUCTOR prompt), event-woken, bounded |
| PRAHARĪ (dispatcher) | script | background, 60 s tick, instance-locked |
| KĀRAKA (builder) | Sonnet 5.5 high | BUILD / REWORK jobs |
| KĀRAKA-escalated | Opus 5.5 high | BUILD / REWORK jobs after escalation or by routing |
| PARĪKṢAKA (verifier) | Opus 5.5 high | VERIFY / POST-DEPLOY / ARTIFACT jobs, source-read-only |
| ADHIKĀRIN | Opus 5.5 high | RULING jobs on demand |
| Bootstrap builder (Wave B only) | Opus 5.5 high | control-plane packets (§15.D-1) |
| LEKHAKA | none | `kyreport.py` |

Capacity: `KY_BUILDERS_MIN=3`, `KY_BUILDERS_MAX=6`, `KY_VERIFIERS_MIN=2`,
`KY_VERIFIERS_MAX=4`; the dispatcher runs `min(max, demand)` per kind. No token caps or
budgets (§15.6). The dispatcher backs off 30 min only on a subscription refusal
(429/usage-limit in the job's last lines) and reports it.

## 5. Topology and paths (KR-01, KR-05, KR-06)

- `KY_ROOT=/Users/Dev/kalayantra`, `KY_RUN=$KY_ROOT/run`, `KY_FLEET=$KY_ROOT/fleet_live`,
  `KY_SCRATCH=/Users/Dev/scratch.noindex/claude/madhav/kalayantra` (TMPDIR, DB dumps,
  job logs). **Every** path in scripts, prompts, cards and packets is absolute, built
  from these variables; nothing is relative to a worktree except source files.
- **Campaign checkout:** branch `kalayantra/campaign`, created in B-2 from `origin/main`
  with upstream `origin/main`, at `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`;
  `PRAVAHA_REPO`, `PRAVAHA_PLAN_MODEL`, prompts, cards and the dispatcher read from it;
  the dispatcher fast-forwards it each tick. (The current detached `wt/campaign` mirror
  is retired after B-0 commits its edits.)
- **Work worktrees:** `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item-id-lower>/`,
  one per item branch, created by the dispatcher at claim, **serialised** between the
  item's BUILD/REWORK and VERIFY jobs by the job lock, removed (`git worktree remove`
  + `prune`) after merge/close once the branch is pushed. **Capacity inventory first
  (B-0):** `git worktree list --porcelain` is reconciled against the 15-per-tool policy;
  stale copies are removed or archived (bundle to `/Users/Dev/Archives/`) before any new
  one; the dispatcher refuses to create a copy that would exceed the ceiling and
  reports it.
- **Slot DBs:** `ky_b1..b6`, `ky_v1..v4` on `ky-pg:55433`, created by the **repository**
  `local_db.sh` (registry-inclusive seed), reset per job; each slot receipt binds the
  schema, ledger and registry fixture hashes; a negative fixture proves the 1320
  prerequisite failure is detected.
- **Preflight v3** derives expectations from configured slots (not "13 worktrees, 11
  DBs"), runs a Claude-only smoke, and is the install receipt's precondition.
- Model `streams[].worktrees[]` and every detector/executor path are migrated in B-0/B-1
  (`ky preflight` checks cwd against them).

## 6. Dispatcher — full lifecycle (KR-04, KR-07, KR-09)

`$KY_FLEET/kydispatch.py` (instance lock `run/dispatcher.lock`; `--dry` prints the job
list; `--once` runs one tick; fixtures under `fleet/tests/dispatch/` with checked-in
expected job lists).

**Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no launches
of any kind (bootstrap included). `run/HOLD_MERGES` → no queue submissions. Then the
release gate (§10): while WAIT, only bootstrap-tagged jobs run. Then recovery of jobs
recorded live in `run/JOBS.jsonl` whose process group is gone (release claim, mark
`interrupted`, re-queue once). Then refresh the campaign checkout (`git fetch` +
`--ff-only`). Then compute and launch.

**Inputs:** `ky next --stream K --json` and `--stream V/S/N` (ready/running/blocked with
`deps_open`), `run/claims/*.json` (unexpired), EVENTS tail parse for the latest verdict
per identity (helper `kyverdicts.py`, tested against `verdicts.py` semantics), `gh pr
list/view --json` (state, head, base, checks, mergeable), `run/PRIORITY.txt`,
`run/jobs/*/state.json`.

**Job kinds and their deterministic pre/post actions:**

| kind | trigger | model | claim | post-action (script) |
|---|---|---|---|---|
| BUILD | K item `ready`, unclaimed, no open PR, in PRIORITY order | Sonnet / Opus by routing (§9) | `KY_STREAM=K KY_LANE=<slot> ky claim <ID> --worker <slot> --lease 10800`; worktree + branch `kalayantra/<id>` from `base_sha`; tests installed (§8); `TESTS` manifest written | job must end with `ky review <ID> --detail "PR #n @ <head>"` or `ky block`; else `interrupted` |
| REWORK | REJECTED verdict at head, or **code-class** CI failure (classified: infra/flaky → RETRY-CI, no model) | same routing; loop +1; escalate per §9 | same worktree, serialised | as BUILD |
| VERIFY | item in `review`, PR head has no verdict at (item, pre_merge, head, evidence-fp), required checks green | Opus | **no item claim** (K owns it); job lock (item, phase, head) | `KY_STREAM=V KY_LANE=<vslot> ky verdict <ID> --head <sha> --phase pre_merge --result … --detail …`; worktree `git status --porcelain` must be empty or the verdict is voided |
| REGEN | PR `DIRTY`/`CONFLICTING` and the conflict is confined to declared generated outputs | script (pinned generator) | job lock | merge base, regenerate only declared outputs, run applicable tests, record hashes, push; if the reviewed patch is unchanged (diff-of-diffs equal) acceptance inherits, else a VERIFY job at the new head; conflicts outside generated files → REWORK |
| MERGE | ACCEPTED at current head, required checks success, base correct, no hold, protected-window listing satisfied | script | — | `gh pr merge <n> --auto --squash` (branch protection enforces checks) |
| COMPLETE | PR merged (or artifact accepted / operation receipted) | script | — | typed `ky done` (`--pr n --reviewed-head sha` \| `--artifact-path` \| `--operation-receipt … --operation-id …` \| `--packet-verdict`); refusals logged with code; `deps_open_strict` → wait, not retry-storm |
| POST-DEPLOY | `writes_data` item merged, `Deploy to Cloud Run` (workflow_run) success containing the merge | Opus (readback judgment) after an OPERATION readback | job lock (item, post_deploy, merge_sha, evidence-fp) | `ky verdict … --phase post_deploy`; re-review allowed when the evidence fingerprint changes |
| OPERATION | executor request needed (`readback_sql`, `migration_readback`, protected-window dispatch) | script via `executor.py` (authority boundary unchanged) | — | receipt in `run/ops/receipts/`; dispatch of the deploy job is **owner-approved in GitHub**, never by a model |
| ARTIFACT | V-owned packet exit whose brief requires a judgment; or `--artifact` verdict for a model/triage artifact | Opus | V claim (`KY_STREAM=V`) | `ky verdict <ID> --artifact-digest <sha256> --phase artifact …`; author ≠ reviewer slot or bound external review |
| MODEL | S-owned model/close work (triage commit, join regeneration, PRIORITY recompute, C-1/C-2 artifacts) | Opus (PLAN job) | S actor | artifact + ARTIFACT review where the brief requires it |
| RULING | `ky request D-…` pending, or `ky inbox --stream N` unread | Opus | N actor | `ky decide D-… --outcome … --as steward --delegated --detail …`; `ky ack` |
| LIVENESS | every 2 h per slot | **script only** (claim/renew/release a fixture item in the fixture event root) | — | proves the slot's DB, worktree root and tracker reachability; no model |
| PLAN | wave boundary or `run/REPACKET.txt` | Opus xhigh | S actor | packets + tests for the next wave; ARTIFACT review of the packet set |

**Claims and locks.** Only the owning stream (K for K items, V for V items) acquires an
item claim; the dispatcher renews every live job's claim every 20 min with
`KY_LANE=<slot> ky renew --lease 10800` (ownership is worker/claim identity, not PID);
on timeout (`KY_MAX_JOB_SECS`: BUILD 10,800, VERIFY 3,600, RULING 1,800, PLAN 14,400)
it **reaps the process group first**, then releases the claim and marks the job
`timed_out`. Successful jobs release their claim in the post-action. Job identity
(`job_id`, `session_id`, item, kind, slot, head/digest, evidence-fp) is persisted in
`run/jobs/<job_id>/state.json` before launch; restart recovery reads it.

**Messaging discipline.** The dispatcher messages the conductor (`ky send --to S`)
only for: escalation to Opus failed, `ky block/park`, verdict reversal, gate state
change, wave complete, quota backoff, dispatcher error, worktree ceiling hit,
unclassifiable CI failure. Everything else is logged in `run/dispatcher.log` and
`JOBS.jsonl`.

**Tests (B-1 acceptance):** fixture EVENTS/claims/gh JSON for every kind and every
transition (ready→claim→review→verify→merge→complete; reject→rework→escalate; dirty→
regen→inherit/re-verify; interrupted→recover; timeout→reap→release; hold precedence;
gate WAIT with bootstrap exemption; ceiling refusal; two dispatcher instances → second
exits). Expected job lists are checked in; a change to them is a reviewed diff.

## 7. Worker launch (`$KY_FLEET/kyjob.sh <job_id>`) (KR-05)

```
# all values from run/jobs/<job_id>/state.json; every path absolute
env -i HOME="$HOME" PATH="$KY_ROOT/bin:<node bin>:/opt/homebrew/bin:/usr/bin:/bin" \
  LANG=en_US.UTF-8 TERM=dumb USER="$USER" TMPDIR="$KY_SCRATCH/tmp/$JOB_ID" \
  ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \
  KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \
  SE_EPHE_PATH="$SE_EPHE_PATH" SWE_EPHE_PATH="$SWE_EPHE_PATH" \
  claude -p --bare --permission-mode bypassPermissions \
    --model "$MODEL" --effort high --max-turns "$MAX_TURNS" \
    --strict-mcp-config --mcp-config "$KY_FLEET/mcp.$MCP_PROFILE.json" \
    $DISALLOWED \
    --output-format stream-json --verbose --add-dir "$KY_ROOT" \
    < "$KY_RUN/jobs/$JOB_ID/prompt.md" > "$KY_RUN/jobs/$JOB_ID/stream.jsonl"
```
- `kyjob.sh` refuses (exit 78) if any of `DATABASE_URL|*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY`
  is set in its own environment; it never forwards them. `no_wrappers` behaviour of the
  current `lane_env` is preserved (tested).
- `MCP_PROFILE` is `none` (empty server list) unless the packet declares
  `needs_chart_data: true` → `marsys-only`.
- **CLAUDE.md under `--bare` is unknown** (not verified). The card therefore restates
  the binding rules (§N.2 freeze STOP, §N.3 idempotency, §N.4 tiers via
  `verification_vocab`, §N.8, B.10 no fabricated values) in ≤ 300 tokens, and B-3's dry
  run includes a fixture job that reports whether the project CLAUDE.md is in context;
  the result is recorded in the install receipt and the card is adjusted once.
- **Verifier boundary:** `--disallowedTools "Edit,Write,NotebookEdit"` plus the worktree's
  tracked files made read-only (`chmod -R a-w` on tracked paths; `run/` evidence dir and
  the slot DB writable); after the job `git status --porcelain` must be empty and the
  tracked-file hash set unchanged, else the verdict is voided and the job marked
  `boundary_violation`. Tested with a fixture that tries `sed -i`.
- Turn caps: BUILD 150, REWORK 100, VERIFY 60, POST-DEPLOY 40, RULING 30, PLAN 300.
- Session persistence stays on (transcripts are reconciliation evidence, §13).
- The prompt file = role card (≤ 1.5 k tokens) + packet (≤ 4 k tokens, §8) + job header
  (job id, slot, worktree, branch, `base_sha`, `next_migration` if allocated, loop
  number, max loops, deadline). Packets above the size cap are rejected by the PLAN
  job's own check, not discovered at launch.

## 8. Packets (KR-08, KR-10)

`00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md`, ≤ 4 k tokens, produced
by PLAN jobs or the planner, validated by `kypacket.py check` (schema + hashes + size)
before the dispatcher will launch it.

Front matter: `id, title, wave, build_tier (sonnet|opus) + routing_reason,
needs_chart_data, max_loops (3), plan_version, test_commits[] (sha + digest + path),
spec_sources[] (path, revision, section range, sha256), schema_receipt (prod_schema.sql
revision hash admitted by B-0), pw_mechanism_version, packet_sha256`.

Sections, all inline:
1. **Immutable pins** — specification document revisions and hashes; the build snapshot
   id (post-rebuild `dash_build`, `registry_revision`) from `run/RELEASE_RECEIPT.json`.
   **Not** `main_sha` and **not** a migration number: the dispatcher records `base_sha`
   at job start and allocates `next_migration` from the allocator at job start; an
   unrelated advance of main never invalidates a packet. A later L1 rebuild
   (new `dash_build`) triggers an explicit `REPIN` MODEL job that revalidates affected
   packets.
2. **Owns (floor) + allowed classes** — exact paths, plus the classes a builder may
   touch with PR disclosure: declared generated outputs, tests, exports, direct
   consumers of a changed signature. Prohibited: frozen paths (§N.2), cross-campaign
   files (Suvarṇa L0–L2 declarations), control-plane code. Touching a prohibited path
   is `ky block --detail "freeze: <path>"` → STOP for native authorization.
3. **Spec excerpt** — quoted verbatim with path, revision, section boundaries, hash;
   plus a **contract reconciliation line** from the planner: "mechanism current as of
   <date>; supersedes brief text X" (Astra found briefs still pointing protected-window
   instructions into `migrate.ts`/`deploy.yml`).
4. **Signatures / contract** — functions, tables, real columns (from the admitted
   schema receipt). A required missing column → prerequisite item, not a packet.
5. **Migration class** — `NONE | ROUTINE | NEEDS-PROTECTED-WINDOW` with the window batch
   id; the allocator supplies the number at job start.
6. **Acceptance** — test file paths and their commits (installed by the dispatcher into
   the item branch at job start, and listed in `run/tests/<ITEM>.txt`), the exact command,
   the **expected failing assertion on `base_sha`** (recorded, re-checked at job start:
   if the test already passes on base, the job stops with `block: test_not_red`), named
   mutations, compat checks, and `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`. For
   unbuilt features the packet claims only "red on base"; "green" is observed by the
   job, never asserted by the packet.
7. **Evidence template** — `run/jobs/<job_id>/inspection.json` keys; readback request
   template for `writes_data`.
8. **PR template** — title (`[PROTECTED-WINDOW]` prefix when required), body sections
   (what, tests, side-files disclosure, migration number), then
   `ky review <ID> --detail "PR #<n> @ <40-hex head>"`.
9. **Do-not list** — no ledger PRs, no control-plane edits, no rebase/force-push, merge
   `origin/main` only when DIRTY and only outside generated files (else REGEN), one PR
   per item, no credential reads, no production access.

Verifier packet = the same file + `gh pr diff` + gate outputs + the item's test results.

## 9. Routing and escalation (KR-10)

`kyroute.py` normalises every `owns`/`shared` entry and every diff path to
**repository-relative** paths; prose entries ("one additive migration", "workflow
edit") are resolved by the planner into paths or **conservatively routed to Opus**.

Opus is forced by any of: a migration file or `migration_class ≠ NONE`; any path under
`platform/python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
`platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**`,
`platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py`, `**/*ephemeris*`,
`platform/scripts/temporal/**`, `platform/scripts/migrate.ts`, `platform/migrations/**`,
`src/proxy.ts`, `src/lib/{auth,security,share,limits,mcp}/**`, `src/app/api/{auth,admin,db}/**`,
`.github/workflows/**`, `infra/**`, `platform/scripts/governance/**`, control-plane
paths (`00_ARCHITECTURE/briefs/kalayantra/fleet/**`, `pravaha_tracker/**`); any diff
line touching `'lit'` state or writing `verification_pass_status`; an import of
`swisseph`/`jhora`. **FROZEN orchestrator files** (ORCHESTRATOR_CONVERGENCE_CLOSE §2
list) are not routed at all: a packet or diff touching them is STOP → native (§N.2).
Routing runs on the packet (pre-launch) and **again on the actual diff** (pre-VERIFY):
a Sonnet-built diff that hits an Opus rule is discarded and re-queued as an Opus BUILD.
Fixtures: KA-1e (sky paths), K1-2 and K6-4 (migrations in prose) must route to Opus.

Escalation: Sonnet job red after `max_loops` → Opus REWORK; one REJECTED verdict on a
Sonnet head → Opus REWORK; Opus REJECTED twice → `ky block` → conductor → RULING or
PLAN (repacket). Escalation grants no authority.

## 10. Release gate (KR-07) and the N-467 stop (§15.D-3)

`$KY_FLEET/kygate.sh` validates **one versioned release receipt**
`run/RELEASE_RECEIPT.json` (producer: Strategic Suvarṇa or the owner; schema in
`fleet/schemas/release_receipt.json`), and prints one line per condition with the
evidence it checked; any missing field is `WAIT`, never inferred:

1. `certification_done`: coordination commit sha + `campaign-coordination` §6 line id;
   `run/HOLD_MERGES` absent; **and** `run/OWNER_RESUME.json` exists with
   `{stop_ref: "N-467", resumed_by, session_id, ts}` — written by the conductor's first
   action when the owner pastes the CONDUCTOR prompt (owner decision D-3).
2. `pins`: `dash_build`, `registry_revision`, their producer and provenance (rebuild run
   id). The gate **admits** them; `J-4p` (re-pin) is then the **first job after the
   gate**, not a precondition of it.
3. `regeneration`: commit sha of the regenerated generated files on main, and the
   hash of a clean re-run in an isolated checkout at that commit (B-1's `kyregen.sh --check`).
4. `pr_dispositions`: exhaustive list (paginated `gh pr list`) of `suvarna/*` and
   `pravaha/*` PRs with `{merged|parked|closed, owner, re_entry}`; label absence is not
   evidence.
5. `coordinators_closed`: SS's enumerated session hand-off records (session ids,
   hand-off note paths). **No authoritative source exists today** → this line reads WAIT
   until SS publishes it in the receipt; a process-observed shutdown is reported
   separately and does not satisfy it.

Negative fixtures: each condition has a receipt that must yield WAIT. STOP and `$KY_ROOT/HOLD`
dominate the gate; the bootstrap exemption applies only to conditions 1–5, never to
STOP/HOLD/HOLD_MERGES.

## 11. Conductor (KR-11, KR-12) — see the paired prompt

- Instance lock `run/conductor.lock` (session id, pid, started_at); a second conductor
  refuses.
- Start-up validates `run/VERSIONS.json` (`kyversion.sh`), reads **only**
  `run/HANDOFF_CONDUCTOR_latest.md`, the gate, `ky status`, `kyreport.py --today`.
- First action in a session after the gate: write `run/OWNER_RESUME.json` (D-3) and
  `ky note --detail "owner resume N-467 by paste; session <id>"`.
- Waits with `ky inbox --stream S --wait 540 --json` (the harness caps one tool call at
  600 s; the call returns immediately on any unacked message, so every handled message
  is acked, and deferred ones are recorded in `run/CONDUCTOR_STATE.json` and acked too).
  Also reconciles the steward inbox (`ky inbox --steward --json`) at start-up and every
  10th wake-up.
- Interventions use the steward override:
  `ky unblock "$ITEM" --as steward --detail "$REASON"`,
  `ky park "$ITEM" --as steward --detail "$REASON; re-entry: $CONDITION"`.
  Owner chat commands are handled directly from chat, never presumed to arrive via `ky`.
- Counters persisted externally: `run/CONDUCTOR_STATE.json {wakeups, started_at,
  session_id}`; hand-off at 60 wake-ups or 8 h or `handoff` or a harness context
  warning; writes `run/HANDOFF_CONDUCTOR_<ts>.md` and updates `_latest`.
- Never builds, verifies, merges by hand, edits control-plane code, rebases, reads
  credentials, or starts a worker itself.

## 12. Finalizer v3 (KR-11)

`finalize.sh` rewritten: `touch run/STOP_dispatcher` → wait for the dispatcher to exit
→ for every job in `JOBS.jsonl` with state live: assert the recorded process group is
gone → remove owned item worktrees (pushed or archived first) → drop slot DBs → verify
absence independently (`git worktree list`, `docker exec ky-pg psql -l`, `pgrep -f
"claude -p"` filtered to recorded session ids) → C-3 and C-4 completed with
`ky done C-3 --artifact-path run/FINAL_REVIEW.json` / `ky done C-4 --artifact-path
run/FINAL_RECEIPT.json`, each artifact digest-bound and ACCEPTED by an ARTIFACT job
from a different slot than its author. Fixture: a surviving recorded process or an
unremoved assigned worktree must prevent ACCEPTED.

## 13. Measurement (KR-12; owner: no caps)

`$KY_FLEET/kyreport.py --today|--since` and `scripts/token_economy/token_baseline.py --jobs`:
- **One row per job** keyed by `job_id` ↔ `session_id`: `result` event usage is
  primary; the transcript reconciles a missing result (killed job); coverage gaps are
  reported as **unknown**, never zero. No double counting of transcript + result.
- Campaign totals include planner, conductor, their subagents, failed and escalated
  jobs, and bootstrap.
- Reported separately: guarded completions (plain count and %), accepted heads,
  weighted progress; jobs with no tracker transition (`no_progress_jobs`), repeated
  identical failures (bounded: the third identical failure blocks the item); escalation
  count; rejection rate; CI-infra retries; lead time claim→done p50/p90; four-class
  tokens by role, by kind and per guarded completion.
- Baselines: v2 campaign = 3,946 cycles, 20 engine items, 316.8 M footer / 3.13 B gross
  (Codex); the audit's "64 % addressable" is an **upper bound**, not a forecast. Tokens
  per accepted item under v3 are reported only after comparable jobs exist.

## 14. Waves

**Wave B — bootstrap (during the hold; control-plane changes permitted per D-1; each
packet independently reviewed; the owner merges; nothing installed before merge).**

| id | work | by | acceptance (detector) |
|---|---|---|---|
| B-0 | **Reconcile the model**: commit the live `plan_model.json` + `KARAKA.md` edits from the detached mirror; add packet fields; compute the transitive closure of (i)–(iv); write triage (a/b/c) and PRIORITY into the model; regenerate readiness and close joins; retire cancelled items by decision; migrate `streams[].worktrees[]`, detector and executor paths to §5; admit the schema receipt (prod_schema.sql hash); **worktree capacity inventory and dispositions** | planner (MODEL) + Opus | model validator green; semantic state identical at a fixed EVENTS boundary (same `done`/`ready` sets); closure and triage files checked in; capacity ≤ 15 after dispositions |
| B-1 | **Implement**: `kydispatch.py`, `kyjob.sh`, `kyverdicts.py`, `kyroute.py`, `kypacket.py`, `kygate.sh` + receipt schema, `kyregen.sh`, `kyreport.py` + baseline `--jobs` reader, `kyversion.sh`, repository `local_db.sh` (registry seed) adopted, `preflight.sh` v3 (slots, Claude smoke), `finalize.sh` v3, `ky`/`kybrief` wrappers re-pointed | Opus bootstrap jobs (one packet each, with tests) | fixture tests per §6/§7/§9/§10/§12; expected job lists checked in; verifier-boundary fixture; routing fixtures KA-1e/K1-2/K6-4; `no_wrappers` and exit-78 tests |
| B-2 | **Review + merge + install**: independent review of each B-1 PR in a separate session; owner merges; `install.sh` copies merged `fleet/` → `$KY_FLEET`, installs the tracker package, writes `run/INSTALL_RECEIPT.json` with sha256 of every installed file and the merge commit; creates `kalayantra/campaign` checkout | Opus job + owner | receipt hashes equal the merged tree; `preflight.sh launch` green |
| B-3 | **Isolated dry run**: fixture model + fixture EVENTS root (`PRAVAHA_EVENTS` override), item `B3-TEST` (docs-only), mock merge submission (`--mock-merge`), real `kyjob.sh` with Sonnet + Opus; includes the CLAUDE.md-visibility fixture and the verifier `sed -i` fixture | dispatcher + 2 jobs | `JOBS.jsonl` shows BUILD + VERIFY with usage; verdict recorded in the fixture root; **zero** live EVENTS writes, zero PR/queue entries, zero production requests |
| B-4 | **Cards + packets**: KARAKA, PARIKSAKA, ADHIKARIN, BOOTSTRAP cards (≤ 1.5 k each) with `COVERAGE.md` (every MUST of charter §0 + §N + learned rules → card line) and ADHIKĀRIN/native sign-off as an ARTIFACT job by a different slot; packets + tests-first for Wave 0 and Wave 1, `kypacket.py check` green | planner | sign-off verdict recorded; packets validated; tests red on their base |
| B-5 | **Governance backfill**: CURRENT_STATE §2 banner + SESSION_LOG entry (C-2 style) stating the Claude relaunch, versions and hashes; the campaign handshake updated from Codex to Claude; `run/VERSIONS.json` | planner | `schema_validator.py` green; `kyversion.sh` green |

**Wave 0 — after the gate.** `J-4p` (re-pin to the admitted pins) first. Then the 11
ACCEPTED PRs in dependency order, VERIFY only where the head moved by non-merge-only
commits: K4-2a #3379 [PW] → K4-2aw #3385 → K4-2b #3390 → K4-3 #3393 → K6-5a #3399 [PW]
→ K6-5 #3402 → K6-123 #3404 [PW]; K7-1a #3333 (REGEN) → K7-1b #3335 → K7-2 #3336;
K-CERT-2 #3426 in the Suvarṇa window per N-450. Protected migrations 1351–1356 (+1362
if still unapplied) in **one** window, one owner approval. Retire #3283, #3275 (by
decision), refresh-or-close #3272, repacket K7-3 (#3337).

**Wave 1 — the computed critical path**, in dependency order from B-0's closure
(J-0c/J-0d/J-0m precede KA-3a/3b; J-5s precedes K3-2; owed steps of K3-1 and L0-M;
KA-4b; K7-3/K7-4; the K5/VC/K6-4/K8-REG/K9/KR members of the closure; any schema
prerequisites created by the rule in §0). DB-touching items batched into ≤ 2 windows.

**Wave 2 — Gochara 5.0 sealing prerequisites and Pravāha disposition** (`J0_DISPOSITION`
re-issued as an ARTIFACT-reviewed packet; the 37 inherited PRs merged/parked/closed by
decision; remaining J sealing items in the closure).

**Wave 3 — certification mappings and close**: K-CERT re-packeted against the admitted
schema (after Suvarṇa's tier-column decision, KYD-150), V-track exits as deterministic
checks or ARTIFACT jobs, N decisions, JOIN-ALL, C-1..C-4 via `finalize.sh` v3,
SESSION_CLOSE validated.

## 15. Owner decisions (recorded) and the three calls taken on the owner's behalf

1. Planner at xhigh. 2. 3 builders + 2 verifiers, scaling up on demand. 3. Re-scope to
the critical path (§0 rule). 4. The five-part Suvarṇa exit signal is the gate (§10).
5. No token caps or budgets. 6. ADHIKĀRIN on demand. 7. All Claude; no Codex; no local
model. 8. Launch by pasting a prompt into an interactive Antigravity session.

Calls taken on the owner's behalf (2026-10-11, per the owner's instruction):
- **D-1 Control plane in Wave B: YES**, scoped per bootstrap packet, independently
  reviewed, owner-merged, installed only via `install.sh` with a hash-bound receipt.
  Campaign builders keep the prohibition. Rationale: the event-driven design cannot
  exist without replacing the lane supervisor; the risk is bounded by review + receipt.
- **D-2 Rework: YES as v2.0 from scratch** (this document), then Astra's second review.
- **D-3 N-467 stop:** the owner's act of pasting the CONDUCTOR prompt **is** the resume;
  the conductor records `run/OWNER_RESUME.json` as its first action and the gate
  checks it. No separate ceremony. Rationale: one unambiguous owner act, machine-checkable.

## 16. Owner steps (the only two pastes)

1. Now, during the hold: new Antigravity session in
   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan` (this checkout,
   at the approved commit), Opus 5.5 / xhigh → paste **KALAYANTRA_V3_PLANNING_PROMPT_v2_0.md**.
   It performs Wave B; you merge its PRs when their independent reviews are green.
2. After `kygate.sh` shows five OK: new Antigravity session in
   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, Opus 5.5 / high →
   paste **KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_0.md**. Your paste is the N-467 resume.
   Restart with the same prompt whenever it posts a hand-off.

## 17. Astra KR-01…KR-12 closure map

| finding | closed by |
|---|---|
| KR-01 planning entrypoint | §16.1 (start in this checkout at the approved commit), §5 campaign checkout created in B-2 with upstream; planning prompt pins the audit path/commit |
| KR-02 bootstrap authority | §15 D-1, §3, §14 Wave B sequencing (implement → review → owner merge → install receipt → isolated dry run), BOOTSTRAP card, B-3 fixture roots and mock merge |
| KR-03 re-scope / DAG | §0 scope rule (closure first; missing column → prerequisite; decisions for retirement; joins regenerated), B-0, Wave 1 ordering |
| KR-04 dispatcher lifecycle | §6 (all job kinds incl. MODEL/ARTIFACT/OPERATION/COMPLETE; claim ownership; job locks; reap-then-release; recovery; fixtures) |
| KR-05 paths / lean launch | §5 absolute paths, §7 launcher (env scrub, exit 78, TMPDIR, strict MCP with explicit profiles, CLAUDE.md unknown handled, verifier boundary enforced and tested) |
| KR-06 runtime migration | §5 slots + capacity inventory, repository `local_db.sh` with registry seed and bound hashes, negative 1320 fixture, preflight v3 from slots, B-0/B-1/B-2 |
| KR-07 gate / N-467 | §10 release receipt with producers and negative fixtures; condition 5 WAIT until sourced; STOP/HOLD precedence; J-4p after the gate; D-3 resume record |
| KR-08 packets | §8 (immutable pins vs base/allocator; test commits installed by the dispatcher; red-on-base check; allowed classes; contract reconciliation line; size cap) |
| KR-09 verdicts / regen | §6 VERIFY/REGEN/POST-DEPLOY (evidence fingerprint; re-review on evidence change; CI classification; diff-of-diffs inheritance; pinned generator; hashes) |
| KR-10 routing | §9 (repo-relative normalisation; metadata rules; prose → Opus; freeze = STOP; fixtures KA-1e/K1-2/K6-4; routing re-run on the diff) |
| KR-11 conductor / finalizer | §11 (lock, steward override, inbox reconciliation, counters) and §12 (finalizer v3 with independent absence checks and typed C-3/C-4) |
| KR-12 measurement / versions | §13 (job↔session join; unknown ≠ zero; corrected 31.1 %/37.6 %; "~4 of 27"), `kyversion.sh` hash pairing, LIVENESS script-only, own-handoff-only reads |

## 18. Risks
- One subscription for everything; headroom unreadable → backoff-and-report; one
  conductor; the owner checks usage at two fixed times a day.
- Sonnet on L3 logic → routing, tests-first, Opus verifier, escalation.
- A dispatcher bug stalls the campaign → fixtures per transition, `--dry` compare in CI,
  LIVENESS, the conductor's digest shows `no_progress_jobs`.
- Suvarṇa slips → Wave B proceeds; the gate waits for the receipt, not the date.
- Scope discipline → the closure is computed and committed; additions need a MODEL job.

## Changelog
- v2.0 (2026-10-11): rebuilt from scratch after Astra review v1.0; essential-governance
  cut list; full dispatcher lifecycle; release receipt gate; packet pin separation;
  routing normalisation; finalizer v3; measurement rules; three owner-delegated calls.
- v1.0 (2026-10-11): withdrawn.
