import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WorkflowView } from '../WorkflowView'
import type { ActiveRun, ActiveRunAsset } from '@/hooks/useActiveRun'

/**
 * Packet B2 — C-4, surface 1/3 (review B1_rereview2_20260926T193112Z.md, "BLOCKS
 * B2"): "WorkflowView.tsx's PlanTimeline — renders the literal word 'error', in
 * red, for a blocked asset, from the same useActiveRun hook AgentsView already
 * reads correctly (ra.disposition and ra.blocked_by_asset_id are already on it,
 * so this is close to a one-line fix)."
 *
 * This file proves PlanTimeline now reads `disposition` the same way
 * AgentsView.tsx already does: `state === 'error' && disposition ===
 * 'blocked_dependency'` renders as "blocked" (amber), never the raw "error"
 * (red) — and that a GENUINE root error (disposition null/anything else) still
 * renders "error" in red, so the fix does not over-correct.
 */
const { mockUseActiveRun } = vi.hoisted(() => ({ mockUseActiveRun: vi.fn() }))
vi.mock('@/hooks/useActiveRun', () => ({ useActiveRun: mockUseActiveRun }))
vi.mock('@/hooks/useCockpitSSE', () => ({ useCockpitSSE: vi.fn() }))

// jsdom does not implement scrollIntoView (EventLogTail's own effect calls it) —
// unrelated to this suite's subject, so a bare no-op polyfill is all this needs.
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

const RUN: ActiveRun = {
  id: 'run-00000000',
  scope: 'global',
  scope_target: null,
  action: 'build',
  state: 'running',
  plan: ['bg_root', 'bg_dependent'],
  current_asset_id: null,
  created_at: '2026-01-01T00:00:00Z',
  started_at: '2026-01-01T00:00:00Z',
  pause_requested_at: null,
  stop_requested_at: null,
}

function assetOf(partial: Partial<ActiveRunAsset>): ActiveRunAsset {
  return {
    asset_id: 'bg_dependent',
    position: 1,
    state: 'error',
    started_at: '2026-01-01T00:00:05Z',
    ended_at: '2026-01-01T00:00:06Z',
    error: null,
    disposition: null,
    blocked_by_asset_id: null,
    ...partial,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('WorkflowView — PlanTimeline blocked-vs-error rendering (Packet B2, C-4)', () => {
  it('a cascade victim (disposition=blocked_dependency) renders "blocked", never the raw "error"', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [assetOf({ disposition: 'blocked_dependency', blocked_by_asset_id: 'bg_root' })],
      refresh: () => {},
    })
    render(<WorkflowView chartId="chart-1" />)
    expect(screen.getByText('blocked')).toBeTruthy()
    expect(screen.queryByText('error')).toBeNull()
  })

  it('a genuine root failure (disposition null) still renders "error" — the fix does not over-correct', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [assetOf({ disposition: null })],
      refresh: () => {},
    })
    render(<WorkflowView chartId="chart-1" />)
    expect(screen.getByText('error')).toBeTruthy()
    expect(screen.queryByText('blocked')).toBeNull()
  })

  it('the blocked row is coloured amber (matching AgentsView\'s BlockedRow), not red', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [assetOf({ disposition: 'blocked_dependency', blocked_by_asset_id: 'bg_root' })],
      refresh: () => {},
    })
    render(<WorkflowView chartId="chart-1" />)
    const label = screen.getByText('blocked')
    // '236, 147, 106'... actually the amber used is rgba(236,147,50,0.9) — check channels.
    expect((label as HTMLElement).style.color).toContain('236, 147, 50')
  })

  it('a genuine "complete" or "building" state is unaffected by the disposition check', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [assetOf({ state: 'complete', disposition: null })],
      refresh: () => {},
    })
    render(<WorkflowView chartId="chart-1" />)
    expect(screen.getByText('complete')).toBeTruthy()
  })
})
