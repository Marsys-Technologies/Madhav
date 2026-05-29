import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, test, expect } from 'vitest'
import AssetDetailPanel from '../AssetDetailPanel'
import { AssetNodeData } from '../AssetNode'

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

function renderPanel(
  assetOverrides: Partial<AssetNodeData> = {},
  isOpen = true,
  onClose = vi.fn()
) {
  const asset = makeAsset(assetOverrides)
  render(<AssetDetailPanel asset={asset} isOpen={isOpen} onClose={onClose} />)
  return { asset, onClose }
}

// ---------------------------------------------------------------------------
// TC-01: returns null when isOpen=false
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — visibility gate', () => {
  test('TC-01: renders nothing when isOpen=false', () => {
    render(
      <AssetDetailPanel
        asset={makeAsset()}
        isOpen={false}
        onClose={vi.fn()}
      />
    )
    expect(screen.queryByTestId('asset-detail-panel')).not.toBeInTheDocument()
  })

  test('TC-02: renders nothing when asset=null even if isOpen=true', () => {
    render(
      <AssetDetailPanel
        asset={null}
        isOpen={true}
        onClose={vi.fn()}
      />
    )
    expect(screen.queryByTestId('asset-detail-panel')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-03 – TC-06: basic rendering when open
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — basic rendering', () => {
  test('TC-03: renders data-testid="asset-detail-panel" when open', () => {
    renderPanel()
    expect(screen.getByTestId('asset-detail-panel')).toBeInTheDocument()
  })

  test('TC-04: sets data-asset-id attribute to asset.asset_id', () => {
    renderPanel({ asset_id: 'A10_msr' })
    expect(screen.getByTestId('asset-detail-panel')).toHaveAttribute('data-asset-id', 'A10_msr')
  })

  test('TC-05: renders known asset full_name in header (not raw asset_label)', () => {
    // A3_chart_facts maps to full_name 'Chart Facts' in ASSET_DESCRIPTIONS
    renderPanel({ asset_id: 'A3_chart_facts', asset_label: 'Chart Facts' })
    expect(screen.getByText('Chart Facts')).toBeInTheDocument()
  })

  test('TC-06: falls back to asset_label in header for unknown asset_id', () => {
    renderPanel({ asset_id: 'ZZ_unknown', asset_label: 'Mystery Asset' })
    expect(screen.getByText('Mystery Asset')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-07: close button
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — close button', () => {
  test('TC-07: close button has data-testid="detail-panel-close"', () => {
    renderPanel()
    expect(screen.getByTestId('detail-panel-close')).toBeInTheDocument()
  })

  test('TC-08: clicking close button calls onClose callback', () => {
    const onClose = vi.fn()
    render(
      <AssetDetailPanel
        asset={makeAsset()}
        isOpen={true}
        onClose={onClose}
      />
    )
    fireEvent.click(screen.getByTestId('detail-panel-close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})

// ---------------------------------------------------------------------------
// TC-09: status display
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — status display', () => {
  test('TC-09: displays asset state as text', () => {
    renderPanel({ state: 'running' })
    expect(screen.getByText('running')).toBeInTheDocument()
  })

  test('TC-10: complete state text is present', () => {
    renderPanel({ state: 'complete' })
    expect(screen.getByText('complete')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-11: rows_written metric
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — rows_written', () => {
  test('TC-11: shows formatted rows_written when provided', () => {
    renderPanel({ state: 'complete', rows_written: 2717 })
    expect(screen.getByText('2,717')).toBeInTheDocument()
  })

  test('TC-12: does not render rows section when rows_written is undefined', () => {
    renderPanel({ state: 'complete' })
    expect(screen.queryByText('Rows Written')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-13: error display for failed state
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — error display', () => {
  test('TC-13: shows error message when state=failed and error provided', () => {
    renderPanel({ state: 'failed', error: 'ephemeris timeout after 30s' })
    expect(screen.getByText('ephemeris timeout after 30s')).toBeInTheDocument()
  })

  test('TC-14: does not render error block when state=failed but no error field', () => {
    renderPanel({ state: 'failed' })
    expect(screen.queryByText('Error')).not.toBeInTheDocument()
  })

  test('TC-15: does not render error block when state=complete even if error field set', () => {
    renderPanel({ state: 'complete', error: 'stale residual error' })
    // Error block only renders when state === 'failed'
    expect(screen.queryByText('stale residual error')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-16 – TC-17: ayanamsha progress
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — ayanamsha progress', () => {
  test('TC-16: renders each ayanamsha in ayanamshas_total', () => {
    renderPanel({
      state: 'running',
      ayanamshas_total: ['lahiri', 'raman', 'kp'],
      ayanamshas_complete: ['lahiri'],
    })
    expect(screen.getByText('lahiri')).toBeInTheDocument()
    expect(screen.getByText('raman')).toBeInTheDocument()
    expect(screen.getByText('kp')).toBeInTheDocument()
  })

  test('TC-17: does not render ayanamsha section when ayanamshas_total is empty', () => {
    renderPanel({ state: 'pending', ayanamshas_total: [] })
    expect(screen.queryByText('Ayanamshas')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-18: duration display
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — duration', () => {
  test('TC-18: shows duration in seconds when started_at and finished_at are both set', () => {
    const started_at = '2026-05-29T10:00:00.000Z'
    const finished_at = '2026-05-29T10:00:05.500Z'
    renderPanel({ state: 'complete', started_at, finished_at })
    expect(screen.getByText('5.5s')).toBeInTheDocument()
  })

  test('TC-19: does not render duration when started_at is missing', () => {
    renderPanel({ state: 'complete', finished_at: '2026-05-29T10:00:05.000Z' })
    expect(screen.queryByText('Duration')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// TC-20: description + output for known assets
// ---------------------------------------------------------------------------

describe('AssetDetailPanel — known asset description metadata', () => {
  test('TC-20: renders description text for known asset A1_engine', () => {
    renderPanel({ asset_id: 'A1_engine', asset_label: 'Engine' })
    expect(
      screen.getByText(/Natal chart computed via Swiss Ephemeris/)
    ).toBeInTheDocument()
  })

  test('TC-21: renders output text for known asset A10_msr', () => {
    renderPanel({ asset_id: 'A10_msr', asset_label: 'MSR' })
    expect(
      screen.getByText(/MSR rows with computed_salience scores/)
    ).toBeInTheDocument()
  })

  test('TC-22: does not render description/output sections for unknown asset_id', () => {
    renderPanel({ asset_id: 'ZZ_unknown', asset_label: 'Mystery' })
    expect(screen.queryByText('Description')).not.toBeInTheDocument()
    expect(screen.queryByText('Output')).not.toBeInTheDocument()
  })
})
