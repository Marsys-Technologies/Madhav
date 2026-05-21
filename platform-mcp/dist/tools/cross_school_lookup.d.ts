/**
 * cross_school_lookup.ts — MCP Tier 3 surgical primitive: cross-school convergence check.
 *
 * What it does: Checks an astrological claim or rule against multiple Jyotish schools
 * — Parashara (primary), Jaimini, KP, and Tajaka — and returns where they agree,
 * disagree, or are silent on the claim. Returns a structured convergence report per
 * school with source citations and a convergence score. Bypasses planner and synthesis;
 * tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use cross_school_lookup when the question is explicitly about
 * multi-school convergence ("Do all four schools agree that 7th lord in 6th house
 * indicates partnership stress?"). Prefer ask_madhav when you want the multi-school
 * data synthesized alongside the native's actual chart signals. Prefer query_signals
 * to retrieve signals already tagged with school convergence fields.
 *
 * Input shape hints:
 *   claim — required; the astrological claim to test across schools. Phrase as a
 *     declarative statement: "Saturn in 10th house delays career until 36" or
 *     "Moon-Ketu conjunction in 4th house indicates maternal separation theme".
 *   schools — optional array; which schools to check. Defaults to all four.
 *     Valid values: "parashara", "jaimini", "kp", "tajaka".
 *
 * Output shape preview: {ok, result: {convergence_score: float, school_positions:
 *   {school: string, stance: "agree"|"disagree"|"silent", citation: string}[]},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: cross_school_lookup({claim: "Saturn in 10th house delays career until 36"}) →
 *   {convergence_score: 0.75, school_positions: [{school: "parashara", stance: "agree",
 *   citation: "Brihat Parashara Hora Shastra ch. 24"}, ...]}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerCrossSchoolLookup(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=cross_school_lookup.d.ts.map