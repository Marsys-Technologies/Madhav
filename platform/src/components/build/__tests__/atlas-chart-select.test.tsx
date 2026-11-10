import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { AtlasView } from '../AtlasView'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

it('exposes the Atlas chart selector under its visible label', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => Response.json(url === '/api/clients'
    ? [{ chart_id: 'fixture-chart', name: 'Fixture chart' }]
    : { data: { assets: [] } },
  )))

  render(<AtlasView assets={[]} defaultChartId="fixture-chart" />)

  await screen.findByRole('option', { name: 'Fixture chart' })
  expect(screen.getByRole('combobox', { name: 'Chart' })).toHaveValue('fixture-chart')
})
