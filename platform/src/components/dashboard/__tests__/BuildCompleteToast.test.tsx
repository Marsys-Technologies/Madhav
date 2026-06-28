import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import BuildCompleteToast, { type RecentBuild } from '../BuildCompleteToast'

// /api/build/recent is decommissioned (410 Gone). BuildCompleteToast is a
// no-op stub. Tests verify the stub contract; full notification tests will be
// restored when the endpoint is replaced.

describe('BuildCompleteToast (stub)', () => {
  it('renders nothing into the DOM', () => {
    const { container } = render(<BuildCompleteToast />)
    expect(container.firstChild).toBeNull()
  })

  it('never calls fetch (endpoint decommissioned)', () => {
    const spy = vi.spyOn(global, 'fetch')
    render(<BuildCompleteToast />)
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })

  it('exports the RecentBuild interface shape', () => {
    // Verify the exported type compiles — build_id, chart_id, status fields present
    const b: RecentBuild = {
      build_id: 'x',
      chart_id: 'y',
      chart_name: 'Test',
      status: 'complete',
      finished_at: new Date().toISOString(),
      ayanamshas: ['lahiri'],
      error_summary: null,
    }
    expect(b.build_id).toBe('x')
  })
})
