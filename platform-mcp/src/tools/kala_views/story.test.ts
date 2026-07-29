/**
 * story.test.ts — ṢAḌ-DARŚANA v2 W0.4/W0.5 kala_story_get facade.
 * Covers: the parva-dedup fix (§0.5, against REAL duplicate rows observed live on
 * 482012f1) and the end-to-end handler shape (envelope + per-chapter tri-plane pointers).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { dedupParvas } from './story.js'

// ── dedupParvas — pure logic, real duplicate shapes verified live on 482012f1 ─────────

function parva(overrides: Partial<{
  id: number; parva_index: number; dasha_planet: string; start_year: number; end_year: number | null
  parva_quality: string; avg_effective_score: number | null
}>) {
  return {
    id: overrides.id ?? overrides.parva_index ?? 1,
    parva_index: overrides.parva_index ?? 1,
    dasha_planet: overrides.dasha_planet ?? 'Saturn',
    dominant_signal_class: null,
    start_year: overrides.start_year ?? 1991,
    end_year: overrides.end_year === undefined ? 1994 : overrides.end_year,
    parva_quality: overrides.parva_quality ?? 'transitional',
    theme_keywords: [] as string[],
    high_convergence_count: 0,
    avg_effective_score: overrides.avg_effective_score ?? null,
    narrative: {},
    source_citation: 'ka_jivana_parva:v1.0',
    computed_at: '2026-07-01T00:00:00Z',
  }
}

describe('dedupParvas — §0.5 parva-dedup fix', () => {
  it('collapses exact-duplicate spans (idx 29/31: Ketu 2027-2028, both "building") to one canonical row', () => {
    const rows = [
      parva({ parva_index: 29, dasha_planet: 'Ketu', start_year: 2027, end_year: 2028, parva_quality: 'building', avg_effective_score: 0.4 }),
      parva({ parva_index: 30, dasha_planet: 'Ketu', start_year: 2027, end_year: 2034, parva_quality: 'building', avg_effective_score: 0.5 }),
      parva({ parva_index: 31, dasha_planet: 'Ketu', start_year: 2027, end_year: 2028, parva_quality: 'building', avg_effective_score: 0.6 }),
    ]
    const { chapters, report } = dedupParvas(rows)

    // idx29 and idx31 share the identical (Ketu, 2027, 2028) span — collapsed to one.
    expect(chapters).toHaveLength(2)
    expect(report.source_row_count).toBe(3)
    expect(report.deduped_row_count).toBe(2)
    expect(report.collapses).toHaveLength(1)
    // Higher avg_effective_score wins (idx31: 0.6 > idx29: 0.4).
    expect(report.collapses[0]!.kept_parva_index).toBe(31)
    expect(report.collapses[0]!.collapsed_parva_indices).toEqual([29])

    // idx30 (2027-2034, the largest span at start_year=2027) is the mahādaśā;
    // the surviving 2027-2028 row is the nested antardaśā self-period.
    const md = chapters.find((c) => c.parva_index === 30)!
    const ad = chapters.find((c) => c.parva_index === 31)!
    expect(md.chapter_level).toBe('mahadasha')
    expect(ad.chapter_level).toBe('antardasha')
    expect(ad.collapsed_duplicate_count).toBe(1)
  })

  it('keeps genuinely-conflicting same-span duplicates (idx 7/9: Saturn 1991-1994, "transitional" vs "consolidating") to ONE row, never both', () => {
    const rows = [
      parva({ parva_index: 7, dasha_planet: 'Saturn', start_year: 1991, end_year: 1994, parva_quality: 'transitional', avg_effective_score: 0.3 }),
      parva({ parva_index: 8, dasha_planet: 'Saturn', start_year: 1991, end_year: 2010, parva_quality: 'receding', avg_effective_score: 0.2 }),
      parva({ parva_index: 9, dasha_planet: 'Saturn', start_year: 1991, end_year: 1994, parva_quality: 'consolidating', avg_effective_score: 0.7 }),
    ]
    const { chapters, report } = dedupParvas(rows)

    expect(chapters).toHaveLength(2)
    expect(report.collapses).toHaveLength(1)
    // idx9 wins (0.7 > 0.3).
    expect(report.collapses[0]!.kept_parva_index).toBe(9)
    expect(report.collapses[0]!.collapsed_parva_indices).toEqual([7])
    expect(chapters.some((c) => c.parva_index === 7)).toBe(false)

    const md = chapters.find((c) => c.parva_index === 8)!
    const ad = chapters.find((c) => c.parva_index === 9)!
    expect(md.chapter_level).toBe('mahadasha')
    expect(ad.chapter_level).toBe('antardasha')
    expect(ad.parva_quality).toBe('consolidating')
  })

  it('ties broken by lowest parva_index when avg_effective_score is equal/null', () => {
    const rows = [
      parva({ parva_index: 20, dasha_planet: 'Mercury', start_year: 2010, end_year: 2013, parva_quality: 'receding', avg_effective_score: null }),
      parva({ parva_index: 18, dasha_planet: 'Mercury', start_year: 2010, end_year: 2013, parva_quality: 'transitional', avg_effective_score: null }),
    ]
    const { report } = dedupParvas(rows)
    expect(report.collapses[0]!.kept_parva_index).toBe(18)
  })

  it('leaves genuinely-distinct, non-overlapping spans untouched (no false-positive collapse)', () => {
    const rows = [
      parva({ parva_index: 1, dasha_planet: 'Jupiter', start_year: 1984, end_year: 1991 }),
      parva({ parva_index: 10, dasha_planet: 'Mercury', start_year: 1994, end_year: 1997 }),
    ]
    const { chapters, report } = dedupParvas(rows)
    expect(chapters).toHaveLength(2)
    expect(report.collapses).toHaveLength(0)
    // Neither shares a start_year with another row — both are mahadasha (no nesting).
    expect(chapters.every((c) => c.chapter_level === 'mahadasha')).toBe(true)
  })

  it('a birth-anchored partial first AD (real pattern: idx1 Jupiter 1984-1991 MD, idx2 Venus 1984-1986 AD active at birth, NOT the same lord as the MD) is still correctly nested by shared start_year alone', () => {
    // Verified live against 482012f1: the first antardasha shown at birth is whichever AD
    // was active when the record starts, not necessarily the MD's own self-period lord —
    // dedup/level-assignment keys on the shared start_year, never on lord equality.
    const rows = [
      parva({ parva_index: 1, dasha_planet: 'Jupiter', start_year: 1984, end_year: 1991, avg_effective_score: 0.3 }),
      parva({ parva_index: 2, dasha_planet: 'Venus', start_year: 1984, end_year: 1986, avg_effective_score: 0.2 }),
    ]
    const { chapters, report } = dedupParvas(rows)
    expect(report.collapses).toHaveLength(0) // distinct spans — nothing to collapse, only to level.
    const md = chapters.find((c) => c.parva_index === 1)!
    const ad = chapters.find((c) => c.parva_index === 2)!
    expect(md.chapter_level).toBe('mahadasha')
    expect(ad.chapter_level).toBe('antardasha')
  })

  it('is a no-op on an empty input', () => {
    const { chapters, report } = dedupParvas([])
    expect(chapters).toHaveLength(0)
    expect(report.source_row_count).toBe(0)
    expect(report.deduped_row_count).toBe(0)
  })
})

// ── handleKalaStoryGet — end-to-end shape over a mocked registry capability call ───────

describe('handleKalaStoryGet', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('builds an envelope with per-chapter tri-plane pointers wired on real data (item 43)', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        content: {
          chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
          parvas: [
            { id: 8, parva_index: 8, dasha_planet: 'Saturn', start_year: 1991, end_year: 2010, parva_quality: 'receding', theme_keywords: ['discipline'], high_convergence_count: 3, avg_effective_score: 0.4, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-01T00:00:00Z' },
            { id: 19, parva_index: 19, dasha_planet: 'Mercury', start_year: 2010, end_year: 2027, parva_quality: 'building', theme_keywords: ['communication'], high_convergence_count: 5, avg_effective_score: 0.6, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-15T00:00:00Z' },
          ],
        },
      }),
    }) as unknown as typeof fetch

    const { handleKalaStoryGet } = await import('./story.js')
    const { response, error } = await handleKalaStoryGet(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      { user_uid: 'u1', key_id: 'k1', role: 'guest' },
    )

    expect(error).toBeUndefined()
    expect(response).toBeDefined()
    expect(response!.tool).toBe('kala_story_get')
    expect(response!.chapters.length).toBe(2)
    expect(response!.calibration_maturity.n_events).toBe(0)
    expect(response!.field_snapshot_id).toContain('ka_jivana_parva=')

    // The 1991-2010 Saturn chapter (current, since "now" is well inside 1991-2010... it
    // is not for 2026 — recompute expectation against actual temporal_position instead of
    // assuming, since the fixture's own "now" is real wall-clock time).
    const mercuryChapter = response!.chapters.find((c) => c.dasha_planet === 'Mercury')!
    expect(mercuryChapter.tri_plane.interpretation_ref).not.toBeNull()
    // A current/future chapter gets a live prediction_ref/intervention_ref (not a no_lever).
    if (mercuryChapter.temporal_position !== 'past') {
      expect(mercuryChapter.tri_plane.intervention_ref).toEqual({
        instrument: 'kala_elect_get',
        hint: expect.stringContaining('Mercury'),
      })
    }
  })

  it('propagates an honest error when the registry capability call fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => 'boom' }) as unknown as typeof fetch
    const { handleKalaStoryGet } = await import('./story.js')
    const { response, error } = await handleKalaStoryGet(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      { user_uid: 'u1', key_id: 'k1', role: 'guest' },
    )
    expect(response).toBeUndefined()
    expect(error).toBeDefined()
  })
})
