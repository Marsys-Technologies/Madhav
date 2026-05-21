/**
 * query_signals.ts — MCP Tier 3 surgical primitive: MSR signal corpus lookup.
 *
 * What it does: Queries the MSR (Master Signal Register) corpus of 499+ astrological
 * signals with structured filters. Returns raw signal rows — domain, valence, dasha
 * activations, confidence, significance, forward-looking flag, and signal text. This
 * is a direct L2.5 data read that bypasses the planner and synthesis stages. Tagged
 * surgical: true in the epistemics block.
 *
 * When to prefer: Use query_signals when you need raw signal data from the MSR corpus
 * rather than synthesized prose. Prefer over ask_madhav when the goal is "give me
 * all forward-looking signals in the career domain" as a structured list. Prefer
 * ask_madhav when interpretation or cross-domain synthesis is also required.
 *
 * Input shape hints:
 *   domain — optional; e.g. "career", "health", "relationships", "spiritual".
 *   planet — optional; filter to signals involving a specific planet.
 *   dasha_lord — optional; filter to signals activated by a specific dasha lord.
 *   min_confidence — optional float 0.0–1.0; filter to signals above this threshold.
 *   forward_looking — optional boolean; true = only prospective signals.
 *   limit — optional; max signals to return (default 50).
 *
 * Output shape preview: {ok, result: {signals: MsrSignalRow[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_signals({domain: "career", forward_looking: true, min_confidence: 0.8}) →
 *   {ok: true, result: {signals: [{signal_id: "SIG.MSR.234", domain: "career", ...}]}, ...}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQuerySignals(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_signals.d.ts.map