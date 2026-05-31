import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AssetTable, type AssetRow } from '../AssetTable'

// Stub CascadePreviewModal (tested separately)
vi.mock('../CascadePreviewModal', () => ({
  CascadePreviewModal: ({ open, onClose }: { open: boolean; onClose: () => void }) =>
    open ? <div data-testid="cascade-modal"><button onClick={onClose}>Close</button></div> : null,
}))

const SAMPLE_ASSETS: AssetRow[] = [
  { assetId: 'pratyaksha',    status: 'complete', rowCount: 1200, progress: 1.0 },
  { assetId: 'panchanga',     status: 'running',  rowCount: 400,  progress: 0.4 },
  { assetId: 'lakshana_kosha', status: 'pending',  rowCount: 0,    progress: 0 },
  { assetId: 'prashna',       status: 'failed',   rowCount: 0,    progress: 0 },
]

describe('AssetTable', () => {
  it('renders with data-testid asset-table', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    expect(screen.getByTestId('asset-table')).toBeTruthy()
  })

  it('renders all 4 layer section headings', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    expect(screen.getByTestId('layer-section-L1')).toBeTruthy()
    expect(screen.getByTestId('layer-section-L2_5')).toBeTruthy()
    expect(screen.getByTestId('layer-section-L3')).toBeTruthy()
    expect(screen.getByTestId('layer-section-L4')).toBeTruthy()
  })

  it('renders Sanskrit section heading for L1 (Adhara)', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    const section = screen.getByTestId('layer-section-L1')
    expect(section.textContent).toContain('Adhara')
  })

  it('renders Sanskrit section heading for L2_5 (Sambandha)', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    const section = screen.getByTestId('layer-section-L2_5')
    expect(section.textContent).toContain('Sambandha')
  })

  it('renders rows for all 28 known assets', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    // Every asset key should have a row
    const allRows = screen.getAllByTestId(/^asset-row-/)
    expect(allRows.length).toBeGreaterThanOrEqual(28)
  })

  it('renders pratyaksha row with Sanskrit name', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const row = screen.getByTestId('asset-row-pratyaksha')
    expect(row.textContent).toContain('Pratyaksha')
  })

  it('renders asset subtitle in the row', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const row = screen.getByTestId('asset-row-pratyaksha')
    expect(row.textContent).toContain('Forensic chart')
  })

  it('renders correct status for complete asset', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getAllByTestId('status-pill-complete').length).toBeGreaterThan(0)
  })

  it('renders correct status for running asset', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getAllByTestId('status-pill-running').length).toBeGreaterThan(0)
  })

  it('renders correct status for pending asset', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getAllByTestId('status-pill-pending').length).toBeGreaterThan(0)
  })

  it('renders correct status for failed asset', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    expect(screen.getAllByTestId('status-pill-failed').length).toBeGreaterThan(0)
  })

  it('shows row count for assets with data', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const row = screen.getByTestId('asset-row-pratyaksha')
    expect(row.textContent).toContain('1,200')
  })

  it('shows dash for assets with zero row count', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const row = screen.getByTestId('asset-row-prashna')
    expect(row.textContent).toContain('—')
  })

  it('renders Rebuild button for each asset row', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    const rebuilds = screen.getAllByTestId(/^rebuild-btn-/)
    expect(rebuilds.length).toBeGreaterThanOrEqual(28)
  })

  it('calls onRebuild prop when Rebuild button is clicked', () => {
    const onRebuild = vi.fn()
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} onRebuild={onRebuild} />)
    fireEvent.click(screen.getByTestId('rebuild-btn-pratyaksha'))
    expect(onRebuild).toHaveBeenCalledWith('pratyaksha')
  })

  it('opens CascadePreviewModal when Rebuild is clicked', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    fireEvent.click(screen.getByTestId('rebuild-btn-panchanga'))
    expect(screen.getByTestId('cascade-modal')).toBeTruthy()
  })

  it('closes CascadePreviewModal when modal Close is clicked', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    fireEvent.click(screen.getByTestId('rebuild-btn-panchanga'))
    fireEvent.click(screen.getByText('Close'))
    expect(screen.queryByTestId('cascade-modal')).toBeNull()
  })

  it('renders cascade hint footer', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    expect(screen.getByTestId('cascade-hint').textContent).toContain('Rebuild just that asset')
  })

  it('shows layer completion count', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={SAMPLE_ASSETS} />)
    const l1Count = screen.getByTestId('layer-count-L1')
    expect(l1Count.textContent).toContain('1 of 8 complete')
  })

  it('renders rows in layer order: L1 before L2_5 before L3 before L4', () => {
    render(<AssetTable buildId="b1" chartId="c1" assets={[]} />)
    const table = screen.getByTestId('asset-table')
    const sectionOrder = Array.from(
      table.querySelectorAll('[data-testid^="layer-section-"]')
    ).map((el) => el.getAttribute('data-testid'))
    expect(sectionOrder).toEqual([
      'layer-section-L1',
      'layer-section-L2_5',
      'layer-section-L3',
      'layer-section-L4',
    ])
  })
})
