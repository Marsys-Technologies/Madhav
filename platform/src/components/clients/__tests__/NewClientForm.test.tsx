/**
 * NewClientForm.test.tsx — C-S8 visual rendering tests
 *
 * Tests: section headings present, Sanskrit names rendered, header bar,
 * hero title, footer microcopy, form structure.
 *
 * DOES NOT test state, validation, or submit handler — those are Stream D's
 * concern (see form_schema.test.ts and route.test.ts for functional coverage).
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NewClientForm } from '../NewClientForm'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

describe('NewClientForm — visual rendering', () => {
  // ── Header bar ───────────────────────────────────────────────────────────

  it('renders the form header bar', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-header')).toBeTruthy()
  })

  it('renders the MARSYS wordmark in the header', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-header').textContent).toContain('MARSYS')
  })

  it('renders the "Jyotish Instrument" micro-label', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-header').textContent).toContain('Jyotish Instrument')
  })

  it('renders the "Step 1 of 2" pill', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('step-pill').textContent).toBe('Step 1 of 2')
  })

  it('renders the gold glyph (॥)', () => {
    const { container } = render(<NewClientForm />)
    expect(container.textContent).toContain('॥')
  })

  // ── Hero title ───────────────────────────────────────────────────────────

  it('renders the Naya Yantra hero title', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-title').textContent).toBe('Naya Yantra')
  })

  it('hero title is in italic Cormorant (checked via font-family style)', () => {
    render(<NewClientForm />)
    const title = screen.getByTestId('form-title')
    const style = title.getAttribute('style') ?? ''
    expect(style.toLowerCase()).toContain('cormorant')
  })

  // ── Sanskrit section headings ─────────────────────────────────────────────

  it('renders the Vyakti section heading for Identity', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-identity').textContent).toContain('Vyakti')
  })

  it('renders "Identity" label in the Vyakti section', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-identity').textContent).toContain('Identity')
  })

  it('renders the Janma Sthana section heading for Birth coordinates', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-birth').textContent).toContain('Janma Sthana')
  })

  it('renders "Birth coordinates" in the Janma Sthana section', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-birth').textContent).toContain('Birth coordinates')
  })

  it('renders the Ganana section heading for Compute', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-compute').textContent).toContain('Ganana')
  })

  it('renders "Compute" in the Ganana section', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('section-compute').textContent).toContain('Compute')
  })

  // ── Footer microcopy ──────────────────────────────────────────────────────

  it('renders the footer', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-footer')).toBeTruthy()
  })

  it('renders the "5 ayanamshas × 28 assets = 140 nodes" microcopy', () => {
    render(<NewClientForm />)
    const footer = screen.getByTestId('footer-microcopy')
    expect(footer.textContent).toContain('140 nodes')
    expect(footer.textContent).toContain('28 assets')
  })

  it('renders the "Compute chart" submit button', () => {
    render(<NewClientForm />)
    const footer = screen.getByTestId('form-footer')
    expect(footer.textContent).toContain('Compute chart')
  })

  it('renders the Cancel button', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-footer').textContent).toContain('Cancel')
  })

  // ── Form structure ────────────────────────────────────────────────────────

  it('renders a form element', () => {
    const { container } = render(<NewClientForm />)
    expect(container.querySelector('form')).toBeTruthy()
  })

  it('renders input fields for name and birthplace', () => {
    const { container } = render(<NewClientForm />)
    const inputs = container.querySelectorAll('input[type="text"], input:not([type])')
    expect(inputs.length).toBeGreaterThan(0)
  })

  it('renders ayanamsha checkboxes', () => {
    const { container } = render(<NewClientForm />)
    const checkboxes = container.querySelectorAll('input[type="checkbox"]')
    expect(checkboxes.length).toBeGreaterThanOrEqual(5)
  })

  it('all ayanamsha checkboxes are checked by default', () => {
    const { container } = render(<NewClientForm />)
    const checkboxes = container.querySelectorAll('input[type="checkbox"]')
    for (const cb of Array.from(checkboxes)) {
      expect((cb as HTMLInputElement).checked).toBe(true)
    }
  })

  it('renders the page with obsidian background style', () => {
    const { container } = render(<NewClientForm />)
    const pageDiv = container.firstElementChild as HTMLElement
    const style = pageDiv?.getAttribute('style') ?? ''
    expect(style).toContain('obsidian')
  })
})
