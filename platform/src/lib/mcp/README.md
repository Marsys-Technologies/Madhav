# platform/src/lib/mcp — MCP Platform Library

This directory contains the platform-side library for the MARSYS-JIS MCP
(Model Context Protocol) server workstream. It is the foundation layer for
Phase MCP-1; the MCP server itself (`platform-mcp/`) is built in MCP-2-S1.

## What's here

| File | Purpose |
|---|---|
| `types.ts` | TypeScript contracts for the MCP response envelope, auth principal, citations, epistemics, synthesis audit, and API key rows. Implements MCP_BRIEF §4.2 exactly. |
| `auth.ts` | `validateMcpKey(authHeader)` — validates Bearer tokens from the MCP server. `generateMcpKey(env)` — creates new API keys. Uses PBKDF2-SHA256 + timing-safe compare; no external bcrypt dependency. |
| `epistemics.ts` | `buildEnvelope()`, `buildErrorEnvelope()`, `buildEpistemicsBlock()`, `buildSynthesisAudit()` — centralised MCP response builders. |
| `suggested_followups.ts` | `generateSuggestedFollowups(plan)` — heuristic generator returning 2-3 plausible follow-up questions per `ask_madhav` response. |

## Auth flow

```
External caller (Cowork / Claude Chat)
  │
  │  Bearer mcp_<env>_<40chars>
  ▼
platform-mcp (Cloud Run sidecar — MCP-2-S1)
  │  validateMcpKey(header) → McpPrincipal | null
  │  POST /api/mcp/execute
  │    X-MCP-Internal-Token: <MCP_INTERNAL_TOKEN>
  │    X-MCP-User:           <user_uid>
  │    X-MCP-Audience-Tier:  <client | super_admin>
  │    X-MCP-Key-Id:         <key_id>
  ▼
platform /api/mcp/execute (verifies service token + reads principal headers)
  │
  ▼
Existing orchestrator path (planner → tools → synthesis)
```

`validateMcpKey` never throws. On any failure (malformed header, key not
found, wrong hash, DB error) it returns `null`; the calling endpoint decides
how to respond (always 401).

## Envelope shape

Every `/api/mcp/*` response matches `McpEnvelope` from `types.ts`, which
implements the contract in `MCP_BRIEF §4.2`:

```jsonc
{
  "ok": true,
  "trace_id": "qry_...",
  "audience_tier": "super_admin",
  "epistemics": { "surgical": false, "confidence_band": "medium", "horizon_days": null, "falsifier": null },
  "result": { /* tool-specific */ },
  "citations": [],
  "plan": { /* PipelinePlan */ },
  "predictions_logged": [],
  "synthesis_audit": { "l25_tools_fired": [...], "holistic_read_passed": true, ... },
  "suggested_followups": ["...", "..."],
  "warnings": []
}
```

Error envelope:
```jsonc
{ "ok": false, "trace_id": "...", "error": { "class": "auth", "message": "...", "remediation": "..." } }
```

## How to add a new MCP-side helper

1. Add the TypeScript type to `types.ts` if a new shape is needed.
2. Add the helper function to the most appropriate file (or create a new
   file in this directory).
3. Add unit tests under `platform/src/lib/__tests__/mcp/`.
4. Update this README if the auth flow or envelope shape changes.
5. The MCP server (`platform-mcp/`) will call the corresponding
   `/api/mcp/*` endpoint — platform-side helpers are not imported directly
   by the MCP server (different service, different repo in prod).

## References

- `MCP_BRIEF §4.2` — response envelope contract (authoritative)
- `MCP_BRIEF §4.3` — auth model (API key format, storage schema)
- `platform/supabase/migrations/070_mcp_api_keys.sql` — DB schema
- `platform/src/app/api/mcp/execute/route.ts` — the main endpoint
- `platform/src/app/api/mcp/keys/route.ts` — admin key CRUD
- `platform/src/app/admin/mcp/keys/` — admin UI
