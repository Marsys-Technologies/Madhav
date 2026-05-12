import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import { QueryLogTable } from '../QueryLogTable'
import type { QueryLogRow } from '@/lib/performance/api_client'

const sampleRow: QueryLogRow = {
  id: 'r1',
  source: 'consume',
  created_at: '2026-05-12T10:00:00Z',
  query_text: 'Q?',
  query_class: 'interpretive',
  plan_type: 'single_answer',
  plan_accuracy_label: 'unjudged',
  validator_verdict: 'pass',
  b10_violation: false,
  b11_violation: false,
  citations_present: true,
  citation_count: 3,
  latency_total_ms: 2500,
  synthesis_status: 'success',
  audit_event_id: 'ae-1',
  eval_run_id: null,
  judge_verdict_summary: null,
}

describe('QueryLogTable', () => {
  it('renders one row per record with all visible columns', () => {
    render(
      <QueryLogTable
        rows={[sampleRow, { ...sampleRow, id: 'r2', source: 'eval', query_class: 'factual' }]}
        total={2}
        page={1}
        pageSize={50}
        onPageChange={() => undefined}
      />
    )
    expect(screen.getByText('interpretive')).toBeInTheDocument()
    expect(screen.getByText('factual')).toBeInTheDocument()
    expect(screen.getAllByText('single_answer').length).toBe(2)
    expect(screen.getAllByText('2500').length).toBeGreaterThan(0)
  })

  it('fires onRowClick when a row is clicked', () => {
    const onRowClick = vi.fn()
    render(
      <QueryLogTable
        rows={[sampleRow]}
        total={1}
        page={1}
        pageSize={50}
        onPageChange={() => undefined}
        onRowClick={onRowClick}
      />
    )
    fireEvent.click(screen.getByText('interpretive'))
    expect(onRowClick).toHaveBeenCalledTimes(1)
    expect(onRowClick.mock.calls[0][0].id).toBe('r1')
  })

  it('disables Prev on page 1 and Next on last page', () => {
    render(
      <QueryLogTable
        rows={[sampleRow]}
        total={1}
        page={1}
        pageSize={50}
        onPageChange={() => undefined}
      />
    )
    expect(screen.getByText('Prev')).toBeDisabled()
    expect(screen.getByText('Next')).toBeDisabled()
  })

  it('shows the empty-state row when rows is empty', () => {
    render(
      <QueryLogTable rows={[]} total={0} page={1} pageSize={50} onPageChange={() => undefined} />
    )
    expect(screen.getByText(/no queries in this window/i)).toBeInTheDocument()
  })

  it('paginates: fires onPageChange when Next is clicked', () => {
    const onPageChange = vi.fn()
    render(
      <QueryLogTable
        rows={[sampleRow]}
        total={150}
        page={1}
        pageSize={50}
        onPageChange={onPageChange}
      />
    )
    fireEvent.click(screen.getByText('Next'))
    expect(onPageChange).toHaveBeenCalledWith(2)
  })
})
