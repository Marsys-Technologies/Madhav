import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import { PreparationReadiness } from '../PreparationReadiness'
import { BuildActionButton } from '../BuildActionButton'
import { AssetProgressBar } from '../AssetProgressBar'

const assets = [
  { asset_id: 'ga_positions', layer: 'ganita', is_active: true, depends_on: [] },
  { asset_id: 'bo_laksana', layer: 'bodha', is_active: true, depends_on: ['ga_positions'] },
] as AssetRow[]

it('keeps Gaṇita prepared when Bodha needs refresh and scopes retry to the affected layer', () => {
  const stats = new Map([
    ['ga_positions', { state: 'lit' }],
    ['bo_laksana', { state: 'stale' }],
  ] as [string, AssetStats][])
  const readiness = { assets, stats, unavailable: false, chartId: 'fixture', activeRun: null }
  const view = render(<PreparationReadiness {...readiness} />)
  expect(screen.getByText('Gaṇita · Prepared')).toBeInTheDocument()
  expect(screen.getByText('Bodha · Needs refresh')).toBeInTheDocument()
  expect(screen.queryByText(/needs a retry/)).toBeNull()

  view.rerender(<PreparationReadiness {...readiness} preparationRetryAssets={['bo_laksana']} />)
  expect(screen.getByText('Bodha · Preparation needs a retry')).toBeInTheDocument()
  expect(screen.getByText('Gaṇita · Prepared')).toBeInTheDocument()
})

it('offers a full rebuild at the same entry point as a selective resume', () => {
  render(<BuildActionButton chartId="fixture" scope="asset_set" scopeTarget="ga_positions,bo_laksana"
    stats={{ total: 2, dormant: 0, stale: 1 }} resumeMissing allowFullRebuild preparation labelSuffix=" through Bodha" />)
  expect(screen.getByRole('button', { name: 'Resume through Bodha' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Rebuild through Bodha' })).toBeInTheDocument()
})

it('shows verification after the final write substep while the asset remains active', () => {
  render(<AssetProgressBar state="building" stage="committing" substep={{ index: 5, total: 5 }} preparation />)
  expect(screen.getByText('Verifying and saving')).toBeInTheDocument()
})
