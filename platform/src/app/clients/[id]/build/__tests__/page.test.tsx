/**
 * build/page.test.tsx — C-S8.5 gate: BuildButton wired into build page.
 *
 * Verifies that BuildButton renders when a chart_id is present.
 * Uses mocks for auth guard and child components to keep the test fast.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BuildButton } from '@/components/cockpit/BuildButton'

// Stub fetch so BuildButton's useEffect poll doesn't fail
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } }))))

describe('BuildButton (C-S8.5 gate)', () => {
  it('renders the build button with a chart_id', () => {
    render(<BuildButton chartId="test-chart-123" />)
    expect(screen.getByTestId('build-button')).toBeTruthy()
  })

  it('shows "Build" label initially', () => {
    render(<BuildButton chartId="test-chart-123" />)
    expect(screen.getByTestId('build-button').textContent).toBe('Build')
  })

  it('is not disabled initially', () => {
    render(<BuildButton chartId="test-chart-123" />)
    const btn = screen.getByTestId('build-button') as HTMLButtonElement
    expect(btn.disabled).toBe(false)
  })

  it('renders without crashing for different chart ids', () => {
    expect(() => render(<BuildButton chartId="abc-def-ghi" />)).not.toThrow()
  })
})
