/**
 * dashboard_components.test.tsx — Render tests for the dashboard components.
 *
 * Tests:
 *   1. CaveatEditor renders existing caveats
 *   2. CaveatEditor shows "Add caveat" button
 *   3. ToolDisableToggle renders enabled state
 *   4. ToolDisableToggle renders disabled state
 *   5. PredictionsCalibration renders placeholder text
 *   6. McpHealthDashboard renders without crashing (tab structure)
 *
 * MCPT v3.1.0-S5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock fetch globally
vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) } as Response))

// Wrapper to provide React Query context
function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  }
}

// ── CaveatEditor ──────────────────────────────────────────────────────────────

import { CaveatEditor } from '@/app/admin/mcp/health/components/CaveatEditor'

describe('CaveatEditor', () => {
  it('renders with no caveats showing placeholder text', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <CaveatEditor toolName="query_chart_facts" initialCaveats={[]} />
      </Wrapper>
    )
    expect(screen.getByText(/No caveats/i)).toBeTruthy()
  })

  it('renders existing caveats with class badge', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    const caveats = [
      {
        id: 'c1',
        caveat_text: 'KP backfill pending v3.3',
        caveat_class: 'data_depth_gap',
        severity: 'warn',
      },
    ]
    render(
      <Wrapper>
        <CaveatEditor toolName="query_chart_facts" initialCaveats={caveats} />
      </Wrapper>
    )
    expect(screen.getByText('KP backfill pending v3.3')).toBeTruthy()
    expect(screen.getByText('data depth gap')).toBeTruthy()
  })

  it('shows Add caveat button', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <CaveatEditor toolName="query_chart_facts" initialCaveats={[]} />
      </Wrapper>
    )
    expect(screen.getByText(/Add caveat/i)).toBeTruthy()
  })

  it('renders tool name in the heading', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <CaveatEditor toolName="vector_search" initialCaveats={[]} />
      </Wrapper>
    )
    expect(screen.getByText(/vector_search/)).toBeTruthy()
  })
})

// ── ToolDisableToggle ─────────────────────────────────────────────────────────

import { ToolDisableToggle } from '@/app/admin/mcp/health/components/ToolDisableToggle'

describe('ToolDisableToggle', () => {
  it('renders in enabled state', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <ToolDisableToggle toolName="query_chart_facts" enabled={true} />
      </Wrapper>
    )
    const toggle = screen.getByRole('button')
    expect(toggle).toBeTruthy()
    expect(toggle.title).toContain('Disable')
  })

  it('renders in disabled state', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <ToolDisableToggle toolName="vector_search" enabled={false} />
      </Wrapper>
    )
    const toggle = screen.getByRole('button')
    expect(toggle.title).toContain('Re-enable')
  })

  it('has sr-only text for accessibility', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <ToolDisableToggle toolName="query_signals" enabled={true} />
      </Wrapper>
    )
    expect(screen.getByText('Enabled')).toBeTruthy()
  })
})

// ── PredictionsCalibration ────────────────────────────────────────────────────

import { PredictionsCalibration } from '@/app/admin/mcp/health/tabs/PredictionsCalibration'

describe('PredictionsCalibration', () => {
  it('renders placeholder heading', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <PredictionsCalibration />
      </Wrapper>
    )
    expect(screen.getByText(/Calibration data available in v3.4/i)).toBeTruthy()
  })

  it('renders the preview table rows', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <PredictionsCalibration />
      </Wrapper>
    )
    expect(screen.getByText('0.7–0.8')).toBeTruthy()
  })

  it('mentions log_prediction and record_outcome tools', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <PredictionsCalibration />
      </Wrapper>
    )
    expect(screen.getByText(/log_prediction/)).toBeTruthy()
    expect(screen.getByText(/record_outcome/)).toBeTruthy()
  })
})

// ── McpHealthDashboard ────────────────────────────────────────────────────────

import { McpHealthDashboard } from '@/app/admin/mcp/health/McpHealthDashboard'

describe('McpHealthDashboard', () => {
  it('renders without crashing', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <McpHealthDashboard />
      </Wrapper>
    )
    expect(screen.getByText('MCP Health Dashboard')).toBeTruthy()
  })

  it('renders all 5 tab triggers', () => {
    const { Wrapper } = { Wrapper: createWrapper() }
    render(
      <Wrapper>
        <McpHealthDashboard />
      </Wrapper>
    )
    expect(screen.getByText('Tool Health')).toBeTruthy()
    expect(screen.getByText('Data Coverage')).toBeTruthy()
    expect(screen.getByText('Audit Findings')).toBeTruthy()
    expect(screen.getByText('Predictions / Calibration')).toBeTruthy()
    expect(screen.getByText('Sessions')).toBeTruthy()
  })
})
