'use server'
/**
 * SAMĪKṢĀ review-tab server actions — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * Every mutation the review surface performs, as authenticated server actions. Each re-checks
 * chart access (never trusts the client), routes through the L-1 DAL / L-3 confirm-flow, and
 * revalidates the tab. NO auto-promotion (W-1): a row only becomes `confirmed`/`open` through
 * an explicit human act here (or L-2's in-stream confirm) — there is no code path that advances
 * a `detected` row without one of these calls.
 *
 * De-duplication note (resolved at integration): L-2 builds the in-stream confirm affordance
 * against the SAME L-1 DAL, creating a brand-new row born `confirmed` directly
 * (`lib/pariprashna/samiksha/confirm.ts`'s `confirmCandidate`). This review-tab flow instead
 * confirms an EXISTING `detected` row (`reviewConfirm.ts`'s `confirmDetectedCandidate`) — the two
 * are complementary primary paths onto the same lifecycle, not duplicates; both were kept,
 * renamed to avoid the file/export collision.
 *
 * ── ONE outcome map (G4, SAMĀPTI §8.1 / BRIEF_PB-3.1 G4) ──────────────────────────────────
 * This module used to carry its OWN private `outcomeToValue` switch, so the live resolve
 * surface never called L-5's `recordConversationalOutcome` — leaving that recorder with zero
 * non-test callers and the estate with two unrelated outcome→value maps. Both resolve actions
 * below now go through `recordConversationalOutcome`, which is the sole caller of the sole
 * map, `outcome_calibration.ts`'s exported `outcomeToValue`. Consequences of the
 * consolidation, all deliberate:
 *   • the Brier score is now COMPUTED on every live resolution (it previously was not),
 *   • a `CalibrationWriteIntent` is now ASSEMBLED on every live resolution (still not
 *     persisted — see `CALIBRATION_PARK_REASON` / PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md),
 *   • `partial` is no longer hard-coded to 0.5 here; it defaults to `DEFAULT_PARTIAL_VALUE`
 *     and an operator fraction can be threaded through `partialValue`.
 * There is no second map to keep in sync. `outcome_map_singularity.test.ts` is the detector
 * that keeps it that way — it fails if a second map or a direct `recordOutcome` call reappears
 * on this surface.
 */

import { revalidatePath } from 'next/cache'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { query, withTransaction } from '@/lib/db/client'
import type { LedgerExecutor } from '@/lib/pariprashna/samiksha/writer'
import { isTurnProvenanceStamp, computeTurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { LEDGER_TABLE, type LedgerStamp, type Outcome } from '@/lib/pariprashna/samiksha/schema'
import { transitionLifecycle } from '@/lib/pariprashna/samiksha/writer'
import { confirmDetectedCandidate } from '@/lib/pariprashna/samiksha/reviewConfirm'
import { recordConversationalOutcome } from '@/lib/pariprashna/samiksha/outcome_recorder'

/** Guard: must have write access ('all') to the chart to mutate its ledger. */
async function assertCanWrite(chartId: string): Promise<void> {
  const access = await resolveChartPageAccess(chartId)
  if (!access || access.permission !== 'all') {
    throw new Error('samiksha: not authorized to modify this chart’s prediction ledger')
  }
}

/**
 * Jātaka Phase-A3 (independent-review finding): `assertCanWrite` authorizes
 * the CHART; every mutation below then acts on `rowId` alone through the
 * shared DAL (transitionLifecycle / confirmDetectedCandidate /
 * recordConversationalOutcome), none of which take a chart_id to bind
 * against. Without this check, a caller with write access to chart A could
 * mutate chart B's ledger row by supplying its id. Called after
 * `assertCanWrite` and before any DAL call.
 */
async function assertRowBelongsToChart(rowId: string, chartId: string) {
  const { rows } = await query<{ chart_id: string; message_part_id: string | null; lifecycle_status: string }>(
    `SELECT chart_id, message_part_id, lifecycle_status FROM ${LEDGER_TABLE} WHERE id = $1`,
    [rowId],
  )
  if (rows[0]?.chart_id !== chartId) {
    throw new Error(`samiksha: ledger row ${rowId} does not belong to chart ${chartId}`)
  }
  return rows[0]
}

/**
 * Copy the exact originating answer's D-16 stamp. Only scripted claims without a
 * message part use the current chart stamp. Missing source provenance refuses confirmation.
 */
async function resolveStampForRow(rowId: string, exec: LedgerExecutor, scriptedStamp: LedgerStamp | null): Promise<LedgerStamp> {
  const { rows } = await exec<{ message_part_id: string | null; metadata_json: Record<string, unknown> | null }>(
    `SELECT l.message_part_id, cm.metadata_json FROM ${LEDGER_TABLE} l
       LEFT JOIN message_parts mp ON mp.id=l.message_part_id
       LEFT JOIN conversation_messages cm ON cm.id=mp.message_id WHERE l.id=$1`, [rowId])
  const source = rows[0]
  if (source?.message_part_id) {
    const stamp = source.metadata_json?.provenance_stamp
    if (!isTurnProvenanceStamp(stamp)) throw new Error('The source answer has no valid provenance stamp.')
    return { build_id: stamp.build_id, priors_version: stamp.priors_version,
      formula_versions: stamp.formula_versions, ranking_config: stamp.ranking_config, now_context_date: stamp.now_context_date }
  }
  if (!scriptedStamp) throw new Error('This prediction has no available source provenance.')
  return scriptedStamp
}

export async function confirmCandidateAction(input: {
  chartId: string
  rowId: string
  probability: number
}): Promise<void> {
  if (!Number.isFinite(input.probability) || input.probability < 0 || input.probability > 1) throw new Error('Probability must be between 0 and 1.')
  await assertCanWrite(input.chartId)
  const initial = await assertRowBelongsToChart(input.rowId, input.chartId)
  // Scripted claims require pooled live metadata reads. Complete those before
  // taking the transaction connection; source-answer reads below reuse it.
  const scriptedStamp = initial.lifecycle_status === 'detected' && !initial.message_part_id
    ? await computeTurnProvenanceStamp(input.chartId) : null
  await withTransaction(async client => {
    const locked = await client.query(`SELECT id, lifecycle_status FROM ${LEDGER_TABLE} WHERE id=$1 AND chart_id=$2 AND chart_context_stale_at IS NULL FOR UPDATE`, [input.rowId, input.chartId])
    if (locked.rows.length !== 1) throw new Error('This prediction is unavailable for confirmation.')
    // A lost response or a stale review tab may repeat an already committed
    // human confirmation. Preserve its original confidence and provenance.
    const state = locked.rows[0].lifecycle_status
    if (['confirmed', 'open', 'window_closed', 'outcome_recorded', 'unverifiable'].includes(state)) return
    if (state !== 'detected') throw new Error('This prediction is unavailable for confirmation.')
    const exec: LedgerExecutor = async <T,>(sql: string, params?: unknown[]) => {
      const result = await client.query(sql, params)
      return { rows: result.rows as T[], rowCount: result.rowCount }
    }
    const stamp = await resolveStampForRow(input.rowId, exec, scriptedStamp)
    await confirmDetectedCandidate({ rowId: input.rowId, probability: input.probability, stamp }, exec)
  })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function editCandidateAction(input: {
  chartId: string
  rowId: string
  claimText: string
}): Promise<void> {
  await assertCanWrite(input.chartId)
  // A `detected` candidate is still editable (freeze trigger only bites past `detected`).
  // Jātaka Phase-A3 (independent-review finding): bound to the caller's own
  // chart (a raw query, not the shared DAL, so it binds chart_id directly
  // rather than via a separate ownership check) and excludes a
  // chart-context-stale row — editing a claim a correction has already
  // superseded would silently mutate historical evidence.
  const result = await query(
    `UPDATE ${LEDGER_TABLE} SET claim_text = $2
      WHERE id = $1 AND chart_id = $3 AND lifecycle_status = 'detected'
        AND chart_context_stale_at IS NULL`,
    [input.rowId, input.claimText, input.chartId],
  )
  if (result.rowCount !== 1) throw new Error('This prediction is no longer editable.')
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function dismissCandidateAction(input: {
  chartId: string
  rowId: string
  reason?: string
}): Promise<void> {
  await assertCanWrite(input.chartId)
  await assertRowBelongsToChart(input.rowId, input.chartId)
  await transitionLifecycle(input.rowId, 'dismissed', { dismissed_reason: input.reason })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

/**
 * Resolve one prediction. Routes through L-5's `recordConversationalOutcome` — the ONE
 * outcome→value map (`outcome_calibration.ts`'s `outcomeToValue`) — never a local
 * re-implementation (G4). See the "ONE outcome map" note in this module's header.
 *
 * Precondition equivalence (why this is not a behaviour change): `recordConversationalOutcome`
 * requires `lifecycle_status = 'window_closed'`. That is EXACTLY what the previous direct
 * `recordOutcome` call already enforced transitively — `LEGAL_TRANSITIONS` (schema.ts) lists
 * `window_closed` as the sole predecessor of both `outcome_recorded` and `unverifiable`, and
 * `transitionLifecycle` asserts it before any write. The recorder simply raises the same
 * rejection earlier, with a message that names the required state.
 */
export async function resolvePredictionAction(input: {
  chartId: string
  rowId: string
  outcome: Outcome
  note?: string
  /** Operator-supplied fraction for a `partial` outcome; defaults to DEFAULT_PARTIAL_VALUE. */
  partialValue?: number
}): Promise<void> {
  await assertCanWrite(input.chartId)
  await assertRowBelongsToChart(input.rowId, input.chartId)
  await recordConversationalOutcome(input.rowId, {
    outcome: input.outcome,
    outcome_note: input.note ?? null,
    partial_value: input.partialValue,
  })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function batchResolveAction(input: {
  chartId: string
  items: { rowId: string; outcome: Outcome }[]
}): Promise<void> {
  await assertCanWrite(input.chartId)
  if (!Array.isArray(input.items) || input.items.length > 100 || new Set(input.items.map(i => i.rowId)).size !== input.items.length) throw new Error('Invalid prediction selection.')
  await withTransaction(async client => {
    const exec: LedgerExecutor = async <T,>(sql: string, params?: unknown[]) => {
      const result = await client.query(sql, params)
      return { rows: result.rows as T[], rowCount: result.rowCount }
    }
    // Lock in a deterministic order; validate every chart binding before any outcome write.
    for (const rowId of input.items.map(i => i.rowId).sort()) {
      const { rows } = await client.query(`SELECT id FROM ${LEDGER_TABLE} WHERE id=$1 AND chart_id=$2 AND chart_context_stale_at IS NULL FOR UPDATE`, [rowId, input.chartId])
      if (rows.length !== 1) throw new Error('A selected prediction is unavailable for this chart.')
    }
    for (const { rowId, outcome } of input.items) await recordConversationalOutcome(rowId, { outcome }, exec)
  })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}
