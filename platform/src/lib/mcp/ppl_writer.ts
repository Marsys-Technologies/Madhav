/**
 * ppl_writer.ts — RETIRED interim Prospective Prediction Log (PPL) writer.
 *
 * ============================================================================
 * RETIRED by PB-3 (SAMĪKṢĀ) lane L-1, per MEMO_PB-3_0 (OT-11 ruling), 2026-07-28.
 * ============================================================================
 * The `mcp_predictions` Postgres table this module used to write (migration 071, an interim
 * relay predating §14) was DROPPED by migration 471. Per MEMO_PB-3_0 §2, `ppl_writer.ts`'s
 * write path is retired "alongside it." X-5 confirmed this module was the sole non-calibration
 * writer of that table, with no downstream analytical consumer and no inbound FK.
 *
 * These functions are now INERT no-ops: they touch NO database and MUST NOT be treated as a
 * durable prediction/outcome log. The exported types + signatures are preserved so existing
 * callers (platform/src/app/api/mcp/writes/[action]/route.ts) keep compiling; disposition of
 * that call chain (re-point at brahma_mimamsa_prediction_ledger vs. remove) is L-5's charge
 * per LEDGER_MAP_PB-3.md ("L-5 disposition-owns whatever remains of this call chain").
 *
 * The conversational prediction loop now lives in `brahma_mimamsa_prediction_ledger` via
 * `platform/src/lib/pariprashna/samiksha/` (PB-3 L-1). See LEDGER_MAP_PB-3.md for which table
 * is authoritative for what.
 *
 * ROLLBACK: re-enabling live writes requires BOTH the SQL rollback in migration 471 AND a git
 * revert of this file (MEMO_PB-3_0 §2 — the SQL rollback alone does not restore live writes).
 *
 * @module ppl_writer
 */

import 'server-only'

// ── Interfaces (preserved for the retained call sites' type imports) ──────────

/**
 * A prospective prediction entry. Historically logged to `mcp_predictions`; now inert.
 */
export interface PredictionEntry {
  prediction_id?: string
  logged_at?: string
  horizon: string
  domain: string
  prediction_text: string
  confidence: 'high' | 'medium' | 'low'
  falsifier: string
  source: {
    key_id: string
    trace_id: string | null
    caller_context: string | null
  }
}

/**
 * An outcome entry linked to a prior PredictionEntry. Historically an UPDATE against
 * `mcp_predictions`; now inert (the table no longer exists).
 */
export interface OutcomeEntry {
  prediction_id: string
  recorded_at?: string
  outcome_text: string
  verified: boolean
  notes: string | null
  source: {
    key_id: string
    trace_id: string | null
  }
}

// ── ID generation (retained; deterministic shape unchanged) ───────────────────

function generatePredictionId(): string {
  const uuid = crypto.randomUUID().replace(/-/g, '')
  return `PPL.MCP.${uuid.slice(0, 8).toUpperCase()}`
}

// ── RETIRED no-ops ────────────────────────────────────────────────────────────

/**
 * RETIRED (PB-3 L-1, MEMO_PB-3_0). No longer persists anything — `mcp_predictions` is
 * dropped. Returns a prediction_id for signature compatibility only; the prediction is NOT
 * durably recorded anywhere by this call. Callers needing a durable conversational prediction
 * must use the SAMĪKṢĀ ledger (platform/src/lib/pariprashna/samiksha).
 */
export async function logPrediction(entry: PredictionEntry): Promise<string> {
  const prediction_id = entry.prediction_id ?? generatePredictionId()
  console.warn(
    '[ppl_writer] logPrediction is RETIRED (PB-3 L-1, MEMO_PB-3_0): mcp_predictions was ' +
      'dropped; this call did not persist. Use brahma_mimamsa_prediction_ledger.',
  )
  return prediction_id
}

/**
 * RETIRED (PB-3 L-1, MEMO_PB-3_0). The `mcp_predictions` table it updated no longer exists;
 * always returns { ok: false }. Outcome recording for conversational predictions now lives in
 * the SAMĪKṢĀ ledger's recordOutcome (platform/src/lib/pariprashna/samiksha), L-5's surface.
 */
export async function recordOutcome(_entry: OutcomeEntry): Promise<{ ok: boolean }> {
  console.warn(
    '[ppl_writer] recordOutcome is RETIRED (PB-3 L-1, MEMO_PB-3_0): mcp_predictions was ' +
      'dropped; this call is a no-op. Use the SAMĪKṢĀ ledger (L-5 disposition).',
  )
  return { ok: false }
}
