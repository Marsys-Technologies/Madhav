/**
 * pariprashna/corpus/adapters/probe_output_adapter.ts — lane P2-N (G3-F).
 *
 * `runner.ts`'s own docblock names the exact gap this module closes: the
 * corpus runner "does NOT itself talk to the deployed route... several
 * dimensions need a live receipt this lane has no route to produce." That
 * route already exists, just unconnected: `scripts/probe/ask.ts` (a
 * proven, existing standing probe — see its own docblock) drives the
 * deployed web door end-to-end and captures every SSE event, including a
 * `receipt.define` event carrying the turn's REAL, server-assembled
 * `AcharyaReadingReceipt` verbatim (confirmed live, 2026-08-28, this
 * session — see `probe_output_adapter.test.ts`'s fixture, a genuine
 * captured turn).
 *
 * This module does NOT re-implement auth, SSE consumption, or any network
 * call — it is a pure function over an already-written probe output record
 * (`scripts/probe/out/<turnId>.json`'s shape), turning it into a
 * `TurnObservation` the existing `runCorpus`/`scoreAllDimensions` machinery
 * can already consume unchanged. Driving `probe/ask.ts` itself (auth,
 * network, one call per fixture) is left to a caller script — this module
 * is intentionally the SAFE, side-effect-free half of that pipeline.
 *
 * §N.8 discipline: a missing or schema-invalid `receipt.define` event
 * yields `receipt: null` — the SAME "no real source ran" state
 * `runner.ts`'s docblock already anticipated — never a throw, never a
 * fabricated stand-in. `turnMetrics` is always `null` here: `probe/ask.ts`
 * does not currently capture a `TurnMetricsSnapshot`-shaped SSE event (no
 * equivalent exists in its event capture) — an honest, disclosed gap, not
 * a silent omission (see this module's own test file for the residual
 * note).
 */

import type { CorpusFixture, TurnObservation } from '../types'
import { AcharyaReadingReceiptSchema, type AcharyaReadingReceipt } from '@/lib/pariprashna/receipt/schema'

/** The subset of `probe/ask.ts`'s written-record shape this adapter reads. Loosely typed on purpose — it's parsing an external JSON file, not a compile-time-guaranteed shape. */
export interface ProbeOutputRecord {
  prose?: unknown
  events?: unknown
}

function extractReceipt(record: ProbeOutputRecord): AcharyaReadingReceipt | null {
  const events = Array.isArray(record.events) ? record.events : []
  const receiptEvent = events.find(
    (e): e is { type: string; raw: { receipt?: unknown } } =>
      typeof e === 'object' && e !== null && (e as { type?: unknown }).type === 'receipt.define',
  )
  if (!receiptEvent) return null

  const candidate = receiptEvent.raw?.receipt
  const parsed = AcharyaReadingReceiptSchema.safeParse(candidate)
  return parsed.success ? parsed.data : null
}

/**
 * Builds a `TurnObservation` from an already-written `probe/ask.ts` output
 * record. Pure, synchronous, no I/O — the caller is responsible for having
 * already run the probe and read its output file.
 */
export function turnObservationFromProbeOutput(record: ProbeOutputRecord, fixture: CorpusFixture): TurnObservation {
  return {
    fixture,
    receipt: extractReceipt(record),
    turnMetrics: null,
    proseText: typeof record.prose === 'string' ? record.prose : null,
  }
}
