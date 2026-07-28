import 'server-only'

import { createHash } from 'node:crypto'

/**
 * Wave-4 learning loop — calibration-stamp producer.
 *
 * ============================================================================
 * RETIRED by PB-3 (SAMĪKṢĀ) lane L-1, per MEMO_PB-3_0 (OT-11 ruling), 2026-07-28.
 * ============================================================================
 * `recordCalibrationStamp()` was confirmed by X-5 to write EXCLUSIVELY to the `mcp_predictions`
 * table (migration 071), which migration 471 DROPPED. Per MEMO_PB-3_0 §2 it is "retired
 * alongside" ppl_writer. The 12 rows it had accumulated at BIND were all content-empty stamp
 * rows (every substantive column NULL) — nothing a downstream consumer could act on.
 *
 * The function is now an INERT no-op: it touches NO database and returns { ok: false }. Its
 * caller (platform/src/lib/pipelines/shared/onfinish_writethrough.ts) invokes it fire-and-
 * forget (`void`, errors already swallowed), so this retirement changes ZERO served bytes on
 * any route — the calibration write simply no longer happens. `hashQuery` is retained (pure,
 * dependency-free) for any remaining importer.
 *
 * Conversational calibration data now flows from confirmed predictions in
 * `brahma_mimamsa_prediction_ledger` → outcome recording → mimamsa_calibration (PB-3 L-5),
 * not from ambient per-turn stamp rows. See LEDGER_MAP_PB-3.md.
 *
 * ROLLBACK: re-enabling live writes requires BOTH the SQL rollback in migration 471 AND a git
 * revert of this file (MEMO_PB-3_0 §2).
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

/**
 * RETIRED (PB-3 L-1, MEMO_PB-3_0). Formerly wrote one calibration stamp to `mcp_predictions`;
 * that table is dropped, so this is now an inert no-op that touches no DB and returns
 * { ok: false }. Kept as a callable no-op so the fire-and-forget caller keeps compiling and
 * serving byte-identically.
 */
export async function recordCalibrationStamp(
  _stamp: CalibrationStamp,
): Promise<{ ok: boolean; prediction_id?: string }> {
  return { ok: false }
}

export const __TESTING__ = { SALIENCE_FORMULA_VERSION }
