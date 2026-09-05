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

/** Opens the collapsed "Stage-machine history" `<details>` so its preserved legacy rows become reachable by `.toBeVisible()` assertions (jest-dom treats non-summary content of a closed `<details>` as invisible). */
function openHistory() {
  fireEvent.click(screen.getByText('Stage-machine history (13-stage record + Phase A drawer)'))
}

describe('CampaignSpine', () => {
  it('renders the executive truth, current stage, and every governed stage in sequence', () => {
    // `programme.position_label` is now the sole source for the position chip (Step 5); its
    // derivation is covered by Task 2's `projectProgrammePosition` unit tests, not here — this
    // fixture value is set directly so this test's job stays "does the chip render the field".
    const snapshot = snapshotFixture()
    snapshot.programme.position_label = 'L0 · Brahmagyan · Wave 2'

    render(<CampaignSurface snapshot={snapshot} />)

    expect(screen.getByText('L0 · Brahmagyan · Wave 2')).toBeVisible()
    expect(screen.getByText('3 / 5')).toBeVisible()
    expect(screen.getByText('Unknown — monitor not observed')).toBeVisible()
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('button', { name: /L1 · Ganita/i })).toHaveAttribute('aria-expanded', 'false')
    // The full 13-stage record now lives inside the collapsed history drawer (Ruling R2 —
    // per-layer state moved to the six always-visible LayerCards). Open the drawer, then
    // PHASE A and PHASE Z's own collapsed summary rows, before counting every
    // individually-rendered stage button — this also implicitly covers the six LayerCard
    // toggle buttons, since their names ("L0 · Brahmagyan", …) match the same `L[0-5]` pattern.
    openHistory()
    fireEvent.click(screen.getByRole('button', { name: /^PHASE A/i }))
    fireEvent.click(screen.getByRole('button', { name: /^PHASE Z/i }))
    expect(screen.getAllByRole('button', { name: /BOOTSTRAP|T0_CENSUS|PLAN_FROZEN|DENOMINATOR_FROZEN|F0_FOUNDATION|L[0-5]|CLOSING|COMPLETE/ })).toHaveLength(13)
  })

  it('keeps denominator reconciliation and an unknown current position explicit', () => {
    const snapshot = snapshotFixture()
    snapshot.progress.denominator_status = 'reconciling'
    snapshot.progress.assets_total = null
    snapshot.campaign.current_stage = null
    snapshot.campaign.current_layer = null
    snapshot.campaign.current_wave = null
    // See the note in the previous test: the position chip now renders `programme.position_label`
    // verbatim, so this fixture must declare the unknown-position copy directly.
    snapshot.programme.position_label = 'Execution not yet evidenced'

    render(<CampaignSurface snapshot={snapshot} />)

    expect(screen.getByText('Reconciling — no percentage')).toBeVisible()
    expect(screen.getAllByText('Execution not yet evidenced')).toHaveLength(2)
    expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
  })

  it('withholds stage counts when the stage itself is not evidenced', () => {
    const snapshot = snapshotFixture()
    const foundation = snapshot.stages.find((stage) => stage.stage_id === 'F0_FOUNDATION')
    if (!foundation) throw new Error('Fixture must include the foundation stage.')
    foundation.state = 'unknown'
    foundation.earned = 0
    foundation.required = 5

    render(<CampaignSurface snapshot={snapshot} />)
    openHistory()
    fireEvent.click(screen.getByRole('button', { name: /^PHASE A/i }))

    expect(screen.getByRole('button', { name: /F0 · Foundation readiness/i })).toBeVisible()
    expect(screen.queryByText('0 / 5')).not.toBeInTheDocument()
  })

  it('withholds a frozen numeric denominator until the accepted campaign spine exists', () => {
    const snapshot = snapshotFixture()
    snapshot.progress.denominator_status = 'frozen'
    snapshot.progress.assets_frozen = 0
    snapshot.progress.assets_total = 128
    snapshot.campaign.current_stage = 'BOOTSTRAP'
    snapshot.campaign.current_layer = null
    snapshot.campaign.current_wave = null
    const denominatorStage = snapshot.stages.find((stage) => stage.stage_id === 'DENOMINATOR_FROZEN')
    if (!denominatorStage) throw new Error('Fixture must include the denominator stage.')
    denominatorStage.state = 'locked'
    denominatorStage.completed_at = null

    render(<CampaignSurface snapshot={snapshot} />)

    // Fix 6: reworded so this stage-machine-ceremony fact reads as visibly distinct from
    // ProgrammeOverview's v2.1 asset-milestone bar, which renders the same "unavailable
    // denominator" moment as a real percentage instead.
    expect(screen.getByText('Stage-machine denominator ceremony: not accepted')).toBeVisible()
    expect(screen.queryByText('0 / 128')).not.toBeInTheDocument()
  })

  it('uses human plan labels for T0 and F0 while retaining exact stage ids as secondary metadata', () => {
    render(<CampaignSurface snapshot={snapshotFixture()} />)
    openHistory()
    fireEvent.click(screen.getByRole('button', { name: /^PHASE A/i }))

    expect(screen.getByRole('button', { name: /T0 · Asset and DAG census/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /F0 · Foundation readiness/i })).toBeVisible()
    expect(screen.getByText('Stage ID: T0_CENSUS')).toBeVisible()
    expect(screen.getByText('Stage ID: F0_FOUNDATION')).toBeVisible()
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
      supersession_eligible: false,
      supersession_blockers: [],
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
    expect(within(synchronization).getByText('Affected assets: Unknown')).toBeVisible()
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
      supersession_eligible: false,
      supersession_blockers: [],
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
    expect(within(now).getByText('F0 · Foundation readiness')).toBeVisible()
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
    openHistory()
    fireEvent.click(screen.getByRole('button', { name: /^PHASE A/i }))

    const foundationButton = screen.getByRole('button', { name: /F0_FOUNDATION/i })
    expect(foundationButton).toHaveAttribute('aria-expanded', 'false')
    foundationButton.focus()
    fireEvent.keyDown(foundationButton, { key: 'Enter' })
    expect(foundationButton).toHaveAttribute('aria-expanded', 'true')

    // The overall bar and six LayerCards legitimately render real percentages elsewhere on the
    // page now — this assertion's actual job (per its name) is that THIS specific unknown-data
    // panel never fabricates one of its own, so it is scoped to F0_FOUNDATION's own panel.
    const panelId = foundationButton.getAttribute('aria-controls')
    const panel = panelId ? document.getElementById(panelId) : null
    if (!panel) throw new Error("F0_FOUNDATION's expanded panel is missing.")
    expect(within(panel).getByText('Asset and DAG census')).toBeVisible()
    expect(within(panel).getByText(/Unknown — acceptance checkpoints are not recorded/i)).toBeVisible()
    expect(within(panel).queryByText(/%/)).not.toBeInTheDocument()
  })

  it('renders the O-Wave declared row (all WPs merged) and provenance chips beside the collapsed Phase A/Z summaries', () => {
    const snapshot = snapshotFixture()

    render(<CampaignSurface snapshot={snapshot} />)
    openHistory()

    expect(screen.getByRole('heading', { name: 'O-WAVE' })).toBeVisible()
    const oWaveSection = screen.getByRole('heading', { name: 'O-WAVE' }).closest('article')
    if (!oWaveSection) throw new Error('O-Wave section is missing.')
    expect(snapshot.programme.o_wave.wps.length).toBeGreaterThan(0)
    for (const wp of snapshot.programme.o_wave.wps) {
      // Ruling R3: the O-wave race is over — all three WPs are stable, merged history.
      expect(wp.status).toBe('merged')
      expect(within(oWaveSection).getByText(`${wp.name}: ${wp.status}`)).toBeVisible()
    }
    expect(within(oWaveSection).getByText('Repo-declared')).toBeVisible()

    const phaseAButton = screen.getByRole('button', { name: /^PHASE A/i })
    expect(within(phaseAButton).getByText('Evidence-derived')).toBeVisible()
    const phaseZButton = screen.getByRole('button', { name: /^PHASE Z/i })
    expect(within(phaseZButton).getByText('Evidence-derived')).toBeVisible()
  })

  it('keeps the sequential stage-machine record inside a collapsed-by-default history drawer that opens to the preserved legacy rows', () => {
    const snapshot = snapshotFixture()

    render(<CampaignSurface snapshot={snapshot} />)

    const summary = screen.getByText('Stage-machine history (13-stage record + Phase A drawer)')
    expect(summary.closest('details')).not.toHaveAttribute('open')
    // Closed by default: the legacy per-stage record is not the first thing a viewer sees —
    // the overall bar and six concurrent layer cards are (Ruling R2).
    expect(screen.queryByRole('button', { name: /^PHASE A/i })).not.toBeVisible()

    openHistory()

    expect(summary.closest('details')).toHaveAttribute('open')
    fireEvent.click(screen.getByRole('button', { name: /^PHASE A/i }))
    expect(screen.getByRole('button', { name: /BOOTSTRAP/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /T0 · Asset and DAG census/i })).toBeVisible()
  })

  it('renders all six layer cards concurrently, never labeling a layer as locked', () => {
    const snapshot = snapshotFixture()

    render(<CampaignSurface snapshot={snapshot} />)

    expect(snapshot.layers.map((layer) => layer.layer_id)).toEqual(['L0', 'L1', 'L2', 'L3', 'L4', 'L5'])
    for (const layer of snapshot.layers) {
      const toggle = screen.getByRole('button', { name: new RegExp(`^${layer.layer_id} · ${layer.layer_name}`) })
      expect(toggle).toBeVisible()
      // Scope to the toggle button itself (header + state badge) rather than the whole card —
      // an expanded card's body reuses the legacy "Asset state legend" (Frozen/Active/…/Locked/
      // Unknown), which legitimately describes per-ASSET states and would otherwise collide.
      const badge = within(toggle).getByText(/^(Completed|Active|Pending|Unknown)$/)
      expect(badge).toBeVisible()
      expect(within(toggle).queryByText('Locked')).not.toBeInTheDocument()
    }
  })

  it("keeps L0's programme sub-wave progress visible on its always-shown card summary, defaulting open", () => {
    const snapshot = snapshotFixture()
    const l0Layer = snapshot.layers.find((layer) => layer.layer_id === 'L0')
    if (!l0Layer) throw new Error('Fixture must include L0.')

    render(<CampaignSurface snapshot={snapshot} />)

    const l0Button = screen.getByRole('button', { name: /L0 · Brahmagyan/i })
    expect(l0Button).toHaveAttribute('aria-expanded', 'true')
    const card = l0Button.closest('article')
    if (!card) throw new Error("L0's card is missing.")
    // The WaveProgressBar is part of LayerCard's always-visible summary now (not gated behind
    // expansion) — every layer's cumulative sub-wave breakdown is visible at a glance.
    const subWaveProgress = within(card).getByLabelText(/programme sub-wave progress/i)
    for (const wave of l0Layer.wave_progress) {
      expect(within(subWaveProgress).getByText(wave.wave_id)).toBeVisible()
      expect(within(subWaveProgress).getByText(wave.label)).toBeVisible()
    }
  })
})
