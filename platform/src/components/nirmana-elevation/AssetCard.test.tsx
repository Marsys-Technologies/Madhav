import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { AssetCard } from './AssetCard'

function assetFixture(assetId = 'ka_smriti'): NirmanaElevationSnapshotV2['assets'][number] {
  const snapshot = structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
  const asset = snapshot.assets.find((candidate) => candidate.asset_id === assetId)
  if (!asset) throw new Error(`Fixture must include ${assetId}.`)
  return asset
}

describe('AssetCard', () => {
  it('presents a plan reference and human identity before the raw system id', () => {
    render(<AssetCard asset={assetFixture()} onOpenAudit={vi.fn()} />)

    expect(screen.getByRole('heading', { name: /A22 · Kāla Smṛti/i })).toBeVisible()
    expect(screen.getByText('Kala Smriti')).toBeVisible()
    expect(screen.getByText('System ID: ka_smriti')).toBeVisible()
  })

  it('shows missing human metadata once and marks registry fallback copy as provisional', () => {
    const asset = {
      ...assetFixture(),
      sanskrit_name: null,
      description: null,
      legacy_aliases: [],
      identity_quality: 'unversioned_fallback' as const,
    }

    render(<AssetCard asset={asset} onOpenAudit={vi.fn()} />)

    expect(screen.getAllByText('Additional human-facing identity is not yet catalogued')).toHaveLength(1)
    expect(screen.getByText('Provisional registry label')).toBeVisible()
    expect(screen.queryByText('Not yet catalogued')).not.toBeInTheDocument()
  })

  it('exposes determinate asset completion as an accessible progress bar', () => {
    const asset = assetFixture('bg_prashna_rules')

    render(<AssetCard asset={asset} onOpenAudit={vi.fn()} />)

    const progress = screen.getByRole('progressbar', { name: /Prashna Rules asset completion/i })
    expect(progress).toHaveAttribute('aria-valuenow', String(asset.milestones_earned))
    expect(progress).toHaveAttribute('aria-valuemax', String(asset.milestones_required))
    expect(progress).toHaveAttribute('aria-valuetext', `${asset.milestones_earned} of ${asset.milestones_required} required milestones earned`)
  })

  it('keeps one current action and blocker visible without opening details', () => {
    const asset = { ...assetFixture('bg_prashna_rules'), blocker: 'Waiting for accepted contract evidence' }

    render(<AssetCard asset={asset} onOpenAudit={vi.fn()} />)

    const card = screen.getByRole('article')
    expect(within(card).getByText(`Now: ${asset.current_action}`)).toBeVisible()
    expect(within(card).getByText('Blocked: Waiting for accepted contract evidence')).toBeVisible()
    expect(within(card).queryByText('Dependencies')).not.toBeInTheDocument()
  })
})
