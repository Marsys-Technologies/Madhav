import { describe, expect, it } from 'vitest'
import { assertLiveEvidence, type AcceptanceCase } from '../collection_types'
import { collectManagedCase, collectRawCase, parsePortalSse } from '../channel_clients'

const test: AcceptanceCase = { id: 'wealth_mechanism_timing_contradiction', question: 'Explain wealth with supporting evidence.', scope_tuple: { intent: 'wealth_deepdive', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'near', intervention: 'none', entitlement: 'reference' }, requiredDimensions: ['wealth'], expected: 'supported_complete' }
const base = { test, expectedRevision: 'candidate-a', source: 'candidate' as const, chartId: '11111111-1111-4111-8111-111111111111' }

describe('Purna real three-door collector', () => {
  it('rejects a supposedly live answer with no real channel execution', () => {
    expect(() => assertLiveEvidence({ caseId: test.id, door: 'portal', inquiryId: 'test', expectedRevision: 'candidate-a', observedRevision: 'candidate-a', snapshotHash: 'snapshot-a', chartBuildId: 'build-a', answer: 'answer', receiptRefs: ['receipt-a'], materialFactIds: ['f1'], deliveredFactIds: ['f1'], unresolvedObligationIds: [], networkCallCount: 0, source: 'live', terminal: 'complete', diagnostic: null })).toThrow('PURNA_COLLECTION_NOT_LIVE_EVIDENCE')
  })
  it('keeps a truncated SSE stream incomplete', async () => {
    const stream = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new TextEncoder().encode('data: {"type":"block.commit","text":"partial"}\n\n')); controller.close() } })
    await expect(parsePortalSse(stream)).resolves.toMatchObject({ truncated: true, answer: 'partial' })
  })
  it('enforces a managed polling deadline', async () => {
    const row = await collectManagedCase({ ...base, maxPolls: 2, wait: async () => {}, invoker: { call: async (name) => name === 'prashna_ask' ? { job_id: 'job-1' } : { status: 'running' } } })
    expect(row.diagnostic).toBe('MANAGED_JOB_POLL_DEADLINE')
    expect(row.networkCallCount).toBe(3)
  })
  it('rejects raw lifecycle pagination that does not advance', async () => {
    const row = await collectRawCase({ ...base, maxActions: 3, invoker: { call: async (name) => name === 'inquiry_start' ? { inquiry_id: 'i-1', lifecycle_token: 'same', next_action_ids: ['item-001'] } : { lifecycle_token: 'same', next_action_ids: ['item-001'] } } })
    expect(row.diagnostic).toBe('RAW_PAGINATION_DID_NOT_ADVANCE')
  })
})
