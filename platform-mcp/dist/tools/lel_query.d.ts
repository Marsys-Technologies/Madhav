/**
 * lel_query.ts — MCP Tier 3 surgical primitive: Life Event Log ground-truth retrieval.
 *
 * What it does: Queries the Life Event Log (LEL) — the authoritative ground-truth
 * corpus of 36 documented life events, 5 period summaries, and 6 chronic patterns
 * with confidence scores up to 0.89. Returns raw event records with dates, categories,
 * significance scores, and associated dasha states. The LEL is the M4 ground-truth
 * spine and is foundational to calibration and backtesting. Tagged surgical: true.
 *
 * When to prefer: Use lel_query to retrieve verified, witnessed life events when
 * the question is "what documented events happened during this period?" Prefer
 * ask_madhav when you need the events interpreted in light of current chart state.
 * Prefer query_dasha_periods to find the dasha active during an event period, then
 * use lel_query to retrieve events from that same period.
 *
 * Input shape hints:
 *   category — optional; event category filter (e.g. "career", "health",
 *     "relationship", "relocation", "education", "chronic").
 *   date_range — optional {start, end} ISO dates; filters events to the range.
 *   min_significance — optional float 0.0–1.0; filters to events at or above threshold.
 *
 * Output shape preview: {ok, result: {events: LelEvent[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: lel_query({category: "career", min_significance: 0.7}) →
 *   {ok: true, result: {events: [{event_id: "LEL.E012", date: "2019-02-15",
 *   category: "career", description: "Resigned from Infosys...", significance: 0.85}]}, ...}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerLelQuery(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=lel_query.d.ts.map