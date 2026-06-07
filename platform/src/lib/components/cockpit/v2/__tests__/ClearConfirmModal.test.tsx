import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClearConfirmModal } from '../ClearConfirmModal'

const PREVIEW_BASE = {
  tables: [{ table: 'ephemeris_daily', rows: 500 }],
  total_rows: 500,
  affected_assets: ['bg_ephemeris'],
  downstream_stale_assets: [],
  preview_hash: 'abc123',
}

describe('ClearConfirmModal', () => {
  it('renders typed confirmation for global scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="global"
        preview={{ ...PREVIEW_BASE, requires_typed_confirmation: 'Abhisek Mohanty' }}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(screen.getByText('Abhisek Mohanty')).toBeTruthy()
    expect(screen.getByPlaceholderText('Abhisek Mohanty')).toBeTruthy()
  })

  it('renders typed confirmation for L0 layer scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="layer"
        scopeTarget="brahmagyan"
        preview={{ ...PREVIEW_BASE, requires_typed_confirmation: 'Abhisek Mohanty' }}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(screen.getByPlaceholderText('Abhisek Mohanty')).toBeTruthy()
  })

  it('does NOT render typed confirmation for non-L0 layer scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="layer"
        scopeTarget="ganita"
        preview={PREVIEW_BASE}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('does NOT render typed confirmation for asset scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="asset"
        scopeTarget="ga_positions"
        preview={PREVIEW_BASE}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('confirm button enabled without typing for non-typed-confirmation scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="asset"
        scopeTarget="ga_positions"
        preview={PREVIEW_BASE}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    const btn = screen.getByRole('button', { name: /clear data/i })
    expect((btn as HTMLButtonElement).disabled).toBe(false)
  })

  it('confirm button disabled when typed value does not match for global scope', () => {
    render(
      <ClearConfirmModal
        chartId="chart-1"
        scope="global"
        preview={{ ...PREVIEW_BASE, requires_typed_confirmation: 'Abhisek Mohanty' }}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    const btn = screen.getByRole('button', { name: /clear instrument/i })
    expect((btn as HTMLButtonElement).disabled).toBe(true)
  })
})
