/**
 * kala_timeline.test.ts — BRAHMA-KA-3-1 acceptance tests
 *
 * Tests exercise the pure algorithmic computation path (computeTimelineAlgorithmic
 * via the tool's fallback) without requiring a live DB.
 *
 * Acceptance gates per KA-3-1 contract:
 *   - Saturn MD present for dates in 1991-08-21 → 2010-08-21
 *   - Mercury MD present for dates in 2010-08-21 → 2027-08-21
 *   - source_citation non-null on all rows
 *   - deterministic: same date always returns same MD
 *   - tool smoke: timeline_query responds with provenance_envelope
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { registerKalaTimeline } from '../tools/kala_timeline.js'

// ── Test principal ────────────────────────────────────────────────────────────

const MOCK_PRINCIPAL: Principal = {
  uid: 'test-uid',
  email: 'test@example.com',
}

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

// ── Helper: call tool via registered handler ──────────────────────────────────

/**
 * Build a minimal McpServer, register kala_timeline, and invoke the tool
 * handler directly by introspecting the registered tools.
 *
 * This avoids spinning up an HTTP server while still exercising the real
 * registration path.
 */
async function callTool(params: Record<string, unknown>): Promise<unknown> {
  // Spy on registerTool to capture the handler
  let capturedHandler: ((p: unknown) => Promise<unknown>) | null = null
  const mockServer = {
    registerTool: (_name: string, _schema: unknown, handler: (p: unknown) => Promise<unknown>) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerKalaTimeline(mockServer, MOCK_PRINCIPAL)

  if (!capturedHandler) throw new Error('Tool handler was not registered')
  return capturedHandler(params)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('kala_timeline KA-3-1 — algorithmic computation', () => {
  // G1: Saturn MD present for 1991–2010
  it('returns Saturn as active_mahadasha for date 2000-01-01', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2000-01-01', end: '2000-01-01' },
      limit: 1,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.timeline).toHaveLength(1)
    expect(parsed.timeline[0].active_mahadasha).toBe('Saturn')
  })

  // G2: Mercury MD present for 2010–2027
  it('returns Mercury as active_mahadasha for date 2015-06-01', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2015-06-01', end: '2015-06-01' },
      limit: 1,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.timeline).toHaveLength(1)
    expect(parsed.timeline[0].active_mahadasha).toBe('Mercury')
  })

  // G3: source_citation non-null
  it('source_citation is non-null and correct on all rows', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '1991-08-21', end: '1991-09-20' },
      limit: 31,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.timeline.length).toBeGreaterThan(0)
    for (const row of parsed.timeline) {
      expect(row.source_citation).toBeTruthy()
      expect(row.source_citation).toBe('PyJHora/SwissEph DE441 + Brahma-L1')
    }
  })

  // G4: deterministic
  it('same date always returns same MD (deterministic)', async () => {
    const params = {
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2005-07-15', end: '2005-07-15' },
      limit: 1,
    }
    const r1 = await callTool(params) as { content: Array<{ text: string }> }
    const r2 = await callTool(params) as { content: Array<{ text: string }> }

    const p1 = JSON.parse(r1.content[0].text)
    const p2 = JSON.parse(r2.content[0].text)
    expect(p1.timeline[0].active_mahadasha).toBe(p2.timeline[0].active_mahadasha)
    expect(p1.timeline[0].active_antardasha).toBe(p2.timeline[0].active_antardasha)
  })

  // G5: provenance_envelope present
  it('response includes provenance_envelope with required fields', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '1984-01-01', end: '2026-12-31' },
      limit: 100,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.provenance_envelope).toBeDefined()
    expect(parsed.provenance_envelope.asset).toBe('kala.timeline')
    expect(parsed.provenance_envelope.unit).toBe('KA-3-1')
    expect(parsed.provenance_envelope.source).toBe('PyJHora/SwissEph DE441 + Brahma-L1')
    expect(parsed.provenance_envelope.layer).toBe('L3 Kāla')
    expect(parsed.provenance_envelope.depends).toContain('L1 ganita.dashas')
    expect(parsed.provenance_envelope.chart_id).toBe(NATIVE_CHART_ID)
    expect(parsed.provenance_envelope.count).toBeGreaterThan(0)
  })

  // Tool smoke: range 1984–2026
  it('tool smoke: date range 1984-02-05 → 2026-12-31 returns timeline rows', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '1984-02-05', end: '2026-12-31' },
      limit: 365,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(Array.isArray(parsed.timeline)).toBe(true)
    expect(parsed.timeline.length).toBe(365)
    expect(parsed.provenance_envelope.range.start).toBe('1984-02-05')
  })

  // Saturn MD boundary: 1991-08-21 is Saturn MD start
  it('1991-08-21 is Saturn MD start boundary', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '1991-08-21', end: '1991-08-21' },
      limit: 1,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.timeline[0].active_mahadasha).toBe('Saturn')
  })

  // Mercury MD boundary: 2010-08-21 is Mercury MD start
  it('2010-08-21 is Mercury MD start boundary', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2010-08-21', end: '2010-08-21' },
      limit: 1,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.timeline[0].active_mahadasha).toBe('Mercury')
  })

  // Error handling: start > end
  it('returns error when start > end', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2026-01-01', end: '2024-01-01' },
      limit: 1,
    }) as { content: Array<{ text: string }>; isError?: boolean }

    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.error).toBeTruthy()
  })

  // AD lord for Saturn-Saturn period
  it('1993-01-01 has Saturn as active_antardasha (Sat-Sat AD, DSH.V.006)', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '1993-01-01', end: '1993-01-01' },
      limit: 1,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    // Both MD and AD should be Saturn in 1993
    expect(parsed.timeline[0].active_mahadasha).toBe('Saturn')
    expect(parsed.timeline[0].active_antardasha).toBe('Saturn')
  })

  // Row structure completeness
  it('each row has all required fields', async () => {
    const result = await callTool({
      chart_id: NATIVE_CHART_ID,
      date_range: { start: '2020-01-01', end: '2020-01-05' },
      limit: 5,
    }) as { content: Array<{ text: string }> }

    const parsed = JSON.parse(result.content[0].text)
    for (const row of parsed.timeline) {
      expect(row).toHaveProperty('date')
      expect(row).toHaveProperty('active_mahadasha')
      expect(row).toHaveProperty('active_antardasha')
      expect(row).toHaveProperty('transit_highlights')
      expect(row).toHaveProperty('signal_activations')
      expect(row).toHaveProperty('source_citation')
      expect(Array.isArray(row.transit_highlights)).toBe(true)
      expect(Array.isArray(row.signal_activations)).toBe(true)
    }
  })
})
