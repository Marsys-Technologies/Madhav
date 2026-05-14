import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ── Mock the 5 child widgets ──────────────────────────────────────────────────
vi.mock('@/components/build/JourneyStrip', () => ({
  JourneyStrip: () => <div data-testid="journey-strip" />,
}))

vi.mock('@/components/build/BriefPanel', () => ({
  BriefPanel: () => <div data-testid="brief-panel" />,
}))

vi.mock('@/components/build/InsightCards', () => ({
  InsightCards: ({ insights }: { insights: unknown[] }) => (
    <div data-testid="insight-cards" data-count={insights.length} />
  ),
}))

vi.mock('@/components/build/MirrorPairsTable', () => ({
  MirrorPairsTable: () => <div data-testid="mirror-pairs-table" />,
}))

vi.mock('@/components/build/PyramidStatusPanel', () => ({
  PyramidStatusPanel: () => <div data-testid="pyramid-status-panel" />,
}))

// ── Import the component under test ──────────────────────────────────────────
import { BuildRightPane } from '@/components/build/BuildRightPane'

const defaultProps = {
  arc: [{ id: 'M1', title: 'Foundation', status: 'completed' as const, milestones: [] }],
  activePhaseId: 'M1',
  brief: null,
  insights: [{ id: '1', severity: 'positive' as const, text: 'L1 built' }],
  mirrorPairs: [],
  layers: [],
}

describe('BuildRightPane', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not render InsightCards when insights array is empty', () => {
    render(<BuildRightPane {...defaultProps} insights={[]} />)
    expect(screen.queryByTestId('insight-cards')).toBeNull()
  })

  it('PyramidStatusPanel is collapsed by default (not visible)', () => {
    render(<BuildRightPane {...defaultProps} />)
    expect(screen.queryByTestId('pyramid-status-panel')).toBeNull()
  })

  it('clicking the toggle opens PyramidStatusPanel', async () => {
    render(<BuildRightPane {...defaultProps} />)
    const toggle = screen.getByRole('button', { name: /pyramid layers/i })
    await userEvent.click(toggle)
    expect(screen.getByTestId('pyramid-status-panel')).toBeTruthy()
  })

  it('clicking the toggle a second time closes PyramidStatusPanel', async () => {
    render(<BuildRightPane {...defaultProps} />)
    const toggle = screen.getByRole('button', { name: /pyramid layers/i })
    await userEvent.click(toggle)
    expect(screen.getByTestId('pyramid-status-panel')).toBeTruthy()
    await userEvent.click(toggle)
    expect(screen.queryByTestId('pyramid-status-panel')).toBeNull()
  })

  it('renders all 5 widget areas in the correct document order', async () => {
    render(<BuildRightPane {...defaultProps} />)
    // Open pyramid panel so all 5 are present
    await userEvent.click(screen.getByRole('button', { name: /pyramid layers/i }))

    const aside = screen.getByRole('complementary')
    const testIds = [
      'journey-strip',
      'brief-panel',
      'insight-cards',
      'mirror-pairs-table',
      'pyramid-status-panel',
    ]
    const elements = testIds.map(id => aside.querySelector(`[data-testid="${id}"]`))
    elements.forEach(el => expect(el).toBeTruthy())

    // Verify DOM order — each element must appear after the previous one
    for (let i = 0; i < elements.length - 1; i++) {
      const pos = elements[i]!.compareDocumentPosition(elements[i + 1]!)
      // Node.DOCUMENT_POSITION_FOLLOWING === 4
      expect(pos & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
  })
})
