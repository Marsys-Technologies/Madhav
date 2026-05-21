---
artifact: CLAUDECODE_BRIEF.md
canonical_id: CLAUDECODE_BRIEF
version: 5.0
status: IN_PROGRESS
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-21
authored_for_session: PHASE-4C-CLOSE
purpose: >
  PHASE-4C-CLOSE orchestrator. Ships Phase 4C P0 fixes — F.1 Muhurat Finder
  sidecar overload (Option A SQL cache path + Option D infra uplift) and F.2
  Ask-Madhav initialMessages prop drop (ConsumeChatV2 destructuring fix).
  Deploys to Cloud Run, runs post-deploy Chrome MCP smokes, closes PR #142
  without merge, archives dead branch.
  Operates from /Users/Dev/Vibe-Coding/Apps/Madhav (main checkout).

scope_note: >
  Phase 4C P0 fixes only. Does NOT touch 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**,
  06_LEARNING_LAYER/**, .geminirules, .env.local. Does not pop or apply any pre-existing stash.

# ════════════════════════════════════════════════════════════════════════════
# EXECUTION STATE — orchestrator updates this YAML after every packet
# ════════════════════════════════════════════════════════════════════════════
packet_status:
  P1:  PENDING    # F.1 brief status flip DRAFT → APPROVED
  P2:  PENDING    # F.2 fix — apply WRAPUP-S3 initialMessages prop fix
  P3:  PENDING    # F.2 tests
  P4:  PENDING    # F.1 fix Option A (panchang_daily_reader + cache path)
  P5:  PENDING    # F.1 fix Option D (sidecar deploy flags)
  P6:  PENDING    # Validator triple
  P7:  PENDING    # PR open, CI watch, merge, deploy
  P8:  PENDING    # Chrome MCP smokes (F.1+F.2+R8)
  P9:  PENDING    # Final summary + CURRENT_STATE v5.41 + brief COMPLETE
  P10: PENDING    # Close PR #142 without merge; archive dead branch

last_completed_packet: null
last_halt: null
session_resumed_count: 0

execution_order:
  - P1
  - P2
  - P3
  - P4
  - P5
  - P6
  - P7
  - P8
  - P9
  - P10

branch: feature/phase-4c-prod-fixes

may_touch:
  - CLAUDECODE_BRIEF.md
  - 00_ARCHITECTURE/BRIEFS/F1_MUHURAT_OVERLOAD_BRIEF_v1_0.md
  - platform/src/components/consume/ConsumeChatV2.tsx
  - platform/src/components/consume/__tests__/**
  - platform/python-sidecar/panchang_engine/panchang_daily_reader.py
  - platform/python-sidecar/panchang_engine/muhurat.py
  - platform/python-sidecar/routers/muhurat.py
  - platform/python-sidecar/tests/test_panchang_daily_reader.py
  - platform/python-sidecar/tests/test_muhurat_cache_path.py
  - platform/cloudbuild-sidecar.yaml
  - 00_ARCHITECTURE/CONDUCTOR/phase4c_close/**
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - .gemini/project_state.md

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - .geminirules
  - .env.local
  - 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
  - 00_ARCHITECTURE/CONDUCTOR/session_queue.yaml
  - platform/src/app/clients/[id]/consume/page.tsx
---

# PHASE-4C-CLOSE Orchestrator Brief

## §1 — Mission

Ship Phase 4C P0 fixes on branch `feature/phase-4c-prod-fixes`, merge to main,
deploy to Cloud Run, smoke-test, close PR #142 without merge, archive dead branch.

## §2 — Operating principles

- **No git add -A.** Stage specific files only.
- **Co-Authored-By trailer** on every commit: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
- **Halt-on-doubt.** Write HUMAN_GATE_<id>.md, set last_halt, STOP.
- **State lives in packet_status.** Update after every packet via Edit.

## §3 — Packet ledger

| Packet | Title | Status |
|---|---|---|
| P1 | F.1 brief DRAFT → APPROVED | PENDING |
| P2 | F.2 fix — initialMessages prop | PENDING |
| P3 | F.2 tests | PENDING |
| P4 | F.1 Option A — panchang_daily_reader + cache path | PENDING |
| P5 | F.1 Option D — sidecar deploy flags | PENDING |
| P6 | Validator triple | PENDING |
| P7 | PR + CI + merge + deploy | PENDING |
| P8 | Chrome MCP smokes | PENDING |
| P9 | Final summary + CURRENT_STATE v5.41 | PENDING |
| P10 | Close PR #142 + delete dead branch | PENDING |

## §4 — Halt conditions

- ConsumeChatV2.tsx signature drifted from WRAPUP-S3 analysis → HUMAN_GATE_P0_DRIFT.md
- Existing code depends on initialMessages always starting undefined → HUMAN_GATE_P2_SEMANTICS.md
- TypeScript or vitest fails on F.2 fix → diagnose first, halt if not resolved in 2 iterations
- Sidecar tests fail and root cause not identified in 2 iterations → halt
- Validator regresses past bounds (schema exit >2, drift exit >3, mirror exit >0)
- CI fails on PR
- Cloud Build deploy fails
- F.1 smoke shows results >5s (cache path didn't engage) → HUMAN_GATE_P8_CACHE_MISS.md
- gh pr close on #142 errors

## §5 — Resumability

On launch: read packet_status, find first PENDING packet, execute.
Increment session_resumed_count each resume.
