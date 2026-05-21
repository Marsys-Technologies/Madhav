/**
 * ask_madhav.ts — MCP tool: end-to-end MARSYS-JIS pipeline.
 *
 * Tier 1 tool (MCP_BRIEF §4.1). Runs the full pipeline: planner → arbitrate
 * → compose_bundle → retrieval → synthesis. Returns a synthesized answer with
 * citations, trace ID, synthesis audit, suggested follow-ups, and epistemics.
 *
 * Tool description is a PLACEHOLDER in this session (~30 words).
 * Full §4.6-standard description (120–180 words, 5 blocks) authors in MCP-2-S2.
 */
import { z } from 'zod';
import { callPlatform } from '../client.js';
// ── Input schema ──────────────────────────────────────────────────────────────
const AskMadhavInputSchema = z.object({
    query: z.string().describe('The question to answer.'),
    mode: z
        .enum([
        'auto',
        'holistic',
        'factual',
        'predictive',
        'cross_domain',
        'discovery',
        'remedial',
        'classical_grounding',
        'multi_school_triangulation',
    ])
        .optional()
        .default('auto')
        .describe('Query mode. Default: auto.'),
    context_hint: z
        .string()
        .optional()
        .describe('Optional summary of prior conversation context from the host chat.'),
});
// ── Tool registration ─────────────────────────────────────────────────────────
/**
 * Register the ask_madhav MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerAskMadhav(server, getPrincipal) {
    // §4.6-standard description — authored MCP-2-S2.
    //
    // What it does: Runs the full MARSYS-JIS astrological pipeline end-to-end —
    // planner selects retrieval tools, tools execute in parallel, results are
    // synthesized against the 514-signal MSR corpus, and the answer is returned
    // with Markdown prose, citations, trace ID, synthesis audit, and epistemics.
    // The Whole-Chart-Read discipline (B.11) is enforced by default: at least
    // one L2.5 synthesis tool always fires, guaranteeing holistic grounding.
    //
    // When to prefer: Use ask_madhav for any question requiring interpretation,
    // synthesis, or prediction. Prefer query_chart_facts or query_signals when
    // the question is a single fact lookup and you want the raw value without
    // synthesis overhead. Prefer plan_query + execute_plan for differential
    // analysis (inspect the plan before committing to execution).
    //
    // Input shape hints:
    //   query — the question in plain English; no chart_id needed (singleton chart).
    //   mode — optional; defaults to "auto" (planner chooses query_class). Use
    //     "holistic" to force B.11 holistic read; "predictive" to trigger PPL
    //     logging; other modes mirror the query_class enum on PipelinePlan.
    //   context_hint — optional single-paragraph summary of prior conversation
    //     context; fed to the planner but not persisted (MCP is stateless per D10).
    //
    // Output shape preview: {ok, answer_markdown, citations[], trace_id, plan,
    //   epistemics, synthesis_audit, suggested_followups[], predictions_logged[]}.
    //
    // Example: ask_madhav({query: "What does my 10th house say about career in
    //   the current Saturn antardasha?", mode: "auto"}) →
    //   {ok: true, answer_markdown: "Saturn as Amatyakaraka...", citations:
    //   ["SIG.MSR.234", "SIG.MSR.512"], trace_id: "qry_2026-05-21_a4f3e2",
    //   synthesis_audit: {holistic_read_passed: true, ...}, ...}
    const fullDescription = 'What it does: Runs the full MARSYS-JIS astrological pipeline end-to-end — ' +
        'planner selects retrieval tools, tools execute in parallel, results are ' +
        'synthesized against the 514-signal MSR corpus, and the answer is returned ' +
        'with Markdown prose, citations, trace ID, synthesis audit, and epistemics. ' +
        'The Whole-Chart-Read discipline (B.11) is enforced by default: at least ' +
        'one L2.5 synthesis tool always fires.\n\n' +
        'When to prefer: Use ask_madhav for any question requiring interpretation, ' +
        'synthesis, or prediction. Prefer query_chart_facts or query_signals for ' +
        'single fact lookups. Prefer plan_query + execute_plan for differential ' +
        'analysis (inspect the plan before committing to execution).\n\n' +
        'Input shape hints: query — the question in plain English; no chart_id (singleton). ' +
        'mode — optional; defaults to "auto". Use "holistic" to force B.11 holistic read; ' +
        '"predictive" to trigger PPL logging. context_hint — optional summary of prior ' +
        'conversation context; fed to the planner but not persisted (stateless per D10).\n\n' +
        'Output shape preview: {ok, answer_markdown, citations[], trace_id, plan, ' +
        'epistemics, synthesis_audit, suggested_followups[], predictions_logged[]}.\n\n' +
        'Example: ask_madhav({query: "What does my 10th house say about career in ' +
        'the current Saturn antardasha?", mode: "auto"}) → ' +
        '{ok: true, answer_markdown: "Saturn as Amatyakaraka...", ' +
        'citations: ["SIG.MSR.234", "SIG.MSR.512"], trace_id: "qry_...", ' +
        'synthesis_audit: {holistic_read_passed: true, ...}}';
    server.tool('ask_madhav', fullDescription, AskMadhavInputSchema.shape, async (args) => {
        const principal = getPrincipal();
        const { status, envelope } = await callPlatform({
            tool: 'ask_madhav',
            params: {
                query: args.query,
                mode: args.mode,
                ...(args.context_hint ? { context_hint: args.context_hint } : {}),
            },
        }, principal);
        const text = JSON.stringify(envelope, null, 2);
        if (!envelope.ok) {
            return {
                content: [{ type: 'text', text }],
                isError: true,
            };
        }
        // Non-2xx from the platform (should be surfaced to the caller)
        if (status >= 400) {
            return {
                content: [{ type: 'text', text }],
                isError: true,
            };
        }
        return {
            content: [{ type: 'text', text }],
        };
    });
}
//# sourceMappingURL=ask_madhav.js.map