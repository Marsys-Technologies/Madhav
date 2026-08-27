---
artifact: PARIPRASHNA_STREAM_EXECUTION_HARNESS
version: 1.0
status: CURRENT — the overnight, fully-autonomous execution harness for the six
  P3 streams. Governs HOW the six streams run unattended (Claude CLI mechanics,
  supervise/wake/resume, model+fallback matrix, commit/merge/deploy/cleanup
  cadence, and the hard safety rails that make no-human-gates responsible). Sits
  under AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md (§8 stream model, §11 swarm/models)
  and the six frozen charters; it operationalizes them for unattended running.
date: 2026-08-28
authorized_by: >
  Native directive, strategy session 2026-08-28 (recorded §1): run all six P3
  streams in parallel, in separate sessions, overnight, fully autonomous, no
  human gates; implement via the Claude CLI with auto-resume so there is no idle
  time — if a session stops, something wakes it and it resumes from where it
  stopped; parallelize within and across streams via worktrees; commit / merge /
  push / deploy and keep production in sync with main at appropriate points, then
  clean up at the end; agentic swarm per stream; balanced model+effort per role
  with no stall from any single agent/model being unavailable.
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/SESSION_A_STREAM_KICKOFF_PROMPTS_v2_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S1_v1_0.md
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/launch_conductor.sh
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/_supervisor.sh
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/resume.sh
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/halt_handler.sh
  - 00_ARCHITECTURE/autonomy/CHARTER_v2_0.md
changelog:
  - "1.0 (2026-08-28, Claude Code / Fable): initial harness — Claude-CLI overnight
    autonomy mechanics mirrored from the proven build_orchestrator conductor,
    model+fallback matrix, progress-based wake, cadence, and safety rails."
---

# Paripraśna — Stream Execution Harness v1.0

## 0 — What this is, and the one thing to internalize first

This document makes the six P3 streams runnable **unattended, overnight, with no
human gates**, and makes them **wake themselves and resume from where they
stopped** so there is no idle time. It does not change WHAT each stream tests
(the test plan v2.1 + the six charters own that) or WHETHER they may run (CG-2 is
CLOSED; P2→P3 is resolved; they may). It owns the *operational envelope*.

**The one load-bearing insight, learned the hard way this campaign:** durable
state lives OUTSIDE the Claude session — in the accepted tracker's append-only
ledger, in each stream's git branch, and in EDIR_V3 — never inside a chat
session's memory. Session A proved this by resuming cleanly three times across
three cold restarts, each time *re-deriving* its true position from live state
rather than trusting a handoff's text. Every mechanism below is built on that:
a stream that is killed, crashes, stalls, or is woken by the watchdog does not
"continue a conversation" — it **re-opens, re-reads live state, and resumes at
the exact next unearned step.** This is why the harness is robust to the Claude
CLI losing a session id, to a machine reboot, to a rate-limit, and to the
overnight gaps that sank the earlier Nirmāṇa fleet.

## 1 — The native directive (verbatim intent, 2026-08-28)

Run all six streams in parallel as separate sessions, overnight, fully
autonomous, no human gates. Implement with the Claude CLI using appropriate
features so there is no idle time: if execution stops, something wakes it and it
resumes from where it stopped. Parallelize within streams and across streams;
leverage worktrees for isolation wherever appropriate. At appropriate points,
commit, merge, push to GitHub, deploy, and keep production in sync with main;
clean up at the very end. Use an agentic swarm in each stream. Ensure no stall
from a particular agent/model being unavailable — assign appropriate models and
effort per role, balanced: neither all-frontier-expensive nor all-cheapest.

## 2 — Topology: how six streams run at once

```
                    fleet_launch.sh   (one command; the native runs this once)
                          │
        ┌────────┬────────┼────────┬────────┬────────┐
     supervisor supervisor …      (one _stream_supervisor.sh per stream S1..S6)
      (S1)       (S2)                        (S6)
        │          │                           │
   stream_run.sh  …    (crash-circuit-breaker respawn loop wraps each)
        │
   claude --dangerously-skip-permissions --append-system-prompt <STREAM PROMPT>
          --print --output-format=stream-json --model <resolved-primary>
          (launched in that stream's OWN worktree; nohup; pidfile; heartbeat)
        │
   internal swarm  (Native Surrogate, verifiers, finders, browser drivers,
                    mechanical lanes — spawned by the stream via the Agent tool,
                    optionally in sub-worktrees for parallel remediation lanes)

   fleet_watchdog.sh   (launchd, every 5 min) — the WAKE mechanism:
     for each stream, reads the tracker's PROGRESS liveness (not process-alive),
     re-invokes any stream whose supervisor died OR whose tracker progress has
     been flat past its stall budget. This is the "no idle time / wake on stop."
```

Six streams, six worktrees, six branches, six tracker `lead-s{1..6}` actors, one
shared merge queue, one shared accepted tracker (the coordination substrate), one
watchdog. Within a stream, the swarm parallelizes freely and may cut *sub*-
worktrees for remediation lanes that would otherwise collide on files.

### 2.1 Worktree isolation (the `--dangerously-skip-permissions` containment)

No-human-gates means each stream runs with `--dangerously-skip-permissions`.
That is only responsible because the blast radius is contained by construction:

- Each stream works ONLY in `.clone/worktrees/pariprashna-v3-s{N}/` on branch
  `pariprashna/v3-s{N}-<slug>`, cut fresh from the frozen baseline SHA.
- `must_not_touch` (declared at each stream's open) forbids: the shared checkout
  at repo root, `campaign/nirmana-autonomous`, any other stream's worktree, any
  other stream's file territory (charter §territory), and the accepted tracker's
  SQLite file (writes go only through the authenticated HTTP/CLI path).
- A stream that needs to touch another stream's territory FILES a cross-stream
  referral (elevation §8.3) — it never edits across the boundary.
- Sub-worktrees a stream cuts for its own parallel lanes live under
  `.clone/worktrees/pariprashna-v3-s{N}-lane-<x>/` and merge back to the stream
  branch, never to main directly.

## 3 — Claude CLI mechanics (mirrored from the proven conductor)

The `build_orchestrator` conductor already runs Claude Code headless and
autonomous in this exact repo; this harness reuses its shape rather than
inventing one. Per-stream launch (inside `stream_run.sh`):

```bash
nohup env CLAUDE_CODE_MAX_OUTPUT_TOKENS=200000 \
  claude --dangerously-skip-permissions \
    --model "$RESOLVED_MODEL" \
    --append-system-prompt "$STREAM_PROMPT_BODY" \
    --print --output-format=stream-json \
    < /dev/null \
    > "$STREAM_LOG" 2>&1 &
echo $! > "$STREAM_PIDFILE"
```

- `--dangerously-skip-permissions` — no human gates (contained per §2.1).
- `--append-system-prompt` — the stream's elevated prompt (from
  `SESSION_A_STREAM_KICKOFF_PROMPTS_v2_0.md`) is injected as system context.
- `--print --output-format=stream-json` — headless, parseable, logged.
- `--model "$RESOLVED_MODEL"` — resolved from the fallback matrix (§5) at launch.
- `nohup … &` + pidfile — survives terminal close; supervisable.
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=200000` — long autonomous runs.

The internal swarm is spawned by the running stream via its Agent tool (subagents
with per-role model overrides, §5), NOT by launching more top-level `claude`
processes — the stream is the orchestrator of its own swarm.

## 4 — Wake & resume: no idle time, resume-from-stop

Two independent layers guarantee liveness; either alone would leave a gap the
Nirmāṇa fleet's 4-hour outage proved is real.

### 4.1 Per-stream supervisor (crash recovery, seconds)

`_stream_supervisor.sh S{N}` wraps `stream_run.sh` in the proven respawn loop
with a crash circuit breaker (mirrors `data_progress/_supervisor.sh`):

- If `stream_run.sh` exits non-zero, respawn after 5s.
- Track crashes; **5 crashes in 60s → stop respawning that stream, call
  `halt_handler.sh S{N} "crash-loop"`, mark it BLOCKED on the tracker, and let
  the other five streams continue.** Never thrash.
- A clean exit (stream reported its own completion + session-close event) ends
  the supervisor for that stream normally.

### 4.2 Fleet watchdog (stall recovery, minutes) — the real "wake it up"

`fleet_watchdog.sh`, run by launchd every 5 minutes, is the mechanism that wakes
a stopped or stalled stream. **It keys on PROGRESS, not process-alive** — the
single most important lesson from the Nirmāṇa outage, where processes were alive
but making no progress and nothing noticed for four hours. Per stream:

1. Read the stream's liveness from the accepted tracker (the freshness machinery
   we hardened in the tracker preconditions — its per-source budgets and the
   completed-session-liveness fix are exactly this).
2. If the supervisor process is dead → relaunch `_stream_supervisor.sh S{N}`.
3. If the supervisor is alive but the stream's tracker progress (last
   `work_started`/`work_accepted`/finding/decision event for `lead-s{N}`) has not
   advanced within the stream's **stall budget** (default 25 min; a browser or
   LIVE-deploy lane may declare a longer budget in its charter) → the stream is
   stalled, not working: kill its pid, let the supervisor respawn it. The fresh
   process re-derives state and resumes (§4.3).
4. If a stream is BLOCKED (self-paused on the §3.2 residue, or crash-looped) → do
   NOT relaunch; record it, leave it for the native's morning review, keep the
   others running. A blocked stream is an honest stop, not a failure to paper over.

The watchdog itself is supervised by launchd (`KeepAlive`), so the waker cannot
itself silently die — the one thing a waker must never do.

### 4.3 Resume-from-stop (why a cold restart lands exactly where it left off)

Every stream prompt's first act on EVERY start (cold launch or watchdog respawn
alike) is the re-derive-state ritual Session A proved:

1. Confirm worktree/branch intact; read the charter + this harness + elevation.
2. Read live state: the tracker projection (what this stream has already
   `work_started`/accepted), its own branch's commits and open PRs, its EDIR_V3
   entries, any WIP commit on its branch.
3. Compute the next unearned step from that state — never from a remembered
   position — and resume there.

Because progress is durable (tracker events + git + EDIR) and the prompt
re-derives rather than trusts, a stream can be killed at any instant and lose at
most the in-flight step, which it re-attempts idempotently. No `--resume`
session-id dependency; external durable state is the resume key.

## 5 — Balanced model + effort + fallback matrix (no single-model stall)

Elevation §11.1 sets the balanced primary assignment; this adds the **fallback
chain per role** so no single model's unavailability (rate limit, outage) stalls
a stream. The hard rail: **a judgment or verification role never downshifts below
Sonnet.** A security fix "verified" by a cheap model is an unearned green (§N.8) —
if the required tier is unavailable, that lane self-pauses rather than fakes it.

| Role | Primary | Fallback chain | Floor (below which the lane pauses, not degrades) |
|---|---|---|---|
| Stream main loop — S3, S5 | Opus / high | Opus → Sonnet/high | Sonnet (never Haiku for these two) |
| Stream main loop — S1, S2, S4, S6 | Sonnet / med-high | Sonnet → Opus/med (up-shift ok) | Sonnet |
| Native Surrogate (per stream) | Opus / high | Opus → Sonnet/high | Sonnet |
| Independent Verifier — security-class & gate closures | Opus / high | Opus → Sonnet/high | **Sonnet — hard floor; if both unavailable, the verification lane self-pauses** |
| Independent Verifier — default | Sonnet / high | Sonnet → Opus/high | Sonnet |
| Finder / Investigator | Sonnet / med | Sonnet → Haiku (mechanical parts only) | Sonnet for judgment; Haiku ok for pure tracing |
| Browser journey driver | Sonnet / med | Sonnet → Haiku (replay of known steps only) | Sonnet for novel journeys |
| Adversarial refuter panel | Opus / high | Opus → Sonnet/high (widen panel to compensate) | Sonnet |
| Mechanical (census, filing, screenshots, grep) | Haiku 4.5 / low | Haiku → Sonnet/low (up-shift ok) | none — cheapest is fine |
| Tracker Ops (event emission) | Haiku 4.5 / low | Haiku → Sonnet/low | none |

Fallback is chosen at spawn time by probing model availability; a lane that hits
its floor with no available model emits a `model_floor_unavailable` tracker event
and self-pauses that lane only (the stream keeps its other lanes running). This
is the "no stall from a particular agent being unavailable" guarantee: work
re-routes to an available appropriate model, and only genuinely unrunnable
high-stakes verification pauses — it is never silently downgraded.

Concurrency: default 8 concurrent subagents per stream; S4 may burst to 12 during
11-stage fan-out. Fleet-wide soft cap so six streams don't exhaust the machine:
the watchdog throttles new subagent bursts if system load is pathological
(favor steady progress over thrash).

## 6 — Cadence: commit, merge, push, deploy, sync, cleanup

### 6.1 Continuous (within a stream, all night)
- **Commit** WIP to the stream branch at every meaningful step — never to main.
- **Push** the stream branch to origin continuously (so state survives machine loss).
- **Event** every step to the tracker (progress = the durable resume key).

### 6.2 Merge to main (gated, autonomous, all night)
A stream may auto-merge a change ONLY when ALL hold:
1. Its **independent verifier** (distinct actor+model, §5) accepted it — merged ≠ fixed.
2. It touches **only that stream's own file territory** (else → referral, no merge).
3. **Full CI is green** (the merge-queue re-checks; skipped credential-gated jobs
   are disclosed, never counted as passes — the campaign's standing rule).
4. It **weakens no** test / CI / auth / safety / sandbox / watchdog check (autonomy
   charter §hard-constraint). Any diff that loosens an authorization check, a CI
   gate, or a guard is an automatic STOP, not a merge.

Security-class changes (the B-001/B-007/B-008 family) carry two extra gates:
5. **Demonstrated-can-fail**: a test that is RED on the pre-fix code and GREEN
   after — the vulnerability proven real and the fix proven to close it.
6. **Additive authorization only**: a security merge may ADD a check, never
   remove or loosen one, and must be **adversarially** verified (a refuter that
   tries to bypass the fix, distinct actor+model ≥ Sonnet). Anything failing this
   self-pauses for the native — a wrong security fix merged autonomously overnight
   is exactly the harm B-007/B-008 showed is possible, so this gate is absolute.

Merge is via the merge queue (`gh pr merge <n>`; never `--squash --delete-branch`
together under merge-queue mode — a known repo quirk).

### 6.3 Deploy & production sync (gated, verified, reversible — NOT a 3am free-for-all)
Production deployment is the one action that is **not** left to per-stream
overnight autonomy without a hard gate, because a bad deploy of a live-auth change
is unrecoverable in a way a bad merge is not (a merge can be reverted on main; a
destructive prod migration cannot un-delete data). The rule:

- Streams LAND merges to main overnight (§6.2). They do **not** each push
  production deploys independently at 3am.
- A single **deploy-sync checkpoint** runs the production deploy through the
  existing pipeline (`migrate.ts` + deploy), then proves `deployed_revision ==
  origin/main HEAD`, runs the `deploy_and_smoke` battery, and confirms a rollback
  path is ready — mirroring the proven `scripts/deploy_and_smoke.sh` +
  `gate_check.sh` pattern. This checkpoint runs either at a scheduled fleet-quiesce
  point or at the convergence session (Session C), **never per-stream mid-night**.
- S5 (security) is the one stream that legitimately needs a LIVE deployed re-proof
  of an auth fix: it does so against the deploy-sync checkpoint's verified
  revision, and if that revision is still stale (e.g. blocked on the unrelated
  Nirmāṇa deploy pipeline, as it is right now behind `cafa894ee`), it does NOT
  fabricate a LIVE pass — it records the honest gap and its Surrogate escalates,
  exactly as its charter already instructs.

The native's "production in sync with main" is honored precisely: sync happens,
verified (deployed==main), reversible, at a controlled checkpoint — not as an
uncontrolled per-stream overnight prod push.

### 6.4 Cleanup (end of fleet)
When all six streams have closed (or blocked-and-recorded) and the deploy-sync
checkpoint is green: delete merged stream branches, remove stream + sub-lane
worktrees, disposition ARCHIVE-class branches, unload the watchdog + supervisor
launchd jobs, tear down pidfiles/logs into an archive, and emit the fleet
session-close. The convergence session (Session C, elevation §9) picks up
integration/regression/CG-3/CG-4 from there.

## 7 — Hard safety rails for no-human-gates overnight (non-negotiable)

These are the conditions under which unattended `--dangerously-skip-permissions`
autonomy is responsible. Every one is enforced by the harness or the stream
prompt, not left to good behavior:

1. **Containment** — worktree isolation + `must_not_touch` + tracker-only writes (§2.1).
2. **No weakening** — any diff loosening a test/CI/auth/safety/sandbox/watchdog check → STOP (§6.2.4).
3. **Security merges are additive + adversarially verified + demonstrated-can-fail** (§6.2.5-6).
4. **Prod deploy is gated, verified (deployed==main), reversible, at a checkpoint** (§6.3).
5. **The §3.2 residue self-pauses**: the native's real chart `482012f1`, any new
   secret, or any irreversible-ambiguity → that stream halts (BLOCKED), the other
   five continue, the native is surfaced it at morning review. Never improvise
   past it (this rail already fired correctly on B-002 and on the P2-enablement gap).
6. **Crash circuit breaker** — 5 crashes/60s halts a stream; no thrash (§4.1).
7. **Progress-based waking** — the watchdog keys on tracker progress, not
   process-alive, so a stalled-but-alive stream is caught (§4.2).
8. **Spend ceilings** — per-stream and fleet-wide token/spend budgets enforced by
   the supervisor; breach halts the stream cleanly with a resumable handoff.
9. **The waker cannot die silently** — launchd `KeepAlive` on the watchdog.
10. **Immutable audit** — every action is an authenticated append-only tracker
    event; the overnight run is fully reconstructable in the morning.

## 8 — The harness scripts (build-and-dry-run before the overnight run)

The scripts this harness needs are small and mirror proven ones already in the
repo (`build_orchestrator/launch_conductor.sh`, `data_progress/_supervisor.sh`,
`scripts/resume.sh`, `scripts/halt_handler.sh`, `scripts/deploy_and_smoke.sh`).
They are NOT shipped pre-run in this strategy artifact, because an unverified
overnight-autonomy script is precisely the "unearned green" §N.8 forbids — a
launcher that looks right but mis-wires `--append-system-prompt` would run six
streams on the wrong brief all night.

**Required before the overnight launch: a short "harness build & dry-run"
session** (its prompt is §9 below) that authors and TESTS:

- `harness/fleet_launch.sh` — starts the six supervisors + the watchdog.
- `harness/_stream_supervisor.sh` — the respawn loop + crash breaker (per stream).
- `harness/stream_run.sh` — resolves the model (§5), launches the stream headless.
- `harness/fleet_watchdog.sh` — the progress-based waker (launchd).
- `harness/model_resolve.sh` — the fallback-chain probe (§5).
- `harness/deploy_sync_checkpoint.sh` — the gated, verified, reversible prod sync (§6.3).
- `harness/fleet_cleanup.sh` — the end-of-fleet teardown (§6.4).
- launchd plists for the watchdog (KeepAlive) — shadow/loopback-safe, per the
  campaign's existing launchd conventions.

The dry-run proves, on ONE stream, for a few minutes, that: launch injects the
correct prompt; the supervisor respawns a killed stream; the watchdog detects a
stalled (alive-but-flat) stream and wakes it; a self-pause halts one stream while
another keeps running; the crash breaker trips at 5/60s; and NOTHING deploys to
production during a dry-run. Only after that passes is the fleet launched for real.

## 9 — Prompt: the harness build & dry-run session (paste-ready)

```text
You are building and DRY-RUN-TESTING the overnight autonomous execution harness for the six
Paripraśna P3 streams — before any real overnight run. No campaign phase runs here; you are
building and proving the harness itself. Read AGENTS.md, CLAUDE.md (handshake), then
00_ARCHITECTURE/briefs/pariprashna_assurance/STREAM_EXECUTION_HARNESS_v1_0.md IN FULL — you are
implementing its §8 script set to the behavior its §2-§7 specify. Also read the proven templates
it cites under 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/ (launch_conductor.sh,
data_progress/_supervisor.sh, scripts/resume.sh, halt_handler.sh, deploy_and_smoke.sh) — mirror
them, don't reinvent. Fresh worktree off current origin/main; may_touch
00_ARCHITECTURE/briefs/pariprashna_assurance/harness/** and the launchd plist dir only.

Build the §8 scripts. Then DRY-RUN-PROVE, on ONE throwaway stream against a scratch branch (never
a real S1-S6 branch, never production): (a) launch injects the correct per-stream prompt via
--append-system-prompt; (b) killing the stream pid → supervisor respawns it and it re-derives
state; (c) a stalled-but-alive stream (flat tracker progress past the stall budget) → the
watchdog wakes it; (d) a simulated self-pause halts that stream while a second dry-run stream
keeps running; (e) the crash breaker trips at 5 crashes/60s and stops thrashing; (f) model_resolve
falls back correctly when the primary is forced unavailable, and REFUSES to downshift a
security-verifier below Sonnet (pauses instead); (g) deploy_sync_checkpoint.sh is a NO-OP in
dry-run mode and cannot touch production. Paste the actual evidence of each — not assertions.

Land the harness via PR -> CI -> merge (bare `gh pr merge <n>`). Exit report: the merge SHA, and
the seven dry-run proofs (a-g) with pasted evidence. If any dry-run proof fails, fix the script
and re-prove — do NOT report the harness ready with a failing proof. If you cannot prove one
responsibly in a 2h ceiling, self-pause with a precise handoff. Ceiling: 2h.
```

## 10 — How the native launches the overnight run

After the §9 build-and-dry-run session reports all seven proofs green and the
harness is merged, the entire overnight run is ONE command:

```bash
bash 00_ARCHITECTURE/briefs/pariprashna_assurance/harness/fleet_launch.sh
```

It starts the six supervised streams and the watchdog, then returns. The fleet
runs unattended: each stream investigates → fixes → independently verifies →
merges (gated) → events its progress; the watchdog keeps every stream live and
resumes any that stops; blocked streams wait for morning review while the rest
continue. In the morning: read the tracker dashboard (the six streams' progress,
findings, merges, and any BLOCKED self-pauses), run the deploy-sync checkpoint if
it hasn't run, and hand convergence to Session C. Cleanup (§6.4) runs at fleet close.

## 11 — Change handling
This harness is under B.8 versioning; a material change bumps the version + logs
it + lands as a tracker plan revision (elevation §5.3). The six elevated stream
prompts it drives live in `SESSION_A_STREAM_KICKOFF_PROMPTS_v2_0.md`; if a stream's
evidence shows a charter needs revision, that is a governed charter bump, not an
inline overnight edit.

*End STREAM_EXECUTION_HARNESS v1.0.*
