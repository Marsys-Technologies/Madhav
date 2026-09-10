/**
 * P2-close Lane K (PPR-03 typed confidence, G3-C) — GroundingCard's new
 * confidenceType prop. The receipt types every citation this turn by `ref`
 * (TypedConfidenceEntrySchema's own doc comment: "same token as
 * facts_consumed[].ref"), the same token `GroundingCard`'s own `citation.ref`
 * already carries — `RightDock.tsx` looks the type up and passes it through.
 * Honest-absence discipline (§N.7 item 6): no prop, no label — never a
 * guessed type.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { GroundingCard } from '@/components/pariprashna/dock/GroundingCard'
import type { Citation } from '@/components/pariprashna/state/types'
import type { ConfidenceType } from '@/lib/pariprashna/confidence/types'

afterEach(cleanup)

const CITATION: Citation = {
  n: 1,
  title: 'Moon in the 12th house of the D9 chart',
  sourceClass: 'chart_factor',
  relevance: 'Navamsha placement',
  ref: 'DVS.D9.MOON',
  grade: 'confirmed',
}

describe('GroundingCard — Lane K typed-confidence label', () => {
  it('renders the confidence-type label alongside the ref when the card is expanded', () => {
    render(<GroundingCard citation={CITATION} highlighted={false} confidenceType="structural_prior" />)
    fireEvent.click(screen.getByText(CITATION.title))
    expect(screen.getByText('DVS.D9.MOON', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('structural signal')).toBeInTheDocument()
  })

  it('renders no confidence label when confidenceType is omitted (honest absence, not a guess)', () => {
    render(<GroundingCard citation={CITATION} highlighted={false} />)
    fireEvent.click(screen.getByText(CITATION.title))
    expect(screen.getByText('DVS.D9.MOON', { exact: false })).toBeInTheDocument()
    expect(screen.queryByText('structural signal')).toBeNull()
    expect(screen.queryByText('untyped')).toBeNull()
  })

  it('maps every PPR-03 confidence type to a distinct reader-facing label', () => {
    const cases: Array<[ConfidenceType, string]> = [
      ['deterministic_fact', 'chart fact'],
      ['classical_prior', 'classical source'],
      ['empirically_calibrated', 'calibrated'],
      ['unresolved', 'untyped'],
    ]
    for (const [type, label] of cases) {
      const { unmount } = render(<GroundingCard citation={CITATION} highlighted={false} confidenceType={type} />)
      fireEvent.click(screen.getByText(CITATION.title))
      expect(screen.getByText(label)).toBeInTheDocument()
      unmount()
    }
  })
})
