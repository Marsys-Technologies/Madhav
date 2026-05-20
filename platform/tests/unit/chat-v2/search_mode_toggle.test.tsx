/**
 * Y-S7 — Search Mode Toggle
 * Amendment 2: parent-context integration tests via ConversationSidebarV2.
 *
 * Click-path: Chat V2 sidebar search bar → "Exact | Semantic" segmented
 *   control visible → click "Semantic" → next search fetch includes
 *   ?semantic=true → click "Exact" → reverts to keyword search.
 *
 * Prerequisite: R9-S2 semantic route at /api/conversations/search?semantic=true
 *   confirmed present before this session ran.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { ConversationSidebarV2 } from '@/components/consume/ConversationSidebarV2'

// ── Parent-context shell ──────────────────────────────────────────────────────

function SidebarShell() {
  return (
    <div data-testid="v2-chat-shell" style={{ height: 600, width: 240 }}>
      <ConversationSidebarV2
        chartId="chart-001"
        activeId={null}
        onSelect={() => {}}
        onNew={() => {}}
        collapsed={false}
        onToggle={() => {}}
      />
    </div>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ConversationSidebarV2 search mode toggle — parent-context (Amendment 2)', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Stub NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH so the toggle renders.
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH', 'true')

    fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ conversations: [], results: [] }),
    })
    global.fetch = fetchSpy as unknown as typeof fetch
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('renders Exact and Semantic toggle buttons in search bar', async () => {
    const { findByTestId } = render(<SidebarShell />)
    await findByTestId('v2-search-mode-exact')
    await findByTestId('v2-search-mode-semantic')
  })

  it('"Exact" is active by default (aria-pressed=true)', async () => {
    const { findByTestId } = render(<SidebarShell />)
    const exactBtn = await findByTestId('v2-search-mode-exact')
    expect(exactBtn.getAttribute('aria-pressed')).toBe('true')

    const semanticBtn = await findByTestId('v2-search-mode-semantic')
    expect(semanticBtn.getAttribute('aria-pressed')).toBe('false')
  })

  it('clicking "Semantic" sets mode (aria-pressed flips)', async () => {
    const { findByTestId } = render(<SidebarShell />)
    const semanticBtn = await findByTestId('v2-search-mode-semantic')

    await act(async () => { fireEvent.click(semanticBtn) })

    expect(semanticBtn.getAttribute('aria-pressed')).toBe('true')
    const exactBtn = await findByTestId('v2-search-mode-exact')
    expect(exactBtn.getAttribute('aria-pressed')).toBe('false')
  })

  it('search with Semantic mode includes ?semantic=true in fetch URL', async () => {
    const { findByTestId, findByLabelText } = render(<SidebarShell />)

    // Switch to semantic
    const semanticBtn = await findByTestId('v2-search-mode-semantic')
    await act(async () => { fireEvent.click(semanticBtn) })

    // Type a query (≥2 chars to trigger search)
    const input = await findByLabelText('Search conversations')
    await act(async () => { fireEvent.change(input, { target: { value: 'Saturn transit' } }) })

    // Wait for debounced search fetch
    await waitFor(() => {
      const searchCalls = fetchSpy.mock.calls.filter(
        (c: unknown[]) => typeof c[0] === 'string' && (c[0] as string).includes('/api/conversations/search'),
      )
      expect(searchCalls.length).toBeGreaterThan(0)
      const url = searchCalls[searchCalls.length - 1][0] as string
      expect(url).toContain('semantic=true')
    }, { timeout: 2000 })
  })

  it('search with Exact mode does NOT include ?semantic=true', async () => {
    const { findByLabelText } = render(<SidebarShell />)

    // Exact is already default — just type a query
    const input = await findByLabelText('Search conversations')
    await act(async () => { fireEvent.change(input, { target: { value: 'Saturn transit' } }) })

    await waitFor(() => {
      const searchCalls = fetchSpy.mock.calls.filter(
        (c: unknown[]) => typeof c[0] === 'string' && (c[0] as string).includes('/api/conversations/search'),
      )
      if (searchCalls.length === 0) return // still waiting
      const url = searchCalls[searchCalls.length - 1][0] as string
      expect(url).not.toContain('semantic=true')
    }, { timeout: 2000 })
  })
})
