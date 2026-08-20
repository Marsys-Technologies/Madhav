/**
 * The empty-state invocation (§5.3 `empty`) + the arrival line (§3.2, J2,
 * AC-16), rendered at their defined trigger conditions.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { EmptyState } from '@/components/pariprashna/EmptyState'
import { ArrivalLine } from '@/components/pariprashna/ArrivalLine'
import { FIXTURE_ARRIVAL_LINE } from '@/components/pariprashna/fixtures/arrival'

afterEach(cleanup)

describe('EmptyState — the invocation (§5.3 `empty`)', () => {
  it('renders the ecliptic hairline, the invocation line, and chart-aware example prompts', () => {
    const prompts = ['What does this period ask of my career?', 'Is a career change on the cards?', 'When should I not initiate anything new?']
    render(<EmptyState examplePrompts={prompts} onPick={() => {}} />)

    expect(document.querySelector('.pp-hairline-draw')).not.toBeNull()
    expect(screen.getByText('Ask the chart.')).toBeInTheDocument()
    for (const p of prompts) {
      expect(screen.getByText(p)).toBeInTheDocument()
    }
  })

  it('never renders generic placeholder examples or cosmic-theater copy (§5.3 "Never")', () => {
    render(<EmptyState examplePrompts={['What does this period ask of my career?']} onPick={() => {}} />)
    expect(screen.queryByText(/tell me about astrology/i)).toBeNull()
  })

  it('invokes onPick with the exact prompt text when a pill is clicked', () => {
    let picked: string | null = null
    render(<EmptyState examplePrompts={['A specific chart-aware prompt']} onPick={(t) => (picked = t)} />)
    fireEvent.click(screen.getByText('A specific chart-aware prompt'))
    expect(picked).toBe('A specific chart-aware prompt')
  })
})

describe('ArrivalLine — chrome, once per session, honest-null when unwired (AC-16)', () => {
  it('renders nothing when no arrival data is supplied (the live-host default until P4-F)', () => {
    const { container } = render(<ArrivalLine arrival={null} />)
    expect(container).toBeEmptyDOMElement()
    expect(screen.queryByTestId('pp-arrival-line')).toBeNull()
  })

  it('renders the supplied line verbatim when data IS supplied (the fixture host)', () => {
    render(<ArrivalLine arrival={FIXTURE_ARRIVAL_LINE} />)
    const el = screen.getByTestId('pp-arrival-line')
    expect(el).toHaveTextContent(FIXTURE_ARRIVAL_LINE.text)
  })

  it('never fabricates content — the fixture sample is labelled as a fixture, not asserted as real daśā truth', () => {
    // A structural guard against silently swapping the labelled fixture for
    // something that reads as authoritative: the sample must say so of itself.
    expect(FIXTURE_ARRIVAL_LINE.text.toLowerCase()).toContain('fixture')
  })
})
