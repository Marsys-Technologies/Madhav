import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import AssetNode, { AssetNodeData } from '../AssetNode'
import AssetNodeGrid from '../AssetNodeGrid'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeAsset(overrides: Partial<AssetNodeData> = {}): AssetNodeData {
  return {
    asset_id: 'A3_chart_facts',
    asset_label: 'Chart Facts',
    state: 'pending',
    ...overrides,
  }
}

const ALL_14_ASSETS: AssetNodeData[] = [
  { asset_id: 'A1_engine',           asset_label: 'Engine',           state: 'complete' },
  { asset_id: 'A2_forensic_render',  asset_label: 'Forensic Render',  state: 'pending' },
  { asset_id: 'A3_chart_facts',      asset_label: 'Chart Facts',      state: 'running' },
  { asset_id: 'A4_panchanga',        asset_label: 'Panchanga',        state: 'failed' },
  { asset_id: 'A5_sensitive_points', asset_label: 'Sensitive Points', state: 'skipped' },
  { asset_id: 'A6_vargas',           asset_label: 'Vargas',           state: 'cancelled' },
  { asset_id: 'A7_dashas',           asset_label: 'Dashas',           state: 'pending' },
  { asset_id: 'A8_t1_structural',    asset_label: 'T1 Structural',    state: 'pending' },
  { asset_id: 'A9_sade_sati',        asset_label: 'Sade Sati',        state: 'pending' },
  { asset_id: 'A10_msr',             asset_label: 'MSR',              state: 'pending' },
  { asset_id: 'A11_cdlm',            asset_label: 'CDLM',             state: 'pending' },
  { asset_id: 'A12_cgm',             asset_label: 'CGM',              state: 'pending' },
  { asset_id: 'A13_rm',              asset_label: 'RM',               state: 'pending' },
  { asset_id: 'A14_ucn_digest',      asset_label: 'UCN Digest',       state: 'pending' },
]

// ---------------------------------------------------------------------------
// AssetNode — basic rendering
// ---------------------------------------------------------------------------

describe('AssetNode', () => {
  test('TC-01: renders with correct data-testid', () => {
    render(<AssetNode data={makeAsset()} />)
    expect(screen.getByTestId('asset-node-A3_chart_facts')).toBeInTheDocument()
  })

  test('TC-02: renders asset_label as visible text', () => {
    render(<AssetNode data={makeAsset({ asset_label: 'Chart Facts' })} />)
    expect(screen.getByText('Chart Facts')).toBeInTheDocument()
  })

  test('TC-03: pending state renders ○ icon', () => {
    render(<AssetNode data={makeAsset({ state: 'pending' })} />)
    expect(screen.getByText('○')).toBeInTheDocument()
  })

  test('TC-04: complete state renders ✓ icon', () => {
    render(<AssetNode data={makeAsset({ state: 'complete' })} />)
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  test('TC-05: running state renders ◉ icon and animate-pulse class', () => {
    render(<AssetNode data={makeAsset({ state: 'running' })} />)
    expect(screen.getByText('◉')).toBeInTheDocument()
    const node = screen.getByTestId('asset-node-A3_chart_facts')
    expect(node.className).toContain('animate-pulse')
  })

  test('TC-06: failed state renders ✗ icon', () => {
    render(<AssetNode data={makeAsset({ state: 'failed' })} />)
    expect(screen.getByText('✗')).toBeInTheDocument()
  })

  test('TC-07: cancelled state renders ⊘ icon', () => {
    render(<AssetNode data={makeAsset({ state: 'cancelled' })} />)
    expect(screen.getByText('⊘')).toBeInTheDocument()
  })

  test('TC-08: skipped state renders — icon', () => {
    render(<AssetNode data={makeAsset({ state: 'skipped' })} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  test('TC-09: failed state shows error message when provided', () => {
    render(
      <AssetNode
        data={makeAsset({ state: 'failed', error: 'ephemeris timeout after 30s' })}
      />
    )
    expect(screen.getByText('ephemeris timeout after 30s')).toBeInTheDocument()
  })

  test('TC-10: complete state shows rows_written when provided', () => {
    render(
      <AssetNode
        data={makeAsset({ state: 'complete', rows_written: 2717 })}
      />
    )
    expect(screen.getByText('2,717 rows')).toBeInTheDocument()
  })

  test('TC-11: running state shows ayanamsha progress when provided', () => {
    render(
      <AssetNode
        data={makeAsset({
          state: 'running',
          ayanamshas_complete: ['lahiri', 'raman'],
          ayanamshas_total: ['lahiri', 'raman', 'kp', 'true_citra', 'yukteshwar'],
        })}
      />
    )
    expect(screen.getByText('2/5 ayanamshas')).toBeInTheDocument()
  })

  test('TC-12: compact mode renders as a button with short name', () => {
    render(
      <AssetNode
        data={makeAsset({ asset_id: 'A3_chart_facts', state: 'pending' })}
        compact={true}
      />
    )
    const btn = screen.getByTestId('asset-node-A3_chart_facts')
    expect(btn.tagName).toBe('BUTTON')
    expect(btn.textContent).toBe('CF')
  })

  test('TC-13: compact mode running has animate-pulse class', () => {
    render(
      <AssetNode
        data={makeAsset({ asset_id: 'A10_msr', state: 'running' })}
        compact={true}
      />
    )
    const btn = screen.getByTestId('asset-node-A10_msr')
    expect(btn.className).toContain('animate-pulse')
  })

  test('TC-14: onClick callback fires with asset data when clicked', () => {
    const handler = vi.fn()
    const asset = makeAsset({ state: 'complete' })
    render(<AssetNode data={asset} onClick={handler} />)
    fireEvent.click(screen.getByTestId('asset-node-A3_chart_facts'))
    expect(handler).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledWith(asset)
  })

  test('TC-15: data-state attribute reflects current state', () => {
    render(<AssetNode data={makeAsset({ state: 'failed' })} />)
    expect(screen.getByTestId('asset-node-A3_chart_facts')).toHaveAttribute('data-state', 'failed')
  })

  test('TC-16: pending state does NOT have animate-pulse class', () => {
    render(<AssetNode data={makeAsset({ state: 'pending' })} />)
    const node = screen.getByTestId('asset-node-A3_chart_facts')
    expect(node.className).not.toContain('animate-pulse')
  })

  test('TC-17: unknown asset_id falls back to first-3-chars uppercase short name in compact mode', () => {
    render(
      <AssetNode
        data={makeAsset({ asset_id: 'ZZZZ_custom', asset_label: 'Custom', state: 'pending' })}
        compact={true}
      />
    )
    const btn = screen.getByTestId('asset-node-ZZZZ_custom')
    expect(btn.textContent).toBe('ZZZ')
  })
})

// ---------------------------------------------------------------------------
// AssetNodeGrid
// ---------------------------------------------------------------------------

describe('AssetNodeGrid', () => {
  test('TC-18: renders data-testid asset-node-grid', () => {
    render(<AssetNodeGrid assets={ALL_14_ASSETS} />)
    expect(screen.getByTestId('asset-node-grid')).toBeInTheDocument()
  })

  test('TC-19: renders all 14 asset nodes', () => {
    render(<AssetNodeGrid assets={ALL_14_ASSETS} />)
    const nodes = ALL_14_ASSETS.map(a => screen.getByTestId(`asset-node-${a.asset_id}`))
    expect(nodes).toHaveLength(14)
  })

  test('TC-20: each node in the grid receives correct asset_label', () => {
    render(<AssetNodeGrid assets={ALL_14_ASSETS} />)
    expect(screen.getByText('Chart Facts')).toBeInTheDocument()
    expect(screen.getByText('Panchanga')).toBeInTheDocument()
    expect(screen.getByText('UCN Digest')).toBeInTheDocument()
  })

  test('TC-21: grid passes onAssetClick to child nodes', () => {
    const handler = vi.fn()
    render(<AssetNodeGrid assets={ALL_14_ASSETS} onAssetClick={handler} />)
    fireEvent.click(screen.getByTestId('asset-node-A1_engine'))
    expect(handler).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ asset_id: 'A1_engine' }))
  })

  test('TC-22: renders empty grid gracefully with zero assets', () => {
    render(<AssetNodeGrid assets={[]} />)
    expect(screen.getByTestId('asset-node-grid')).toBeInTheDocument()
    expect(screen.getByTestId('asset-node-grid').children).toHaveLength(0)
  })
})
