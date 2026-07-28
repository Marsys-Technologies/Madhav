/**
 * SAMĪKṢĀ badge render — PB-3 lane L-3. The badge shows the count and is NEVER red (§10.2 /
 * W-2: non-alarming). This asserts the DOM value + that the styling references the gold-dim
 * token family and contains no red anywhere (demonstrate-can-fail: a red badge would fail).
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { SamiksaBadge } from '@/components/pariprashna/samiksha/SamiksaBadge'

afterEach(cleanup)

const RED = /(?:^|[^a-z])red|#f[0-9a-f]{0,2}0{2,}|rgb\(\s*2(?:5[0-5]|00)\s*,\s*0\s*,\s*0/i

describe('SamiksaBadge', () => {
  it('renders the count and is styled with the non-red gold-dim token', () => {
    const { container } = render(<SamiksaBadge count={5} />)
    const el = container.querySelector('.samiksa-badge') as HTMLElement
    expect(el).not.toBeNull()
    expect(el.textContent).toBe('5')
    const style = el.getAttribute('style') ?? ''
    expect(style).toContain('gold-dim')
    expect(style).not.toMatch(RED)
    // Accessible, non-shameful name — no "failed"/"overdue" framing.
    const label = el.getAttribute('aria-label') ?? ''
    expect(label).toMatch(/to review/)
    expect(label).not.toMatch(/fail|overdue|debt|behind/i)
  })

  it('renders nothing when the count is zero (empty queue needs no ornament)', () => {
    const { container } = render(<SamiksaBadge count={0} />)
    expect(container.querySelector('.samiksa-badge')).toBeNull()
  })

  it('pluralises the accessible label correctly', () => {
    render(<SamiksaBadge count={1} />)
    expect(screen.getByLabelText('1 prediction item to review')).toBeTruthy()
  })
})
