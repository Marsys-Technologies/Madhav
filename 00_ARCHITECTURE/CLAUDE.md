---
artifact: CLAUDE
version: 1.0
status: CURRENT
backfill_note: >
  Frontmatter backfilled by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  This is the 00_ARCHITECTURE folder-instructions file for Claude Code.
---

# 00_ARCHITECTURE — Instructions

This folder contains the project's governing documents.

## Primary file
`PROJECT_ARCHITECTURE_v2_1.md` — the blueprint. Do not modify without native's explicit approval and a version bump (v2.1 → v2.2 for minor; v3.0 for architectural change).

## Other files in this folder
- `SESSION_LOG.md` — chronological log of sessions, their outputs, and next-session objectives. Update at end of every session.
- `GOVERNANCE_STACK.md` (future) — version registry, confidence ledger, contradiction log, falsifier registry
- `FILE_INDEX.md` (future) — master index of all project artifacts

## Discipline
- Every version change produces a changelog entry
- Major version bump (v2.1 → v3.0) requires native's explicit approval
- Minor version bump (v2.1 → v2.2) for defect fixes; document in changelog
