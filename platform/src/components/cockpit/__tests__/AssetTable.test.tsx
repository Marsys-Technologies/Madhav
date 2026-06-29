import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AssetTable, type AssetRow } from '../AssetTable'

// Stub CascadePreviewModal (tested separately)
vi.mock('../CascadePreviewModal', () => ({
  CascadePreviewModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? <div data-testid="cascade-modal"><button onClick={onClose}>Close</button></div> : null,
}))

const SAMPLE_ASSETS: AssetRow[] = [
  { assetId: 'pratyaksha',     status: 'complete', rowCount: 1200, lastUpdated: '2026-06-29T10:00:00Z' },
  { assetId: 'panchanga',      status: 'running',  rowCount: 400,  lastUpdated: '2026-06-29T10:01:00Z' },
  { assetId: 'lakshana_kosha', status: 'pending',  rowCount: 0,    lastUpdated: '' },
  { assetId: 'prashna',        status: 'failed',   rowCount: 0,    lastUpdated: '' },
]

describe('AssetTable', () => {
  it('renders empty state message when no assets provided', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    expect(screen.getByText(/No asset data yet/)).toBeTruthy()
  })

  it('renders a table when assets are provided', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getByRole('table')).toBeTruthy()
  })

  it('renders Asset, Status, Rows, Updated, Actions column headers', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getByText('Asset')).toBeTruthy()
    expect(screen.getByText('Status')).toBeTruthy()
    expect(screen.getByText('Rows')).toBeTruthy()
    expect(screen.getByText('Updated')).toBeTruthy()
    expect(screen.getByText('Actions')).toBeTruthy()
  })

  it('renders one row per asset', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const rows = screen.getAllByRole('row')
    // 1 header row + 4 data rows
    expect(rows.length).toBe(5)
  })

  it('renders the row count formatted for assets with data', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getByText('1,200')).toBeTruthy()
  })

  it('renders 0 for assets with zero row count', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    // Two assets have rowCount 0
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(2)
  })

  it('renders Rebuild button for non-running assets', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    // complete, pending, failed all get Rebuild
    const rebuilds = screen.getAllByText('Rebuild')
    expect(rebuilds.length).toBeGreaterThanOrEqual(3)
  })

  it('renders Stop button for running assets', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getByText('Stop')).toBeTruthy()
  })

  it('renders Skip button for pending assets', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getByText('Skip')).toBeTruthy()
  })

  it('opens CascadePreviewModal when Rebuild is clicked', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    // Click the first Rebuild button (pratyaksha — status=complete)
    const rebuilds = screen.getAllByText('Rebuild')
    fireEvent.click(rebuilds[0])
    expect(screen.getByTestId('cascade-modal')).toBeTruthy()
  })

  it('closes CascadePreviewModal when modal Close is clicked', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const rebuilds = screen.getAllByText('Rebuild')
    fireEvent.click(rebuilds[0])
    fireEvent.click(screen.getByText('Close'))
    expect(screen.queryByTestId('cascade-modal')).toBeNull()
  })

  it('renders a dash when lastUpdated is empty', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    // Two assets have lastUpdated='' → should render '—'
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThanOrEqual(2)
  })

  it('renders a time string when lastUpdated is set', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    // At least one asset has a valid ISO date — toLocaleTimeString renders something
    const tds = document.querySelectorAll('td')
    const timeValues = Array.from(tds).map(td => td.textContent ?? '')
    const hasTime = timeValues.some(t => /\d+:\d+/.test(t))
    expect(hasTime).toBe(true)
  })

  it('does not render table when assets is empty', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    expect(screen.queryByRole('table')).toBeNull()
  })
})
