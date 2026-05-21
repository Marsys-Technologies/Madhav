/**
 * resources/index.ts — MCP resource registration for MARSYS-JIS.
 *
 * Registers two MCP resources that Claude reads once at session attach:
 *   - marsys://chart-overview  (~1300 words, L1-grounded chart summary)
 *   - marsys://house-rules     (~1000 words, acharya-grade operating manual)
 *
 * Together these replace 5-10 tool calls of orientation per session
 * (MCP_BRIEF §4.5). Resources are served as text/markdown. The files
 * are loaded synchronously at registration time; the MCP server restarts
 * on Cloud Run update, so stale content is not a runtime risk.
 *
 * Authored: MCP-2-S2 (2026-05-21)
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
/**
 * Register both MARSYS-JIS MCP resources on the given server.
 *
 * Call this once per McpServer instance, alongside the tool registrations,
 * before connecting the transport.
 *
 * @param server  The McpServer instance to register resources on.
 */
export declare function registerResources(server: McpServer): void;
//# sourceMappingURL=index.d.ts.map