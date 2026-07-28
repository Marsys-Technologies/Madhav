import { describe, it, expect } from 'vitest'
import {
  MESSAGE_PART_KINDS,
  MessagePartKindSchema,
  parsePartContent,
  BODY_SCHEMA_BY_KIND,
  CanonicalMessageSchema,
  MessagePartInputSchema,
} from '../schema'

describe('kind enum', () => {
  it('is the closed 7-member set that mirrors migration 467 CHECK', () => {
    expect([...MESSAGE_PART_KINDS]).toEqual([
      'text',
      'reasoning',
      'tool_call',
      'tool_result',
      'citation',
      'prediction_candidate',
      'attachment',
    ])
  })

  it('rejects a kind outside the enum', () => {
    expect(MessagePartKindSchema.safeParse('bogus').success).toBe(false)
    expect(MessagePartKindSchema.safeParse('flag').success).toBe(false) // flag is a wire event, NOT a part kind
  })

  it('has a body schema for every kind (no gaps)', () => {
    for (const k of MESSAGE_PART_KINDS) {
      expect(BODY_SCHEMA_BY_KIND[k]).toBeDefined()
    }
  })
})

describe('parsePartContent — per-kind body validation', () => {
  // One valid body per kind.
  const valid: Record<string, unknown> = {
    text: { text: 'hello', block_id: 'b1' },
    reasoning: { text: 'thinking', signature: 'sig', provider_opaque: 'opaque' },
    tool_call: { call_id: 'c1', tool_name: 'ganita_nakshatra_get', args: { planet: 'Moon' }, envelope_ref: 'env1' },
    tool_result: { call_id: 'c1', status: 'done', count: 3, ms: 120 },
    citation: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 's', reader_label: 'Moon', grade: 'primary' },
    prediction_candidate: { claim: 'career shift', window: '2027-Q1', confidence: 0.6, falsifier: 'no shift by 2027-06' },
    attachment: { media_type: 'image/png', url: 'x', filename: 'chart.png', bytes: 100 },
  }

  it.each(MESSAGE_PART_KINDS)('accepts a valid %s body and narrows kind', (kind) => {
    const parsed = parsePartContent(kind, valid[kind])
    expect(parsed.kind).toBe(kind)
  })

  it('rejects an invalid kind literal', () => {
    expect(() => parsePartContent('bogus', { text: 'x' })).toThrow()
  })

  it('rejects a body missing a required field', () => {
    expect(() => parsePartContent('tool_call', { tool_name: 'x', args: {} })).toThrow() // no call_id
    expect(() => parsePartContent('citation', { index: 1, signal_id: 's' })).toThrow() // no layer/snippet
    expect(() => parsePartContent('prediction_candidate', { window: 'x' })).toThrow() // no claim
  })

  it('rejects unknown extra fields (strict bodies)', () => {
    expect(() => parsePartContent('text', { text: 'x', sneaky: 1 })).toThrow()
  })

  it('rejects tool_result with a non-terminal status', () => {
    expect(() => parsePartContent('tool_result', { call_id: 'c1', status: 'running' })).toThrow()
  })

  it('rejects prediction_candidate confidence outside [0,1]', () => {
    expect(() => parsePartContent('prediction_candidate', { claim: 'x', confidence: 1.5 })).toThrow()
  })

  it('requires tool_name to be present (canonical-name discipline is caller-side, presence is schema-side)', () => {
    expect(() => parsePartContent('tool_call', { call_id: 'c1', args: {} })).toThrow()
  })
})

describe('CanonicalMessageSchema', () => {
  const base = {
    id: '11111111-1111-1111-1111-111111111111',
    conversation_id: '22222222-2222-2222-2222-222222222222',
    role: 'assistant',
    schema_version: 1,
    model_id: 'claude-opus-4-8[1m]',
    provider: 'anthropic',
  }

  it('accepts a well-formed canonical message', () => {
    expect(CanonicalMessageSchema.safeParse(base).success).toBe(true)
  })

  it('rejects a non-uuid id', () => {
    expect(CanonicalMessageSchema.safeParse({ ...base, id: 'not-a-uuid' }).success).toBe(false)
  })

  it('rejects a role outside user|assistant|tool', () => {
    expect(CanonicalMessageSchema.safeParse({ ...base, role: 'system' }).success).toBe(false)
  })

  it('rejects a non-positive schema_version', () => {
    expect(CanonicalMessageSchema.safeParse({ ...base, schema_version: 0 }).success).toBe(false)
  })
})

describe('MessagePartInputSchema', () => {
  it('accepts a well-formed input', () => {
    expect(
      MessagePartInputSchema.safeParse({ seq: 0, kind: 'text', body: { text: 'x' }, model_visible: true }).success,
    ).toBe(true)
  })

  it('rejects a negative seq', () => {
    expect(
      MessagePartInputSchema.safeParse({ seq: -1, kind: 'text', body: { text: 'x' }, model_visible: true }).success,
    ).toBe(false)
  })

  it('rejects a missing model_visible', () => {
    expect(MessagePartInputSchema.safeParse({ seq: 0, kind: 'text', body: { text: 'x' } }).success).toBe(false)
  })
})
