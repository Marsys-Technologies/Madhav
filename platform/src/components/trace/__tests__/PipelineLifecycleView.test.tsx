import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { PipelineLifecycleView } from '../PipelineLifecycleView'
import { ToolCoverageMatrix } from '../ToolCoverageMatrix'
import type { TraceStep } from '@/lib/trace/types'

const baseStep = (overrides: Partial<TraceStep>): TraceStep => ({
  query_id: 'q1',
  step_seq: 0,
  step_name: 'classify',
  step_type: 'deterministic',
  layer: 'system',
  status: 'done',
  latency_ms: 10,
  data_summary: {},
  payload: {},
  started_at: new Date().toISOString(),
  ended_at: new Date().toISOString(),
  ...overrides,
} as TraceStep)

describe('PipelineLifecycleView', () => {
  it('renders without throwing on empty steps', () => {
    expect(() =>
      render(<PipelineLifecycleView steps={[]} manifestTools={[]} />),
    ).not.toThrow()
  })

  it('renders all five stage headings (Classify, Plan, Retrieve, Assemble, Synthesize)', () => {
    const { container } = render(
      <PipelineLifecycleView steps={[]} manifestTools={[]} />,
    )
    const text = container.textContent ?? ''
    expect(text).toMatch(/Classify/i)
    expect(text).toMatch(/Plan/i)
    expect(text).toMatch(/Retrieve/i)
    expect(text).toMatch(/Assemble/i)
    expect(text).toMatch(/Synthesize/i)
  })

  it('surfaces planned tool names from plan-step tool_calls', () => {
    const planStep = baseStep({
      step_seq: 1,
      step_name: 'plan',
      step_type: 'llm',
      payload: {
        tool_calls: [{ tool_name: 'msr_sql' }, { tool_name: 'temporal' }],
      },
    } as Partial<TraceStep>)
    const { container } = render(
      <PipelineLifecycleView steps={[planStep]} manifestTools={['msr_sql', 'temporal']} />,
    )
    expect(container.textContent ?? '').toContain('msr_sql')
  })

  it('shows skipped tools (in manifest but not planned)', () => {
    const planStep = baseStep({
      step_seq: 1,
      step_name: 'plan',
      step_type: 'llm',
      payload: { tool_calls: [{ tool_name: 'msr_sql' }] },
    } as Partial<TraceStep>)
    const { container } = render(
      <PipelineLifecycleView
        steps={[planStep]}
        manifestTools={['msr_sql', 'vector_search']}
      />,
    )
    expect(container.textContent ?? '').toContain('vector_search')
  })

  it('renders the assemble short-circuit message when payload says so', () => {
    const assemble = baseStep({
      step_seq: 4,
      step_name: 'context_assembly',
      data_summary: { short_circuited: true, total_token_estimate: 1500, threshold: 2000 },
    } as Partial<TraceStep>)
    const { container } = render(
      <PipelineLifecycleView steps={[assemble]} manifestTools={[]} />,
    )
    expect(container.textContent ?? '').toMatch(/Skipped|threshold/i)
  })
})

describe('ToolCoverageMatrix', () => {
  const ALL_RETRIEVAL_TOOLS = [
    'msr_sql',
    'vector_search',
    'cgm_graph_walk',
    'temporal',
    'pattern_register',
  ]

  it('renders one chip per manifest tool', () => {
    const { container } = render(
      <ToolCoverageMatrix
        manifestTools={ALL_RETRIEVAL_TOOLS}
        planned={[]}
        executed={[]}
        results={{}}
      />,
    )
    for (const t of ALL_RETRIEVAL_TOOLS) {
      expect(container.textContent ?? '').toContain(t)
    }
  })

  it('classifies a planned + executed + non-empty tool as gold/has rows', () => {
    const { container } = render(
      <ToolCoverageMatrix
        manifestTools={['msr_sql']}
        planned={['msr_sql']}
        executed={['msr_sql']}
        results={{ msr_sql: { rows: 7, empty: false } }}
      />,
    )
    expect(container.textContent ?? '').toContain('7')
  })

  it('marks an unplanned tool as skipped', () => {
    const { container } = render(
      <ToolCoverageMatrix
        manifestTools={['msr_sql']}
        planned={[]}
        executed={[]}
        results={{}}
      />,
    )
    expect(container.textContent ?? '').toMatch(/skipped/i)
  })
})
