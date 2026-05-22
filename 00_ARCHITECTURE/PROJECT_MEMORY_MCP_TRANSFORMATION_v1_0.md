---
artifact: PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
status: LIVING
version: 1.0
authored_by: Claude (Cowork session, Opus 4.7)
authored_on: 2026-05-22
audience: every future Cowork session and every Claude Code session in Antigravity IDE
disposition: persistent operating principle for the MCP Transformation project
scope: project-spanning; read at every session open while MCP Transformation is in flight
---

# Project Memory — MCP Transformation

## §1 — Project name

**MCP Transformation.** This is the operator-blessed name for the v3.1 rebuild of the MARSYS-JIS MCP server, comprising 17 sessions across phases v3.1.0 (foundation) → v3.2 (classical grounding) → v3.3 (depth backfill) → v3.4 (epistemic refinement + red-team + final seal).

All artifacts under this project use the prefix `MCPT` where a short identifier is needed (queue files, worktree directory names, branch names, etc.). The full phrase "MCP Transformation" is used in prose, master-plan titles, and external references.

## §2 — Tooling separation (load-bearing)

**Cowork is for planning. Claude Code (extension running inside Google Antigravity IDE) is for implementation.** Per native ruling, 2026-05-22.

This separation is operationally strict for the duration of the MCP Transformation project:

| Surface | Used for | Used by |
|---|---|---|
| **Claude in Cowork** | Architectural design, plan authoring, brief writing, review, post-implementation analysis, governance artifact authoring | The native (Abhisek Mohanty) working with Claude (Opus 4.7 or Sonnet 4.7) interactively |
| **Claude Code extension in Google Antigravity IDE** | All code implementation; all migration authoring + application; all test writing + running; all commits, pushes, PRs; all sub-agent spawning by the Conductor; all autonomous wave execution | Conductor instances + their spawned sub-agents, running per-worktree, mostly autonomously |

**Consequences:**

- Cowork sessions DO NOT edit application code (`platform/`, `platform-mcp/`) in this project. They edit governance artifacts only (`00_ARCHITECTURE/`, `CLAUDE.md`, `.geminirules`).
- All implementation prompts (Conductor kickoff prompts, sub-agent briefs' shell commands, gate commands) are authored *for* the Claude Code extension in Antigravity IDE — not for Cowork, not for the web `claude.ai`, not for Claude Chat.
- The Conductor itself runs in Claude Code in Antigravity (per the existing `00_ARCHITECTURE/CONDUCTOR/` pattern). It spawns sub-agents via the Task tool inside Claude Code; those sub-agents are also Claude Code instances.
- When a Cowork session authors a brief whose `gate_command` or example terminal commands invoke `claude`, the command name refers to the Claude Code CLI invoked by the Antigravity extension; not the Cowork CLI.

## §3 — Autonomy posture

Per the MCP v1 precedent (native ruling 2026-05-21) and confirmed for MCP Transformation:

- `requires_human_approval: false` on every queue entry except the final v3.4-S2 red-team + sealing entry.
- `--dangerously-skip-permissions` enabled on every Claude Code sub-agent spawn.
- Per-session autonomous commit + push to feature branches.
- Per-wave auto-PR creation; auto-merge after the wave-collector gate passes.
- Halts only fire on hard failures (gate command exit ≠ 0 with no clean recovery path, sub-agent reports `HALT_NEEDS_HUMAN`, or context-budget exhaustion mid-session).

## §4 — Where the master plan lives

`00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md` is the single source of truth for the parallel execution. Every Conductor instance reads it at start. The plan includes phase summary, dependency graph, wave structure, worktree allocation, migration-number reservations, source-data manifest, and the halt-response runbook.

## §5 — Why this memory file exists

Without this file, every future session has to re-discover the operating principles in §2 + §3 from context. With it, a Cowork session opening on this project reads `CLAUDE.md` + this file and immediately knows it does not author code; a Claude Code session opening in Antigravity reads its brief + the master plan + this file and knows it has full autonomy except where explicitly gated.

Read this file at every session open until MCP Transformation closes at v3.4-S2.

---

*End of PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md. Living until MCP Transformation closes; archive at v3.4-S2 close.*
