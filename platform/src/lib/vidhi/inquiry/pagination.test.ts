import { describe, expect, it } from 'vitest'
import type { SemanticCapabilityBinding } from '../../retrieval/registry/knowledge/types'
import { classifyInquiryResult, deriveInquiryPaginationReceipt, extractInquirySemanticFindings, semanticInquiryResultCount } from './pagination'
import generatedCapabilityKnowledge from '../../../generated/capability_knowledge.snapshot.json'

function binding(overrides: Partial<SemanticCapabilityBinding> = {}): SemanticCapabilityBinding {
  return {
    binding_id: 'registry:test', kind: 'registry_capability', relation: 'primary', capability_uri: 'marsys://tool/L1/test',
    input_contract: {}, output_contract: {}, pagination: 'offset', pagination_verified: true, result_collection_verified: true,
    pagination_contract: { request_position_path: 'offset', request_limit_path: 'limit', effective_maximum: 50, result_collection_path: 'content.rows', more_available_path: 'content.more_available', deterministic_order: ['id'] },
    executable: true, ...overrides,
  }
}

describe('inquiry pagination receipts', () => {
  it('advances a verified offset from server-observed more_available', () => {
    expect(deriveInquiryPaginationReceipt(binding(), { results: [{ content: { rows: [1], more_available: true } }] }, { offset: 50, limit: 25 }))
      .toEqual({ semantics: 'offset', exhausted: false, next: 75 })
  })

  it('prefers a reviewed server continuation over unnormalized caller pagination arguments', () => {
    const serverContinued = generatedCapabilityKnowledge.scus
      .find((scu) => scu.scu_id === 'scu.catalog.get_dashas')!
      .bindings.find((candidate) => candidate.binding_id === 'registry:marsys://tool/L1/get_dashas') as SemanticCapabilityBinding

    expect(serverContinued.pagination_contract).toMatchObject({
      request_position_path: 'offset',
      request_limit_path: 'limit',
      result_collection_path: 'content.rows',
      more_available_path: 'content.more_available',
      next_path: 'content.next_offset',
      deterministic_order: expect.arrayContaining(['dasha_row_id ASC']),
    })

    expect(deriveInquiryPaginationReceipt(
      serverContinued,
      { content: { rows: [{ dasha_row_id: 'a' }], more_available: true, next_offset: 2 } },
      { offset: -10, limit: Number.POSITIVE_INFINITY },
    )).toEqual({ semantics: 'offset', exhausted: false, next: 2 })
  })

  it('reads a reviewed nested request position and limit path', () => {
    const nested = binding({
      pagination_contract: {
        request_position_path: 'page.offset',
        request_limit_path: 'page.limit',
        effective_maximum: 50,
        result_collection_path: 'content.rows',
        more_available_path: 'content.more_available',
        deterministic_order: ['id'],
      },
    })
    expect(deriveInquiryPaginationReceipt(nested, { content: { rows: [1], more_available: true } }, { page: { offset: 40, limit: 10 } }))
      .toEqual({ semantics: 'offset', exhausted: false, next: 50 })
  })

  it('proves terminal exhaustion when the reviewed marker is false', () => {
    expect(deriveInquiryPaginationReceipt(binding(), { content: { rows: [], more_available: false } }, { offset: 75, limit: 25 }))
      .toEqual({ semantics: 'offset', exhausted: true, next: null })
  })

  it('reads reviewed collection and pagination paths through a ToolBundle JSON content string', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [], more_available: false }) }] }
    expect(classifyInquiryResult(binding(), raw)).toBe('empty')
    expect(semanticInquiryResultCount(binding(), raw)).toBe(0)
    expect(deriveInquiryPaginationReceipt(binding(), raw, { offset: 0, limit: 50 }))
      .toEqual({ semantics: 'offset', exhausted: true, next: null })
  })

  it('extracts each reviewed semantic row rather than treating the adapter envelope as one finding', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [{ id: 'a' }, { id: 'b' }], more_available: false }) }] }

    expect(extractInquirySemanticFindings(binding(), raw)).toEqual({
      mode: 'reviewed_collection',
      result_collection_path: 'content.rows',
      rows: [{ id: 'a' }, { id: 'b' }],
    })
  })

  it('keeps adapter items opaque when no result collection path was independently reviewed', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [{ id: 'a' }, { id: 'b' }] }) }] }

    expect(extractInquirySemanticFindings(binding({ result_collection_verified: false }), raw)).toEqual({
      mode: 'opaque_adapter_items',
      result_collection_path: null,
      rows: raw.results,
    })
  })

  it('does not invent a semantic empty for an unreviewed wrapped response', () => {
    const raw = { results: [{ content: JSON.stringify({ rows: [] }) }] }
    expect(classifyInquiryResult(binding({ pagination_verified: false, result_collection_verified: false }), raw)).toBe('served')
    expect(semanticInquiryResultCount(binding({ pagination_verified: false, result_collection_verified: false }), raw)).toBeNull()

    expect(classifyInquiryResult(binding({ pagination_verified: false, result_collection_verified: true }), raw)).toBe('empty')
  })

  it('classifies explicit nested failure envelopes as failed before counting wrapper rows', () => {
    const raw = { results: [{ content: JSON.stringify({ ok: false, error: 'sidecar unavailable', rows: [] }) }] }
    expect(classifyInquiryResult(binding(), raw)).toBe('failed')
  })

  it('never fabricates exhaustion for an unreviewed capped route', () => {
    expect(deriveInquiryPaginationReceipt(binding({ pagination_verified: false }), { content: { rows: [1] } }, {}))
      .toEqual({ semantics: 'offset', exhausted: false, next: 'unproven' })
  })
})
