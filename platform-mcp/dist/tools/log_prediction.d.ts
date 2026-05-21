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
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
/**
 * Register the log_prediction MCP tool.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export declare function registerLogPrediction(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=log_prediction.d.ts.map