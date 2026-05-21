/**
 * query_chart_facts.ts — MCP Tier 3 surgical primitive: parametric chart-fact lookup.
 *
 * What it does: Queries the 795-row chart_facts table with structured filters
 * (category, planet, house, as_of_date). Returns raw chart-fact rows — birth
 * data, dignity computations, shadbala, aspects, nakshatra placements, divisional
 * chart positions — without running the planner or synthesis. This is a direct
 * L1 data read. The response is tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use query_chart_facts when the question is a single fact
 * lookup ("What is Saturn's shadbala?" / "Which planets are in house 7?").
 * Prefer ask_madhav when synthesis or interpretation is needed alongside the fact.
 * Prefer query_signals when you need MSR signal corpus data rather than raw chart facts.
 *
 * Input shape hints:
 *   category — required; e.g. "shadbala", "dignity", "nakshatra", "aspect",
 *     "house_placement", "dasha_vimshottari", "divisional_D9".
 *   planet — optional; filter to a specific planet (e.g. "Saturn", "Moon").
 *   house — optional; filter to a specific house number (1–12).
 *   as_of_date — optional ISO date; filters time-sensitive facts to that date.
 *   limit — optional; max rows to return (default 50).
 *
 * Output shape preview: {ok, result: {rows: ChartFactRow[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_chart_facts({category: "shadbala", planet: "Saturn"}) →
 *   {ok: true, result: {rows: [{planet: "Saturn", category: "shadbala",
 *   value: "7.4 rupas", ...}]}, epistemics: {surgical: true, confidence_band: "high"}}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQueryChartFacts(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_chart_facts.d.ts.map