---
artifact: PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0.md
document: Autonomous Execution Plan for the Platform Modernization Program
version: 1.0
status: DRAFT (execution plan — pending native approval; the "HOW" under MASTER_PLAN v2.1's "WHAT")
date: 2026-05-27
governs_execution_of: 00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md (v2.1)
native_execution_decisions (2026-05-27):
  - "Fully autonomous, no interruptions; Claude Code with --dangerously-skip-permissions / bypass."
  - "Full ZERO-TOUCH incl. production (prod DB migrations, deploys, secret/flag flips run autonomously)."
  - "Integration = Conductor cherry-picks to main on green (no human PR review)."
  - "Unattended model = periodic mechanical re-kick per Conductor context batch."
  - "2–3 parallel autonomous sessions, one git worktree per stream."
  - "Remove all human APPROVAL gates; keep automated PASS/FAIL gates (self-halt streams on red)."
  - "Conductor + sub-agent driven to raise velocity and beat context-memory decay."
expose_to_chat: false
---

# Autonomous Execution Plan v1.0

## §0 — Stance & the honesty clause

This plan executes MASTER_PLAN v2.1 with **zero human approval gates**. Because you also chose **zero-touch
prod** + **auto-cherry-pick to main on green**, there is no human catch anywhere: the automated gate system
is the *only* thing between a defect and production. This plan therefore over-invests in **automated safety
rails** (reversible-by-construction patterns, auto-smoke + auto-rollback, a program kill-switch, and the
G1–G5b hard gates as queue barriers). **Residual risk you are accepting:** a blind spot in an automated gate
can reach prod unobserved until the post-deploy smoke catches it (and auto-rolls back). The mitigations below
shrink that window; they do not eliminate it. The macro-phase red-team at program close is the backstop.

## §1 — Execution topology

```
                    ┌────────────────────────────────────────────┐
                    │  CONDUCTOR (orchestrator chat)               │
                    │  walks session_queue.yaml · spawns sub-agents│
                    │  runs check_commands (gates) · cherry-picks  │
                    │  to main on green · auto-rollback on red     │
                    └───────────────┬──────────────────────────────┘
        ┌───────────────────────────┼───────────────────────────┐
   Stream A (worktree A)      Stream B (worktree B)        Stream C (worktree C)
   Claude Code, bypass        Claude Code, bypass          Claude Code, bypass
   sub-agents per brief       sub-agents per brief         sub-agents per brief
        └─ commits ─┐              └─ commits ─┐                └─ commits ─┐
                    └──────── Conductor cherry-pick → main (on green) ──────┘
```

- **2–3 streams**, each a dedicated **git worktree** + its own Claude Code session run with bypass
  permissions. Streams never share a checkout (race/FS-contention lesson).
- **Conductor** is the brain: it owns `session_queue.yaml`, decides which briefs are *eligible* (their gate
  dependencies are green + file-fences are free), hands eligible briefs to streams, runs each brief's
  `check_commands`, and on green **cherry-picks the stream's commits to main** (commits kept cleanly
  cherry-pickable). On red it **auto-rolls back** the stream and re-queues or halts (no human).
- **Sub-agents**: within a stream, the brief is executed by sub-agents (one per discrete unit) so each unit
  runs in a *fresh* context — this is the primary defense against context-memory decay degrading code.
- **Re-kick**: when a Conductor batch (~20 sub-agents) or the chat context fills, it writes its state to
  `CONDUCTOR_LOG.md` + `session_queue.yaml` and stops cleanly; you paste a one-line "continue" to spawn the
  next batch in a fresh chat. No decisions — purely mechanical.

## §2 — Stream ↔ wave mapping (dependency-driven, not phase-rigid)

The Conductor schedules by the **dependency + gate graph**, so streams pull whatever is *eligible* rather
than following a rigid phase table. The graph (from MASTER_PLAN §7 + §15.2):

| Queue unit | Needs (blockedBy) | Gate barrier | File-fence (must_not_touch overlap) |
|---|---|---|---|
| **0a** naming-taxonomy renames | — | naming-CI green | touches many; run mostly alone or first |
| **0b** B.11 adapter hotfix | — | citation-gate parity test | `consume/route.ts` |
| **0b** secret/DB-pw remediation | — | secret-scan green | scripts/, deploy.yml |
| **0b** mirror-retirement (1 atomic PR, 5 surfaces) | — | drift_detector green | governance docs |
| **1** JH-equiv engine (new `natal_engine/`) | 0a (names) | **G1 JH-parity** (pinned JH oracle) | `python-sidecar/` |
| **2b** unified contract + chart_id-in-contract | 0a | **G3** before de-judgment | `lib/retrieve/`, manifest |
| **2c** registry owner/subject + chart_grants + authorizeChartAccess + role rename | 0a | **G2** before tier-excision | `charts` table, auth |
| **2d** Command Center scaffold (runtime_config + gate_registry) | 0a | — | cockpit, configService |
| **2a** deterministic L1→L2.5 build into extended schema | **1 (G1)** | **G4** before NATIVE fallback removed | `chart_facts`, `l25_*` — fence vs 2c on `charts` |
| **3** de-judgment | 2b (G3) | — | `msr_sql.ts`, MCP `query_signals.ts` |
| **3** gateway + control-model-B + pipeline isolation | 2b | — | `lib/pipelines/` |
| **3** per-chart cutover (strangler + freeze-old) | 1+2a+2c | — | data tables |
| **3** Consult rename + role-gated nav | 2c | — | app routes |
| **3** tier excision | 2c (G2) | **G2** | disclosure/, mcp keys |
| **3** legacy-pipeline delete | 0b (B.11) + **G5b** (onFinish parity) | **G5/G5b** | `synthesis/`, route.ts |
| **4** build-trigger wiring, SQL upgrade, Memorystore, CDN/Armor, observability | 3 close | budget-guard | infra |
| **4** eval re-baseline, learning-loop, red-team seal | 3 close | red-team green | — |

**Realistic flow with 2–3 streams:** Batch 1 runs **0a** (solo first, it touches everything), then **0b**,
**1**, and **2b/2c/2d** fan out across streams (they need only 0a, not the engine). **2a** unlocks when G1
goes green. Wave 3 units unlock as their gates clear. Wave 4 last.

## §3 — Conductor configuration (no-human-halt variant)

Extend the existing Conductor (`00_ARCHITECTURE/CONDUCTOR/`) with:
- **`session_queue.yaml`** entries each carry: `id`, `wave`, `brief_path`, `worktree`, `blockedBy[]` (gate
  ids + other unit ids), `may_touch[]`, `must_not_touch[]`, `check_commands[]` (the automated gate), and
  `on_red: rollback|halt_queue`.
- **Gate automation** — each hard gate is a `check_command` that exits 0/non-0:
  - **G1** `pytest natal_engine/tests/test_jh_parity.py` (engine reproduces the pinned JH oracle fixture).
  - **G2** an integration test asserting `authorizeChartAccess` is live + no tier path reachable.
  - **G3** a test asserting the unified contract exists + both channels build from it.
  - **G4** a test asserting no `NATIVE_CHART_ID`/`DEFAULT_CHART_ID` literal remains in production paths.
  - **G5/G5b** golden-transcript test: adapter `onFinish` parity (persistence + predictions + observatory)
    AND citation gate present on adapter path, before legacy delete.
- **Cherry-pick-to-main on green**: on all `check_commands` green, Conductor cherry-picks the stream's
  commits to `main` (commits scoped + clean). On red → `on_red`.
- **Replace the old human-halt checkpoints** with: (a) `rollback` (git reset the stream worktree to last
  green, re-queue with the failure note appended to the brief), or (b) `halt_queue` (Conductor stops the
  WHOLE queue and writes `CONDUCTOR_HALT_LOG.md`) for gate failures that imply a systemic problem. No human
  prompt; the halt log is read at the next re-kick.
- **Program kill-switch**: a post-deploy smoke failure or Cloud Run error-rate spike triggers `halt_queue` +
  auto-rollback of the last cherry-pick. Automated.
- **Context-decay control**: ≤20 sub-agent spawns per orchestrator chat; each sub-agent gets a *self-contained*
  brief (no reliance on prior chat memory); `PROGRAM_STATE.md` is the single re-kick pointer.

## §4 — Worktree & stream setup (pre-created; pasteable)

```bash
# from repo root on main, pre-create one worktree + branch per stream
git worktree add ../MadhavStreamA -b prog/stream-a main
git worktree add ../MadhavStreamB -b prog/stream-b main
git worktree add ../MadhavStreamC -b prog/stream-c main
# launch each in its own Claude Code session with bypass perms:
#   claude --dangerously-skip-permissions   (run inside each worktree dir)
# Conductor runs in a SEPARATE chat at repo root on main.
```
Worktrees are retired (`git worktree remove`) at program close. Branch base = `main`; Conductor cherry-picks
forward, so streams stay shallow and conflict-light.

## §5 — Per-brief template (every queue unit = one CLAUDECODE_BRIEF)

Each brief is self-contained (context-decay defense) and carries:
- `scope` + `wave` + `worktree` + `blockedBy`.
- `may_touch` / `must_not_touch` globs (the file-fence — enforced so parallel streams never collide).
- **Acceptance criteria** (all automated):
  1. Its `check_commands` pass (incl. any hard gate it sits behind).
  2. **"Click-through reaches the behavior"** — for any user-visible change, an integration test that mounts
     the parent context (not prop-injection) proves the new path is actually reachable (anti ship-but-don't-mount).
  3. **Golden-transcript test** for any behaviour-preserving refactor (output identical pre/post).
  4. New code has unit tests; coverage does not drop.
- `commit_cadence`: commit per logical unit with a structured message; commits must be cleanly
  cherry-pickable (touch only declared paths).
- `on_red`: rollback (default) or halt_queue.
- `rollback_plan`: how to revert this unit (git + any reversible data/infra step).
- **Brief-amendment rule**: if scope changes mid-flight, Conductor issues a *fresh* brief — never edits the
  running one (executors follow the prompt, not the amended doc).

## §6 — Autonomous safety rails (these REPLACE the human gates)

Because prod is zero-touch, every irreversible class is made reversible-by-construction + auto-checked:
1. **DB: additive + staging→live atomic swap.** No destructive in-place. Reuse the Phase 4C
   `bootstrap_*` staging→live swap + `build_id` pattern; the old data is frozen, not dropped. Column drops
   (the last strangler step) run ONLY after a green post-cutover validation window.
2. **Data cutover: parallel-build + validate + freeze-old** (MASTER_PLAN §12). Per-chart, behind a
   Command Center gate; native chart first; diff-vs-old recorded.
3. **Deploys: pre-flight + post-deploy smoke + auto-rollback.** Every prod deploy is preceded by green tests
   + an automated smoke spec and followed by a post-deploy smoke; failure → auto-rollback to the prior
   Cloud Run revision (revision pinned) + `halt_queue`.
4. **Secrets/flags: scripted, idempotent, logged, default-safe.** New flags default OFF (a flip is
   reversible); secret writes are versioned; every flip logged to `gate_change_log`.
5. **Cost guard:** Wave-4 GCP scale ops (SQL tier, Memorystore, CDN) carry a budget pre-check; auto-stop if
   projected cost exceeds a set ceiling.
6. **Hard gates as barriers:** a stream physically cannot reach a prod op until its gate `check_command` is
   green (G1–G5b).
7. **Determinism backbone:** drift/schema validators + naming-CI run on every cherry-pick; a red blocks the
   merge.

## §7 — Context-memory-decay mitigation (quality at velocity)

- **Sub-agent-per-unit**: each discrete task runs in a fresh sub-agent context — no decayed mega-context.
- **Self-contained briefs**: every brief restates the context it needs; no "as discussed above."
- **`PROGRAM_STATE.md`** (single pointer): current wave, eligible units, last green per stream, open halts.
  Read at every re-kick; replaces the heavy session-open reads (lean-transform governance).
- **Conductor batch ceiling** (~20 sub-agents) forces a clean re-kick before context rots.
- **Golden-transcript + integration tests** catch the specific failure mode of an autonomous agent
  "finishing" without wiring the behaviour through.

## §8 — Kickoff sequence (the first re-kick batch)

1. Pre-create worktrees A/B/C (§4).
2. Conductor setup chat: generate `session_queue.yaml` + the Wave-0/Wave-1 briefs + `PROGRAM_STATE.md`;
   pin the **JH oracle** (which JH version + ayanamsha — the one operational input still needed) as the G1
   fixture.
3. Launch Batch 1: **0a** (Stream A, solo first — it renames broadly), then **0b** (Stream B) + **engine
   Wave 1** (Stream C) once 0a's rename CI is green; **2b/2c/2d** fan out as streams free up.
4. Conductor runs gates, cherry-picks green units to main, auto-rolls back red.
5. On batch/context fill → clean stop + `PROGRAM_STATE.md` update → you re-kick.

## §9 — Open operational inputs (small; not design forks)
1. **JH oracle pin** — which JH version/build + ayanamsha is the G1 golden fixture (capture once).
2. **Macro-phase number** for the program wrapper (M6 vs M5-X) — governance label only.
3. **Cost ceiling** for the Wave-4 budget guard.
4. **Smoke-spec auth** — confirm the `SMOKE_SESSION_COOKIE` / `SMOKE_CHART_ID` env for post-deploy smoke.
5. The five non-blocking §15.4 forks from the master plan (depth-replacement, Anthropic-cost, etc.) — can be
   resolved as their wave's brief is authored; none block kickoff.

## §10 — Provenance
Model-authored (Claude, Cowork), DRAFT. Encodes the native's 2026-05-27 autonomous-execution decisions.
Executes MASTER_PLAN v2.1. No implementation begins until the native approves + the JH oracle is pinned.
Next Cowork step on approval: generate the concrete `session_queue.yaml` + the Wave-0/Wave-1
CLAUDECODE_BRIEF files + `PROGRAM_STATE.md`.
