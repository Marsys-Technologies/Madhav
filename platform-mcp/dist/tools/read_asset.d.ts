/**
 * read_asset.ts — MCP Tier 4 tool: read a canonical MARSYS-JIS artifact.
 *
 * Returns the raw markdown of a canonical artifact (MSR, UCN, CDLM, CGM, RM,
 * FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE) by canonical_id, with an
 * optional section filter.
 *
 * This is a Tier 4 tool per MCP_BRIEF §4.1. It is surgical (no planner, no
 * B.11 floor enforcement, no synthesis). Use when you need the full text of
 * a synthesis layer document — e.g., the full CGM for a graph overview, or
 * the full FORENSIC for a birth-data audit. For targeted fact lookups within
 * a document, prefer query_signals or query_chart_facts.
 *
 * Access control: Per decision D12 (full transparency), all authenticated
 * callers receive full file content.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerReadAsset(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=read_asset.d.ts.map