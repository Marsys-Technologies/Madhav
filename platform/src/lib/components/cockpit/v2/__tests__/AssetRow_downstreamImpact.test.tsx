import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssetRow } from '../AssetRow'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

/**
 * Packet B2 ("the DAG-derived downstream count").
 *
 * AssetRow.tsx's `DownstreamImpactNote` is the ONE consumer of
 * the downstream-dependents count (stats route, DOWNSTREAM_DEPENDENTS_SQL) — rendered only alongside a
 * GENUINE root failure (never a 'blocked' cascade victim: that row's own
 * downstream reach is not what its badge is about).
 *
 * §N.8: absent, zero, and populated must never collapse into one another. This
 * file proves all three render distinctly, and that the "upper bound, not a
 * prediction" caveat lives in the rendered surface (the title attribute), not
 * only in a comment.
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

describe('AssetRow — downstream_dependent_count rendering (Packet B2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('a genuine failure with a positive count renders "could affect up to N downstream", captioned as an upper bound', () => {
    renderRow(statOf({
      state: 'error',
      error: 'worker_crash: RuntimeError: boom',
      downstream_dependent_count: 42,
    }))
    const note = screen.getByText(/could affect up to 42 downstream/)
    expect(note).toBeTruthy()
    expect(note.textContent).toContain('upper bound, not a prediction')
    expect(note.getAttribute('title')).toMatch(/Upper bound from the dependency graph, not an observed or predicted cascade/)
  })

  it('a genuine failure with count === 0 renders "no downstream impact" — a real, present zero, never a blank', () => {
    renderRow(statOf({
      state: 'error',
      error: 'worker_crash: RuntimeError: boom',
      downstream_dependent_count: 0,
    }))
    expect(screen.getByText('no downstream impact')).toBeTruthy()
    // Must not ALSO render the "could affect" phrasing for a zero.
    expect(screen.queryByText(/could affect up to/)).toBeNull()
  })

  it('a genuine failure with count ABSENT (null — the stats query failed) renders NEITHER note — silence, not a fabricated number', () => {
    renderRow(statOf({
      state: 'error',
      error: 'worker_crash: RuntimeError: boom',
      downstream_dependent_count: null,
    }))
    expect(screen.queryByText(/could affect up to/)).toBeNull()
    expect(screen.queryByText('no downstream impact')).toBeNull()
  })

  it('a genuine failure with count UNDEFINED (field never populated by an older client) also renders neither note', () => {
    renderRow(statOf({
      state: 'error',
      error: 'worker_crash: RuntimeError: boom',
      // downstream_dependent_count intentionally omitted
    }))
    expect(screen.queryByText(/could affect up to/)).toBeNull()
    expect(screen.queryByText('no downstream impact')).toBeNull()
  })

  it('a BLOCKED cascade victim never shows the downstream-impact note, even with a real count — the note is about ROOT failures, not their consequences', () => {
    renderRow(statOf({
      state: 'blocked',
      error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data',
      blocked_by_asset_id: 'bg_root',
      downstream_dependent_count: 99,
    }))
    expect(screen.getByText(/blocked by upstream failure: bg_root/)).toBeTruthy()
    expect(screen.queryByText(/could affect up to/)).toBeNull()
    expect(screen.queryByText('no downstream impact')).toBeNull()
  })

  it('a healthy (non-error) asset never shows the downstream-impact note, even with a real count', () => {
    renderRow(statOf({
      state: 'lit',
      error: null,
      downstream_dependent_count: 42,
    }))
    expect(screen.queryByText(/could affect up to/)).toBeNull()
    expect(screen.queryByText('no downstream impact')).toBeNull()
  })
})
