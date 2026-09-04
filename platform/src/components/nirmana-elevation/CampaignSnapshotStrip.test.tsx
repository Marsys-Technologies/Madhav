import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { CampaignSnapshotStrip } from './CampaignSnapshotStrip'

function unknownObservationSnapshot(): NirmanaElevationSnapshotV2 {
  const snapshot = structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
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
  snapshot.campaign.current_stage = null
  snapshot.campaign.current_layer = null
  snapshot.active_runs = []
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  if (!monitor) throw new Error('Fixture must include the program monitor source.')
  Object.assign(monitor, { state: 'unknown', observed_at: null, age_seconds: null })
  return snapshot
}

describe('CampaignSnapshotStrip', () => {
  it('distinguishes page refresh from an absent synchronization observation', () => {
    render(<CampaignSnapshotStrip snapshot={unknownObservationSnapshot()} />)

    const strip = screen.getByRole('region', { name: /nirmāṇa campaign/i })
    expect(within(strip).getByText(/snapshot refreshed/i)).toBeVisible()
    expect(within(strip).queryByText(/^Observed /)).not.toBeInTheDocument()
    expect(within(strip).getByText('Unknown — monitor not observed')).toBeVisible()
    expect(within(strip).getByText('Affected assets: Unknown')).toBeVisible()
  })

  it('renders the current-position metric as the programme-derived position label verbatim', () => {
    // The position chip no longer re-derives its text from `campaign.current_stage`/
    // `current_wave` — it renders `snapshot.programme.position_label` as-is. That
    // derivation is Task 2's `projectProgrammePosition` unit-test surface, not this
    // component test's job, so the fixture just declares the label directly.
    const snapshot = structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
    snapshot.programme = {
      ...snapshot.programme,
      position_label: 'O-WAVE · WP-2 · L0 · W3 (3/4 built_or_dispositioned)',
    }

    render(<CampaignSnapshotStrip snapshot={snapshot} />)

    const strip = screen.getByRole('region', { name: /nirmāṇa campaign/i })
    expect(within(strip).getByText('O-WAVE · WP-2 · L0 · W3 (3/4 built_or_dispositioned)')).toBeVisible()
  })
})
