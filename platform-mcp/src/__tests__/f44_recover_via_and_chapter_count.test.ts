/**
 * f44_recover_via_and_chapter_count.test.ts — F-44 exit tests (PARIŚEṢA-RĀTRI)
 *
 * F-44b: response_budget collapse fallback never names a fictional recovery instrument
 *   — both emission sites in response_budget.ts (applyResponseBudget + finalizeMcpBudget)
 *
 * F-44a: kala_story_get chapter_count stays in sync with chapters after trim
 *   — story.ts must resync chapter_count from post-trim chapters.length
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { applyResponseBudget, finalizeMcpBudget, type TrimmableSection } from '../lib/response_budget.js'
import { handleKalaStoryGet } from '../tools/kala_views/story.js'
import type { Principal } from '../types.js'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'super_admin' }

// ── Minimal parva row factory — each row serialises to ~400B JSON after processing ──

function makeParva(index: number): Record<string, unknown> {
  return {
    id: index,
    parva_index: index,
    dasha_planet: ['Jupiter', 'Saturn', 'Mercury', 'Venus', 'Sun'][index % 5],
    dominant_signal_class: null,
    start_year: 1960 + index * 2,
    end_year: 1960 + index * 2 + 16,
    parva_quality: 'building',
    theme_keywords: ['career', 'growth'],
    high_convergence_count: 1,
    avg_effective_score: 0.6,
    narrative: {
      text:
        `Chapter ${index}: This is a moderately detailed narrative text for testing purposes. ` +
        'It contains enough content to make each chapter large enough that a collection of ten ' +
        'or more chapters will exceed a 2KB budget when combined with the envelope overhead, ' +
        'reliably triggering budget trimming without requiring a live database.',
    },
    source_citation: 'kala_jivana_parva',
    computed_at: '2026-01-01T00:00:00Z',
  }
}

// ── Mock fetch for handleKalaStoryGet — routes on URL + body.uri ─────────────

function makeMockFetch(parvas: Record<string, unknown>[]) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const urlStr = String(url)
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {}

    if (urlStr.includes('/api/retrieval/capability')) {
      const uri = body['uri'] as string
      if (uri === 'marsys://tool/L3/query_life_arc') {
        return {
          ok: true,
          json: async () => ({ ok: true, content: { content: { parvas }, is_error: false } }),
          text: async () => '',
        } as Response
      }
      if (uri?.includes('lel_query')) {
        return {
          ok: true,
          json: async () => ({ ok: true, content: { content: { events: [], has_more: false }, is_error: false } }),
          text: async () => '',
        } as Response
      }
      // Any other capability — return empty
      return {
        ok: true,
        json: async () => ({ ok: true, content: { content: {}, is_error: false } }),
        text: async () => '',
      } as Response
    }

    if (urlStr.includes('/api/mcp/db/query')) {
      // resolveFieldSnapshot + fetchTopInsight — both handle { rows: [] } gracefully
      return {
        ok: true,
        json: async () => ({ rows: [] }),
        text: async () => '',
      } as Response
    }

    return {
      ok: true,
      json: async () => ({}),
      text: async () => '',
    } as Response
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

// ════════════════════════════════════════════════════════════════════════════
// F-44b — non-actionable recover_via: instrument must be null, not invented
// ════════════════════════════════════════════════════════════════════════════

describe('F-44b: response_budget collapse fallback uses instrument: null, not response_format:legacy', () => {
  it('applyResponseBudget (whole response) path: recover_via.instrument is null', () => {
    // Large non-trimmable content triggers the (whole response) trim_report entry.
    // No sections declared → PASS 1/2 have nothing to zero; afterSections = before.
    const content = { data: 'x'.repeat(5000) }
    const result = applyResponseBudget(content, 1, []) // 1 KB budget, no sections
    const entry = result.trim_report?.find((e) => e.path === '(whole response)')
    expect(entry).toBeDefined()
    expect(entry!.recover_via.instrument).not.toBe('response_format:legacy') // fails before fix
    expect(entry!.recover_via.instrument).toBeNull()
  })

  it('finalizeMcpBudget trim_report collapse path: recover_via.instrument is null', () => {
    // ~4 KB non-trimmable base + 1 KB budget → applyResponseBudget zeroes the trimmable
    // section and attaches a trim_report; finalizeMcpBudget then finds even a 1-entry
    // trim_report can't fit → collapses to the (trim_report) summary entry.
    const bigBase = 'x'.repeat(4000)
    const content: Record<string, unknown> = {
      non_trimmable_base: bigBase,
      items: Array.from({ length: 5 }, (_, i) => ({ id: i, value: 'item' })),
    }
    const sections: TrimmableSection<Record<string, unknown>>[] = [
      {
        path: 'items',
        getArray: (c) => c['items'] as unknown[],
        setArray: (c, kept) => { c['items'] = kept },
        minKeep: 1,
        recover: { instrument: 'some_tool', hint: 'use this tool to get items' },
        label: 'items',
      },
    ]
    finalizeMcpBudget(content, { maxKb: 1, sections, budgetKbRequested: 1 })
    const trimReport = content['trim_report'] as Array<Record<string, unknown>>
    // The collapse summary entry replaces all trim_report rows
    const collapsed = trimReport?.find((e) => e['path'] === '(trim_report)')
    expect(collapsed).toBeDefined()
    const recoverVia = collapsed!['recover_via'] as { instrument: string | null }
    expect(recoverVia.instrument).not.toBe('response_format:legacy') // fails before fix
    expect(recoverVia.instrument).toBeNull()
  })
})

// ════════════════════════════════════════════════════════════════════════════
// F-44a — chapter_count must be resynced from post-trim chapters.length
// ════════════════════════════════════════════════════════════════════════════

describe('F-44a: kala_story_get chapter_count stays in sync with chapters after trim', () => {
  it('chapter_count equals chapters.length at budget_kb: 2 (full trim expected)', async () => {
    // 10 chapters × ~400B each ≈ 4KB chapters alone; with envelope overhead the full
    // response is well over 2KB, so finalizeMcpBudget zeros chapters.
    // BEFORE fix: chapter_count = 10, chapters.length = 0 → mismatch.
    // AFTER fix:  chapter_count = 0,  chapters.length = 0 → match.
    const parvas = Array.from({ length: 10 }, (_, i) => makeParva(i))
    vi.stubGlobal('fetch', makeMockFetch(parvas))

    const result = await handleKalaStoryGet(
      { chart_id: CANONICAL_CHART_ID, budget_kb: 2 },
      TEST_PRINCIPAL,
    )
    expect(result.error).toBeUndefined()
    const response = result.response!
    expect(response.chapter_count).toBe(response.chapters.length) // fails before fix
  })

  it('chapter_count equals chapters.length at budget_kb: 8 (partial trim regression guard)', async () => {
    // At 8 KB some chapters survive but chapter_count was never resynced — still reported
    // original count even after partial trim.
    // AFTER fix: chapter_count must always equal the post-trim chapters.length.
    const parvas = Array.from({ length: 10 }, (_, i) => makeParva(i))
    vi.stubGlobal('fetch', makeMockFetch(parvas))

    const result = await handleKalaStoryGet(
      { chart_id: CANONICAL_CHART_ID, budget_kb: 8 },
      TEST_PRINCIPAL,
    )
    expect(result.error).toBeUndefined()
    const response = result.response!
    expect(response.chapter_count).toBe(response.chapters.length)
  })
})
