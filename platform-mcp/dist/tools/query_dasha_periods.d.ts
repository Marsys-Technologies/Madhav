/**
 * query_dasha_periods.ts — MCP Tier 3 surgical primitive: dasha schedule lookup.
 *
 * What it does: Queries the Vimshottari dasha schedule for the native's chart and
 * returns structured period records. Given a date or range, returns the active
 * Mahadasha, Antardasha, and Pratyantar with exact start/end dates. Given no
 * parameters, returns the full dasha sequence. Bypasses the planner and synthesis
 * stages; tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use query_dasha_periods when the question is precisely "what dasha
 * is active on date X?" or "give me the full dasha timeline from 2020 to 2030".
 * Prefer ask_madhav when you also want synthesis — e.g., "what does this dasha
 * mean for career in light of the chart?" Prefer query_chart_facts with
 * category:"dasha_vimshottari" for raw DB rows without the structured period wrapper.
 *
 * Input shape hints:
 *   at — optional ISO date; returns the period active on that date (e.g. "2026-05-21").
 *   range — optional {start, end} ISO date pair; returns all periods overlapping the range.
 *   system — optional dasha system name; defaults to "vimshottari".
 *
 * Output shape preview: {ok, result: {periods: DashaPeriod[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_dasha_periods({at: "2026-05-21"}) →
 *   {ok: true, result: {periods: [{mahadasha: "Saturn", antardasha: "Venus",
 *   start: "2025-11-01", end: "2027-01-15"}]}, epistemics: {surgical: true, ...}}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQueryDashaPeriods(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_dasha_periods.d.ts.map