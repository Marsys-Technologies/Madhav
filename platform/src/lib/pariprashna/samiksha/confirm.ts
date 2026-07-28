import 'server-only'
/**
 * SAMĪKṢĀ candidate → ledger confirm flow — PB-3 (SAMĪKṢĀ) lane L-2.
 *
 * Design authority: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14.3 + D-16(d).
 *
 * The flow the brief names "candidate → confirm → ledger row":
 *   1. The detector (detector.ts) emitted a structured candidate, persisted as a
 *      PB-2 `prediction_candidate` message_part in the stream (state `detected`
 *      lives on the ledger row, NOT the part).
 *   2. A HUMAN confirms it ("Log to Samīkṣā" — no auto-promotion, §14.3 / W-1).
 *   3. Confirmation writes the L-1 ledger row via L-1's DAL, born `confirmed`,
 *      with the D-16 stamp COPIED from PB-2 M-6's `getLastTurnStamp()` read API
 *      (D-16(d): copied, never re-computed, never joined live — the DB trigger
 *      `trg_bmpl_freeze_confirmed` freezes it thereafter) and
 *      `created_from_channel='pariprashna'`.
 *
 * This module OWNS none of the ledger schema/transition logic — it calls L-1's
 * DAL (writer.ts) and reads PB-2 M-6's stamp API. It is the thin seam that
 * copies the stamp and maps the structured candidate onto L-1's create input.
 *
 * The DB calls default to the shared client but accept an injected
 * `LedgerExecutor` + stamp reader so the E2E test drives the REAL DAL against a
 * REAL throwaway Postgres (the PB-2 false-confidence-gate lesson — never a mock
 * of the confirm agreeing with itself).
 */

import { getLastTurnStamp, type TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { createLedgerRow, transitionLifecycle, type LedgerExecutor } from './writer'
import type { ConfidenceBand, LedgerRow, LedgerStamp } from './schema'
import type { StructuredPredictionCandidate } from './detector'

/**
 * Copy PB-2 M-6's read-API stamp (`TurnProvenanceStamp`) onto the ledger's
 * `LedgerStamp` shape. A pure FIELD COPY of exactly the five D-16 values — the
 * read side's `computed_at` is audit metadata, not one of the five copied
 * fields, so it is dropped. This is D-16(d) in code: copied, never referenced.
 */
export function toLedgerStamp(t: TurnProvenanceStamp): LedgerStamp {
  return {
    build_id: t.build_id,
    priors_version: t.priors_version,
    formula_versions: t.formula_versions,
    ranking_config: t.ranking_config,
    now_context_date: t.now_context_date,
  }
}

/** Injected dependencies (default to the real, shared surfaces). */
export interface ConfirmDeps {
  exec?: LedgerExecutor
  /** Reads the last turn's D-16 stamp (PB-2 M-6 getLastTurnStamp by default). */
  readStamp?: (conversationId: string) => Promise<TurnProvenanceStamp | null>
}

export interface ConfirmCandidateInput {
  chart_id: string
  conversation_id: string
  /** FK → the originating PB-2 `message_parts.id`. Null for a W-6 scripted claim. */
  message_part_id?: string | null
  candidate: StructuredPredictionCandidate
  /**
   * The Brier-ready confidence band committed at confirm time (§14.3: the confirm
   * UI elicits one via a slider that produces a numrange). REQUIRED — the ledger
   * confidence is always a band, never a point; a stated point only pre-positions
   * the slider (see the client `ConfidenceSlider`), the human still commits a band.
   */
  confidence: ConfidenceBand
  /** Optional human edits to the detected claim/domain/window/direction. */
  edits?: Partial<Pick<StructuredPredictionCandidate, 'claim_text' | 'domain' | 'direction' | 'window_start' | 'window_end'>>
}

/**
 * Confirm a candidate → a `confirmed` ledger row (the primary path). Reads the
 * conversation's last-turn D-16 stamp and COPIES it in. Throws if no stamp
 * exists (a real reading always has one — PB-2 M-6 writes it per assistant turn;
 * refusing to confirm without it is honest, not a silent zero-stamp row).
 */
export async function confirmCandidate(
  input: ConfirmCandidateInput,
  deps: ConfirmDeps = {},
): Promise<LedgerRow> {
  const readStamp = deps.readStamp ?? getLastTurnStamp
  const turnStamp = await readStamp(input.conversation_id)
  if (!turnStamp) {
    throw new Error(
      `confirmCandidate: no provenance stamp found for conversation ${input.conversation_id}; ` +
        `cannot confirm a claim without the D-16 stamp to copy (§14.3 / D-16(d))`,
    )
  }

  const c = input.candidate
  const claim_text = input.edits?.claim_text ?? c.claim_text
  const domain = input.edits?.domain ?? c.domain
  const direction = input.edits?.direction ?? c.direction
  const windowStart = input.edits?.window_start ?? c.window_start
  const windowEnd = input.edits?.window_end ?? c.window_end
  const window =
    windowStart && windowEnd ? { start: windowStart, end: windowEnd } : null

  return createLedgerRow(
    {
      chart_id: input.chart_id,
      message_part_id: input.message_part_id ?? null,
      claim_text,
      domain: domain ?? null,
      window,
      confidence: input.confidence,
      direction: direction ?? null,
      technique_refs: c.technique_refs,
      grounding_fact_ids: c.grounding_fact_ids,
      created_from_channel: 'pariprashna',
      initial_status: 'confirmed',
      stamp: toLedgerStamp(turnStamp),
    },
    deps.exec,
  )
}

export interface DismissCandidateInput {
  chart_id: string
  message_part_id?: string | null
  candidate: StructuredPredictionCandidate
  /** Why the human rejected it — persisted to feed detector-precision tuning
   *  (§14.3 "Dismissal-with-reason feeds detector precision"). REQUIRED. */
  reason: string
}

/**
 * Dismiss a candidate WITH REASON. The reason is persisted via L-1's DAL: a
 * `detected` row is created, then transitioned `detected → dismissed` carrying
 * `dismissed_reason` (a column L-1's schema already provides — verified, no gap).
 * No stamp is copied: a dismissed claim was never confirmed, so it holds no
 * historical-claim stamp. This keeps dismissal recall auditable (W-1) instead of
 * silently dropping the candidate.
 */
export async function dismissCandidate(
  input: DismissCandidateInput,
  deps: ConfirmDeps = {},
): Promise<LedgerRow> {
  const c = input.candidate
  const row = await createLedgerRow(
    {
      chart_id: input.chart_id,
      message_part_id: input.message_part_id ?? null,
      claim_text: c.claim_text,
      domain: c.domain ?? null,
      window: c.window_start && c.window_end ? { start: c.window_start, end: c.window_end } : null,
      direction: c.direction ?? null,
      technique_refs: c.technique_refs,
      grounding_fact_ids: c.grounding_fact_ids,
      created_from_channel: 'pariprashna',
      initial_status: 'detected',
    },
    deps.exec,
  )
  return transitionLifecycle(row.id, 'dismissed', { dismissed_reason: input.reason }, deps.exec)
}
