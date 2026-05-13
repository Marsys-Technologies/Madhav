/**
 * CP.3 AC.CP3.6 — Observatory deep-link pencil visible on every provider stack card.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, title }: { href: string; children: React.ReactNode; title?: string }) => (
    <a href={href} title={title}>{children}</a>
  ),
}))

import { StackBreakdownCards } from '../StackBreakdownCards'
import type { BreakdownsResponse } from '@/lib/observatory/types'

function makeData(providers: string[]): BreakdownsResponse {
  return {
    rows: providers.map(p => ({
      dim_value: p,
      cost_usd: 1.0,
      request_count: 10,
      input_tokens: 1000,
      output_tokens: 500,
      cache_tokens: 0,
      avg_latency_ms: 200,
    })),
  }
}

describe('AC.CP3.6 — StackBreakdownCards deep-link pencil', () => {
  it('shows pencil link for gemini provider (maps to gemini stack)', () => {
    render(<StackBreakdownCards data={makeData(['gemini'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('/aiops/control?stack=gemini&from=observatory')
  })

  it('maps openai provider to gpt stack in the pencil href', () => {
    render(<StackBreakdownCards data={makeData(['openai'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect((link as HTMLAnchorElement).href).toContain('stack=gpt')
  })

  it('maps anthropic provider to anthropic stack in the pencil href', () => {
    render(<StackBreakdownCards data={makeData(['anthropic'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect((link as HTMLAnchorElement).href).toContain('stack=anthropic')
  })

  it('maps nim provider to nim stack in the pencil href', () => {
    render(<StackBreakdownCards data={makeData(['nim'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect((link as HTMLAnchorElement).href).toContain('stack=nim')
  })

  it('maps deepseek provider to deepseek stack in the pencil href', () => {
    render(<StackBreakdownCards data={makeData(['deepseek'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect((link as HTMLAnchorElement).href).toContain('stack=deepseek')
  })

  it('shows pencil on all 5 provider cards when all are present', () => {
    render(<StackBreakdownCards data={makeData(['anthropic', 'openai', 'gemini', 'deepseek', 'nim'])} dimension="provider" />)
    const links = screen.getAllByTitle('Configure in AIOps')
    expect(links).toHaveLength(5)
  })

  it('does NOT show pencil for pipeline_stage dimension', () => {
    render(<StackBreakdownCards data={makeData(['synthesize'])} dimension="pipeline_stage" />)
    expect(screen.queryByTitle('Configure in AIOps')).toBeFalsy()
  })

  it('pencil href includes from=observatory', () => {
    render(<StackBreakdownCards data={makeData(['gemini'])} dimension="provider" />)
    const link = screen.getByTitle('Configure in AIOps')
    expect((link as HTMLAnchorElement).href).toContain('from=observatory')
  })
})
