---
canonical_id: CLAUDECODE_BRIEF_MCP_M3_M4_SESSION_MEMORY
version: 1.0
status: READY-FOR-EXECUTION — M3 session state + memory, M4 chart-switch advisory
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASES M3 + M4)
depends_on: M2 (select_chart param path), M1 (principal)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: live code, read 2026-06-30
hard_constraints:
  - new MCP session store (none exists today); `conversations` table is the design PRECEDENT, not reused as-is
  - memory scoped per (user × chart); entitlement re-checked on recall (a grant can be revoked)
  - scoped DELETE only (reverse-citation gate); VITEST; migrations: next free number (verify; ≥382)
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — MCP M3 (session + memory) + M4 (chart-switch advisory)

> The MCP server is stateless by design (D10). M3 adds OPTIONAL durable state so a returning user resumes and
> select_chart sticks — without breaking the stateless request model (state is looked up, not held in the
> connection). M4 is a small advisory riding on M3's state.

## §1 — Ground truth (verified)
- NO `mcp_sessions` table, no generic per-user session store exists. M3 = build.
- Closest precedent: `public.conversations` (`0001_brahma_baseline.sql:1730-1743`) — keyed `user_id` + NOT-NULL
  `chart_id`, module 'build'|'consume'. Good schema template but NOT directly reusable (requires chart_id;
  module-constrained). Use as design reference only.
- There is NO `mimamsa_preferences` table (a prior scar referenced one that doesn't exist — ignore).

## §2 — M3.1 Session-state store (the one real decision — resolved)
**Decision: create a new `mcp_sessions` table** (chart-agnostic-capable; a session may exist before a chart is
chosen). Migration: next free number across BOTH migration dirs — supabase dir is at 381, platform dir at 364;
**use 382 in `platform/supabase/migrations/`** after a cross-dir collision check (`382_mcp_sessions.sql`).
Minimal schema: `session_id` (uuid PK), `user_uid` (text, NOT NULL), `active_chart_id` (uuid, NULLABLE),
`created_at`, `last_seen_at`, `state_json` (jsonb for small per-session scratch). Keyed by user; active chart
optional. Statelessness preserved: each `POST /mcp` looks up the row by a client-supplied session key, mutates,
writes back — no in-process session held.

## §3 — M3.2/M3.3 Memory + continuity + M4 advisory
- **M3.2 conversation memory:** durable per (user × chart). Reuse the `conversations`/`conversation_messages`
  precedent OR a lean `mcp_session_messages` keyed to `mcp_sessions`. Add `recall_session` +
  `list_my_sessions` tools (both chart-agnostic at param level; scoped to `principal.uid`). **On recall,
  re-check entitlement** for the session's `active_chart_id` (a view-grant can be revoked between sessions —
  never replay data the user can no longer access). Memory is the user's own; never cross-user.
- **M3.3 continuity:** `select_chart` (M2) now persists `active_chart_id` into `mcp_sessions`; subsequent
  per-chart calls may omit `chart_id` and inherit the active one (still gated).
- **M4.1 chart-switch advisory (ruled: warn, not block):** when a call's `chart_id` differs from the session's
  `active_chart_id`, return a clear advisory in the tool result ("you've switched to chart X; start a new
  conversation to avoid mixing chart contexts") — advisory only, the call still proceeds (after the gate). This
  needs M3's state to detect the delta.

## §4 — Acceptance criteria
- `mcp_sessions` migration applied (number verified collision-free); statelessness preserved (no in-process
  session state; lookup-mutate-writeback).
- A returning user resumes; `recall_session`/`list_my_sessions` return only that user's sessions; recall
  re-checks entitlement and refuses a now-unentitled chart's data.
- Memory scoped per (user × chart); zero cross-user leakage (prove with 2 users).
- `select_chart` persists active chart; per-chart calls inherit it; switching charts surfaces the M4 advisory
  (warn, not block).
- Any DELETE is user/session-scoped behind the reverse-citation gate; Vitest; chart-agnostic gate green;
  retrieval FROZEN.

## §5 — VERIFICATION PHASE (mandatory; phase NOT done until ALL pass — independent Auditor)
**V1 — Build gate:** both packages `npm run build` exit 0; `typecheck-mcp` CI green.
**V2 — Migration safety:** the `mcp_sessions` (+ any message) migration applied to prod; migration number
verified collision-free across BOTH migration dirs (run the cross-dir check; supabase dir was at 381 — use the
next free, coordinate so M5/M6 migrations don't collide); migration is additive (no destructive change to
existing tables); rollback note present.
**V3 — Tests:** session create/lookup/writeback; `recall_session`/`list_my_sessions` scoped to principal.uid;
the entitlement RE-CHECK on recall (revoked grant → refuse replay); the M4 switch-delta detection. Vitest green.
**V4 — Deploy + revision match:** deployed amjis-mcp revision SHA == merged SHA.
**V5 — Behavioral proof on PROD (≥2 users):**
  - statelessness preserved: confirm each POST /mcp still creates a fresh server (no in-process session held);
    state is DB lookup-mutate-writeback only.
  - user A resumes a prior session; `list_my_sessions` returns ONLY A's sessions (B's absent — prove isolation).
  - recall of a session whose active_chart_id the user is NO LONGER entitled to → refused (revoke a grant, then recall).
  - `select_chart` persists active chart; a subsequent per-chart call omitting chart_id inherits it AND is still
    gated; switching to a different chart surfaces the M4 advisory (warn, call still proceeds after gate).
**V6 — Invariants:** memory strictly per (user × chart); zero cross-user leakage (the headline security check);
any DELETE was user/session-scoped with a reverse-citation report; retrieval untouched; chart-agnostic green.
**On ANY V-failure:** remediation loop (charter §4); no advance until V1–V6 pass.

*End of CLAUDECODE_BRIEF_MCP_M3_M4_SESSION_MEMORY v1.0. Next: M5 production OAuth (can parallelize with M2/M3).*
