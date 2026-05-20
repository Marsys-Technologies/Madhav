/**
 * Y-S2 — Citation Freshness Badge
 * Amendment 2: parent-context integration tests using CitationCtxShell.
 *
 * Click-path: Chat V2 response with [^N] citations → each badge shows a small
 *   colored dot: green (confidence ≥0.8), yellow (0.5–0.79), red (<0.5).
 *   No dot when confidence=undefined. Guarded by NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS.
 *
 * Amendment 1: flag MUST be in deploy.yml --build-arg (verified via acceptance grep).
 *
 * Decision log: confidence field added to CitationPartSchema in data_parts.ts
 * as optional number. Server does not yet emit it (confidence will be absent/
 * undefined in current production data — dots absent until server emits field).
 * Client-side code is ready. See commit body for caveat.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import React from 'react'
import { NumberedCitation } from '@/components/chat/NumberedCitation'

// ── Parent-context shell ──────────────────────────────────────────────────────

function CitationCtxShell({ children }: { children: React.ReactNode }) {
  return (
    <div data-testid="v2-chat-shell">
      <div data-testid="v2-message">{children}</div>
    </div>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('NumberedCitation confidence dot — parent-context (Amendment 2)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('renders green dot for confidence=0.9 (high)', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" confidence={0.9} />
      </CitationCtxShell>,
    )
    const dot = getByTestId('v2-citation-confidence-dot')
    expect(dot).toBeTruthy()
    expect(dot.getAttribute('data-confidence-band')).toBe('high')
    expect(dot.className).toContain('bg-green-500')
  })

  it('renders yellow dot for confidence=0.65 (medium)', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={2} signalId="SIG.MSR.002" confidence={0.65} />
      </CitationCtxShell>,
    )
    const dot = getByTestId('v2-citation-confidence-dot')
    expect(dot.getAttribute('data-confidence-band')).toBe('medium')
    expect(dot.className).toContain('bg-yellow-500')
  })

  it('renders red dot for confidence=0.3 (low)', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={3} signalId="SIG.MSR.003" confidence={0.3} />
      </CitationCtxShell>,
    )
    const dot = getByTestId('v2-citation-confidence-dot')
    expect(dot.getAttribute('data-confidence-band')).toBe('low')
    expect(dot.className).toContain('bg-red-500')
  })

  it('renders no dot when confidence=undefined', () => {
    const { queryByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={4} signalId="SIG.MSR.004" confidence={undefined} />
      </CitationCtxShell>,
    )
    expect(queryByTestId('v2-citation-confidence-dot')).toBeNull()
  })

  it('renders no dot when flag=false', () => {
    vi.unstubAllEnvs()
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS', 'false')

    const { queryByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" confidence={0.9} />
      </CitationCtxShell>,
    )
    expect(queryByTestId('v2-citation-confidence-dot')).toBeNull()
  })

  it('dot has aria-label with confidence level', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" confidence={0.8} />
      </CitationCtxShell>,
    )
    const dot = getByTestId('v2-citation-confidence-dot')
    expect(dot.getAttribute('aria-label')).toContain('high')
  })

  it('boundary: confidence=0.8 is green (high), confidence=0.5 is yellow (medium)', () => {
    const { rerender, getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" confidence={0.8} />
      </CitationCtxShell>,
    )
    expect(getByTestId('v2-citation-confidence-dot').getAttribute('data-confidence-band')).toBe('high')

    rerender(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" confidence={0.5} />
      </CitationCtxShell>,
    )
    expect(getByTestId('v2-citation-confidence-dot').getAttribute('data-confidence-band')).toBe('medium')
  })
})
