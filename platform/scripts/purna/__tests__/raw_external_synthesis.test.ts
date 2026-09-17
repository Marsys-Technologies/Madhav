import { describe, expect, it, vi } from 'vitest'
import { stableFingerprint } from '../../../src/lib/retrieval/registry/knowledge/stable'
import type { InquiryContract } from '../../../src/lib/vidhi/inquiry'

const mocks = vi.hoisted(() => ({
  snapshot: vi.fn(),
  header: vi.fn(),
  synthesize: vi.fn(),
  accountability: vi.fn(),
}))

vi.mock('../../../src/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: mocks.snapshot,
}))
vi.mock('../../../src/lib/retrieval/chart_header', () => ({ fetchChartHeaderResolution: mocks.header }))
vi.mock('../../../src/lib/pipeline/prashna_ask_synthesis', () => ({ synthesizeReading: mocks.synthesize }))
vi.mock('../../../src/lib/vidhi/inquiry', () => ({ buildStructuredResponseAccountability: mocks.accountability }))

import { synthesizeRawLifecycleEvidence } from '../raw_external_synthesis'

const rawPayload = { results: [{ house: 2, signal: 'strengthened' }] }
const contract = {
  contract_id: 'sha256:combined', semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
  chart_id: '11111111-1111-4111-8111-111111111111', question: 'What supports wealth?',
  scope_tuple: { intent: 'wealth_deepdive', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'near', intervention: 'none', entitlement: 'native' },
  capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
  plan_items: [{ item_id: 'item-001', obligation_ids: ['obl-001'], binding_id: 'registry:marsys://tool/L1/wealth', argument_resolution: { temporal_anchor_date: '2026-09-18' } }],
  obligations: [{ obligation_id: 'obl-001', evidence_refs: [`raw:${stableFingerprint(rawPayload)}`] }],
} as unknown as InquiryContract

describe('Pūrṇa raw external synthesis', () => {
  it('uses the receipt-hashed raw payload for synthesis and the accountability denominator', async () => {
    mocks.snapshot.mockReturnValue({ content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1' })
    mocks.header.mockResolvedValue({ header: { current_maha_antar: 'Mercury / Saturn' }, flags: [] })
    mocks.synthesize.mockResolvedValue({ reading: 'A grounded wealth reading.', model_id: 'model-1', judgment_flags: [] })
    const envelope = { accountability_version: 'inquiry-response-accountability-v1' }
    mocks.accountability.mockReturnValue(envelope)

    const result = await synthesizeRawLifecycleEvidence({
      test: { id: 'case-1', question: contract.question, scope_tuple: contract.scope_tuple, requiredDimensions: ['wealth'], expected: 'supported_complete' },
      inquiryId: 'inquiry-1', contract, evidencePayloads: [rawPayload],
    })

    expect(mocks.synthesize).toHaveBeenCalledWith(expect.objectContaining({
      evidence: [{ tool_name: 'marsys://tool/L1/wealth', bundle: rawPayload }],
      nowContextDate: '2026-09-18',
    }))
    expect(mocks.accountability).toHaveBeenCalledWith(contract, expect.objectContaining({
      response_text: 'A grounded wealth reading.', evidence_payloads: [rawPayload],
    }))
    expect(result).toEqual({ answer: 'A grounded wealth reading.', responseAccountability: envelope })
  })
})
