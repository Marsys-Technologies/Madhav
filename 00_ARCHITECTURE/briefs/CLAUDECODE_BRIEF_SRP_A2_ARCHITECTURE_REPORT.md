---
canonical_id: CLAUDECODE_BRIEF_SRP_A2
version: 1.0
status: CURRENT
phase: SRP-A-2
session_type: analysis
authored: 2026-05-25
worktree: MadhavSRP-A2
branch: arch/srp-a2-arch-report
blocked_by: arch/srp-a1-tech-debt (merged)
deploy_target: none (report only)
may_touch:
  - 00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md (create)
must_not_touch:
  - platform/src/**
  - platform-mcp/src/**
---

# CLAUDECODE BRIEF: SRP-A-2 — Target Architecture Report

## Context

You are synthesizing the Technical Debt Audit (SRP-A-1) into a combined **deletion list +
target architecture report**. This is the strategic deliverable of the System Repair Plan:
the document that tells the team what to keep, what to remove, and what the ideal
steady-state system looks like.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-A2`
Branch: `arch/srp-a2-arch-report`

**Pre-condition**: Read `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md` in full before writing.
That document is your primary input.

Also read for context:
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (tool catalog)
- `platform/src/app/api/mcp/primitives/[tool]/route.ts` (dispatcher)
- `platform/src/lib/mcp/primitives_registry.ts` (post-SRP-F-1 state)

---

## Output Document Structure

Create `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md` with the sections below.

---

### §1 — Executive Summary

One-page summary: what the audit found, what the target state is, and the three most
impactful actions ranked by LoC removed + risk reduced.

---

### §2 — Deletion List

A precise, executable list of what to remove. Group by theme. Each entry:

```markdown
#### DEL-NNN: <Short Title>

- **Files**: `path/to/file.ts` (lines N–M)
- **Symbols**: `functionName`, `ClassName`, `TYPE_DEFINITION`
- **Reason**: Dead code / orphaned flag / duplicate type / etc.
- **LoC removed**: ~N
- **Blockers**: None / Must remove X first / Gated on flag removal
- **Recommended PR**: One-liner description of what the PR does
- **Risk**: LOW / MEDIUM / HIGH
```

**Required themes to cover**:

**Theme 1: Legacy Orchestrator Removal**
- All code reachable only when `MARSYS_FLAG_R11V2_USE_ADAPTERS=false`
- The `createOrchestrator()` function and its callees
- `single_model_strategy` and `SingleModelStrategyConfig`
- The `false` branch of the adapter flag gate in the route handler
- Estimated trigger: after the adapter path has been stable in production for 30 days
  (i.e., not before ~2026-06-22 given deploy of 2026-05-22)

**Theme 2: Deprecated Symbol Cleanup**
- `PRIMARY_TOOL_NAMES` (zero call sites, `@deprecated`)
- Any other `@deprecated` symbols confirmed to have zero call sites in SRP-A-1

**Theme 3: Orphaned Feature Flag Removal**
- For each flag in SRP-A-1 Category B confirmed safe to remove:
  - Remove from `feature_flags.ts`
  - Remove from `deploy.yml`
  - Note the required `gcloud run services update --remove-env-vars` step
  - AIOps flags (`ADAPTERS_ENABLED`, `CONSUME_UI_V2_ENABLED`) were scheduled for
    ~2026-05-28 — confirm and include

**Theme 4: Shared Vocabulary Layer**
- Create a single `platform/src/lib/types/shared_enums.ts` defining:
  - `Valence = 'benefic' | 'malefic' | 'context-dependent'`
  - `SignificanceTier = 'tier_1' | 'tier_2' | 'tier_3'`
  - `QueryDomain` (union of all domain strings)
- Delete per-file duplicate enum definitions
- Note: this is a refactor, not a deletion. Include it here as a "replacement" item.

---

### §3 — Target Architecture

Narrative description of the ideal steady-state system, covering:

**§3.1 — Two-Pipeline Architecture**

```
                    ┌─────────────────────────────────────────┐
                    │           Portal /api/query              │
                    │                                          │
                    │  MARSYS_FLAG_R11V2_USE_ADAPTERS          │
                    │         ┌───────────┐                    │
                    │  true ──│ Adapter   │── runAgenticLoop() │  ← Current production
                    │         │  + B.11   │   up to 8 iters    │
                    │         └───────────┘                    │
                    │                                          │
                    │  false ─│ Classic   │── single synthesis │  ← Sunset candidate
                    │         │ Orch.     │   1-2 LLM calls    │
                    │         └───────────┘                    │
                    └─────────────────────────────────────────┘
```

Describe:
- Why the adapter pipeline is the strategic path (agentic, provider-agnostic, extensible).
- A concrete 6-month sunset plan for the classic orchestrator (milestone: 30 stable days
  → flag removal PR → monitor 14 days → delete classic code).
- How to ensure the flag is truly clean-removable (no hidden consumers).

**§3.2 — Single Vocabulary Layer**

Current state: `valence`, `significance`, `domain`, `QueryPlan` field types are each
defined 2–5 times across `platform/src/`, `platform-mcp/src/`, and `00_ARCHITECTURE/`.

Target state: All shared enums defined in `platform/src/lib/types/shared_enums.ts` and
imported by every consumer. `platform-mcp/` imports from a shared package or copies only
what the sidecar needs. Schema validation at the border (Zod schemas in MCP tools use
the canonical vocabulary).

Migration path: Create shared_enums.ts → update imports → delete duplicates (one PR per
vocabulary type to keep diffs reviewable).

**§3.3 — primitives_registry.ts as Single Source of Truth**

Current state: MCP dispatch whitelist (`primitives_registry.ts`) and MCP server registrations
(`server.ts`) are maintained separately and can drift. This is what caused FIX-1.

Target state: Auto-sync tooling. Proposal:
```
Option A — Generated: primitives_registry.ts is auto-generated from server.ts at build time.
  A CI step runs the generator and fails if the committed file differs.
  Low manual maintenance, high reliability.

Option B — Validated: A CI test asserts that every tool in server.ts appears in
  primitives_registry.ts and vice versa. No generation, just a gate.
  Lower build complexity, still catches drift.
```

Recommend one option with rationale. Include the command/script outline.

**§3.4 — Logging Discipline**

Current state: `params_json` in msr_sql.ts logged plan values, not actual filter values
(FIX-7). Pattern may exist in other retrieval tools.

Target state: A lint rule or code convention: "every structured log entry's filter fields
must reference the variables actually passed to SQL". Proposal: add an ESLint custom rule
or a PR checklist item for retrieval tool changes.

**§3.5 — Test Coverage Targets**

Target: ≥ 80% branch coverage on all retrieval tools in `platform/src/lib/retrieve/`.

Current baseline (from SRP-A-1 audit): approximately N%.

Path to 80%:
- SRP-T-1 adds coverage for msr_sql, lel_query, query_ephemeris.
- Remaining gaps: [list from A-1 audit].
- Estimated sessions to reach 80%: N (can be done incrementally, 2-3 tools per session).

---

### §4 — Implementation Roadmap

A phased execution plan for the deletion list and architecture changes. Keep it practical:

| Phase | Scope | Prereq | Est. Effort |
|-------|-------|--------|-------------|
| Phase R.1 | Orphaned flag cleanup (Theme 2 + 3) | SRP-F-1 deployed 30 days | 1 session |
| Phase R.2 | Shared vocabulary layer (Theme 4) | None | 2 sessions |
| Phase R.3 | primitives_registry auto-sync | None | 1 session |
| Phase R.4 | Classic orchestrator sunset | R11V2 stable 30 days | 1 session |
| Phase R.5 | Coverage push to 80% | SRP-T-1/T-2 merged | 2-3 sessions |

---

## Acceptance Criteria

- [ ] Deletion list covers ≥ 500 LoC across the themes.
- [ ] Every deletion entry has file path, symbols, reason, LoC, blocker, risk.
- [ ] Target architecture covers all three channels (MCP, portal Classic, portal Claude Style).
- [ ] 6-month sunset plan for classic orchestrator is concrete and dateable.
- [ ] Implementation roadmap has ≥ 4 phases with prereqs and effort estimates.
- [ ] `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md` committed.
- [ ] PR opened from `arch/srp-a2-arch-report`.
- [ ] NO production code files modified.

## Session Close

Commit message:
```
arch(srp-a2): target architecture report v1.0 — deletion list + ideal system design

Deletion list: ~Xk LoC across legacy orchestrator, orphaned flags, duplicate types.
Architecture: two-pipeline model, shared vocabulary layer, primitives registry auto-sync,
logging discipline, coverage targets. 4-phase implementation roadmap with dateable milestones.
```
