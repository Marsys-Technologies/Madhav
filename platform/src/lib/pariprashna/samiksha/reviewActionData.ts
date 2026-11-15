import 'server-only'

import { query } from '@/lib/db/client'
import { getLastTurnStamp, computeTurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { LEDGER_TABLE, type LedgerStamp } from './schema'

/**
 * Jātaka Phase-A3 (independent-review finding): `assertCanWrite` authorizes
 * the CHART; every mutation below then acts on `rowId` alone through the
 * shared DAL (transitionLifecycle / confirmDetectedCandidate /
 * recordConversationalOutcome), none of which take a chart_id to bind
 * against. Without this check, a caller with write access to chart A could
 * mutate chart B's ledger row by supplying its id. Called after
 * `assertCanWrite` and before any DAL call.
 */
export async function assertRowBelongsToChart(rowId: string, chartId: string): Promise<void> {
  const { rows } = await query<{ chart_id: string }>(
    `SELECT chart_id FROM ${LEDGER_TABLE} WHERE id = $1`,
    [rowId],
  )
  if (rows[0]?.chart_id !== chartId) {
    throw new Error(`samiksha: ledger row ${rowId} does not belong to chart ${chartId}`)
  }
}

/**
 * Resolve the D-16 stamp to COPY at confirmation. Prefers the most recent persisted turn stamp
 * for the row's originating conversation (D-16(d): copy the turn's own stamp). Falls back to the
 * live computed stamp for the chart when the row has no originating turn (W-6 scripted claim) or
 * no prior stamped turn — a conservative, disclosed choice so confirmation never silently fails.
 */
export async function resolveStampForRow(rowId: string, chartId: string): Promise<LedgerStamp> {
  const { rows } = await query<{ conversation_id: string | null }>(
    `SELECT cm.conversation_id
       FROM ${LEDGER_TABLE} l
       LEFT JOIN message_parts mp ON mp.id = l.message_part_id
       LEFT JOIN conversation_messages cm ON cm.id = mp.message_id
      WHERE l.id = $1`,
    [rowId],
  )
  const conversationId = rows[0]?.conversation_id ?? null
  if (conversationId) {
    const last = await getLastTurnStamp(conversationId)
    if (last) {
      return {
        build_id: last.build_id,
        priors_version: last.priors_version,
        formula_versions: last.formula_versions,
        ranking_config: last.ranking_config,
        now_context_date: last.now_context_date,
      }
    }
  }
  const computed = await computeTurnProvenanceStamp(chartId)
  return {
    build_id: computed.build_id,
    priors_version: computed.priors_version,
    formula_versions: computed.formula_versions,
    ranking_config: computed.ranking_config,
    now_context_date: computed.now_context_date,
  }
}

/** Guarded edit of a detected claim; authorization stays in the action. */
export async function editCandidateClaim(rowId: string, claimText: string, chartId: string): Promise<void> {
  // A `detected` candidate is still editable (freeze trigger only bites past `detected`).
  // Jātaka Phase-A3 (independent-review finding): bound to the caller's own
  // chart (a raw query, not the shared DAL, so it binds chart_id directly
  // rather than via a separate ownership check) and excludes a
  // chart-context-stale row — editing a claim a correction has already
  // superseded would silently mutate historical evidence.
  await query(
    `UPDATE ${LEDGER_TABLE} SET claim_text = $2
      WHERE id = $1 AND chart_id = $3 AND lifecycle_status = 'detected'
        AND chart_context_stale_at IS NULL`,
    [rowId, claimText, chartId],
  )
}
