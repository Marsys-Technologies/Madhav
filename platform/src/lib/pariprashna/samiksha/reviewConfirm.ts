import 'server-only'
/**
 * SAMĪKṢĀ confirm-flow orchestration — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * Confirming a `detected` candidate from the review tab must: (1) set its confidence band from
 * the elicited probability WHILE the row is still `detected` (settled-claim fields freeze the
 * instant it advances past `detected`, per migration 470's trg_bmpl_freeze_confirmed — so the
 * band MUST be written first), (2) copy the D-16 stamp at the detected→confirmed transition,
 * and (3) advance confirmed→open so the prediction appears in the Open timeline while its
 * window runs. This orchestration lives in L-3 (not the vendored L-1 DAL) so the L-1 snapshot
 * stays byte-identical for clean integration; it composes the L-1 DAL's own functions.
 *
 * Injectable executor (same seam as the DAL) so the flow is testable end-to-end on a real
 * migrated throwaway Postgres. The stamp is passed IN (the caller resolves it via
 * getLastTurnStamp / computeTurnProvenanceStamp) so this module needs no live provenance read.
 */

import { LEDGER_TABLE, toNumrangeLiteral, type LedgerRow, type LedgerStamp } from './schema'
import { confirmDetectedRow, transitionLifecycle, type LedgerExecutor } from './writer'
import { query as sharedQuery } from '@/lib/db/client'

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

const clamp01 = (v: number) => Math.max(0, Math.min(1, v))

/**
 * Turn a point probability into a narrow inclusive-lower / exclusive-upper confidence band,
 * clamped to [0,1]. Default half-width 0.05 → p=0.6 yields [0.55,0.65).
 */
export function probabilityToBand(p: number, halfWidth = 0.05): { low: number; high: number } {
  const low = clamp01(p - halfWidth)
  let high = clamp01(p + halfWidth)
  if (high <= low) high = clamp01(low + 0.01)
  return { low, high }
}

/**
 * Confirm an EXISTING `detected` ledger row (the review-tab flow): set band (if the row has no
 * confidence yet), copy the stamp, and open the window. Returns the row now in `open`. The
 * confidence UPDATE is guarded to `lifecycle_status='detected'` so it can never mutate a
 * settled row.
 *
 * Named distinctly from L-2's `confirmCandidate` (lib/pariprashna/samiksha/confirm.ts), which
 * creates a BRAND-NEW row born `confirmed` directly for the in-stream one-tap flow — the two
 * are complementary primary paths onto the same lifecycle, not duplicates of each other.
 */
export async function confirmDetectedCandidate(
  args: { rowId: string; probability?: number; stamp: LedgerStamp; setBandIfMissing?: boolean },
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow> {
  const { rowId, probability, stamp, setBandIfMissing = true } = args

  if (setBandIfMissing && probability != null) {
    const band = probabilityToBand(probability)
    // Only set when currently NULL, and only while still detected (freeze-safe).
    await exec(
      `UPDATE ${LEDGER_TABLE} SET confidence = $2::numrange
        WHERE id = $1 AND lifecycle_status = 'detected' AND confidence IS NULL`,
      [rowId, toNumrangeLiteral(band)],
    )
  }

  await confirmDetectedRow(rowId, stamp, exec) // detected → confirmed (stamp copied)
  return transitionLifecycle(rowId, 'open', {}, exec) // confirmed → open
}
