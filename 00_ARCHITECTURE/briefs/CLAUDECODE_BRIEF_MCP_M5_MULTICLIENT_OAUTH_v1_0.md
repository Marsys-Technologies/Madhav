---
canonical_id: CLAUDECODE_BRIEF_MCP_M5_MULTICLIENT_OAUTH
version: 1.0
status: READY-FOR-EXECUTION — M5 production OAuth + multi-client (Claude first; provision rest)
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M5)
depends_on: M1 (resolveMcpPrincipal); may PARALLELIZE with M2/M3 (touches auth front-door, not chart logic)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: live code, read 2026-06-30
hard_constraints:
  - real Firebase identity binding (profiles.id IS the Firebase uid); no 'anonymous' tokens
  - DB-backed OAuth (survives restart + multi-instance); migrations: next free number (verify; ≥382/383)
  - tool names snake_case, NO '-' (Gemini); Streamable HTTP only; VITEST
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — MCP M5: PRODUCTION OAUTH + MULTI-CLIENT

> The Bearer-key path is production-real. The OAuth path is in-memory scaffold. M5 productionizes OAuth so real
> external connectors (Claude first) authenticate with real portal identity, surviving restart + multi-instance.
> M0 already made the auth-code grant fail-closed; M5's real job is to make a real uid flow through it.

## §1 — Ground truth (verified)
- ALL OAuth state is in-memory Maps: auth codes (`authorize.ts:31`), tokens+refresh (`token_store.ts:28-29`),
  client registry = one hardcoded `test_client` (`token.ts:23-33`). Each has a "replace with DB" comment naming
  the target tables: **`mcp_oauth_tokens`, `mcp_oauth_clients`** (+ need an auth-codes table).
- M0 fixed the anonymous bug to **fail-closed**: auth-code grant now 400s if `authCode.uid` is unset
  (`token.ts:95-100`). BUT `authorize.ts` still never sets `uid` (no real Firebase round-trip; `FIREBASE_AUTH_URL`
  declared, unused) → the auth-code path is currently always-400. **M5's core: make authorize round-trip
  Firebase and stamp the verified uid.**
- Identity pattern to replicate: `getServerUser()` reads `__session` cookie → `verifySessionCookie()`
  (`platform/src/lib/firebase/server.ts:38-55`); `profiles.id` IS the Firebase uid
  (`access-control.ts:13-25`). `createSessionCookie(idToken, …)` mints the cookie.
- Migrations: two-dir merged lexical ordering; current global max 381 (supabase dir). Use **382/383** in
  `platform/supabase/migrations/` after a cross-dir collision check.

## §2 — M5.1 Auth architecture (one core, many front-doors)
One identity core: every front-door (Bearer key, OAuth) resolves to the SAME `McpPrincipal {user_uid, key_id?,
role}` via M1's `resolveMcpPrincipal`. Front-doors differ only in how they establish `user_uid`; downstream
(entitlement, tools) is front-door-agnostic.

## §3 — M5.2 Production OAuth (DB-backed + real identity)
1. **Migration** (`382_mcp_oauth.sql` or next free): `mcp_oauth_clients` (client_id PK, client_secret_hash,
   owner_uid, redirect_uris[], created_at), `mcp_oauth_tokens` (access_token_hash PK, refresh_token_hash, uid,
   scopes[], expires_at), `mcp_oauth_auth_codes` (code_hash PK, uid, client_id, scopes[], pkce_challenge,
   expires_at, consumed_at). Hash secrets/tokens at rest.
2. **Replace the in-memory Maps** in `authorize.ts` / `token.ts` / `token_store.ts` with these tables (so tokens
   survive restart + work across Cloud Run instances — today min-instances can be >1; in-memory breaks).
3. **Real Firebase round-trip in `authorize.ts`:** redirect through Firebase auth, verify the `__session`
   cookie via `verifySessionCookie` exactly as `getServerUser` does, stamp the verified `uid` onto the
   auth-code record (the `uid?` field already exists, `authorize.ts:23`). Then `issueTokens(uid, scopes)`
   carries a real uid → entitlement resolves against `profiles.id`.
4. **Dynamic client registration:** add `POST /oauth/register` (advertise `registration_endpoint` in discovery)
   writing to `mcp_oauth_clients`, replacing the hardcoded `test_client`.

## §4 — M5.3 Claude E2E + M5.4 provision the rest
- **M5.3 (Claude first):** Claude custom-connector path end-to-end with real identity + entitlement. Claude MCP
  connector facts: HTTPS only, tool calls only, ~25k-token response cap, resolve UUIDs→names, response_format
  enum. Prove a real Claude connector connects, authenticates to a real profile, and is entitlement-gated.
- **M5.4 (design + scaffold, build-as-taken-up):**
  - ChatGPT connector: `{type:"mcp",server_label,server_url,require_approval}`; Streamable HTTP or SSE; OAuth
    `authorization` header re-sent every request (server must accept bearer per-call — already stateless ✓);
    `require_approval` defaults on.
  - Gemini Remote-MCP: `{type:"mcp_server",name,url,headers,allowed_tools}`; **Streamable HTTP only, no SSE**
    (already ✓); **no `-` in names** (already ✓); not on Gemini-3 yet (external).
  - DeepSeek: NO MCP → must also work as a plain tool-calling backend (not a connector). Validate-and-repair
    JSON mandatory; `deepseek-v4-flash` pinned (ISSUE-6 ✓).

## §5 — Acceptance criteria
- One identity core: Bearer + OAuth both yield `{user_uid, role}` via `resolveMcpPrincipal`.
- OAuth is DB-backed (clients/tokens/codes tables); tokens survive a server restart and work across ≥2
  instances; no in-memory Maps remain in the OAuth path; no `'anonymous'` token can be minted.
- The auth-code grant round-trips real Firebase identity (verified uid stamped on the code); a real Claude
  connector authenticates to a real profile and is entitlement-gated E2E.
- Dynamic client registration works (`/oauth/register` → `mcp_oauth_clients`); `test_client` hardcode gone.
- ChatGPT/Gemini/DeepSeek paths designed + scaffolded; naming/transport constraints satisfied.
- Migration number verified collision-free; secrets hashed at rest; Vitest; retrieval FROZEN; chart-agnostic green.

## §6 — M0.5 lessons to carry (verified prod-only failure modes — bake these in)
- **A header declared ≠ a header sent.** F1 needed a SECOND PR because registry_bridge didn't actually attach
  `x-mcp-internal-token`. For every NEW service-to-service call M5 adds (OAuth → platform), assert the auth
  header/token is ACTUALLY transmitted (integration test that inspects the outgoing request), not just that the
  receiver checks for it.
- **A URL without its key is dead.** F2 needed `PYTHON_SIDECAR_API_KEY`, not just `PYTHON_SIDECAR_URL`. For any
  new env M5 wires into the amjis-mcp Cloud Run deploy (Firebase admin creds, token-signing secret), verify BOTH
  the URL/endpoint AND its credential are present in the deploy env — and prove it with a live call, not config inspection.
- **Deploy env parity:** a var present for amjis-web is NOT automatically present for amjis-mcp (the F2 root cause).
  Diff the two services' env; anything OAuth/identity-related M5 needs must be explicitly added to amjis-mcp.

## §7 — VERIFICATION PHASE (mandatory; phase NOT done until ALL pass — independent Auditor)
**V1 — Build gate:** both packages build; `typecheck-mcp` CI green.
**V2 — Migration:** `mcp_oauth_clients/tokens/auth_codes` applied; number collision-free (cross-dir check);
secrets/tokens HASHED at rest (verify no plaintext token/secret column); additive migration; rollback note.
**V3 — Tests:** token issue/validate/refresh against the DB store; auth-code grant REJECTS when uid unset
(fail-closed, M0 behavior preserved) and SUCCEEDS with a real Firebase uid; dynamic client registration;
one-identity-core (Bearer + OAuth both → `{user_uid,role}`). Vitest green.
**V4 — Restart + multi-instance proof (the core M5 win):** issue a token → RESTART the service (or new revision)
→ the token STILL validates (proves DB-backed, not in-memory). Run against ≥2 instances (min-instances ≥2 or two
revisions) → a token issued on one validates on the other. This is the acceptance that the in-memory scaffold is gone.
**V5 — Real identity E2E:** a real Claude connector completes the OAuth round-trip → the issued token carries a
REAL Firebase uid (NOT 'anonymous') → an entitlement-gated tool call resolves against that uid's profile and is
denied for an unentitled chart. Prove the full connect→identity→entitlement chain on prod.
**V6 — Header/key actually-sent checks (per §6):** integration tests prove any new service-to-service auth token
is transmitted; any new amjis-mcp deploy env var (URL + its credential) is present and exercised by a live call.
**V7 — Invariants:** no in-memory OAuth Maps remain (grep); no `'anonymous'` token mintable; tool names
snake_case no '-'; Streamable HTTP only; retrieval FROZEN; chart-agnostic green; reverse-citation on any delete.
**On ANY V-failure:** remediation loop (charter §4); no advance until V1–V7 pass.

*End of CLAUDECODE_BRIEF_MCP_M5_MULTICLIENT_OAUTH v1.0. Next: M6 per-model profile + M7 richness.*
