import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { CampaignSnapshotStrip } from './CampaignSnapshotStrip'
import { CampaignSpine } from './CampaignSpine'
import { NowNextRail } from './NowNextRail'

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
