/**
 * kala_ahead_get_w1_joins.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1,
 * item 32 half: "upcoming gulika-kālam windows within the forward horizon").
 *
 * Tests the new kala_ahead_get join field added on top of tools/kala_views/ahead.ts's
 * existing thin facade: gulika_kalam_ahead. A separate file from kala_ahead_get.test.ts
 * (not an edit to it) — this lane shares ahead.ts with several already-merged/in-flight
 * sibling lanes, and a new file carries far lower merge-conflict risk than editing the
 * existing suite.
 *
 * Contract gates:
 *   ✓ Gate W1 objectivity: gulika_kalam_ahead is a raw per-day window list — no grading.
 *   ✓ Gate W1 acceptance: present-and-non-empty when the range source resolves,
 *     honest-empty (via `coverage`) when it doesn't.
 *   ✓ gulika_kalam_ahead_horizon_days discloses the 30-day cap explicitly (never a silent
 *     truncation of the requested horizon_years).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const PANCHANGS = [
  { date: '2026-07-29', inauspicious: [{ label: 'rahu_kalam', start_utc: '2026-07-29T10:00:00Z', end_utc: '2026-07-29T11:30:00Z' }, { label: 'gulika_kalam', start_utc: '2026-07-29T06:00:00Z', end_utc: '2026-07-29T07:30:00Z' }] },
  { date: '2026-07-30', inauspicious: [{ label: 'gulika_kalam', start_utc: '2026-07-30T07:00:00Z', end_utc: '2026-07-30T08:30:00Z' }] },
  { date: '2026-07-31', inauspicious: [] }, // honest: a day with no gulika_kalam entry resolved is simply absent, not fabricated
]

function mockRegistryFetch(opts: { reachable: boolean; gulikaReachable?: boolean; panchangs?: typeof PANCHANGS }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: [] }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      if (opts.gulikaReachable === false) throw new Error('panchanga range service unreachable in test')
      inner = { panchangs: opts.panchangs ?? PANCHANGS, count: (opts.panchangs ?? PANCHANGS).length }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('kala_ahead_get W1 join — gulika_kalam_ahead (item 32)', () => {
  it('extracts one window per day carrying a gulika_kalam entry, verbatim', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_ahead).toEqual([
      { date: '2026-07-29', window_start_utc: '2026-07-29T06:00:00Z', window_end_utc: '2026-07-29T07:30:00Z' },
      { date: '2026-07-30', window_start_utc: '2026-07-30T07:00:00Z', window_end_utc: '2026-07-30T08:30:00Z' },
    ])
  })

  it('a day with no gulika_kalam entry is simply absent from the list — never fabricated', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_ahead.find((w) => w.date === '2026-07-31')).toBeUndefined()
  })

  it('discloses the 30-day horizon cap regardless of requested horizon_years', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, { horizon_years: 10 }, TEST_PRINCIPAL)
    expect(result.gulika_kalam_ahead_horizon_days).toBe(30)
  })

  it('coverage marks gulika_kalam_ahead computed when windows resolve', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['gulika_kalam_ahead']?.state).toBe('computed')
  })

  it('honest_empty (never fabricated) when the range service is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, gulikaReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_ahead).toEqual([])
    expect(result.provenance_envelope.gulika_kalam_reachable).toBe(false)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['gulika_kalam_ahead']?.state).toBe('honest_empty')
    expect(byConcept['gulika_kalam_ahead']?.reason?.length).toBeGreaterThan(0)
  })

  it('honest_empty when the range resolves but no day carries a gulika_kalam entry', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, panchangs: [{ date: '2026-07-29', inauspicious: [] }] }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.gulika_kalam_ahead).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['gulika_kalam_ahead']?.state).toBe('honest_empty')
  })
})
