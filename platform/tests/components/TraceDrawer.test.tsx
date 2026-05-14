import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TraceDrawer } from '@/components/consume/TraceDrawer'

// Mock TracePanelContent — heavy SSE hook, not needed for drawer structure tests
vi.mock('@/components/trace/TracePanel', () => ({
  TracePanelContent: ({ queryId }: { queryId: string | null }) => (
    <div data-testid="trace-panel-content" data-query-id={queryId ?? ''} />
  ),
  TracePanel: () => null,
}))

// Mock useTraceStream — avoids EventSource which isn't defined in jsdom
vi.mock('@/hooks/useTraceStream', () => ({
  useTraceStream: vi.fn(() => ({
    steps: [],
    done: false,
    error: null,
    planningActive: false,
    planningModel: null,
    toolsSelected: [],
    queryIntentSummary: null,
  })),
}))

// Mock Sheet components (base-ui) — stub to keep tests DOM-based
vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ open, children }: { open: boolean; children: React.ReactNode }) =>
    open ? <div data-testid="sheet">{children}</div> : null,
  SheetContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sheet-content">{children}</div>
  ),
  SheetHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sheet-header">{children}</div>
  ),
  SheetTitle: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sheet-title">{children}</div>
  ),
}))

describe('TraceDrawer', () => {
  it('renders nothing when closed', () => {
    render(<TraceDrawer queryId="q1" open={false} onOpenChange={() => {}} />)
    expect(screen.queryByTestId('sheet')).toBeNull()
  })

  it('renders TracePanelContent when open', () => {
    render(<TraceDrawer queryId="q1" open={true} onOpenChange={() => {}} />)
    expect(screen.getByTestId('trace-panel-content')).toBeDefined()
    expect(screen.getByTestId('trace-panel-content').getAttribute('data-query-id')).toBe('q1')
  })

  it('passes null queryId through', () => {
    render(<TraceDrawer queryId={null} open={true} onOpenChange={() => {}} />)
    expect(screen.getByTestId('trace-panel-content').getAttribute('data-query-id')).toBe('')
  })

  it('shows "Query Trace" title when open', () => {
    render(<TraceDrawer queryId="q1" open={true} onOpenChange={() => {}} />)
    expect(screen.getByTestId('sheet-title').textContent).toContain('Query Trace')
  })
})
