import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssetRow } from '../AssetRow'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

/**
 * Packet B1 — C-3 (review B1_review_20260926T182200Z.md, BLOCKS PACKET B2).
 *
 * `AssetRow.tsx` is the LIVE per-asset surface (unlike the dead
 * `components/build_orchestrator/AssetNode.tsx`) and its blocked branch had ZERO
 * tests before this file. B1 replaced a text-sniffing anti-pattern
 * (`errorMessage.startsWith('BLOCKED:')`, tagged "O1" from an earlier campaign)
 * with the structural signal `derivedState === 'blocked'`, sourced from the
 * server's deriveState() (via build_run_assets.disposition, never re-derived from
 * `error` TEXT — §N.7 item 1). This file proves that replacement, including the
 * one case that would catch a regression to the old sniff: a genuine `state:
 * 'error'` row whose text happens to start with 'BLOCKED:' must still render RED,
 * not amber — because classification comes from `state`, never from scanning
 * `error`.
 */

vi.mock('@/hooks/useUserRole', () => ({ useUserRole: vi.fn() }))
import { useUserRole } from '@/hooks/useUserRole'
const mockUseUserRole = useUserRole as ReturnType<typeof vi.fn>

const DATA_ASSET = {
  asset_id: 'bg_laksana_probe',
  layer: 'ganita',
  sort_order: 1,
  sanskrit_name: 'Lakṣaṇa',
  english_name: 'Laksana probe',
  english_description: '',
  storage_type: 'table',
  target_table: 'ganita_positions',
  count_sql: 'SELECT count(*) FROM ganita_positions',
  size_sql: null,
  target_floor: 9,
  expected_volume_formula: null,
  expected_volume_inputs: null,
  volume_explanation: null,
  depends_on: [],
  scope: 'per_chart' as const,
  is_active: true,
  estimated_seconds: null,
  created_at: '2026-01-01T00:00:00Z',
  asset_type: 'data' as const,
  layer_name: 'Gaṇita',
  layer_index: 'L1',
  provides_apis: null,
  health_probe: null,
  catalog_status: 'CURRENT' as const,
  asset_kind: 'data' as const,
  service_health: null,
  last_invoked_at: null,
  last_selftest_at: null,
  selftest_detail: null,
}

function statOf(partial: Partial<AssetStats>): AssetStats {
  return {
    asset_id: 'bg_laksana_probe',
    actual_rows: null,
    volume: null,
    size_bytes: null,
    last_updated: '2026-01-01T00:00:00Z',
    error: null,
    state: 'dormant',
    last_built_at: null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
    ...partial,
  }
}

function renderRow(stat: AssetStats) {
  return render(
    <AssetRow
      asset={DATA_ASSET}
      stat={stat}
      chartId="chart-1"
      activeRunId={null}
      activeRunPaused={false}
      onRunStarted={() => {}}
    />
  )
}

describe('AssetRow — blocked-dependency rendering (Packet B1, C-3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('a blocked asset (state=blocked) renders the amber "blocked by upstream failure" note, with the named blocker', () => {
    renderRow(statOf({
      state: 'blocked',
      error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
      blocked_by_asset_id: 'bg_root',
    }))
    expect(screen.getByText(/blocked by upstream failure: bg_root/)).toBeTruthy()
    // Never the red genuine-failure text for this same row.
    expect(screen.queryByText(/BLOCKED: upstream dependency/)).toBeNull()
  })

  it('a blocked asset with no blocked_by_asset_id yet (prospective-only column, historical row) still renders the amber note, without a blocker name', () => {
    renderRow(statOf({
      state: 'blocked',
      error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
      blocked_by_asset_id: null,
    }))
    const note = screen.getByText(/blocked by upstream failure/)
    expect(note.textContent).toBe('blocked by upstream failure')
  })

  it('a genuine error (state=error) still renders red, with the real error text', () => {
    renderRow(statOf({
      state: 'error',
      error: 'worker_crash: RuntimeError: boom',
    }))
    expect(screen.getByText('worker_crash: RuntimeError: boom')).toBeTruthy()
    expect(screen.queryByText(/blocked by upstream failure/)).toBeNull()
  })

  it('THE REGRESSION GUARD: a genuine error whose text happens to start with "BLOCKED:" still renders RED, never amber — proves classification is structural (state), not text-sniffed', () => {
    // If the old `errorMessage.startsWith('BLOCKED:')` sniff were ever reinstated,
    // this row would misclassify as amber "blocked by upstream failure" despite
    // state === 'error' (a genuine cause, per the server's own deriveState()).
    // This is exactly the inversion Packet B1 exists to prevent — the same class
    // of defect Decision 2 fixed on the engine side for the writer-timeout case.
    renderRow(statOf({
      state: 'error',
      error: 'BLOCKED: upstream dependency(ies) timeout:600s did not complete in this run; skipped to avoid building on incomplete data',
    }))
    expect(screen.getByText(/BLOCKED: upstream dependency\(ies\) timeout:600s/)).toBeTruthy()
    expect(screen.queryByText(/^blocked by upstream failure/)).toBeNull()
  })

  it('the status dot reads amber (not red) for a blocked asset', () => {
    const { container } = renderRow(statOf({
      state: 'blocked',
      error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
      blocked_by_asset_id: 'bg_root',
    }))
    const dot = container.querySelector('[title="CURRENT · blocked"]') as HTMLElement | null
    expect(dot).toBeTruthy()
    // StatusDot: isRed is false for 'blocked' (grouped with isAmber instead), so the
    // dot must NOT be red ('rgba(220,80,80,...)') — it must be the amber '#ECC56A'
    // (jsdom normalizes the hex literal to its rgb() equivalent).
    expect(dot!.style.background).not.toContain('220, 80, 80')
    expect(dot!.style.background).toContain('236, 197, 106')
  })
})
