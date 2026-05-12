import { describe, expect, it } from 'vitest'
import { narratePipelineStep, narrateTraceStep } from '@/lib/consume/pipeline_event_translator'
import {
  PIPELINE_STEP_NARRATION,
  containsBannedToken,
} from '@/lib/jyotish/domain_labels'

describe('pipeline_event_translator', () => {
  it('every keyed step narrates without leaking internal tokens', () => {
    for (const step of Object.keys(PIPELINE_STEP_NARRATION)) {
      const out = narratePipelineStep(step)
      expect(out.length, step).toBeGreaterThan(0)
      expect(containsBannedToken(out), `${step} leaks: ${out}`).toBeNull()
    }
  })

  it('appends a count when provided', () => {
    const out = narratePipelineStep('vector_search', { count: 3 })
    expect(out).toContain('Searching classical sources')
    expect(out).toContain('(3 so far)')
  })

  it('appends latency only above 1500 ms', () => {
    expect(narratePipelineStep('synthesis', { latencyMs: 500 })).toBe('Reasoning through the question')
    expect(narratePipelineStep('synthesis', { latencyMs: 4321 })).toMatch(/4\.3s/)
  })

  it('unknown step falls back to titlecased label', () => {
    expect(narratePipelineStep('new_phase_one')).toBe('New Phase One')
  })

  it('narrateTraceStep reads chunks_returned + latency', () => {
    const out = narrateTraceStep({
      step_name: 'vector_search',
      status: 'done',
      latency_ms: 2100,
      data_summary: { chunks_returned: 5 },
    })
    expect(out).toContain('(5 so far)')
    expect(out).toContain('2.1s')
  })
})
