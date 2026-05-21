/**
 * client.ts — HTTP client for calling the MARSYS platform from the MCP server.
 *
 * All outbound calls from platform-mcp → platform route through this module.
 * This centralises:
 *   - Service-to-service identity token acquisition (GCP metadata server or
 *     SERVICE_TOKEN env var for local dev).
 *   - X-MCP-* principal headers (resolved from Bearer key validation).
 *   - Error handling: network errors return clean error envelopes; no
 *     thrown exceptions propagate to the MCP tool layer.
 *
 * Exports:
 *   callPlatform()          → /api/mcp/execute   (ask_madhav, execute_plan)
 *   callPlatformPlan()      → /api/mcp/plan       (plan_query)
 *   callPlatformPrimitive() → /api/mcp/primitives/{toolName}
 *
 * Environment variables:
 *   PLATFORM_URL          — base URL of the amjis-web Cloud Run service
 *   MCP_INTERNAL_TOKEN    — shared secret for X-MCP-Internal-Token header
 *   SERVICE_TOKEN         — static identity token override (local dev only)
 */
import type { McpToolCall, PlatformCallResult, Principal } from './types.js';
/**
 * Call /api/mcp/execute for ask_madhav or execute_plan.
 *
 * @param toolCall  The tool name and params to send to the platform.
 * @param principal The resolved principal (user_uid, audience_tier, key_id).
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export declare function callPlatform(toolCall: McpToolCall, principal: Principal): Promise<PlatformCallResult>;
/**
 * Call /api/mcp/plan for plan_query (planner only, no execution).
 *
 * @param query     The question to plan.
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope (result = PipelinePlan).
 */
export declare function callPlatformPlan(query: string, principal: Principal): Promise<PlatformCallResult>;
/**
 * Call /api/mcp/primitives/{toolName} for surgical primitive tool invocations.
 * (Phase MCP-3-S1 creates these endpoints; this function is wired but may
 * return 404 until that session ships.)
 *
 * @param toolName  The primitive tool name (e.g. "chart_facts_query").
 * @param params    Tool-specific parameters.
 * @param principal The resolved principal.
 * @returns         The HTTP status code and parsed McpEnvelope.
 */
export declare function callPlatformPrimitive(toolName: string, params: Record<string, unknown>, principal: Principal): Promise<PlatformCallResult>;
//# sourceMappingURL=client.d.ts.map