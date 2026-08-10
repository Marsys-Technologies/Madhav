/**
 * kala_views/story.ts — ṢAḌ-DARŚANA v2 W0.4/W0.5 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4/§0.5 ·
 * §2 file map · item 43).
 * ==========================================================================
 * VIEW 4 — STORY (`kala_story_get`) — "What is the story of my life in time?"
 *
 * A THIN FACADE (W0 depth — no new computation) over the EXISTING life-arc substrate:
 * `kala_jivana_parva` (queried via the registered `marsys://tool/L3/query_life_arc`
 * capability — the same table `kala_life_arc_get` already serves). This file adds NOTHING
 * astrological — it composes already-computed parva rows into the elevated
 * `kala_envelope.ts` shape (argument-shaped reading, question_frame, field_snapshot_id
 * stub, PER-CHAPTER tri-plane pointers wired on real data, 3-state coverage, freshness,
 * calibration_maturity) via `argument_composer.ts`.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * §0.5 — THE PARVA-DEDUP FIX (serving-layer only; verified live against 482012f1)
 *
 * `kala_jivana_parva` carries genuine duplicate rows: e.g. parva_index 7/8/9 are all
 * Saturn starting 1991 (7: 1991-1994 "transitional", 8: 1991-2010 "receding", 9: 1991-1994
 * "consolidating"); parva_index 18/19/20 are all Mercury starting 2010 (18: 2010-2013
 * "transitional", 19: 2010-2027 "building", 20: 2010-2013 "receding"); parva_index 29/30/31
 * are all Ketu starting 2027 (29 and 31 are EXACT duplicates: 2027-2028 "building" twice).
 * Two distinct phenomena are tangled together here:
 *   (a) genuine daśā-level nesting — the longest span sharing a start_year with its
 *       siblings is the mahādaśā chapter (e.g. idx 8/19/30); a shorter span sharing that
 *       SAME start_year is the nested antardaśā active at that start_year. For a MD
 *       boundary that begins a fresh AD sequence this is the self-period (same lord as the
 *       MD — idx 7or9/18or20/29or31 are all Saturn/Saturn, Mercury/Mercury, Ketu/Ketu
 *       respectively); at the birth-anchored FIRST chapter the nested AD is whichever lord
 *       was active mid-sequence when the record starts and need NOT match the MD's lord
 *       (idx 1 Jupiter MD 1984-1991 nests idx 2 Venus AD 1984-1986, not a Jupiter AD — see
 *       story.test.ts's dedicated case). The level-assignment rule below keys on the
 *       shared start_year alone, never on lord equality, so it handles both correctly.
 *   (b) an exact-duplicate write bug — TWO rows sharing the identical
 *       (dasha_planet, start_year, end_year) span with CONFLICTING quality labels (idx 7 vs
 *       9: "transitional" vs "consolidating" for the identical 1991-1994 Saturn span; idx
 *       18 vs 20: "transitional" vs "receding" for the identical 2010-2013 Mercury span) or
 *       literal duplicates (idx 29 vs 31: both "building" for the identical 2027-2028 span).
 * `dedupParvas()` below collapses (b) at serving time — grouping by the exact
 * (dasha_planet, start_year, end_year) span, keeping ONE canonical row per group
 * (highest avg_effective_score, tie-broken by lowest parva_index — never fabricated;
 * an honest deterministic pick among genuinely-conflicting duplicate rows) and recording
 * every collapse in `dedup_report` (never silently dropped — B.10) — then assigns an
 * honest `chapter_level` ('mahadasha' | 'antardasha') from (a)'s span-nesting rule so the
 * two phenomena are no longer conflated in what STORY serves. This is a SERVING-layer fix
 * inside this new facade only — it does not touch `query_life_arc.ts` or the
 * `kala_jivana_parva` writer (`ka_jivana_parva.py`), which remain out of this lane's scope
 * (root-cause fix, if warranted, belongs to whichever lane owns that writer).
 * ══════════════════════════════════════════════════════════════════════════════════════
 *
 * WHAT THIS FILE IS NOT (W0 scope discipline):
 *   - It does NOT implement Chara-daśā second-voice narration (v1 §4.2) — W3.
 *   - It does NOT implement punctuation-mark overlay (returns, eclipses-on-natal) — W3.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * §W1 item 10 — PER-CHAPTER LEL PINNING + RETRODICTION FIT (SHAD_DARSHANA_BRIEF_v2_0.md
 * §3 W1, v1 §7.10) — implemented in THIS facade, not upstream.
 *
 * `query_life_arc.ts`'s `include_lel_events` param remains a documented no-op (verified: its
 * SQL never joins an LEL table despite the param name) — this facade does NOT route through
 * it. Instead `fetchAllChartLelEvents` below calls the L5 `marsys://tool/L5/lel_query`
 * registry capability DIRECTLY (the same capability `lel_query`/`mimamsa_lel_query` serve),
 * paginated to exhaustion, and `pinLelEventsToChapter` JOINS the results onto each STORY
 * chapter by date-range overlap — a JOIN over EXISTING LEL data, computing NOTHING new about
 * the events themselves. The retrodiction fit is a deliberately modest, defensible signal
 * (lexical theme-keyword overlap, §N.7 "an honest 'insufficient data' beats an invented
 * confidence score") — NOT the calibrated, weighted, cohort-normalized fit W2's `mi_bhara`
 * will eventually own (stage 9, brief §3 W2).
 *
 * ── THE CIRCULARITY GUARD (brief §7 rail; HARD, non-negotiable campaign gate) ───────────
 * "The field never reads the LEL." This facade is the ONLY consumer of LEL data added in
 * this lane, and its LEL read serves ONE purpose: an honest per-chapter DISPLAY join on this
 * response. The pinned events / retrodiction fit computed here:
 *   - are NOT written to any table;
 *   - are NOT read by any other writer or capability (nothing downstream of THIS response
 *     consumes them — they terminate at this HTTP response);
 *   - never flow into `dedupParvas`, `_assign_quality` (upstream `ka_jivana_parva`'s own
 *     quality/theme computation, already complete before this file ever sees a parva row),
 *     `buildArgumentReading`'s thesis/verdict, or any prediction/score/hazard value served
 *     anywhere else in the estate.
 * The temporal-field-adjacent computations that exist TODAY (`ka_jivana_parva`'s
 * quality/theme assignment, `ka_gochara_sweep`'s windows) have zero code path to `life_events`
 * — see `CIRCULARITY_GUARD_lel_invariance` in `platform/python-sidecar/tests/l3/
 * test_ka_jivana_parva_circularity_guard.py`, the CI invariance test this item ships with
 * (brief §3 Gate W1: "the Circularity-Guard LEL-invariance test ships with item 10 and is
 * green"). That test names its proxy honestly (`ka_jivana_parva` — the closest currently-
 * computed "temporal field" output, since the real `ka_kshetra` hazard pipeline doesn't
 * exist until W2) and documents that it must be re-pointed at `ka_kshetra`/`mi_bhara` once
 * W2 lands.
 * ══════════════════════════════════════════════════════════════════════════════════════
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  resolveFieldSnapshot,
  pointerTo,
  noLeverPointer,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  noLelCalibrationMaturity,
  kalaEvidenceTrimmableSection,
  type ArgumentReading,
  type ArgumentEvidence,
  type KalaCoverageEntry,
  type QuestionFrame,
  type KalaEnvelope,
  type TriPlanePointers,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { finalizeMcpBudget, type TrimmableSection } from '../../lib/response_budget.js'
// Reuses the SAME registry-capability caller the priority/explain lane already factored
// out (kala_views/shared.ts) rather than adding a fourth local copy — see that file's
// header for why this is the deliberately-kept-local pattern for this directory.
import { callKalaRegistryCap, unwrapKalaPayload, round3 } from './shared.js'

// ── W2.8 — fetchTopInsight (kala_insights leading the reading) ──────────────────────
// SHAD_DARSHANA_BRIEF_v2_0.md §3 W2: "reading-leads-with-insight enforced in composer."
// Queries kala_insights ORDER BY insight_score DESC LIMIT 1 to surface the highest-scored
// insight for this chart (1c826d5a has 2 scarcity rows; 482012f1 has 0 rows → honest_empty).
// Uses the same read-only DB proxy (/api/mcp/db/query) as resolveFieldSnapshot and the W2.7
// salience vector fetch — never throws; honest_empty on 0 rows, unreachable on fetch error.

const PLATFORM_URL_FOR_INSIGHTS = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN_FOR_INSIGHTS = process.env['MCP_INTERNAL_TOKEN'] ?? ''

export interface TopInsightResult {
  state: 'computed' | 'honest_empty' | 'unreachable'
  insight_id?: string | null
  insight_type?: string | null
  insight_score?: number | null
  statement_key?: string | null
  statement_params?: unknown
  fact_ids?: string[]
  reason?: string
}

/** Fetches the highest-scoring row from kala_insights for a chart (ORDER BY insight_score DESC
 *  LIMIT 1). Returns state='computed' with the row's fields when data exists, state='honest_empty'
 *  when 0 rows, state='unreachable' when the DB proxy call fails. Never throws. */
export async function fetchTopInsight(
  chartId: string,
  principal: { user_uid: string; key_id: string },
): Promise<TopInsightResult> {
  try {
    const res = await fetch(`${PLATFORM_URL_FOR_INSIGHTS}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-mcp-internal-token': MCP_INTERNAL_TOKEN_FOR_INSIGHTS,
        'x-mcp-user': principal.user_uid,
        'x-mcp-key-id': principal.key_id,
      },
      body: JSON.stringify({
        sql:
          'SELECT insight_id, insight_type, insight_score, statement_key, statement_params, fact_ids ' +
          'FROM kala_insights WHERE chart_id = $1 AND lel_derived = FALSE ' +
          'ORDER BY insight_score DESC LIMIT 1',
        params: [chartId],
      }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      return {
        state: 'unreachable',
        reason: `kala_insights read failed (HTTP ${res.status}): ${text.slice(0, 200)}`,
      }
    }
    const data = (await res.json()) as { rows?: Array<Record<string, unknown>> }
    const row = data.rows?.[0]
    if (!row) {
      return { state: 'honest_empty' }
    }
    return {
      state: 'computed',
      insight_id: row['insight_id'] as string | null ?? null,
      insight_type: row['insight_type'] as string | null ?? null,
      insight_score: row['insight_score'] != null ? Number(row['insight_score']) : null,
      statement_key: row['statement_key'] as string | null ?? null,
      statement_params: row['statement_params'],
      fact_ids: (row['fact_ids'] as string[] | null) ?? [],
    }
  } catch (err) {
    return {
      state: 'unreachable',
      reason: `kala_insights fetch threw: ${err instanceof Error ? err.message : String(err)}`,
    }
  }
}

// ── Input schema ─────────────────────────────────────────────────────────────────────

export const KalaStoryInputShape = {
  chart_id: z.string().uuid().describe('Chart UUID. Required — no default chart.'),
  top_k: z.number().int().min(1).max(739).optional().describe('Max source parva rows to fetch before dedup (default: all — 739).'),
  question_frame: z.object({
    domain: z.string().optional(),
    entity: z.string().optional(),
    horizon: z.string().optional(),
    intent_verb: z.string().optional(),
    stakes: z.string().optional(),
    comparison_target: z.string().optional(),
  }).optional().describe('E4 (Elevation §5) — the caller-supplied question frame. The chart is always implicit.'),
  budget_kb: z.number().min(1).max(200).optional().describe('Response size ceiling in KB. Default 40.'),
}

const KalaStoryZod = z.object(KalaStoryInputShape)
export type KalaStoryInput = z.infer<typeof KalaStoryZod>

// ── Raw parva row shape (kala_jivana_parva, via marsys://tool/L3/query_life_arc) ──────

interface RawParva {
  id: number
  parva_index: number
  dasha_planet: string
  dominant_signal_class: string | null
  start_year: number
  end_year: number | null
  parva_quality: string
  theme_keywords: string[]
  high_convergence_count: number
  avg_effective_score: number | null
  narrative: Record<string, unknown>
  source_citation: string
  computed_at: string
}

// ── §0.5 — parva dedup by span+level (serving-layer only; see file header) ─────────────

export type ChapterLevel = 'mahadasha' | 'antardasha'

export interface StoryChapter {
  parva_index: number
  dasha_planet: string
  start_year: number
  end_year: number | null
  chapter_level: ChapterLevel
  parva_quality: string
  theme_keywords: string[]
  narrative: Record<string, unknown>
  high_convergence_count: number
  avg_effective_score: number | null
  source_citation: string
  temporal_position: 'past' | 'current' | 'future'
  collapsed_duplicate_count: number
  tri_plane: TriPlanePointers
  // §W1 item 10 — per-chapter LEL pinning + retrodiction fit (see file header's
  // CIRCULARITY GUARD note: this data terminates at this response, never flows onward).
  lel_events_pinned: PinnedLelEvent[]
  lel_pinned_count: number
  retrodiction_fit: ChapterRetrodictionFit
}

// ── §W1 item 10 — LEL pinning + retrodiction fit ────────────────────────────────────────

/** Raw shape served by the `marsys://tool/L5/lel_query` registry capability
 *  (query_life_events.ts). `shape`/`interval_start`/`interval_end` are LEL schema v2
 *  (migration 457) columns this lane additively wired into that capability's SELECT (were
 *  previously stored but never served) — populated only for shape='interval' rows. */
interface RawLelEvent {
  event_id: string
  event_date: string
  category: string
  domain: string
  description: string
  significance: string | null
  event_type: string
  source_citation: string
  source_section: string | null
  outcome_observed: boolean | null
  shape?: 'point' | 'interval' | 'chain'
  interval_start?: string | null
  interval_end?: string | null
}

interface LelQueryPayload {
  events?: RawLelEvent[]
  has_more?: boolean
  total_matching?: number
}

export interface PinnedLelEvent {
  event_id: string
  event_date: string
  category: string
  domain: string
  event_type: string
  description: string
  outcome_observed: boolean | null
  source_citation: string
  /** Whether this event's category/domain/event_type/description shares a literal word
   *  with the chapter's theme_keywords — the retrodiction fit's per-event unit. */
  theme_aligned: boolean
}

export interface ChapterRetrodictionFit {
  pinned_event_count: number
  aligned_event_count: number
  aligned_ratio: number | null
  method: 'lexical_theme_keyword_match'
  note: string
}

const LEL_PAGE_LIMIT = 50
// Safety cap on pagination — the native's corpus is ~63 rows (well under one page-and-a-
// half); 10 pages (≤500 rows) is generous headroom against a misbehaving `has_more` flag
// ever causing an unbounded loop, never a claim about expected corpus size.
const LEL_MAX_PAGES = 10

/** Fetches the WHOLE LEL corpus for a chart via the L5 `lel_query` registry capability,
 *  paginated to exhaustion via limit+offset (this facade calls the capability directly, so
 *  — unlike the MCP-level `lel_query` tool's date-cursor-only pagination documented in
 *  `scripts/audit/t0_retrodiction/lib/lel.ts` — server-side `offset` is honored). Never
 *  throws: LEL pinning is additive to STORY, not load-bearing — an LEL outage must not take
 *  the whole tool down. A fetch failure is reported honestly via the returned `fetchError`,
 *  surfaced per-chapter in `retrodiction_fit.note` and in this response's coverage block —
 *  never silently swallowed (B.10). */
async function fetchAllChartLelEvents(
  chartId: string,
  principal: Principal,
): Promise<{ events: RawLelEvent[]; fetchError: string | null }> {
  const events: RawLelEvent[] = []
  let offset = 0
  try {
    for (let page = 0; page < LEL_MAX_PAGES; page++) {
      const content = await callKalaRegistryCap(
        'marsys://tool/L5/lel_query',
        { chart_id: chartId, limit: LEL_PAGE_LIMIT, offset },
        principal,
      )
      const inner = unwrapKalaPayload(content) as LelQueryPayload
      const pageEvents = Array.isArray(inner.events) ? inner.events : []
      events.push(...pageEvents)
      if (pageEvents.length === 0 || !inner.has_more) break
      offset += pageEvents.length
    }
    return { events, fetchError: null }
  } catch (err) {
    return { events, fetchError: String(err) }
  }
}

/** An LEL event's effective date span. Interval-shaped events (LEL schema v2) use their
 *  real [interval_start, interval_end]; every other shape (point/chain, or an interval row
 *  with a null bound) collapses to a single-day span at event_date — never fabricated wider
 *  bounds for a point event. */
function lelEventSpan(event: RawLelEvent): { start: string; end: string } {
  if (event.shape === 'interval' && event.interval_start && event.interval_end) {
    return { start: event.interval_start, end: event.interval_end }
  }
  return { start: event.event_date, end: event.event_date }
}

/** A chapter's date span as ISO 'YYYY-MM-DD' boundary strings (which compare correctly
 *  lexically). `end_year === null` is an ongoing/open-ended chapter — bounded at a sentinel
 *  far-future date for the overlap comparison, never a fabricated real close date. */
function chapterDateSpan(startYear: number, endYear: number | null): { start: string; end: string } {
  return { start: `${startYear}-01-01`, end: endYear !== null ? `${endYear}-12-31` : '9999-12-31' }
}

/** Per-chapter LEL pinning (date-range JOIN — no new computation about the events
 *  themselves) + the modest lexical retrodiction-fit signal (§N.7: an honest
 *  "insufficient_data" beats an invented confidence score). CIRCULARITY GUARD: this
 *  function's output is consumed ONLY by this response's `chapters[].lel_events_pinned` /
 *  `retrodiction_fit` fields — see file header. */
export function pinLelEventsToChapter(
  startYear: number,
  endYear: number | null,
  themeKeywords: string[],
  events: RawLelEvent[],
  lelFetchError: string | null,
): { pinned: PinnedLelEvent[]; fit: ChapterRetrodictionFit } {
  const span = chapterDateSpan(startYear, endYear)
  const themeLower = themeKeywords.map((k) => k.toLowerCase()).filter((k) => k.length > 0)

  const pinned: PinnedLelEvent[] = []
  for (const ev of events) {
    const evSpan = lelEventSpan(ev)
    const overlaps = evSpan.start <= span.end && evSpan.end >= span.start
    if (!overlaps) continue
    const searchable = `${ev.category} ${ev.domain} ${ev.event_type} ${ev.description}`.toLowerCase()
    const aligned = themeLower.some((kw) => searchable.includes(kw))
    pinned.push({
      event_id: ev.event_id,
      event_date: ev.event_date,
      category: ev.category,
      domain: ev.domain,
      event_type: ev.event_type,
      description: ev.description.length > 220 ? `${ev.description.slice(0, 217)}...` : ev.description,
      outcome_observed: ev.outcome_observed ?? null,
      source_citation: ev.source_citation,
      theme_aligned: aligned,
    })
  }

  const pinnedCount = pinned.length
  const alignedCount = pinned.filter((p) => p.theme_aligned).length

  if (lelFetchError) {
    return {
      pinned,
      fit: {
        pinned_event_count: pinnedCount,
        aligned_event_count: alignedCount,
        aligned_ratio: null,
        method: 'lexical_theme_keyword_match',
        note: `lel_fetch_failed — could not retrieve (or only partially retrieved) LEL events for this chart: ${lelFetchError}. Retrodiction fit not reliably computed; treat as honest-unavailable, not zero.`,
      },
    }
  }

  if (pinnedCount === 0) {
    return {
      pinned,
      fit: {
        pinned_event_count: 0,
        aligned_event_count: 0,
        aligned_ratio: null,
        method: 'lexical_theme_keyword_match',
        note: 'insufficient_data — no native-logged LEL events fall within this chapter\'s date span (an honest empty, not a claim of a quiet period).',
      },
    }
  }

  return {
    pinned,
    fit: {
      pinned_event_count: pinnedCount,
      aligned_event_count: alignedCount,
      aligned_ratio: round3(alignedCount / pinnedCount),
      method: 'lexical_theme_keyword_match',
      note: `${alignedCount} of ${pinnedCount} pinned LEL event(s) share a literal word with this chapter's ` +
        `theme_keywords (${themeKeywords.join(', ') || 'none recorded'}) in their category/domain/event_type/` +
        `description text. A simple lexical corroboration signal, NOT a calibrated probability or model score — ` +
        `the weighted, cohort-normalized retrodiction fit is W2's mi_bhara job (brief §3 W2 stage 9).` +
        `${pinnedCount < 3 ? ' Sample is small (<3 events) — read this ratio as indicative only.' : ''}`,
    },
  }
}

export interface DedupCollapse {
  dasha_planet: string
  start_year: number
  end_year: number | null
  kept_parva_index: number
  collapsed_parva_indices: number[]
  reason: string
}

export interface DedupReport {
  source_row_count: number
  deduped_row_count: number
  collapses: DedupCollapse[]
}

/** Collapses exact-duplicate (dasha_planet, start_year, end_year) rows to one canonical
 *  row (highest avg_effective_score, tie-broken by lowest parva_index), then labels every
 *  surviving row's chapter_level from the span-nesting rule (the sibling with the LARGEST
 *  span for a shared start_year is the mahādaśā; any other sibling sharing that start_year
 *  is the antardaśā self-period). Deterministic, no fabrication — every collapse recorded. */
type DedupedChapter = Omit<StoryChapter, 'tri_plane' | 'temporal_position' | 'lel_events_pinned' | 'lel_pinned_count' | 'retrodiction_fit'>

export function dedupParvas(rows: RawParva[]): { chapters: DedupedChapter[]; report: DedupReport } {
  const exactGroups = new Map<string, RawParva[]>()
  for (const row of rows) {
    const key = `${row.dasha_planet}|${row.start_year}|${row.end_year ?? 'null'}`
    const group = exactGroups.get(key)
    if (group) group.push(row)
    else exactGroups.set(key, [row])
  }

  const collapses: DedupCollapse[] = []
  const canonical: RawParva[] = []
  for (const group of exactGroups.values()) {
    if (group.length === 1) {
      canonical.push(group[0]!)
      continue
    }
    const sorted = [...group].sort((a, b) => {
      const scoreA = a.avg_effective_score ?? -Infinity
      const scoreB = b.avg_effective_score ?? -Infinity
      if (scoreB !== scoreA) return scoreB - scoreA
      return a.parva_index - b.parva_index
    })
    const kept = sorted[0]!
    canonical.push(kept)
    collapses.push({
      dasha_planet: kept.dasha_planet,
      start_year: kept.start_year,
      end_year: kept.end_year,
      kept_parva_index: kept.parva_index,
      collapsed_parva_indices: sorted.slice(1).map((r) => r.parva_index),
      reason: `${sorted.length} rows shared the identical span (${kept.dasha_planet} ${kept.start_year}-${kept.end_year ?? 'ongoing'}) with conflicting/duplicate quality labels (${sorted.map((r) => r.parva_quality).join(', ')}) — kept parva_index ${kept.parva_index} (highest avg_effective_score, tie-broken by lowest parva_index).`,
    })
  }

  // Span-nesting: for each start_year (across dasha_planet, since a start_year is only
  // shared by an MD and its own first AD, which is always the same planet in Vimśottarī),
  // the row with the largest span is 'mahadasha'; any sibling sharing that exact start_year
  // is 'antardasha'.
  const byStartYear = new Map<number, RawParva[]>()
  for (const row of canonical) {
    const arr = byStartYear.get(row.start_year)
    if (arr) arr.push(row)
    else byStartYear.set(row.start_year, [row])
  }

  const levelByParvaIndex = new Map<number, ChapterLevel>()
  for (const siblings of byStartYear.values()) {
    if (siblings.length === 1) {
      levelByParvaIndex.set(siblings[0]!.parva_index, 'mahadasha')
      continue
    }
    const withSpan = siblings.map((r) => ({ row: r, span: (r.end_year ?? r.start_year) - r.start_year }))
    withSpan.sort((a, b) => b.span - a.span)
    levelByParvaIndex.set(withSpan[0]!.row.parva_index, 'mahadasha')
    for (const entry of withSpan.slice(1)) levelByParvaIndex.set(entry.row.parva_index, 'antardasha')
  }

  const collapsedCountByKept = new Map<number, number>()
  for (const c of collapses) collapsedCountByKept.set(c.kept_parva_index, c.collapsed_parva_indices.length)

  const chapters = canonical
    .sort((a, b) => a.start_year - b.start_year || a.parva_index - b.parva_index)
    .map((row) => ({
      parva_index: row.parva_index,
      dasha_planet: row.dasha_planet,
      start_year: row.start_year,
      end_year: row.end_year,
      chapter_level: levelByParvaIndex.get(row.parva_index) ?? 'mahadasha' as ChapterLevel,
      parva_quality: row.parva_quality,
      theme_keywords: row.theme_keywords,
      narrative: row.narrative,
      high_convergence_count: row.high_convergence_count,
      avg_effective_score: row.avg_effective_score,
      source_citation: row.source_citation,
      collapsed_duplicate_count: collapsedCountByKept.get(row.parva_index) ?? 0,
    }))

  return {
    chapters,
    report: { source_row_count: rows.length, deduped_row_count: chapters.length, collapses },
  }
}

function temporalPosition(startYear: number, endYear: number | null, nowYear: number): 'past' | 'current' | 'future' {
  if (endYear !== null && endYear < nowYear) return 'past'
  if (startYear > nowYear) return 'future'
  return 'current'
}

/** Item 43 (tri-plane traversability): every served chapter carries LIVE pointers into the
 *  other two planes, wired on the chapter's own real temporal_position — never a stub
 *  identical across all rows. Past chapters honestly have no forward prediction/lever;
 *  current/future chapters point at the real, already-registered kala_bundle_get /
 *  kala_elect_get instruments (kala_elect_get lands in this SAME PR — no dangling pointer
 *  to an unregistered tool). */
function chapterTriPlane(position: 'past' | 'current' | 'future', dasha_planet: string): TriPlanePointers {
  const interpretation_ref = pointerTo('get_domain_reading', `interpretive grounding for the ${dasha_planet} period`)
  if (position === 'past') {
    return {
      interpretation_ref,
      prediction_ref: noLeverPointer('chapter is fully in the past — no forward prediction applies'),
      intervention_ref: noLeverPointer('chapter is fully in the past — no election lever applies'),
    }
  }
  return {
    interpretation_ref,
    prediction_ref: pointerTo('kala_bundle_get', 'the forward temporal field covering this chapter\'s active/upcoming span'),
    intervention_ref: pointerTo('kala_elect_get', `election windows for undertakings during the ${dasha_planet} period`),
  }
}

function buildArgumentReading(chapters: StoryChapter[], nowYear: number): ArgumentReading {
  const current = chapters.find((c) => c.temporal_position === 'current')
  const future = chapters.filter((c) => c.temporal_position === 'future').slice(0, 2)

  const evidence: ArgumentEvidence[] = [current, ...future]
    .filter((c): c is StoryChapter => c != null)
    .slice(0, 3)
    .map((c) => ({
      claim: `${c.dasha_planet} ${c.chapter_level} (${c.start_year}-${c.end_year ?? 'ongoing'}), quality: ${c.parva_quality}, themes: ${c.theme_keywords.join(', ') || 'none recorded'}`,
      // kala_jivana_parva does not expose L1 fact_ids per row at this facade depth
      // (§N.5 — never fabricated); source_citation is stated in the claim's provenance
      // instead via each chapter's own source_citation field.
      fact_ids: [],
      strength: (c.avg_effective_score ?? 0) >= 0.5 ? 'strong' : (c.avg_effective_score ?? 0) > 0 ? 'moderate' : undefined,
    }))

  const thesis = current
    ? `The native is currently in the ${current.dasha_planet} ${current.chapter_level} (${current.start_year}-${current.end_year ?? 'ongoing'}), a ${current.parva_quality} chapter${current.theme_keywords.length ? ` themed around ${current.theme_keywords.join(', ')}` : ''}.`
    : `No chapter in the deduplicated life-arc covers the current year (${nowYear}) — the served horizon may not include it.`

  const verdict = current
    ? { statement: `The ${current.dasha_planet} chapter is ${current.parva_quality}${future[0] ? `; the next chapter (${future[0].dasha_planet}, from ${future[0].start_year}) follows` : ''}.`, tier: 'structural_prior' as const }
    : { statement: 'No current chapter resolvable from the served life-arc.', tier: 'unresolved' as const }

  // No natural resolution horizon is computed at this facade's argument-reading depth —
  // the per-chapter retrodiction_fit (item 10, wired below) is a per-chapter lexical
  // corroboration signal, not a whole-story falsifier condition — an honestly absent
  // falsifier here, never invented.
  const falsifier = null

  return { thesis, evidence, dissent: [], verdict, falsifier }
}

function buildCoverage(
  dedupReport: DedupReport,
  lelEventTotal: number,
  lelFetchError: string | null,
): KalaCoverageEntry[] {
  const coverage: KalaCoverageEntry[] = [
    computedCoverage('dasha_chapter_hierarchy'),
    computedCoverage('parva_dedup_by_span_and_level'),
  ]
  if (dedupReport.collapses.length > 0) {
    coverage.push(honestEmptyCoverage(
      'source_parva_exact_duplicates',
      `${dedupReport.collapses.length} exact-duplicate span group(s) collapsed at serving — see dedup_report; kala_jivana_parva itself still carries the duplicate rows (writer-level root cause out of this facade's scope).`,
    ))
  }
  // §W1 item 10: per-chapter LEL pinning + retrodiction fit — now wired (see file header).
  if (lelFetchError) {
    coverage.push(honestEmptyCoverage(
      'lel_pinning_per_chapter',
      `LEL fetch failed against marsys://tool/L5/lel_query: ${lelFetchError}. Every chapter's ` +
      'retrodiction_fit.note reports this same failure honestly rather than a silent zero.',
    ))
  } else if (lelEventTotal === 0) {
    coverage.push(honestEmptyCoverage(
      'lel_pinning_per_chapter',
      'The LEL fetch succeeded but returned zero events for this chart — no life events are ' +
      'logged for this native/chart, so every chapter honestly pins zero events.',
    ))
    // W2.4b: the SHAD_DARSHANA_BRIEF_v2_0.md §3 W2 checklist specifies the literal flag name
    // `no_lived_history_recorded` for the LEL-absent scenario. The PARĪKṢAKA disposition was
    // PARKED-HONEST ("spirit satisfied, literal flag name absent"). This entry adds the literal
    // name as an alias alongside lel_pinning_per_chapter (backward compat: both are emitted,
    // the pre-existing name is kept so callers that already read lel_pinning_per_chapter are
    // not broken). Only emitted when lelEventTotal === 0 (genuinely no LEL events for chart).
    coverage.push(honestEmptyCoverage(
      'no_lived_history_recorded',
      'No life events are logged in the LEL for this chart/native — the per-chapter retrodiction ' +
      'fit is an honest_empty (not a claim of a quiet period). This flag name is the literal ' +
      'SHAD_DARSHANA_BRIEF_v2_0.md §3 W2 specification; lel_pinning_per_chapter is its alias ' +
      '(retained for backward compatibility).',
    ))
  } else {
    coverage.push(computedCoverage('lel_pinning_per_chapter'))
  }
  coverage.push(notInCorpusCoverage(
    'chara_dasha_second_voice',
    'Chara-daśā narrative overlay (v1 §4.2, item 31-adjacent) not yet joined; STORY currently serves the Vimśottarī spine only.',
  ))
  coverage.push(notInCorpusCoverage(
    'punctuation_events',
    'sky-event calendar (returns, eclipses-on-natal, item 3/4) not yet built; punctuation marks are not interleaved into chapters.',
  ))
  // E6 per-view elevation for STORY: developmental_thesis — what this period asks given what
  // previous chapters built. KALA_SUPREME_ELEVATION_v1_0.md §6: STORY elevation =
  // "developmental_thesis: what this period asks of the native given what previous chapters
  // built (from lord-relationship + house-progression + LEL verdicts of prior same-lord chapters)."
  // SHAD_DARSHANA_CLOSE_v1_0.md §2 E6 disposition: VERIFIED-FIXED (lite); the developmental_thesis
  // sub-elevation is the W3 depth portion — requires cross-chapter lord-relationship analysis not
  // yet wired at the serving facade. G12 R26.
  coverage.push(honestEmptyCoverage(
    'developmental_thesis',
    'E6 per-view elevation for STORY (KALA_SUPREME_ELEVATION_v1_0.md §6): the developmental ' +
    'thesis per chapter — what this period asks given what previous chapters built, from ' +
    'lord-relationship + house-progression + LEL verdicts of prior same-lord chapters — ' +
    'is not yet computed at this facade. Requires cross-chapter lord-relationship analysis ' +
    'wired into story composition. SHAD_DARSHANA_CLOSE_v1_0.md §2 E6 disposition: ' +
    'VERIFIED-FIXED (lite); developmental_thesis is the W3 depth remainder, not yet built.',
  ))
  return coverage
}

export interface KalaStoryResponse extends KalaEnvelope<ArgumentReading> {
  tool: 'kala_story_get'
  chart_id: string
  chapters: StoryChapter[]
  chapter_count: number
  dedup_report: DedupReport
  composed_text: string
}

export async function handleKalaStoryGet(
  input: KalaStoryInput,
  principal: Principal,
): Promise<{ response?: KalaStoryResponse; error?: { message: string; extra?: Record<string, unknown> } }> {
  let content: unknown
  try {
    content = await callKalaRegistryCap('marsys://tool/L3/query_life_arc', {
      chart_id: input.chart_id,
      include_lel_events: false, // honestly not consumed downstream (no-op upstream — see file header)
      top_k: input.top_k ?? 739,
      offset: 0,
    }, principal)
  } catch (err) {
    return { error: { message: String(err), extra: { chart_id: input.chart_id } } }
  }

  const inner = unwrapKalaPayload(content)
  const rawParvas = (inner['parvas'] as RawParva[]) ?? []

  const { chapters: dedupedRaw, report: dedupReport } = dedupParvas(rawParvas)

  // §W1 item 10 — fetch the WHOLE LEL corpus once (not per-chapter — one bounded fetch,
  // bucketed client-side), then pin per chapter by date-range overlap. See file header's
  // CIRCULARITY GUARD note.
  const { events: lelEvents, fetchError: lelFetchError } = await fetchAllChartLelEvents(input.chart_id, principal)

  const nowYear = new Date().getUTCFullYear()
  const chapters: StoryChapter[] = dedupedRaw.map((c) => {
    const position = temporalPosition(c.start_year, c.end_year, nowYear)
    const { pinned, fit } = pinLelEventsToChapter(c.start_year, c.end_year, c.theme_keywords, lelEvents, lelFetchError)
    return {
      ...c,
      temporal_position: position,
      tri_plane: chapterTriPlane(position, c.dasha_planet),
      lel_events_pinned: pinned,
      lel_pinned_count: pinned.length,
      retrodiction_fit: fit,
    }
  })

  const reading = buildArgumentReading(chapters, nowYear)
  const coverage = buildCoverage(dedupReport, lelEvents.length, lelFetchError)
  const composed = composeArgument(reading)
  const questionFrame: QuestionFrame | null = input.question_frame ?? null

  // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
  // (The W0 stub composed from ka_jivana_parva's newest computed_at is retired with it.)
  const fieldSnapshot = await resolveFieldSnapshot(input.chart_id, principal)

  const envelope = makeKalaEnvelope<ArgumentReading>({
    reading,
    questionFrame,
    fieldSnapshot,
    triPlane: {
      // The envelope-level pointer is the whole-story frame; per-chapter pointers above
      // (item 43 "wired on real data") carry the actually-differentiated live pointers.
      interpretation_ref: pointerTo('get_chart_orientation', 'the whole-chart synthesis this life-arc narrates'),
      prediction_ref: pointerTo('kala_bundle_get', 'the forward temporal field for the current/next chapter'),
      intervention_ref: chapters.some((c) => c.temporal_position !== 'past')
        ? pointerTo('kala_elect_get', 'election windows for undertakings inside the current/next chapter')
        : noLeverPointer('every served chapter is in the past — no intervention lever applies'),
    },
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  const response: KalaStoryResponse = {
    ...envelope,
    tool: 'kala_story_get',
    chart_id: input.chart_id,
    chapters,
    chapter_count: chapters.length,
    dedup_report: dedupReport,
    composed_text: composed.full_text,
  }

  const sections: TrimmableSection<KalaStoryResponse>[] = [
    kalaEvidenceTrimmableSection<KalaStoryResponse>({ instrument: 'kala_story_get', hint: 'call again with a narrower top_k for full evidence' }),
    {
      path: 'chapters',
      label: 'life-arc chapters',
      minKeep: 5,
      getArray: (c) => c.chapters,
      setArray: (c, kept) => { c.chapters = kept as StoryChapter[] },
      recover: { instrument: 'kala_story_get', hint: 'call again with a larger budget_kb for the full chapter list' },
    },
  ]

  const budgeted = finalizeMcpBudget(response as unknown as Record<string, unknown>, {
    maxKb: input.budget_kb ?? 40,
    sections: sections as unknown as TrimmableSection<Record<string, unknown>>[],
    budgetKbRequested: input.budget_kb,
  }) as unknown as KalaStoryResponse

  return { response: budgeted }
}

// ── MCP registration ────────────────────────────────────────────────────────────────
// ONE canonical registration site for kala_story_get (SHAD_DARSHANA_BRIEF_v2_0.md §2 file
// map). Mirrors the sibling kala_views registrations (priority.ts's
// registerKalaPriorityTool, etc.) — registry_bridge.ts imports and calls this function.

function dualOutput(data: unknown): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }] } {
  return { structuredContent: { type: 'object', object: data }, content: [{ type: 'text', text: JSON.stringify(data) }] }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: message, tool, ...extra }), isError: true as const }
}

export function registerKalaStoryTool(server: McpServer, principal: Principal): void {
  server.tool(
    'kala_story_get',
    'STORY — "What is the story of my life in time?" Returns the daśā-anchored ' +
    'biographical life-arc (kala_jivana_parva) as a clean chapter hierarchy: each chapter ' +
    'names its lord (mahādaśā or the nested antardaśā self-period), its quality ' +
    '(building/peak/consolidating/receding/transitional), its theme keywords, and whether ' +
    'it is past/current/future — with per-chapter tri-plane pointers into the ' +
    'interpretation, prediction, and intervention (kala_elect_get) planes wired on real ' +
    'data, not stubs (item 43). Fixes the source table\'s known parva-duplication defect ' +
    'at serving (dedup by exact span + daśā level; see this response\'s dedup_report) — ' +
    'the source kala_jivana_parva table itself is unchanged. Each chapter also carries ' +
    'per-chapter LEL pinning + a modest lexical retrodiction_fit (item 10): native-logged ' +
    'life events that fall within the chapter\'s date span, plus how many of them share a ' +
    'literal theme_keyword — an honest corroboration signal, not a calibrated score (that\'s ' +
    'W2\'s mi_bhara job). CIRCULARITY GUARD: this LEL read terminates at this response — it ' +
    'never feeds any prediction, score, or hazard value served elsewhere. W0 depth: Chara-' +
    'daśā second-voice narration and punctuation-mark overlay are not yet wired — reported ' +
    'honestly via this response\'s coverage block.',
    KalaStoryInputShape,
    async (args) => {
      const parsed = args as KalaStoryInput
      if (!parsed.chart_id) return errorOutput('kala_story_get', 'chart_id is required')
      try {
        const { response, error } = await handleKalaStoryGet(parsed, principal)
        if (error) return errorOutput('kala_story_get', error.message, error.extra)
        return dualOutput(response)
      } catch (err) {
        return errorOutput('kala_story_get', String(err), { chart_id: parsed.chart_id })
      }
    },
  )
}
