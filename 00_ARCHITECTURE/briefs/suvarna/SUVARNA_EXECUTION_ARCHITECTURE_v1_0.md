---
artifact: SUVARNA_EXECUTION_ARCHITECTURE
canonical_id: SUVARNA_EXECUTION_ARCHITECTURE
version: "1.5"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_CAMPAIGN_PLAN_v1_5.md (the what and when; this document is the how)
decision_owner: "Strategic Suvarṇa under N-28 (the native informed, veto at any time)"
changelog:
  - "1.5 (2026-09-30, plan set v1.5 pre-final): §2.1 folder layout with the swarm's own clone, native-owned authority/, config/, control/ and broker/ (N-35, N-36, N-37). §2.2 writes through the build broker; the global-L0 grant (N-31). §2.4 isolation decided (N-25) and rewritten: separate user, broker, bot identity, authority out of reach, residuals (Astra F2). §3.1 Steward parks to Strategic Suvarṇa; Build operator dispatches L0 through the broker. §5.1 change-triggered passes, fenced queue, merge gate. §5.4 runner stall and lane reconciliation. §5.5 durable runtime from launch, no /loop; SS decision runtime L.18 (N-34; Astra F6, F17). §6.2 merges by the swarm through the merge gate; deploy by ancestry of the squash commit. §6.4 families: Pravāha, J1.FO, cascade notification. §6.5 L0 waves without a dump (N-29, N-31); new §6.6 serving guard (N-33). §7 summary per charter v1.5 (N-28). §8 stage-aware Monitor matrix (Astra F3; CODE-38). §11 decisions log under authority/, typed decisions, detector types incl. the four new ones (CODE-44, -47, -50, -54; -54 built). §12.10 SS writes without the native present; §12.11 digest informs; §12.12 tools run from the control checkout; §12.16 semantic fingerprint and currency contract (Astra F14)."
  - "1.4.1 (2026-09-30, review pass 3 folded; REVIEW_PASS3_DISPOSITION_v1_0.md): §2.4/§5.5 the allow-list forms the documents use (single-quoted reader psql and pg_dump, governance scripts, suvarna-build), the swarm's pushes limited to suvarna/* branches, decide/decisions/runtime_settings not allowed to the swarm; the hold-guard hook runs from hq and fails closed for dispatches. §6.1 wave membership only from the J1-frozen LEVEL_MAP.json. §6.2 item 2: a level wave dispatches every non-family asset at the level and never a family asset (one run over the level's non-family assets). §8: isolation reads warn until N-25 is decided (Monitor exit 0 or 1, 1 only from isolation before N-25); builder_scope warn until E7.2 writes builder_identity.json. §11.7: scorecard generator pinned by the spec; register_rows_state deferred checks; fk_no_cascade target; levels_elevated level_map. §12.5: Suvarṇa range 1200–1299 and the deny-list amendment (N-27). §12.13/§12.15: the census_run wrapper."
  - "1.4 (2026-09-29, review pass 2 folded; REVIEW_PASS2_DISPOSITION_v1_0.md): new §2.4 isolation (PROPOSED pending N-25: separate macOS user, Suvarṇa settings file with explicit denies and the hold-guard hook, own GitHub identity, branch protection, decisions log read-only to the swarm; what launch requires either way). §2.1/§12.2 one branch rule: lanes from suvarna/trunk (synced from main every pass); PRs to main from landing branches cut from origin/main; source branches read or cherry-picked only; fold lanes before the cut-over pushed as fast-forwards to campaign/nikasha-test, read by the tracker at origin/campaign/nikasha-test (§12.7). §2.2, §8: D6 applied. §3.1, §3.3: effort sets aligned with plan §6.2. §5.5: /loop 10m, passes read snapshot.json and the event tail, lanes only through the lane launcher, settings file untracked and passed explicitly. §6.2: deployed = ancestry. §6.4: waiting_on_family shown as blocked. §6.5: L3 close is an asset-list run; L2 after F3.FK. §7: which charter version is in force. §8: every 5 minutes; builder_scope from the authenticated preflight (the reader cannot read chart_grants.permission or profiles); isolation and decision-writer checks. §11: exact ELEVATED only (E6.3t); empty specs read unknown; new detector types; FAMILY_ASSETS.json path; registry coverage via E6.5. §12.7 folds; §12.9 the measured cascade (8 keys, 7 tables); §12.10 only Strategic Suvarṇa writes decisions; §12.12 tracker and Monitor run from committed code in hq, one owner of tracker code, the hq_commit command, the mirror on hq only; §12.14 exit code 2."
  - "1.3 (2026-09-29, review pass 1 and decisions D1–D6 folded): §5.5 new runtime section (D5: interim /loop to G2, durable supervised headless pass loop, stateless passes, watchdog, rollover, allowlist). §6 families excluded from wave completion with asset-level waits (D2), L0 wave safety and full-layer rebuild (D4), waves wait for fixes merged to main and deployed. §2.2, §3.1, §8 builder identity and L0 native dispatch (D1); reader login (D6); power rule matches monitor.py. §11.7 new detector types (built by L.13). §12.2 Track E lanes branch from their source branches; §12.5 names the placeholder branch; §12.6 one review path; §12.7 ledger cut-over; §12.9 L2 MSR = the L2 writers only; §12.10 decisions log outside git behind the decide CLI; §12.12 hq commits under a lock and plan revisions merged, never fast-forward-only; §12.14 provisional censuses checked by script; §12.15 census lock; §12.16 certification record fields. Corrected: §1 (three definition replacements, t0→t3; Nirmāṇa's plan quote), §2.3 (families; migration numbers), §4.1 (plan_item), §5.4 (stall owner), §7 (charter wins; destructive needs snapshot and approval; no budget), §11.6 (credential). The 1.2 body's charter-points paragraph had changed without a bump; recorded here. Sources: REVIEW_PASS1_DISPOSITION_v1_0.md."
  - "1.2 (2026-09-29): §12 operating conventions added, settling the open questions the role-instruction draft raised (queue-to-tracker mapping, ids, one queue per session, leases on campaign-coordination, migration reservations, output paths, ledger folds before landing, stall and spend metering, the L2 MSR set, decision-log writers, digest, hq commits, census checkout). Four missing scripts assigned to Track E as J1 prerequisites (plan §5.1 E5). Three charter points left for the native."
  - "1.1 (2026-09-29): real-time visibility made a first-class requirement (native, 2026-09-28): new principle 9, new §11 (the tracker: one event log as the single source of truth, detectors decide done, live push, resilience), emit duties added to the queue life (§4.3), the conductor loop (§5.1), the Monitor (§8) and restartability (§10). The tracker is built and tested (34 tests)."
  - "1.0 (2026-09-28): first draft. Isolation, the swarm, models and effort, the work queue, the build strategy, autonomy and its limits, environment, cost control."
---

# Suvarṇa — execution architecture

How the campaign runs itself: autonomous, parallel wherever the data allows, sequential only where it must be,
and never idle.

## §1 · Design principles

1. **Only data forces order.** Work waits only for work whose output it reads. Nothing else waits.
2. **Read-only work runs wide.** Analysis never collides, so it runs across all layers at once.
3. **Walk the build chain as few times as possible.** It is the one thing parallelism cannot shorten (§6).
4. **Deterministic code before agents.** A script does the counting, folding, dispatching and checking. Agents do judgement and code.
5. **Park and continue.** A parked question (to Strategic Suvarṇa) never stalls unrelated work.
6. **Diagnose before retrying.** A second failure of the same thing becomes a diagnosis task, never a third attempt.
7. **Freeze the standard before judging against it.** Nirmāṇa replaced its definition three times (t0 → t3); most of its freezes were judged against a standard it later dropped.
8. **Every result is gated.** A fresh reviewer tries to break it before it counts.
9. **Visible the moment it happens.** Every state change is written to the event log as it happens, by the role that caused it, before that role moves on. The tracker (§11) shows it within about a second. A change that is not in the log did not happen, as far as the campaign is concerned.

### 1.1 · Lessons from Nirmāṇa, and the rule each produced

| What happened | Evidence | Rule here |
|---|---|---|
| Sessions spent turns re-checking a lock that had not moved | L2 state log: "held steady across cycles #489–#490" | Event-driven waits, no polling (§5.3) |
| One asset retried many times without a root cause | `ka_kshetra`: 19th attempt | Principle 6; retry cap (§5.4) |
| The standard changed mid-campaign | 3 superseded revisions (t0–t2); 72 of 98 freezes under t0 | Principle 7; the engine freezes first |
| Weak verification | 97 of 98 frozen assets still carry Nikaṣa gaps | Nine gates plus a gate review on everything |
| Layers frozen strictly one after another | Nirmāṇa's unified plan (v2.0) §1: "layers freeze strictly in order" | Asset-level dependency waves (§6) |

## §2 · Isolation

The campaign runs in its own folder, on its own branches, with its own switch. Other campaigns keep running.

### 2.1 · Folder

```
/Users/Dev/suvarna/                 (native-owned; the swarm traverses it)
├── .repo/            the swarm's own clone (owner suvarna), from which hq, trunk and lanes are worktrees
├── hq/               worktree, branch suvarna/hq — queues, digests, the decisions mirror (owner suvarna, group-writable)
├── trunk/            worktree, branch suvarna/trunk (main plus accepted packets; main merged in every pass)
├── lanes/<lane-id>/  one worktree per active lane, created and removed by the Conductor
├── evidence/         census outputs, build evidence, fingerprints and diffs, drill reports (not committed)
├── run/              EVENTS.jsonl, snapshot, heartbeats, spend, locks/, claims/, parks/ (swarm-writable)
├── authority/        DECISIONS.jsonl, HOLDS.jsonl (swarm may only append), HOLD_CLEARS.jsonl — native-owned (N-35, N-37)
├── config/           the Suvarṇa Claude Code settings file — native-owned, read-only to the swarm
├── control/          native-owned worktree at the pinned control release: the tracker, Monitor, hook, merge gate,
│                     gate evaluator and broker that actually run (N-37); updated only by Strategic Suvarṇa
└── broker/           builder.env — owned by _suvarnabuild, unreadable to the swarm (N-36)
```

- **Never the main checkout**, and never the native's repository: the swarm's clone is its own (`.repo`).
- **Work reaches `main` through small PRs** from landing branches `suvarna/land/<group>` cut from `origin/main`, merged by
  the swarm's identity through the merge gate (§12.2, N-38).
- **Lane worktrees are disposable.** A lane's work lives on its branch until it is merged.

### 2.2 · Database

- **Reads:** `~/.config/suvarna/pgenv.sh` of the `suvarna` user on the local proxy (§8), logging in as `suvarna_reader`,
  read-only by privilege (D6).
- **Writes:** two paths only.
  - Migrations (1200–1299), applied by the deploy pipeline after a merge, then verified read-only.
  - Builds through `POST /api/cockpit/runs` as the builder identity (D1), **only through the build broker** (N-36), which
    alone can read `builder.env`: the canonical chart's `build` grant, and the global-L0 grant for L0 asset lists (N-31);
    never `clear_before`. The server enforces the scope (E7.1).
- **No hand-written SQL against production. No privileged credentials.**

### 2.3 · Other live workstreams

- **An asset lease.** Before Suvarṇa changes an asset, it takes a lease on it on the shared campaign-coordination branch (§12.4). Before taking one, it checks whether another workstream holds that asset.
- **The L3 families:** Gochara belongs to the Pravāha campaign; Saṅgam and Kṣetra are Suvarṇa design work until J1.FO decides who implements them (plan §5.3). Suvarṇa never leases or changes a family asset (charter R8) until SS records a hand-back (HB-G, HB-S, HB-K). It certifies what they build (§6.4).
- **Migration numbers:** reserved one at a time (§12.5).

### 2.4 · Who the swarm runs as — decided (N-25; N-36, N-37)

**Why.** Claude Code merges allow rules across scopes, and allowed interpreters (`pytest`, governance scripts) run
agent-written code with the process's full filesystem authority (GPT-6 Astra F2). So the boundary must be the OS and the
server, not the allow-list.

- **A separate macOS user `suvarna`** runs every swarm process: the runners, lanes, the Monitor and the tracker
  (launchd services, NATIVE_SETUP NS.8). It cannot read the native's credential files (NS.3), `authority/` beyond
  reading, `config/` or `control/` beyond reading, or `broker/`.
- **Its own Claude Code settings**, `$SUVARNA_HOME/config/claude-settings.json` (native-owned), passed with `--settings` by
  every launch: `defaultMode: dontAsk`; allow, in exactly the forms the role documents use: the swarm's `suvarna_tracker`
  modules (`emit`, `census_run`, `hq_commit`, `lane_launch`, `monitor`, `events`, `hold --set`, `merge_gate`), never
  `decide`, `decisions`, `runtime_settings` or `hold --clear`; `bash -c 'source ~/.config/suvarna/pgenv.sh && psql …'`;
  `python3 platform/scripts/governance/<script>.py`; `pytest`; `git` with pushes only to `suvarna/*` (plus the Engine's
  fold push to `campaign/nikasha-test` before E4.3); `gh pr create`, `gh pr view`; `~/.config/suvarna/bin/suvarna-build …`
  (the broker wrapper). **Deny rules:** `gh pr merge*` (merges go through `merge_gate`), `gh api*`, force-push, pushes to
  `main`, `mcp__github__*merge*`, `mcp__postgres__*`, `gcloud*`, reading `**/.env*` and the native's credential paths,
  editing `config/**`, `control/**`, `authority/**`; the hold hook (PreToolUse, from `control/`, fail-closed on any
  malformed payload).
- **The build broker** (N-36): `sudo -n -u _suvarnabuild /opt/homebrew/bin/python3 /Users/Dev/suvarna/control/…/broker.py`,
  the one sudo rule the swarm has (NS.2). It refuses while any hold is active, validates the asset list against the frozen
  level map minus the family set (or the active L0 assets for the global grant), passes `expect_job_image_tag`, and alone
  reads `builder.env`.
- **Its own GitHub identity** `marsys-suvarna-bot` (Write on the repository only; NS.5). It merges only through the merge
  gate (N-38); `main`'s org ruleset 20141220 requires every check (with `Suvarṇa path guard`, NS.6), squashes through the
  merge queue and has no bypass actor; the bot cannot change the ruleset.
- **Authority out of reach** (N-37): the decisions log and the hold-clear ledger are writable only by the native's account
  (Strategic Suvarṇa runs as it); the hold ledger is append-only for the swarm (`uappnd`); the control code runs from a
  native-owned checkout, so the swarm cannot change the hook, Monitor or gate evaluator it is judged by.
- **Residuals** (charter §13): the swarm can read its own reader credential (read-only by privilege), its GitHub token and
  its Claude token; a PR could edit its own CI job (refused by the path guard, caught by the post-merge audit).

**Measured continuously:** the Monitor's `isolation` (as `suvarna`: the process user; the probe paths unreadable; the
secret sweep empty; the reader readable and mode 600; `authority/`, `config/`, `control/` unwritable; the settings hash)
and `decision_log_integrity` (ownership, mode, append-only prefix) checks; proved once by LG.2 and LG.4.

## §3 · The swarm

### 3.1 · Roles

| Role | What it does | Model · effort | Runs |
|---|---|---|---|
| **Conductor** | Owns the work queue. Dispatches ready work, folds results, releases dependents. Never builds, never reviews. | Opus 5.5 · medium | 1, long-running |
| **Steward** | Classifies questions against the charter (§7). Parks reserved questions to Strategic Suvarṇa, batched, with a recommendation; records no decision (charter P14); approves briefs within G16. | Opus 5.5 · high | on demand, rarely |
| **Architect** | Turns a track brief into packet specs. Designs algorithms and derivability mechanisms. | Opus 5.5 · high | a few at a time |
| **Analyst** | Read-only work: census, layer-instance drafts, asset briefs, dispositions, fix designs. | Sonnet 5 · medium | many in parallel |
| **Builder** | Code, tests, migrations for one packet. | Sonnet 5 · medium (high for writer or ledger changes) | several in parallel |
| **Gate reviewer** | Fresh, read-only, adversarial. Rules ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT. | Opus 5.5 · medium (high for writer, ledger, auth, reopen and algorithm packets) | several in parallel |
| **Build operator** | Dispatches orchestrator runs in dependency waves through `suvarna-build` (D1); dispatches L0 waves through the broker under the global grant (N-31) with the impact statement and rebuild plan; collects evidence. Mostly a script (E5.3). | Sonnet 5 · low | 1 per chart |
| **Scribe** | Folds accepted packets into the register, ledgers and state; computes tallies; rotates fingerprints; runs drift. Mostly scripts. | Sonnet 5 · low | 1 |
| **Monitor** | Environment checks (the reader's read-only by effective privilege; the builder's scope through the authenticated preflight; isolation; decision writers), heartbeat, repair, and the Conductor watchdog (§5.5). Agent stalls and spend belong to the Conductor (§12.8). | no model — a script | always on |
| **Independent reviewer** | Third-party review of plans, track briefs and rulings. | GPT-6 Astra or Kimi | at gates |

### 3.2 · Why this split

- **Opus only where judgement decides the outcome:** conducting, deciding, designing and reviewing.
- **Sonnet does the volume:** analysis and coding.
- **Scripts do the bookkeeping.** The register-tally drift was a typed number; a script would not have drifted.
- **Builders never review. Reviewers never build.** Every gate is a fresh context.

### 3.3 · Concurrency caps (starting values, tuned from measured spend; enforced by the lane launcher, CODE-42)

| Kind | Cap | Why |
|---|---|---|
| Analysts | 6 | read-only; limited by review capacity downstream |
| Builders | 4 | limited by merge conflicts on shared files |
| Gate reviewers | 3 | one per finished packet, in parallel with the next build |
| Architects | 2 | high-cost; design work is sequenced by need |
| Census (any layer) | 1 at a time, across every session, families included | concurrent runs exhausted the connection pool once; enforced by the census lock (§12.15) |
| Orchestrator builds | 1 per chart | the orchestrator enforces a per-chart database lock |

- **Effort (plan §6.2, the same set):** high for algorithm design and the Architect's derivability work, reopen
  drafting, the Steward's classifications, a Builder's writer or ledger changes, and gate reviews of writer, ledger,
  auth, reopen and algorithm packets; medium otherwise; low for mechanical roles.

## §4 · The work queue

### 4.1 · The item

Every piece of work is one line in `hq/00_ARCHITECTURE/control/suvarna/state/QUEUE.jsonl` (Exec Suvarṇa) or
`QUEUE_ENGINE.jsonl` (Nikaṣa Engine) (§12.3):

| Field | Meaning |
|---|---|
| `id`, `stage`, `lane` | identity and grouping |
| `plan_item` | the `plan_model.json` id it rolls up to (§12.1) |
| `kind` | analysis · design · build · migrate · rebuild · review · fold · decision |
| `depends_on` | queue ids that must be done first |
| `write_set` | files, tables and assets it changes (empty for read-only work) |
| `risk` | low · normal · high — sets model effort and review depth |
| `role`, `model`, `effort` | who runs it |
| `state` | ready · running · review · accepted · folded · parked · blocked |
| `evidence` | where its proof lives |

### 4.2 · When an item is ready

All four must hold:

1. every `depends_on` item is folded;
2. its `write_set` does not overlap anything running;
3. the concurrency cap for its kind has room;
4. no asset in its `write_set` is leased to another workstream.

### 4.3 · The item's life

```
ready → running → review → accepted → folded
                     │  ↘ corrections → running
                     └──→ rejected   → running (with the review attached)
blocked or parked → ready, once the condition clears
```

- **Every transition is an event.** The role that moves an item emits it at that moment (§11.3). Queue states map to tracker states: `accepted` shows as `review`; `folded` shows as `done`, and needs evidence.
- **Nothing folds without a gate verdict.**
- **Folding is a script run by the Scribe:** register row states, ledger emit (with the withholding list), tallies, fingerprints, drift check.

## §5 · The conductor never idles

### 5.1 · The loop

A pass starts only when the runner's deterministic readiness check sees actionable change: new events since the queue's
committed offset, a ready item, a decision change, a failure or a due timer (N-34). **Every pass is stateless:** it reads
the role files, its queue, the decisions log, the tracker's snapshot and the event tail, holds the queue's fenced lock for
the whole pass, emits a heartbeat with its `--session`, and ends by committing its queue and offset (§12.12).

1. Fold what finished.
2. Release its dependents.
3. Dispatch every ready item through the lane launcher, up to the caps (the launcher enforces them).
4. Land what is accepted: open landing PRs and merge them through the merge gate (N-38).
5. If nothing is ready and something is running: end the pass; the runner waits for the next change.
6. If nothing is ready and nothing is running: pull from the standing queue (§5.2).
7. If the standing queue is empty too: write the reason to state, park what is missing to Strategic Suvarṇa, end the pass.

### 5.2 · The standing queue

Useful work that never blocks anything and can always be picked up:
- analysis for layers not yet started;
- opportunity-register research;
- test-coverage gaps;
- documentation of finished work.

### 5.3 · Waiting without burning

- **No polling cycles.** The conductor waits on completion notifications and on long timers for external events (CI, deploy, a decision).
- **A timer never shorter than the thing it waits for.** A deploy that takes 15 minutes gets one check at about 15 minutes, not fifteen.

### 5.4 · Failure handling

| Situation | Response |
|---|---|
| A build fails once | retry once, unchanged |
| The same build fails twice | stop retrying; diagnosis item (Analyst, then Architect) |
| A gate rejects twice | escalate to the Steward with both reviews |
| An agent stalls (no event and no commit for 10 minutes) | the Conductor restarts it from its last commit (§12.8) |
| A runner stalls (heartbeat older than three times the maximum backoff) | the Monitor relaunches it (`launchctl kickstart`); three relaunches in an hour → a hold, parked to Strategic Suvarṇa |
| A lane dies after pushing | the next pass reconciles its claim: pushed branch → review; else failed, retry once (CODE-42) |
| Environment failure | dispatch pauses on the Monitor's stage check; the Monitor repairs what it can |

### 5.5 · Runtime (N-34; supersedes the D5 interim)

The swarm must run for weeks with nobody present, and no step may need the native (N-28). So there is **no `/loop`
interim** (it expired weekly and needed the native to re-arm it).

- **Services** (launchd daemons with `UserName suvarna`, `KeepAlive`; NATIVE_SETUP NS.8):
  `com.marsys.suvarna.tracker`, `…monitor` (checks every 5 minutes; watchdog), `…runner.engine`, `…runner.exec`. The
  runners are **idle until N-1 is decided**.
- **A runner** (`suvarna_tracker.runner --session engine|exec`, CODE-41): a cheap readiness check each tick; one
  `claude -p "<Conductor prompt>" --settings $SUVARNA_HOME/config/claude-settings.json --permission-mode dontAsk` pass
  only on actionable change; backoff 1 → 2 → 4 … 30 minutes when idle; one fenced owner per queue (a fencing token in the
  queue's state line; a pass whose token changed refuses to commit); `CLAUDE_CODE_OAUTH_TOKEN` from the swarm's token file;
  `DISABLE_AUTOUPDATER=1` (Claude Code pinned at 2.1.239); usage-limit errors recognised and waited out, never
  restart-looped.
- **Lanes:** separate processes in their own worktrees, started only by the lane launcher (atomic claim, caps, duplicate
  refusal, intent event before spawn, pid recorded; CODE-42). No in-process background subagents for lanes.
- **Watchdog:** the Monitor relaunches a stalled runner (heartbeat older than three times the maximum backoff); at most
  three an hour, then a hold.
- **Strategic Suvarṇa's decision runtime (L.18)**, a user agent of the native's account (`com.marsys.suvarna.strategic`):
  starts an SS pass on a new `decision requested` event or a gate whose prerequisites all read done; records decisions
  with their rationale; SLA under 1 hour; escalation at 24 h (digest) and 72 h (a notification to the native, information
  only). Its own settings allow `decide`, `hold --clear`, git on `strategy/suvarna-plan` and the control release, and
  reading everything; it never dispatches builds or runs lanes.
- **Cost:** a pass re-reads about 50–100 k tokens; change-triggered passes replace the fixed cadence (Astra Q17); every pass
  emits its token use (CODE-59).
- **Single point of failure:** the Mac. State is in files and git; a failure is safe (holds, idle runners), not fast.

## §6 · The build strategy — the critical path

### 6.1 · The shape of the dependency map

The 127 active assets form **27 dependency levels** (measured 2026-09-28):

| Levels | Assets | Shape |
|---|---|---|
| 0–1 | 55 | wide: mostly L0 and L1, plus 8 L3 assets |
| 2–5 | 23 | narrowing |
| 6–26 | 49 | a long thin chain, 1–5 assets per level: L2 → L3 → L4 → L5 |

- Parallelism shortens analysis and coding. It cannot shorten the chain.
- **The chain is the critical path.** Every walk of it costs the same no matter how many lanes run.
- **The map moves.** Family sessions and Suvarṇa both change `asset_registry.depends_on` (Kṣetra's edges are known to
  be wrong). So the level map is snapshotted and versioned at J1 (E6.3, `00_ARCHITECTURE/control/LEVEL_MAP.json`); wave
  ranges are derived from the snapshot and re-derived, with a plan-model update in the same commit, if a later registry
  change moves an asset. **Wave membership comes only from that frozen file**, never from the live registry: the wave
  items' `levels_elevated` detectors carry `level_map` (CODE item, review pass 3), and the level-wave script reads it. A dependency cycle
  is an error, never level 0.
- **Family positions (measured 2026-09-29):** `ka_gochara_resonance` and `ka_vedha_gochara` at level 1, `ka_gochara`
  at 5, `ka_kshetra` at 12, `ka_sangam` at 13; 16 assets read a family asset (§6.4).

### 6.2 · Therefore: fix first, walk once

1. **Fixes land before rebuilds.** All planned fixes for an asset are merged to `main` **and deployed** before it is
   rebuilt: each wave group goes to `main` as one or more PRs from landing branches, merged by the swarm through the merge
   gate into the squash merge queue (N-38); the deploy
   follows (plan items B.W0M…B.W5M). A wave's fixes are every Track I item for an asset in its level range (I.W0…I.W5),
   whatever the layer. At dispatch the level-wave script re-checks that the PR's merge (squash) commit is an **ancestor** of the running
   commit and that the writer files at that commit hash to what the packet recorded (charter §6.4), because other
   workstreams deploy to `main` too.
2. **One wave per level.** When every asset at a level has its fixes deployed and every upstream asset is certified and
   current, the Build operator dispatches one orchestrator run covering **the level's non-family assets** for the chart:
   every asset at that level in the frozen `LEVEL_MAP.json` that is not in `FAMILY_ASSETS.json`'s `family_set`, as an
   `--assets` list, never `--level`. A wave **never** dispatches a family asset or a reader (family assets sit at levels
   1, 5, 12 and 13, readers at 13; a whole-level run would rebuild family data, charter R8); the level-wave script
   refuses if its dispatch set intersects the family set. For an L0 wave
   it prepares the impact statement, rebuild plan and fingerprints and dispatches under the global grant (§6.5).
3. **Certify as the wave lands.** The inspector re-measures that level; gaps close; certifications are written, each
   carrying what it was measured against (§12.16).
4. **Front-load the wide top.** Levels 0–2 (65 assets) are rebuilt and certified as early as their fixes allow. Most downstream work then sits on certified inputs.
5. **A failure mid-chain** stops only its own downstream. Everything off that branch continues.
6. **An upstream change after certification** invalidates the downstream certifications: the stale-certification
   detector (E5.5) finds any certification whose writer hash, upstream certification ids or row-set fingerprint no
   longer match. The inspector re-measures them; a rebuild runs only if the output actually changed.

### 6.3 · Charts

- The canonical chart only, unless N-12 (ruled before the first L0 wave) adds others.
- L0 is global: one build, no chart; it changes the inputs of every chart (§6.5).
- Other charts are a later, recorded addition. Each chart walks the chain once.

### 6.4 · The L3 family assets in the waves (D2; Pravāha; J1.FO)

- **The family set and its readers** live in `00_ARCHITECTURE/control/FAMILY_ASSETS.json`, frozen at J1 (E6.3) and pinned
  by hash in every wave item (CODE-45): Gochara (the Pravāha campaign's) always; Saṅgam and Kṣetra only if J1.FO gives
  their implementation to a family session (otherwise they are ordinary Suvarṇa assets from J1 on).
- **Excluded from wave completion.** A wave completes without them; readers wait asset by asset (`waiting_on_family`)
  and are certified under B.FR.L3/L4/L5.
- **Certification.** A family asset's Build gate passes only on an orchestrator run on the canonical chart whose substep
  plan completed; Suvarṇa's re-measure writes the certification (B.FG, B.FS, B.FK). Gochara: not before the registered
  writer produces '5.0' and the century writer is retired (Pravāha A5.6, A6.2).
- **Cascades and staleness** from a granted Suvarṇa rebuild into another owner's rows are exempt from R8 and notified the
  same day on the coordination branch (charter R8; F-3 principle).
- **Saṅgam** is certified only after its L2 upstreams (B.W2); MSR rebuilds need F3.FK and F3.GUARD (N-32).

### 6.5 · L0 waves and full-layer rebuilds (N-29, N-31; supersedes D4's dump)

- **Every L0 wave** is dispatched by the builder through the broker under the global-L0 grant (N-31), with: a measured
  impact statement (L0 assets whose output changes; per other chart, the downstream closure now served from stale L0
  inputs, disclosed through the serving notice, N-33); the transitive write/delete footprint (E5.9); a rebuild plan (the
  orchestrator runs that regenerate the affected rows, proved by the E5.7 rebuild drill); pre/post semantic fingerprints
  and a row-level diff on the natural keys, retained to campaign close. **Reversal:** hold; revert the landing through the
  merge gate and rebuild. No dump.
- **Full-layer rebuild** (layer close): one `action=rebuild, clear_before=false` asset-list run over the layer's active
  assets (L3: minus the family set); for L1+ from scratch for the chart; for L0 proven by fingerprint equality or an
  explained diff; for L2 only after F3.FK and F3.GUARD.
- **L0 is four dispatches** (levels 0–3; `bg_concordance` at level 3 split out of W1): B.L0.0 … B.L0.3.

### 6.6 · The serving guard (N-33)

Served output is never wrong or partial without an authority switch or a disclosed maintenance window. For every served
table a wave writes, the mode recorded in `00_ARCHITECTURE/control/SERVING_GUARD_INVENTORY.json` (E5.8) applies:
(a) **candidate → verify → switch authority → reverse on failure** (the Pravāha pattern; L2 producer generations,
migration 1036); or (b) a **disclosed maintenance window** (a serving notice carried by the served envelope; the serving
canary of golden MCP reads for `482012f1` before and after; closed only on a passing canary). A table not in the inventory
is not written (charter §6 precondition 8).

## §7 · Autonomy and its limits

The charter (`SUVARNA_AUTONOMY_CHARTER_v1_0.md` v1.5) supersedes this summary; where they differ, the charter wins.

### 7.1 · Granted — the swarm decides alone, and logs it before acting

- Dispatch, sequence and cancel queue items; model and effort within §3.1 and the caps.
- Accept a gate verdict and fold it; retry once; open diagnosis items.
- Record `N/A` only as the census computes it from a declared registry rule (D3).
- Merge accepted packets to `suvarna/trunk`; open landing PRs and **merge them through the merge gate** (N-38).
- Dispatch orchestrator builds in dependency order through the broker, for the canonical chart and global L0 (N-31).
- Set a hold (never clear one).

### 7.2 · Reserved — park to Strategic Suvarṇa, and continue with everything else

- Everything on the plan's open decision list (plan §8.2).
- Any change to the frozen writer contract.
- Any destructive operation: a rebuild plan, a serving guard, a recorded fingerprint and an SS decision (charter R3; N-29).
- Any scope beyond the canonical chart, and any change of scope or end state (SS takes these to the native).
- Retiring an asset or changing its output beyond its brief.
- Anything the charter does not clearly grant.

### 7.3 · Prohibited — refuse, never park

Reading or logging credentials · writing production data outside migrations and the orchestrator · weakening a gate ·
closing a gap on anything but PASS or a registry N/A · committing to `main` directly or merging outside the merge gate ·
bypassing permission checks · writing the decisions log or clearing a hold · changing serving without the serving guard.

### 7.4 · Decisions without stalls (N-28)

- **Parked to Strategic Suvarṇa**, never to the native. The Steward emits `decision requested` the moment a question is
  foreseen, with a recommendation; SS's runtime answers within its SLA; only the dependants wait.
- **The native** is informed by the digest and dashboard and may veto at any time; the native acts only on the physical
  setup, credentials, scope or end-state changes and N-1.

## §8 · Environment

The Monitor (`python -m suvarna_tracker.monitor`, a service of the `suvarna` user, every 5 minutes; exit 0 ok, 1 warn,
2 block) evaluates a **stage-aware matrix** (CODE-38; Astra F3): stage **S1** (launch and analysis, no production write),
**S2** (builds), **S3** (global L0 waves). A check required at the current stage that fails **or cannot be measured**
blocks; a check not yet applicable reads `not_applicable`, never `warn`. Composite checks `stage_ready_S1`,
`stage_ready_S2`, `stage_ready_S3` are what the preconditions and the tracker read. Native paths and UIDs are pinned in the
Monitor's config, never `~`-expanded.

| Check | Stage | What |
|---|---|---|
| `db_proxy` | S1 | proxy on 5433 (repair: restart) |
| `credential` | S1 | the reader file present, mode 600, owned by `suvarna` |
| `credential_readonly` | S1 | the login is `suvarna_reader`, no write path by effective privilege (D6) |
| `isolation` | S1 | run as `suvarna`: the native's credential paths unreadable; the secret sweep empty; `authority/`, `config/`, `control/` unwritable; the builder file unreadable; settings hash as recorded |
| `decision_log_integrity` | S1 | the log and hold-clear ledger native-owned; only appended since last seen (CODE-37) |
| `decision_writers` | S1 | every `decided` line written by `strategic-suvarna` |
| `hold` | S1 | no active hold in the ledger (a hold is not an error: it stops dispatch) |
| `conductor_heartbeat` | S1 | one per session, judged by receipt (CODE-63) |
| `merge_audit` | S1 | every bot merge had its ACCEPT, green checks and a clean path guard |
| `native_setup` | S1 | `NS_VERIFY.json` all PASS and under 48 h old (re-run daily) |
| `tracker` | S1 | `/api/health` ok (repair: restart the service) |
| `disk` | S1 | room for evidence |
| `power`, `sleep_prevented` | S2 | on AC, sleep prevented; a warn fails a build precondition |
| `builder_scope` | S2 | through the broker's preflight: the builder `guest`/`active`, grants exactly the canonical `build` grant and the global-L0 grant, matching `builder_identity.json`; `not_applicable` before E7.2 |
| `l0_impact_ready` | S3 | the wave's impact statement, rebuild plan and fingerprints present |

## §9 · Cost control

- **Default effort is medium.** High is used only where the table in §3.1 says so. Low is used for mechanical roles.
- **Scripts before agents** for anything countable.
- **A spend meter** records tokens per role and per stage.
- **No budget ceilings** (N-15, native, 2026-09-29): spend is reported, not capped. If a ceiling is ever set, the Steward reports at 80% and dispatch pauses at 100%.
- **Weekly:** spend against estimate, per stage, in the scorecard.

## §10 · Restartability

- **All state lives in files:** the queues, the decisions log (`$SUVARNA_HOME/authority/DECISIONS.jsonl`), the register, the ledgers. None of it lives in an agent's memory.
- **Every packet is idempotent** and commits its progress, so a crash loses at most one step.
- **The Conductor can be restarted at any time** and resumes from its queue in `hq/00_ARCHITECTURE/control/suvarna/state/` and the decisions log; every pass is stateless (§5.1, §5.5).
- **A daily digest** informs the native (no action required): finished, parked, decided, next, spend.
- **The event log is append-only** and survives any crash; the tracker rebuilds its whole view from it on restart.

## §11 · Real-time visibility — the tracker

The native asked for a live view of the whole campaign: the plan, what runs in parallel and what in sequence, where we are, what is next, what is done, and useful measures, updated the moment things change. This section makes that a requirement on every role, not an afterthought.

### 11.1 · One source of truth

| Piece | Where | What it holds |
|---|---|---|
| Plan model | `00_ARCHITECTURE/control/suvarna/plan_model.json` | tracks (parallel, sequential or hybrid), items, dependencies, decisions, and how each item is proven done |
| Event log | `$SUVARNA_HOME/run/EVENTS.jsonl` | one line per state change, append-only |
| Decisions log | `$SUVARNA_HOME/authority/DECISIONS.jsonl` | the campaign's decisions (§12.10), read through the fail-closed gate evaluator (CODE-36); every `done_by: decision` item reads it: `decided` → done, `delegated` → waiting; a disagreeing decision event shows as a conflict |
| Detectors | `platform/scripts/governance/suvarna_tracker/detectors.py` (run from the hq worktree, §12.12) | checks against real sources, read from committed refs, never working trees: the register and ledgers at `NIKASHA_REF` (`origin/campaign/nikasha-test` until E4.3, then `origin/suvarna/trunk`), fetched before each read; PR merged, file on main, register tallies and rows, database columns, levels elevated; §11.7 adds more |
| Tracker | `platform/scripts/governance/suvarna_tracker/` | pure function of the four above; served on `127.0.0.1:8765` |

### 11.2 · Earned signals (CLAUDE.md §N.8)

- **Where a detector exists, the detector decides "done".** An event that claims done while the detector disagrees is shown as a *conflict*, never as done.
- **A detector that cannot measure** shows *unmeasured*, never done.
- **An event may mark an item done only with evidence** (refused at write time otherwise). A decision counts as decided only with what was decided.

### 11.3 · Who emits what

Every role emits through one command, which validates and appends atomically:

```
python -m suvarna_tracker.emit item --actor <role> --item <id> --state <running|review|blocked|parked|failed|done> [--step <name>] [--progress 0..1] [--evidence <path|PR>] [--detail <text>]
python -m suvarna_tracker.emit decision --actor steward --decision N-7.T4 --state requested --detail <text>
python -m suvarna_tracker.decide --id <id> --state decided --outcome <approve|reject|defer> --revision <artifact@version> --rationale "<why>" --source "<evidence; the native's words for N-1, a veto or a scope change>" --detail <text> --writer strategic-suvarna   # Strategic Suvarṇa only
python -m suvarna_tracker.emit heartbeat --actor conductor --detail "<what it is doing>"
python -m suvarna_tracker.emit metric --actor scribe --name <name> --value <number>
```

| Role | Emits |
|---|---|
| Conductor | `running` on dispatch; a heartbeat each loop pass |
| Builder, Analyst | step events (e.g. census, instance, briefs, designs) and progress as they go |
| Gate reviewer | `review`, then the verdict: back to `running`, or accepted |
| Scribe | `done` with evidence, at fold |
| Steward | decision `requested` event when foreseen, with the park file (to Strategic Suvarṇa); never a log line |
| Build operator | build started and finished, per level |
| Monitor | heartbeat and a `note` when an environment check changes; the Conductor watchdog's `blocked` (§5.5). Whole-item `blocked` on a plan item is the Conductor's (§12.1) |

A role that cannot emit (the log unwritable) stops and reports; it does not continue invisibly.

### 11.4 · How it stays real-time

- The tracker tails the event log every second and pushes a new snapshot to open pages over Server-Sent Events. **Measured: about 0.1 s** from a line being written to the page showing it (worst case about 1 s, one engine tick).
- It sends a visible heartbeat every 5 seconds, so a quiet campaign reads as live, and a stuck server reads as stuck.
- Detectors run in the background on time-to-live timers, so a slow check never delays an event.

### 11.5 · How it stays up, and honest when it cannot

| Failure | Behaviour (tested) |
|---|---|
| Tracker process killed | the supervisor restarts it in about 2 s; the page reconnects by itself about 0.4 s later |
| Page loses the stream | falls back to polling every 5 s and says so in amber |
| Server unreachable | the page says so in red, with the age of the data it still shows |
| Corrupt line in the event log | skipped, counted, and shown in the health strip |
| Bad edit to the plan model | the last good plan stays up; the error is shown |
| A detector crashes or its source is missing | that one item shows *unmeasured*; the rest carry on |
| Restart | the last snapshot is restored from disk at once, then rebuilt from the log |

### 11.6 · Known limits

- **Database credential source.** The detectors use the read-only environment file `~/.config/suvarna/pgenv.sh` (mode 600, N-20). They source it in a subprocess and never print it.
- **Local only.** The tracker listens on `127.0.0.1`. Viewing from another device needs a decision on how to expose it safely.
- **The plan model is hand-kept.** A change to the plan must be made in the plan document and in `plan_model.json` together, in one commit; the Scribe checks they agree at every fold.
- **ELEVATED comes only from the exact function.** Until E6.3t switches the tracker to the E6.3 function at the
  committed ref, `levels_elevated` and `assets_elevated` read unknown; the old one-certificate proxy is never shown as
  done. Certification cannot start before J1, which requires E6.3 and E6.3t.

### 11.7 · Detector types

Rule for all: an expected input that does not exist yet reads **pending**; a detector that cannot measure, whose spec is
unpinned (`pinned_by`), whose evidence is stale, or whose **type is not built yet** reads **unknown**. None is ever done.
Registered today (`detectors.py`): `pr_merged`, `prs_merged`, `branch_merged`, `main_has_file`, `main_has_files`,
`main_file_contains`, `register_tally_consistent`, `register_wellformed`, `register_rows_closed`, `register_rows_state`,
`register_freeze_clean`, `db_columns_exist`, `migrations_applied`, `scorecard_pass`, `monitor_check_ok`,
`deployed_contains`, `wave_deployed`, `levels_elevated`, `assets_elevated`, `registry_coverage`, `evidence_recent`,
`ledger_no_open_gap_on`, `fk_no_cascade`, `acks_from`, `main_protected`.

v1.5 changes (CODE items in `reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md` §5):

| Type | Done when | CODE |
|---|---|---|
| `evidence_verified` (new) | the evidence JSON parses; every `expect` value equals; required keys present; within `max_age_hours`; `commit_key` equals the pinned commit | 47 |
| `ci_job_passed` (new) | the named CI job concluded success on a `main` commit containing the named paths | 50 |
| `peer_tracker_item` (new; built) | a peer campaign's tracker (`/api/state`) shows the item with the expected status | 54 |
| `elevated_interface_ok` (new) | the tracker's own caller runs `elevated_assets(ref, repo)` at the committed ref and a planted unreadable input raises | 44 |
| `scorecard_pass` | also bound to the inspector blob, registry revision and a successful CI run | 48 |
| `registry_coverage` | strict schema; expected cell count pinned; N/A rules cite decisions | 49 |
| `fk_no_cascade` | `no_fk` = zero keys of any kind; no `allow` escape | 46 |
| `wave_deployed` | exact head ref and PR from `LANDING.json`; the squash merge commit an ancestor of the running commit; writer hashes equal | 52 |
| `levels_elevated`, `assets_elevated` | frozen map and family file pinned by hash; exact population; terminal dispositions counted, not dropped | 45 |
| `main_protected` | v2: the org ruleset by id, required checks incl. `Suvarṇa path guard`, 0 approvals, merge queue, no bypass, the bot Write only | 40 |
| `acks_from` | the detail equals the marker exactly (version-bound), after `since` | 55 |
| all | fetch failures are errors; per-type maximum age; a deadline per run | 51 |

## §12 · Operating conventions (settled 2026-09-29; revised in v1.3)

Settled in Strategic Suvarṇa from the role-instruction review. Role files cite these by number.

| # | Question | Convention |
|---|---|---|
| 12.1 | How a queue item reaches the tracker | Each queue line carries **`plan_item`**, the `plan_model.json` id it rolls up to. Events name `plan_item` in `--item` and the queue id in `--step`, so a packet's events never change the whole item's status. Only the Conductor emits whole-item `running`/`blocked`/`parked`; only the Scribe emits `done`, and never on an item a detector or a decision closes. |
| 12.2 | Ids and branches | Queue id: `<plan_item>-<kind>-<nnn>` (e.g. `A.L2-brief-014`). Lane branch: `suvarna/lane/<queue id>`. Lane worktree: `$SUVARNA_HOME/lanes/<queue id>`. **One base rule:** every lane branches from `suvarna/trunk` (= `main` plus accepted packets; the Conductor merges `origin/main` into it by a merge commit every pass). `campaign/nikasha-test` and `campaign/nirmana-engine` are never a base for anything bound for `main`: they sit on `l3/kala-layer-briefs` and carry ~190 foreign commits, Saṅgam family code among them; read them with `git show` or cherry-pick with `-x`. **The one exception:** a fold lane before the E4.3 cut-over is cut from `origin/campaign/nikasha-test` (§12.7) and is never PR-bound. **Landing:** a PR to `main` comes from `suvarna/land/<group>`, cut from `origin/main`, with the group's accepted lane branches merged into it; PR #2736 is not retargeted. Never edit `/Users/Dev/madhav-nikasha` or `/Users/Dev/madhav-engine` directly. |
| 12.3 | One Conductor or two | **One per session, one queue per Conductor**: `QUEUE.jsonl` (Exec Suvarṇa) and `QUEUE_ENGINE.jsonl` (Nikaṣa Engine), both in `hq/00_ARCHITECTURE/control/suvarna/state/`. Each has one writer, fenced: the runner holds `run/locks/queue_<session>.lock` for the whole pass and a fencing token in the queue's state line (CODE-41). |
| 12.4 | Leases | The project's existing mechanism: a row in `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on branch `origin/campaign-coordination`, claimed before and released after. Lease id: `SUVARNA-<queue id>`. The L3 family assets are never leased by Suvarṇa (N-17, charter R8). |
| 12.5 | Migration numbers | **The Suvarṇa range, decided (N-27): 1200–1299**, recorded as a reservation row on the coordination branch (§12.4). **Why a range is needed:** main's committed `.claude/settings.json` (L3 Kāla #2718) denies `Edit(platform/migrations/…)` on `[0-9][0-9][0-9]_*`, `10[0-6][0-9]_*`, `1070_*`, `11[2-9][0-9]_*`, `1[2-9][0-9][0-9]_*` and `ws2_*` for every session in the repo, and a deny beats the `--settings` allow, so only L3's 1071–1119 is writable. **Evidence 1200–1299 is free (2026-09-30):** no file numbered 1200 or above on `origin/main` or on any of the 2,220 local and remote refs, in either migration folder; none in the 22 open PRs; 0 of the 883 `_migrations_applied` rows (read-only, as `suvarna_reader`); the highest applied is 1150 (L3 Gochara). **The amendment** (E0.1): one small PR to `main`, coordinated with the L3 Kāla owner and authored by Strategic Suvarṇa as a control PR outside the swarm (E0.1; no swarm agent may edit `.claude/settings.json`), replacing `Edit(platform/migrations/1[2-9][0-9][0-9]_*)` by `Edit(platform/migrations/1[3-9][0-9][0-9]_*)`. The deny does not cover `platform/supabase/migrations/`, which `migrate.ts` also applies; Suvarṇa never writes there to step around it (charter P13). **Within the range**, one number at a time: after a fresh `origin/main` and open-PR sweep, the next free number; commit a placeholder migration file **on the lane branch** and push it at once; record the number in the queue line and on the coordination branch; never on `main` (charter P9); never reuse a number. N-26 renumbers 1094–1096 into the range. Until E0.1 is merged no Suvarṇa lane writes a migration (E7.1, E3.2 wait). |
| 12.6 | Where committed outputs live | On the lane branch, merged to `suvarna/trunk`: layer instances `00_ARCHITECTURE/briefs/suvarna/layers/<Lx>/`; asset briefs `…/layers/<Lx>/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md`; fix designs `…/layers/<Lx>/designs/`; gate reviews `00_ARCHITECTURE/briefs/suvarna/reviews/<queue id>_REVIEW_<n>.md` (committed on the packet's lane branch and merged with the packet, for audit; `<n>` is the review round). This is the one review path; raw review scratch and other evidence stay in `$SUVARNA_HOME/evidence/<queue id>/` (not committed). |
| 12.7 | Register and ledger folds before landing | **Before the E4.3 cut-over** only the Nikaṣa Engine Scribe folds, on a fold lane cut from `origin/campaign/nikasha-test`; the Nikaṣa Engine Conductor then pushes it as a fast-forward: `git push origin suvarna/lane/<qid>:campaign/nikasha-test` (never forced; a rejected push means re-cut from the new tip and redo the fold). The tracker reads `NIKASHA_REF=origin/campaign/nikasha-test` (fetched first), so the fold is visible at once; `/Users/Dev/madhav-nikasha` is never touched. **No ledger emits before E5.2 lands**; pre-E5.2 folds change register rows only. Exec Suvarṇa's Scribe files a fold request (`$SUVARNA_HOME/evidence/<qid>/FOLD_REQUEST.md` and a `note`). **Cut-over (E4.3):** folds stop at a named cut; the ledgers land on `main` last; line count and md5 of both ledgers and the register are equal across the old and new locations (evidence); Strategic Suvarṇa re-points `NIKASHA_REF` to `origin/suvarna/trunk` in one step; folds resume on lanes from `suvarna/trunk`. |
| 12.8 | Stall detection and spend | **The Conductor** does both: an agent with no event and no commit for 10 minutes is stalled (restart from its last commit); after every agent run it emits `metric` events for tokens used, by role and stage (N-15: reported, not capped). The Monitor stays an environment checker; the Conductor runs `monitor --once` before each dispatch and pauses on exit 2. |
| 12.9 | Which assets are "L2 MSR" (charter R1, F-3) | **The L2 writers** whose rebuild replaces rows in `bodha_msr_signals`: `bo_sudarshana`, `bo_vargottama_dhana` (W0); `bo_special_lagna`, `bo_arudha`, `bo_nakshatra_semantic` (W1); `bo_laksana`, `bo_laksana_rerank` (W2); A.L2i confirms from the writers. **F-3 (N-32):** all eight keys into it are dropped and the refusal in `assert_l2_msr_delete_safe` retired; no MSR rebuild runs until F3.FK (`fk_no_cascade`, `no_fk`) and F3.GUARD read done. Downstream rows referencing changed signals are rebuilt in wave order; `msr_referential_integrity.py` measures dangling references after each wave; family downstream (`kala_convergence`) is notified (charter R8). |
| 12.10 | Who writes `DECISIONS.jsonl` | **The authoritative log is `$SUVARNA_HOME/authority/DECISIONS.jsonl`** (native-owned folder and file, read-only to the swarm; N-37), appended only through `python -m suvarna_tracker.decide`, **only by Strategic Suvarṇa** (`--writer strategic-suvarna`), each line with a typed `outcome`, the `revision` decided and a `rationale` (CODE-36); an `approve` is refused while any prerequisite reads not done. The native's own rulings (N-1, a veto, a scope change) carry the native's words as their source. No swarm role writes to it (P14). The mirror on `suvarna/hq` is refreshed by SS (`decide --mirror-to`). Other campaigns' rulings (Pravāha) are cited, never recorded here. |
| 12.11 | Daily digest | Written by the Steward to `hq/…/state/DIGEST_<date>.md` and announced as a tracker `note`: finished, parked (with age), decided by SS (with rationale), next, spend. It informs the native; no action is required. |
| 12.12 | Committing `suvarna/hq` state; where the tools run | Each queue's writer commits its own file on `suvarna/hq` at the end of every pass, only through `python3 -m suvarna_tracker.hq_commit --paths <path…> -m "<msg>"` (the hq lock; explicit paths only). Plan revisions reach hq from `origin/strategy/suvarna-plan` by a merge commit made by the swarm at pass start (never fast-forward-only, never a rebase). **The tracker, Monitor, hook, merge gate, gate evaluator and broker run from the native-owned control checkout `/Users/Dev/suvarna/control`** at a pinned control release tag `suvarna-control-v<x>` (N-37); only SS moves it to a new release, after LG.7's regression and real-CLI run; the services are restarted by SS then. Tracker code is changed only on `strategy/suvarna-plan`. |
| 12.13 | Which checkout the census runs from | `/Users/Dev/madhav-nikasha` (read-only) until E4.1 lands the inspector on `main`; `suvarna/trunk` after. Always through `census_run` (§12.15). The census records the inspector's commit with its output. A level wave censuses only its assets once E1.9 adds `--assets`. |
| 12.14 | Gating measurements | **Provisional censuses** (before J1) are checked by script, not by an Opus review: exit code (0 clean · 2 FAIL present · 3 PARTIAL/NO_DETECTOR/ERRORED present · 4 unknown · 5 script error; 4 and 5 are unmeasured · 75 census lock held), the inspector's commit, per-layer row counts. (The inspector's docstring disagrees with its code on code 3: an E1.2 row.) **Certifying censuses** (after J1) get a gate review before the step is done, at fold. |
| 12.15 | One census at a time | Every census, in every session and in the family sessions, runs through the validated wrapper `python3 -m suvarna_tracker.census_run --layer <Lx> --out <absolute path> --wait 900 --emit --actor <role>` (review pass 3 B6). It takes the exclusive census lock `$SUVARNA_HOME/run/locks/census.lock` itself (`--wait` seconds, default 0; exit 75 means another census holds it: wait or re-queue), sources `~/.config/suvarna/pgenv.sh`, builds and runs only `asset_census.py --layer <Lx> --out <file>` from the census checkout (today `/Users/Dev/madhav-nikasha`; the switch to `suvarna/trunk` at E4.1, §12.13, is a CODE item), and refuses (exit 2) a relative `--out` or one with shell metacharacters; create the evidence folder first (`mkdir -p`). `census_lock -- <command>` no longer wraps an arbitrary command: it would have bypassed every Bash deny. |
| 12.16 | What a certification record carries; when it is current | The asset, gate or addition, verdict, criterion and detector (never `NONE` for a PASS), census run id, job image tag, writer file hashes, upstream certification ids, the **semantic fingerprint** and the certificate **generation**. **Semantic fingerprint** (Astra F14): sha256 over the asset's rows for the chart (or globally for L0) in natural-key order, each row as canonical JSON of its declared semantic columns; surrogate ids, timestamps, build and attempt ids and other volatile columns excluded as declared in the asset brief; embeddings compared under the brief's declared equivalence policy. An idempotent rebuild that changes no semantic column leaves the fingerprint, and so every downstream certificate, current. E5.5 writes invalidations with an **invalidation watermark** (the newest event offset and commit it has processed); `elevated_assets` refuses a ledger ref newer than the watermark. Layer closes run in an **acceptance epoch** (population, standard revision and input generations fixed; changes to its inputs coordinated by lease); at most two re-walks per layer before SS reviews the cause. |

**Charter points** (history; v1.5 moves authority to Strategic Suvarṇa under N-28): ruled 2026-09-29 as charter v1.2 amendments A–C: L0's global build under G13; per-layer idempotency in G4; pre-wave fingerprints and a reserved undo for normal level waves (charter §6.7). Charter v1.3 folds D1–D5 (builder identity and native L0 dispatch; family staleness exemption and hand-back; registry-computed N/A; L0 dump and diff; watchdog and no bypass). Charter v1.4 folds review pass 2 (only Strategic Suvarṇa writes decisions; F-3 plus F3.FK; ancestry; landing branches; §13 isolation, proposed pending N-25).
