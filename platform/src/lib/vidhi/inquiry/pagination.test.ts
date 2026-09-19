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

function judgmentBinding(): SemanticCapabilityBinding {
  return binding({
    binding_id: 'registry:marsys://tool/L-JUDGMENT/judgment_query',
    capability_uri: 'marsys://tool/L-JUDGMENT/judgment_query',
    pagination: 'none',
    pagination_verified: null,
    result_collection_verified: false,
    pagination_contract: undefined,
    non_paginated_closure: {
      closure_version: 'judgment-reading-checklist-v2',
      checklist_path: 'reading_checklist',
      checklist_contract_id: 'judgment-reading-checklist-v2',
      required_units: [
        'bhava_bhavesha_from_lagna', 'bhava_bhavesha_from_chandra', 'karakas',
        'operative_varga', 'corroborating_vargas', 'ashtakavarga', 'special_lagnas',
        'sensitive_degree_firings', 'kp_cusp_chain', 'yogi_avayogi', 'bearing_yogas',
        'bearing_afflictions', 'notably_absent_yogas', 'dasha_levels', 'gochara_sweep', 'tajaka',
      ],
      material_trim_paths: ['budget_kb_applied', 'trim_report', 'material_trimmed', 'response_trimmed', 'truncated'],
      source_ref: 'test:judgment-reading-checklist',
    },
  } as Partial<SemanticCapabilityBinding>)
}

function classicalBinding(): SemanticCapabilityBinding {
  return binding({
    binding_id: 'registry:marsys://tool/L0/query_classical_texts',
    capability_uri: 'marsys://tool/L0/query_classical_texts',
    pagination: 'cursor',
    pagination_contract: {
      request_position_path: 'page_cursor', request_limit_path: 'limit', effective_maximum: 200,
      result_collection_path: 'content.citations', next_path: 'content.next_page_cursor',
      more_available_path: 'content.more_available', deterministic_order: ['text_id ASC', 'id ASC'],
      material_trim_paths: ['budget_kb_applied', 'trim_report', 'response_trimmed'],
    },
  } as Partial<SemanticCapabilityBinding>)
}

const completeJudgmentChecklist = {
  contract_id: 'judgment-reading-checklist-v2',
  units: [
    'bhava_bhavesha_from_lagna', 'bhava_bhavesha_from_chandra', 'karakas',
    'operative_varga', 'corroborating_vargas', 'ashtakavarga', 'special_lagnas',
    'sensitive_degree_firings', 'kp_cusp_chain', 'yogi_avayogi', 'bearing_yogas',
    'bearing_afflictions', 'notably_absent_yogas', 'dasha_levels', 'gochara_sweep', 'tajaka',
  ].map(unit => ({ unit, state: 'served' })),
  exhaustive: true,
  non_exhaustive: false,
  units_served: 16,
  units_total: 16,
  units_unserved: [],
}

describe('inquiry pagination receipts', () => {
  it('advances a verified offset from server-observed more_available', () => {
    expect(deriveInquiryPaginationReceipt(binding(), { results: [{ content: { rows: [1], more_available: true } }] }, { offset: 50, limit: 25 }))
      .toEqual({ semantics: 'offset', exhausted: false, next: 75 })
  })

  it('consumes the reviewed build-pinned dasha cursor rather than replaying a caller offset', () => {
    const serverContinued = generatedCapabilityKnowledge.scus
      .find((scu) => scu.scu_id === 'scu.catalog.get_dashas')!
      .bindings.find((candidate) => candidate.binding_id === 'registry:marsys://tool/L1/get_dashas') as SemanticCapabilityBinding

    expect(serverContinued.pagination_contract).toMatchObject({
      request_position_path: 'page_cursor',
      request_limit_path: 'limit',
      result_collection_path: 'content.rows',
      more_available_path: 'content.more_available',
      next_path: 'content.next_page_cursor',
      deterministic_order: expect.arrayContaining(['dasha_row_id ASC']),
    })

    expect(deriveInquiryPaginationReceipt(
      serverContinued,
      { content: { rows: [{ dasha_row_id: 'a' }], more_available: true, next_page_cursor: 'opaque-page-2' } },
      { page_cursor: 'opaque-page-1', offset: -10, limit: Number.POSITIVE_INFINITY },
    )).toEqual({ semantics: 'cursor', exhausted: false, next: 'opaque-page-2' })
  })

  it('extracts and continues the reviewed classical citation cursor byte-for-byte', () => {
    const raw = { content: { citations: [{ citation_ref: 'BPHS:1.1' }], more_available: true, next_page_cursor: 'opaque.classical.page.2' } }
    expect(extractInquirySemanticFindings(classicalBinding(), raw)).toMatchObject({
      mode: 'reviewed_collection', result_collection_path: 'content.citations',
      rows: [{ citation_ref: 'BPHS:1.1' }],
    })
    expect(deriveInquiryPaginationReceipt(classicalBinding(), raw, { page_cursor: 'opaque.classical.page.1', limit: 5 }))
      .toEqual({ semantics: 'cursor', exhausted: false, next: 'opaque.classical.page.2' })
  })

  it.each([
    ['citation trim report', { content: { citations: [{ citation_ref: 'BPHS:1.1' }], next_page_cursor: null, more_available: false }, trim_report: [{ path: 'content.citations', removed_count: 2 }] }],
    ['applied response budget', { content: { citations: [{ citation_ref: 'BPHS:1.1' }], next_page_cursor: null, more_available: false }, budget_kb_applied: 20 }],
  ])('keeps a terminal classical response open after %s', (_label, raw) => {
    expect(deriveInquiryPaginationReceipt(classicalBinding(), raw, { limit: 5 }))
      .toEqual({ semantics: 'cursor', exhausted: false, next: 'unproven' })
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

  it('treats the uncapped, deterministic contradiction collection as complete without promoting supplemental legs', () => {
    const contradictions = generatedCapabilityKnowledge.scus
      .find((scu) => scu.scu_id === 'scu.catalog.query_contradictions')!
      .bindings.find((candidate) => candidate.binding_id === 'registry:marsys://tool/L2/query_contradictions') as SemanticCapabilityBinding
    const raw = { content: { contradictions: [{ contradiction_id: 'c-1' }], discoveries: [{ discovery_id: 'd-1' }], anomalies: [{ anomaly_id: 'a-1' }] } }

    expect(contradictions).toMatchObject({
      pagination: 'none',
      result_collection_verified: true,
      pagination_contract: {
        result_collection_path: 'content.contradictions',
        deterministic_order: ['combined_salience DESC NULLS LAST', 'contradiction_id ASC'],
      },
    })
    expect(extractInquirySemanticFindings(contradictions, raw)).toEqual({
      mode: 'reviewed_collection',
      result_collection_path: 'content.contradictions',
      rows: [{ contradiction_id: 'c-1' }],
    })
    expect(deriveInquiryPaginationReceipt(contradictions, raw, {})).toEqual({ semantics: 'none', exhausted: true, next: null })
  })

  it('closes judgment only for a structurally complete untrimmed reading checklist', () => {
    expect(deriveInquiryPaginationReceipt(
      judgmentBinding(),
      { content: { reading_checklist: completeJudgmentChecklist } },
      {},
    )).toEqual({ semantics: 'none', exhausted: true, next: null })
  })

  it.each([
    ['missing checklist', { content: {} }],
    ['malformed checklist', { content: { reading_checklist: { ...completeJudgmentChecklist, units_served: '12' } } }],
    ['wrong checklist contract', { content: { reading_checklist: { ...completeJudgmentChecklist, contract_id: 'judgment-reading-checklist-v1' } } }],
    ['missing mandatory unit', { content: { reading_checklist: { ...completeJudgmentChecklist, units: completeJudgmentChecklist.units.slice(0, -1), units_served: 15, units_total: 15 } } }],
    ['duplicate mandatory unit', { content: { reading_checklist: { ...completeJudgmentChecklist, units: [...completeJudgmentChecklist.units.slice(0, -1), completeJudgmentChecklist.units[0]] } } }],
    ['unsettled mandatory unit', { content: { reading_checklist: { ...completeJudgmentChecklist, units: completeJudgmentChecklist.units.map(unit => unit.unit === 'notably_absent_yogas' ? { ...unit, state: 'not_computed' } : unit) } } }],
    ['contradictory counts', { content: { reading_checklist: { ...completeJudgmentChecklist, units_served: 11 } } }],
    ['non-exhaustive marker', { content: { reading_checklist: { ...completeJudgmentChecklist, non_exhaustive: 'salience_sampled' } } }],
    ['unserved units', { content: { reading_checklist: { ...completeJudgmentChecklist, exhaustive: false, units_served: 11, units_unserved: ['tajaka'] } } }],
    ['applied byte budget', { content: { reading_checklist: completeJudgmentChecklist, budget_kb_applied: 12, trim_report: null } }],
    ['outer-envelope applied byte budget', { budget_kb_applied: 12, trim_report: null, content: { reading_checklist: completeJudgmentChecklist } }],
    ['material trim report', { content: { reading_checklist: completeJudgmentChecklist, trim_report: [{ path: 'checklist.bearing_yogas', kept_count: 3 }] } }],
    ['material trim indicator', { content: { reading_checklist: completeJudgmentChecklist, response_trimmed: true } }],
  ])('keeps judgment open for %s', (_label, raw) => {
    expect(deriveInquiryPaginationReceipt(judgmentBinding(), raw, {}))
      .toEqual({ semantics: 'none', exhausted: false, next: 'unproven' })
  })

  it('preserves pagination:none closure for ordinary bindings without a typed closure contract', () => {
    expect(deriveInquiryPaginationReceipt(
      binding({ pagination: 'none', pagination_verified: null, pagination_contract: undefined }),
      { content: {} },
      {},
    )).toEqual({ semantics: 'none', exhausted: true, next: null })
  })
})
