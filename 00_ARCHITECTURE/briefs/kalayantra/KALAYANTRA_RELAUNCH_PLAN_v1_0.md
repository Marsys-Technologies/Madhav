---
artifact: KALAYANTRA_RELAUNCH_PLAN_v1_0.md
status: DRAFT — for native approval; supersedes the operating model of CHARTER v1.2 §3/§5/§11 and the VELOCITY AMENDMENT v2.0 §2–§4 once approved; the charter's goal (§0), the five hash-pinned plan documents, and the tracker rules stay in force
version: 1.0
authored_by: Claude Code (Fable 5.1), token-economy audit session, worktree kalayantra/relaunch-plan
authored_on: 2026-10-11
audience: native (approver); the planning session (KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md); the conductor session (KALAYANTRA_V3_CONDUCTOR_PROMPT_v1_0.md); the KĀLA-YANTRA and Suvarṇa conductors
paired_prompts:
  - KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md   # builds packets, tests, cards, bootstrap PRs
  - KALAYANTRA_V3_CONDUCTOR_PROMPT_v1_0.md  # runs the campaign from the owner's interactive session
pairing_rule: any change to this plan bumps its version and regenerates both prompts to the same version; a prompt that cites a different plan version refuses to run
strategy: KALAYANTRA_RELAUNCH_STRATEGY_v1_0.md
evidence: 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md; scratch notes_ky_state.md, notes_suvarna_state.md, KY_MECHANICS_CATALOGUE.md (2026-10-11)
owner_decisions_2026-10-11:
  - all Claude, no Codex, no local model
  - planner Opus 5.5 xhigh; conductor, ADHIKĀRIN, verifier, escalation builder Opus 5.5 high; builders Sonnet 5.5 high
  - 3 builders + 2 verifiers standing; scale up on demand when there is work
  - re-scope to the critical path; defer the rest; disposition inherited Pravāha material
  - the five-part Suvarṇa exit gate is the launch gate
  - no token caps or budgets (usage is measured and reported; the dispatcher pauses only when the subscription itself refuses a request)
  - ADHIKĀRIN is an on-demand job, not a standing lane
---

# KĀLA-YANTRA v3 — relaunch plan (Claude, event-driven)

## 0. Goal and definition of done (unchanged)

Build the Kāla layer as one engine per PLAN v1.1 §9 / ALGO v1.1 (21 cards), absorb
Gochara 5.0 to its "5.0" flip, rebuild and serve the layer for chart `482012f1`, ship
certification mappings, close with a validated SESSION_CLOSE and a finalizer receipt
(CHARTER §0). Suvarṇa certifies the Kāla assets afterwards (charter v1.2 line 49).

**Re-scope rule (owner-approved).** The remaining 102 items are triaged by the
planning session into **(a) critical path** — required for "Kāla serves `482012f1`
end-to-end with certification mappings"; **(b) deferrable** — parked with a reason
and a re-entry condition; **(c) inherited Pravāha material** — dispositioned
(merge / park / close), never rebuilt. Only (a) is scheduled. Partial failure closes
as `CLOSED-PARTIAL` with the (b) list attached.

## 1. What changes, and why (one line each, evidence in the audit)

| v2 (as run 10-06 → 10-10) | v3 | evidence |
|---|---|---|
| 13 polling lanes, 57 % idle, 3,946 cycles for 20 engine items | **jobs**: a worker starts only for a named job and exits | F-3; notes_ky_state §3.1 |
| Codex lanes + a mid-launch CLI swap; Claude conductor hand-over | **all Claude** from the outset | owner decision |
| conductor "runs in a continuous loop, visibly, do not stop" | **thin conductor**, woken by messages, hand-off bounded | F-1; INTERACTIVE_CONDUCTOR_PROMPT v1.0 |
| ADHIKĀRIN standing lane, 75 % idle | **on-demand ruling job** | notes_ky_state §3 |
| briefs are pointers into 115 KB + 84 KB docs; 14 commands before the first edit | **packets** with pins, excerpts, signatures, tests-first | F-5; VERDICTS classes |
| 74/180 verdicts rejected, 29 duplicates, whole-file reading | **diff + packet + gate output**, one verdict per head, enforced by the dispatcher | §4 catalogue |
| one-shot protected-window PRs each waiting on a human grant (K0a-3: 42 h) | **batched windows**, one grant each | notes_ky_state §3.5 |
| generated-file conflicts hand-merged; 88 conflict cycles | **regenerate-on-conflict** script job | F-6 |
| no token metering of lanes | **per-job four-class metering** in `run/JOBS.jsonl`; daily report | F-10 |
| lanes at `/Users/Dev/kalayantra/wt/<lane>`; mirror detached with uncommitted edits | **per-branch worktrees under the policy root**; mirror tracks `origin/main` | catalogue §6 |

## 2. Launch gate — the Suvarṇa exit signal (owner-approved)

`fleet/kygate.sh` prints five lines, each `OK`/`WAIT` with evidence; the dispatcher
starts **no build or verify job** until all five read `OK` (bootstrap jobs are exempt):

1. `certification-done` posted by Strategic Suvarṇa and `run/HOLD_MERGES` removed.
2. Post-rebuild L1 pins published once in `run/PINS.json` (`main_sha`, `dash_build`,
   `registry_revision`, `next_migration`); Kāla re-pins once (J-4p) and never chases.
3. Generated files regenerated on `main` by script (census, writer digests) — verified
   by a clean `regen` run producing no diff.
4. Suvarṇa/Pravāha PR sweep complete: every open `suvarna/*` and `pravaha/*` PR is
   merged, parked with a written disposition and owner, or closed (`gh pr list` shows
   zero without a disposition label).
5. The long-lived Suvarṇa coordinator sessions have posted hand-off notes and are no
   longer acting as conductors (Suvarṇa confirms on `campaign-coordination` §6).

The gate is a signal, not a date. 13 Oct is Suvarṇa's target.

## 3. Roster (owner-approved)

| role | model / effort | mode | launched by |
|---|---|---|---|
| Planner / packet author | Opus 5.5 **xhigh** | interactive session (one-time plan build; per-wave refresh) | owner, PLANNING prompt |
| SŪTRADHĀRA (conductor) | Opus 5.5 high | interactive session, event-woken, hand-off bounded | owner, CONDUCTOR prompt |
| PRAHARĪ (dispatcher) | script, no model | background loop, 60 s tick | conductor (owner approves the start command) |
| KĀRAKA (builder) | Sonnet 5.5 high | headless job per item | dispatcher |
| KĀRAKA-escalated | Opus 5.5 high | headless job | dispatcher (escalation rule §6) |
| PARĪKṢAKA (verifier) | Opus 5.5 high | headless job per PR head; read-only tools | dispatcher |
| ADHIKĀRIN (rulings) | Opus 5.5 high | headless job on demand | dispatcher (ruling request) |
| LEKHAKA | none — digest and ledger compiled by `kyreport.py` | — | — |

**Capacity:** `KY_BUILDERS_MIN=3`, `KY_BUILDERS_MAX=6`, `KY_VERIFIERS_MIN=2`,
`KY_VERIFIERS_MAX=4`. The dispatcher runs `min(max, ready-and-unclaimed)` builders and
`min(max, review-queue)` verifiers. No token cap or budget (owner decision). The
dispatcher pauses 30 min only on a rate-limit error from the subscription (existing
`KY_QUOTA_BACKOFF` behaviour) and reports the event.

**Frontier-by-rule (always Opus):** Gaṇita computation core, migrations, FROZEN
orchestrator files, any diff touching `'lit'` or `verification_pass_status`,
security/auth, governance detectors, control-plane code (dispatcher, tracker, fleet
scripts). Globs: TOKEN_ECONOMY_AUDIT_v1_0.md §7.

## 4. Mechanics

### 4.1 Homes and worktrees
- Fleet home stays `/Users/Dev/kalayantra` (`$KY`): tracker, `run/`, `logs/`, `bin/`.
- **Campaign mirror** moves to `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`,
  a worktree tracking `origin/main`, fast-forwarded by the dispatcher each tick. The
  current mirror's uncommitted `plan_model.json` and `KARAKA.md` edits are committed
  to main first (B3-1).
- **Per-branch work worktrees** under the policy root:
  `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item-id-lower>/`, created
  by the dispatcher at claim, shared by the builder and verifier jobs of that branch
  (one copy per branch), removed after merge or close. Hard ceiling 15 per tool;
  the dispatcher counts before creating.
- Lane DBs become **slot DBs**: `ky_b1..b6`, `ky_v1..v4` on `ky-pg:55433`, reset per
  job via `local_db.sh reset <slot>`.
- Variables to change for the move: catalogue §6 list (`WT`, `CAMP`, `REPO`, `ROOT`,
  `GIT`, `PRAVAHA_PLAN_MODEL`, `PRAVAHA_REPO`, `streams[].worktrees[]`, prompt paths).

### 4.2 Dispatcher (`fleet/kydispatch.py`, deterministic, tested)
Tick every 60 s; `--dry` prints the job list without launching. Each tick:
1. Refresh the mirror (`git fetch` + fast-forward); honour `$KY/HOLD` (no launches),
   `run/STOP_dispatcher`, `run/HOLD_MERGES` (no merge queueing), `run/HOLD_GENERATED`.
2. Gate check (§2) — if any `WAIT`, only bootstrap jobs run.
3. Compute jobs, in this priority:
   - **RULING** — unread `ky inbox --stream N` or a requested `D-*` → ADHIKĀRIN job.
   - **POST-DEPLOY** — merged `writes_data` items with a successful `Deploy to Cloud
     Run` run and no `post_deploy` verdict → verifier job.
   - **VERIFY** — items in `review` whose PR head has no verdict at that head (EVENTS
     parse) and whose required checks are green → verifier job. Failed checks →
     REWORK instead.
   - **REWORK** — PR with a `REJECTED` verdict at head, or red required checks →
     builder job (`step: rework`, loop counter +1; escalation per §6).
   - **REGEN** — PR `DIRTY`/`CONFLICTING` → script job `regen-and-merge-main.sh`
     (regenerates census/digests, merges `origin/main`, pushes); if the script cannot
     resolve → builder job `resolve-conflict`.
   - **BUILD** — `ky next --stream K --json` ready items, minus active claims
     (`run/claims/*.json` unexpired), minus items with an open PR, ordered by
     `run/PRIORITY.txt` (wave order maintained by the conductor) → builder job.
   - **MERGE** — accepted heads with green checks and no hold → `gh pr merge --auto`
     (the existing `sweep.py` logic, folded in).
4. Launch up to the capacity in §3; one job per item; record `run/JOBS.jsonl`.
5. Renew the claim of every live job every 20 min (`ky renew` as the job's slot); mark
   a job dead on timeout (`KY_MAX_JOB_SECS`, builder 10,800 s / verifier 3,600 s /
   ruling 1,800 s) and release its claim.
6. On a job's `result` event: parse four-class usage into `JOBS.jsonl`; on a
   rate-limit error set `KY_QUOTA_BACKOFF`; on `rc≠0` without a tracker transition,
   `ky send --to S` an escalation.
7. Message the conductor (`ky send --to S`) **only** on: escalation, `ky block/park`,
   verdict reversal, gate change, wave complete, quota backoff, dispatcher error.
   Everything routine is logged, not messaged.

### 4.3 Worker launch (`fleet/kyjob.sh <kind> <item> <slot>`)
```
cd <worktree>; export KY_STREAM=<K|V|N> KY_LANE=<slot> KY_ROOT=$KY PATH=$KY/bin:$PATH
claude -p --bare --permission-mode bypassPermissions \
  --model <sonnet|opus> --effort high --max-turns <builder 150 | verifier 60 | ruling 30> \
  [--disallowedTools "Edit,Write,NotebookEdit"   # verifier and ruling jobs] \
  --output-format stream-json --verbose --add-dir $KY < run/jobs/<job_id>.prompt.md
```
- The job prompt = role card (≤ 1.5 k tokens) + the item **packet** (§5) + the job
  header (job id, slot, worktree, branch, head, pins, loop number, max loops).
- `--bare` skips hooks, LSP, plugins and extra settings; no MCP servers unless the
  packet declares `needs_chart_data: true` (then `--strict-mcp-config --mcp-config
  fleet/mcp.marsys-only.json`).
- Session persistence stays **on** so the corrected baseline meter can read worker
  transcripts; the `result` event is the authoritative per-job usage.
- Environment is the existing `env -i` allow-list (no `DATABASE_URL`, refuse on
  exit 78).

### 4.4 Conductor (interactive; prompt paired to this plan)
- Starts by reading this plan, the latest `run/HANDOFF_*.md`, `ky status`, `kygate.sh`,
  `kyreport.py --today`.
- Ensures the dispatcher runs (`nohup fleet/kydispatch.py >> run/dispatcher.log &`,
  pid in `run/dispatcher.pid`) — the owner approves this command once per session.
- Waits with **one blocking tool call**: `ky inbox --stream S --wait 1200 --json`
  (a 3-second poll inside a single tool call; no model turns while idle).
- On each message: decide, act (`run/PRIORITY.txt`, holds, `ky send` replies,
  `ky unblock/park`, request a ruling, scale `KY_BUILDERS_MAX`), `ky ack`, one-line log.
- Never builds, verifies, merges by hand, edits fleet/tracker code, rebases, or
  reads a credential.
- **Hand-off** when any holds: 40 wake-ups since start, 8 h elapsed, the owner types
  `handoff`, or the harness warns about context. Writes `run/HANDOFF_<ts>.md` (≤ 5 k:
  state, open escalations, priority list, decisions taken, next steps), posts it to
  the owner, stops. The owner restarts with the same prompt.
- Digest on `status` or at hand-off: ≤ 15 lines from `kyreport.py`.

## 5. Packet format (`00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md`)

Front matter: `id, title, wave, build_tier (sonnet|opus), needs_chart_data,
max_loops (3), plan_version, packet_sha256_of_sources`.

Sections, all inline (no "see §x" without the quoted text):
1. **Pins** — copied from `run/PINS.json` at packet time (`main_sha`, `dash_build`,
   `registry_revision`, `next_migration`); the builder verifies them first and stops
   if they moved.
2. **Owns (floor) + allowed side-files** — exact paths/globs; anything else is a
   `ky block` with detail, not an edit.
3. **Spec excerpt** — the PLAN/ALGO/ruling text quoted verbatim with its anchor and
   source sha256 (planner-generated; a mismatch at job time fails the job).
4. **Signatures / contract** — functions, tables, real column names (never invented;
   `contract` from the model item).
5. **Migration class** and, if `NEEDS-PROTECTED-WINDOW`, the window batch it belongs to.
6. **Acceptance (tests first)** — test file paths already committed on the packet
   branch, the exact command, and `KY_ITEM=<ID> bash fleet/precheck.sh --item`; the
   tests must fail on `main_sha` and pass on the branch.
7. **Evidence template** — the `run/<slot>.c<job>.inspection.json` keys the verifier
   expects; for `writes_data`, the post-deploy readback request.
8. **PR template** — title (`[PROTECTED-WINDOW]` prefix where required), body sections,
   `ky review <ID> --detail "PR #n @ <head>"`.
9. **Do-not list** — no ledger PRs, no fleet/tracker edits, no rebase/force-push,
   merge `origin/main` only when DIRTY, one PR per item, no credential reads.

Verifier packet = the same file + the diff (`gh pr diff`) + the gate outputs; the card
forbids opening files outside the diff and its direct callers/callees without a
stated reason in the verdict.

## 6. Escalation and loop rules
- A builder job may run ≤ `max_loops` (3) edit→precheck loops inside its turn cap.
- Escalate to **Opus** when: the Sonnet job ends red; a verifier REJECTS; the diff
  touches a frontier-by-rule path (router re-run on the actual diff — local work is
  discarded, not patched); 2 server/context errors.
- After an Opus rejection: `ky block <ID> --detail` → conductor → ruling job if a
  charter/doctrine question, else re-packet by the planner.
- Verdict identity = (item, phase, head); the dispatcher never launches a second
  verify job for a head that has a verdict; merge-only pushes inherit (existing rule).

## 7. Waves

**Wave B — bootstrap, during the hold (planning session + Opus builders; no gate needed)**
| id | item | tier | acceptance |
|---|---|---|---|
| B3-1 | commit the live `plan_model.json` + `KARAKA.md` edits from the detached mirror to main; add packet fields (`build_tier`, `acceptance_cmd`, `max_loops`, `needs_chart_data`) | opus | model validator green; `ky status` identical before/after |
| B3-2 | `fleet/kydispatch.py` + pytest (job computation from fixture EVENTS/claims/gh JSON; priorities; capacity; gate; hold files; renewals; dead-job release) | opus | tests green; `--dry` on the frozen live tracker lists the expected jobs and launches nothing |
| B3-3 | `fleet/kyjob.sh`, `run/JOBS.jsonl` metering, `scripts/token_economy/token_baseline.py --fleet-jobs` reader, `fleet/kyreport.py` (daily report §8) | opus | fixture job round-trips usage; report renders |
| B3-4 | role cards (KARAKA, PARIKSAKA, ADHIKARIN; ≤ 1.5 k tokens each) with a MUST-coverage checklist against charter v1.2 + amendment v2.0 + learned rules | planner (xhigh) | every MUST mapped; ADHIKĀRIN/native sign-off |
| B3-5 | worktree-root migration (catalogue §6 variable list); campaign mirror as a tracking worktree; slot DBs; `fleet.env` v3; `valid_lane` → slots | opus | `preflight.sh launch` green against the new paths |
| B3-6 | `fleet/kygate.sh` (§2) and `fleet/regen-and-merge-main.sh` | opus | gate prints five lines with evidence; regen on a fixture conflict yields a clean merge |
| B3-7 | packets + tests-first for Wave 0 and Wave 1 (§5); `run/PINS.json` provisional (re-pinned at gate) | planner | each packet's tests fail on `main_sha`, pass only with the intended change where a reference exists; packet sha256 recorded |
| B3-8 | end-to-end dry run: one synthetic docs-only item `B3-TEST` through build → verify → merge-queue (merge held) with the real dispatcher | opus | `JOBS.jsonl` shows 2 jobs with usage; verdict recorded; no merge |
| B3-9 | CURRENT_STATE §2 banner + SESSION_LOG entry for KĀLA-YANTRA (C-2 backfill, owed since 10-06) | planner | schema_validator green |

**Wave 0 — land what is already verified (first jobs after the gate)**
The 11 ACCEPTED PRs, in dependency order; re-verdict only where the head moved by
non-merge commits; protected migrations 1351–1356 (+1362 if not applied by Suvarṇa)
in **one** window with one grant.
- K4-2a #3379 [PW] → K4-2aw #3385 → K4-2b #3390 → K4-3 #3393 → K6-5a #3399 [PW] →
  K6-5 #3402 → K6-123 #3404 [PW].
- K7-1a #3333 (REGEN job first) → K7-1b #3335 → K7-2 #3336.
- K-CERT-2 #3426: inside the Suvarṇa window per N-450; post-deploy verdict due.
- Retire: #3283 (ledger PR, superseded), #3275 (cancelled item; tracker set to
  `not_applicable`), #3272 (refresh as a docs packet or close), #3337 K7-3 draft →
  rework packet (KYD-125/129 pins owed).

**Wave 1 — K-track critical path to "serves 482012f1"** (planner decides membership
from the 21 unstarted K items + owed steps of K3-1 and L0-M + KA-4b + K7-3/K7-4;
candidates: K5-G1a/G1b, K5-2/2b/3, VC-1/2, K6-4, K8-REG, K9-*, KR-1/2). DB-touching
items batched into at most two protected windows for the wave.

**Wave 2 — Gochara 5.0 absorption by disposition.** Re-issue `J0_DISPOSITION` as a
packet (v1.1 was rejected 4× and never accepted); the 37 inherited `pravaha/*` PRs are
merged / parked / closed per disposition — not rebuilt; only J items on the critical
path (J-0m for KA-3a/3b, J-5s for K3-2, the flip) are scheduled.

**Wave 3 — certification mappings and close.** K-CERT re-briefed against the real
schema once Suvarṇa's tier column exists (KYD-150); V-track packet exits as
deterministic-first packets; N decisions; JOIN-ALL, C-1..C-4, `finalize.sh`,
SESSION_CLOSE validated.

## 8. Measurement and reporting (no caps; honest signals)
`fleet/kyreport.py --today|--since` prints: items done; PRs merged; jobs by kind and
outcome; rework loops and escalations; rejections / verdicts; lead time claim→done
p50/p90; four-class tokens by role and **per accepted item**; quota-backoff events;
gate status. Targets (signals, not gates): idle share ≈ 0 by construction (every job
is work; measure `jobs_without_tracker_transition` instead), rejection rate < 20 %,
lead time p50 ≤ 4 h, ≥ 8 items/day at steady state. The conductor's own usage is
read from its transcript by the baseline script; one conductor at a time.

## 9. Risks and mitigations
- **One subscription for everything** (Claude already 81 % of tokens; headroom not
  readable): backoff-and-report on refusal; the owner checks usage at two fixed
  times a day; scale-down is one env var.
- **Sonnet on L3 logic:** frontier-by-rule, tests-first, Opus verifier, escalation.
- **Dispatcher starvation bug:** decision log per tick; a liveness job per slot
  every 2 h; `--dry` compare in CI against fixtures.
- **Suvarṇa slips:** Wave B proceeds; launch waits for the gate, not the date.
- **Worktree ceiling (15):** dispatcher counts; audit worktrees are removed before
  launch.

## 10. Out of scope (recorded)
Nirmāṇa fleet revival; Codex in any role; token caps; changes to the FROZEN
orchestrator; reducing verification rigour; rebuilding Pravāha material.

## Changelog
- v1.0 (2026-10-11): initial relaunch plan incorporating the owner's six decisions.
