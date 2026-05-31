/**
 * Cockpit page v2 mount gate.
 *
 * Verifies that CockpitShell renders all v2 components per VISUAL_CONTRACT_v2.md
 * and does NOT render legacy BuildConstellation / zodiac-wheel components.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CockpitShell } from '../CockpitShell'

// Stub fetch for active-build polling and progress hook
beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      if (String(url).includes('/api/build/active')) {
        return Promise.resolve(
          new Response(
            JSON.stringify([{ build_id: 'test-build-abc', status: 'running' }]),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
        )
      }
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    }),
  )
})

// Stub client-only hooks / EventSource
vi.stubGlobal('EventSource', vi.fn(() => ({ onopen: null, onerror: null, onmessage: null, close: vi.fn() })))

describe('CockpitShell v2 mount (VISUAL_CONTRACT_v2 Page 2)', () => {
  it('renders the cockpit shell wrapper', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.getByTestId('cockpit-shell')).toBeTruthy()
  })

  it('renders LiveDependencyGraph', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    // LiveDependencyGraph root element is data-testid="dependency-graph-svg"
    expect(screen.getByTestId('dependency-graph-svg')).toBeTruthy()
  })

  it('renders OverallProgress (Sampurna gati)', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.getByTestId('overall-progress')).toBeTruthy()
  })

  it('renders TelemetryStrip', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.getByTestId('telemetry-strip')).toBeTruthy()
  })

  it('renders AssetTable', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.getByTestId('asset-table')).toBeTruthy()
  })

  it('renders BuildControlsBar', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.getByTestId('build-controls-bar')).toBeTruthy()
  })

  it('does not render legacy BuildConstellation', () => {
    render(<CockpitShell chartId="test-chart-123" />)
    expect(screen.queryByTestId('build-constellation')).toBeNull()
    expect(screen.queryByTestId('constellation-canvas')).toBeNull()
  })
})
