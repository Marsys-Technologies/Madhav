import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { LayerStage } from './LayerStage'

function snapshotFixture(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

function layerFixture(snapshot: NirmanaElevationSnapshotV2) {
  const layer = snapshot.layers.find((candidate) => candidate.layer_id === 'L3')
  if (!layer) throw new Error('Fixture must include L3.')

  return layer
}

describe('LayerStage', () => {
  it('renders accessible layer progress, the state legend, eligible preview, and collapsed completed waves', () => {
    const snapshot = snapshotFixture()
    const layer = snapshot.layers.find((candidate) => candidate.layer_id === 'L0')
    if (!layer) throw new Error('Fixture must include L0.')

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={vi.fn()} waveProgress={layer.wave_progress} />)

    const progress = screen.getByRole('progressbar', { name: /L0 · Brahmagyan layer progress/i })
    expect(progress).toHaveAttribute('aria-valuenow', String(layer.frozen))
    expect(progress).toHaveAttribute('aria-valuemax', String(layer.assets_total))
    expect(screen.getByText(`${layer.frozen} / ${layer.assets_total} assets frozen`)).toBeVisible()
    const subWaveProgress = screen.getByLabelText(/programme sub-wave progress/i)
    for (const waveId of ['W1', 'W2', 'W3', 'W4', 'W5', 'W6']) {
      expect(within(subWaveProgress).getByText(waveId)).toBeVisible()
    }
    const legend = screen.getByLabelText(/asset state legend/i)
    for (const label of ['Frozen', 'Active', 'Blocked', 'Eligible next', 'Locked', 'Unknown']) {
      expect(within(legend).getByText(label)).toBeVisible()
    }
    expect(screen.getByText(/eligible-next preview/i)).toBeVisible()
    expect(within(screen.getByLabelText(/eligible-next preview/i)).getByText('(bg_prashna_rules)')).toBeVisible()
    const completedSummary = screen.getByText(/Wave 0.*completed/i)
    expect(completedSummary.closest('details')).not.toHaveAttribute('open')
  })

  it('uses indeterminate copy when layer progress has not been observed', () => {
    const snapshot = snapshotFixture()
    const layer = snapshot.layers.find((candidate) => candidate.layer_id === 'L0')
    if (!layer) throw new Error('Fixture must include L0.')
    Object.assign(layer, { state: 'unknown', assets_total: null, frozen: 0, waves: [] })

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={vi.fn()} waveProgress={layer.wave_progress} />)

    expect(screen.getByText(`Required gate: ${layer.required_gate}`)).toBeVisible()
    expect(screen.getByText('Progress unknown — no layer total has been observed.')).toBeVisible()
    expect(screen.queryByText('0 assets frozen; layer total is unknown')).not.toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: /L0 · Brahmagyan layer progress/i })).toHaveAttribute('aria-valuetext', 'Progress unknown — no layer total has been observed.')
  })

  it('keeps locked waves collapsed and limits a wave to two parallel asset columns', () => {
    const snapshot = snapshotFixture()
    const layer = layerFixture(snapshot)

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={vi.fn()} waveProgress={layer.wave_progress} />)

    const lockedSummary = screen.getByText(/Wave 0.*locked/i)
    expect(lockedSummary.closest('details')).not.toHaveAttribute('open')
    fireEvent.click(lockedSummary)
    const wave = screen.getByRole('group', { name: 'Wave 0' })
    expect(wave.querySelector('.xl\\:grid-cols-3')).not.toBeInTheDocument()
    expect(wave.querySelector('.lg\\:grid-cols-2')).toBeInTheDocument()
  })

  it('stacks waves in numeric order and keeps parallel assets within their labelled wave', () => {
    const snapshot = snapshotFixture()
    const layer = layerFixture(snapshot)
    const kaSmriti = snapshot.assets.find((asset) => asset.asset_id === 'ka_smriti')
    if (!kaSmriti) throw new Error('Fixture must include ka_smriti.')

    const waveOne = { ...kaSmriti, asset_id: 'ka_wave_one', wave_index: 1, sanskrit_name: 'Kāla One', english_name: 'Kala One', description: 'First wave asset' }
    const waveTwo = { ...kaSmriti, asset_id: 'ka_wave_two_a', wave_index: 2, sanskrit_name: 'Kāla Two A', english_name: 'Kala Two A', description: 'Second wave asset A' }
    const waveTwoSibling = { ...kaSmriti, asset_id: 'ka_wave_two_b', wave_index: 2, sanskrit_name: 'Kāla Two B', english_name: 'Kala Two B', description: 'Second wave asset B' }
    const waveThree = { ...kaSmriti, asset_id: 'ka_wave_three', wave_index: 3, sanskrit_name: 'Kāla Three', english_name: 'Kala Three', description: 'Third wave asset' }
    snapshot.assets = [waveThree, waveTwoSibling, waveOne, waveTwo] as NirmanaElevationSnapshotV2['assets']
    layer.waves = [
      { wave_index: 3, state: 'locked', asset_ids: ['ka_wave_three'], completed_asset_ids: [], active_asset_ids: [], blocked_asset_ids: [], locked_asset_ids: ['ka_wave_three'], unknown_asset_ids: [], eligible_next_asset_ids: [] },
      { wave_index: 2, state: 'active', asset_ids: ['ka_wave_two_a', 'ka_wave_two_b'], completed_asset_ids: [], active_asset_ids: ['ka_wave_two_a'], blocked_asset_ids: [], locked_asset_ids: [], unknown_asset_ids: ['ka_wave_two_b'], eligible_next_asset_ids: ['ka_wave_two_b'] },
      { wave_index: 1, state: 'completed', asset_ids: ['ka_wave_one'], completed_asset_ids: ['ka_wave_one'], active_asset_ids: [], blocked_asset_ids: [], locked_asset_ids: [], unknown_asset_ids: [], eligible_next_asset_ids: [] },
    ]

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={vi.fn()} waveProgress={layer.wave_progress} />)

    fireEvent.click(screen.getByText(/Wave 1.*completed/i))
    fireEvent.click(screen.getByText(/Wave 3.*locked/i))
    expect(screen.getAllByRole('group', { name: /wave [123]/i }).map((element) => element.getAttribute('aria-label'))).toEqual(['Wave 1', 'Wave 2', 'Wave 3'])
    const waveTwoGroup = screen.getByRole('group', { name: 'Wave 2' })
    expect(within(waveTwoGroup).getByText('System ID: ka_wave_two_a')).toBeVisible()
    expect(within(waveTwoGroup).getByText('System ID: ka_wave_two_b')).toBeVisible()
    expect(within(waveTwoGroup).queryByText('System ID: ka_wave_three')).not.toBeInTheDocument()
    expect(within(screen.getByRole('group', { name: 'Wave 3' })).getByText(`Locked by: ${layer.required_gate}`)).toBeVisible()
  })

  it('renders canonical bilingual identity, a truthful missing state, and secondary legacy aliases', () => {
    const snapshot = snapshotFixture()
    const layer = layerFixture(snapshot)
    const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'ka_smriti')
    if (!asset) throw new Error('Fixture must include ka_smriti.')
    asset.legacy_aliases = asset.legacy_aliases.map((alias) => ({ ...alias, english_name: 'Year-by-year digest' }))
    const incomplete = { ...asset, asset_id: 'ka_uncatalogued', sanskrit_name: null, english_name: 'Uncatalogued asset', description: null, legacy_aliases: [], identity_quality: 'incomplete' as const }
    snapshot.assets = [asset, incomplete] as NirmanaElevationSnapshotV2['assets']
    layer.waves = [{ wave_index: 0, state: 'active', asset_ids: ['ka_smriti', 'ka_uncatalogued'], completed_asset_ids: [], active_asset_ids: ['ka_smriti'], blocked_asset_ids: [], locked_asset_ids: [], unknown_asset_ids: ['ka_uncatalogued'], eligible_next_asset_ids: ['ka_uncatalogued'] }]
    const onOpenAudit = vi.fn()

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={onOpenAudit} waveProgress={layer.wave_progress} />)

    expect(screen.getByText('System ID: ka_smriti')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Kāla Smṛti' })).toBeVisible()
    expect(screen.getByText('Kala Smriti')).toBeVisible()
    expect(screen.getByText('Per-varsha digest')).toBeVisible()
    expect(screen.getByText(/year-by-year digest/i)).toBeVisible()
    expect(within(screen.getByText('System ID: ka_uncatalogued').closest('article')!).getAllByText('Additional human-facing identity is not yet catalogued')).toHaveLength(1)
    expect(screen.queryByText('Kāla Uncatalogued')).not.toBeInTheDocument()
    const legacyLabel = screen.getByText('Legacy reference')
    const legacyId = screen.getByText('A22')
    expect(legacyLabel.compareDocumentPosition(legacyId) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /audit details for ka_smriti/i }))
    expect(onOpenAudit).toHaveBeenCalledWith('ka_smriti')
  })

  it('discloses six milestone positions, N/A-aware counts, actions, dependencies, and producer inheritance', () => {
    const snapshot = snapshotFixture()
    const layer = layerFixture(snapshot)
    const source = snapshot.assets.find((asset) => asset.asset_id === 'bg_sign_medical')
    if (!source) throw new Error('Fixture must include bg_sign_medical.')
    const asset = {
      ...source,
      asset_id: 'ka_disclosure',
      layer: 'L3' as const,
      wave_index: 0,
      sanskrit_name: 'Kāla Disclosure',
      english_name: 'Kala Disclosure',
      description: 'Year-by-year digest evidence',
      milestones: source.milestones.map((milestone, index) => index === 2 ? { ...milestone, state: 'not_applicable' as const, event_type: null, accepted_at: null } : milestone),
      milestones_earned: 5,
      milestones_required: 5,
      current_action: 'Confirm inherited execution evidence',
      next_action: 'Freeze accepted disclosure',
      depends_on: ['ka_prerequisite'],
      unlocks: ['ka_successor'],
      blocker: 'Waiting for source receipt',
      producer_id: 'ka_producer',
    }
    const fiveOfSix = {
      ...source,
      asset_id: 'ka_five_of_six',
      layer: 'L3' as const,
      wave_index: 0,
      milestones: source.milestones.map((milestone, index) => index === 5 ? { ...milestone, state: 'pending' as const, event_type: null, accepted_at: null } : milestone),
      milestones_earned: 5,
      milestones_required: 6,
    }
    snapshot.assets = [asset, fiveOfSix] as NirmanaElevationSnapshotV2['assets']
    layer.waves = [{ wave_index: 0, state: 'active', asset_ids: ['ka_disclosure', 'ka_five_of_six'], completed_asset_ids: [], active_asset_ids: ['ka_disclosure'], blocked_asset_ids: [], locked_asset_ids: [], unknown_asset_ids: ['ka_five_of_six'], eligible_next_asset_ids: ['ka_five_of_six'] }]

    render(<LayerStage layer={layer} assets={snapshot.assets} onOpenAudit={vi.fn()} waveProgress={layer.wave_progress} />)

    const card = screen.getByText('System ID: ka_disclosure').closest('article')!
    expect(within(card).getAllByRole('listitem', { name: /^(analysed|decision accepted|built or dispositioned|deployed and executed|verified|frozen):/i })).toHaveLength(6)
    expect(within(card).getByText('5 of 5 required milestones')).toBeVisible()
    expect(within(card).getByLabelText(/built or dispositioned: not applicable/i)).toBeVisible()
    expect(within(card).getByText('not applicable')).toBeVisible()
    expect(within(card).queryByText(/^\d+%$/)).not.toBeInTheDocument()
    expect(within(screen.getByText('System ID: ka_five_of_six').closest('article')!).getByText('5 of 6 required milestones')).toBeVisible()

    fireEvent.click(within(card).getByRole('button', { name: /show details for ka_disclosure/i }))
    expect(screen.getByText('Confirm inherited execution evidence')).toBeVisible()
    expect(screen.getByText('Freeze accepted disclosure')).toBeVisible()
    expect(screen.getByText('ka_prerequisite')).toBeVisible()
    expect(screen.getByText('ka_successor')).toBeVisible()
    expect(screen.getByText('Waiting for source receipt')).toBeVisible()
    expect(screen.getByText('ka_producer')).toBeVisible()
    expect(screen.getByText('Producer inheritance')).toBeVisible()
  })
})
