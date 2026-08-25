import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type {
  NirmanaElevationSnapshotV1,
  NirmanaElevationSnapshotV2,
} from '@/lib/nirmana-elevation/types'
import {
  NirmanaElevationTracker,
  NirmanaElevationTrackerView,
} from './NirmanaElevationTracker'

const remainingLayerIds = ['L1', 'L2', 'L3', 'L4', 'L5'] as const

const snapshotV1: NirmanaElevationSnapshotV1 = {
  schema_version: '1.0',
  generation: '1'.repeat(64),
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
  }],
  active_runs: [{ run_id: 'run-42', layer: 'L0', wave_index: 2, state: 'running', active_asset_ids: ['ga_lagna'], completed_assets: 0, planned_assets: 1, started_at: '2026-08-25T08:00:00.000Z', last_progress_at: '2026-08-25T08:29:00.000Z' }],
  release: { main_sha: 'abc123', deployed_sha: 'abc123', deployed_revision: 'amjis-web-0042', production_in_sync: true, observed_at: '2026-08-25T08:28:00.000Z' },
  sources: [{ source_id: 'build-runs', provenance: 'Cloud SQL', state: 'fresh', observed_at: '2026-08-25T08:29:00.000Z', age_seconds: 60, error: null }],
  data_quality: { verdict: 'reliable', gaps: ['Asset denominator is reconciling'], contradictions: [] },
}

function snapshotV2(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function unavailableV2(message: string): NirmanaElevationSnapshotV2 {
  const snapshot = snapshotV2()
  snapshot.sources = [{ ...snapshot.sources[0], state: 'unavailable', error: message }]
  snapshot.data_quality = { verdict: 'degraded', gaps: [message], contradictions: [] }
  return snapshot
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('NirmanaElevationTracker', () => {
  it('renders the v2 campaign spine and keeps the audit surface secondary by default', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV2())))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByRole('heading', { name: /nirmāṇa campaign/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /campaign spine/i })).toBeVisible()
    expect(screen.getByLabelText(/now, next, then campaign rail/i)).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Praśna Rules')).toBeVisible()
    expect(screen.getByText('Prashna Rules')).toBeVisible()
    expect(screen.getByRole('button', { name: /audit evidence.*reliable/i })).toBeVisible()
    expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /sequential layer rail/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /asset evidence ledger/i })).not.toBeInTheDocument()
  })

  it('selects the temporary v1 evidence view for a schema v1 payload', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV1)))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/tracker upgrade pending — showing schema v1 evidence view/i)).toBeVisible()
    expect(screen.getByRole('heading', { name: /sequential layer rail/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /asset evidence ledger/i })).toBeVisible()
    expect(screen.queryByRole('heading', { name: /campaign spine/i })).not.toBeInTheDocument()
  })

  it('treats a malformed v2 snapshot as unavailable instead of rendering a partial tracker', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ ...snapshotV2(), stages: [] })))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/live snapshot unavailable/i)).toBeVisible()
    expect(screen.queryByRole('heading', { name: /campaign spine/i })).not.toBeInTheDocument()
  })

  it.each([
    {
      label: '503 response',
      nextResponse: () => jsonResponse(unavailableV2('Cloud SQL unavailable'), 503),
      error: /cloud sql unavailable/i,
    },
    {
      label: 'malformed response',
      nextResponse: () => jsonResponse({ ...snapshotV2(), stages: [] }),
      error: /did not satisfy the shared evidence contract/i,
    },
  ])('retains the last valid v2 DOM after a $label', async ({ nextResponse, error }) => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(jsonResponse(snapshotV2()))
      .mockImplementation(() => Promise.resolve(nextResponse())))

    render(<NirmanaElevationTracker pollIntervalMs={10} />)
    await screen.findByText('Praśna Rules')

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2), { timeout: 500 })

    expect(screen.getByText('Praśna Rules')).toBeVisible()
    expect(screen.getByRole('alert')).toHaveTextContent(/current state unknown/i)
    expect(screen.getByRole('alert')).toHaveTextContent(error)
    expect(screen.getByRole('alert')).toHaveTextContent(/failure observed/i)
    expect(within(screen.getByRole('alert')).getByRole('time')).toBeVisible()
  })

  it('refreshes on focus and reconnect', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(jsonResponse(snapshotV2()))))

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')

    act(() => window.dispatchEvent(new Event('focus')))
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    act(() => window.dispatchEvent(new Event('online')))
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3))
  })

  it('allows only the newest response to replace the rendered snapshot', async () => {
    let resolveFirst: (response: Response) => void = () => undefined
    const first = new Promise<Response>((resolve) => { resolveFirst = resolve })
    const later = snapshotV2()
    later.campaign.current_wave = 3
    later.layers[0].waves[0].wave_index = 3
    later.assets[0].wave_index = 3
    vi.stubGlobal('fetch', vi.fn()
      .mockReturnValueOnce(first)
      .mockResolvedValueOnce(jsonResponse(later)))

    render(<NirmanaElevationTracker />)
    act(() => window.dispatchEvent(new Event('focus')))
    expect(await screen.findByText('L0 · Brahmagyan · Wave 3')).toBeVisible()
    await act(async () => resolveFirst(jsonResponse(snapshotV2())))

    expect(screen.getByText('L0 · Brahmagyan · Wave 3')).toBeVisible()
  })

  it('withholds numeric milestone progress for an unresolved asset', () => {
    const snapshot = snapshotV2()
    const asset = snapshot.assets[0]
    asset.execution_obligation = 'unresolved'
    asset.milestones_earned = null
    asset.milestones_required = null

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:00:00.000Z')} />)

    const card = screen.getByText(asset.asset_id).closest('article')
    if (!card) throw new Error('Current asset card is missing.')
    expect(within(card).getByText('Milestone count unavailable')).toBeVisible()
    expect(within(card).queryByText(/\d+ of \d+ required milestones/i)).not.toBeInTheDocument()
  })

  it('opens a read-only asset-filtered audit drawer with provenance and release evidence', () => {
    const snapshot = snapshotV2()
    snapshot.release = {
      main_sha: 'main-abc',
      deployed_sha: 'deployed-def',
      deployed_revision: 'amjis-web-0042',
      production_in_sync: false,
      observed_at: '2026-08-26T00:02:00.000Z',
    }
    snapshot.data_quality.contradictions = ['Deployed SHA differs from main.']
    snapshot.assets[1].evidence_refs = ['unrelated:ka_smriti']

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    fireEvent.click(screen.getByRole('button', { name: /audit details for bg_prashna_rules/i }))

    const drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getByText('Reusable contract fixture')).toBeVisible()
    expect(within(drawer).getByText('main-abc')).toBeVisible()
    expect(within(drawer).getByText('deployed-def')).toBeVisible()
    expect(within(drawer).getByText('amjis-web-0042')).toBeVisible()
    expect(within(drawer).getByText('Deployed SHA differs from main.')).toBeVisible()
    expect(within(drawer).getByText('build_run:run-l0-wave-2')).toBeVisible()
    expect(within(drawer).queryByText('unrelated:ka_smriti')).not.toBeInTheDocument()

    fireEvent.click(within(drawer).getByRole('button', { name: /close audit drawer/i }))
    expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument()
  })

  it('opens the global audit by keyboard, contains Tab focus, and restores focus after Escape', async () => {
    const user = userEvent.setup()
    render(<NirmanaElevationTrackerView snapshot={snapshotV2()} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    const trigger = screen.getByRole('button', { name: /audit evidence.*reliable/i })

    trigger.focus()
    await user.keyboard('{Enter}')

    const drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    await waitFor(() => expect(drawer).toContainElement(document.activeElement as HTMLElement))
    for (let index = 0; index < 4; index += 1) {
      await user.tab()
      await waitFor(() => expect(drawer).toContainElement(document.activeElement as HTMLElement))
    }

    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument())
    expect(trigger).toHaveFocus()
  })

  it('clears an asset audit filter on close and globally reopens all campaign evidence', async () => {
    const user = userEvent.setup()
    const snapshot = snapshotV2()
    snapshot.assets[1].evidence_refs = ['unrelated:ka_smriti']
    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    const assetTrigger = screen.getByRole('button', { name: /audit details for bg_prashna_rules/i })

    assetTrigger.focus()
    await user.keyboard('{Enter}')
    let drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getByText('build_run:run-l0-wave-2')).toBeVisible()
    expect(within(drawer).queryByText('unrelated:ka_smriti')).not.toBeInTheDocument()

    const close = within(drawer).getByRole('button', { name: /close audit drawer/i })
    close.focus()
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument())
    expect(assetTrigger).toHaveFocus()

    const globalTrigger = screen.getByRole('button', { name: /audit evidence.*3 references.*reliable/i })
    globalTrigger.focus()
    await user.keyboard('{Enter}')
    drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getByText('build_run:run-l0-wave-2')).toBeVisible()
    expect(within(drawer).getByText('unrelated:ka_smriti')).toBeVisible()
    expect(within(drawer).getByText('build_run:medical-mappings')).toBeVisible()
  })
})
