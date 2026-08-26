import { createRef } from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { CampaignSnapshotStrip } from './CampaignSnapshotStrip'
import { CampaignSpine } from './CampaignSpine'
import { NowNextRail } from './NowNextRail'
import { AuditDrawer } from './AuditDrawer'

function snapshotFixture(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

function CampaignSurface({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  return <main>
    <CampaignSnapshotStrip snapshot={snapshot} />
    <NowNextRail snapshot={snapshot} />
    <CampaignSpine snapshot={snapshot} />
  </main>
}

describe('CampaignSpine', () => {
  it('renders the executive truth, current stage, and every governed stage in sequence', () => {
    render(<CampaignSurface snapshot={snapshotFixture()} />)

    expect(screen.getByText('L0 · Brahmagyan · Wave 2')).toBeVisible()
    expect(screen.getByText('3 / 5')).toBeVisible()
    expect(screen.getByText(/1 asset active/i)).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('button', { name: /L1 · Ganita/i })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getAllByRole('button', { name: /BOOTSTRAP|T0_CENSUS|PLAN_FROZEN|DENOMINATOR_FROZEN|F0_FOUNDATION|L[0-5]|CLOSING|COMPLETE/ })).toHaveLength(13)
  })

  it('keeps denominator reconciliation and an unknown current position explicit', () => {
    const snapshot = snapshotFixture()
    snapshot.progress.denominator_status = 'reconciling'
    snapshot.progress.assets_total = null
    snapshot.campaign.current_stage = null
    snapshot.campaign.current_layer = null
    snapshot.campaign.current_wave = null

    render(<CampaignSurface snapshot={snapshot} />)

    expect(screen.getByText('Reconciling — no percentage')).toBeVisible()
    expect(screen.getByText('Current position unknown')).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'false')
  })

  it('distinguishes a not-yet-observed synchronization state from source failure', () => {
    const snapshot = snapshotFixture()
    snapshot.program_sync = {
      status: 'unknown',
      source_observation_id: null,
      observed_at: null,
      age_seconds: null,
      affected_asset_ids: [],
      current_definition_sha256: null,
      candidate_definition_sha256: null,
      candidate_catalogue_sha256: null,
    }
    const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
    if (!monitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(monitor, {
      state: 'unknown',
      observed_at: null,
      age_seconds: null,
      error_code: null,
      error_message: null,
    })

    render(<CampaignSurface snapshot={snapshot} />)

    const synchronization = screen.getByText('Synchronization not yet observed').closest<HTMLElement>('[role="alert"]')
    if (!synchronization) throw new Error('Unknown synchronization live region is missing.')
    expect(within(synchronization).getByText('Observation age: Unknown')).toBeVisible()
    expect(within(synchronization).getByText('Affected assets: 0')).toBeVisible()
    expect(within(synchronization).queryByText('Source unavailable')).not.toBeInTheDocument()
  })

  it('distinguishes release reconciliation from evidence refresh using release-divergence evidence', () => {
    const snapshot = snapshotFixture()
    const definitionHash = 'd'.repeat(64)
    snapshot.program_sync = {
      status: 'release_attention',
      source_observation_id: null,
      observed_at: '2026-08-26T00:02:00.000Z',
      age_seconds: 60,
      affected_asset_ids: [],
      current_definition_sha256: definitionHash,
      candidate_definition_sha256: definitionHash,
      candidate_catalogue_sha256: null,
    }
    snapshot.release = {
      main_sha: 'a'.repeat(40),
      deployed_sha: 'b'.repeat(40),
      deployed_revision: 'amjis-web-release-divergence',
      production_in_sync: false,
      observed_at: '2026-08-26T00:02:00.000Z',
    }
    snapshot.data_quality = {
      verdict: 'degraded',
      gaps: ['Program release reconciliation requires attention.'],
      contradictions: ['Deployed SHA differs from main.'],
    }
    const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
    if (!monitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(monitor, {
      state: 'fresh',
      observed_at: snapshot.program_sync.observed_at,
      age_seconds: snapshot.program_sync.age_seconds,
      error_code: null,
      error_message: null,
    })

    render(<CampaignSurface snapshot={snapshot} />)

    const synchronization = screen.getByText('Release reconciliation required').closest<HTMLElement>('[role="alert"]')
    if (!synchronization) throw new Error('Release-reconciliation live region is missing.')
    expect(within(synchronization).getByText('Observation age: 1 minute')).toBeVisible()
    expect(within(synchronization).getByText('Affected assets: 0')).toBeVisible()
    expect(within(synchronization).queryByText('Evidence refresh required')).not.toBeInTheDocument()
  })

  it('shows the exact source observation identity with the candidate digests in the audit drawer only', () => {
    const snapshot = snapshotFixture()
    const sourceObservationId = '30303030-3030-4030-8030-303030303030'
    const candidateDigest = 'c'.repeat(64)
    snapshot.program_sync = {
      ...snapshot.program_sync,
      source_observation_id: sourceObservationId,
      candidate_catalogue_sha256: candidateDigest,
    }

    render(<AuditDrawer snapshot={snapshot} assetId={null} open onOpenChange={() => {}} finalFocus={createRef<HTMLElement>()} />)

    expect(screen.getByText(sourceObservationId)).toBeInTheDocument()
    expect(screen.getByText(`Candidate label catalogue: ${candidateDigest}`)).toBeInTheDocument()
  })

  it.each([
    ['baseline_missing', 'Baseline awaiting acceptance'],
    ['plan_adaptation_required', 'Plan adaptation required'],
    ['evidence_refresh_required', 'Evidence refresh required'],
    ['label_refresh_required', 'Label catalogue refresh required'],
    ['in_sync', 'In sync'],
    ['source_unavailable', 'Source unavailable'],
  ] as const)('renders %s with the required plain-language synchronization copy', (status, copy) => {
    const snapshot = snapshotFixture()
    snapshot.data_quality = { verdict: 'reliable', gaps: [], contradictions: [] }
    snapshot.program_sync = {
      ...snapshot.program_sync,
      status,
      observed_at: '2026-08-26T00:02:00.000Z',
      age_seconds: 60,
      affected_asset_ids: ['bg_prashna_rules'],
    }
    const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
    if (!monitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(monitor, {
      state: status === 'source_unavailable' ? 'unavailable' : 'fresh',
      observed_at: snapshot.program_sync.observed_at,
      age_seconds: snapshot.program_sync.age_seconds,
    })

    render(<CampaignSurface snapshot={snapshot} />)

    expect(screen.getByText('Program synchronization')).toBeVisible()
    const synchronization = screen.getByText(copy).closest<HTMLElement>('[role]')
    if (!synchronization) throw new Error('Program synchronization live region is missing.')
    expect(within(synchronization).getByText(copy)).toBeVisible()
    expect(within(synchronization).getByText('Observation age: 1 minute')).toBeVisible()
    expect(within(synchronization).getByText('Affected assets: 1')).toBeVisible()
    expect(synchronization).toHaveAttribute('role', status === 'in_sync' || status === 'baseline_missing' ? 'status' : 'alert')
  })

  it('marks a stale in-sync observation as an alert without presenting quiet execution as an error', () => {
    const stale = snapshotFixture()
    stale.data_quality = { verdict: 'reliable', gaps: [], contradictions: [] }
    stale.program_sync = {
      ...stale.program_sync,
      status: 'in_sync',
      observed_at: '2026-08-26T00:00:00.000Z',
      age_seconds: 901,
      affected_asset_ids: [],
    }
    const staleMonitor = stale.sources.find((source) => source.source_id === 'program_monitor')
    if (!staleMonitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(staleMonitor, { state: 'stale', observed_at: stale.program_sync.observed_at, age_seconds: 901 })

    const { rerender } = render(<CampaignSurface snapshot={stale} />)

    let synchronization = screen.getByText(/observation stale/i).closest<HTMLElement>('[role="alert"]')
    if (!synchronization) throw new Error('Stale synchronization alert is missing.')
    expect(within(synchronization).getByText('In sync')).toBeVisible()
    expect(within(synchronization).getByText(/observation stale/i)).toBeVisible()

    const quiet = snapshotFixture()
    quiet.data_quality = { verdict: 'reliable', gaps: [], contradictions: [] }
    quiet.program_sync = {
      ...quiet.program_sync,
      status: 'in_sync',
      observed_at: '2026-08-26T00:02:00.000Z',
      age_seconds: 60,
      affected_asset_ids: [],
    }
    const quietMonitor = quiet.sources.find((source) => source.source_id === 'program_monitor')
    if (!quietMonitor) throw new Error('Fixture must include the program monitor source.')
    Object.assign(quietMonitor, { state: 'fresh', observed_at: quiet.program_sync.observed_at, age_seconds: 60 })
    rerender(<CampaignSurface snapshot={quiet} />)

    synchronization = screen.getByText('No program change detected.').closest<HTMLElement>('[role="status"]')
    if (!synchronization) throw new Error('Quiet synchronization status is missing.')
    expect(within(synchronization).getByText('In sync')).toBeVisible()
    expect(within(synchronization).queryByText(/error|failed|stale/i)).not.toBeInTheDocument()
    expect(within(screen.getByLabelText('Now, next, then campaign rail')).getByText('No current attention receipt')).toBeVisible()
  })

  it('keeps a known F0 current stage in the rail without inventing a current layer', () => {
    const snapshot = snapshotFixture()
    snapshot.campaign.current_stage = 'F0_FOUNDATION'
    snapshot.campaign.current_layer = null
    snapshot.campaign.current_wave = null

    render(<CampaignSurface snapshot={snapshot} />)

    const rail = screen.getByLabelText('Now, next, then campaign rail')
    const now = within(rail).getByText('Now').closest('section')
    if (!now) throw new Error('Now rail section is missing.')
    expect(within(now).getByText('F0_FOUNDATION')).toBeVisible()
    expect(within(now).queryByText('Unknown current stage')).not.toBeInTheDocument()
  })

  it('labels active-layer eligibility as eligible now and keeps the gate as a separate prerequisite', () => {
    render(<CampaignSurface snapshot={snapshotFixture()} />)

    const strip = screen.getByRole('region', { name: /nirmāṇa campaign/i })
    expect(within(strip).getByText('Eligible now')).toBeVisible()
    expect(within(strip).getByText('1 asset eligible now')).toBeVisible()
    expect(within(strip).getByText('Completion prerequisite: L0 assets frozen')).toBeVisible()

    const rail = screen.getByLabelText('Now, next, then campaign rail')
    const eligible = within(rail).getByText('Eligible now').closest('section')
    if (!eligible) throw new Error('Eligible-now rail section is missing.')
    expect(within(eligible).getByText('1 asset eligible now')).toBeVisible()
    expect(within(eligible).getByText('Completion prerequisite: L0 assets frozen')).toBeVisible()
    expect(within(eligible).queryByText(/eligible after gate/i)).not.toBeInTheDocument()
  })

  it('toggles stages with the keyboard and reports unknown F0 lanes without a fabricated percentage', () => {
    const snapshot = snapshotFixture()
    const foundation = snapshot.stages.find((stage) => stage.stage_id === 'F0_FOUNDATION')
    if (!foundation?.foundation_lanes) throw new Error('Fixture must include foundation lanes.')
    foundation.state = 'unknown'
    foundation.earned = null
    foundation.required = null
    foundation.foundation_lanes[0] = {
      ...foundation.foundation_lanes[0],
      state: 'unknown',
      completed_at: null,
    }

    render(<CampaignSurface snapshot={snapshot} />)

    const foundationButton = screen.getByRole('button', { name: /F0_FOUNDATION/i })
    expect(foundationButton).toHaveAttribute('aria-expanded', 'false')
    foundationButton.focus()
    fireEvent.keyDown(foundationButton, { key: 'Enter' })
    expect(foundationButton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Asset and DAG census')).toBeVisible()
    expect(screen.getByText(/Unknown — acceptance checkpoints are not recorded/i)).toBeVisible()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })
})
