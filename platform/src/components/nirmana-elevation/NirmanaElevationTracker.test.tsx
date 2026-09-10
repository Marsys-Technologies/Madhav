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

// jsdom has no EventSource implementation. The tracker now always subscribes
// to the cockpit SSE bus on mount (see the SSE-triggered-refetch effect in
// NirmanaElevationTracker.tsx), so every test that renders the live
// <NirmanaElevationTracker /> component (not just the SSE-specific tests
// below) needs this shim in place or the render itself throws. Stubbed once
// at module scope; instances are cleared per-test in the shared afterEach.
class MockEventSource {
  static instances: MockEventSource[] = []
  listeners: Record<string, ((event: MessageEvent) => void)[]> = {}
  onerror: (() => void) | null = null
  constructor(public url: string) { MockEventSource.instances.push(this) }
  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    this.listeners[type] = [...(this.listeners[type] ?? []), listener]
  }
  close() {}
  emit(type: string) { this.listeners[type]?.forEach((listener) => listener(new MessageEvent(type))) }
}
vi.stubGlobal('EventSource', MockEventSource)

const remainingLayerIds = ['L1', 'L2', 'L3', 'L4', 'L5'] as const
const unsafeDatabaseUri = `postgresql${'://tracker_admin:secret-password@db.private.internal/nirmana'}`
const unsafeGithubToken = `gh${'p_abcdefghijklmnopqrstuvwxyz1234567890ABCD'}`
const unsafeOpenAiToken = `sk${'-proj-abcdefghijklmnopqrstuvwxyz1234567890'}`

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

function unavailableV2(): NirmanaElevationSnapshotV2 {
  const message = 'Authoritative source is unavailable.'
  const snapshot = snapshotV2()
  snapshot.sources = [{ ...snapshot.sources[0], state: 'unavailable', error_code: 'NIRMANA_SOURCE_UNAVAILABLE', error_message: message }]
  snapshot.data_quality = { verdict: 'degraded', gaps: [message], contradictions: [] }
  return snapshot
}

function baselineMissingV2(): NirmanaElevationSnapshotV2 {
  const snapshot = snapshotV2()
  snapshot.program_sync = {
    status: 'baseline_missing',
    source_observation_id: '77777777-7777-4777-8777-777777777777',
    observed_at: '2026-08-27T05:00:00.000Z',
    age_seconds: 120,
    affected_asset_ids: [],
    current_definition_sha256: null,
    candidate_definition_sha256: 'd'.repeat(64),
    candidate_catalogue_sha256: 'e'.repeat(64),
    supersession_eligible: false,
    supersession_blockers: [],
  }
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  if (!monitor) throw new Error('Fixture must include the program monitor source.')
  Object.assign(monitor, {
    state: 'fresh', observed_at: '2026-08-27T05:00:00.000Z', age_seconds: 120,
    error_code: null, error_message: null,
  })
  return snapshot
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
  MockEventSource.instances = []
})

describe('NirmanaElevationTracker', () => {
  it('explains when the first program synchronization observation is missing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV2())))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText('Tracker awaiting first synchronization')).toBeVisible()
    expect(screen.getByText('No program synchronization observation has been received yet. Progress and asset labels are intentionally withheld until the first governed observation is available.')).toBeVisible()
  })

  it('turns a missing first observation into an actionable setup state without claiming progress', () => {
    const snapshot = snapshotV2()
    snapshot.program_sync = {
      status: 'unknown',
      source_observation_id: null,
      observed_at: null,
      age_seconds: null,
      affected_asset_ids: [],
      current_definition_sha256: null,
      candidate_definition_sha256: null,
      candidate_catalogue_sha256: null,
      supersession_eligible: false,
      supersession_blockers: [],
    }
    const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
    if (!monitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(monitor, { state: 'unknown', observed_at: null, age_seconds: null })

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-28T00:13:00.000Z')} />)

    expect(screen.getByRole('heading', { name: 'Synchronization setup required' })).toBeVisible()
    expect(screen.getByText(/no monitor observation has been recorded/i)).toBeVisible()
    expect(screen.getByText(/verify the dedicated monitor scheduler in google cloud/i)).toBeVisible()
    expect(screen.getByText(/wait for its natural five-minute run/i)).toBeVisible()
    expect(screen.queryByRole('main')).not.toBeInTheDocument()
  })

  it('refreshes the tracker after guarded baseline acceptance succeeds', async () => {
    const baselineMissing = baselineMissingV2()
    const synchronized = snapshotV2()
    let snapshotLoads = 0
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockImplementation((input: RequestInfo | URL) => {
      if (String(input).endsWith('/evidence')) {
        return Promise.resolve(jsonResponse({ outcome: 'created' }, 201))
      }
      snapshotLoads += 1
      return Promise.resolve(jsonResponse(snapshotLoads === 1 ? baselineMissing : synchronized))
    }))

    render(<NirmanaElevationTracker />)
    fireEvent.click(await screen.findByRole('button', { name: 'Accept current baseline' }))

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3))
    expect(screen.queryByRole('button', { name: 'Accept current baseline' })).not.toBeInTheDocument()
  })

  it('reports accepted baseline truthfully when the authoritative snapshot reload fails', async () => {
    const baselineMissing = baselineMissingV2()
    let snapshotLoads = 0
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockImplementation((input: RequestInfo | URL) => {
      if (String(input).endsWith('/evidence')) {
        return Promise.resolve(jsonResponse({ outcome: 'created' }, 201))
      }
      snapshotLoads += 1
      return Promise.resolve(snapshotLoads === 1
        ? jsonResponse(baselineMissing)
        : jsonResponse(unavailableV2(), 503))
    }))

    render(<NirmanaElevationTracker />)
    fireEvent.click(await screen.findByRole('button', { name: 'Accept current baseline' }))

    expect(await screen.findByText(/baseline was accepted, but current evidence could not refresh/i)).toBeVisible()
    expect(screen.getByRole('button', { name: 'Baseline accepted' })).toBeDisabled()
    expect(screen.queryByText(/refreshing the tracker from authoritative evidence/i)).not.toBeInTheDocument()
  })

  it('renders the v2 campaign spine and keeps the audit surface secondary by default', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV2())))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByRole('heading', { name: /nirmāṇa campaign/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /campaign spine/i })).toBeVisible()
    expect(screen.getByLabelText(/now, next, then campaign rail/i)).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Praśna Rules')).toBeVisible()
    expect(screen.getAllByText('Prashna Rules').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /audit evidence.*degraded/i })).toBeVisible()
    expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /sequential layer rail/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /asset evidence ledger/i })).not.toBeInTheDocument()
  })

  it('shows plan adaptation with observation age and affected assets without replacing the campaign spine', () => {
    const snapshot = snapshotV2()
    snapshot.program_sync = {
      ...snapshot.program_sync,
      status: 'plan_adaptation_required',
      observed_at: '2026-08-26T00:00:00.000Z',
      age_seconds: 180,
      affected_asset_ids: ['bg_prashna_rules', 'ka_smriti'],
    }

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)

    expect(screen.getByText('Program synchronization')).toBeVisible()
    const synchronization = screen.getByText('Plan adaptation required').closest<HTMLElement>('[role="alert"]')
    if (!synchronization) throw new Error('Program synchronization alert is missing.')
    expect(within(synchronization).getByText('Plan adaptation required')).toBeVisible()
    expect(within(synchronization).getByText('Observation age: 3 minutes')).toBeVisible()
    expect(within(synchronization).getByText('Affected assets: 2')).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Praśna Rules')).toBeVisible()
    expect(screen.getAllByText('Prashna Rules').length).toBeGreaterThan(0)
  })

  it('keeps synchronization definition hashes secondary in the audit drawer', () => {
    const snapshot = snapshotV2()
    const currentHash = 'b'.repeat(64)
    const candidateHash = 'c'.repeat(64)
    snapshot.program_sync = {
      ...snapshot.program_sync,
      status: 'plan_adaptation_required',
      current_definition_sha256: currentHash,
      candidate_definition_sha256: candidateHash,
    }

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)

    expect(document.body).not.toHaveTextContent(currentHash)
    expect(document.body).not.toHaveTextContent(candidateHash)
    fireEvent.click(screen.getByRole('button', { name: /audit evidence/i }))

    const drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getByRole('heading', { name: /program synchronization observation/i })).toBeVisible()
    expect(within(drawer).getByText(currentHash)).toBeVisible()
    expect(within(drawer).getByText(candidateHash)).toBeVisible()
  })

  it('selects the temporary v1 evidence view for a schema v1 payload', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV1)))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/tracker upgrade pending — showing schema v1 evidence view/i)).toBeVisible()
    expect(screen.getByRole('heading', { name: /sequential layer rail/i })).toBeVisible()
    expect(screen.getByRole('heading', { name: /asset evidence ledger/i })).toBeVisible()
    expect(screen.queryByRole('heading', { name: /campaign spine/i })).not.toBeInTheDocument()
  })

  it('renders bounded generic text for credential-bearing v1 source errors and asset blockers', () => {
    const unsafeSnapshot = structuredClone(snapshotV1)
    unsafeSnapshot.sources[0] = {
      ...unsafeSnapshot.sources[0],
      state: 'unavailable',
      error: unsafeDatabaseUri,
    }
    unsafeSnapshot.assets[0] = {
      ...unsafeSnapshot.assets[0],
      current_run_state: null,
      blocker: 'run 99999999-9999-4999-8999-999999999999 failed: password=secret-password host=db.private.internal',
      evidence_refs: [],
    }
    unsafeSnapshot.active_runs = []

    render(<NirmanaElevationTrackerView snapshot={unsafeSnapshot} fetchedAt={new Date('2026-08-26T00:00:00.000Z')} />)

    expect(screen.getByText('Authoritative source is unavailable.')).toBeVisible()
    expect(screen.getByText('Accepted asset execution requires attention.')).toBeVisible()
    expect(document.body).not.toHaveTextContent('secret-password')
    expect(document.body).not.toHaveTextContent('db.private.internal')
    expect(document.body).not.toHaveTextContent('99999999-9999-4999-8999-999999999999')
  })

  it('renders only bounded public references for arbitrary schema-v1 evidence refs', () => {
    const unsafeSnapshot = structuredClone(snapshotV1)
    const buildRunId = '11111111-1111-4111-8111-111111111111'
    const digest = 'a'.repeat(64)
    unsafeSnapshot.assets[0].evidence_refs = [
      `run:${buildRunId}`,
      `build_run:${buildRunId}`,
      `sha:${digest}`,
      'stage:T0_CENSUS',
      'foundation:A',
      'event:asset_frozen',
      `receipt:asset_frozen:${buildRunId}`,
      `campaign_event:${buildRunId}`,
      'source:db.private.internal:5432',
      'run:10.0.0.8:5432',
      'sha:not-a-hash',
      'event:tracker_admin',
      'receipt:asset_frozen:private-token',
      unsafeDatabaseUri,
      'https://tracker_admin@db.private.internal/evidence?token=private-token',
      'authorization=Bearer private-token',
      'password=secret-password host=db.private.internal user=tracker_admin',
      '-----BEGIN PRIVATE KEY----- private-key-material -----END PRIVATE KEY-----',
      unsafeGithubToken,
      unsafeOpenAiToken,
      `sha:${'a'.repeat(600)}`,
    ]

    render(<NirmanaElevationTrackerView snapshot={unsafeSnapshot} fetchedAt={new Date('2026-08-26T00:00:00.000Z')} />)

    for (const reference of [
      `run:${buildRunId}`,
      `build_run:${buildRunId}`,
      `sha:${digest}`,
      'stage:T0_CENSUS',
      'foundation:A',
      'event:asset_frozen',
      `receipt:asset_frozen:${buildRunId}`,
      `campaign_event:${buildRunId}`,
    ]) expect(screen.getByText(reference)).toBeInTheDocument()
    expect(screen.getAllByText('redacted:unsafe-reference')).toHaveLength(13)
    expect(document.body).not.toHaveTextContent('secret-password')
    expect(document.body).not.toHaveTextContent('db.private.internal')
    expect(document.body).not.toHaveTextContent('tracker_admin')
    expect(document.body).not.toHaveTextContent('private-token')
    expect(document.body).not.toHaveTextContent('PRIVATE KEY')
    expect(document.body).not.toHaveTextContent(unsafeGithubToken)
    expect(document.body).not.toHaveTextContent(unsafeOpenAiToken)
    expect(document.body).not.toHaveTextContent('a'.repeat(600))
    expect(document.body).not.toHaveTextContent('10.0.0.8')
    expect(document.body).not.toHaveTextContent('not-a-hash')
  })

  it('does not copy a credential-bearing v1 source error into the unavailable banner', async () => {
    const unsafeSnapshot = structuredClone(snapshotV1)
    unsafeSnapshot.sources[0] = {
      ...unsafeSnapshot.sources[0],
      state: 'unavailable',
      error: 'password=secret-password host=db.private.internal run=private-cause',
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(unsafeSnapshot, 503)))

    render(<NirmanaElevationTracker />)

    expect(await screen.findByText(/live snapshot unavailable — authoritative source is unavailable\./i)).toBeVisible()
    expect(document.body).not.toHaveTextContent('secret-password')
    expect(document.body).not.toHaveTextContent('db.private.internal')
    expect(document.body).not.toHaveTextContent('private-cause')
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
      nextResponse: () => jsonResponse(unavailableV2(), 503),
      error: /authoritative source is unavailable/i,
    },
    {
      label: 'malformed response',
      nextResponse: () => jsonResponse({ ...snapshotV2(), stages: [] }),
      error: /did not satisfy the shared evidence contract/i,
    },
  ])('retains the last valid v2 DOM after a focus refresh $label', async ({ nextResponse, error }) => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(jsonResponse(snapshotV2()))
      .mockImplementation(() => Promise.resolve(nextResponse())))

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')

    expect(fetch).toHaveBeenCalledTimes(1)
    act(() => window.dispatchEvent(new Event('focus')))
    expect(fetch).toHaveBeenCalledTimes(2)

    await screen.findByText(/current state unknown/i)

    expect(screen.getByText('Praśna Rules')).toBeVisible()
    const retainedSnapshotAlert = screen.getByText(/current state unknown/i).closest<HTMLElement>('[role="alert"]')
    if (!retainedSnapshotAlert) throw new Error('Retained-snapshot alert is missing.')
    await waitFor(() => expect(retainedSnapshotAlert).toHaveTextContent(error))
    expect(retainedSnapshotAlert).toHaveTextContent(/failure observed/i)
    expect(within(retainedSnapshotAlert).getByRole('time')).toBeVisible()
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
    // The position chip (CampaignSnapshotStrip) now renders `programme.position_label` verbatim
    // instead of re-deriving it from `campaign.current_wave` at render time (Task 4 Step 5,
    // controller ruling on 2026-09-04: authorized one-line fix, file kept out of Task 4's
    // normal scope otherwise). Restamp the label here so it still distinguishes this "later"
    // snapshot from the default fixture — this test's actual subject is unchanged: it verifies
    // only the newest of two in-flight responses replaces the rendered snapshot.
    later.programme = { ...later.programme, position_label: 'L0 · Brahmagyan · Wave 3' }
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
    const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'bg_prashna_rules')!
    asset.execution_obligation = 'unresolved'
    asset.milestones_earned = null
    asset.milestones_required = null

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:00:00.000Z')} />)

    const card = screen.getByText(`System ID: ${asset.asset_id}`).closest('article')
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
    snapshot.assets.find((asset) => asset.asset_id === 'ka_smriti')!.evidence_refs = ['unrelated:ka_smriti']
    const projectedReceipt = snapshot.audit.receipts.find((receipt) => receipt.event_type === 'build_run_authorized')
    if (!projectedReceipt) throw new Error('Server-projected fixture must include a build-run authorization receipt.')

    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    fireEvent.click(screen.getByRole('button', { name: /audit details for bg_prashna_rules/i }))

    const drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getByText('Cloud SQL asset_registry')).toBeVisible()
    expect(within(drawer).getByText('main-abc')).toBeVisible()
    expect(within(drawer).getByText('deployed-def')).toBeVisible()
    expect(within(drawer).getByText('amjis-web-0042')).toBeVisible()
    expect(within(drawer).getByText('Deployed SHA differs from main.')).toBeVisible()
    expect(within(drawer).getByText('campaign_authorization')).toBeVisible()
    expect(within(drawer).getByText('build_run_authorized')).toBeVisible()
    expect(within(drawer).getAllByText(projectedReceipt.ledger_ref).length).toBeGreaterThan(0)
    expect(within(drawer).getByText(projectedReceipt.payload_sha256)).toBeVisible()
    expect(within(drawer).getAllByText('build_run:33333333-3333-4333-8333-333333333333').length).toBeGreaterThan(0)
    expect(within(drawer).queryByText('unrelated:ka_smriti')).not.toBeInTheDocument()

    fireEvent.click(within(drawer).getByRole('button', { name: /close audit drawer/i }))
    expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument()
  })

  it('opens the global audit by keyboard, contains Tab focus, and restores focus after Escape', async () => {
    const user = userEvent.setup()
    render(<NirmanaElevationTrackerView snapshot={snapshotV2()} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    const trigger = screen.getByRole('button', { name: /audit evidence.*degraded/i })

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
    snapshot.assets.find((asset) => asset.asset_id === 'ka_smriti')!.evidence_refs = ['unrelated:ka_smriti']
    render(<NirmanaElevationTrackerView snapshot={snapshot} fetchedAt={new Date('2026-08-26T00:03:00.000Z')} />)
    const assetTrigger = screen.getByRole('button', { name: /audit details for bg_prashna_rules/i })

    assetTrigger.focus()
    await user.keyboard('{Enter}')
    let drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getAllByText('build_run:33333333-3333-4333-8333-333333333333').length).toBeGreaterThan(0)
    expect(within(drawer).queryByText('unrelated:ka_smriti')).not.toBeInTheDocument()
    expect(within(drawer).queryByText('build_run:11111111-1111-4111-8111-111111111111')).not.toBeInTheDocument()

    const close = within(drawer).getByRole('button', { name: /close audit drawer/i })
    close.focus()
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.queryByRole('dialog', { name: /campaign evidence audit/i })).not.toBeInTheDocument())
    expect(assetTrigger).toHaveFocus()

    const globalTrigger = screen.getByRole('button', { name: /audit evidence.*degraded/i })
    globalTrigger.focus()
    await user.keyboard('{Enter}')
    drawer = screen.getByRole('dialog', { name: /campaign evidence audit/i })
    expect(within(drawer).getAllByText('build_run:33333333-3333-4333-8333-333333333333').length).toBeGreaterThan(0)
    expect(within(drawer).getByText('unrelated:ka_smriti')).toBeVisible()
    expect(within(drawer).getAllByText('build_run:11111111-1111-4111-8111-111111111111').length).toBeGreaterThan(0)
  })

  it('subscribes to the chart-scoped cockpit SSE bus on mount', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(snapshotV2())))

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')

    expect(MockEventSource.instances).toHaveLength(1)
    expect(MockEventSource.instances[0].url).toContain('chart_id=482012f1-710e-4a25-994a-93821f5871aa')
  })

  it('debounces an SSE event into exactly one additional snapshot refetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(snapshotV2()))
    vi.stubGlobal('fetch', fetchMock)

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')
    const callsAfterMount = fetchMock.mock.calls.length
    const source = MockEventSource.instances[0]

    vi.useFakeTimers()
    act(() => { source.emit('run.state_change') })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount)

    await act(async () => { await vi.advanceTimersByTimeAsync(2_000) })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount + 1)
  })

  it('debounces a nirmana.evidence_accepted SSE event into exactly one additional snapshot refetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(snapshotV2()))
    vi.stubGlobal('fetch', fetchMock)

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')
    const callsAfterMount = fetchMock.mock.calls.length
    const source = MockEventSource.instances[0]

    vi.useFakeTimers()
    act(() => { source.emit('nirmana.evidence_accepted') })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount)

    await act(async () => { await vi.advanceTimersByTimeAsync(2_000) })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount + 1)
  })

  it('coalesces a burst of SSE events within the debounce window into one refetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(snapshotV2()))
    vi.stubGlobal('fetch', fetchMock)

    render(<NirmanaElevationTracker />)
    await screen.findByText('Praśna Rules')
    const callsAfterMount = fetchMock.mock.calls.length
    const source = MockEventSource.instances[0]

    vi.useFakeTimers()
    act(() => { source.emit('run.state_change') })
    act(() => { source.emit('asset.state_change') })
    act(() => { source.emit('nirmana.evidence_accepted') })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount)

    await act(async () => { await vi.advanceTimersByTimeAsync(2_000) })
    expect(fetchMock.mock.calls.length).toBe(callsAfterMount + 1)
  })
})
