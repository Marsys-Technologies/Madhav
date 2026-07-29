/**
 * story.test.ts — ṢAḌ-DARŚANA v2 W0.4/W0.5 kala_story_get facade.
 * Covers: the parva-dedup fix (§0.5, against REAL duplicate rows observed live on
 * 482012f1), the end-to-end handler shape (envelope + per-chapter tri-plane pointers), and
 * §W1 item 10 (per-chapter LEL pinning + retrodiction fit).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { dedupParvas, pinLelEventsToChapter } from './story.js'

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

// ── pinLelEventsToChapter — §W1 item 10, pure logic ─────────────────────────────────────

function lelEvent(overrides: Partial<{
  event_id: string; event_date: string; category: string; domain: string; description: string
  event_type: string; source_citation: string; outcome_observed: boolean | null
  shape: 'point' | 'interval' | 'chain'; interval_start: string | null; interval_end: string | null
}>) {
  return {
    event_id: overrides.event_id ?? 'evt-1',
    event_date: overrides.event_date ?? '2000-06-01',
    category: overrides.category ?? 'career',
    domain: overrides.domain ?? 'career/promotion',
    description: overrides.description ?? 'Some career event',
    significance: null,
    event_type: overrides.event_type ?? 'career',
    source_citation: overrides.source_citation ?? 'LIFE_EVENT_LOG_v1_2.md (native-disclosed)',
    source_section: null,
    outcome_observed: overrides.outcome_observed ?? true,
    shape: overrides.shape ?? 'point',
    interval_start: overrides.interval_start ?? null,
    interval_end: overrides.interval_end ?? null,
  }
}

describe('pinLelEventsToChapter — §W1 item 10', () => {
  it('pins a point-shaped event whose event_date falls inside the chapter span', () => {
    const events = [lelEvent({ event_id: 'a', event_date: '1992-03-01' })]
    const { pinned } = pinLelEventsToChapter(1991, 1994, ['discipline'], events, null)
    expect(pinned.map((p) => p.event_id)).toEqual(['a'])
  })

  it('does NOT pin a point-shaped event whose event_date falls outside the chapter span', () => {
    const events = [lelEvent({ event_id: 'a', event_date: '1995-03-01' })]
    const { pinned } = pinLelEventsToChapter(1991, 1994, ['discipline'], events, null)
    expect(pinned).toHaveLength(0) // 1995 is outside 1991-1994
  })

  it('pins an event exactly on the chapter boundary (inclusive)', () => {
    const events = [
      lelEvent({ event_id: 'start', event_date: '1991-01-01' }),
      lelEvent({ event_id: 'end', event_date: '1994-12-31' }),
      lelEvent({ event_id: 'outside', event_date: '1995-01-01' }),
    ]
    const { pinned } = pinLelEventsToChapter(1991, 1994, ['discipline'], events, null)
    expect(pinned.map((p) => p.event_id).sort()).toEqual(['end', 'start'])
  })

  it('an open-ended chapter (end_year null) still pins events far in the future', () => {
    const events = [lelEvent({ event_id: 'far-future', event_date: '2080-01-01' })]
    const { pinned } = pinLelEventsToChapter(2010, null, ['building'], events, null)
    expect(pinned.map((p) => p.event_id)).toEqual(['far-future'])
  })

  it('an interval-shaped event pins by [interval_start, interval_end] overlap, not event_date alone', () => {
    // event_date (anchor) is OUTSIDE the chapter, but the interval overlaps it.
    const events = [
      lelEvent({
        event_id: 'chronic', event_date: '2010-01-01', shape: 'interval',
        interval_start: '1994-12-31', interval_end: '2010-12-30',
      }),
    ]
    const { pinned } = pinLelEventsToChapter(1991, 1994, ['discipline'], events, null)
    expect(pinned.map((p) => p.event_id)).toEqual(['chronic'])
  })

  it('theme_aligned is true when a theme keyword appears literally in category/domain/event_type/description', () => {
    const events = [
      lelEvent({ event_id: 'match', event_date: '2000-01-01', domain: 'relationship/marriage', category: 'relationship' }),
      lelEvent({ event_id: 'no-match', event_date: '2000-06-01', domain: 'career/promotion', category: 'career', description: 'Got promoted' }),
    ]
    const { pinned, fit } = pinLelEventsToChapter(1998, 2001, ['beauty', 'relationship', 'creativity'], events, null)
    const match = pinned.find((p) => p.event_id === 'match')!
    const noMatch = pinned.find((p) => p.event_id === 'no-match')!
    expect(match.theme_aligned).toBe(true)
    expect(noMatch.theme_aligned).toBe(false)
    expect(fit.pinned_event_count).toBe(2)
    expect(fit.aligned_event_count).toBe(1)
    expect(fit.aligned_ratio).toBe(0.5)
    expect(fit.method).toBe('lexical_theme_keyword_match')
  })

  it('reports honest insufficient_data (null ratio) when zero events are pinned', () => {
    const { pinned, fit } = pinLelEventsToChapter(1900, 1901, ['discipline'], [], null)
    expect(pinned).toHaveLength(0)
    expect(fit.pinned_event_count).toBe(0)
    expect(fit.aligned_ratio).toBeNull()
    expect(fit.note).toContain('insufficient_data')
  })

  it('reports an honest lel_fetch_failed note (never a silent zero) when the LEL fetch errored', () => {
    const { fit } = pinLelEventsToChapter(1998, 2001, ['relationship'], [], 'HTTP 500')
    expect(fit.aligned_ratio).toBeNull()
    expect(fit.note).toContain('lel_fetch_failed')
    expect(fit.note).toContain('HTTP 500')
  })

  it('never invents an aligned_ratio above the true fraction — sample-size caveat on small samples', () => {
    const events = [lelEvent({ event_id: 'one', event_date: '2000-01-01', domain: 'relationship/x', category: 'relationship' })]
    const { fit } = pinLelEventsToChapter(1998, 2001, ['relationship'], events, null)
    expect(fit.pinned_event_count).toBe(1)
    expect(fit.aligned_ratio).toBe(1)
    expect(fit.note).toContain('Sample is small')
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

  it('wires per-chapter LEL pinning + retrodiction fit end-to-end (§W1 item 10)', async () => {
    // Dispatches a distinct fixture per capability `uri` — query_life_arc vs lel_query —
    // mirroring what /api/retrieval/capability actually does for two different capabilities.
    global.fetch = vi.fn(async (_url: unknown, opts: unknown) => {
      const body = JSON.parse((opts as { body: string }).body) as { uri: string }
      if (body.uri === 'marsys://tool/L3/query_life_arc') {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            content: {
              chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
              parvas: [
                { id: 8, parva_index: 8, dasha_planet: 'Saturn', start_year: 1991, end_year: 1994, parva_quality: 'transitional', theme_keywords: ['discipline', 'responsibility'], high_convergence_count: 3, avg_effective_score: 0.4, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-01T00:00:00Z' },
              ],
            },
          }),
        }
      }
      if (body.uri === 'marsys://tool/L5/lel_query') {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            content: {
              chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
              events: [
                { event_id: 'lel-1', event_date: '1992-06-01', category: 'career', domain: 'career/first_job_joined', description: 'Started first responsibility-heavy role', significance: null, event_type: 'career', source_citation: 'LEL', source_section: null, outcome_observed: true, shape: 'point', interval_start: null, interval_end: null },
                { event_id: 'lel-2', event_date: '1998-01-01', category: 'relationship', domain: 'relationship/x', description: 'Unrelated later event', significance: null, event_type: 'relationship', source_citation: 'LEL', source_section: null, outcome_observed: true, shape: 'point', interval_start: null, interval_end: null },
              ],
              count: 2,
              total_matching: 2,
              has_more: false,
              filters: {},
              provenance: {},
            },
          }),
        }
      }
      throw new Error(`unexpected capability uri in test: ${body.uri}`)
    }) as unknown as typeof fetch

    const { handleKalaStoryGet } = await import('./story.js')
    const { response, error } = await handleKalaStoryGet(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      { user_uid: 'u1', key_id: 'k1', role: 'guest' },
    )

    expect(error).toBeUndefined()
    expect(response).toBeDefined()
    const chapter = response!.chapters[0]!
    // lel-1 (1992, inside 1991-1994) is pinned; lel-2 (1998) is outside the span.
    expect(chapter.lel_pinned_count).toBe(1)
    expect(chapter.lel_events_pinned[0]!.event_id).toBe('lel-1')
    // 'responsibility' theme keyword appears literally in lel-1's description.
    expect(chapter.lel_events_pinned[0]!.theme_aligned).toBe(true)
    expect(chapter.retrodiction_fit.pinned_event_count).toBe(1)
    expect(chapter.retrodiction_fit.aligned_event_count).toBe(1)
    expect(chapter.retrodiction_fit.aligned_ratio).toBe(1)

    const lelCoverage = response!.coverage.find((c) => c.concept === 'lel_pinning_per_chapter')!
    expect(lelCoverage).toBeDefined()
    expect(lelCoverage.state).toBe('computed')
  })

  it('degrades honestly (never throws) when the LEL fetch itself fails, and reports it in coverage', async () => {
    let callCount = 0
    global.fetch = vi.fn(async (_url: unknown, opts: unknown) => {
      const body = JSON.parse((opts as { body: string }).body) as { uri: string }
      callCount++
      if (body.uri === 'marsys://tool/L3/query_life_arc') {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            content: {
              chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
              parvas: [
                { id: 1, parva_index: 1, dasha_planet: 'Jupiter', start_year: 1984, end_year: 1991, parva_quality: 'receding', theme_keywords: ['expansion'], high_convergence_count: 0, avg_effective_score: null, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-01T00:00:00Z' },
              ],
            },
          }),
        }
      }
      // Every lel_query call fails.
      return { ok: false, status: 500, text: async () => 'lel outage' }
    }) as unknown as typeof fetch

    const { handleKalaStoryGet } = await import('./story.js')
    const { response, error } = await handleKalaStoryGet(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
      { user_uid: 'u1', key_id: 'k1', role: 'guest' },
    )

    expect(error).toBeUndefined()
    expect(response).toBeDefined()
    expect(callCount).toBeGreaterThan(1) // both capability calls were attempted
    const chapter = response!.chapters[0]!
    expect(chapter.lel_pinned_count).toBe(0)
    expect(chapter.retrodiction_fit.note).toContain('lel_fetch_failed')
    const lelCoverage = response!.coverage.find((c) => c.concept === 'lel_pinning_per_chapter')!
    expect(lelCoverage.state).not.toBe('computed')
  })
})
