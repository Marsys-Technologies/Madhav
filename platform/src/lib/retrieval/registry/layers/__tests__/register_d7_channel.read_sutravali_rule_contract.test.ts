import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { clearRegistry, getCapability } from '../../index'
import { registerD7ChannelCapabilities } from '../register_d7_channel'

const mockQuery = vi.mocked(query)
const RULE_ID = 'a8c5fa0a-6105-4e50-83de-7e88f7d235ad'

function readRuleCapability() {
  return getCapability('marsys://tool/L0/read_sutravali_rule')!
}

describe('read_sutravali_rule direct SQL contract', () => {
  beforeEach(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
    mockQuery.mockReset()
  })

  it('requires rule_id before querying', async () => {
    const result = await readRuleCapability().handler({})

    expect(mockQuery).not.toHaveBeenCalled()
    expect(result).toEqual({
      content: { error: 'rule_id is required' },
      is_error: true,
    })
  })

  it('uses the public router projection and UUID-text equality, then maps its response shape', async () => {
    mockQuery.mockResolvedValue({
      rows: [{
        rule_id: RULE_ID,
        text_id: 'bphs',
        verse_ref: '24.17',
        antecedent_jsonb: { planet: 'SAT' },
        predicate_jsonb: { relation: 'occupies', house: '10' },
        prediction_jsonb: { outcome: 'career_responsibility' },
        confidence: '0.875',
        extracted_by: 'sutravali-import-v1',
      }],
    } as never)

    const result = await readRuleCapability().handler({ rule_id: RULE_ID })

    expect(mockQuery).toHaveBeenCalledTimes(1)
    const [sql, values] = mockQuery.mock.calls[0]!
    expect((sql as string).replace(/\s+/g, ' ').trim()).toBe(
      'SELECT r.rule_id, r.text_id, r.verse_ref, r.antecedent_jsonb, r.predicate_jsonb, r.prediction_jsonb, r.confidence, r.extracted_by FROM sutravali_rules r WHERE r.rule_id::text = $1',
    )
    expect(values).toEqual([RULE_ID])
    expect(result).toEqual({
      content: {
        rule: {
          rule_id: RULE_ID,
          text_id: 'bphs',
          verse_ref: '24.17',
          antecedent: { planet: 'SAT' },
          predicate: { relation: 'occupies', house: '10' },
          prediction: { outcome: 'career_responsibility' },
          confidence: 0.875,
          extracted_by: 'sutravali-import-v1',
        },
      },
      is_error: false,
    })
  })

  it('keeps the public not-found error and adds a machine-readable empty_reason', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)

    const result = await readRuleCapability().handler({ rule_id: RULE_ID })

    expect(result).toEqual({
      content: {
        error: `Rule '${RULE_ID}' not found`,
        empty_reason: 'rule_id_not_found',
        rule_id: RULE_ID,
      },
      is_error: true,
    })
  })

  it('declares the density_contract the handler honours (SS N-268, §N.6 iv)', async () => {
    const cap = readRuleCapability()
    expect(cap.density_contract).toEqual({ paginated: false, facets: [], empty_reason: true })

    // the numeric confidence score (not a declared tier, N-211 E5): the served select reads it and the response carries it per rule.
    mockQuery.mockResolvedValue({
      rows: [{
        rule_id: RULE_ID, text_id: 'bphs', verse_ref: '24.17',
        antecedent_jsonb: {}, predicate_jsonb: {}, prediction_jsonb: {},
        confidence: '0.6', extracted_by: 'python_regex_v2',
      }],
    } as never)
    const hit = await cap.handler({ rule_id: RULE_ID })
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).toMatch(/r\.confidence/)
    expect((hit.content as { rule: { confidence: number } }).rule.confidence).toBe(0.6)

    // empty_reason: true is backed by a real code path on the empty result.
    mockQuery.mockResolvedValue({ rows: [] } as never)
    const miss = await cap.handler({ rule_id: RULE_ID })
    expect((miss.content as { empty_reason?: string }).empty_reason).toBe('rule_id_not_found')
  })

  it('returns database failures as handler errors', async () => {
    mockQuery.mockRejectedValue(new Error('database unavailable'))

    const result = await readRuleCapability().handler({ rule_id: RULE_ID })

    expect(result).toEqual({
      content: { error: 'Error: database unavailable' },
      is_error: true,
    })
  })
})
