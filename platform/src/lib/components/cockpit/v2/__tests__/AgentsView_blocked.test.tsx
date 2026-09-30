import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ActiveRunAsset, ActiveRun } from '@/hooks/useActiveRun'

/**
 * Packet B1 — C-2b (review B1_review_20260926T182200Z.md).
 *
 * `AgentsView.tsx` was named the WORST of the three live surfaces the packet's
 * own before-measurement census missed: it read build_run_assets.state RAW
 * (via useActiveRun -> GET /api/cockpit/runs/active), with no disposition field
 * even available, so a cascade-blocked dependent counted under "Errors this run"
 * completely unaffected by every fix elsewhere in this packet.
 *
 * The fix: runs/active/route.ts now selects `disposition` (+ gated
 * `blocked_by_asset_id`), ActiveRunAsset carries both, and AgentsView splits its
 * single `errors` bucket into `errors` (disposition !== 'blocked_dependency') and
 * a new `blocked` bucket, rendered in its own amber section.
 */

vi.mock('@/hooks/useActiveRun', () => ({ useActiveRun: vi.fn() }))
import { useActiveRun } from '@/hooks/useActiveRun'
const mockUseActiveRun = useActiveRun as ReturnType<typeof vi.fn>

import { AgentsView } from '../AgentsView'

const RUN: ActiveRun = {
  id: 'run-1', scope: 'global', scope_target: null, action: 'build', state: 'running',
  plan: ['bg_root', 'bg_dependent'], current_asset_id: null, created_at: '2026-09-27T00:00:00Z',
  started_at: '2026-09-27T00:00:00Z', pause_requested_at: null, stop_requested_at: null,
}

function ra(partial: Partial<ActiveRunAsset>): ActiveRunAsset {
  return {
    asset_id: 'x', position: 0, state: 'queued', started_at: null, ended_at: null,
    error: null, disposition: null, blocked_by_asset_id: null,
    ...partial,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('AgentsView — blocked vs genuine error buckets (Packet B1, C-2b)', () => {
  it('a blocked dependent (state=error, disposition=blocked_dependency) is reported under "Blocked this run", never "Errors this run"', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [
        ra({
          asset_id: 'bg_dependent', state: 'error',
          error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
          disposition: 'blocked_dependency', blocked_by_asset_id: 'bg_root',
        }),
      ],
      refresh: () => {},
    })
    render(<AgentsView chartId="chart-1" />)
    expect(screen.getByText('Blocked this run (1)')).toBeTruthy()
    expect(screen.queryByText(/Errors this run/)).toBeNull()
    expect(screen.getByText(/blocked by upstream failure: bg_root/)).toBeTruthy()
  })

  it('a genuine root failure (state=error, disposition NOT blocked_dependency) is still reported under "Errors this run"', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [
        ra({
          asset_id: 'bg_root', state: 'error',
          error: 'worker_crash: RuntimeError: boom', disposition: null,
        }),
      ],
      refresh: () => {},
    })
    render(<AgentsView chartId="chart-1" />)
    expect(screen.getByText('Errors this run (1)')).toBeTruthy()
    expect(screen.queryByText(/Blocked this run/)).toBeNull()
    expect(screen.getByText('worker_crash: RuntimeError: boom')).toBeTruthy()
  })

  it('a mixed run buckets each asset independently — one cause, one blocked, counted separately', () => {
    mockUseActiveRun.mockReturnValue({
      run: RUN,
      assets: [
        ra({ asset_id: 'bg_root', state: 'error', error: 'worker_crash: boom', disposition: null }),
        ra({
          asset_id: 'bg_dependent', state: 'error',
          error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
          disposition: 'blocked_dependency', blocked_by_asset_id: 'bg_root',
        }),
      ],
      refresh: () => {},
    })
    render(<AgentsView chartId="chart-1" />)
    expect(screen.getByText('Errors this run (1)')).toBeTruthy()
    expect(screen.getByText('Blocked this run (1)')).toBeTruthy()
  })
})
