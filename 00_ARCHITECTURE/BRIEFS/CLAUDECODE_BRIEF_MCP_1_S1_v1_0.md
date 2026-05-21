---
artifact: CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Cowork 2026-05-21
authored_at: 2026-05-21
session_id: MCP-1-S1
session_name: MCP-1-S1 — Foundation (platform endpoint + auth + envelope + admin keys CRUD)
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: (self — this is the reference standard)
predecessor_session: MCP-0-AUTHOR (brief authoring meta-session)
next_session_anticipated: MCP-2-S1 (MCP server scaffold)
---

# CLAUDECODE_BRIEF — MCP-1-S1
## Foundation: platform endpoint + auth + envelope + admin keys CRUD

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This is the **foundation session** — it adds the `/api/mcp/*` HTTP surface
on the platform that the MCP server (built in MCP-2-S1) will call. No
MCP server work happens in this session.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-1-S1 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-0-AUTHOR (sub-briefs authored) |
| Anticipated next | MCP-2-S1 (MCP server scaffold) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **full read**; this session
   implements §5.1 (file structure), §5.2 (data flow for `ask_madhav`),
   §4.2 (response envelope contract — including synthesis_audit and
   suggested_followups per D-additions 2026-05-21), §4.3 (API key auth
   model), §6 governance carry-over rules
3. `platform/src/lib/firebase/server.ts` — read existing `getServerUser()`
   semantics; your auth lib mirrors this pattern
4. `platform/src/app/api/chat/consume/route.ts` — **read fully**; this is
   the orchestrator you wrap. Understand the existing call sequence:
   getServerUser → planner → arbitrate → compose_bundle → tools →
   synthesis → trace logging. Your `/api/mcp/execute` reuses these helpers,
   does not duplicate them.
5. `platform/src/lib/pipeline/pipeline_planner.ts` — understand the
   PipelinePlan output shape; your envelope returns it in the `plan` field
6. `platform/supabase/migrations/` — check the latest migration number to
   pick the next sequential one (likely 070; verify)
7. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §C.1–§C.6

Skim only:
- `platform/src/components/admin/` — to model the admin UI on existing patterns

---

## §3 — Scope (11 items — execute in order; commit after each)

### Item 1 — Migration 070: `mcp_api_keys` table

**What:** Create `platform/supabase/migrations/070_mcp_api_keys.sql` with
the schema from MCP_BRIEF §4.3. Apply locally if a local Supabase is
running; otherwise just author the file (the deploy pipeline applies it).

**AC.MCP_1_S1.1:** File exists; SQL is valid; indexed on `user_uid` and
`(key_hash, revoked_at IS NULL)` for fast lookup.

**Why:** Persistent home for API keys; bcrypt-hashed; bound to Firebase UID
+ audience_tier.

### Item 2 — Auth library (`platform/src/lib/mcp/auth.ts`)

**What:** Export `validateMcpKey(authHeader: string)` that:
- Extracts `Bearer <key>` from the header
- Splits prefix `mcp_<env>_` from the random tail
- Looks up by prefix (key_id) in `mcp_api_keys` where `revoked_at IS NULL`
- bcrypt-compares the tail against `key_hash`
- Updates `last_used_at` on success
- Returns `{user_uid, audience_tier, key_id} | null`

**AC.MCP_1_S1.2:** Function exported; types defined in
`platform/src/lib/mcp/types.ts`; rejects invalid tokens with `null`; never
throws (caller decides how to respond).

**Why:** Single source of truth for MCP authentication. Every MCP-side
endpoint calls this before doing work.

### Item 3 — Epistemics envelope builder (`platform/src/lib/mcp/epistemics.ts`)

**What:** Export:
- `buildEnvelope({ok, trace_id, audience_tier, result, citations?, plan?, predictions_logged?, synthesis_audit?, suggested_followups?, warnings?}): McpEnvelope` — the success envelope per MCP_BRIEF §4.2
- `buildErrorEnvelope({trace_id, error_class, message, remediation?}): McpEnvelope` — the error envelope
- `buildEpistemicsBlock({surgical, confidence_band, horizon_days?, falsifier?}): EpistemicsBlock`
- `buildSynthesisAudit({l25_tools_fired, l25_contribution_summary, dominant_signals, domains_touched, holistic_read_passed}): SynthesisAuditBlock`

**AC.MCP_1_S1.3:** All four functions exported; return types match the
JSON shape in MCP_BRIEF §4.2 exactly; unit-tested.

**Why:** Envelope is the load-bearing API contract. Centralized builder
prevents drift between endpoints.

### Item 4 — Suggested followups generator (`platform/src/lib/mcp/suggested_followups.ts`)

**What:** Export `generateSuggestedFollowups(plan: PipelinePlan, result: SynthesisResult): string[]`
that returns 2-3 plausible next questions based on:
- Tools the planner DEPRIORITIZED (in `plan.tool_calls[]` with `priority: 3` that ran)
- Query classes NOT triggered (e.g., if class was "factual", suggest a
  "holistic" follow-up)
- Domains adjacent to those touched (per `synthesis_audit.domains_touched`)

Phase-1 implementation may be heuristic (template-based); a richer LLM-driven
version is post-v1.

**AC.MCP_1_S1.4:** Function exported; returns non-empty array for any
non-trivial query; unit-tested.

**Why:** Per MCP_BRIEF §4.7 — major UX win for Claude as client.

### Item 5 — `/api/mcp/execute` endpoint

**What:** Author `platform/src/app/api/mcp/execute/route.ts` (POST handler):

1. Validate service-to-service identity token (audience: `amjis-web` URL);
   reject with 401 if invalid
2. Read `X-MCP-User`, `X-MCP-Audience-Tier`, `X-MCP-Key-Id` headers (set by
   MCP server after its own Bearer validation)
3. Parse body: `{tool: "ask_madhav" | "plan_query" | "execute_plan", params: {...}}`
4. For `ask_madhav`: invoke the same orchestrator path as
   `/api/chat/consume/route.ts` but in single-shot mode (no conversation
   loading per MCP_BRIEF D10). Reuse `callPipelinePlanner`,
   `arbitrateBudgets`, `hydrateBundle`, parallel tool execution,
   `createOrchestrator().synthesize`. Capture `query_id` as `trace_id`.
5. For `plan_query`: call `callPipelinePlanner` only; return PipelinePlan;
   no execution
6. For `execute_plan`: validate plan against `PipelinePlanSchema`; re-check
   audience-tier-permitted tools; run from arbitrate onward
7. Build envelope via `buildEnvelope` with `synthesis_audit` (filled from
   what tools fired) + `suggested_followups` + `predictions_logged` (from
   PPL writer when present; for MCP-1-S1 ppl_writer doesn't exist yet —
   leave empty array, MCP-4-S1 wires it)
8. Return JSON

**AC.MCP_1_S1.5:** Endpoint live; returns valid envelope with
`synthesis_audit`, `suggested_followups`, `trace_id` populated;
service-to-service auth blocks unauthenticated requests; integration test
covers happy path + auth-fail path.

**Why:** This is the load-bearing endpoint. Everything else exists to
support this.

### Item 6 — `/api/mcp/keys` admin CRUD

**What:** Author `platform/src/app/api/mcp/keys/route.ts`:
- GET (list user's keys; admin sees all): returns `[{key_id, label, audience_tier, created_at, last_used_at, revoked_at}]`
- POST (create key; super-admin only): body `{user_uid, audience_tier, label}`; generates `mcp_<env>_<random32>`, bcrypts it, inserts row, returns the full key ONCE (`{key_id, full_key, ...}`)
- DELETE `/api/mcp/keys/[key_id]` (revoke; super-admin or key owner): sets `revoked_at`

**AC.MCP_1_S1.6:** All three operations work; full key returned exactly
once on creation; revocation prevents future auth; super-admin gates
enforced via existing `isSuperAdmin` helper.

**Why:** Admin needs a way to issue and revoke keys.

### Item 7 — Admin UI: `/admin/mcp/keys`

**What:** Author minimal admin page under `platform/src/app/admin/mcp/keys/`:
- Server component: lists keys (calls GET)
- "Create new key" form (calls POST, displays full key in a modal with
  copy button, warns "this is the only time it's shown")
- Revoke button per row (calls DELETE)

Style: match existing admin UI patterns. No fancy framework — same
`@/components/admin/*` primitives as elsewhere.

**AC.MCP_1_S1.7:** Page renders for super-admin; non-admin gets 403;
create flow displays full key exactly once; revoke flow works without
page reload.

**Why:** Native (you) needs a way to mint your own key for personal use
in Claude Chat / Cowork.

### Item 8 — Schema validator + drift detector check

**What:** Run `python platform/scripts/governance/schema_validator.py` and
`python platform/scripts/governance/drift_detector.py`. Both should pass
(this session adds new files; existing canonical artifacts unchanged).

**AC.MCP_1_S1.8:** Both scripts exit 0.

**Why:** Per CLAUDE.md governance discipline — every change passes drift
+ schema validation.

### Item 9 — Jest tests for auth + epistemics + suggested_followups

**What:** Author tests under `platform/src/lib/__tests__/mcp/`:
- `auth.test.ts` — valid key, invalid key, revoked key, malformed header, missing header (≥5 tests)
- `epistemics.test.ts` — envelope shape, error envelope, synthesis_audit shape, epistemics block (≥6 tests)
- `suggested_followups.test.ts` — non-empty result, deduplication, format (≥3 tests)

**AC.MCP_1_S1.9:** All tests pass; ≥14 tests total covering MCP-1-S1
surface.

**Why:** Quality bar per CLAUDE.md §J. Auth + envelope + followups are
all unit-testable.

### Item 10 — Integration test: `/api/mcp/execute` happy path

**What:** Author `platform/src/app/api/mcp/__tests__/execute.integration.test.ts`:
- Mock service-to-service token validation
- Mock principal headers
- Send `{tool: "ask_madhav", params: {query: "What is the current dasha?"}}`
- Assert envelope shape: `ok: true`, `trace_id`, `audience_tier`,
  `epistemics`, `result`, `synthesis_audit.holistic_read_passed`,
  `suggested_followups[]`

(Use the existing test harness pattern from `/api/chat/consume` integration
tests if any exist; otherwise scaffold minimally.)

**AC.MCP_1_S1.10:** Test passes; envelope shape validated end-to-end.

**Why:** Catches integration drift the unit tests miss.

### Item 11 — README in `platform/src/lib/mcp/`

**What:** Author `platform/src/lib/mcp/README.md` — one-pager describing:
- What's in this directory
- Auth flow (Bearer → validate → principal headers → endpoint)
- Envelope shape (link to MCP_BRIEF §4.2)
- How to add a new MCP-side helper

**AC.MCP_1_S1.11:** README exists; covers the four items above.

**Why:** Next session (MCP-2-S1) is in a different directory tree
(`platform-mcp/`); a README anchors the platform-side surface.

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-1-S1 opening. Will implement the foundation: migration 070,
`/api/mcp/execute`, `/api/mcp/keys`, `/api/mcp/keys` admin UI, auth +
envelope + suggested_followups libraries, tests. 11 scope items.
No `platform-mcp/` work in this session — that's MCP-2-S1."

---

## §5 — Scope constraints

### may_touch

```
platform/supabase/migrations/070_mcp_api_keys.sql                 # CREATE
platform/src/lib/mcp/auth.ts                                      # CREATE
platform/src/lib/mcp/epistemics.ts                                # CREATE
platform/src/lib/mcp/suggested_followups.ts                       # CREATE
platform/src/lib/mcp/types.ts                                     # CREATE
platform/src/lib/mcp/README.md                                    # CREATE
platform/src/app/api/mcp/execute/route.ts                         # CREATE
platform/src/app/api/mcp/keys/route.ts                            # CREATE
platform/src/app/api/mcp/keys/[key_id]/route.ts                   # CREATE
platform/src/app/admin/mcp/keys/page.tsx                          # CREATE
platform/src/app/admin/mcp/keys/CreateKeyDialog.tsx               # CREATE (if extracted)
platform/src/app/admin/mcp/keys/KeyList.tsx                       # CREATE (if extracted)
platform/src/lib/__tests__/mcp/auth.test.ts                       # CREATE
platform/src/lib/__tests__/mcp/epistemics.test.ts                 # CREATE
platform/src/lib/__tests__/mcp/suggested_followups.test.ts        # CREATE
platform/src/app/api/mcp/__tests__/execute.integration.test.ts    # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md          # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/pipeline/**                                      # planner unchanged
platform/src/lib/retrieve/**                                      # retrieval tools unchanged
platform/src/app/api/chat/consume/**                              # orchestrator route unchanged
platform/src/lib/firebase/**                                      # existing auth unchanged (we mirror, not modify)
platform-mcp/**                                                   # owned by MCP-2-S1; doesn't exist yet
01_FACTS_LAYER/**                                                 # L1 sealed
025_HOLISTIC_SYNTHESIS/**                                         # L2.5 sealed
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                            # planner prompt sealed
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                                # macro arc unchanged
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                          # appended in MCP-2-S1 with MCP_SERVER entry
CLAUDE.md                                                         # §E update is post-workstream-close
```

### Commit cadence

Commit after each scope item with format:

```
feat(mcp): MCP-1-S1 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_1_S1.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 11 scope items are completed, gate command passes, and commits
are pushed, emit:

```
---FINAL_SUMMARY---
session_id: MCP-1-S1
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
  - <sha_item_6>
  - <sha_item_7>
  - <sha_item_8>
  - <sha_item_9>
  - <sha_item_10>
  - <sha_item_11>
scope_items_completed:
  - AC.MCP_1_S1.1   # migration 070
  - AC.MCP_1_S1.2   # auth lib
  - AC.MCP_1_S1.3   # epistemics builder
  - AC.MCP_1_S1.4   # suggested_followups
  - AC.MCP_1_S1.5   # /api/mcp/execute
  - AC.MCP_1_S1.6   # /api/mcp/keys CRUD
  - AC.MCP_1_S1.7   # admin UI
  - AC.MCP_1_S1.8   # drift + schema validators pass
  - AC.MCP_1_S1.9   # unit tests pass
  - AC.MCP_1_S1.10  # integration test passes
  - AC.MCP_1_S1.11  # README
scope_items_failed: []
gate_command_runs:
  - name: mcp_1_s1_foundation_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  Foundation laid: migration 070 authored (apply post-merge), /api/mcp/*
  endpoints live, auth/envelope/followups libs in place, admin keys UI
  reachable for super-admin. Next session (MCP-2-S1) builds platform-mcp/
  Node service consuming these endpoints.
human_decision_needed: >
  <empty if PASS; otherwise: e.g. "migration 070 ordering conflict with
  parallel workstream — request guidance on renumbering">
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md.*
