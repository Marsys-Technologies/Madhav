---
canonical_id: SYSTEM_REPAIR_MASTER_PLAN
version: 1.1
status: CURRENT
authored: 2026-05-25
author: Claude (Cowork planning session)
description: >
  Master plan for the three-phase System Repair, Test, and Architecture exercise
  surfaced by the Cross-Channel Parity Audit v2.0 (2026-05-25).
  Covers 8 Claude Code sessions: 2 fix sessions, 4 test sessions, 2 architecture sessions.
  v1.1: Restructured for two-stream fully-autonomous execution (no human gates,
  sub-agent per session, --dangerously-skip-permissions, Conductor-driven).
related_artifacts:
  - CROSS_CHANNEL_PARITY_AUDIT_2026-05-25_v2_0.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F1_PORTAL_FIXES.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F2_MCP_FIXES.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T1_PORTAL_UNIT_TESTS.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T2_MCP_UNIT_TESTS.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T3_INTEGRATION_TESTS.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T4_SYSTEM_TESTS.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A1_TECH_DEBT_AUDIT.md
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A2_ARCHITECTURE_REPORT.md
  - 00_ARCHITECTURE/CONDUCTOR/srp/session_queue.yaml
changelog:
  - version: 1.0
    date: 2026-05-25
    note: Initial authoring. Three-phase, 8-session plan.
artifact: SYSTEM_REPAIR_MASTER_PLAN_v1_0
---

# SYSTEM REPAIR MASTER PLAN v1.0

## 1. Background and Mandate

The Cross-Channel Parity Audit v2.0 (2026-05-25) confirmed 7 code defects across the three
MARSYS-JIS query channels (MCP sidecar, portal Classic Marsys, portal Claude Style):

| ID    | Channel   | Severity | Description                                                         |
|-------|-----------|----------|---------------------------------------------------------------------|
| FIX-1 | MCP       | P0       | 14 UDA tools absent from `primitives_registry.ts` — blocked at gate |
| FIX-2 | MCP/Portal| P0       | `msr_sql.ts` reads `plan.forward_looking`, not `params.forward_looking` |
| FIX-3 | MCP       | P1       | `query_signals` valence enum vocabulary mismatch (positive vs benefic) |
| FIX-4 | MCP       | P1       | `query_ephemeris` sample_step sent as string "7d", portal expects number |
| FIX-5 | MCP       | P1       | `lel_query` sends `min_significance` float, portal reads `significance` string |
| FIX-6 | MCP       | P2       | `lel_query` reports `source_version: "1.6"`, canonical LEL is v1.7 |
| FIX-7 | Portal    | P2       | `msr_sql.ts` `params_json` log uses `plan.*` values, masking actual filters |

Additionally, a broader campaign is required:
- **Phase 2**: Comprehensive test coverage for all three channels — currently near-zero at the
  retrieval-layer filter level.
- **Phase 3**: Concurrent technical debt audit and target architecture report documenting what
  should be retained, deleted, and rebuilt.

## 2. Execution Model

- **Planning / authoring**: Cowork (this document + session briefs).
- **Implementation**: Two parallel Conductor streams running in Claude Code with
  `--dangerously-skip-permissions`. No human gates — fully autonomous session after session.
- **Sub-agent per session**: Each session is spawned as a fresh sub-agent (Task tool) to
  prevent context bleed and memory exhaustion across the 6-8 session run.
- **Two streams** (see §9):
  - **Stream 1** — Phase 1 (fixes) + Phase 2 (tests), Conductor-driven, batched parallel
  - **Stream 2** — Phase 3 (architecture), Conductor-driven, sequential
- **Conductor queues**:
  - `00_ARCHITECTURE/CONDUCTOR/srp/stream1_queue.yaml` (F-1/F-2 → merge → T-1/T-2 → T-3/T-4)
  - `00_ARCHITECTURE/CONDUCTOR/srp/stream2_queue.yaml` (A-1 → A-2)
- **Operator setup**: one `STREAM1_SETUP_PROMPT.md` runs in the main worktree to create all
  worktrees. Then two Conductor kick-off prompts start the streams independently.

## 3. Phase Overview

```
Phase 1 — Fixes (sessions F-1, F-2)          Phase 3 — Architecture (sessions A-1, A-2)
  F-1: Portal fixes ──────────────┐               A-1: Tech Debt Audit ─────────────┐
  F-2: MCP sidecar fixes ─────────┤               A-2: Architecture Report ─────────┤
                                  ↓                                                  │
Phase 2 — Tests (T-1 through T-4) [blocked on F-1 + F-2 merge]                     │
  T-1: Portal retrieval unit tests                                                   │
  T-2: MCP tool unit tests                                                           │
  T-3: Integration tests (MCP live DB)                                               │
  T-4: System tests (portal pipeline E2E)                                            │
                                                                                     │
Sealing artifact: SYSTEM_REPAIR_CLOSE_v1_0.md ←─────────────────────────────────────┘
```

Phase 1 and Phase 3 are **parallel-safe** — they touch different files:
- Phase 1 modifies production code (portal + MCP sidecar).
- Phase 3 reads code for analysis and writes architecture report documents only.

Phase 2 is **blocked** on Phase 1 merge to main (tests must target fixed code).

## 4. Session Roster

### Phase 1 — Fixes

#### SRP-F-1: Portal Fixes
- **Branch**: `fix/srp-f1-portal-fixes`
- **Worktree**: `MadhavSRP-F1`
- **Deploy target**: `amjis-web` (Cloud Run web service)
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F1_PORTAL_FIXES.md`
- **Scope**:
  - FIX-1: `platform/src/lib/mcp/primitives_registry.ts` — add 14 UDA tools to
    `SURGICAL_TOOLS` and `MCP_TO_RETRIEVAL_TOOL`.
  - FIX-2: `platform/src/lib/retrieve/msr_sql.ts` — read `forward_looking` from
    `params` not `plan`.
  - FIX-6: `platform-mcp/src/tools/lel_query.ts` — update `source_version` from
    `"1.6"` to `"1.7"`.
  - FIX-7: `platform/src/lib/retrieve/msr_sql.ts` — fix `params_json` log to reflect
    actual filter values.
- **ACs**:
  - `isAllowedSurgicalTool('msr_sql')` returns true for all 14 new tools.
  - `forward_looking: true` sent via MCP results in `is_forward_looking = true` SQL filter.
  - Vitest: 0 regressions. All pre-existing tests pass.
  - PR opened; human merges to main and deploys `amjis-web`.

#### SRP-F-2: MCP Sidecar Fixes
- **Branch**: `fix/srp-f2-mcp-fixes`
- **Worktree**: `MadhavSRP-F2`
- **Deploy target**: `amjis-mcp` (Cloud Run sidecar service)
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F2_MCP_FIXES.md`
- **Scope**:
  - FIX-3: `platform-mcp/src/tools/query_signals.ts` — fix `valence` enum to use
    `"benefic"/"malefic"/"context-dependent"`.
  - FIX-4: `platform-mcp/src/tools/query_ephemeris.ts` — convert `sample_step` string
    enum to numeric value before calling platform.
  - FIX-5: `platform-mcp/src/tools/lel_query.ts` — align significance param name:
    either send `significance` string or fix platform reader to handle `min_significance`.
- **ACs**:
  - `valence: "benefic"` query returns non-empty MSR signal results.
  - `sample_step: "7d"` correctly downsamples ephemeris rows (every 7th row).
  - `significance_tier: "tier_1"` correctly filters LEL events.
  - MCP vitest: 0 regressions.
  - PR opened; human merges to main and deploys `amjis-mcp`.

---

### Phase 2 — Tests

All Phase 2 sessions are **blocked on F-1 and F-2 being merged to main**.

#### SRP-T-1: Portal Retrieval Unit Tests
- **Branch**: `test/srp-t1-portal-unit`
- **Worktree**: `MadhavSRP-T1`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T1_PORTAL_UNIT_TESTS.md`
- **Scope**: Vitest unit tests for `platform/src/lib/retrieve/`:
  - `msr_sql.ts` — filter fidelity: domain, forward_looking, valence, planet, signal_type.
  - `lel_query.ts` — significance, category, and confidence filters.
  - `query_ephemeris.ts` — date range, sample_step numeric downsampling.
  - `primitives_registry.ts` — `isAllowedSurgicalTool` coverage for all 33 registered tools.
- **ACs**:
  - ≥ 40 new test cases.
  - All 7 original bugs have regression tests (one per fix).
  - 100% branch coverage on all filter code paths.
  - `npx vitest run` 0 failures.

#### SRP-T-2: MCP Tool Unit Tests
- **Branch**: `test/srp-t2-mcp-unit`
- **Worktree**: `MadhavSRP-T2`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T2_MCP_UNIT_TESTS.md`
- **Scope**: Vitest unit tests for `platform-mcp/src/tools/`:
  - `query_signals.ts` — param translation: valence, domain, planet, forward_looking.
  - `query_ephemeris.ts` — param translation: sample_step string→number, date range.
  - `lel_query.ts` — param translation: significance_tier→significance, category.
  - `lel_query.ts` — source_version annotation matches canonical LEL version.
  - Snapshot tests for `callPlatformPrimitive` call arguments.
- **ACs**:
  - ≥ 30 new test cases.
  - Every param translation path has a unit test.
  - `npx vitest run` inside `platform-mcp/` 0 failures.

#### SRP-T-3: Integration Tests — MCP Live DB
- **Branch**: `test/srp-t3-integration`
- **Worktree**: `MadhavSRP-T3`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T3_INTEGRATION_TESTS.md`
- **Scope**: Integration tests calling the MCP primitives route (`/api/mcp/primitives/[tool]`)
  against a live DB (Postgres via proxy). Requires `INTEGRATION_TEST_API_KEY` env var.
  - Happy-path tests for all 14 formerly-phantom tools (non-empty response).
  - Filter fidelity tests: `forward_looking: true` returns only predictive signals.
  - `valence: "benefic"` returns non-empty, `valence: "positive"` returns empty.
  - `sample_step: "7d"` returns row count ≈ date_range_days / 7.
  - `significance_tier: "tier_1"` returns only high-significance LEL events.
- **ACs**:
  - All 14 formerly-phantom tools return HTTP 200 with non-empty data.
  - Filter tests pass for all 5 fixed bugs.
  - Tests skip gracefully if `DB_PROXY_PORT` not set (CI-safe).
  - 0 failures against local DB proxy.

#### SRP-T-4: System Tests — Portal Pipeline E2E
- **Branch**: `test/srp-t4-system`
- **Worktree**: `MadhavSRP-T4`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T4_SYSTEM_TESTS.md`
- **Scope**: End-to-end tests exercising the full portal pipeline via the `/api/query` route.
  Requires `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` env vars (same as existing smoke suite).
  - Adapter pipeline path: `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` confirmed in response.
  - B.11 floor: all 5 forced tools appear in trace `tool_executions`.
  - Planner visibility: tools with `expose_to_planner: true` appear in `tools_authorized`.
  - `forward_looking` query (e.g., "what transits are coming up") routes to signals with
    `is_forward_looking = true`.
  - MCP channel: 5 representative tools invoked via MCP API, results non-empty.
- **ACs**:
  - ≥ 15 E2E scenario tests.
  - B.11 floor verified programmatically from query trace.
  - All 5 adapter providers return non-error responses for a chart read query.
  - Tests skip if smoke env vars absent (CI-safe via `describe.skipIf`).

---

### Phase 3 — Architecture (Concurrent with Phase 1)

#### SRP-A-1: Technical Debt Audit
- **Branch**: `arch/srp-a1-tech-debt`
- **Worktree**: `MadhavSRP-A1`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A1_TECH_DEBT_AUDIT.md`
- **Scope**: Read-only analysis of the entire `platform/` and `platform-mcp/` codebase.
  - Dead code catalog: unused exports, unreachable branches, `@deprecated` symbols.
  - Orphaned feature flags in `feature_flags.ts`, `deploy.yml`, and Cloud Run env.
  - Legacy pipeline remnants: `createOrchestrator()`, `single_model_strategy`, `consume-tools.ts`
    and any other code that cannot be reached when `USE_ADAPTERS=true`.
  - Duplicate type definitions (e.g., valence, significance, domain enums defined in multiple
    places with inconsistent vocabulary).
  - Logging debt: `params_json` mismatches, missing trace fields.
  - Output: `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md` — structured catalog with severity
    (CRITICAL / HIGH / MEDIUM / LOW) and estimated LoC impact.
- **ACs**:
  - Catalog covers all files changed since R11.A merge (2026-05-22).
  - Every dead-code entry has: file path, line range, reason it's unreachable/unused.
  - Every orphaned flag entry has: flag name, last-set location, whether a `--remove-env-vars`
    step is needed.
  - Report saved to `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md`.

#### SRP-A-2: Architecture Report
- **Branch**: `arch/srp-a2-arch-report` (or same as A-1 if A-1 is already merged)
- **Worktree**: `MadhavSRP-A2`
- **Brief**: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A2_ARCHITECTURE_REPORT.md`
- **Prereq**: SRP-A-1 complete (uses TECH_DEBT_AUDIT_v1_0.md as input).
- **Scope**: Synthesize A-1 findings into a combined deletion list + target architecture document.
  - **Deletion list**: Exact files and functions to remove, grouped by: (a) dead adapter
    plumbing, (b) orphaned feature flags, (c) legacy pipeline code, (d) duplicate type
    definitions. Each entry: file, symbol, blocker (if any), recommended PR.
  - **Target architecture**: Narrative + diagram describing the ideal steady-state system:
    - Two backend pipelines (Classic orchestrator / Adapter+loop) with clean feature-flag
      separation and a 6-month sunset plan for Classic.
    - Single vocabulary layer for shared enums (valence, significance, domain) sourced from
      one canonical types file.
    - `primitives_registry.ts` as the permanent single source of truth for MCP dispatch
      (with auto-sync tooling proposal).
    - Logging discipline: `params_json` always reflects actual filter values.
    - Test coverage targets: ≥ 80% branch coverage on all retrieval tools.
  - Output: `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md`.
- **ACs**:
  - Deletion list entries sum to ≥ 500 LoC removable without regressions.
  - Target architecture covers all three query channels.
  - Report saved to `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md`.

## 5. Dependency Graph

```
SRP-F-1 ─────────────────────────────────────────────┐
                                                      ├──→ SRP-T-1 ─┐
SRP-F-2 ─────────────────────────────────────────────┘              │
                                                                     ├──→ SEAL
SRP-A-1 ──→ SRP-A-2 ────────────────────────────────────────────────┘

SRP-T-2 (unblocked — tests against code post-F-2)
SRP-T-3 (blocked on F-1 + F-2 merge to main + deploy)
SRP-T-4 (blocked on F-1 + F-2 merge to main + deploy)
```

Parallel-safe pairs:
- F-1 ∥ F-2 (different repos: platform vs platform-mcp)
- F-1 ∥ A-1 (A-1 is read-only)
- F-2 ∥ A-1 (A-1 is read-only)
- T-1 ∥ T-2 (different test targets)
- A-1 ∥ T-1, T-2 (A-1 read-only)

## 6. Sealing

On completion of all 8 sessions:

1. Confirm `TECH_DEBT_AUDIT_v1_0.md` and `TARGET_ARCHITECTURE_REPORT_v1_0.md` are committed.
2. Confirm all Phase 2 test suites pass on post-fix code.
3. Author `SYSTEM_REPAIR_CLOSE_v1_0.md` sealing artifact at `00_ARCHITECTURE/`.
4. Update `CURRENT_STATE_v1_0.md` — append SRP close to concurrent workstreams.
5. Update `CLAUDE.md §E` — append SRP entry.
6. Append to `SESSION_LOG.md`.

## 7. Worktree Pre-Creation Commands

Paste into terminal before opening Antigravity windows:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Phase 1
git worktree add ../MadhavSRP-F1 -b fix/srp-f1-portal-fixes
git worktree add ../MadhavSRP-F2 -b fix/srp-f2-mcp-fixes

# Phase 2 (create after F-1 + F-2 merge)
git worktree add ../MadhavSRP-T1 -b test/srp-t1-portal-unit
git worktree add ../MadhavSRP-T2 -b test/srp-t2-mcp-unit
git worktree add ../MadhavSRP-T3 -b test/srp-t3-integration
git worktree add ../MadhavSRP-T4 -b test/srp-t4-system

# Phase 3 (parallel-safe with Phase 1)
git worktree add ../MadhavSRP-A1 -b arch/srp-a1-tech-debt
git worktree add ../MadhavSRP-A2 -b arch/srp-a2-arch-report
```

## 8. Key File Paths (Reference)

| File | Purpose |
|------|---------|
| `platform/src/lib/mcp/primitives_registry.ts` | MCP dispatch whitelist (SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL) |
| `platform/src/lib/retrieve/msr_sql.ts` | MSR SQL retrieval — forward_looking + logging bugs |
| `platform/src/lib/retrieve/lel_query.ts` | LEL retrieval — reads `significance` string |
| `platform/src/lib/retrieve/query_ephemeris.ts` | Ephemeris retrieval — sample_step expects number |
| `platform/src/lib/retrieve/index.ts` | RETRIEVAL_TOOLS registry (51 tools) |
| `platform/src/app/api/mcp/primitives/[tool]/route.ts` | Primitive dispatcher — hardcoded QueryPlan |
| `platform-mcp/src/tools/query_signals.ts` | MCP valence enum (FIX-3) |
| `platform-mcp/src/tools/query_ephemeris.ts` | MCP sample_step string (FIX-4) |
| `platform-mcp/src/tools/lel_query.ts` | MCP significance field name + source_version (FIX-5, FIX-6) |
| `platform-mcp/src/server.ts` | MCP tool registrations (40 tools) |
| `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` | expose_to_planner flags, channel assignments |

---

## 9. Two-Stream Fully-Autonomous Execution

### Topology

```
Terminal A (Stream 1)                    Terminal B (Stream 2)
─────────────────────────────            ─────────────────────────────────
  ONE-TIME SETUP (both streams)
  Paste STREAM1_SETUP_PROMPT.md
  → Creates all 8 worktrees
  → Verifies environment

  Then open two Claude Code windows:

  Window 1 (Stream 1 Conductor)          Window 2 (Stream 2 Conductor)
  Paste STREAM1_CONDUCTOR_KICKOFF.md     Paste STREAM2_CONDUCTOR_KICKOFF.md
  cd /Users/Dev/Vibe-Coding/Apps/Madhav  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  claude --dangerously-skip-permissions  claude --dangerously-skip-permissions

  BATCH 1 (parallel sub-agents):
    Sub-agent A → F-1 in MadhavSRP-F1
    Sub-agent B → F-2 in MadhavSRP-F2      Sub-agent C → A-1 in MadhavSRP-A1

  MERGE STEP (Conductor inline):
    git merge fix/srp-f1 fix/srp-f2
    → fixes land on main locally

  BATCH 2 (parallel sub-agents):
    Sub-agent D → T-1 in MadhavSRP-T1      Sub-agent E → A-2 in MadhavSRP-A2
    Sub-agent F → T-2 in MadhavSRP-T2      (blocked on A-1)

  BATCH 3 (parallel sub-agents):
    Sub-agent G → T-3 in MadhavSRP-T3
                  (dev server started in worktree)
    Sub-agent H → T-4 in MadhavSRP-T4
                  (dev server started in worktree)
```

### No Human Gates

All PR merges, merges to main, and test execution happen autonomously. The Conductor
uses `check_commands` to verify each session completed before advancing to the next batch.
PRs are opened as normal commits (branches pushed to origin); human review happens after
the full run completes, not as blocking gates within the run.

### Sub-agent Context Isolation

Each session is a fresh Task sub-agent with its own context window. The Conductor passes
the brief path and worktree path as the only context. This prevents the "context bleed"
that occurs when all 8 sessions run in a single chat.

### `--dangerously-skip-permissions`

Both Conductor windows are started with `claude --dangerously-skip-permissions`. This
propagates to all sub-agents automatically. Sub-agents can run git commands, npm scripts,
and bash without per-command approval prompts.

### Executor Files

| File | Purpose |
|------|---------|
| `CONDUCTOR/srp/STREAM1_SETUP_PROMPT.md` | Paste in main → creates all worktrees |
| `CONDUCTOR/srp/stream1_queue.yaml` | Stream 1 Conductor queue (F+T sessions) |
| `CONDUCTOR/srp/STREAM1_CONDUCTOR_KICKOFF.md` | Paste in Window 1 → starts Stream 1 |
| `CONDUCTOR/srp/stream2_queue.yaml` | Stream 2 Conductor queue (A sessions) |
| `CONDUCTOR/srp/STREAM2_CONDUCTOR_KICKOFF.md` | Paste in Window 2 → starts Stream 2 |

### changelog

- v1.0 (2026-05-25): Initial three-phase plan with human gates
- v1.1 (2026-05-25): Restructured for two-stream no-gate sub-agent Conductor execution

---

*End of SYSTEM_REPAIR_MASTER_PLAN_v1_0.md*
