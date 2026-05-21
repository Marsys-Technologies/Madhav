/**
 * query_panchanga.ts — MCP Tier 3 surgical primitive: daily panchang lookup.
 *
 * What it does: Returns the five limbs of the Vedic day (panchang) for any
 * date: tithi (lunar day), vara (weekday), nakshatra (Moon's asterism), yoga
 * (Sun+Moon sum), and karana (half-tithi). Also returns hora (planetary hour),
 * choghadiya (auspiciousness windows), muhurat windows, inauspicious periods
 * (Rahu Kalam, Gulika Kalam, Yamaghanta), and special yogas. Data is sourced
 * from the pre-computed panchanga_daily table (73,414 rows, 1900–2100).
 * Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use for date-specific panchang questions ("What are today's
 * auspicious windows?", "What is the nakshatra on 2026-05-21?"). Prefer
 * ask_madhav when you need interpretation of the panchang in light of the chart
 * (e.g., "How does today's Rahu Kalam interact with my natal Rahu?").
 *
 * Input shape hints:
 *   date — required ISO date string (YYYY-MM-DD).
 *   observer — optional {lat, lon} in decimal degrees; defaults to the native's
 *     birth location (Bhubaneswar: lat 20.29, lon 85.82).
 *
 * Output shape preview: {ok, result: {tithi, vara, nakshatra, yoga, karana,
 *   hora: [], choghadiya: [], inauspicious: {}, auspicious: {}},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_panchanga({date: "2026-05-21"}) →
 *   {ok: true, result: {tithi: "Shukla Chaturdashi", vara: "Guruvara",
 *   nakshatra: "Vishakha", yoga: "Shiva", karana: "Bava", ...}}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerQueryPanchanga(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=query_panchanga.d.ts.map