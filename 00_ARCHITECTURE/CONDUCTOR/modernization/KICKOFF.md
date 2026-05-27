# Kickoff — Platform Modernization (autonomous, zero human gates)

Paste the prompts below into a Claude Code (Antigravity) session running with bypass / 
`--dangerously-skip-permissions`. The Conductor obeys the operating contract; you only re-kick.

## Operating contract (the Conductor follows this — it's also in the execution plan + queue)
- **No human approval gates. Full zero-touch incl. prod.** Never pause for confirmation.
- Each batch: read `session_queue.yaml` + `PROGRAM_STATE.md`; pick **eligible** units (deps + gates green,
  file-fence free); run each via a **sub-agent in its assigned worktree** (fresh context per unit); up to
  **3 concurrent** where fences allow. `0a.1` and `0b.1` both touch `consume/route.ts` → never concurrent.
- Per unit: execute its brief → run its `check_commands` → **green:** commit (scoped, cleanly
  cherry-pickable) + **cherry-pick to main** → **red:** do its `on_red` (`rollback` or `halt_queue`).
- Honor safety rails (execution plan §6) + hard gates **G1–G6**. New flags default OFF; DB changes additive +
  staging→live swap; every prod deploy = pre-flight + post-deploy smoke + auto-rollback; kill-switch on error spike.
- **Build unit `0t` (tracker) FIRST** so progress is observable.
- `1.2` stays blocked until `fixtures/jh_oracle.json` exists — skip it, run everything else.
- Stop cleanly at ~20 sub-agent spawns or when context fills: update `PROGRAM_STATE.md` (gate board,
  last-green per stream, open halts) + append `CONDUCTOR_LOG.md`, then end with a one-paragraph status.

## BOOTSTRAP + KICKOFF PROMPT (paste THIS — it sets up the whole environment, then runs)
```
You are the Conductor for the MARSYS-JIS Platform Modernization program, running fully autonomously with
bypass permissions and NO human approval gates. Do everything below yourself, in order, without pausing to
ask me anything.

PHASE 0 — Bootstrap the environment (idempotent; do once):
1. Confirm you are in /Users/Dev/Vibe-Coding/Apps/Madhav. `git rev-parse --abbrev-ref HEAD`; if not on main, `git checkout main`. `git status`.
2. Read in full: 00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md (v2.1), PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0.md, 00_ARCHITECTURE/CONDUCTOR/modernization/{KICKOFF.md, PROGRAM_STATE.md, session_queue.yaml}, and every file in CONDUCTOR/modernization/briefs/.
3. If artifacts under 00_ARCHITECTURE/ and tools/program-tracker/ are uncommitted, commit to main: `git add 00_ARCHITECTURE tools/program-tracker && git commit -m "program: modernization plan + conductor scaffolding + tracker"`.
4. Detect toolchain (pnpm vs npm in platform/, node, python/pytest). If a runner a gate needs is missing, install or adapt the check and note it in CONDUCTOR_LOG.md.
5. Create 3 worktrees if absent (reuse if present): `git worktree add ../MadhavStreamA -b prog/stream-a main` (+ StreamB/prog/stream-b, StreamC/prog/stream-c).
6. Build unit 0t (tracker) NOW per briefs/BRIEF_0t_program_tracker.md: implement tools/program-tracker/ server.mjs (serves public/index.html + GET /status.json + SSE /events) + collect.mjs (assembles status from session_queue.yaml + PROGRAM_STATE.md + git + gate_status.json) + package.json + smoke test. UI already exists at public/index.html. Start on http://localhost:8787 (background); confirm /status.json valid. Commit + cherry-pick to main; mark 0t green in PROGRAM_STATE.md.
7. Create CONDUCTOR_LOG.md + CONDUCTOR_HALT_LOG.md under CONDUCTOR/modernization/ if absent.

PHASE 1 — Run Batch 1 (autonomous, no human gates):
8. Pick all ELIGIBLE units from session_queue.yaml (deps+gates green, fence free). Run each via a sub-agent IN ITS ASSIGNED WORKTREE (fresh context), up to 3 concurrent; keep 0a.1 and 0b.1 serial (shared consume/route.ts).
9. Per unit: follow brief; create/confirm gate harness; run check_commands. GREEN → commit (scoped, cherry-pickable) + cherry-pick to main + update PROGRAM_STATE.md + tracker gate_status.json + CONDUCTOR_LOG.md. RED → on_red (rollback+re-queue, or halt_queue → CONDUCTOR_HALT_LOG.md + stop the queue).
10. Honor safety rails (execution plan §6) + gates G1–G6. Flags default OFF; DB additive + staging→live swap; prod deploys get pre-flight + post-deploy smoke + auto-rollback; kill-switch on error spike.
11. 1.2 (engine→JH parity, G1) is BLOCKED until python-sidecar/natal_engine/fixtures/jh_oracle.json exists — skip it; run everything else incl. 1.1.
12. NEVER pause for approval. Stop only at ~20 sub-agents or context fill: write clean PROGRAM_STATE.md + append CONDUCTOR_LOG.md, end with a one-paragraph status (re-kick? anything need me?).

Begin now with Phase 0, step 1.
```

## RE-KICK PROMPT (each subsequent batch, fresh chat)
```
Continue the Platform Modernization program. Read
00_ARCHITECTURE/CONDUCTOR/modernization/PROGRAM_STATE.md + session_queue.yaml +
CONDUCTOR_HALT_LOG.md (if present). Resume from the next eligible units across the three worktrees, same
rules as kickoff: no human gates, cherry-pick to main on green, rollback/halt on red, build-first anything
newly eligible, stop + update PROGRAM_STATE.md at the context budget.
```

## On a halt
If a `halt_queue` appears (e.g. engine parity 1.2, or a leaked secret 0b.2), the Conductor stops the whole
queue and writes `CONDUCTOR_HALT_LOG.md`. Read it, resolve the root cause (or provide the missing input),
then re-kick — it resumes from where it halted.
