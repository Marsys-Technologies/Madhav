/**
 * auth.ts — Bearer key validation for the platform-mcp MCP server.
 *
 * Validates incoming Bearer tokens from MCP clients (Claude Chat, Cowork)
 * by calling back to the platform's /api/mcp/keys/validate endpoint.
 *
 * Architecture decision (MCP_BRIEF §5.1, Item 8): call-through to platform
 * is the correct approach — the MCP server has no direct DB connection.
 * Validation is delegated to the platform, which uses the same PBKDF2-SHA256
 * verification and timing-safe comparison that MCP-1-S1 implemented.
 *
 * Returns: Principal on success, null on any auth failure.
 * Never throws — callers receive null on error.
 */
import type { Principal } from './types.js';
/**
 * Validate the Authorization header from an incoming MCP request.
 *
 * Calls GET /api/mcp/keys/validate with the raw Authorization header forwarded.
 * Uses the X-MCP-Internal-Token service secret so the platform trusts the caller.
 *
 * @param authorizationHeader  The raw "Authorization" header value (e.g. "Bearer mcp_prod_...").
 * @returns  Principal on success, null on any failure (invalid key, network error, etc.).
 */
export declare function validateMcpKeyFromHeader(authorizationHeader: string | undefined): Promise<Principal | null>;
//# sourceMappingURL=auth.d.ts.map