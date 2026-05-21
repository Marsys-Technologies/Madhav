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
    // PLACEHOLDER description — full §4.6 description lands in MCP-2-S2.
    const placeholderDescription = 'Runs the full MARSYS-JIS pipeline for the question and returns a ' +
        'synthesized answer with citations, trace ID, and epistemics. [Full ' +
        'description authoring: MCP-2-S2]';
    server.tool('ask_madhav', placeholderDescription, AskMadhavInputSchema.shape, async (args) => {
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