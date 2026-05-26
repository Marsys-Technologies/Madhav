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
 * obligation, not optional. Any predictive holistic_bundle call (mode="predictive")
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

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformWrites } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const LOG_PREDICTION_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Logs a prospective prediction to the MARSYS-JIS Prospective Prediction Log (PPL) ' +
    'with domain, horizon, confidence, and falsifier BEFORE any outcome is observed. ' +
    'Required fields: domain, horizon, prediction_text, confidence, falsifier.',
  whenToPrefer:
    'FIRST CALL when you are making any time-indexed, testable astrological prediction — ' +
    'this is a governance obligation, not optional. ' +
    'Log before discussing outcomes; PPL discipline requires predictions are logged first. ' +
    'Use record_outcome later when the outcome is observable.',
})

// ── Input schema ──────────────────────────────────────────────────────────────

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
const LogPredictionInputSchema = z.object({
  domain: z
    .enum(['career', 'health', 'relationships', 'spiritual', 'finance', 'relocation', 'family'])
    .describe('The life domain of this prediction.'),
  horizon: z
    .string()
    .describe(
      'Time horizon: ISO date ("2026-09-30") or quarter string ("2026-Q3"). ' +
      'The falsifier\'s time boundary must match this horizon.'
    ),
  prediction_text: z
    .string()
    .max(2000)
    .describe('The prediction in prose. Be specific and testable. Max 2000 chars.'),
  // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
  // Accepts float 0.0–1.0 (old callers) or enum string (new callers).
  // Float is mapped: >0.75→high, 0.5–0.75→medium, <0.5→low.
  confidence: z
    .union([
      z.enum(['high', 'medium', 'low']),
      z.number().min(0).max(1),
    ])
    .transform(c =>
      typeof c === 'number'
        ? c > 0.75 ? 'high' : c >= 0.5 ? 'medium' : 'low'
        : c
    )
    .describe(
      'Calibrated confidence: high (>0.75), medium (0.5–0.75), low (<0.5). ' +
      'Also accepts float 0.0–1.0 (backward-compat).'
    ),
  // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
  // falsifier is now optional with empty-string default for old callers that omit it.
  falsifier: z
    .string()
    .optional()
    .default('')
    .describe(
      'Specific observation that would disprove the prediction. ' +
      'Must be concrete and time-bounded — not vague hedges.'
    ),
  caller_context: z
    .string()
    .optional()
    .describe('Optional label for context (e.g. "career query, Saturn MD active").'),
})

type LogPredictionInput = z.infer<typeof LogPredictionInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the log_prediction MCP tool.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerLogPrediction(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'log_prediction',
    LOG_PREDICTION_DESCRIPTION,
    LogPredictionInputSchema.shape,
    async (input: LogPredictionInput) => {
      const principal = getPrincipal()

      const result = await callPlatformWrites(
        'log_prediction',
        {
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
        },
        principal
      )

      if (!result.envelope.ok) {
        return errorResult(result.envelope)
      }

      return okResult(result.envelope)
    }
  )
}
