import { describe, expect, it } from 'vitest'
import type { SemanticCapabilityBinding } from '../../retrieval/registry/knowledge/types'
import { classifyInquiryResult, deriveInquiryPaginationReceipt } from './pagination'

function binding(overrides: Partial<SemanticCapabilityBinding> = {}): SemanticCapabilityBinding {
  return {
    binding_id: 'registry:test', kind: 'registry_capability', relation: 'primary', capability_uri: 'marsys://tool/L1/test',
    input_contract: {}, output_contract: {}, pagination: 'offset', pagination_verified: true,
    pagination_contract: { request_position_path: 'offset', request_limit_path: 'limit', effective_maximum: 50, result_collection_path: 'content.rows', more_available_path: 'content.more_available', deterministic_order: ['id'] },
    executable: true, ...overrides,
  }
}

describe('inquiry pagination receipts', () => {
  it('advances a verified offset from server-observed more_available', () => {
    expect(deriveInquiryPaginationReceipt(binding(), { results: [{ content: { rows: [1], more_available: true } }] }, { offset: 50, limit: 25 }))
      .toEqual({ semantics: 'offset', exhausted: false, next: 75 })
  })

  it('proves terminal exhaustion when the reviewed marker is false', () => {
    expect(deriveInquiryPaginationReceipt(binding(), { content: { rows: [], more_available: false } }, { offset: 75, limit: 25 }))
      .toEqual({ semantics: 'offset', exhausted: true, next: null })
  })

  it('reads reviewed collection and pagination paths through a ToolBundle JSON content string', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [], more_available: false }) }] }
    expect(classifyInquiryResult(binding(), raw)).toBe('empty')
    expect(deriveInquiryPaginationReceipt(binding(), raw, { offset: 0, limit: 50 }))
      .toEqual({ semantics: 'offset', exhausted: true, next: null })
  })

  it('does not invent a semantic empty for an unreviewed wrapped response', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [] }) }] }
    expect(classifyInquiryResult(binding({ pagination_verified: false }), raw)).toBe('served')
  })

  it('never fabricates exhaustion for an unreviewed capped route', () => {
    expect(deriveInquiryPaginationReceipt(binding({ pagination_verified: false }), { content: { rows: [1] } }, {}))
      .toEqual({ semantics: 'offset', exhausted: false, next: 'unproven' })
  })
})
