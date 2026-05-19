/**
 * AskMadhavLink unit tests — AC.4C8.1 + AC.4C8.6
 *
 * Tests:
 *   - Component renders a button with correct aria-label
 *   - Click navigates to correct URL with encoded prompt
 *   - Context within 10 KB passes through unmodified
 *   - Context over 10 KB is trimmed to essentials (_truncated: true)
 *   - 30-day range injection budget guard (AC.4C8.6)
 *   - serialiseContext utility directly
 *
 * Phase: 4C-8 (Item 8)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AskMadhavLink, serialiseContext, DEFAULT_CHART_ID } from '../components/AskMadhavLink'

// ── Mock next/navigation ──────────────────────────────────────────────────────

const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Build a fake Panchang day object of approximately `targetKB` kilobytes.
 * Uses a repeated string payload in the `_padding` key.
 */
function buildFakePanchang(targetKB: number): Record<string, unknown> {
  const padding = 'x'.repeat(targetKB * 1024)
  return {
    date: '2026-05-20',
    lat: 20.2961,
    lon: 85.8245,
    angas: { tithi: { name: 'Chaturthi', number: 4 } },
    timings: { sunrise_utc: '2026-05-20T00:12:00Z', sunset_utc: '2026-05-20T13:38:00Z' },
    _padding: padding,
  }
}

// ── Tests: serialiseContext ───────────────────────────────────────────────────

describe('serialiseContext', () => {
  it('passes small payloads through unmodified', () => {
    const ctx = { date: '2026-05-20', angas: { tithi: { name: 'Chaturthi' } } }
    const result = JSON.parse(serialiseContext(ctx)) as Record<string, unknown>
    expect(result).toMatchObject(ctx)
    expect(result['_truncated']).toBeUndefined()
  })

  it('truncates payloads over 10 KB and sets _truncated: true', () => {
    const big = buildFakePanchang(15) // 15 KB — well over the 10 KB guard
    const result = JSON.parse(serialiseContext(big)) as Record<string, unknown>
    expect(result['_truncated']).toBe(true)
    expect(typeof result['_note']).toBe('string')
    expect((result['_note'] as string).toLowerCase()).toContain('query_panchanga')
    // Essential fields preserved
    expect(result['date']).toBe('2026-05-20')
    expect(result['angas']).toBeDefined()
    // Padding stripped
    expect(result['_padding']).toBeUndefined()
  })

  it('30-day range simulation (AC.4C8.6) — truncates gracefully', () => {
    // A 30-day range would be ~30× the single-day payload ≈ 120-150 KB
    const thirtyDays = Array.from({ length: 30 }, (_, i) => buildFakePanchang(5))
    const rangeCtx = { range: thirtyDays, date: '2026-05-20' }
    const serialised = serialiseContext(rangeCtx)
    const result = JSON.parse(serialised) as Record<string, unknown>
    expect(result['_truncated']).toBe(true)
    // Ensure the output is under 10 KB
    const byteLen = new TextEncoder().encode(serialised).length
    expect(byteLen).toBeLessThanOrEqual(10_240)
  })

  it('serialises payload that is exactly at the 10 KB limit without truncating', () => {
    // Build a payload that serialises to ≤ 10 240 bytes
    const ctx = { date: '2026-05-20', data: 'x'.repeat(8_000) }
    const result = JSON.parse(serialiseContext(ctx)) as Record<string, unknown>
    expect(result['_truncated']).toBeUndefined()
  })
})

// ── Tests: AskMadhavLink component ───────────────────────────────────────────

describe('AskMadhavLink', () => {
  beforeEach(() => mockPush.mockClear())

  it('renders a button with MessageCircle icon', () => {
    render(<AskMadhavLink prompt="What does Chaturthi mean for me today?" />)
    const btn = screen.getByRole('button')
    expect(btn).toBeInTheDocument()
  })

  it('shows truncated tooltip in aria-label and title', () => {
    const prompt = 'What does Chaturthi mean for me today?'
    render(<AskMadhavLink prompt={prompt} />)
    const btn = screen.getByRole('button')
    expect(btn.getAttribute('title')).toContain(prompt)
    expect(btn.getAttribute('aria-label')).toContain(prompt)
  })

  it('truncates tooltip for long prompts (>60 chars)', () => {
    const longPrompt = 'A'.repeat(80)
    render(<AskMadhavLink prompt={longPrompt} />)
    const btn = screen.getByRole('button')
    const tooltip = btn.getAttribute('title') ?? ''
    expect(tooltip).toContain('…')
    expect(tooltip.length).toBeLessThan(longPrompt.length + 20)
  })

  it('click pushes to correct URL with encoded prompt (no context)', () => {
    const prompt = 'What does Chaturthi mean for me today?'
    render(<AskMadhavLink prompt={prompt} />)
    fireEvent.click(screen.getByRole('button'))
    expect(mockPush).toHaveBeenCalledOnce()
    const url = mockPush.mock.calls[0][0] as string
    expect(url).toContain(`/clients/${DEFAULT_CHART_ID}/consume`)
    expect(url).toContain(`prompt=`)
    // URLSearchParams encodes spaces as '+'; decode both '+' and '%20'
    const rawPrompt = new URLSearchParams(url.split('?')[1]).get('prompt') ?? ''
    expect(rawPrompt).toBe(prompt)
    expect(url).not.toContain('context=')
  })

  it('click injects context when provided (AC.4C8.1)', () => {
    const prompt = 'What does Chaturthi mean for me today?'
    const ctx = { date: '2026-05-20', angas: { tithi: { name: 'Chaturthi' } } }
    render(<AskMadhavLink prompt={prompt} panchang_context={ctx} />)
    fireEvent.click(screen.getByRole('button'))
    const url = mockPush.mock.calls[0][0] as string
    expect(url).toContain('context=')
    const rawContext = new URLSearchParams(url.split('?')[1]).get('context') ?? ''
    const parsed = JSON.parse(rawContext) as Record<string, unknown>
    expect(parsed['date']).toBe('2026-05-20')
  })

  it('uses custom chart_id when provided', () => {
    render(<AskMadhavLink prompt="Test" chart_id="custom_chart_id_123" />)
    fireEvent.click(screen.getByRole('button'))
    const url = mockPush.mock.calls[0][0] as string
    expect(url).toContain('/clients/custom_chart_id_123/consume')
  })

  it('large context is truncated before URL encoding (AC.4C8.6)', () => {
    const prompt = 'Test big context'
    const bigCtx = buildFakePanchang(15)
    render(<AskMadhavLink prompt={prompt} panchang_context={bigCtx} />)
    fireEvent.click(screen.getByRole('button'))
    const url = mockPush.mock.calls[0][0] as string
    const rawContext = new URLSearchParams(url.split('?')[1]).get('context') ?? ''
    const parsed = JSON.parse(rawContext) as Record<string, unknown>
    expect(parsed['_truncated']).toBe(true)
    // Context part should be under 10 KB encoded
    const byteLen = new TextEncoder().encode(rawContext).length
    expect(byteLen).toBeLessThanOrEqual(10_240)
  })
})
