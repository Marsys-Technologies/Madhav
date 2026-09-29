---
artifact: SUVARNA_EXECUTION_ARCHITECTURE
canonical_id: SUVARNA_EXECUTION_ARCHITECTURE
version: "1.1"
status: DRAFT — for native review
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_CAMPAIGN_PLAN_v1_2.md (the what and when; this document is the how)
decision_owner: Native (Abhisek Mohanty)
changelog:
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
5. **Park and continue.** A question for the native never stalls unrelated work.
6. **Diagnose before retrying.** A second failure of the same thing becomes a diagnosis task, never a third attempt.
7. **Freeze the standard before judging against it.** Nirmāṇa replaced its definition five times; most of its freezes were judged against a standard it later dropped.
8. **Every result is gated.** A fresh reviewer tries to break it before it counts.
9. **Visible the moment it happens.** Every state change is written to the event log as it happens, by the role that caused it, before that role moves on. The tracker (§11) shows it within about a second. A change that is not in the log did not happen, as far as the campaign is concerned.

### 1.1 · Lessons from Nirmāṇa, and the rule each produced

| What happened | Evidence | Rule here |
|---|---|---|
| Sessions spent turns re-checking a lock that had not moved | L2 state log: "held steady across cycles #489–#490" | Event-driven waits, no polling (§5.3) |
| One asset retried many times without a root cause | `ka_kshetra`: 19th attempt | Principle 6; retry cap (§5.4) |
| The standard changed mid-campaign | 5 superseded definition revisions; 72 of 98 freezes under the first | Principle 7; the engine freezes first |
| Weak verification | 97 of 98 frozen assets still carry Nikaṣa gaps | Nine gates plus a gate review on everything |
| Layers frozen strictly one after another | plan §1 "layers freeze strictly in order" | Asset-level dependency waves (§6) |

## §2 · Isolation

The campaign runs in its own folder, on its own branches, with its own switch. Other campaigns keep running.

### 2.1 · Folder

```
/Users/Dev/suvarna/
├── hq/               worktree, branch suvarna/hq (from strategy/suvarna-plan) — plan, state, queue, decisions (the campaign's record);
│                     state lives in 00_ARCHITECTURE/control/suvarna/state/ (repository root stays clean, ROOT_FILE_POLICY)
├── trunk/            worktree, branch suvarna/trunk (from main) — integration branch all lanes merge into
├── lanes/<lane-id>/  one worktree per active lane, created and removed by the conductor
├── evidence/         census outputs, build evidence, review scratch (not committed)
└── run/              SUVARNA_HOLD switch, heartbeat, spend meter, locks, mailboxes
```

- **Never the main checkout.** It carries other campaigns' uncommitted state.
- **`suvarna/trunk` reaches `main` through small PRs,** one per accepted packet group, never one giant PR.
- **Lane worktrees are disposable.** A lane's work lives on its branch until it is merged.

### 2.2 · Database

- **Reads:** the pre-resolved read-only environment on the local proxy (§8).
- **Writes:** two paths only.
  - Migrations, applied by the deploy pipeline, then verified against the live database.
  - Builds, dispatched through the orchestrator.
- **No hand-written SQL against production. No privileged credentials** without a named native approval.

### 2.3 · Other live workstreams

- **An asset lease.** Before Suvarṇa changes an asset, it takes a lease on it on the shared campaign-coordination branch. Before taking one, it checks whether another workstream holds that asset.
- **L3 Gochara** is live today. Its assets stay leased to it until the two workstreams agree a hand-over (see the L3 focus-families document).
- **Migration numbers** come from the reserved ranges, checked across both migration folders at the moment of numbering.

## §3 · The swarm

### 3.1 · Roles

| Role | What it does | Model · effort | Runs |
|---|---|---|---|
| **Conductor** | Owns the work queue. Dispatches ready work, folds results, releases dependents. Never builds, never reviews. | Opus 5.5 · medium | 1, long-running |
| **Steward** | Decides within the delegated charter (§7). Parks reserved questions for the native, batched. | Opus 5.5 · high | on demand, rarely |
| **Architect** | Turns a stage brief into packet specs. Designs algorithms and derivability mechanisms. | Opus 5.5 · high | a few at a time |
| **Analyst** | Read-only work: census, layer-instance drafts, asset briefs, dispositions, fix designs. | Sonnet 5 · medium | many in parallel |
| **Builder** | Code, tests, migrations for one packet. | Sonnet 5 · medium (high for writer or ledger changes) | several in parallel |
| **Gate reviewer** | Fresh, read-only, adversarial. Rules ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT. | Opus 5.5 · medium (high for ledger writes, reopens, algorithms) | several in parallel |
| **Build operator** | Dispatches orchestrator runs in dependency waves; collects evidence. Mostly a script. | Sonnet 5 · low | 1 per chart |
| **Scribe** | Folds accepted packets into the register, ledgers and state; computes tallies; rotates fingerprints; runs drift. Mostly scripts. | Sonnet 5 · low | 1 |
| **Monitor** | Heartbeat, stall detection, spend meter, environment checks. | no model — a script | always on |
| **Independent reviewer** | Third-party review of plans, stage briefs and rulings. | GPT-6 Astra or Kimi | at stage gates |

### 3.2 · Why this split

- **Opus only where judgement decides the outcome:** conducting, deciding, designing and reviewing.
- **Sonnet does the volume:** analysis and coding.
- **Scripts do the bookkeeping.** The register-tally drift was a typed number; a script would not have drifted.
- **Builders never review. Reviewers never build.** Every gate is a fresh context.

### 3.3 · Concurrency caps (starting values, tuned from measured spend)

| Kind | Cap | Why |
|---|---|---|
| Analysts | 6 | read-only; limited by review capacity downstream |
| Builders | 4 | limited by merge conflicts on shared files |
| Gate reviewers | 3 | one per finished packet, in parallel with the next build |
| Architects | 2 | high-cost; design work is sequenced by need |
| Full six-layer census | 1 at a time | concurrent runs exhausted the connection pool once |
| Orchestrator builds | 1 per chart | the orchestrator enforces a per-chart database lock |

## §4 · The work queue

### 4.1 · The item

Every piece of work is one line in `hq/00_ARCHITECTURE/control/suvarna/state/QUEUE.jsonl`:

| Field | Meaning |
|---|---|
| `id`, `stage`, `lane` | identity and grouping |
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

On every event (an agent finishing, a build finishing, a decision arriving, a timer), and emitting a heartbeat event at each pass so a stalled conductor is visible on the tracker:

1. Fold what finished.
2. Release its dependents.
3. Dispatch every ready item, up to the caps.
4. If nothing is ready and something is running: wait for the next event.
5. If nothing is ready and nothing is running: pull from the standing queue (§5.2).
6. If the standing queue is empty too: write the reason to state, request what is missing, and sleep until it arrives.

### 5.2 · The standing queue

Useful work that never blocks anything and can always be picked up:
- analysis for layers not yet started;
- opportunity-register research;
- test-coverage gaps;
- documentation of finished work.

### 5.3 · Waiting without burning

- **No polling cycles.** The conductor waits on completion notifications and on long timers for external events (CI, deploy, a native decision).
- **A timer never shorter than the thing it waits for.** A deploy that takes 15 minutes gets one check at about 15 minutes, not fifteen.

### 5.4 · Failure handling

| Situation | Response |
|---|---|
| A build fails once | retry once, unchanged, in case the cause was transient |
| The same build fails twice | stop retrying; open a diagnosis item (Analyst, then Architect if needed) |
| A gate rejects twice | escalate to the Steward with both reviews |
| An agent stalls (no progress for 10 minutes) | the Monitor flags it; the Conductor restarts it from its last commit |
| Environment failure (database proxy down, machine asleep) | the Monitor pauses dispatch, repairs what it can, and resumes |

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

### 6.2 · Therefore: fix first, walk once

1. **Fixes land before rebuilds.** All planned fixes for an asset are merged before it is rebuilt.
2. **One wave per level.** When every asset at a level has its fixes merged and every upstream asset is certified, the Build Operator dispatches one orchestrator run covering that whole level for the chart.
3. **Certify as the wave lands.** The inspector re-measures that level; gaps close; certifications are written.
4. **Front-load the wide top.** Levels 0–2 (65 assets) are rebuilt and certified as early as their fixes allow. Most downstream work then sits on certified inputs.
5. **A failure mid-chain** stops only its own downstream. Everything off that branch continues.
6. **An upstream change after certification** invalidates the downstream certifications. The inspector re-measures them; a rebuild runs only if the output actually changed.

### 6.3 · Charts

- The canonical chart first (decision N-12).
- L0 is global: one build, no chart.
- Other charts are a later, recorded addition. Each chart walks the chain once.

## §7 · Autonomy and its limits

A delegated-authority charter (`SUVARNA_AUTONOMY_CHARTER_v1_0.md`, to be written from this section once approved) binds every agent.

### 7.1 · Granted — the swarm decides alone, and logs it before acting

- Dispatch, sequence, re-sequence and cancel queue items.
- Choose model and effort within the caps and the budget.
- Accept a gate verdict and fold it.
- Retry once; open diagnosis items.
- Set a gate `N/A` only with a written reason that a gate reviewer has accepted.
- Merge accepted packets to `suvarna/trunk`; open PRs to `main` for accepted groups.
- Dispatch orchestrator builds in dependency order.

### 7.2 · Reserved — park for the native, and continue with everything else

- Everything on the plan's decision list (§8 of the plan).
- Any change to the frozen writer contract (CLAUDE.md §N.2).
- Any destructive operation (clear-and-rebuild of a populated table) without a verified snapshot.
- Any scope beyond the canonical chart.
- Retiring an asset, or changing an asset's output in a way not in its approved brief.
- Exceeding a budget ceiling.
- Anything the charter does not clearly grant.

### 7.3 · Prohibited — refuse, never park

- Reading, moving or logging credentials.
- Writing production data outside migrations and the orchestrator.
- Weakening, skipping or reinterpreting a gate.
- Closing a gap on anything other than PASS or a justified N/A.
- Committing to `main` directly.

### 7.4 · Native decisions without stalls

- **Lead time.** The Steward requests a decision as soon as it is foreseeable, not when it is needed.
- **Batching.** Decisions are sent in batches at natural join points, each with a recommendation.
- **Continuing.** While a decision is pending, only the items that depend on it wait.

## §8 · Environment

The Monitor checks these before any dispatch, and every 15 minutes while work runs:

- **Database proxy** listening on 5433. Restart if not.
- **Read-only credential file** present at `~/.config/suvarna/pgenv.sh`, owner-only (N-20). If missing, pause and park; never recreate it, never call `gcloud` per command. Checked by `python -m suvarna_tracker.monitor`.
- **Power.** On AC power, with sleep prevented. On battery, pause long builds and warn.
- **The hold switch.** `run/SUVARNA_HOLD` absent. If present: finish running items, dispatch nothing new.
- **Disk space** for evidence.
- **The tracker** answering `/api/health`. If not, the supervisor restarts it; if that fails, the Monitor restarts the supervisor. The swarm keeps working either way: the event log is written whether or not the tracker is up.

## §9 · Cost control

- **Default effort is medium.** High is used only where the table in §3.1 says so. Low is used for mechanical roles.
- **Scripts before agents** for anything countable.
- **A spend meter** records tokens per role and per stage.
- **No budget ceilings** (N-15, native, 2026-09-29): spend is reported, not capped. If the native later sets a ceiling, the Steward reports at 80% and dispatch pauses at 100%.
- **Weekly:** spend against estimate, per stage, in the scorecard.

## §10 · Restartability

- **All state lives in files:** the queue, decisions, the register, the ledgers. None of it lives in an agent's memory.
- **Every packet is idempotent** and commits its progress, so a crash loses at most one step.
- **The Conductor can be restarted at any time** and resumes from `hq/00_ARCHITECTURE/control/suvarna/state/`.
- **A daily digest** goes to the native: what finished, what is parked, what is next, spend.
- **The event log is append-only** and survives any crash; the tracker rebuilds its whole view from it on restart.

## §11 · Real-time visibility — the tracker

The native asked for a live view of the whole campaign: the plan, what runs in parallel and what in sequence, where we are, what is next, what is done, and useful measures, updated the moment things change. This section makes that a requirement on every role, not an afterthought.

### 11.1 · One source of truth

| Piece | Where | What it holds |
|---|---|---|
| Plan model | `00_ARCHITECTURE/control/suvarna/plan_model.json` | tracks (parallel, sequential or hybrid), items, dependencies, decisions, and how each item is proven done |
| Event log | `$SUVARNA_HOME/run/EVENTS.jsonl` | one line per state change, append-only |
| Detectors | `platform/scripts/governance/suvarna_tracker/detectors.py` | checks against real sources: PR merged, file on main, register tallies and rows, ledgers, database columns, levels elevated |
| Tracker | `platform/scripts/governance/suvarna_tracker/` | pure function of the three above; served on `127.0.0.1:8765` |

### 11.2 · Earned signals (CLAUDE.md §N.8)

- **Where a detector exists, the detector decides "done".** An event that claims done while the detector disagrees is shown as a *conflict*, never as done.
- **A detector that cannot measure** shows *unmeasured*, never done.
- **An event may mark an item done only with evidence** (refused at write time otherwise). A decision counts as decided only with what was decided.

### 11.3 · Who emits what

Every role emits through one command, which validates and appends atomically:

```
python -m suvarna_tracker.emit item --actor <role> --item <id> --state <running|review|blocked|parked|failed|done> [--step <name>] [--progress 0..1] [--evidence <path|PR>] [--detail <text>]
python -m suvarna_tracker.emit decision --actor steward --decision N-7 --state <requested|decided|delegated> --detail <text>
python -m suvarna_tracker.emit heartbeat --actor conductor --detail "<what it is doing>"
python -m suvarna_tracker.emit metric --actor scribe --name <name> --value <number>
```

| Role | Emits |
|---|---|
| Conductor | `running` on dispatch; a heartbeat each loop pass |
| Builder, Analyst | step events (e.g. census, instance, briefs, designs) and progress as they go |
| Gate reviewer | `review`, then the verdict: back to `running`, or accepted |
| Scribe | `done` with evidence, at fold |
| Steward | decision `requested` when foreseen; `decided` when the native rules |
| Build operator | build started and finished, per level |
| Monitor | `blocked` and the reason when the environment stops work, and again when it clears |

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

- **Database credential source.** The detectors that read the database use a read-only environment file. Today that file sits in a session scratch folder; a permanent location is needed before execution (decision for the native).
- **Local only.** The tracker listens on `127.0.0.1`. Viewing from another device needs a decision on how to expose it safely.
- **The plan model is hand-kept.** A change to the plan must be made in the plan document and in `plan_model.json` together; the Scribe checks they agree at every fold.
