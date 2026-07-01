/**
 * platform-mcp/src/oauth/connector_compat.ts
 *
 * M5.4 — Multi-client connector compatibility scaffold.
 * Design notes and invariants for ChatGPT, Gemini, and DeepSeek connectors.
 * These constraints are in addition to the core MCP OAuth implementation.
 *
 * M5 — MCP elevation arc (2026-07-01).
 */

// ── ChatGPT connector (M5.4) ─────────────────────────────────────────────────
//
// ChatGPT uses the "actions" connector format:
//   { type: "mcp", server_label: "marsys-jis", server_url: "https://madhav.marsys.in/mcp" }
//
// Key constraints:
//   1. Streamable HTTP only (no SSE GET) — already satisfied by our server (405 on GET /mcp).
//   2. OAuth `authorization` header re-sent on EVERY request (bearer per-call model).
//      Our stateless server already satisfies this — we validate the Bearer on every request.
//   3. `require_approval` defaults on for ChatGPT tool calls — the user approves each call.
//      No server-side changes needed; this is a client-side setting.
//   4. ~25k-token response cap: keep tool responses concise; streaming helps.
//   5. Tool descriptions: snake_case, no hyphens (satisfied globally).
//
// To connect ChatGPT:
//   1. Register a client: POST /mcp/oauth/register with your redirect_uri.
//   2. Configure the ChatGPT action with server_url and OAuth credentials.
//   3. The auth-code flow will use PKCE (S256); the token endpoint is /mcp/oauth/token.

// ── Gemini Remote-MCP connector (M5.4) ───────────────────────────────────────
//
// Gemini uses the Remote-MCP format (available on Gemini 2.0 Flash+, not Gemini 3 yet):
//   {
//     type: "mcp_server",
//     name: "marsys_jis",      // MUST use underscore, NOT hyphen — Gemini rejects hyphens
//     url: "https://madhav.marsys.in/mcp",
//     headers: { "Authorization": "Bearer <token>" },
//     allowed_tools: ["compute_natal_positions", ...]
//   }
//
// Key constraints:
//   1. Streamable HTTP ONLY — Gemini does NOT support SSE transport.
//      Already satisfied (405 on GET /mcp).
//   2. NO hyphens in server name or tool names — use underscores.
//      All our tool names are snake_case (enforced globally).
//   3. Bearer token sent in `headers.Authorization` on every request.
//      Our stateless Bearer validation satisfies this.
//   4. `allowed_tools` filters which tools the Gemini app can call.
//      No server-side filtering needed; this is a client-side constraint.
//
// To connect Gemini:
//   1. Issue a Bearer MCP key (existing key management, no OAuth needed for Gemini).
//   2. Configure the Gemini app with the mcp_server spec above.
//   3. Gemini 3.0: full MCP connector expected; same constraints apply.

// ── DeepSeek connector (M5.4) ────────────────────────────────────────────────
//
// DeepSeek has NO native MCP connector — it uses plain tool-calling (function calling).
// The integration pattern is a backend proxy:
//
//   1. DeepSeek sends a tool_call in its response.
//   2. The application layer (portal or a middleware) dispatches to POST /mcp
//      with the Bearer key and the appropriate MCP tool call.
//   3. The MCP server processes it and returns the result.
//   4. The application injects the result back into the DeepSeek conversation.
//
// Key constraints:
//   - Validate-and-repair JSON mandatory: DeepSeek-v4 may produce malformed JSON in
//     tool_call arguments. The application layer must validate before dispatching.
//   - `deepseek-v4-flash` model pinned (ISSUE-6 resolution).
//   - No MCP protocol wire-format changes needed; all tool names snake_case (satisfied).
//
// Server-side: no changes needed. The plain tool-calling path uses the same POST /mcp
// endpoint with a Bearer key. DeepSeek specifics are handled in the portal's chat layer.

/**
 * Connector capability matrix for runtime checks.
 * Used by connector-specific middleware if needed.
 */
export const CONNECTOR_CONSTRAINTS = {
  chatgpt: {
    transport: 'streamable_http' as const,
    auth: 'oauth_bearer' as const,
    tool_name_pattern: /^[a-z][a-z0-9_]*$/,  // snake_case, no hyphens
    max_response_tokens: 25_000,
    per_call_auth: true,     // Bearer re-sent every request
    require_approval: true,  // default on in ChatGPT
  },
  gemini: {
    transport: 'streamable_http' as const,  // ONLY — no SSE
    auth: 'bearer_header' as const,
    tool_name_pattern: /^[a-z][a-z0-9_]*$/,  // NO hyphens (Gemini rejects them)
    server_name_pattern: /^[a-z][a-z0-9_]*$/,  // name field: underscores only
    per_call_auth: true,
  },
  deepseek: {
    transport: 'plain_tool_call' as const,  // no MCP connector; portal-mediated
    auth: 'bearer_key' as const,
    validate_repair_json: true,  // mandatory for deepseek-v4 function call arguments
    pinned_model: 'deepseek-v4-flash' as const,
  },
} as const

/**
 * Verify a tool name is compatible with all connectors (no hyphens, snake_case).
 * Enforced at registration time; this is a design-time guard.
 */
export function isToolNameConnectorCompatible(name: string): boolean {
  return /^[a-z][a-z0-9_]*$/.test(name)
}
