/**
 * log_prediction.ts — MCP tool: log a prospective prediction to the PPL.
 *
 * Tier 6 — Write tool (MCP-4-S1). PPL discipline enforcement for MCP callers.
 *
 * Tool description (§4.6-standard, ≥100 words, 5 blocks):
 *
 * What it does: Logs a prospective prediction to the MARSYS-JIS Prospective
 * Prediction Log (PPL). The PPL is the governance substrate that ensures
 * astrological predictions are recorded with their falsifier and confidence
 * horizon BEFORE any outcome is observed — preserving the held-out prospective
 * data discipline required by the Learning Layer (CLAUDE.md §E rule #4).
 * Predictions are stored in the mcp_predictions table with full provenance:
 * key_id, trace_id, and timestamp.
 *
 * When to prefer: Call this tool whenever you are making a time-indexed,
 * testable astrological prediction in a session. This is a governance
 * obligation, not optional. Any predictive ask_madhav call (mode="predictive")
 * triggers this automatically server-side, but you can also call it directly
 * for predictions you formulate yourself from synthesized data. Do NOT wait
 * until after discussing outcomes to log — PPL discipline requires predictions
 * are logged first.
 *
 * Input shape hints:
 *   domain     — one of: career, health, relationships, spiritual, finance,
 *                relocation, family. Use the most specific domain applicable.
 *   horizon    — ISO date ("2026-09-30") or quarter string ("2026-Q3").
 *                The falsifier's time boundary should match this horizon.
 *   falsifier  — a concrete, specific observation that would disprove the
 *                prediction if it does NOT occur. E.g.: "No promotion or role
 *                change by 2026-09-30" not "If things don't work out."
 *   confidence — calibrated estimate: "high" (>0.75), "medium" (0.5–0.75),
 *                "low" (<0.5). Be honest — overconfidence is a calibration error.
 *
 * Output shape preview:
 *   {ok: true, result: {prediction_id: "PPL.MCP.XXXXXXXX"}, trace_id, epistemics}
 *
 * Example:
 *   log_prediction({
 *     domain: "career",
 *     horizon: "2026-Q3",
 *     prediction_text: "Native transitions to a leadership role in current company during Saturn Antardasha's activation of 10th lord Jupiter in 9th",
 *     confidence: "medium",
 *     falsifier: "No promotion, title change, or expanded leadership scope by 2026-09-30",
 *     caller_context: "Asked about career trajectory; Saturn MD + Jupiter AD active"
 *   })
 *   → {ok: true, result: {prediction_id: "PPL.MCP.A3F8B2C1"}, ...}
 */
import { z } from 'zod';
import { callPlatformWrites } from '../client.js';
// ── Input schema ──────────────────────────────────────────────────────────────
const LogPredictionInputSchema = z.object({
    domain: z
        .enum(['career', 'health', 'relationships', 'spiritual', 'finance', 'relocation', 'family'])
        .describe('The life domain of this prediction.'),
    horizon: z
        .string()
        .describe('Time horizon: ISO date ("2026-09-30") or quarter string ("2026-Q3"). ' +
        'The falsifier\'s time boundary must match this horizon.'),
    prediction_text: z
        .string()
        .max(2000)
        .describe('The prediction in prose. Be specific and testable. Max 2000 chars.'),
    confidence: z
        .enum(['high', 'medium', 'low'])
        .describe('Calibrated confidence: high (>0.75), medium (0.5–0.75), low (<0.5).'),
    falsifier: z
        .string()
        .describe('Specific observation that would disprove the prediction. ' +
        'Must be concrete and time-bounded — not vague hedges.'),
    caller_context: z
        .string()
        .optional()
        .describe('Optional label for context (e.g. "career query, Saturn MD active").'),
});
// ── Tool registration ─────────────────────────────────────────────────────────
/**
 * Register the log_prediction MCP tool.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerLogPrediction(server, getPrincipal) {
    server.tool('log_prediction', 'Log a prospective prediction to the MARSYS-JIS PPL. Call BEFORE observing any outcome. ' +
        'Governance obligation for time-indexed predictions — logs domain, horizon, confidence, ' +
        'and falsifier with full provenance. Returns prediction_id for later outcome recording.', LogPredictionInputSchema.shape, async (input) => {
        const principal = getPrincipal();
        const result = await callPlatformWrites('log_prediction', {
            entry: {
                domain: input.domain,
                horizon: input.horizon,
                prediction_text: input.prediction_text,
                confidence: input.confidence,
                falsifier: input.falsifier,
                source: {
                    caller_context: input.caller_context ?? null,
                },
            },
        }, principal);
        if (!result.envelope.ok) {
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(result.envelope, null, 2),
                    },
                ],
                isError: true,
            };
        }
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(result.envelope, null, 2),
                },
            ],
        };
    });
}
//# sourceMappingURL=log_prediction.js.map