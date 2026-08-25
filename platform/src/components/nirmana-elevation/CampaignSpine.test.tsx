import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { CampaignSnapshotStrip } from './CampaignSnapshotStrip'
import { CampaignSpine } from './CampaignSpine'
import { NowNextRail } from './NowNextRail'

function snapshotFixture(): NirmanaElevationSnapshotV2 {
  const snapshot = structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
  snapshot.progress.assets_frozen = 18
  snapshot.layers[0].waves[0].active_asset_ids = ['bg_prashna_rules', 'bg_sign_medical', 'bg_chart_service']
  snapshot.active_runs = [{
    ...snapshot.active_runs[0],
    active_asset_ids: ['bg_prashna_rules', 'bg_sign_medical', 'bg_chart_service'],
  }]
  return snapshot
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
    expect(screen.getByText('18 / 128')).toBeVisible()
    expect(screen.getByText(/3 assets active/i)).toBeVisible()
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
