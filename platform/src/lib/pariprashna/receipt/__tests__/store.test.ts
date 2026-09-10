/**
 * receipt/store.test.ts — lane G3-A (PPR-01), hardened P2-I (defect 1).
 *
 * `withAcharyaReadingReceipt` is pure (no DB) and is tested here directly.
 *
 * `getLastTurnReceipt` / `getTurnReceiptByMessageId` are exercised here with
 * `@/lib/db/client`'s `query` mocked (the same `vi.mock('@/lib/db/client', ...)`
 * pattern already used across the route-test suite, e.g.
 * `src/app/api/mcp/writes/__tests__/lel_event_record.test.ts`) rather than a
 * live DB-integration harness — this is a real red→green proof that the read
 * path REJECTS a shape-valid-but-incoherent row, not a tautology: the mock
 * returns a row a real query could return (a `metadata_json` value exactly
 * as it would come back from Postgres), and the two functions under test run
 * through their real DB-reading code path — only the `pg` call itself is
 * faked.
 *
 * Defect 1 (adversary finding): `getLastTurnReceipt`/`getTurnReceiptByMessageId`
 * used to run ONLY `AcharyaReadingReceiptSchema.safeParse` (shape check) on
 * the stored row — never `validateAcharyaReadingReceipt` (the §N.8
 * hash/coherence check the WRITE path already runs before persisting). A
 * receipt with a `receipt_hash` that does not match its own content, or a
 * `status: 'measured'` field missing its data, is shape-valid and used to
 * pass straight through to the caller as if it were trustworthy. The tests
 * below construct exactly such rows and prove the read path now returns
 * `null` for both.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

import { withAcharyaReadingReceipt, getLastTurnReceipt, getTurnReceiptByMessageId } from '../store'
import { assembleAcharyaReadingReceipt } from '../assemble'
import { validateAcharyaReadingReceipt } from '../validate'
import { computeReceiptHash } from '../hash'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

beforeEach(() => {
  mockQuery.mockReset()
})

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

describe('getLastTurnReceipt / getTurnReceiptByMessageId — read-path validation (defect 1)', () => {
  it('a genuine, coherent receipt round-trips through both read functions', async () => {
    const receipt = receiptFixture()
    // Sanity: the fixture is actually coherent (a real green baseline, not
    // just "the mock returns something").
    expect(validateAcharyaReadingReceipt(receipt).ok).toBe(true)

    mockQuery.mockResolvedValue({ rows: [{ metadata_json: { acharya_reading_receipt: receipt } }] })
    await expect(getLastTurnReceipt('conv-1')).resolves.toEqual(receipt)
    await expect(getTurnReceiptByMessageId('msg-1')).resolves.toEqual(receipt)
  })

  it('RED→GREEN: a receipt_hash that does not match its own content is shape-valid (passes safeParse) but is now rejected as null', async () => {
    const receipt = receiptFixture()
    // Tamper with a data field WITHOUT recomputing receipt_hash — exactly
    // the "hand-authored fake value with no traceable source" the adversary
    // demonstrated. `'0'.repeat(64)` is a plausible-looking but fabricated
    // hash, distinct from the real recomputed one.
    const tampered = { ...receipt, receipt_hash: '0'.repeat(64) }

    // Prove the RED half first: Zod's shape check alone has no opinion on
    // hash/content coherence and passes this straight through.
    const { AcharyaReadingReceiptSchema } = await import('../schema')
    const shapeCheck = AcharyaReadingReceiptSchema.safeParse(tampered)
    expect(shapeCheck.success).toBe(true) // shape-valid — this is the defect surface
    expect(validateAcharyaReadingReceipt(tampered).ok).toBe(false) // but incoherent

    // Now the GREEN half: the read path itself must reject it.
    mockQuery.mockResolvedValue({ rows: [{ metadata_json: { acharya_reading_receipt: tampered } }] })
    await expect(getLastTurnReceipt('conv-1')).resolves.toBeNull()
    await expect(getTurnReceiptByMessageId('msg-1')).resolves.toBeNull()
  })

  it('RED→GREEN: a status:"measured" field with a null data subfield — hash correctly recomputed over the incoherent content — is shape-valid but is now rejected as null', async () => {
    const receipt = receiptFixture()
    // The exact incoherent shape validate.ts's V2 check exists to catch:
    // coverage claims measured but floor_item_total is null. The hash is
    // recomputed correctly over this tampered content, so V1 (hash-matches-
    // content) alone would NOT catch this — isolating that V2 itself is what
    // catches it, independent of hash tampering.
    const { receipt_hash: _oldHash, ...contentWithoutHash } = receipt
    void _oldHash
    const tamperedContent = {
      ...contentWithoutHash,
      coverage: {
        status: 'measured' as const,
        served: 3,
        empty: 0,
        dark: 0,
        floor_item_total: null,
        channel: 'web' as const,
        channel_note: null,
        unavailable_reason: null,
      },
    }
    const tampered = { ...tamperedContent, receipt_hash: computeReceiptHash(tamperedContent) }

    const { AcharyaReadingReceiptSchema } = await import('../schema')
    const shapeCheck = AcharyaReadingReceiptSchema.safeParse(tampered)
    expect(shapeCheck.success).toBe(true) // shape-valid — floor_item_total is legitimately nullable
    const validation = validateAcharyaReadingReceipt(tampered)
    expect(validation.ok).toBe(false) // but incoherent (V2)
    expect(validation.violations.some((v) => v.includes('floor_item_total is null'))).toBe(true)
    expect(validation.violations.some((v) => v.includes('receipt_hash mismatch'))).toBe(false) // isolated: NOT a hash defect

    mockQuery.mockResolvedValue({ rows: [{ metadata_json: { acharya_reading_receipt: tampered } }] })
    await expect(getLastTurnReceipt('conv-1')).resolves.toBeNull()
    await expect(getTurnReceiptByMessageId('msg-1')).resolves.toBeNull()
  })

  it('a legacy/malformed row (fails shape check outright) still returns null', async () => {
    mockQuery.mockResolvedValue({ rows: [{ metadata_json: { acharya_reading_receipt: { bogus: true } } }] })
    await expect(getLastTurnReceipt('conv-1')).resolves.toBeNull()
  })

  it('no prior receipt-bearing row returns null', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    await expect(getLastTurnReceipt('conv-1')).resolves.toBeNull()
  })
})
