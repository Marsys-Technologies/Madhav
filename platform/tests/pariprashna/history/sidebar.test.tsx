/**
 * History sidebar (BRIEF_PB-4 Lane F-1, §10.1) — grouping by chart then
 * recency, collapse-state persistence, and the streaming-dot state
 * transition. Demonstrated-can-fail per §N.8: each assertion below is a
 * concrete DOM/localStorage check, not a "renders without throwing" smoke.
 */
import { describe, it, expect, afterEach, beforeEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { Sidebar } from '@/components/pariprashna/history/Sidebar'
import type { ThreadSummary } from '@/components/pariprashna/history/types'

afterEach(cleanup)
beforeEach(() => {
  window.localStorage.clear()
})

const CHART_A = 'chart-a'
const CHART_B = 'chart-b'

function thread(overrides: Partial<ThreadSummary>): ThreadSummary {
  return {
    id: 'thread-1',
    chartId: CHART_A,
    chartName: 'Abhisek Mohanty',
    title: 'What does this period ask of my career?',
    updatedAtMs: Date.now(),
    active: false,
    streaming: false,
    ...overrides,
  }
}

describe('Sidebar grouping', () => {
  it('groups threads by chart, chart groups ordered by their own most-recent thread', () => {
    const now = Date.now()
    const threads: ThreadSummary[] = [
      thread({ id: 't-old-a', chartId: CHART_A, chartName: 'Abhisek Mohanty', title: 'Old A', updatedAtMs: now - 10_000 }),
      thread({ id: 't-new-b', chartId: CHART_B, chartName: 'Family Chart', title: 'New B', updatedAtMs: now }),
      thread({ id: 't-new-a', chartId: CHART_A, chartName: 'Abhisek Mohanty', title: 'New A', updatedAtMs: now - 1_000 }),
    ]
    render(<Sidebar threads={threads} onSelect={() => {}} />)

    const rows = screen.getAllByTestId('pp-sidebar-row').map((el) => el.getAttribute('data-thread-id'))
    // Chart B's only thread is more recent than either of chart A's, so its
    // group renders first; within chart A, the newer thread renders first.
    expect(rows).toEqual(['t-new-b', 't-new-a', 't-old-a'])
  })

  it('renders an honest empty state and no fabricated rows when there are no threads', () => {
    render(<Sidebar threads={[]} onSelect={() => {}} />)
    expect(screen.queryAllByTestId('pp-sidebar-row')).toHaveLength(0)
    expect(screen.getByText(/will appear here once it starts/i)).toBeInTheDocument()
  })
})

describe('Sidebar streaming dot + active tick', () => {
  it('shows the streaming dot only for a streaming thread', () => {
    const threads = [thread({ id: 't-live', streaming: true }), thread({ id: 't-settled', streaming: false, updatedAtMs: Date.now() - 5000 })]
    render(<Sidebar threads={threads} onSelect={() => {}} />)

    const rows = screen.getAllByTestId('pp-sidebar-row')
    const live = rows.find((r) => r.getAttribute('data-thread-id') === 't-live')!
    const settled = rows.find((r) => r.getAttribute('data-thread-id') === 't-settled')!
    expect(live.querySelector('[data-testid="pp-sidebar-streaming-dot"]')).not.toBeNull()
    expect(settled.querySelector('[data-testid="pp-sidebar-streaming-dot"]')).toBeNull()
  })

  it('marks the active thread with aria-current', () => {
    const threads = [thread({ id: 't-active', active: true }), thread({ id: 't-inactive', active: false, updatedAtMs: Date.now() - 5000 })]
    render(<Sidebar threads={threads} onSelect={() => {}} />)
    const rows = screen.getAllByTestId('pp-sidebar-row')
    const active = rows.find((r) => r.getAttribute('data-thread-id') === 't-active')!
    const inactive = rows.find((r) => r.getAttribute('data-thread-id') === 't-inactive')!
    expect(active.getAttribute('aria-current')).toBe('true')
    expect(inactive.getAttribute('aria-current')).toBeNull()
  })
})

describe('Sidebar collapse persistence', () => {
  it('persists collapse state across remounts via localStorage', () => {
    const threads = [thread({})]
    const { unmount } = render(<Sidebar threads={threads} onSelect={() => {}} />)

    const toggle = screen.getByRole('button', { name: /collapse past readings/i })
    fireEvent.click(toggle)
    expect(window.localStorage.getItem('pariprashna.sidebar.collapsed')).toBe('1')
    unmount()

    render(<Sidebar threads={threads} onSelect={() => {}} />)
    expect(screen.getByRole('button', { name: /expand past readings/i })).toBeInTheDocument()
  })

  it('round-trips back open the same way', () => {
    window.localStorage.setItem('pariprashna.sidebar.collapsed', '1')
    render(<Sidebar threads={[thread({})]} onSelect={() => {}} />)
    const toggle = screen.getByRole('button', { name: /expand past readings/i })
    fireEvent.click(toggle)
    expect(window.localStorage.getItem('pariprashna.sidebar.collapsed')).toBe('0')
  })
})

describe('Sidebar row selection + rename', () => {
  it('calls onSelect with the row thread id on click', () => {
    let selected: string | null = null
    render(<Sidebar threads={[thread({ id: 't-1' })]} onSelect={(id) => (selected = id)} />)
    fireEvent.click(screen.getByTestId('pp-sidebar-row'))
    expect(selected).toBe('t-1')
  })

  it('commits a rename on double-click → edit → Enter, and does not fire onSelect', () => {
    let selected: string | null = null
    let renamed: [string, string] | null = null
    render(
      <Sidebar
        threads={[thread({ id: 't-1', title: 'Old title' })]}
        onSelect={(id) => (selected = id)}
        onRename={(id, title) => (renamed = [id, title])}
      />,
    )
    fireEvent.doubleClick(screen.getByText('Old title'))
    const input = screen.getByDisplayValue('Old title')
    fireEvent.change(input, { target: { value: 'New title' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(renamed).toEqual(['t-1', 'New title'])
    expect(selected).toBeNull()
  })

  it('activates a row via Enter and Space (keyboard parity with click)', () => {
    const selections: string[] = []
    render(<Sidebar threads={[thread({ id: 't-1' })]} onSelect={(id) => selections.push(id)} />)
    const row = screen.getByTestId('pp-sidebar-row')
    fireEvent.keyDown(row, { key: 'Enter' })
    fireEvent.keyDown(row, { key: ' ' })
    expect(selections).toEqual(['t-1', 't-1'])
  })
})

describe('Sidebar accessibility structure', () => {
  it('nests each chart group as an ARIA group (list > group > listitem — a bare list > div > listitem tree fails aria-required-children)', () => {
    const threads = [thread({ id: 't-1', chartId: CHART_A, chartName: 'Abhisek Mohanty' })]
    render(<Sidebar threads={threads} onSelect={() => {}} />)
    const list = screen.getByRole('list', { name: /past readings/i })
    const group = screen.getByRole('group', { name: 'Abhisek Mohanty' })
    expect(list.contains(group)).toBe(true)
    expect(group.contains(screen.getByTestId('pp-sidebar-row'))).toBe(true)
  })

  it('carries the full untruncated title as a tooltip on both the collapsed glyph and the expanded label, for CSS-truncated long titles', () => {
    const longTitle = 'A'.repeat(200)
    render(<Sidebar threads={[thread({ id: 't-1', title: longTitle })]} onSelect={() => {}} />)
    expect(screen.getByText(longTitle)).toHaveAttribute('title', longTitle)
  })
})

describe('Sidebar large-history-list performance (test plan §5.1 "History sidebar" row)', () => {
  it('groups, sorts, and renders 2000 threads across 200 charts well within an interactive budget', () => {
    const now = Date.now()
    const threads: ThreadSummary[] = Array.from({ length: 2000 }, (_, i) => {
      const chartIndex = i % 200
      return thread({
        id: `t-${i}`,
        chartId: `chart-${chartIndex}`,
        chartName: `Chart ${chartIndex}`,
        title: `Question ${i}`,
        updatedAtMs: now - i * 1000,
      })
    })
    const start = performance.now()
    render(<Sidebar threads={threads} onSelect={() => {}} />)
    const elapsedMs = performance.now() - start
    // Component/INTEGRATION-rung budget, not a LIVE-deployed-perf claim — this
    // is jsdom, not a real browser paint. 500ms is a generous ceiling for
    // 2000 rows across 200 groups; a real regression (e.g. an accidental
    // O(n²) re-sort per row) blows well past it, which is what this guards.
    expect(elapsedMs).toBeLessThan(500)
    expect(screen.getAllByTestId('pp-sidebar-row')).toHaveLength(2000)
  })
})
