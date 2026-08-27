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
})
