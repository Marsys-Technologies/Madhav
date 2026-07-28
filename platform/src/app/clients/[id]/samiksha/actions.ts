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
 */

import { revalidatePath } from 'next/cache'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { query } from '@/lib/db/client'
import { getLastTurnStamp, computeTurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { LEDGER_TABLE, type LedgerStamp, type Outcome } from '@/lib/pariprashna/samiksha/schema'
import { transitionLifecycle, recordOutcome } from '@/lib/pariprashna/samiksha/writer'
import { confirmDetectedCandidate } from '@/lib/pariprashna/samiksha/reviewConfirm'

/** Guard: must have write access ('all') to the chart to mutate its ledger. */
async function assertCanWrite(chartId: string): Promise<void> {
  const access = await resolveChartPageAccess(chartId)
  if (!access || access.permission !== 'all') {
    throw new Error('samiksha: not authorized to modify this chart’s prediction ledger')
  }
}

/**
 * Resolve the D-16 stamp to COPY at confirmation. Prefers the most recent persisted turn stamp
 * for the row's originating conversation (D-16(d): copy the turn's own stamp). Falls back to the
 * live computed stamp for the chart when the row has no originating turn (W-6 scripted claim) or
 * no prior stamped turn — a conservative, disclosed choice so confirmation never silently fails.
 */
async function resolveStampForRow(rowId: string, chartId: string): Promise<LedgerStamp> {
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

export async function confirmCandidateAction(input: {
  chartId: string
  rowId: string
  probability: number
}): Promise<void> {
  await assertCanWrite(input.chartId)
  const stamp = await resolveStampForRow(input.rowId, input.chartId)
  await confirmDetectedCandidate({ rowId: input.rowId, probability: input.probability, stamp })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function editCandidateAction(input: {
  chartId: string
  rowId: string
  claimText: string
}): Promise<void> {
  await assertCanWrite(input.chartId)
  // A `detected` candidate is still editable (freeze trigger only bites past `detected`).
  await query(
    `UPDATE ${LEDGER_TABLE} SET claim_text = $2
      WHERE id = $1 AND lifecycle_status = 'detected'`,
    [input.rowId, input.claimText],
  )
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function dismissCandidateAction(input: {
  chartId: string
  rowId: string
  reason?: string
}): Promise<void> {
  await assertCanWrite(input.chartId)
  await transitionLifecycle(input.rowId, 'dismissed', { dismissed_reason: input.reason })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function resolvePredictionAction(input: {
  chartId: string
  rowId: string
  outcome: Outcome
  note?: string
}): Promise<void> {
  await assertCanWrite(input.chartId)
  await recordOutcome(input.rowId, {
    outcome: input.outcome,
    outcome_value: outcomeToValue(input.outcome),
    outcome_note: input.note ?? null,
  })
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

export async function batchResolveAction(input: {
  chartId: string
  items: { rowId: string; outcome: Outcome }[]
}): Promise<void> {
  await assertCanWrite(input.chartId)
  for (const { rowId, outcome } of input.items) {
    await recordOutcome(rowId, { outcome, outcome_value: outcomeToValue(outcome) })
  }
  revalidatePath(`/clients/${input.chartId}/samiksha`)
}

/**
 * Map a qualitative outcome to its Brier numeric value. `unverifiable` (can't-tell) returns
 * null — Brier-EXCLUDED (the DAL forces null too, and the DB CHECK backstops it; this is the
 * third, action-layer guarantee). `partial` scores 0.5.
 */
function outcomeToValue(outcome: Outcome): number | null {
  switch (outcome) {
    case 'happened':
      return 1
    case 'did_not_happen':
      return 0
    case 'partial':
      return 0.5
    case 'unverifiable':
      return null
  }
}
