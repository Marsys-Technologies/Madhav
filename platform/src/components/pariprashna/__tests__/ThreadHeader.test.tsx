/**
 * V3-E-062 — the Portal rendered zero h1-h6 elements anywhere on the page:
 * landmarks and the skip-link were correctly present, but a screen-reader
 * user navigating by heading (VoiceOver's rotor, NVDA's `H` key) found
 * nothing on any surface state. `ThreadHeader` renders unconditionally
 * ahead of both the empty state and the transcript (see
 * `PariprashnaApp.tsx`), so giving the chart-holder name a real `<h1>`
 * covers every surface state with a single, always-present heading.
 *
 * This test is demonstrated-can-fail: reverting the `<h1>` back to a plain
 * `<div>` makes `getByRole('heading', { level: 1 })` throw.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThreadHeader } from '../ThreadHeader'

describe('ThreadHeader', () => {
  it('renders the chart-holder name as a real h1 heading', () => {
    render(<ThreadHeader chartPin={{ name: 'Abhisek Mohanty', bornLine: '05 Feb 1984 · 10:43 · Bhubaneswar' }} />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Abhisek Mohanty')
  })
})
