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
import { z } from 'zod';
import { callPlatformPrimitive } from '../client.js';
const QueryDashaPeriodsInputSchema = z.object({
    at: z.string().optional().describe('ISO date to look up the active dasha period for (e.g. "2026-05-21").'),
    range: z.object({
        start: z.string().describe('ISO start date of the range.'),
        end: z.string().describe('ISO end date of the range.'),
    }).optional().describe('Date range to retrieve all overlapping dasha periods.'),
    system: z.string().optional().default('vimshottari').describe('Dasha system. Defaults to "vimshottari".'),
});
export function registerQueryDashaPeriods(server, getPrincipal) {
    server.tool('query_dasha_periods', 'What it does: Returns the Vimshottari dasha schedule for the native\'s chart — ' +
        'Mahadasha, Antardasha, Pratyantar — with exact start/end dates, bypassing synthesis. ' +
        'When to prefer: Use for "what dasha is active on date X?" without synthesis overhead. ' +
        'Prefer ask_madhav when you also need interpretation of what the period means. ' +
        'Input shape hints: at — single ISO date lookup; range — {start, end} for a date window; ' +
        'system defaults to "vimshottari". All params optional; omitting all returns full sequence. ' +
        'Output shape preview: {ok, result: {periods: DashaPeriod[]}, trace_id, epistemics: {surgical: true}}. ' +
        'Example: query_dasha_periods({at: "2026-05-21"}) → active Mahadasha + Antardasha with dates.', QueryDashaPeriodsInputSchema.shape, async (args) => {
        const principal = getPrincipal();
        const { status, envelope } = await callPlatformPrimitive('query_dasha_periods', {
            ...(args.at ? { at: args.at } : {}),
            ...(args.range ? { range: args.range } : {}),
            system: args.system ?? 'vimshottari',
        }, principal);
        const text = JSON.stringify(envelope, null, 2);
        return {
            content: [{ type: 'text', text }],
            isError: !envelope.ok || status >= 400,
        };
    });
}
//# sourceMappingURL=query_dasha_periods.js.map