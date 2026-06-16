---
artifact: CLAUDECODE_BRIEF.md (R5 instance)
status: COMPLETE
authored_on: 2026-04-29
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R5 Timeline (LEL surface)"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md
phase_id: R5
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT, post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r5
branch: redesign/r5-timeline
parallelizable_with: [R1, R2, R3, R6]
corpus_write_authority: "APPEND-ONLY to 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md via /api/lel"
---

# CLAUDECODE_BRIEF — Portal Redesign R5 Timeline

## How this file got here

Copied into the R5 worktree from the project's per-phase brief pool. Renamed to activate `CLAUDE.md §C item #0`.

## Governing scope

Lands `/clients/[id]/timeline` — the UI home for LEL events and prospective predictions. Ships an append-only LEL writer endpoint and a parser. **No DB schema change** — LEL stays as markdown. Executes `EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md`. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R5_REPORT_v1_0.md`.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md` — pay particular attention to §4 (LEL writer is APPEND-ONLY; no edits to existing entries) and the parser tolerance requirements in §3.
3. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — read the file end to end so the parser correctly handles its actual format.
4. `CLAUDE.md §E` — Cross-cutting workstreams clause naming LEL + prediction log discipline.
5. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 4 (Timeline Room in Chart Profile flips its CTA when R5 closes).
6. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 + §3 R5 row.
7. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed.
2. No in-flight phase shares a `may_touch` glob with R5. (R5 is the only phase that writes to `01_FACTS_LAYER/` — append-only — so it has unique write authority that no other phase can shadow.)
3. Working tree clean. Branch `redesign/r5-timeline`.
4. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` parses with the parser this session lands. Run a parser dry-run before committing the parser code: load the file, log the parsed events count, abort if parse fails for ANY existing event.

If any fail: emit `pre_flight_failure` and halt.

## Acceptance criteria

Session does not claim close until ALL of:
1. EXEC_BRIEF §1–§5 deliverables landed (page, TimelineView, PredictionTable, EventCard, Log dialogs, parser, writer, /api/lel endpoint).
2. EXEC_BRIEF §6 tests pass — including parser tolerance tests and write-then-reparse round-trip.
3. **drift_detector.py is load-bearing this session** because LEL frontmatter version bumps. Confirm exit 0 explicitly in the closure report.
4. If R2 is already closed when R5 closes: edit R2's `<RoomCard>` Timeline Room CTA to flip from `disabled` to `href="/clients/[id]/timeline"`. Capture in closure report.
5. Closure report at `status: COMPLETE`.
6. Tracker §3 R5 row flipped to `status: closed`.
7. mirror_enforcer.py / schema_validator.py exit 0.
8. SESSION_LOG appended.
9. This file flipped to `status: COMPLETE`.

## One-line summary

Give LEL events and prospective predictions a real UI home — read-mostly with append-only super_admin writes — without touching the data model.

---
