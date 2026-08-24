import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { NirmanaElevationTracker } from './NirmanaElevationTracker'
import type { NirmanaElevationSnapshot as NirmanaTrackerSnapshot } from '@/lib/nirmana-elevation/types'

const remainingLayerIds = ['L1', 'L2', 'L3', 'L4', 'L5'] as const

const snapshot: NirmanaTrackerSnapshot = {
  schema_version: '1.0',
  generation: 'a'.repeat(64),
  generated_at: '2026-08-25T08:30:00.000Z',
  campaign: {
    campaign_id: 'nirmana-elevation',
    definition_revision: 'r1',
    definition_status: 'reconciling',
    campaign_status: 'takeover',
    current_layer: 'L0',
    current_wave: 2,
  },
  progress: {
    denominator_status: 'reconciling',
    assets_total: null,
    assets_frozen: 1,
    layers_total: 6,
    layers_frozen: 0,
    buildable_assets_total: null,
    accepted_rebuilds: 0,
  },
  layers: [
    {
      layer_id: 'L0', order: 0, state: 'open', assets_total: null,
      optimization_reviewed: 2, rebuilt_or_dispositioned: 1, verified: 1, frozen: 0,
      waves: [{ wave_index: 2, state: 'active', asset_ids: ['ga_lagna'], active_asset_ids: ['ga_lagna'], blocked_asset_ids: [] }],
    },
    ...remainingLayerIds.map((layer_id, index) => ({
      layer_id, order: index + 1, state: 'locked' as const, assets_total: null,
      optimization_reviewed: 0, rebuilt_or_dispositioned: 0, verified: 0, frozen: 0, waves: [],
    })),
  ],
  assets: [{
    asset_id: 'ga_lagna', display_name: 'Lagna', layer: 'L0', wave_index: 2, producer_id: 'ga_lagna_writer',
    covered_asset_ids: [], execution_obligation: 'build', lifecycle_state: 'running', readiness_state: 'unverified',
    current_run_state: 'running', progress_mode: 'determinate', work_committed: 3, work_total: 8,
    current_unit_label: 'substeps', baseline_duration_seconds: 80, final_duration_seconds: null, improvement_percent: null,
    blocker: null, evidence_refs: ['run:42', 'sha:abc123'],
  }, {
    asset_id: 'ga_sensitive', display_name: 'Sensitive', layer: 'L0', wave_index: 2, producer_id: null,
    covered_asset_ids: [], execution_obligation: 'probe', lifecycle_state: 'queued', readiness_state: 'unknown',
    current_run_state: null, progress_mode: 'indeterminate', work_committed: null, work_total: null,
    current_unit_label: 'awaiting probe', baseline_duration_seconds: null, final_duration_seconds: null, improvement_percent: null,
    blocker: 'Dependency receipt is unavailable', evidence_refs: [],
  }],
  active_runs: [{ run_id: 'run-42', layer: 'L0', wave_index: 2, state: 'running', active_asset_ids: ['ga_lagna'], completed_assets: 0, planned_assets: 2, started_at: '2026-08-25T08:00:00.000Z', last_progress_at: '2026-08-25T08:29:00.000Z' }],
  release: { main_sha: 'abc123', deployed_sha: 'abc123', deployed_revision: 'amjis-web-0042', production_in_sync: true, observed_at: '2026-08-25T08:28:00.000Z' },
  sources: [{ source_id: 'build-runs', provenance: 'Cloud SQL', state: 'fresh', observed_at: '2026-08-25T08:29:00.000Z', age_seconds: 60, error: null }],
  data_quality: { verdict: 'reliable', gaps: ['Asset denominator is reconciling'], contradictions: [] },
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function unavailableSnapshot(message: string): NirmanaTrackerSnapshot {
  return {
    ...snapshot,
    sources: [{ ...snapshot.sources[0], state: 'unavailable', error: message }],
    data_quality: { verdict: 'degraded', gaps: [message], contradictions: [] },
  }
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('NirmanaElevationTracker', () => {
  it('renders the operational regions with a reconciling denominator rather than an invented percentage', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshot)))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/reconciling — no percentage/i)).toBeVisible()
    expect(screen.getByRole('heading', { name: /nirmāṇa elevation tracker/i })).toBeVisible()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /sequential layer rail/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /current-layer waves/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /asset evidence ledger/i })).toBeVisible()
    expect(screen.getByText('3 / 8 substeps')).toBeVisible()
    expect(screen.getByText(/indeterminate — awaiting probe/i)).toBeVisible()
  })

  it('retains the last known snapshot behind an explicit unknown overlay after an unavailable response', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(jsonResponse(snapshot))
      // The polling interval can fire again before assertions complete when
      // the full suite runs concurrently. Every later response stays
      // explicitly unavailable instead of making fetch return undefined or
      // reusing an already-consumed Response body.
      .mockImplementation(() => Promise.resolve(jsonResponse(unavailableSnapshot('Cloud SQL unavailable'), 503))))

    render(<NirmanaElevationTracker pollIntervalMs={10} />)
    await screen.findByText('Lagna')

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2), { timeout: 500 })

    expect(screen.getByText('Lagna')).toBeVisible()
    expect(screen.getByRole('alert')).toHaveTextContent(/current state unknown/i)
    expect(screen.getByRole('alert')).toHaveTextContent(/cloud sql unavailable/i)
  })

  it('treats a malformed snapshot body as unavailable instead of rendering an empty tracker', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ schema_version: '1.0' })))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/live snapshot unavailable/i)).toBeVisible()
    expect(screen.queryByText(/sequential layer rail/i)).not.toBeInTheDocument()
  })

  it('refreshes on focus and only the newest response may replace a snapshot', async () => {
    let resolveFirst: (response: Response) => void = () => undefined
    const first = new Promise<Response>((resolve) => { resolveFirst = resolve })
    const later = { ...snapshot, generation: 'b'.repeat(64), campaign: { ...snapshot.campaign, current_wave: 3 } }
    vi.stubGlobal('fetch', vi.fn()
      .mockReturnValueOnce(first)
      .mockResolvedValueOnce(jsonResponse(later)))

    render(<NirmanaElevationTracker />)
    act(() => window.dispatchEvent(new Event('focus')))
    await screen.findByText(/wave 3/i)
    await act(async () => resolveFirst(jsonResponse(snapshot)))

    expect(screen.getByText('L0 · Wave 3')).toBeVisible()
  })
})
