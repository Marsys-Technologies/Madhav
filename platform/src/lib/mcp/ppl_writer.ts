/**
 * ppl_writer.ts — Interim Prospective Prediction Log (PPL) writer for MCP.
 *
 * PPL substrate status (per CLAUDE.md §E):
 *   The formal 06_LEARNING_LAYER/ PPL scaffold is not yet in place. This module
 *   is the interim path per "sessions that emit time-indexed predictions before
 *   Step 11 closes must still log them." Predictions are stored in the
 *   `mcp_predictions` Postgres table (migration 071) — an interim relay that
 *   survives until the formal substrate lands.
 *
 * TODO(MCP-MIGRATION): when 06_LEARNING_LAYER/ is scaffolded, migrate all rows
 * from `mcp_predictions` to the formal PPL API. Migration path:
 *   1. SELECT all rows WHERE migrated_at IS NULL from mcp_predictions.
 *   2. POST each to the new PPL API endpoint (authored in the M-arc PPL session).
 *   3. UPDATE mcp_predictions SET migrated_at = now(), migrated_to = <ppl_entry_id>
 *      for each migrated row.
 *   4. Retain the mcp_predictions table as archive with migrated_at populated.
 *
 * PPL discipline (G4, MCP_BRIEF §6; CLAUDE.md §E):
 *   "Every time-indexed prediction a session emits is logged with its confidence,
 *    horizon, and falsifier before the outcome is observed."
 *   logPrediction() MUST be called BEFORE the response is returned to the caller
 *   to ensure governance compliance. This is enforced in /api/mcp/execute for
 *   predictive calls (Item 5 of MCP-4-S1 scope).
 *
 * LEL prediction subsection format (preserved for reference — was interim path v0):
 *   ## MCP Predictions
 *   <!-- PPL.MCP.XXXXXXXX -->
 *   ```yaml
 *   prediction_id: PPL.MCP.XXXXXXXX
 *   logged_at: <ISO>
 *   horizon: <horizon>
 *   domain: <domain>
 *   prediction_text: |
 *     <text>
 *   confidence: <high|medium|low>
 *   falsifier: <text>
 *   source:
 *     key_id: <key_id>
 *     trace_id: <trace_id>
 *     caller_context: <context>
 *   ```
 *   The LEL append path was superseded by the mcp_predictions table (migration 071)
 *   per IMPORTANT_CONTEXT override in MCP-4-S1 session brief. The markdown format
 *   is preserved above for documentation and future migration tooling reference.
 *
 * @module ppl_writer
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Interfaces ────────────────────────────────────────────────────────────────

/**
 * A prospective prediction entry to be logged to the PPL.
 *
 * Governance requirement: ALL fields except caller_context are mandatory.
 * falsifier must be a concrete, falsifiable statement — not a placeholder.
 * horizon must be an ISO date or quarter string (e.g. "2026-Q3" or "2026-09-30").
 */
export interface PredictionEntry {
  /** Generated: "PPL.MCP." + nanoid(8). Caller may provide; generated if absent. */
  prediction_id?: string
  /** ISO 8601 timestamp. Defaults to now(). */
  logged_at?: string
  /** Time horizon for the prediction, e.g. "2026-Q3" or "2026-09-30". */
  horizon: string
  /** Domain: one of career, health, relationships, spiritual, finance, relocation, family. */
  domain: string
  /** The prediction in prose. Max 2000 chars. */
  prediction_text: string
  /** Calibrated confidence: high | medium | low. */
  confidence: 'high' | 'medium' | 'low'
  /**
   * What specific observation would disprove this prediction.
   * Auto-logged entries set this to "[AUTO_LOGGED — native to specify falsifier]".
   */
  falsifier: string
  /** Provenance: required by G4 (MCP_BRIEF §6). */
  source: {
    key_id: string
    trace_id: string | null
    caller_context: string | null
  }
}

/**
 * An outcome entry linked to a prior PredictionEntry.
 *
 * Call ONLY after the outcome is observable — PPL discipline rule #4
 * ("held-out prospective data is sacrosanct; the model never sees outcome
 * before prediction").
 */
export interface OutcomeEntry {
  /** Links to a prior PredictionEntry.prediction_id. */
  prediction_id: string
  /** ISO 8601 timestamp. */
  recorded_at?: string
  /** Prose description of what actually happened. */
  outcome_text: string
  /** Did the prediction come true? Factual determination only — not interpretation. */
  verified: boolean
  /** Optional notes on partial matches, context, etc. */
  notes: string | null
  /** Provenance. */
  source: {
    key_id: string
    trace_id: string | null
  }
}

// ── ID generation ─────────────────────────────────────────────────────────────

/**
 * Generate a new PPL prediction ID.
 * Format: "PPL.MCP." + 8 alphanumeric chars (from crypto.randomUUID).
 */
function generatePredictionId(): string {
  // Use the last 8 chars of a UUID segment for brevity and uniqueness.
  const uuid = crypto.randomUUID().replace(/-/g, '')
  return `PPL.MCP.${uuid.slice(0, 8).toUpperCase()}`
}

// ── logPrediction ─────────────────────────────────────────────────────────────

/**
 * Log a prospective prediction to the interim PPL substrate (mcp_predictions table).
 *
 * PPL discipline: this MUST be called before returning the prediction to the
 * caller. The /api/mcp/execute route calls this for predictive mode queries
 * before assembling the response envelope.
 *
 * @param entry  The prediction to log.
 * @returns      The prediction_id (either provided or generated).
 */
export async function logPrediction(entry: PredictionEntry): Promise<string> {
  const prediction_id = entry.prediction_id ?? generatePredictionId()
  const logged_at = entry.logged_at ?? new Date().toISOString()

  // Truncate prediction text to 2000 chars to match DB column expectation.
  const prediction_text = entry.prediction_text.slice(0, 2000)

  try {
    await query(
      `INSERT INTO mcp_predictions (
        prediction_id, logged_at, horizon, domain, prediction_text,
        confidence, falsifier, key_id, trace_id, caller_context
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      ON CONFLICT (prediction_id) DO NOTHING`,
      [
        prediction_id,
        logged_at,
        entry.horizon,
        entry.domain,
        prediction_text,
        entry.confidence,
        entry.falsifier,
        entry.source.key_id,
        entry.source.trace_id,
        entry.source.caller_context,
      ]
    )
  } catch (err) {
    // Log but do not throw — PPL write failure should not block the caller's response.
    // The prediction is lost in this case; a future reconciliation pass can identify
    // gaps by comparing query_trace_steps predictive calls with mcp_predictions rows.
    console.error('[ppl_writer] logPrediction DB error', err)
  }

  return prediction_id
}

// ── recordOutcome ─────────────────────────────────────────────────────────────

/**
 * Record an outcome against a prior prediction.
 *
 * The prediction_id must match a row in mcp_predictions. If not found,
 * returns {ok: false}. The outcome fields are written to the same row
 * (not a separate table) to keep the prediction-outcome pair co-located
 * for migration to the formal PPL substrate.
 *
 * @param entry  The outcome to record.
 * @returns      {ok: true} if the prediction_id was found; {ok: false} if not.
 */
export async function recordOutcome(entry: OutcomeEntry): Promise<{ ok: boolean }> {
  const recorded_at = entry.recorded_at ?? new Date().toISOString()

  try {
    const { rows } = await query<{ prediction_id: string }>(
      `UPDATE mcp_predictions
       SET outcome_text        = $2,
           verified            = $3,
           outcome_notes       = $4,
           outcome_recorded_at = $5,
           outcome_key_id      = $6,
           outcome_trace_id    = $7
       WHERE prediction_id = $1
       RETURNING prediction_id`,
      [
        entry.prediction_id,
        entry.outcome_text,
        entry.verified,
        entry.notes,
        recorded_at,
        entry.source.key_id,
        entry.source.trace_id,
      ]
    )

    if (rows.length === 0) {
      return { ok: false }
    }
    return { ok: true }
  } catch (err) {
    console.error('[ppl_writer] recordOutcome DB error', err)
    return { ok: false }
  }
}
