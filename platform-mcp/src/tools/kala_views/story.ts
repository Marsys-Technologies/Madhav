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
 *   - It does NOT implement per-chapter LEL pinning + retrodiction fit (item 10) — W1; and
 *     `query_life_arc.ts`'s `include_lel_events` param is currently a no-op (verified: the
 *     capability's SQL never joins an LEL table despite the param name) — reported honestly
 *     via `honest_empty` coverage below, not silently assumed working.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  buildFieldSnapshotIdStub,
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
import { callKalaRegistryCap, unwrapKalaPayload } from './shared.js'

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
export function dedupParvas(rows: RawParva[]): { chapters: Omit<StoryChapter, 'tri_plane' | 'temporal_position'>[]; report: DedupReport } {
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

  // No natural resolution horizon is computed at this facade depth (per-chapter LEL
  // retrodiction fit, item 10, is W1) — an honestly absent falsifier, never invented.
  const falsifier = null

  return { thesis, evidence, dissent: [], verdict, falsifier }
}

function buildCoverage(dedupReport: DedupReport): KalaCoverageEntry[] {
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
  coverage.push(honestEmptyCoverage(
    'lel_pinning_per_chapter',
    'query_life_arc\'s include_lel_events param does not currently join LEL rows into the ' +
    'response (verified against live data 2026-07-29) — per-chapter LEL evidence + ' +
    'retrodiction fit (item 10, W1) is not available to this facade yet.',
  ))
  coverage.push(notInCorpusCoverage(
    'chara_dasha_second_voice',
    'Chara-daśā narrative overlay (v1 §4.2, item 31-adjacent) not yet joined; STORY currently serves the Vimśottarī spine only.',
  ))
  coverage.push(notInCorpusCoverage(
    'punctuation_events',
    'sky-event calendar (returns, eclipses-on-natal, item 3/4) not yet built; punctuation marks are not interleaved into chapters.',
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

  const nowYear = new Date().getUTCFullYear()
  const chapters: StoryChapter[] = dedupedRaw.map((c) => {
    const position = temporalPosition(c.start_year, c.end_year, nowYear)
    return { ...c, temporal_position: position, tri_plane: chapterTriPlane(position, c.dasha_planet) }
  })

  const reading = buildArgumentReading(chapters, nowYear)
  const coverage = buildCoverage(dedupReport)
  const composed = composeArgument(reading)
  const questionFrame: QuestionFrame | null = input.question_frame ?? null

  const mostRecentComputedAt = rawParvas.reduce<string | null>((acc, r) => {
    if (!r.computed_at) return acc
    if (acc === null || r.computed_at > acc) return r.computed_at
    return acc
  }, null)

  const envelope = makeKalaEnvelope<ArgumentReading>({
    reading,
    questionFrame,
    fieldSnapshotId: buildFieldSnapshotIdStub({ ka_jivana_parva: mostRecentComputedAt }),
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
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
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
    'the source kala_jivana_parva table itself is unchanged. W0 depth: Chara-daśā second-' +
    'voice narration, punctuation-mark overlay, and per-chapter LEL pinning are not yet ' +
    'wired — reported honestly via this response\'s coverage block.',
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
