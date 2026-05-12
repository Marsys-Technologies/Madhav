import { describe, it, expect } from 'vitest'

import { buildJudgePrompt, parseJudgeResponse } from '../judge_prompt'

describe('buildJudgePrompt', () => {
  it('includes the original query text', () => {
    const p = buildJudgePrompt({
      query_text: 'Will my career take off?',
      query_class: 'predictive',
      plan_type: 'time_indexed_prediction',
      tools_selected: ['msr_sql', 'cgm_graph_walk'],
      planner_confidence: 0.78,
    })
    expect(p).toContain('Will my career take off?')
    expect(p).toContain('predictive')
    expect(p).toContain('msr_sql, cgm_graph_walk')
  })

  it('renders "(none)" when no tools selected', () => {
    const p = buildJudgePrompt({
      query_text: 'Q',
      query_class: 'factual',
      plan_type: 'single_answer',
      tools_selected: [],
      planner_confidence: null,
    })
    expect(p).toContain('tools_selected: (none)')
  })
})

describe('parseJudgeResponse', () => {
  it('parses a clean JSON response', () => {
    const v = parseJudgeResponse('{"verdict": "correct", "reasoning": "matches rubric 1+3"}')
    expect(v).toEqual({ verdict: 'correct', reasoning: 'matches rubric 1+3' })
  })

  it('extracts JSON from prose-wrapped output', () => {
    const v = parseJudgeResponse(
      'Here is the verdict:\n{"verdict":"wrong","reasoning":"missing L2.5 tool for holistic query"}\nDone.'
    )
    expect(v?.verdict).toBe('wrong')
  })

  it('returns null on missing JSON object', () => {
    expect(parseJudgeResponse('I think this is correct.')).toBeNull()
  })

  it('returns null on malformed JSON', () => {
    expect(parseJudgeResponse('{verdict: correct}')).toBeNull()
  })

  it('returns null on unknown verdict value', () => {
    expect(parseJudgeResponse('{"verdict":"maybe","reasoning":"x"}')).toBeNull()
  })

  it('coerces missing reasoning to empty string', () => {
    expect(parseJudgeResponse('{"verdict":"correct"}')).toEqual({
      verdict: 'correct',
      reasoning: '',
    })
  })
})
