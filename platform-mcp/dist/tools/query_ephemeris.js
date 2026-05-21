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
import { z } from 'zod';
import { callPlatformPrimitive } from '../client.js';
const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
const QueryEphemerisInputSchema = z.object({
    planet: z.enum(PLANETS).describe('Jyotish graha. One of: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.'),
    date_range: z.object({
        start: z.string().describe('ISO start date (YYYY-MM-DD).'),
        end: z.string().describe('ISO end date (YYYY-MM-DD).'),
    }).describe('Date range for position lookup. Max ~1 year recommended.'),
});
export function registerQueryEphemeris(server, getPrincipal) {
    server.tool('query_ephemeris', 'What it does: Returns date-indexed planetary positions (sign, degree, nakshatra, ' +
        'retrograde status, speed) from the ephemeris_daily table for a given planet and date range. ' +
        'When to prefer: Use for "What sign was Saturn in during Q1 2025?" or retrograde status checks. ' +
        'Prefer query_transit_event for "when does X enter Y?" searches. ' +
        'Prefer ask_madhav when positional data needs chart synthesis. ' +
        'Input shape hints: planet is one of the 9 Jyotish grahas; ' +
        'date_range {start, end} is required; max ~1 year range recommended. ' +
        'Output shape preview: {ok, result: {positions: EphemerisRow[]}, trace_id, epistemics: {surgical: true}}. ' +
        'Example: query_ephemeris({planet: "Saturn", date_range: {start: "2025-01-01", end: "2025-03-31"}}) ' +
        '→ daily degree/sign/nakshatra for Saturn.', QueryEphemerisInputSchema.shape, async (args) => {
        const principal = getPrincipal();
        const { status, envelope } = await callPlatformPrimitive('query_ephemeris', {
            planet: args.planet,
            date_range: args.date_range,
        }, principal);
        const text = JSON.stringify(envelope, null, 2);
        return {
            content: [{ type: 'text', text }],
            isError: !envelope.ok || status >= 400,
        };
    });
}
//# sourceMappingURL=query_ephemeris.js.map