---
artifact: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M4D_S1.md
status: COMPLETE
domain: governance
session_id: M4-D-S1
authored: 2026-05-02
authored_by: Cowork (housekeeping pass)
may_touch:
  - 00_ARCHITECTURE/**
  - .geminirules
  - .gemini/project_state.md
  - 00_ARCHITECTURE/SESSION_LOG.md
must_not_touch:
  - platform/src/**
  - platform/tests/**
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
gate: NAP.M4.7 native approval required before work item (j) — CURRENT_STATE M4→M5 flip
---

# CLAUDECODE_BRIEF — M4-D-S1 — M4 Macro-Phase Close

## Governing plan

`00_ARCHITECTURE/PHASE_M4D_PLAN_v1_0.md` (DRAFT → flip CURRENT at session open).
Read fully before any tool call. §3.1 lists the 10 work items (a)–(j).

## Entry gates (all must be satisfied before session proceeds)

1. M4-C formally CLOSED — M4_C_CLOSE_v1_0.md exists with status CLOSED. ✓ (2026-05-02)
2. NAP.M4.7 brief authored — 00_ARCHITECTURE/EVAL/NAP_M4_7_BRIEF_v1_0.md. ✓ (2026-05-02)
3. PHASE_M4D_PLAN_v1_0.md available. ✓ (2026-05-02)

## Pre-flight reads (in order)

1. This file.
2. CLAUDE.md §C items 1–11.
3. 00_ARCHITECTURE/CAPABILITY_MANIFEST.json.
4. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md — confirm active_macro_phase M4, M4-C closed, next M4-D-S1.
5. 00_ARCHITECTURE/PHASE_M4D_PLAN_v1_0.md — full read, §3.1 work items (a)–(j).
6. 00_ARCHITECTURE/EVAL/NAP_M4_7_BRIEF_v1_0.md — read §1–§4 and present §4 decision template to native NOW.
7. 00_ARCHITECTURE/M4_A_CLOSE_v1_0.md §3, M4_B_CLOSE §6, M4_C_CLOSE §6 — carry-forward rosters.
8. 00_ARCHITECTURE/SESSION_LOG.md last 3 entries.
9. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–§C.6 + §K.

## Work items (a)–(j)

See PHASE_M4D_PLAN §3.1 for full specification of each item.

(a) Compile full carry-forward roster from M4-A/B/C close docs.
(b) Author 00_ARCHITECTURE/EVAL/REDTEAM_M4_v1_0.md — IS.8(b) 9-axis red-team.
(c) CF.LL7.1 CDLM-patch disposition — default Option β (accept-as-M5-input).
(d) KR.M4A.RT.LOW.1 git tree — default Option β (defer).
(e) R.LL1TPA.1 final reachability record.
(f) DECISION-1 R.LL5DESIGN.1 propagation verify.
(g) Author 00_ARCHITECTURE/M4_CLOSE_v1_0.md.
(h) NAP.M4.7 sign-off — present brief, await native reply.
(i) Author 00_ARCHITECTURE/HANDOFF_M4_TO_M5_v1_0.md.
(j) CURRENT_STATE M4→M5 flip — ONLY after NAP.M4.7 APPROVED.

## Artifacts to produce

- 00_ARCHITECTURE/EVAL/REDTEAM_M4_v1_0.md
- 00_ARCHITECTURE/M4_CLOSE_v1_0.md
- 00_ARCHITECTURE/HANDOFF_M4_TO_M5_v1_0.md
- CURRENT_STATE update: M4→M5 (work item j, gated)
- CAPABILITY_MANIFEST.json: register three new artifacts above
- SESSION_LOG.md: append session entry

## Close criteria

All 10 work items (a)–(j) discharged.
If NAP.M4.7 not yet replied: close_status PARTIAL, work item (j) deferred to M4-D-S2.
