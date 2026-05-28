import 'server-only'

import { createHash } from 'node:crypto'

import { query } from '@/lib/db/client'

/**
 * Wave-4 learning loop — calibration-stamp producer.
 *
 * Every chat completion through the adapter pipeline writes one row to
 * mcp_predictions carrying the deterministic stamp. This is independent of
 * the LEL serve-time toggle: predictions log even with LEL off (LEL is a
 * panel input, not a logging gate). Brief BRIEF_4_learning_loop.md §Scope.
 *
 * Idempotency: keyed on (chart_id, ayanamsha_id, query_hash, salience_formula_version);
 * duplicate writes are no-ops via ON CONFLICT DO NOTHING.
 *
 * Failures are swallowed — calibration logging must never break the user's
 * response.
 */

const SALIENCE_FORMULA_VERSION = 'v3.0'

export interface CalibrationStamp {
  chart_id: string
  ayanamsha_id: string
  /** The user's query text (will be hashed). */
  query_text: string
  /** Model ID the response was synthesized with (e.g. "claude-opus-4-7-1m"). */
  model_id: string
  /** ISO timestamp; defaults to now. */
  predicted_at_iso?: string
  /** Override the formula version (defaults to current SALIENCE_FORMULA_VERSION). */
  salience_formula_version?: string
}

export function hashQuery(query_text: string): string {
  return createHash('sha256').update(query_text).digest('hex').slice(0, 16)
}

function generatePredictionId(): string {
  const uuid = (globalThis.crypto?.randomUUID?.() ?? '').replace(/-/g, '')
  const id = uuid || createHash('sha256').update(String(Date.now())).digest('hex')
  return `PPL.CAL.${id.slice(0, 8).toUpperCase()}`
}

/**
 * Write one calibration stamp to mcp_predictions. Idempotent on
 * (chart_id, ayanamsha_id, query_hash, salience_formula_version).
 */
export async function recordCalibrationStamp(
  stamp: CalibrationStamp
): Promise<{ ok: boolean; prediction_id?: string }> {
  const query_hash = hashQuery(stamp.query_text)
  const predicted_at = stamp.predicted_at_iso ?? new Date().toISOString()
  const formula_version = stamp.salience_formula_version ?? SALIENCE_FORMULA_VERSION
  const prediction_id = generatePredictionId()

  try {
    await query(
      `INSERT INTO mcp_predictions (
         prediction_id,
         logged_at,
         chart_id,
         ayanamsha_id,
         query_hash,
         salience_formula_version,
         model_id,
         predicted_at_iso,
         caller_context
       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       ON CONFLICT (chart_id, ayanamsha_id, query_hash, salience_formula_version)
         WHERE chart_id IS NOT NULL
           AND ayanamsha_id IS NOT NULL
           AND query_hash IS NOT NULL
           AND salience_formula_version IS NOT NULL
       DO NOTHING`,
      [
        prediction_id,
        predicted_at,
        stamp.chart_id,
        stamp.ayanamsha_id,
        query_hash,
        formula_version,
        stamp.model_id,
        predicted_at,
        'wave4-calibration-stamp',
      ]
    )
    return { ok: true, prediction_id }
  } catch (err) {
    console.error('[calibration_producer] recordCalibrationStamp DB error', err)
    return { ok: false }
  }
}

export const __TESTING__ = { SALIENCE_FORMULA_VERSION }
