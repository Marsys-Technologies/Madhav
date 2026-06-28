---
artifact: MCP_ELEVATION_AUDIT_FINDINGS_v1_0.md
canonical_id: MCP_ELEVATION_AUDIT_FINDINGS
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (3-agent parallel audit: retrieval code + MCP code + live DB) — for native Abhisek Mohanty
classification: audit findings — MCP elevation + Part 3 seam (MCP side) + security/entitlement findings
input_audit: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md (Cowork baseline)
method: read actual platform-mcp/src/ code (server.ts, tools/, oauth/, auth.ts, resources/) + platform
  auth/gateway code; runtime tool count confirmed against server.ts registrations; code wins over docs
mcp_service: amjis-mcp (Cloud Run, asia-south1)
changelog:
  - v1.0 (2026-06-28): First code audit. Confirms Cowork baseline on 8 of 9 items; surfaces 5 new
      findings not present in the Cowork audit; precise tool count (31, not ~30); new P0 live breakage.
---

# MCP ELEVATION AUDIT FINDINGS (v1.0)

> **Scope:** Part 2 (MCP channel 2.1–2.10) + Part 3 MCP-side (seam + entitlement boundary + security findings).
> Strictly read-only. Code wins over docs.
> Divergences from `RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md` are flagged with ★.

---

## §1 — VERDICT TABLE

| Item | Goal | Verdict | Priority |
|---|---|---|---|
| 2.1 | Identity (portal identity) | **PARTIAL** (bare uid + key_id; no role) | P1 |
| 2.2 | Chart entitlement | **ABSENT** | **P0 — Security** |
| 2.3 | Chart selection | **ABSENT** | P1 |
| 2.4 | Session state + memory | **ABSENT** (by design) | P2 |
| 2.5 | Chart-switch isolation | **ABSENT** | P2 |
| 2.6 | Multi-client auth | **PARTIAL** (in-memory scaffold, not production) | P1 |
| 2.7 | Per-model declared profile | **ABSENT** | P2 |
| 2.8 | Resources & prompts | **PARTIAL/dead** (defined, not registered) | P1 |
| 2.9 | Transport/rate-limit/observability | **PARTIAL** | P1–P2 |
| 2.10 | Latent bugs | **5 confirmed bugs** | P0–P1 |
| 3.1 | Seam path map | **GAP** (28/31 tools bypass registry) | P0 |
| 3.2 | Entitlement boundary (Option 1) | **ABSENT** on MCP path | P0 |
| 3.3 | Option 1 implementable? | **YES** — one blocking prereq | P0 |

---

## §2 — FULL TOOL INVENTORY (server.ts registrations)

**Actual registered tool count: 31.** Health endpoint reports `tools: 13` — stale by 18.

| # | Tool Name | File | Backend | Entitlement? | Bypass registry? |
|---|---|---|---|---|---|
| 1 | `resolve_entity` | `l0_brahmagyan.ts` | Platform REST | None | Partial bypass |
| 2 | `list_entities` | `l0_brahmagyan.ts` | Platform REST | None | Partial bypass |
| 3 | `asset_registry_all` | `l0_brahmagyan.ts` | Platform REST | None | Partial bypass |
| 4 | `asset_registry_l0` | `l0_brahmagyan.ts` | Platform REST | None | Partial bypass |
| 5 | `intent_classify` | `l0_brahmagyan.ts` | Local render | No SQL | Partial bypass |
| 6 | `query_planet_position` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 7 | `query_planet_transit` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 8 | `query_aspects_at_time` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 9 | `query_retrograde_periods` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 10 | `ephemeris_cache_year` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 11 | `ephemeris_cache_native_lifetime` | `l0_ephemeris.ts` | Sidecar GET | None | ✗ bypass |
| 12 | `compute_natal_positions` | `retrieval/pyhora_natal.ts` | Sidecar POST | None | ✗ bypass |
| 13 | `query_dasha_periods` | `retrieval/pyhora_natal.ts` | Sidecar POST | None | ✗ bypass |
| 14 | `query_special_lagnas` | `retrieval/pyhora_natal.ts` | Sidecar POST | None | ✗ bypass |
| 15 | `holistic_bundle` | `tools/bo_2-8.ts` | Sidecar POST | None | ✗ bypass |
| 16 | `holistic_bundle_chart_facts` | `retrieval/holistic_bundle.ts` | Direct pg.Pool | `WHERE chart_id=$1` (no owner check) | ✗ bypass |
| 17 | `kala_temporal_bundle` | `retrieval/kala_temporal.ts` | Sidecar GET + fallback | None | ✗ bypass |
| 18 | `query_remedies` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id at all** | ✗ bypass |
| 19 | `query_remedies_for_chart` | `retrieval/remedy_tools.ts` | Direct pg.Pool | Planet/domain only | ✗ bypass |
| 20 | `list_remedies_by_category` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id** | ✗ bypass |
| 21 | `read_remedy` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id** | ✗ bypass |
| 22 | `query_tantric_remedies` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id** | ✗ bypass |
| 23 | `query_remedies_by_planet` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id** | ✗ bypass |
| 24 | `query_mantras` | `retrieval/remedy_tools.ts` | Direct pg.Pool | **No chart_id** | ✗ bypass |
| 25 | `event_anchors` | `phala_event_anchors.ts` | Sidecar POST | None | ✗ bypass |
| 26 | `mitigation_map` | `phala_mitigation_map.ts` | `callPlatformPrimitive` → `/api/mcp/primitives` | None | ✓ (but **401 on every call**) |
| 27 | `muhurta_finder` | `muhurta_finder.ts` | `callPlatformPrimitive` → `/api/mcp/primitives` | None | ✓ (but **401 on every call**) |
| 28 | `phala_outlook` | `phala_outlook.ts` | Sidecar POST | None | ✗ bypass |
| 29 | `lel_query` | `mimamsa_lel_intake.ts` | Sidecar POST | `chart_id` param (no ownership check) | ✗ bypass |
| 30 | `record_outcome` | `mimamsa_outcome.ts` | Sidecar POST | None | ✗ bypass |
| 31 | `query_calibration` | `mimamsa_outcome.ts` | Sidecar POST | None | ✗ bypass |

**Dead file (source tree, NOT registered in `server.ts`):**
- `tools/bo_2-7.ts` (`bodha_signal_search`) — written but not imported or registered. Dead code.

**Registry-through path: 2 tools (`mitigation_map`, `muhurta_finder`) — both currently 401ing.**
**Bypass: 29 of 31 tools.**

---

## §3 — PER-ITEM FINDINGS

### 2.1 — Identity

**Verdict: PARTIAL**

`Principal` type (`platform-mcp/src/types.ts:100-104`):
```typescript
export interface Principal {
  user_uid: string
  key_id: string
}
```

`audience_tier` was excised 2026-05-28 (Stream A `3.tier_excision`). The principal now carries only `user_uid` + `key_id`.

**Auth resolution paths:**
- **Bearer key:** `auth.ts:67` → `validateMcpKeyFromHeader()` → `GET /api/mcp/keys/validate` → `{valid, user_uid, key_id}`. No role returned.
- **OAuth:** `server.ts:88-94` maps `oauthRecord.uid` to a Principal from in-memory `token_store.ts:23`. No role present.

**Missing for portal-equivalent identity:** `role` field (owner/guest/super_admin), email, `chart_grants` membership, and a DB-backed client registry. All paths produce a bare `{user_uid, key_id}` — insufficient for `authorizeChartAccess` without an additional DB lookup (`user_uid → owner_id`).

**★ Divergence from Cowork:** Confirmed. `audience_tier` correctly excised; role gap confirmed.

---

### 2.2 — Chart Entitlement (SECURITY)

**Verdict: ABSENT — CRITICAL SECURITY GAP**

`authorizeChartAccess` is **never called anywhere in `platform-mcp/src/`**.

**Full tool-call path (no entitlement check anywhere):**
1. Client sends `POST /mcp` with Bearer token
2. `server.ts:83` → `validateMcpKeyFromHeader()` → `Principal {user_uid, key_id}`
3. `server.ts:105-138`: fresh `McpServer` + all 31 tools registered unconditionally
4. Tool handler receives `chart_id` as a plain UUID parameter from the LLM
5. **No ownership or grant check occurs**

**Concrete evidence (sampling):**
- `retrieval/holistic_bundle.ts:278`: `async ({ chart_id })` → `WHERE chart_id = $1`. No owner check.
- `tools/bo_2-8.ts:166`: `async ({ chart_id })` → sidecar POST. No check.
- `retrieval/kala_temporal.ts:534`: `chart_id` → sidecar. No check.
- `phala_mitigation_map.ts:259-263`: `chart_id` → `callPlatformPrimitive`. No check.
- `retrieval/remedy_tools.ts`: 7 tools query `brahma_remedy_corpus` with **no `chart_id` restriction at all** — fully open corpus.

**Also confirmed on the primitives route** (`platform/src/app/api/mcp/primitives/[tool]/route.ts:80-95`): zero calls to `authorizeChartAccess`.

**Conclusion: Any valid API key can read any `chart_id` in the database.** The attack vector is trivial: enumerate or guess chart UUIDs, send as the `chart_id` parameter to any of the 31 tools.

**★ Divergence from Cowork:** Confirmed exactly. No change since Cowork audit.

---

### 2.3 — Chart Selection

**Verdict: ABSENT**

No `list_my_charts`, `select_chart`, or active-chart concept anywhere in `platform-mcp/src/`. The LLM/client must supply `chart_id` as a bare UUID to every tool call. No "my charts" scoping, no session-scoped chart pointer.

---

### 2.4 — Session State + Memory

**Verdict: ABSENT (by design, per D10)**

`server.ts:140`:
```typescript
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
})
```

Comment at `server.ts:11`: "Stateless per D10 (no conversation history; host chat owns the thread)."

Each `POST /mcp` creates a new `McpServer` + transport, discarded after response. No session store, no conversation memory, no recall tools. This is a deliberate architectural decision — the host application (Claude Desktop, ChatGPT, etc.) owns the conversation thread.

---

### 2.5 — Chart-Switch Isolation

**Verdict: ABSENT**

No detection or advisory signal for mid-conversation `chart_id` switches. Statelessness (2.4) makes this structurally impossible without adding per-connection state. No mechanism to compare prior-request `chart_id` to current-request `chart_id`.

---

### 2.6 — Multi-Client Auth

**Verdict: PARTIAL — in-memory scaffold, not production-safe**

The OAuth implementation is entirely in-memory Maps with no DB persistence:

- `oauth/token_store.ts:28-29`:
  ```typescript
  const tokenStore = new Map<string, TokenRecord>()   // "replace with DB in production"
  const refreshStore = new Map<string, string>()
  ```
- `oauth/authorize.ts:31`:
  ```typescript
  const authCodes = new Map<string, AuthCodeRecord>()  // "replace with DB in production"
  ```
- `oauth/token.ts:23-33`: `CLIENT_REGISTRY` is a hardcoded in-memory Map with exactly ONE entry: `test_client` / owner `test_uid`. Comment: "replace with DB in production — table: mcp_oauth_clients"

**Consequences:**
1. **Server restart wipes all tokens, refresh tokens, and auth codes.** Any connected Claude Desktop/ChatGPT user must re-authenticate.
2. **No real client registration.** No `POST /oauth/register`. Only `test_client` exists.
3. **`authorization_code` grant issues anonymous tokens**: `oauth/token.ts:95`: `issueTokens(authCode.uid ?? 'anonymous', authCode.scopes)`. The Firebase auth redirect in `authorize.ts` never populates `uid` on the auth code, so every auth_code grant produces `user_uid: 'anonymous'` — i.e., zero user identity through the OAuth path.

**Bearer key path is functional** — `GET /api/mcp/keys/validate` against the DB works. The production path for real users is Bearer key, not OAuth. OAuth is scaffolding only.

**★ Divergence from Cowork:** Confirmed. Precise anonymous-UID bug (`authCode.uid ?? 'anonymous'`) is additional detail not in Cowork.

---

### 2.7 — Per-Model Declared Profile

**Verdict: ABSENT**

No client→model-family declaration mechanism anywhere in `platform-mcp/src/`. No per-model surface shaping. The same 31 tools are presented universally to every connecting client — Claude Desktop, ChatGPT connector, Gemini Remote MCP — regardless of the model family behind the connection.

`getMcpSurfaceSpec(family)` exists in the retrieval layer (`platform/src/lib/retrieval/maro/normalizer.ts:350`) but is never called from the MCP server.

---

### 2.8 — Resources + Prompts

**Verdict: PARTIAL — 9 resources built but dead; 0 prompts**

`platform-mcp/src/resources/index.ts:36` — `registerResources(server)` is the entry point. 9 resource files are ready:

| Resource URI | File | Status |
|---|---|---|
| `marsys://chart-snapshot` | `chart_snapshot.ts` | Built, dead |
| `marsys://chart-overview` | `chart_overview.ts` | Built, dead |
| `marsys://house-rules` | `house_rules.ts` | Built, dead |
| `marsys://capabilities` | `capabilities.ts` | Built, dead |
| `marsys://school-conventions` | `school_conventions.ts` | Built, dead |
| `marsys://chart-bundle/{chart_id}` | `chart_bundle_resource.ts` | Built, dead |
| `marsys://multi-ayanamsha/{chart_id}` | `multi_ayanamsha_resource.ts` | Built, dead |
| `marsys://classical-texts/{text_key}` | `classical_texts_resource.ts` | Built, dead |
| `marsys://resource/sutravali/…` | `sutravali_resource.ts` | Built, dead |

`grep "registerResources" platform-mcp/src/server.ts` → **zero results**. Not imported, not called.

**MCP prompts:** Zero `server.prompt()` calls anywhere in `platform-mcp/src/`.

**Fix:** one-liner — add `registerResources(server)` to `server.ts` after `McpServer` instantiation.

**★ Divergence from Cowork:** Confirmed exactly.

---

### 2.9 — Deployment / Transport / Rate-Limit / Observability

**Verdict: PARTIAL**

**Transport:**
- `server.ts:139`: `new StreamableHTTPServerTransport(...)` — POST-only Streamable HTTP. `GET /mcp` returns 405. No SSE.
- Compatible with Gemini Remote MCP (which requires Streamable HTTP). Claude Desktop works. ChatGPT connector works.

**Rate limiting:**
- Platform primitives route (`primitives/[tool]/route.ts:101-106`): calls `checkRateLimit(keyId)` ✓
- **17 of 31 tools** call the sidecar directly (`bo_2-8.ts`, `kala_temporal.ts`, `event_anchors`, `phala_outlook`, `pyhora_natal.ts`, `mimamsa_lel_intake.ts`, `mimamsa_outcome.ts`, `l0_ephemeris.ts` ×6) — **bypass rate limiting entirely**
- The 7 remedy tools query pg.Pool directly — no rate limit

**Observability:**
- `console.error/warn` only at the MCP layer — no structured logging, no request IDs, no metrics
- The platform's `traceEmitter` fires for primitives-route calls but NOT for sidecar-direct tool calls
- No distributed trace propagation from MCP → sidecar

**Health endpoint (`server.ts:164-167`):**
```json
{ "status": "ok", "service": "marsys-mcp", "version": "1.0.0", "tools": 13,
  "stream_g_capabilities": ["compute_natal_positions", "query_dasha_periods", "query_special_lagnas"] }
```
- **`tools: 13` is stale — actual count is 31** (off by 18)
- `stream_g_capabilities` lists only 3 of the 31 registered tools
- No mention of resources (which are all dead anyway)

**`generated/tool_list.json`:** Lists 11 URIs matching the original Stream A+B capability list. Stale artifact; not aligned to the 31 live registrations.

**Cloud Run config** (from server.ts comments): `amjis-mcp` service, 512 MB, min 1 instance, concurrency 80, region `asia-south1`. No deployment YAML found in `platform-mcp/`.

**★ Divergence from Cowork:** Tool count now precisely quantified as 31, not "~30". Rate limiting gap quantified: 17/31 sidecar-direct tools have zero rate limiting.

---

### 2.10 — Latent Bugs (all confirmed)

**BUG-1 — P0 LIVE BREAKAGE: `callPlatformPrimitive` silently 401s on every call**

`platform/src/app/api/mcp/primitives/[tool]/route.ts:87`:
```typescript
const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as 'client' | 'super_admin' | null
if (!userUid || !audienceTierHeader || !keyId) {
  return ... 401
}
```

`platform-mcp/src/client.ts:128` comment: `// X-MCP-Audience-Tier header removed (Stream A 3.tier_excision 2026-05-28)`

The header is NOT sent by the MCP client. The platform route still requires it. **Result: `mitigation_map` and `muhurta_finder` — the TWO tools that correctly use the registry path — return 401 on every real call.** The only tools using the "correct" architecture are the broken ones.

**Fix:** Remove the `audienceTierHeader` guard from the `if (!userUid || !audienceTierHeader || !keyId)` check in the primitives route. The tier excision was correct; the route was not updated.

**BUG-2 — P1: Health endpoint `tools: 13` stale (actual: 31)**

`server.ts:165`: hardcoded `"tools": 13`. Actual registrations: 31. Stale by 18. Any client or monitoring system relying on this count has wrong data.

**BUG-3 — P1: `registerResources()` never called**

All 9 resources built and wired in `resources/index.ts` — not wired into `server.ts`. Zero MCP resources served at runtime. Fix: one import + one call.

**BUG-4 — P1: OAuth anonymous UID bug**

`oauth/token.ts:95`: `issueTokens(authCode.uid ?? 'anonymous', authCode.scopes)`. The auth code record has `uid: undefined` because the Firebase redirect in `authorize.ts` issues the code without setting UID. Every `authorization_code` grant produces `user_uid: 'anonymous'` — no real identity through the OAuth path.

**BUG-5 — P2 NEW: `kala_temporal.ts` lines 156–341 contain native-specific fallback data**

When the Python sidecar is unavailable, `kala_temporal_bundle` returns hardcoded FORENSIC data specific to the native Abhisek Mohanty (dasha sequences, obstruction/convergence analysis, life events). A non-native chart request silently receives the native's data as the "fallback" response. This is a native-contamination defect per §D.1 of the RETRIEVAL_SYSTEM_DESIGN_APPROACH.

**Not in Cowork audit — NEW finding.**

---

## §4 — PART 3: THE SEAM (MCP side)

### 3.1 — Path Map: Every MCP-to-Retrieval Path

| MCP tool category | Retrieval path | Single source? | Entitlement? |
|---|---|---|---|
| `callPlatformPrimitive` tools (2 tools) | `/api/mcp/primitives/[tool]` → registry | ✓ single source | ✗ no entitlement; also **401s** (BUG-1) |
| Direct pg.Pool tools (8 tools: `holistic_bundle_chart_facts`, 7 remedy tools) | Own pool, raw SQL | ✗ bypasses registry | ✗ |
| Sidecar tools (21 tools) | Python sidecar HTTP | ✗ bypasses registry | ✗ |

**No path through the MCP channel honors the single-source or entitlement requirements of the frozen sync contract.**

### 3.2 — The Entitlement-Boundary Ruling on the MCP Side

Option 1 requires:
1. `authorizeChartAccess(principal, chart_id)` called **before any chart-keyed retrieval** — ABSENT on all 31 MCP tools.
2. A `user_uid → owner_id` resolution step — ABSENT from `platform-mcp/src/` entirely.
3. A chokepoint where the check fires — the pattern exists (`invoke_tool.ts` on the platform side) but is not wired into MCP server dispatch.

The MCP `Principal` type carries only `{user_uid, key_id}`. `authorizeChartAccess` expects `owner_id`. There is no code anywhere in the MCP server that resolves `user_uid` to an `owner_id`. This must be added as a one-time lookup on auth (cache in the session context for the request lifetime).

### 3.3 — Is Option 1 Implementable on the MCP Side?

**Yes — three steps, no architectural change required:**

1. **Add `user_uid → owner_id` lookup** to the auth layer (`auth.ts` or at start of request handling in `server.ts`). Fetches `users.owner_id WHERE uid = user_uid`. Extend the `Principal` type to carry `owner_id`.

2. **Add `authorizeChartAccess(principal, chart_id)` at tool dispatch** — either:
   - As a middleware in `server.ts` that fires before every tool call and checks `chart_id` from args, OR
   - As the first line in every tool handler that takes a `chart_id` parameter.
   The `invoke_tool.ts` pattern on the platform side is the reference implementation.

3. **Wire `registerResources()` while at it** (BUG-3) — resources also need entitlement on the per-chart ones.

The retrieval layer (`platform/src/lib/retrieval/`) stays frozen and chart-agnostic — it does not change.

---

## §5 — NEW FINDINGS vs COWORK AUDIT

**NEW-1: P0 LIVE BREAKAGE — `callPlatformPrimitive` always 401s.**
The platform primitives route still requires `x-mcp-audience-tier` header that the MCP client stopped sending after the tier excision (2026-05-28). `mitigation_map` and `muhurta_finder` — the two correctly-architected tools — fail on every real call. The two "worst" tools (registry bypass) work; the two "best" (registry path) are broken. This reversal is critical and was not in the Cowork audit.

**NEW-2: Tool count is 31, not ~30.**
Health reports 13; `tool_list.json` lists 11; Cowork said "~30 hand-rolled in-process tools." Actual: 31 registered in `server.ts`. The `bodha_signal_search` tool (`bo_2-7.ts`) is written but NOT registered — it is dead code.

**NEW-3: Rate limiting gap quantified — 17/31 sidecar-direct tools have zero rate limiting.**
Cowork noted "no rate limiting" without quantifying. The primitives path DOES have rate limiting (`checkRateLimit(keyId)`); it's the sidecar-direct tools (17 of 31) that bypass it. This means ~55% of tools are completely unrate-limited.

**NEW-4: `kala_temporal.ts` native-specific fallback (lines 156–341).**
Native contamination defect: non-native chart requests silently receive Abhisek Mohanty's FORENSIC dasha/obstruction data when the sidecar is unavailable. Violates §D.1 of the chart-agnostic mandate.

**NEW-5: OAuth anonymous UID — `authCode.uid ?? 'anonymous'` in `oauth/token.ts:95`.**
Cowork noted OAuth issues broadly. The specific mechanism is `uid: undefined` on the auth code because the Firebase redirect in `authorize.ts` never sets it. Every auth_code flow produces `user_uid: 'anonymous'` — a user identity black hole.

---

## §6 — TOP GAPS IN PRIORITY ORDER

| Priority | Gap | Evidence | Action |
|---|---|---|---|
| **P0-A** | **Chart entitlement absent** — any valid key reads any chart | `auth.ts`, all 31 tool handlers — zero `authorizeChartAccess` calls | Add `user_uid→owner_id` lookup + `authorizeChartAccess` at tool dispatch (see §4.3.2). |
| **P0-B** | **`callPlatformPrimitive` silently 401s** — `mitigation_map` + `muhurta_finder` broken | `route.ts:87` `audienceTierHeader` guard + `client.ts:128` removed header | Remove `audienceTierHeader` from the `if` guard in primitives route. |
| **P0-C** | **Keystone: 28/31 tools bypass registry** (owned by retrieval fork but MCP must adapt) | `server.ts` — direct pg.Pool + sidecar imports | After retrieval fork wires the registry path, MCP must migrate all 31 tools to `callPlatformPrimitive` pattern. |
| **P1-A** | **`registerResources()` never called** — 9 resources dead | `server.ts` has no import/call for `registerResources` | `import { registerResources } from './resources'` + `registerResources(server)` in `server.ts`. |
| **P1-B** | **Production OAuth not safe** — in-memory Maps, anonymous UID, single hardcoded client | `oauth/token_store.ts`, `oauth/token.ts:95`, `oauth/authorize.ts:31` | DB-backed token + client tables (`mcp_oauth_tokens`, `mcp_oauth_clients`); fix `authorize.ts` to set `uid` on auth code after Firebase redirect. |
| **P1-C** | **Principal missing `owner_id`** — blocks entitlement wiring | `types.ts:100-104` — no `owner_id` | Extend `Principal` + add DB lookup at auth time. |
| **P1-D** | **Identity has no role** — no owner/guest/super_admin at MCP layer | Both auth paths return bare uid+key_id | Extend Principal with role from `user_uid → role` DB lookup. |
| **P1-E** | **Health stale (`tools: 13`, actual 31)** + `tool_list.json` stale (11 URIs) | `server.ts:165`, `generated/tool_list.json` | Regenerate from live registrations; make health endpoint dynamic. |
| **P2-A** | **Per-model declared profile absent** — universal-only surface | `server.ts` — no MARO invocation | Wire `getMcpSurfaceSpec()` from `platform/src/lib/retrieval/maro/normalizer.ts:350` into tool registration. |
| **P2-B** | **17/31 tools have no rate limiting** (sidecar-direct bypass) | `remedy_tools.ts`, `bo_2-8.ts`, `kala_temporal.ts`, etc. | Add rate-limit middleware before tool dispatch in `server.ts`. |
| **P2-C** | **No structured observability** — `console.error` only; no request IDs; no trace propagation | `server.ts` — no structured logger | Add structured logging + request-ID propagation; wire `traceEmitter` for sidecar-direct calls. |
| **P2-D** | **Chart-switch isolation absent** | Stateless design (intentional) | Requires per-connection state — advisory signal to LLM that chart context has changed. |
| **P2-E** | **0 prompts** | Zero `server.prompt()` calls | Define acharya-grade prompts for whole-chart entry points. |
| **P3-A** | **`kala_temporal.ts` native-specific fallback** (lines 156–341) — contamination | `kala_temporal.ts:156–341` | Remove native fallback data; return a clean error when sidecar unavailable. |
| **P3-B** | **`bo_2-7.ts` dead code** (`bodha_signal_search` written but not registered) | Not imported in `server.ts` | Either register or delete. |
| **P3-C** | **Stale `tool_list.json`** | `generated/tool_list.json` — 11 URIs vs 31 live | Regenerate or delete stale artifact. |

---

*End of MCP_ELEVATION_AUDIT_FINDINGS v1.0 — code-grounded, 2026-06-28.*
*Input: 3-agent parallel audit (retrieval code + MCP code + live DB checks).*
*§5 lists 5 new findings not present in the Cowork baseline audit.*
*The §6 P0-B item (callPlatformPrimitive 401) is the most urgent operational fix.*
