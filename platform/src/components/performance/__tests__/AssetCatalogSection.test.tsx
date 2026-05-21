import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AssetCatalogSection } from '../AssetCatalogSection'
import type { AssetCatalogResponse } from '@/lib/performance/asset_health'

vi.mock('@/lib/performance/api_client', () => ({
  fetchAssets: vi.fn().mockResolvedValue({
    fingerprint: 'test-fp',
    total: 2,
    entries: [
      {
        canonical_id: 'FORENSIC',
        path: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
        version: '8.0',
        status: 'CURRENT',
        layer: 'L1',
        expose_to_chat: true,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc',
        native_id: 'abhisek',
        health: 'green',
        reachability: 'reachable',
        bound_tools: ['lel_query'],
      },
      {
        canonical_id: 'OLD_REPORT',
        path: '03_DOMAIN_REPORTS/old.md',
        version: '1.0',
        status: 'SUPERSEDED',
        layer: 'L3',
        expose_to_chat: false,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'def',
        native_id: 'abhisek',
        health: 'gray',
        reachability: 'no_tool',
        bound_tools: [],
      },
    ],
  } satisfies AssetCatalogResponse),
}))

function wrap(children: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('AssetCatalogSection', () => {
  it('renders section heading', async () => {
    render(wrap(<AssetCatalogSection />))
    expect(screen.getByTestId('asset-catalog-section')).toBeDefined()
  })

  it('renders scoreboard after data loads', async () => {
    render(wrap(<AssetCatalogSection />))
    // scoreboard cell
    const total = await screen.findByText('2')
    expect(total).toBeDefined()
  })

  it('renders FORENSIC entry in the layer group', async () => {
    render(wrap(<AssetCatalogSection />))
    const id = await screen.findByText('FORENSIC')
    expect(id).toBeDefined()
  })
})
