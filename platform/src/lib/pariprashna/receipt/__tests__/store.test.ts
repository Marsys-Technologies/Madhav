/**
 * receipt/store.test.ts — lane G3-A (PPR-01).
 *
 * `withAcharyaReadingReceipt` is pure (no DB) and is tested here directly.
 * `getLastTurnReceipt` / `getTurnReceiptByMessageId` need a live
 * `conversation_messages` row and are exercised by a DB-integration test
 * only where the codebase already has that harness (see
 * `store/__tests__/store.db.test.ts` for the pattern this lane did not
 * duplicate — a residual disclosed in the G3-A report).
 */
import { describe, it, expect } from 'vitest'

import { withAcharyaReadingReceipt } from '../store'
import { assembleAcharyaReadingReceipt } from '../assemble'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

function receiptFixture() {
  const provenanceStamp: TurnProvenanceStamp = {
    build_id: null,
    priors_version: 'p1',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-08-19',
    computed_at: '2026-08-19T00:00:00.000Z',
  }
  return assembleAcharyaReadingReceipt({
    turnId: 't1',
    conversationId: 'c1',
    chartId: 'chart1',
    plan: { domains: [] },
    committedBlocks: [],
    accumulatedText: '',
    citationsFound: [],
    citationRewriteEnabled: false,
    resolvedCitations: [],
    citationHallucinationCount: 0,
    completenessReceipt: null,
    safetyDecision: undefined,
    validToolResults: [],
    provenanceStamp,
  })
}

describe('withAcharyaReadingReceipt', () => {
  it('attaches the receipt as an additive sub-object, never replacing existing metadata keys', () => {
    const metadata = { custom: { model: 'x' }, provenance_stamp: { build_id: 'b1' } }
    const receipt = receiptFixture()
    const merged = withAcharyaReadingReceipt(metadata, receipt)
    expect(merged.custom).toEqual({ model: 'x' })
    expect(merged.provenance_stamp).toEqual({ build_id: 'b1' })
    expect(merged.acharya_reading_receipt).toEqual(receipt)
  })

  it('does not mutate the input metadata object', () => {
    const metadata = { custom: { model: 'x' } }
    withAcharyaReadingReceipt(metadata, receiptFixture())
    expect(Object.keys(metadata)).toEqual(['custom'])
  })
})
