---
artifact: SUVARNA_EXECUTION_ARCHITECTURE
canonical_id: SUVARNA_EXECUTION_ARCHITECTURE
version: "1.4.1"
status: DRAFT — for native review (N-1)
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_CAMPAIGN_PLAN_v1_4.md (the what and when; this document is the how)
decision_owner: Native (Abhisek Mohanty)
changelog:
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
5. **Park and continue.** A question for the native never stalls unrelated work.
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
/Users/Dev/suvarna/
├── hq/               worktree, branch suvarna/hq (from strategy/suvarna-plan) — plan, queues, digests, the decisions mirror (the campaign's record),
│                     and the committed tracker and Monitor code that actually runs (§12.12);
│                     state lives in 00_ARCHITECTURE/control/suvarna/state/ (repository root stays clean, ROOT_FILE_POLICY)
├── trunk/            worktree, branch suvarna/trunk (main plus accepted packets; main merged in every pass) — the integration branch
├── config/           the Suvarṇa Claude Code settings file and hooks (§2.4), owned by the native, read-only to the swarm
├── lanes/<lane-id>/  one worktree per active lane, created and removed by the conductor
├── evidence/         census outputs, build evidence, L0 dumps and diffs, review scratch (not committed)
└── run/              DECISIONS.jsonl (the authoritative decisions log, §12.10), EVENTS.jsonl, SUVARNA_HOLD switch,
                      heartbeat, spend meter, locks/ (census, hq), mailboxes
```

- **Never the main checkout.** It carries other campaigns' uncommitted state.
- **Work reaches `main` through small PRs** from landing branches `suvarna/land/<group>` cut from `origin/main`, one per
  wave group or accepted packet group, never one giant PR (§12.2).
- **Lane worktrees are disposable.** A lane's work lives on its branch until it is merged.

### 2.2 · Database

- **Reads:** `~/.config/suvarna/pgenv.sh` on the local proxy (§8), logging in as `suvarna_reader`, a login that is
  read-only by privilege, not by session setting (D6, applied 2026-09-29).
- **Writes:** two paths only.
  - Migrations, applied by the deploy pipeline, then verified against the live database.
  - Builds, dispatched through the orchestrator by `POST /api/cockpit/runs` as the builder identity (D1): a
    dispatch-only grant on the canonical chart, used only through `~/.config/suvarna/bin/suvarna-build`, never
    `clear_before`. Global L0 builds are dispatched by the native at the Build operator's parked request.
- **No hand-written SQL against production. No privileged credentials** without a named native approval.

### 2.3 · Other live workstreams

- **An asset lease.** Before Suvarṇa changes an asset, it takes a lease on it on the shared campaign-coordination branch (§12.4). Before taking one, it checks whether another workstream holds that asset.
- **The L3 families** (Gochara, Saṅgam, Kṣetra) belong to their family sessions (N-17). Suvarṇa never leases or changes their assets (charter R8) until the native records a hand-back (HB-G, HB-S, HB-K). It certifies what they build (§6.4).
- **Migration numbers:** reserved one at a time (§12.5).

### 2.4 · Who the swarm runs as — PROPOSED, pending N-25

**Why.** Claude Code merges allow rules across scopes. Today the native's user settings default to
`bypassPermissions` and allow `Bash(*)`, `Edit(**)`, `Write(**)`, `mcp__github__*` and `mcp__postgres__*`; the repo's
committed `.claude/settings.json`, which every worktree loads, allows `git push*`, `gh pr *`, `gh api *` and sourcing
`/Users/Dev/madhav-l3/dbenv.sh` and `dbenv_builder.sh` (both world-readable); any process running as the native can
append to the decisions log. An allowlist placed beside these bounds nothing.

**The proposal (N-25).**
- **A separate macOS user**, `suvarna`, runs every swarm process (Conductors, lanes, Monitor watchdog relaunches).
  Its home holds nothing of the native's: no read access to `~/.config/madhav-admin`, `~/.codex`, the native's GitHub
  and cloud logins, `/Users/Dev/madhav-l3/dbenv*`, or any `platform/.env*`.
- **Its own Claude Code settings**, `$SUVARNA_HOME/config/claude-settings.json`, owned by the native and read-only to
  `suvarna`, passed explicitly (`--settings`) by every launch: `defaultMode: dontAsk`; allow, in exactly the forms the
  role documents use: the `suvarna_tracker` modules the swarm runs (`emit`, `census_run`, `hq_commit`, `lane_launch`,
  `monitor`, `events`), never `decide`, `decisions` or `runtime_settings` (those are Strategic Suvarṇa's and the
  native's, review pass 3 B6); `bash -c 'source ~/.config/suvarna/pgenv.sh && psql …'` and `… && pg_dump …`
  (single-quoted); `python3 platform/scripts/governance/<script>.py`; `pytest`; `git` with pushes only to
  `suvarna/*` branches, plus the Nikaṣa Engine's fast-forward fold push to `campaign/nikasha-test` before E4.3 (§12.7)
  (no `+` refspec, no `…:main`, no force); `gh pr create`, `gh pr view`;
  `~/.config/suvarna/bin/suvarna-build …`; **explicit deny rules**, which win over allow rules in every other scope: `gh pr merge*`, `gh api*`,
  `git push --force*`, `git push* main*`, `mcp__github__*merge*`, `mcp__postgres__*`, `gcloud*`, `Read`/`Bash` on
  `**/.env*`, `/Users/Dev/madhav-l3/dbenv*`, `~/.config/madhav-admin/**`, `~/.codex/**`, and `Edit`/`Write` on
  `$SUVARNA_HOME/config/**` and `$SUVARNA_HOME/run/DECISIONS.jsonl`; a **hold-guard hook** (PreToolUse) that refuses
  every production-visible command while `run/SUVARNA_HOLD` exists. The hook runs the committed code in the hq worktree
  (`PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance`), never Strategic Suvarṇa's worktree, and **fails
  closed for dispatches**: if it cannot run (an import failure, an unreadable path under N-25) or cannot read its
  payload, it refuses an `Agent` dispatch and any dispatch-like command rather than letting it through. The repo's project settings still load in each
  worktree; the deny rules are written to cover everything they allow that Suvarṇa must not do.
- **Its own GitHub identity** (a machine user or GitHub App) with a token scoped to this repository: it can push
  branches and open PRs. **Branch protection on `main`** requires a pull request with the native's approving review and
  allows bypass only by the native, so the server refuses this identity's merge (R7 held by GitHub).
- **The decisions log** `$SUVARNA_HOME/run/DECISIONS.jsonl` is owned by the native's account, readable by `suvarna`,
  writable only by the native (Strategic Suvarṇa runs as the native). The swarm cannot forge a decision (P14).
- **Shared folders by group:** `/Users/Dev/suvarna/{hq,trunk,lanes,evidence}` and `run/` (except the decisions log)
  are group-writable for a `suvarna-campaign` group holding both users; `~/.config/suvarna/pgenv.sh` and `builder.env`
  move to the `suvarna` user (mode 600), and the native keeps no copy the swarm can read.

**Required at launch either way** (L.16a, L.16b, L.16g; FI-7 waits): the settings file with its deny rules and hook,
passed to every agent; `chmod 600` on the two `dbenv` files; the swarm's own GitHub identity and branch protection on
`main`; the Monitor's `isolation` check (who it runs as, what it can read and write, the settings files' hashes
against a recorded baseline; it reads `warn` until N-25 is decided and must read `ok` after) and its decision-writer
check (any `decided` line not written by `strategic-suvarna` blocks). **What N-25 adds:** without it, everything above is a second line only, because the swarm runs as the native
and can reach the native's logins and the log.

## §3 · The swarm

### 3.1 · Roles

| Role | What it does | Model · effort | Runs |
|---|---|---|---|
| **Conductor** | Owns the work queue. Dispatches ready work, folds results, releases dependents. Never builds, never reviews. | Opus 5.5 · medium | 1, long-running |
| **Steward** | Classifies questions against the charter (§7). Parks reserved questions for the native, batched; records no decision (charter P14). | Opus 5.5 · high | on demand, rarely |
| **Architect** | Turns a track brief into packet specs. Designs algorithms and derivability mechanisms. | Opus 5.5 · high | a few at a time |
| **Analyst** | Read-only work: census, layer-instance drafts, asset briefs, dispositions, fix designs. | Sonnet 5 · medium | many in parallel |
| **Builder** | Code, tests, migrations for one packet. | Sonnet 5 · medium (high for writer or ledger changes) | several in parallel |
| **Gate reviewer** | Fresh, read-only, adversarial. Rules ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT. | Opus 5.5 · medium (high for writer, ledger, auth, reopen and algorithm packets) | several in parallel |
| **Build operator** | Dispatches orchestrator runs in dependency waves through `suvarna-build` (D1); prepares and parks L0 waves for the native to dispatch; collects evidence. Mostly a script (E5.3). | Sonnet 5 · low | 1 per chart |
| **Scribe** | Folds accepted packets into the register, ledgers and state; computes tallies; rotates fingerprints; runs drift. Mostly scripts. | Sonnet 5 · low | 1 |
| **Monitor** | Environment checks (the reader's read-only by effective privilege; the builder's scope through the authenticated preflight; isolation; decision writers), heartbeat, repair, and the Conductor watchdog (§5.5). Agent stalls and spend belong to the Conductor (§12.8). | no model — a script | always on |
| **Independent reviewer** | Third-party review of plans, track briefs and rulings. | GPT-6 Astra or Kimi | at gates |

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

On every event (an agent finishing, a build finishing, a decision arriving, a timer), and emitting a heartbeat event at each pass so a stalled conductor is visible on the tracker. **Every pass is stateless (D5):** it starts by reading the role files, its queue and the decisions log, and ends by committing its queue (§12.12). Nothing lives only in the Conductor's context.

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
| An agent stalls (no event and no commit for 10 minutes) | the Conductor detects it (§12.8) and restarts it from its last commit |
| The Conductor stalls (heartbeat older than three loop intervals) | the Monitor's watchdog relaunches a headless pass (§5.5); three relaunches in an hour → hold and park |
| Environment failure (database proxy down, machine asleep) | the Conductor pauses dispatch on Monitor exit 2; the Monitor repairs what it can; dispatch resumes when it clears |

### 5.5 · Runtime (D5)

A Claude Code session is bounded by its context and ends when its turn ends; the swarm must run for weeks with the
native absent. So the runtime is chosen explicitly.

- **Interim, from launch to G2 (L.15):** `/loop 10m` in the two execution sessions (a fixed interval; a self-paced
  loop is not allowed). Its scheduled tasks expire after 7 days, so the native re-arms it weekly. In place from the start: stateless passes (§5.1); the permission allowlist
  below; the watchdog in alerting mode (a stale Conductor heartbeat emits `blocked` and writes `run/CONDUCTOR_STALLED`);
  `caffeinate -dimsu`, AC power, lid open, automatic OS restarts off.
- **Durable, before B.W1 (L.14):** each Conductor runs as a supervised headless loop of stateless passes, on the
  `run_tracker.sh` pattern (loop, restart after 2 s, stop file) or a launchd `KeepAlive` agent:
  `claude -p "<Conductor prompt>" --settings $SUVARNA_HOME/config/claude-settings.json --permission-mode dontAsk`, in
  the session's hq worktree. **A pass reads** its role files, its queue, the decisions log, the tracker's
  `run/snapshot.json`, and `EVENTS.jsonl` only from the byte offset its last pass committed in the queue's state line,
  so pass cost stays flat as the log grows.
  - **Watchdog:** the Monitor's `--watch` loop relaunches a pass when the Conductor heartbeat is older than three loop
    intervals; at most three relaunches an hour, then it sets the hold and parks (charter G15).
  - **Rollover:** a session rolls over on a pass count or a context threshold with a CLAUDE.md §H close; the watchdog
    starts the next.
  - **Lanes:** every lane agent is a separate process in its own worktree with its own heartbeat, started only by the
    lane launcher `python3 -m suvarna_tracker.lane_launch --qid <qid> --role <role> --model <model> --effort <effort>`,
    which runs `claude -p` in `$SUVARNA_HOME/lanes/<qid>` with the settings file and `dontAsk` fixed and records the
    pid; the launcher is the only `claude` command on the allow-list. A pass that ends hands its lanes to the next pass.
    In-process background subagents are not used for lanes (their fate when a parent exits is undocumented). This holds
    from launch, under `/loop` too.
  - **Usage limits:** a limit pause looks like a stall; the watchdog reads the CLI's error and waits it out, never
    restart-loops. Billing the runner by API key removes the pause; that is the native's choice (N-23).
- **Permissions (both modes):** the Suvarṇa settings file `$SUVARNA_HOME/config/claude-settings.json` (§2.4), never a
  tracked `.claude/settings.json` (that file is shared by every branch and would collide with plan merges), passed by
  `--settings` to every session, pass and lane. It allows exactly the §2.4 forms: the swarm's `suvarna_tracker`
  modules (never `decide`, `decisions`, `runtime_settings`), `psql` and `pg_dump` only as
  `bash -c 'source ~/.config/suvarna/pgenv.sh && …'`, `git` with pushes only to `suvarna/*` and the §12.7 fold push
  (never a `+` refspec, a `…:main` destination or `--force`), `python3 platform/scripts/governance/<script>.py`, `pytest`, `gh pr create/view`,
  `~/.config/suvarna/bin/suvarna-build`, the lane launcher; it denies everything §2.4 lists plus `rm -rf` outside `$SUVARNA_HOME/lanes` and `curl` to hosts off the
  list. A denial is logged, never a stall. No bypass mode (charter P13).
- **Cost:** each fresh pass re-reads about 50–100 k tokens; the spend meter shows it per pass.
- **Single point of failure:** the Mac. Hold-and-park makes a failure safe, not fast.

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
   rebuilt: each wave group goes to `main` as one PR from a landing branch, which the native merges; the deploy
   follows (plan items B.W0M…B.W5M). A wave's fixes are every Track I item for an asset in its level range (I.W0…I.W5),
   whatever the layer. At dispatch the level-wave script re-checks that the merge is an **ancestor** of the running
   commit and that the writer files at that commit hash to what the packet recorded (charter §6.4), because other
   workstreams deploy to `main` too.
2. **One wave per level.** When every asset at a level has its fixes deployed and every upstream asset is certified and
   current, the Build operator dispatches one orchestrator run covering **the level's non-family assets** for the chart:
   every asset at that level in the frozen `LEVEL_MAP.json` that is not in `FAMILY_ASSETS.json`'s `family_set`, as an
   `--assets` list, never `--level`. A wave **never** dispatches a family asset or a reader (family assets sit at levels
   1, 5, 12 and 13, readers at 13; a whole-level run would rebuild family data, charter R8); the level-wave script
   refuses if its dispatch set intersects the family set. For an L0 wave
   it prepares the pre-check, dump and impact statement and parks the dispatch for the native (§6.5).
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

### 6.4 · The L3 family assets in the waves (D2)

- **The family set and its readers** live in `00_ARCHITECTURE/control/FAMILY_ASSETS.json` (keys pinned in Track E §8),
  versioned and frozen at J1 (E6.3). The `levels_elevated` detector and the census read it.
- **Excluded from wave completion.** A wave completes without the family assets and their readers. Readers carry an
  asset-level wait ("family input certified"), are shown as `blocked` with detail `waiting_on_family: <asset>`
  (ROLE_CONDUCTOR step 7), are never silently dropped, and are certified under B.FR.L3, B.FR.L4, B.FR.L5 once their
  input is.
- **Certification.** A family asset's Build gate passes only on an orchestrator run on the canonical chart (any
  `triggered_by`) whose substep plan completed (CLAUDE.md §N.8); a hand-run cutover script does not count. Suvarṇa's
  independent re-measure then writes the certification (B.FG, B.FS, B.FK). This is Suvarṇa's ledger, not family build
  state, so charter R8 is not touched.
- **Staleness propagation.** A Suvarṇa wave with a real delta flips downstream family assets to `stale` through the
  orchestrator's own propagation. That is exempt from R8; the wave evidence records it and the family session is told.
- **Saṅgam** is certified only after its L2 upstreams (B.W2). With the cascade removed (F3.FK) a later L2 rebuild no
  longer deletes its rows; until then no L2 MSR rebuild runs at all (charter R1).

### 6.5 · L0 waves and full-layer rebuilds (D4)

- **Every L0 wave:** pre-wave `pg_dump --format=custom` of each affected L0 table to `$SUVARNA_HOME/evidence/<qid>/`,
  verified by `pg_restore --list` and row counts against the fingerprint (fail closed and park if it cannot be made or
  verified; after D6 some tables have column-level grants, which can make the dump fail); a measured impact statement
  (L0 assets whose output changed; per other chart, the downstream assets flipped to stale, or the computed closure if a
  global run does not propagate; E5.3 verifies once which case holds); dispatch by the native; a post-wave row-level
  diff on the natural keys. Reversal: hold; the native runs a surgical revert migration generated from the diff
  (preferred) or a restore. The dump is purged after the level certifies and the diff is filed.
- **Full-layer rebuild** (layer close, plan §1.2): one `action=rebuild, clear_before=false` run; `scope=layer` for L0,
  L1, L2, L4, L5, an asset-list run over L3 minus `FAMILY_ASSETS.json` for L3; for L1+ a from-scratch rebuild for the
  chart; for L0 proven by fingerprint equality or an explained diff; for L2 only after F-3 and F3.FK.
- **L0 is four native dispatches** (levels 0–3; `bg_concordance` at level 3 is split out of W1 and parked like the
  others): B.L0.0…B.L0.3, batched by the Steward.

## §7 · Autonomy and its limits

The charter (`SUVARNA_AUTONOMY_CHARTER_v1_0.md`: v1.2 approved by N-19 and CHARTER-AMEND-A-C; the v1.3–v1.4 changes are confirmed with N-1) supersedes this summary; where they differ, the charter wins.

### 7.1 · Granted — the swarm decides alone, and logs it before acting

- Dispatch, sequence, re-sequence and cancel queue items.
- Choose model and effort within the §3.1 table and the caps (no budget ceiling, N-15).
- Accept a gate verdict and fold it.
- Retry once; open diagnosis items.
- Record a gate `N/A` only as the census computes it from a declared registry rule (D3).
- Merge accepted packets to `suvarna/trunk`; open PRs to `main` for accepted groups.
- Dispatch orchestrator builds in dependency order, as the builder identity, for the canonical chart (L0 waves: the native dispatches).

### 7.2 · Reserved — park for the native, and continue with everything else

- Everything on the plan's decision list (§8 of the plan).
- Any change to the frozen writer contract (CLAUDE.md §N.2).
- Any destructive operation: needs a verified snapshot and a recorded native approval (charter R3).
- Any scope beyond the canonical chart.
- Retiring an asset, or changing an asset's output in a way not in its approved brief.
- Exceeding a budget ceiling, if the native sets one (none set, N-15).
- Anything the charter does not clearly grant.

### 7.3 · Prohibited — refuse, never park

- Reading, moving or logging credentials.
- Writing production data outside migrations and the orchestrator.
- Weakening, skipping or reinterpreting a gate.
- Closing a gap on anything other than PASS or a registry-computed N/A.
- Committing to `main` directly.
- Running any agent with permission checks bypassed.

### 7.4 · Native decisions without stalls

- **Lead time.** The Steward requests a decision as soon as it is foreseeable, not when it is needed.
- **Batching.** Decisions are sent in batches at natural join points, each with a recommendation.
- **Continuing.** While a decision is pending, only the items that depend on it wait.

## §8 · Environment

The Monitor checks these before any dispatch, and every 5 minutes while work runs (`--watch 300`;
`python -m suvarna_tracker.monitor`; exit 0 ok, 1 warn, 2 block). **Before N-25 is decided the Monitor exits 0 or 1,
and 1 only from `isolation`**; no launch step requires every check `ok` before N-25:

- **Database proxy** listening on 5433. Restart if not.
- **Read-only credential file** present at `~/.config/suvarna/pgenv.sh`, owner-only (N-20): missing is a block, too
  open a warn. If missing, pause and park; never recreate it, never call `gcloud` per command.
- **Read-only by privilege** (`credential_readonly`, D6): the login is `suvarna_reader`, its role default is read-only,
  and it has no write path by effective privilege. Anything else blocks. D6 is applied (2026-09-29); the check reads ok.
- **Builder scope** (`builder_scope`, D1, added by E7.3): measured through `suvarna-build --preflight`, whose
  authenticated answer carries the builder's own `{principal_id, role, status, grants}` as the server sees it; the
  reader cannot measure it (D6 withholds `chart_grants.permission` and `profiles`). The account is `guest` and
  `active`, its grants are exactly `{(482012f1, 'build')}`, and it matches the provisioning record
  `run/builder_identity.json` (E7.2). **Before E7.2 writes `builder_identity.json` it reads `warn`** (never `ok`: nothing
  has been measured), so E7.3 cannot read done early. Once the file exists, anything else, or a preflight that fails,
  blocks.
- **Isolation** (`isolation`, L.16a, §2.4): the process runs as the expected user; the paths §2.4 lists are unreadable;
  the decisions log is not writable (under N-25); the settings files in every scope match their recorded hashes.
  **Until N-25 is decided it reads `warn`** (the expected user and paths are not yet defined); after it, `ok` when every
  check holds under the decided outcome (the separate user, or the fallback hardening), anything else blocks.
- **Decision writers** (`decision_writers`): any `decided` line in the log whose writer is not `strategic-suvarna`
  blocks.
- **Power.** On AC power, with sleep prevented. On battery the Monitor warns; below 50% it blocks and dispatch pauses.
  A production build treats a power warn as a failed precondition (charter §6.7).
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

- **All state lives in files:** the queues, the decisions log (`$SUVARNA_HOME/run/DECISIONS.jsonl`), the register, the ledgers. None of it lives in an agent's memory.
- **Every packet is idempotent** and commits its progress, so a crash loses at most one step.
- **The Conductor can be restarted at any time** and resumes from its queue in `hq/00_ARCHITECTURE/control/suvarna/state/` and the decisions log; every pass is stateless (§5.1, §5.5).
- **A daily digest** goes to the native: what finished, what is parked, what is next, spend.
- **The event log is append-only** and survives any crash; the tracker rebuilds its whole view from it on restart.

## §11 · Real-time visibility — the tracker

The native asked for a live view of the whole campaign: the plan, what runs in parallel and what in sequence, where we are, what is next, what is done, and useful measures, updated the moment things change. This section makes that a requirement on every role, not an afterthought.

### 11.1 · One source of truth

| Piece | Where | What it holds |
|---|---|---|
| Plan model | `00_ARCHITECTURE/control/suvarna/plan_model.json` | tracks (parallel, sequential or hybrid), items, dependencies, decisions, and how each item is proven done |
| Event log | `$SUVARNA_HOME/run/EVENTS.jsonl` | one line per state change, append-only |
| Decisions log | `$SUVARNA_HOME/run/DECISIONS.jsonl` | the native's decisions (§12.10); every `done_by: decision` item reads it: `decided` → done, `delegated` → waiting; a disagreeing decision event shows as a conflict |
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
python -m suvarna_tracker.decide --id <id> --state decided --source "<native's words, where, when>" --detail <text> --writer strategic-suvarna   # Strategic Suvarṇa only, native present
python -m suvarna_tracker.emit heartbeat --actor conductor --detail "<what it is doing>"
python -m suvarna_tracker.emit metric --actor scribe --name <name> --value <number>
```

| Role | Emits |
|---|---|
| Conductor | `running` on dispatch; a heartbeat each loop pass |
| Builder, Analyst | step events (e.g. census, instance, briefs, designs) and progress as they go |
| Gate reviewer | `review`, then the verdict: back to `running`, or accepted |
| Scribe | `done` with evidence, at fold |
| Steward | decision `requested` event when foreseen; when the native answers in its session, a `note` with the native's words for Strategic Suvarṇa to record (never a log line) |
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

### 11.7 · Detector types added for plan v1.3 (built by L.13)

Rule for all of them: an expected input that does not exist yet reads **pending**; a detector that cannot measure, or
a spec left empty for a later item to pin (`pinned_by`), reads **unknown**. Neither is ever done. v1.4 changes the
semantics of the deploy checks and adds three types (the code is listed in REVIEW_PASS2_DISPOSITION as CODE items).

| Type | Done when |
|---|---|
| `prs_merged` | every listed PR is merged; PRs named by `head_refs` are resolved with `gh pr list --head <ref> --base main --state all` |
| `main_has_files` | every listed path exists on `origin/main` |
| `scorecard_pass` | the scorecard at the path on the ref (schema in Track E §5) has `tests[T].verdict == "PASS"` for every listed test, its `generator` equals the spec's pinned `generator` (never the path the scorecard names for itself), its `generator_sha256` equals that committed file's hash, and its `inspector_commit` is an ancestor of the ref |
| `migrations_applied` | each number has its row in `_migrations_applied` (read-only) |
| `register_rows_state` | each row's state is one of the listed states; a `DEFERRED` row counts only if the spec's `deferred_withholding_entry` is in the withholding list at the Nikaṣa ref and the spec's `deferred_pr` (a number, or a head ref `gh pr view` resolves) is merged (E4.2r) |
| `register_freeze_clean` | every row in `expect_rows` is present (a missing row is an error) and every BLOCKS_FREEZE row is CLOSED or DONE (rows in `allow_deferred` may be DEFERRED) |
| `monitor_check_ok` | the named check reads `ok` in `python -m suvarna_tracker.monitor --once --json`, run by the detector itself (`run/monitor_state.json` keeps only the non-ok list) |
| `deployed_contains` | after a fetch, every listed PR's merge commit is an ancestor (`git merge-base --is-ancestor`) of the running commit from `~/.config/suvarna/bin/suvarna-build --preflight` (`job_sha` for `component: job`, `deployed_sha` for `web`) |
| `wave_deployed` | the wave's landing PR (recorded by E5.3 in `evidence/<wave>/LANDING.json`) is merged and its merge commit is an ancestor of the running job commit |
| `assets_elevated` | every asset of the named set in `00_ARCHITECTURE/control/FAMILY_ASSETS.json` on `origin/main` is ELEVATED by the exact function (unknown before E6.3t) |
| `registry_coverage` | `00_ARCHITECTURE/control/registry_coverage_report.json` on `origin/main` (written by E6.5's `asset_census.py --registry-check`) carries `registry_revision`, an empty `uncovered_required_criteria` list and `covered_cells`; a missing key is an error, never a pass |
| `fk_no_cascade` | the foreign keys into the named table match the spec's `target`: `no_fk` = none at all; `set_null` = every one `confdeltype = 'n'`. `CASCADE`, `RESTRICT` and `NO ACTION` (`c`, `r`, `a`) read pending, since a restricting key refuses the L2 delete-then-insert (read-only `pg_constraint` query as the reader); F3.FK |
| `acks_from` | the event log holds a `note` from each named actor whose detail starts with the named marker (e.g. `ACK FI-8`) |
| `main_protected` | `gh api repos/{owner}/{repo}/rulesets` (or branch protection) shows `main` requiring a pull request with an approving review, bypass limited to the named actor |
| `ledger_no_open_gap_on` | the gap ledger has no open `kind: gap` row on a criterion with the listed prefixes |

`levels_elevated` also gains `exclude: family_set` (read from `FAMILY_ASSETS.json` once E6.3 lands it) and `level_map`
(wave membership from the J1-frozen `LEVEL_MAP.json` on `origin/main`, pending until it exists; never the live
registry), and reads unknown until E6.3t. `level_map` and `target` are v1.4.1 spec keys (CODE items, review pass 3).

## §12 · Operating conventions (settled 2026-09-29; revised in v1.3)

Settled in Strategic Suvarṇa from the role-instruction review. Role files cite these by number.

| # | Question | Convention |
|---|---|---|
| 12.1 | How a queue item reaches the tracker | Each queue line carries **`plan_item`**, the `plan_model.json` id it rolls up to. Events name `plan_item` in `--item` and the queue id in `--step`, so a packet's events never change the whole item's status. Only the Conductor emits whole-item `running`/`blocked`/`parked`; only the Scribe emits `done`, and never on an item a detector or a native decision closes. |
| 12.2 | Ids and branches | Queue id: `<plan_item>-<kind>-<nnn>` (e.g. `A.L2-brief-014`). Lane branch: `suvarna/lane/<queue id>`. Lane worktree: `$SUVARNA_HOME/lanes/<queue id>`. **One base rule:** every lane branches from `suvarna/trunk` (= `main` plus accepted packets; the Conductor merges `origin/main` into it by a merge commit every pass). `campaign/nikasha-test` and `campaign/nirmana-engine` are never a base for anything bound for `main`: they sit on `l3/kala-layer-briefs` and carry ~190 foreign commits, Saṅgam family code among them; read them with `git show` or cherry-pick with `-x`. **The one exception:** a fold lane before the E4.3 cut-over is cut from `origin/campaign/nikasha-test` (§12.7) and is never PR-bound. **Landing:** a PR to `main` comes from `suvarna/land/<group>`, cut from `origin/main`, with the group's accepted lane branches merged into it; PR #2736 is not retargeted. Never edit `/Users/Dev/madhav-nikasha` or `/Users/Dev/madhav-engine` directly. |
| 12.3 | One Conductor or two | **One per session, one queue per Conductor**: `QUEUE.jsonl` (Exec Suvarṇa) and `QUEUE_ENGINE.jsonl` (Nikaṣa Engine), both in `hq/00_ARCHITECTURE/control/suvarna/state/`. Each has one writer. |
| 12.4 | Leases | The project's existing mechanism: a row in `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on branch `origin/campaign-coordination`, claimed before and released after. Lease id: `SUVARNA-<queue id>`. The L3 family assets are never leased by Suvarṇa (N-17, charter R8). |
| 12.5 | Migration numbers | **The Suvarṇa range, proposed (N-27): 1200–1299**, recorded as a reservation row on the coordination branch (§12.4). **Why a range is needed:** main's committed `.claude/settings.json` (L3 Kāla #2718) denies `Edit(platform/migrations/…)` on `[0-9][0-9][0-9]_*`, `10[0-6][0-9]_*`, `1070_*`, `11[2-9][0-9]_*`, `1[2-9][0-9][0-9]_*` and `ws2_*` for every session in the repo, and a deny beats the `--settings` allow, so only L3's 1071–1119 is writable. **Evidence 1200–1299 is free (2026-09-30):** no file numbered 1200 or above on `origin/main` or on any of the 2,220 local and remote refs, in either migration folder; none in the 22 open PRs; 0 of the 883 `_migrations_applied` rows (read-only, as `suvarna_reader`); the highest applied is 1150 (L3 Gochara). **The amendment** (E0.1): one small PR to `main`, coordinated with the L3 Kāla owner and authored by the native or that owner (no agent may edit `.claude/settings.json`), replacing `Edit(platform/migrations/1[2-9][0-9][0-9]_*)` by `Edit(platform/migrations/1[3-9][0-9][0-9]_*)`. The deny does not cover `platform/supabase/migrations/`, which `migrate.ts` also applies; Suvarṇa never writes there to step around it (charter P13). **Within the range**, one number at a time: after a fresh `origin/main` and open-PR sweep, the next free number; commit a placeholder migration file **on the lane branch** and push it at once; record the number in the queue line and on the coordination branch; never on `main` (charter P9); never reuse a number. N-26 renumbers 1094–1096 into the range. Until E0.1 is merged no Suvarṇa lane writes a migration (E7.1, E3.2 wait). |
| 12.6 | Where committed outputs live | On the lane branch, merged to `suvarna/trunk`: layer instances `00_ARCHITECTURE/briefs/suvarna/layers/<Lx>/`; asset briefs `…/layers/<Lx>/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md`; fix designs `…/layers/<Lx>/designs/`; gate reviews `00_ARCHITECTURE/briefs/suvarna/reviews/<queue id>_REVIEW_<n>.md` (committed on the packet's lane branch and merged with the packet, for audit; `<n>` is the review round). This is the one review path; raw review scratch and other evidence stay in `$SUVARNA_HOME/evidence/<queue id>/` (not committed). |
| 12.7 | Register and ledger folds before landing | **Before the E4.3 cut-over** only the Nikaṣa Engine Scribe folds, on a fold lane cut from `origin/campaign/nikasha-test`; the Nikaṣa Engine Conductor then pushes it as a fast-forward: `git push origin suvarna/lane/<qid>:campaign/nikasha-test` (never forced; a rejected push means re-cut from the new tip and redo the fold). The tracker reads `NIKASHA_REF=origin/campaign/nikasha-test` (fetched first), so the fold is visible at once; `/Users/Dev/madhav-nikasha` is never touched. **No ledger emits before E5.2 lands**; pre-E5.2 folds change register rows only. Exec Suvarṇa's Scribe files a fold request (`$SUVARNA_HOME/evidence/<qid>/FOLD_REQUEST.md` and a `note`). **Cut-over (E4.3):** folds stop at a named cut; the ledgers land on `main` last; line count and md5 of both ledgers and the register are equal across the old and new locations (evidence); Strategic Suvarṇa re-points `NIKASHA_REF` to `origin/suvarna/trunk` in one step; folds resume on lanes from `suvarna/trunk`. |
| 12.8 | Stall detection and spend | **The Conductor** does both: an agent with no event and no commit for 10 minutes is stalled (restart from its last commit); after every agent run it emits `metric` events for tokens used, by role and stage (N-15: reported, not capped). The Monitor stays an environment checker; the Conductor runs `monitor --once` before each dispatch and pauses on exit 2. |
| 12.9 | Which assets are "L2 MSR" (charter R1, F-3) | **The L2 writers** whose rebuild replaces rows in `bodha_msr_signals`. Measured 2026-09-29: seven writers have it as their registry target (`bo_sudarshana`, `bo_vargottama_dhana` in W0; `bo_special_lagna`, `bo_arudha`, `bo_nakshatra_semantic` in W1; `bo_laksana`, `bo_laksana_rerank` in W2); A.L2i confirms the full set from the writers. **The cascade's victims** are the tables with an `ON DELETE CASCADE` key into it: `kala_convergence` (family), `kala_darshana`, `kala_bhavishya`, `kala_activation`, `kala_obstruction`, `bodha_signal_embeddings`, `bodha_contradictions` (two keys). No MSR rebuild runs until F-3 is decided and `fk_no_cascade` (F3.FK) reads done. |
| 12.10 | Who writes `DECISIONS.jsonl` | **The authoritative log is `$SUVARNA_HOME/run/DECISIONS.jsonl`, outside git**, appended only through `python -m suvarna_tracker.decide` (exclusive file lock; every field required; the latest line per id wins), **only by Strategic Suvarṇa, with the native present** (`--writer strategic-suvarna`). No swarm role writes to it (charter P14); the Steward requests and parks. Under N-25 the file is owned by the native's account and read-only to the swarm. Only the native's own words with their source (where, when). The mirror (`hq/…/state/DECISIONS.jsonl`) has one writer (Strategic Suvarṇa, `decide --mirror-to`, committed under the hq lock) on one branch (`suvarna/hq`); it is never changed on `strategy/suvarna-plan`. The tracker and every precondition read the log itself; the Monitor blocks on a `decided` line by any other writer. Nothing else is a decision (charter §2, P10). |
| 12.11 | Daily digest | Written by the Steward to `hq/…/state/DIGEST_<date>.md` (a new file: `hq_commit --add-new`, §12.12) and announced as a tracker `note`; it lists every new decision line for the native to confirm. The native reads it from the dashboard. |
| 12.12 | Committing `suvarna/hq` state; where the tools run | Each queue's writer commits its own file on `suvarna/hq` at the end of every Conductor pass, only through `python3 -m suvarna_tracker.hq_commit --paths <path…> -m "<msg>"` (the hq lock `$SUVARNA_HOME/run/locks/hq.lock`; explicit paths only; `--add-new` for a new file such as a digest, CODE item). Plan revisions reach hq from `strategy/suvarna-plan` by a merge commit (`git merge --no-edit origin/strategy/suvarna-plan`), never fast-forward-only and never a rebase. **The tracker and the Monitor run from the hq worktree**, i.e. from committed code; Strategic Suvarṇa restarts them after each plan merge (L.17). **Tracker code has one owner:** it is changed only on `strategy/suvarna-plan` (by Strategic Suvarṇa, or a lane PR to that branch, e.g. E7.3) and reaches hq by the merge. |
| 12.13 | Which checkout the census runs from | `/Users/Dev/madhav-nikasha` (read-only) until E4.1 lands the inspector on `main`; `suvarna/trunk` after. Always through `census_run` (§12.15). The census records the inspector's commit with its output. A level wave censuses only its assets once E1.9 adds `--assets`. |
| 12.14 | Gating measurements | **Provisional censuses** (before J1) are checked by script, not by an Opus review: exit code (0 clean · 2 FAIL present · 3 PARTIAL/NO_DETECTOR/ERRORED present · 4 unknown · 5 script error; 4 and 5 are unmeasured · 75 census lock held), the inspector's commit, per-layer row counts. (The inspector's docstring disagrees with its code on code 3: an E1.2 row.) **Certifying censuses** (after J1) get a gate review before the step is done, at fold. |
| 12.15 | One census at a time | Every census, in every session and in the family sessions, runs through the validated wrapper `python3 -m suvarna_tracker.census_run --layer <Lx> --out <absolute path> --wait 900 --emit --actor <role>` (review pass 3 B6). It takes the exclusive census lock `$SUVARNA_HOME/run/locks/census.lock` itself (`--wait` seconds, default 0; exit 75 means another census holds it: wait or re-queue), sources `~/.config/suvarna/pgenv.sh`, builds and runs only `asset_census.py --layer <Lx> --out <file>` from the census checkout (today `/Users/Dev/madhav-nikasha`; the switch to `suvarna/trunk` at E4.1, §12.13, is a CODE item), and refuses (exit 2) a relative `--out` or one with shell metacharacters; create the evidence folder first (`mkdir -p`). `census_lock -- <command>` no longer wraps an arbitrary command: it would have bypassed every Bash deny. |
| 12.16 | What a certification record carries | The asset, gate or addition, verdict, the criterion and its detector (never `NONE` for a PASS), the census run id, the run's job image tag, the writer file hashes, the upstream certification ids, and the row-set fingerprint. E5.5 invalidates a record when any of these no longer matches. |

**Charter points** (the native's): ruled 2026-09-29 as charter v1.2 amendments A–C: L0's global build under G13; per-layer idempotency in G4; pre-wave fingerprints and a reserved undo for normal level waves (charter §6.7). Charter v1.3 folds D1–D5 (builder identity and native L0 dispatch; family staleness exemption and hand-back; registry-computed N/A; L0 dump and diff; watchdog and no bypass). Charter v1.4 folds review pass 2 (only Strategic Suvarṇa writes decisions; F-3 plus F3.FK; ancestry; landing branches; §13 isolation, proposed pending N-25).
