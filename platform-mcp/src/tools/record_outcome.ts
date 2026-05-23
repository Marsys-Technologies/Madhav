/**
 * record_outcome.ts — MCP tool: record an outcome against a prior prediction.
 *
 * Tier 6 — Write tool (MCP-4-S1). Closes the prediction-outcome loop in the PPL.
 *
 * Tool description (§4.6-standard, ≥100 words, 5 blocks):
 *
 * What it does: Records an observed outcome against a prior PPL prediction
 * (identified by prediction_id from log_prediction). Updates the mcp_predictions
 * row with the outcome text, verification verdict, and full provenance. This
 * closes the prediction-outcome loop required by the Learning Layer discipline:
 * predictions are logged before observation; outcomes are recorded after.
 * Calibration feedback accumulates over time via this mechanism.
 *
 * When to prefer: Call this tool ONLY after an outcome is observable and you
 * have factual evidence of what occurred. Do not call it speculatively or
 * prematurely — the verified field is a factual determination, not an
 * interpretation. If the horizon date has not yet passed, do not record an
 * outcome. If partial evidence is available (e.g., some but not all predicted
 * conditions met), record with verified=false and explain in notes. Link to
 * the specific prediction_id returned by log_prediction.
 *
 * Input shape hints:
 *   prediction_id — from a prior log_prediction call ("PPL.MCP.XXXXXXXX").
 *                   If the id is unknown, use list_recent_queries to find
 *                   the trace_id of the originating query, then check the
 *                   predictions_logged field of that response.
 *   outcome_text  — factual description of what happened. Cite sources if
 *                   possible (e.g. "Native confirmed promotion in May 2026").
 *   verified      — true if the prediction came true as stated; false otherwise.
 *                   Partial matches are false with explanation in notes.
 *   notes         — optional context, partial match explanations, caveats.
 *
 * Output shape preview:
 *   {ok: true, result: {linked_to: "PPL.MCP.XXXXXXXX", found: true}, trace_id, epistemics}
 *   If prediction_id not found: result.found = false, warnings contain details.
 *
 * Example:
 *   record_outcome({
 *     prediction_id: "PPL.MCP.A3F8B2C1",
 *     outcome_text: "Native received team lead title in August 2026, confirmed by native in session 2026-09-10",
 *     verified: true,
 *     notes: "Promotion was within existing company, not new company as some signals suggested"
 *   })
 *   → {ok: true, result: {linked_to: "PPL.MCP.A3F8B2C1", found: true}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformWrites } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const RECORD_OUTCOME_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Records an observed outcome against a prior PPL prediction (by prediction_id ' +
    'from log_prediction), closing the prediction-outcome loop required by the Learning Layer discipline.',
  whenToPrefer:
    'Use ONLY after an outcome is observable and you have factual evidence of what occurred. ' +
    'Do not call speculatively or before the horizon date passes. ' +
    'Partial matches record with verified=false and explanation in notes.',
})

// ── Input schema ──────────────────────────────────────────────────────────────

const RecordOutcomeInputSchema = z.object({
  prediction_id: z
    .string()
    .describe('The prediction_id from a prior log_prediction call (format: PPL.MCP.XXXXXXXX).'),
  outcome_text: z
    .string()
    .max(2000)
    .describe('Factual description of what actually occurred. Cite sources where possible.'),
  verified: z
    .boolean()
    .describe('Did the prediction come true as stated? true = yes; false = no or partial.'),
  notes: z
    .string()
    .optional()
    .describe('Optional context, partial match explanation, or caveats.'),
})

type RecordOutcomeInput = z.infer<typeof RecordOutcomeInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the record_outcome MCP tool.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerRecordOutcome(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'record_outcome',
    RECORD_OUTCOME_DESCRIPTION,
    RecordOutcomeInputSchema.shape,
    async (input: RecordOutcomeInput) => {
      const principal = getPrincipal()

      const result = await callPlatformWrites(
        'record_outcome',
        {
          entry: {
            prediction_id: input.prediction_id,
            outcome_text: input.outcome_text,
            verified: input.verified,
            notes: input.notes ?? null,
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
