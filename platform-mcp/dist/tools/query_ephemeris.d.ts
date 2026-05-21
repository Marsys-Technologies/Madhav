/**
 * query_ephemeris.ts — MCP Tier 3 surgical primitive: planetary position lookup.
 *
 * What it does: Returns date-indexed planetary positions from the ephemeris_daily
 * table. Given a planet and date range, returns the planet's sign, degree, nakshatra,
 * retrograde status, and speed for each day in the range. Data covers all 9 Jyotish
 * grahas plus Rahu/Ketu. Source: pre-computed Swiss Ephemeris output in the
 * ephemeris_daily table. Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use for precise positional questions ("What sign was Saturn in
 * during March 2025?", "Was Mars retrograde on date X?"). Prefer query_transit_event
 * when you want to find a specific transit occurrence rather than a positional scan.
 * Prefer ask_madhav when you need the positional data synthesized against the chart.
 *
 * Input shape hints:
 *   planet — required; Jyotish planet name: "Sun", "Moon", "Mars", "Mercury",
 *     "Jupiter", "Venus", "Saturn", "Rahu", "Ketu".
 *   date_range — required {start, end} ISO date pair; max range ~1 year recommended.
 *
 * Output shape preview: {ok, result: {positions: EphemerisRow[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_ephemeris({planet: "Saturn", date_range: {start: "2025-01-01", end: "2025-03-31"}}) →
 *   {ok: true, result: {positions: [{date: "2025-01-01", sign: "Aquarius",
 *   degree: 17.4, retrograde: false, nakshatra: "Shatabhisha"}]}, ...}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQueryEphemeris(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_ephemeris.d.ts.map