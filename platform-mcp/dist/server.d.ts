/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - Three tools registered: ask_madhav, plan_query, execute_plan.
 *   (Tier 3 primitives, read_asset, get_trace, list_recent_queries land in MCP-3.)
 *
 * Cloud Run configuration (amjis-mcp service):
 *   Memory: 512 MB, Min instances: 1, Concurrency: 80, Region: asia-south1.
 *   Health check: GET /health → 200 { status: "ok", service: "marsys-mcp" }
 */
export {};
//# sourceMappingURL=server.d.ts.map