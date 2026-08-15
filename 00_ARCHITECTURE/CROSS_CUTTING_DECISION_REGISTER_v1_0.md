---
artifact: CROSS_CUTTING_DECISION_REGISTER_v1_0.md
version: 1.0
status: LIVING
role: >
  Append-only, tool-neutral register for decisions not owned by a live campaign ledger.
  CCD identifiers are resolved from this file at session close.
update_rule: >
  Append only. Never renumber, rewrite, or delete entries. Supersede a decision with a
  later CCD entry that names the earlier identifier.
---

# Cross-Cutting Decision Register

## How to use this register

Use this register only for a decision that is not owned by an active campaign ledger.
At session close, resolve the next `CCD-NNN` identifier from the live register, append
the decision with tool/date provenance, and reference the session, work-order, and
coordination lease that produced it.

| ID | Date | Tool | Status | Decision |
|---|---|---|---|---|
| CCD-001 | 2026-08-15 | Codex | ACTIVE | Establish Claude Code/Codex shared-brain parity: tool-neutral state, decision, lease, and session-log protocol; exclusive env-authenticated `marsys-jis` Codex MCP surface; Codex instruction and skill bridges. |
| CCD-002 | 2026-08-15 | Codex | ACTIVE | Round-trip acceptance marker: Codex wrote this bounded state change; a fresh Claude Code session must cite CCD-002 before appending its successor. |
| CCD-003 | 2026-08-15 | Claude Code | ACTIVE | Round-trip acceptance successor: Claude Code consumed CCD-002 and wrote CCD-003; a fresh Codex session must cite both identifiers. |
| CCD-004 | 2026-08-15 | Codex | ACTIVE | Close the onboarding verification: the canonical `.claude/skills` inventory is four active skills, not five; retain the MCP credential-rotation and validator-debt follow-ups as shared owner-visible work. |

## CCD-001 — Cross-tool onboarding and operating protocol

- **Authority:** native approval in the Codex onboarding session, 2026-08-15.
- **Rationale:** project-wide decisions previously had no canonical, monotonic, tool-neutral
  home. Codex and Claude Code need one durable state surface rather than chat-history handoffs.
- **Affected surfaces:** this register; `CURRENT_STATE_v1_0.md`; governance protocol; session
  templates and validator; Codex profiles; instruction/skill bridges.
- **Coordination:** L-11 on `campaign-coordination`; documentation/tooling only, no deploy,
  build/rebuild, database, migration, or application-code scope.
- **Supersession:** none.

## CCD-002 — Round-trip acceptance marker

- **Date:** 2026-08-15.
- **Tool:** Codex.
- **Status:** ACTIVE.
- **Decision:** Round-trip acceptance marker: Codex wrote this bounded state change; a fresh Claude Code session must cite CCD-002 before appending its successor.

## CCD-003 — Round-trip acceptance successor

- **Date:** 2026-08-15.
- **Tool:** Claude Code.
- **Status:** ACTIVE.
- **Decision:** Round-trip acceptance successor: Claude Code consumed CCD-002 and wrote CCD-003; a fresh Codex session must cite both identifiers.

## CCD-004 — Onboarding closure verification and standing follow-ups

- **Authority:** native closure instruction in the Codex onboarding session, 2026-08-15.
- **Skill-inventory correction:** the canonical `.claude/skills` tree contains exactly four
  active, valid skills — `create-migration`, `pr-description`, `run-checks`, and
  `session-close`. The reported fifth skill was an audit-count error: no fifth directory,
  `SKILL.md`, hidden entry, archived entry, or ignored entry exists in the worktree or
  `origin/main`. Codex discovery through `.agents/skills` is therefore complete at four,
  not a symlink-discovery failure.
- **SECURITY — owner action:** the pre-existing global Codex configuration contains an inline
  MCP credential in a URL. Rotate that credential and convert the global configuration to
  environment-sourced authentication; this is not repository work and was not changed here.
- **DEBT — shared dual-tool follow-up:** repository-wide validation retains schema 43 and drift
  218 findings. They predate this onboarding, are shared debt under the dual-tool protocol, and
  are a candidate first owner-authorized Codex assignment.
- **Supersession:** none.
