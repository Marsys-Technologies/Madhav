---
artifact: CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-3-S2
session_name: MCP-3-S2 — read_asset, get_trace, list_recent_queries + rate limiting
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-3-S1 (10 surgical primitives + dispatcher)
next_session_anticipated: MCP-4-S1 (writes: log_prediction, record_outcome, flag_disagreement)
---

# CLAUDECODE_BRIEF — MCP-3-S2
## read_asset, get_trace, list_recent_queries + per-key rate limiting

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This session completes Phase MCP-3. It ships:
- **Tier 4 tool** (`read_asset`) — returns raw markdown of canonical artifacts.
- **Tier 5 observability tools** (`get_trace`, `list_recent_queries`) —
  expose the existing audit trail to MCP callers.
- **Rate limiter** — per-key RPM and daily token budget enforcement wired
  into all `/api/mcp/*` endpoints.

These are additive changes. No existing endpoints are restructured; the
rate limiter is middleware that wraps them.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-3-S2 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-3-S1 (10 primitives + dispatcher complete) |
| Anticipated next | MCP-4-S1 (writes: PPL + disagreement) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §4.1 Tier 4
   (read_asset) and Tier 5 (get_trace, list_recent_queries), §4.4 (rate
   limiting), §7.3 (Phase MCP-3 acceptance criteria)**
3. `platform/src/app/api/mcp/execute/route.ts` — understand where to call
   the rate limiter (before invoking the orchestrator)
4. `platform/src/app/api/mcp/primitives/[tool]/route.ts` — understand the
   handler pattern; rate limiter wires in the same position
5. `platform/src/app/api/audit/` or `platform/src/app/api/audit/[query_id]/`
   — read the existing audit/trace endpoint to understand how `get_trace`
   can delegate to it or call it internally

Skim only:
- `platform/src/lib/mcp/auth.ts` — refresh on the key_id and audience_tier
  fields; rate limiter keys on `key_id`

---

## §3 — Scope (7 items — execute in order; commit after each)

### Item 1 — Per-key rate limiter (`platform/src/lib/mcp/rate_limiter.ts`)

**What:** Author `platform/src/lib/mcp/rate_limiter.ts` that exports:

```typescript
interface RateLimitResult {
  allowed: boolean;
  reason?: 'rpm_exceeded' | 'daily_budget_exceeded';
  retry_after_seconds?: number;
}

export async function checkRateLimit(
  key_id: string,
  estimated_tokens?: number
): Promise<RateLimitResult>
```

Implementation:
- Use a rolling-window counter stored in a lightweight in-memory cache
  (e.g., a `Map<string, {count: number, window_start_ms: number}>`) for
  RPM tracking. Default limit: 60 RPM per key.
- Use a daily counter stored in Supabase `mcp_api_keys.daily_token_count`
  (new column, added via a migration or computed from `query_trace_steps`
  filtered by `key_id` + today's date). Default daily budget: 500,000
  tokens. If `estimated_tokens` is provided, check budget before execution;
  deduct after.

**Implementation decision for this session:** Use the Supabase
`query_trace_steps` table with a `WHERE key_id = $1 AND created_at > now()::date`
query to compute daily token usage — no new DB column required. RPM
tracking stays in-process (Map). Document this in a comment in the file
with a note that a Redis-based solution is Phase 2 hardening.

Also export a utility:
```typescript
export function buildRateLimitErrorEnvelope(reason: string): McpEnvelope
```
that returns `{ok: false, error: {class: "rate_limit", message: reason,
remediation: "Reduce request frequency or contact admin to raise limits."}}`.

**AC.MCP_3_S2.1:** `rate_limiter.ts` exists; `checkRateLimit` exported;
RPM check uses in-process rolling window; daily budget check queries
`query_trace_steps`; `buildRateLimitErrorEnvelope` exported; TypeScript
strict passes.

**Why:** Per MCP_BRIEF §4.4 — cost discipline requires per-key rate
limiting. The rate limiter protects against spam `ask_madhav()` calls that
would rack up LLM bills (Risk R3 in §8).

Commit: `feat(mcp): MCP-3-S2 item 1 — per-key rate limiter (RPM + daily token budget)`

---

### Item 2 — Wire rate limiter into all `/api/mcp/*` endpoints

**What:** Add rate-limiter middleware to the following existing handlers
(edit each file minimally — add 3-4 lines before the main handler logic):

- `platform/src/app/api/mcp/execute/route.ts`
- `platform/src/app/api/mcp/primitives/[tool]/route.ts`
- `platform/src/app/api/mcp/keys/route.ts` (POST/DELETE only — skip GET
  list; key management is admin-level and low-volume)

Call pattern:
```typescript
const rateLimitResult = await checkRateLimit(principal.key_id, estimatedTokens);
if (!rateLimitResult.allowed) {
  return NextResponse.json(
    buildRateLimitErrorEnvelope(rateLimitResult.reason ?? 'rate_limit'),
    { status: 429, headers: { 'Retry-After': String(rateLimitResult.retry_after_seconds ?? 60) } }
  );
}
```

For `ask_madhav`, `estimated_tokens` is unknown at invocation time (synthesis
tokens aren't known until synthesis completes). Use a conservative estimate
of 4000 tokens per `ask_madhav` call for the budget pre-check; the actual
count is deducted post-synthesis via the trace step logger.

**AC.MCP_3_S2.2:** Rate limiter called in all three handlers before work
is done; returns HTTP 429 with `Retry-After` header and error envelope on
limit hit; TypeScript strict passes in `platform/`.

**Why:** Rate limiting is only effective if applied before work begins —
not after. Adding it to existing endpoints is minimal-invasive change.

Commit: `feat(mcp): MCP-3-S2 item 2 — rate limiter wired into /api/mcp/* handlers`

---

### Item 3 — `/api/mcp/recent` endpoint (`platform/src/app/api/mcp/recent/route.ts`)

**What:** Author `platform/src/app/api/mcp/recent/route.ts` — GET handler:

1. Validate service-to-service token + MCP headers.
2. Parse query params: `limit` (default 20, max 100), `since` (ISO date,
   default 7 days ago).
3. Query `query_trace_steps` where `key_id = $key_id AND created_at > $since`
   ORDER BY `created_at DESC` LIMIT `$limit`.
4. Return `{ok: true, trace_id: null, audience_tier, epistemics: {surgical: true, ...}, result: { queries: [...] }}`.

Each query row in `result.queries`:
```typescript
{
  trace_id: string;
  created_at: string;
  tool: string;   // "ask_madhav" | "plan_query" | "execute_plan" | primitive name
  source: string; // "mcp" | "mcp_primitive"
  query_summary: string; // first 80 chars of the query string
}
```

**AC.MCP_3_S2.3:** Endpoint exists; GET with valid auth returns query
history; `limit` and `since` params work; TypeScript strict passes.

**Why:** `list_recent_queries` (the MCP tool in Item 5) calls this endpoint.
Also useful for the native to audit recent MCP usage via the admin UI.

Commit: `feat(mcp): MCP-3-S2 item 3 — /api/mcp/recent endpoint`

---

### Item 4 — `read_asset` MCP tool (`platform-mcp/src/tools/read_asset.ts`)

**What:** Author `platform-mcp/src/tools/read_asset.ts`.

The `read_asset` tool reads a canonical artifact by `canonical_id` and
returns its markdown. Implementation: the MCP server calls a new platform
endpoint `/api/mcp/asset` (or `/api/mcp/execute` with `tool: "read_asset"`)
which loads the artifact from disk (the canonical file path resolved from
`CAPABILITY_MANIFEST.json`).

**Architecture decision:** Add a lightweight `/api/mcp/asset` endpoint
to the platform (this session also adds that route in `platform/`). The
route:
1. Authenticates via service token + MCP headers.
2. Reads `canonical_id` from body.
3. Resolves path from a hardcoded safe map of `canonical_id → file_path`
   (not from user input directly — path traversal prevention).
4. Reads the file; applies audience-tier access control (for Phase 1, all
   authenticated callers get full access — per D12 full transparency).
5. Returns file content as markdown.

Tool description (§4.6-standard, ≥100 words):

```
What it does: Returns the raw markdown of a canonical MARSYS-JIS artifact
by its canonical_id (e.g., "MSR", "FORENSIC", "UCN", "CDLM", "CGM", "RM",
"LEL"). Use when you need the full text of a synthesis layer document, not
just a signal-level query result.

When to prefer: Prefer read_asset when you need to read an entire
document — e.g., the full CGM for a graph overview, or the full FORENSIC
for a birth-data audit. Prefer query_signals or query_chart_facts for
targeted fact lookups within the document.

Input shape hints: canonical_id — one of the known canonical IDs from the
CAPABILITY_MANIFEST. section — optional section filter (e.g., "§A" or "Tier
1"); if omitted, full document returned.

Output shape preview: {ok, result: {canonical_id, content: "<markdown>",
word_count, path}, trace_id, epistemics: {surgical: true}}.

Example: read_asset({canonical_id: "MSR"}) → returns full MSR markdown
(~514 signals, 30,000+ words); read_asset({canonical_id: "FORENSIC",
section: "Planetary Positions"}) → returns the Planetary Positions section.
```

Input schema:
```json
{
  "type": "object",
  "properties": {
    "canonical_id": { "type": "string" },
    "section": { "type": "string" }
  },
  "required": ["canonical_id"]
}
```

Export `registerReadAsset(server: McpServer, getPrincipal: () => Principal)`.

Also create `platform/src/app/api/mcp/asset/route.ts` (POST) with the
logic described above. The safe canonical_id → path map should include:
`MSR`, `UCN`, `CDLM`, `CGM`, `RM`, `FORENSIC`, `LEL`, `MACRO_PLAN`,
`PROJECT_ARCHITECTURE`. Reject unknown canonical_ids with `{ok: false,
error: {class: "validation", message: "Unknown canonical_id: " + id}}`.

**AC.MCP_3_S2.4:** `read_asset.ts` tool wrapper exists with §4.6 description;
`/api/mcp/asset` endpoint exists on platform; unknown canonical_id returns
validation error; TypeScript strict passes in both `platform/` and
`platform-mcp/`.

**Why:** Tier 4 tool — enables Claude to read the full MSR, CGM, or
FORENSIC document when a targeted query is insufficient. Per MCP_BRIEF §4.1,
the tool honors audience tier and section-level access (Phase 1: full
access for all authenticated callers per D12).

Commit: `feat(mcp): MCP-3-S2 item 4 — read_asset tool + /api/mcp/asset endpoint`

---

### Item 5 — `get_trace` and `list_recent_queries` MCP tools

**What:**

**`platform-mcp/src/tools/get_trace.ts`**:
- Calls `callPlatformPrimitive('get_trace', { trace_id }, principal)` which
  routes through `/api/mcp/primitives/get_trace`. Wait — `get_trace` is
  not in the surgical whitelist from MCP-3-S1. Instead, call the
  platform's existing `/api/audit/[query_id]` (or equivalent) endpoint
  directly from the client.
- Better architecture: expose a new thin endpoint at
  `platform/src/app/api/mcp/trace/[trace_id]/route.ts` that validates
  service token + MCP headers, then reads `query_trace_steps` for the
  given `trace_id`, and returns the full step ledger.
- The MCP tool `get_trace` calls
  `callPlatform('GET /api/mcp/trace/:trace_id', {}, principal)` (update
  `client.ts` with a `callPlatformTrace(trace_id, principal)` helper).
- Description (§4.6-standard, ≥100 words): focus on full transparency (D12)
  — full prompts, payloads, retrieval results returned; use for debugging
  a prior `ask_madhav` call; input is `trace_id` from any prior response.

**`platform-mcp/src/tools/list_recent_queries.ts`**:
- Calls `callPlatformRecent(params, principal)` helper in `client.ts`
  (a GET to `/api/mcp/recent`).
- Description (§4.6-standard, ≥100 words): focus on "see what this API
  key has called recently"; useful for audit and cost awareness.
- Input schema: `{ limit?: number, since?: string }`.

Also:
- Add `callPlatformTrace(trace_id, principal)` to `platform-mcp/src/client.ts`.
- Add `callPlatformRecent(params, principal)` to `platform-mcp/src/client.ts`.
- Create `platform/src/app/api/mcp/trace/[trace_id]/route.ts` (GET).
- Update `platform-mcp/src/server.ts` to register all 16 tools (add
  `registerGetTrace` and `registerListRecentQueries`).

**AC.MCP_3_S2.5:** Both tool files exist with §4.6 descriptions; both
register in `server.ts`; `/api/mcp/trace/[trace_id]` and `/api/mcp/recent`
endpoints exist on platform; `client.ts` updated with two new helpers;
TypeScript strict passes in both.

**Why:** Observability tier (Tier 5 per MCP_BRIEF §4.1). `get_trace`
enables Claude to investigate past queries; `list_recent_queries` gives
the native or Claude visibility into usage patterns and cost.

Commit: `feat(mcp): MCP-3-S2 item 5 — get_trace + list_recent_queries tools + trace endpoint`

---

### Item 6 — Jest tests for rate limiter and recent endpoint

**What:** Author tests under `platform/src/lib/__tests__/mcp/`:
- `rate_limiter.test.ts`:
  1. First call within RPM window → `allowed: true`
  2. 61st call in same window → `allowed: false, reason: "rpm_exceeded"`
  3. `buildRateLimitErrorEnvelope` returns correct error class

- `recent.test.ts`:
  1. GET with valid auth → returns array (can be empty)
  2. GET with invalid auth → 401
  3. `limit` param respected (mock DB response with 100 items, limit=5 → 5 returned)

Minimum: ≥6 tests total across both files.

**AC.MCP_3_S2.6:** Both test files exist; all tests pass
(`npx jest --testPathPattern="mcp/rate_limiter|mcp/recent" --passWithNoTests`).

**Why:** Rate limiter correctness is testable without a DB connection;
RPM window logic is pure in-process math. The recent-queries test validates
the endpoint respects auth and limit param.

Commit: `test(mcp): MCP-3-S2 item 6 — rate limiter + recent endpoint tests`

---

### Item 7 — Full gate command

**What:** Run the full gate command from `session_queue_MCP.yaml` MCP-3-S2:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP/platform &&
test -f src/app/api/mcp/recent/route.ts &&
test -f src/lib/mcp/rate_limiter.ts &&
npx tsc --noEmit &&
npx jest --testPathPattern="mcp/rate_limiter|mcp/recent" --passWithNoTests &&
cd ../platform-mcp &&
test -f src/tools/read_asset.ts &&
test -f src/tools/get_trace.ts &&
test -f src/tools/list_recent_queries.ts &&
npx tsc --noEmit
```

Fix any issues. Confirm all 16 tools are registered in `server.ts` (3 Tier
1/2 + 10 primitives + read_asset + get_trace + list_recent_queries).

**AC.MCP_3_S2.7:** Full gate command exits 0; server registers all 16 tools.

**Why:** Gate must pass before the session can be marked complete.

Commit: `chore(mcp): MCP-3-S2 item 7 — full gate passes; all 16 tools registered`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-3-S2 opening. Will implement: read_asset (Tier 4), get_trace +
list_recent_queries (Tier 5), per-key rate limiter, /api/mcp/recent and
/api/mcp/trace/[trace_id] endpoints. 7 scope items. All 16 v1 tools will
be registered in server.ts by end of this session."

---

## §5 — Scope constraints

### may_touch

```
platform/src/lib/mcp/rate_limiter.ts                            # CREATE
platform/src/app/api/mcp/recent/route.ts                        # CREATE
platform/src/app/api/mcp/asset/route.ts                         # CREATE
platform/src/app/api/mcp/trace/[trace_id]/route.ts              # CREATE
platform/src/app/api/mcp/execute/route.ts                       # UPDATE — rate limiter call (3-4 lines)
platform/src/app/api/mcp/primitives/[tool]/route.ts             # UPDATE — rate limiter call (3-4 lines)
platform/src/lib/__tests__/mcp/rate_limiter.test.ts             # CREATE
platform/src/lib/__tests__/mcp/recent.test.ts                   # CREATE
platform-mcp/src/tools/read_asset.ts                            # CREATE
platform-mcp/src/tools/get_trace.ts                             # CREATE
platform-mcp/src/tools/list_recent_queries.ts                   # CREATE
platform-mcp/src/client.ts                                      # UPDATE — add callPlatformTrace, callPlatformRecent
platform-mcp/src/server.ts                                      # UPDATE — register 3 new tools
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md        # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/retrieve/**                                     # retrieval tools sealed
platform/src/lib/pipeline/**                                     # planner sealed
platform/src/app/api/chat/consume/**                             # orchestrator sealed
platform/src/app/api/mcp/keys/route.ts                          # MCP-1-S1 endpoint (no structural change)
platform/src/lib/mcp/auth.ts                                     # MCP-1-S1 auth unchanged
platform/src/lib/mcp/epistemics.ts                               # MCP-1-S1 builder unchanged
platform/src/lib/mcp/primitives_registry.ts                     # MCP-3-S1 registry unchanged
platform-mcp/src/tools/ask_madhav.ts                             # descriptions unchanged
platform-mcp/src/tools/plan_query.ts                             # descriptions unchanged
platform-mcp/src/tools/execute_plan.ts                           # descriptions unchanged
platform-mcp/src/tools/query_*.ts                                # MCP-3-S1 primitives unchanged
platform-mcp/resources/**                                        # MCP-2-S2 resources unchanged
01_FACTS_LAYER/**                                                # L1 sealed
025_HOLISTIC_SYNTHESIS/**                                        # L2.5 sealed
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                        # not touched in this session
CLAUDE.md                                                       # §E update is post-workstream-close
```

### Commit cadence

```
<type>(mcp): MCP-3-S2 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_3_S2.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 7 scope items are completed and the gate command passes, emit:

```
---FINAL_SUMMARY---
session_id: MCP-3-S2
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
  - <sha_item_6>
  - <sha_item_7>
scope_items_completed:
  - AC.MCP_3_S2.1   # rate_limiter.ts
  - AC.MCP_3_S2.2   # rate limiter wired into endpoints
  - AC.MCP_3_S2.3   # /api/mcp/recent
  - AC.MCP_3_S2.4   # read_asset tool + /api/mcp/asset
  - AC.MCP_3_S2.5   # get_trace + list_recent_queries tools
  - AC.MCP_3_S2.6   # Jest tests for rate limiter + recent
  - AC.MCP_3_S2.7   # full gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_3_s2_observability_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  Phase MCP-3 complete. All 16 v1 tools registered (3 Tier-1/2, 10
  primitives, read_asset, get_trace, list_recent_queries). Rate limiter
  wired into /api/mcp/execute and /api/mcp/primitives/[tool]. Next session:
  MCP-4-S1 (writes: log_prediction, record_outcome, flag_disagreement +
  PPL interim path).
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md.*
