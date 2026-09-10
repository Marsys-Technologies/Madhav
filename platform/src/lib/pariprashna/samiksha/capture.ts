import 'server-only'
/**
 * SAMĪKṢĀ turn-commit capture — PB-3.1 gap **G1**: the prediction loop's entry point.
 *
 * Governing spec: `BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md` §Scope G1 + `REPORT_PB-3.md`'s P0:
 *
 *   > Mount `LogToSamiksha` on the live Paripraśna reading route, wired to the
 *   > already-persisted `prediction_candidate` message_part (which already carries the
 *   > `message_parts.id` the ledger's FK needs) — either as the in-stream one-tap affordance
 *   > L-2 built it to be, **or by having the route itself write a `detected` ledger row at
 *   > turn-commit so the review tab's `AwaitingSection` stops being structurally empty**.
 *   > Either path closes the same gap.
 *
 * This module is the SECOND path, chosen deliberately (see §Why this path, below). It is the
 * only writer of `detected` rows in the codebase, and it makes every already-built downstream
 * stage reachable for the first time:
 *
 *   reading → `detected` (HERE)
 *     → review tab `AwaitingSection` (`getReviewData`'s `awaiting`, already live-mounted)
 *     → human confirm with a probability (`confirmDetectedCandidate`) → `confirmed` → `open`
 *     → daily job closes the window → `window_closed`
 *     → human resolves → `outcome_recorded` / `unverifiable`
 *
 * ## Why this path and not the in-stream mount
 *
 * `LogToSamiksha.tsx` needs three things per candidate on the CLIENT: the structured
 * candidate, the conversation id, and the originating `message_parts.id`. The Paripraśna wire
 * protocol carries NONE of them — `route_writer_adapter.ts` documents the asymmetry explicitly:
 * "the real `PariprashnaEvent` union has no dedicated prediction-candidate event; the route
 * surfaces a candidate to the CLIENT only as a formatted `flag` info string". The part ids do
 * not even exist until `writeTurn` commits, which happens AFTER the stream's prose is done.
 * Mounting the in-stream affordance therefore requires a new protocol event + reducer + client
 * state — a wire-format change, not a mount. That is a separate lane; it is recorded as a
 * residual, not silently skipped.
 *
 * The turn-commit write, by contrast, needs no protocol change, runs where the part ids are
 * already in hand, and lands the candidate in the review tab's `AwaitingSection` — which is
 * already fully live-mounted (`/clients/[id]/samiksha` → `SamiksaReview` → `AwaitingSection`,
 * whose own docstring calls itself "the STANDALONE review-tab twin of the in-stream confirm
 * affordance"). It is the shorter, lower-risk path to the same live loop.
 *
 * ## W-1 (no auto-promotion) is preserved, not weakened
 *
 * §14.3 / W-1 forbids AUTO-PROMOTION — a machine writing a `confirmed` claim the human never
 * assented to. This module writes `detected`, which `schema.ts` defines as one of the two legal
 * birth states precisely for this purpose ("a `detected` shadow of a candidate part"). A
 * `detected` row is a queue entry awaiting a human, carries NO D-16 stamp (the stamp is copied
 * at the human's confirm, per D-16(d)), and cannot advance without the human act. Promotion
 * still happens only on the explicit tap. `confidence` is deliberately left NULL so the human
 * commits the Brier band themselves via the review tab's `ProbabilitySlider` — the heuristic
 * Stage-1 `score` is a detector-precision number, NOT a calibrated probability, and seeding a
 * band from it would be manufactured precision (§N.7 rule 6) and would suppress the slider.
 *
 * ## Pairing and idempotency
 *
 * Candidates are paired to their persisted parts by CLAIM TEXT (`body->>'claim'`, which
 * `predictionCandidatePartFromDetection` writes verbatim), consuming each matched part id at
 * most once — order-independent and duplicate-safe, unlike positional pairing. A candidate
 * whose part cannot be located is REPORTED as `unpaired` and NOT written: a ledger row with a
 * guessed/null FK would break the review tab's `resolveTurnAnchors` deep-link and is a worse
 * outcome than an honest omission.
 *
 * Re-committing the same turn is a no-op: any part that already has a ledger row is skipped, so
 * the capture never accretes duplicates (CLAUDE.md §N.3's rebuild-REPLACES spirit, applied to a
 * table whose rows carry human-owned lifecycle state and therefore must never be deleted).
 *
 * The executor is injectable (the same seam as the L-1 DAL) so this module is testable
 * end-to-end against a REAL migrated Postgres, not a mock of itself.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { enrichCandidate, type CitationRef } from './detector'
import type { PredictionCandidate as RawCandidate } from '@/lib/ppl/prediction_detector'
import { createLedgerRow, type LedgerExecutor } from './writer'
import { LEDGER_TABLE, type LedgerRow } from './schema'
import { configService } from '@/lib/config/index'
import { enqueueLedgerIntent } from '@/lib/pariprashna/arm3/outbox'

/**
 * NO-LEAKAGE arm-3's flag (G1-C · PPR-31 arm 3). ONE read site, so "the
 * in-process write path is unchanged while this is off" is enforced at one line
 * and a test can prove it at that one line — the same discipline
 * `consent/flag.ts` uses for G1-B.
 */
export const LEDGER_OUT_OF_PROCESS_FLAG = 'PARIPRASHNA_LEDGER_OUT_OF_PROCESS' as const

export function isLedgerOutOfProcessEnabled(): boolean {
  return configService.getFlag(LEDGER_OUT_OF_PROCESS_FLAG)
}

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

export interface CaptureDetectedInput {
  /** The chart the reading was conducted on. */
  chartId: string
  /**
   * `conversation_messages.id` of the assistant turn whose parts were JUST committed by
   * `writeTurn`. The `prediction_candidate` parts are read back from this id.
   */
  messageId: string
  /**
   * The Stage-1 raw detections the route already persisted as `prediction_candidate` parts —
   * i.e. exactly the array the route passed to `predictionCandidatePartFromDetection`.
   */
  candidates: readonly RawCandidate[]
  /** The turn's citation parts, for the §14.2 `grounding_fact_ids` map. */
  citations?: readonly CitationRef[]
  /**
   * The turn's genuine now-date (ISO yyyy-mm-dd) — the D-16 `now_context_date`. Relative
   * horizons ("in 2 years") resolve against THIS date, not against the capture's wall clock.
   */
  nowDate: string
}

export interface CaptureDetectedResult {
  /** The `detected` rows written by this call. Empty when arm-3 is on — see `enqueued`. */
  created: LedgerRow[]
  /** Candidates whose part already had a ledger row (idempotent re-commit). */
  skippedExisting: number
  /** Candidates whose persisted part could not be located — no row written, honestly reported. */
  unpaired: number
  /**
   * NO-LEAKAGE arm-3 (G1-C · PPR-31): candidates handed to the out-of-process
   * ledger writer via `pariprashna_ledger_outbox` instead of being INSERTed here.
   * Always 0 while `PARIPRASHNA_LEDGER_OUT_OF_PROCESS` is OFF (the default).
   *
   * A SEPARATE counter, not folded into `created`, on purpose: an enqueued intent
   * is not a ledger row. No row exists until the worker drains it, and reporting
   * a queued intent as `created` would be a status claiming more than its
   * detector measured (CLAUDE.md §N.8).
   */
  enqueued: number
}

interface PartRow {
  id: string
  claim: string | null
}

/**
 * Write one `detected` ledger row per newly-detected prediction candidate of a just-committed
 * assistant turn. Returns what it did; throws only on an unexpected DB fault (the route treats
 * a throw as non-fatal — a capture failure must never cost the reader their turn).
 */
export async function captureDetectedCandidates(
  input: CaptureDetectedInput,
  exec: LedgerExecutor = defaultExecutor,
): Promise<CaptureDetectedResult> {
  const empty: CaptureDetectedResult = {
    created: [],
    skippedExisting: 0,
    unpaired: 0,
    enqueued: 0,
  }
  if (input.candidates.length === 0) return empty

  // NO-LEAKAGE arm-3 (G1-C · PPR-31 arm 3). OFF by default, in which case this is
  // `false` before any other work happens and the path below is byte-for-byte the
  // in-process write it has always been. ON, the same candidates are queued for
  // the out-of-process writer instead — which is what makes the role cutover
  // survivable, since `role_web_serve` has no ledger INSERT at all after it.
  const viaOutbox = isLedgerOutOfProcessEnabled()

  // The persisted parts for this turn, in seq order.
  const { rows: parts } = await exec<PartRow>(
    `SELECT id, body->>'claim' AS claim
       FROM message_parts
      WHERE message_id = $1 AND kind = 'prediction_candidate'
      ORDER BY seq`,
    [input.messageId],
  )
  if (parts.length === 0) return { ...empty, unpaired: input.candidates.length }

  // claim text → FIFO queue of part ids (duplicate claim texts consume distinct parts).
  const byClaim = new Map<string, string[]>()
  for (const p of parts) {
    if (!p.claim) continue
    const q = byClaim.get(p.claim)
    if (q) q.push(p.id)
    else byClaim.set(p.claim, [p.id])
  }

  // Parts that ALREADY have a ledger row — the idempotency guard.
  const { rows: existing } = await exec<{ message_part_id: string }>(
    `SELECT DISTINCT message_part_id FROM ${LEDGER_TABLE} WHERE message_part_id = ANY($1::uuid[])`,
    [parts.map((p) => p.id)],
  )
  const alreadyLedgered = new Set(existing.map((r) => r.message_part_id))

  const citations = [...(input.citations ?? [])]
  const created: LedgerRow[] = []
  let skippedExisting = 0
  let unpaired = 0
  let enqueued = 0

  for (const raw of input.candidates) {
    const queue = byClaim.get(raw.text)
    const partId = queue?.shift()
    if (!partId) {
      unpaired += 1
      continue
    }
    if (alreadyLedgered.has(partId)) {
      skippedExisting += 1
      continue
    }

    const c = enrichCandidate(raw, { citations, nowDate: input.nowDate })
    const window =
      c.window_start && c.window_end ? { start: c.window_start, end: c.window_end } : null

    if (viaOutbox) {
      // arm-3: request the write, do not perform it. `confidence` is omitted here
      // for exactly the reason the header gives — the human commits the band at
      // confirm — and the outbox's `create_detected` payload schema does not even
      // accept one, so the queue cannot become a channel for writing a band no
      // human assented to.
      await enqueueLedgerIntent(
        {
          op: 'create_detected',
          payload: {
            chart_id: input.chartId,
            message_part_id: partId,
            claim_text: c.claim_text,
            domain: c.domain,
            window,
            direction: c.direction,
            technique_refs: c.technique_refs,
            grounding_fact_ids: c.grounding_fact_ids,
            created_from_channel: 'pariprashna',
          },
        },
        { query: exec },
      )
      enqueued += 1
      continue
    }

    const row = await createLedgerRow(
      {
        chart_id: input.chartId,
        message_part_id: partId,
        claim_text: c.claim_text,
        domain: c.domain,
        window,
        // confidence intentionally omitted — the human commits the band at confirm (see header).
        direction: c.direction,
        technique_refs: c.technique_refs,
        grounding_fact_ids: c.grounding_fact_ids,
        created_from_channel: 'pariprashna',
        initial_status: 'detected',
      },
      exec,
    )
    created.push(row)
  }

  return { created, skippedExisting, unpaired, enqueued }
}
