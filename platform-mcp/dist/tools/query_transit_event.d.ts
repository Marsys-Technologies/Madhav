/**
 * query_transit_event.ts — MCP Tier 3 surgical primitive: transit event search.
 *
 * What it does: Searches the ephemeris_daily table for specific transit events
 * — sign ingresses, exact conjunctions, oppositions, or degree crossings —
 * within a date range. Answers "When does Saturn enter Aquarius?" or "When
 * does Jupiter transit the 10th house?" Returns event records with the exact
 * date, the planet's state before and after, and any associated astrological
 * significance tags. Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use when you need the specific date(s) a transit occurs
 * rather than a day-by-day position scan. Prefer query_ephemeris for daily
 * positional data over a range. Prefer ask_madhav when you also need synthesis
 * of what the transit means for the native's chart and life domains.
 *
 * Input shape hints:
 *   planet — required; the transiting planet (e.g. "Saturn", "Jupiter").
 *   target — required; the transit target — a sign name (e.g. "Aquarius"),
 *     a house number ("house_10"), or a degree reference ("15 Scorpio").
 *   date_range — required {start, end} ISO date pair; narrows the search window.
 *
 * Output shape preview: {ok, result: {events: TransitEvent[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_transit_event({planet: "Saturn", target: "Aquarius",
 *   date_range: {start: "2020-01-01", end: "2025-12-31"}}) →
 *   {ok: true, result: {events: [{date: "2022-04-29", event_type: "sign_ingress",
 *   planet: "Saturn", from_sign: "Capricorn", to_sign: "Aquarius"}]}, ...}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQueryTransitEvent(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_transit_event.d.ts.map