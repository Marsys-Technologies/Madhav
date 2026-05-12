import { describe, expect, it } from 'vitest'
import {
  serializeSSE,
  parseSSE,
  type ReasoningStepEvent,
  type ProvenanceEvent,
  type ContextUsageEvent,
  type CorrectionEvent,
  type SanskritTermsEvent,
} from '@/types/sse_events'

describe('sse_events — shape + serialization', () => {
  it('serializes and round-trips a reasoning_step event', () => {
    const ev: ReasoningStepEvent = {
      type: 'reasoning_step',
      phase: 'pipeline',
      text: 'Reading the question',
      timestamp: 1700000000000,
    }
    const wire = serializeSSE(ev)
    expect(wire).toContain('event: reasoning_step')
    expect(wire).toContain('"phase":"pipeline"')
    const parsed = parseSSE(wire)
    expect(parsed).toEqual(ev)
  })

  it('round-trips context_usage', () => {
    const ev: ContextUsageEvent = {
      type: 'context_usage',
      prior_turns_used: 1,
      mode: 'narrative_context',
      reason: 'follow-up about prior topic',
    }
    expect(parseSSE(serializeSSE(ev))).toEqual(ev)
  })

  it('round-trips correction', () => {
    const ev: CorrectionEvent = {
      type: 'correction',
      original_claim: 'Jupiter is in the 7th',
      corrected_claim: 'Jupiter is in the 5th',
      classical_source: 'FORENSIC chart',
    }
    expect(parseSSE(serializeSSE(ev))).toEqual(ev)
  })

  it('round-trips sanskrit_terms', () => {
    const ev: SanskritTermsEvent = {
      type: 'sanskrit_terms',
      terms: [
        { term: 'Vimshottari', definition: '120-year dasha system', transliteration: 'viṃśottarī' },
      ],
    }
    expect(parseSSE(serializeSSE(ev))).toEqual(ev)
  })

  it('round-trips provenance', () => {
    const ev: ProvenanceEvent = {
      type: 'provenance',
      models: [{ stage: 'planner', role: 'Question reader', model_id: 'gemini-2.5-pro', latency_ms: 1200 }],
      sources: {
        astrological: [{ asset: 'MSR', label: 'Astrological Signals', items: [{ id: 'SIG.MSR.142', label: 'Saturn–Moon affliction' }] }],
        technical: [{ kind: 'latency', label: 'Synthesis', value: '5.2s' }],
      },
    }
    expect(parseSSE(serializeSSE(ev))).toEqual(ev)
  })

  it('parseSSE returns null on bad input', () => {
    expect(parseSSE('garbage')).toBeNull()
  })
})
