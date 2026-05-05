// USTAD_S2_6 — ReconciliationBanner UI tests.
// Updated OBS-UX-S4: ReconciliationBannerView now renders ProviderStatusCard
// cards (data-testid="reconciliation-card-{provider}") instead of StatusChip
// chips. Tests updated to match new card-grid structure.

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import {
  ReconciliationBannerView,
  type ReconciliationBannerRow,
} from '../../reconciliation/ReconciliationBannerView'

function row(
  partial: Partial<ReconciliationBannerRow> & {
    provider: string
    status: ReconciliationBannerRow['status']
  },
): ReconciliationBannerRow {
  return {
    reconciliation_id: `rec-${partial.provider}-${partial.status}`,
    period_start: '2026-05-01',
    period_end: '2026-05-01',
    variance_pct: 0,
    computed_cost_usd: 0,
    authoritative_cost_usd: 0,
    created_at: '2026-05-03T00:00:00Z',
    ...partial,
  }
}

describe('ReconciliationBannerView', () => {
  it('renders nothing when history is empty (test 4)', () => {
    const { container } = render(<ReconciliationBannerView rows={[]} />)
    expect(container.firstChild).toBeNull()
    expect(screen.queryByTestId('reconciliation-banner')).not.toBeInTheDocument()
  })

  it("renders 'matched' card for a reconciled provider (test 5)", () => {
    render(
      <ReconciliationBannerView
        rows={[row({ provider: 'anthropic', status: 'matched', variance_pct: 0.1 })]}
      />,
    )
    const card = screen.getByTestId('reconciliation-card-anthropic')
    expect(card).toBeInTheDocument()
    expect(card).toHaveAttribute('data-status', 'matched')
    expect(card.textContent).toMatch(/Anthropic/)
    expect(card.textContent).toMatch(/Reconciled/)
  })

  it("renders 'variance_alert' card (red) for an alerting provider (test 6)", () => {
    render(
      <ReconciliationBannerView
        rows={[row({ provider: 'openai', status: 'variance_alert', variance_pct: 7.5 })]}
      />,
    )
    const card = screen.getByTestId('reconciliation-card-openai')
    expect(card).toHaveAttribute('data-status', 'variance_alert')
    expect(card.textContent).toMatch(/OpenAI/)
    expect(card.textContent).toMatch(/Alert/)
    expect(card.textContent).toMatch(/7\.5/)
  })

  it("renders 'missing_authoritative' card for a no-data provider (test 7)", () => {
    render(
      <ReconciliationBannerView
        rows={[
          row({
            provider: 'deepseek',
            status: 'missing_authoritative',
            variance_pct: null,
          }),
        ]}
      />,
    )
    const card = screen.getByTestId('reconciliation-card-deepseek')
    expect(card).toHaveAttribute('data-status', 'missing_authoritative')
    expect(card.textContent).toMatch(/DeepSeek/)
    expect(card.textContent).toMatch(/No data/)
  })

  it('deduplicates by provider (defensive — loader is the primary dedupe)', () => {
    render(
      <ReconciliationBannerView
        rows={[
          row({ provider: 'gemini', status: 'matched' }),
          row({
            provider: 'gemini',
            status: 'variance_alert',
            reconciliation_id: 'second-gemini',
          }),
        ]}
      />,
    )
    const cards = screen.getAllByTestId('reconciliation-card-gemini')
    expect(cards).toHaveLength(1)
    expect(cards[0]).toHaveAttribute('data-status', 'matched')
  })
})
