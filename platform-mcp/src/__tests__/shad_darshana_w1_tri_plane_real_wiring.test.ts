/**
 * shad_darshana_w1_tri_plane_real_wiring.test.ts — ṢAḌ-DARŚANA W1 item 43 (SHAD_DARSHANA_
 * BRIEF_v2_0.md §3 W1 "43 (tri-plane pointers wired on real data)"; design authority
 * KALA_SUPREME_ELEVATION_v1_0.md §11).
 *
 * The W0 unit battery (`shad_darshana_w0_tri_plane_no_dead_end.test.ts`) proves the SHAPE
 * every tri-plane slot must have (a well-formed `{instrument, hint}` pointer or an honest
 * `no_lever(reason)` — never a third shape). This file proves something the shape check
 * cannot: that the wiring on all SIX view facades is REAL, not a decorative placeholder —
 *
 *   (A) STATIC CENSUS — every `instrument` string any facade's tri_plane construction cites
 *       resolves to an ACTUALLY-REGISTERED tool somewhere in `platform-mcp/src/tools/**`,
 *       never a dangling/typo'd reference to a tool that was renamed or never built. This
 *       is the "no dead-end" guarantee at the granularity the W0 shape check cannot reach
 *       (a syntactically well-formed pointer to a NONEXISTENT tool would still pass the W0
 *       battery — this census is what actually catches that class of regression).
 *
 *   (B) CONDITIONAL WIRING — for the two facades whose tri_plane branches on the object's
 *       OWN computed state (STORY: past vs current/future chapter; EXPLAIN: PACT chain
 *       live vs denied), asserts BOTH branches independently and deterministically (not
 *       dependent on wall-clock date) — the gap this lane closed: the pre-existing STORY
 *       test only exercised whichever branch the ACTUAL current date happened to produce.
 *
 *   (C) UNCONDITIONAL WIRING SURVIVES TOTAL DATA UNREACHABILITY — for NOW/AHEAD (which
 *       degrade gracefully to honest_empty coverage rather than hard-erroring when their
 *       OWN data sources are unreachable), proves the tri_plane pointers to SIBLING views
 *       (kala_ahead_get, kala_elect_get, kala_explain_get) are viewlevel facts that do NOT
 *       collapse to no_lever just because this call's own substrate happened to be down —
 *       i.e. they are not silently gated on data availability where they should not be.
 *
 * Items 8/10/28/29/32 (the substrate that landed since W0) do not change any of the SIX
 * facades' tri_plane wiring — none of the tri_plane branches in this codebase are
 * conditioned on those specific fields (confirmed by reading every tri_plane construction
 * site: NOW/AHEAD/PRIORITY are unconditional view-level pointers; ELECT is unconditional;
 * only STORY/EXPLAIN branch, and both branch on OTHER already-real state — temporal_position
 * and pact_status respectively, both of which predate this wave). This file's job is
 * therefore the regression guard proving that remains true, not a rewrite.
 */
import { describe, it, expect, vi } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Principal } from '../types.js'
import { isNoLever, type TriPlanePointer } from '../lib/kala_envelope.js'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const TOOLS_ROOT = path.join(HERE, '..', 'tools')

function isWellFormedPointer(p: TriPlanePointer): boolean {
  return !isNoLever(p) && typeof (p as { instrument?: unknown }).instrument === 'string' &&
    (p as { instrument: string }).instrument.trim().length > 0 &&
    typeof (p as { hint?: unknown }).hint === 'string' && (p as { hint: string }).hint.trim().length > 0
}

function assertRealPointer(p: TriPlanePointer | null, label: string): void {
  expect(p, `${label}: expected a real pointer, got null`).not.toBeNull()
  expect(isNoLever(p!), `${label}: expected a real pointer, got a no_lever`).toBe(false)
  expect(isWellFormedPointer(p!), `${label}: pointer is malformed`).toBe(true)
}

function assertHonestNoLever(p: TriPlanePointer | null, label: string): void {
  expect(p, `${label}: expected an honest no_lever, got null`).not.toBeNull()
  expect(isNoLever(p!), `${label}: expected a no_lever, got a real pointer`).toBe(true)
  expect((p as { reason: string }).reason.trim().length, `${label}: no_lever reason is empty`).toBeGreaterThan(0)
}

// ── (A) Static census — every instrument name cited by a tri_plane pointer construction
// site in the six view facades resolves to a tool actually registered SOMEWHERE under
// platform-mcp/src/tools. ────────────────────────────────────────────────────────────────

function walkTs(dir: string, out: string[]): void {
  let entries: string[]
  try { entries = readdirSync(dir) } catch { return }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue
    const full = path.join(dir, entry)
    let st
    try { st = statSync(full) } catch { continue }
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts') && !entry.endsWith('.test.ts')) out.push(full)
  }
}

function readAllToolSources(): { file: string; content: string }[] {
  const files: string[] = []
  walkTs(TOOLS_ROOT, files)
  return files.map((f) => ({ file: f, content: readFileSync(f, 'utf-8') }))
}

/** Every `pointerTo('<instrument>', ...)` call site's first-argument literal, collected from
 *  the six view facades' own source (a purely static/textual scan — no execution). */
function collectCitedInstruments(sources: { file: string; content: string }[]): Map<string, string[]> {
  const cited = new Map<string, string[]>()
  const viewFiles = sources.filter((s) => s.file.includes(`${path.sep}kala_views${path.sep}`) && !s.file.endsWith(`${path.sep}shared.ts`))
  for (const { file, content } of viewFiles) {
    for (const m of content.matchAll(/pointerTo\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) {
      const name = m[1]!
      const list = cited.get(name) ?? []
      if (!list.includes(file)) list.push(file)
      cited.set(name, list)
    }
  }
  return cited
}

/** True iff `name` is registered as a real MCP tool anywhere under platform-mcp/src/tools —
 *  either directly (`server.tool('name', ...)` / `regAlias(server, 'name', ...)`) or via the
 *  `const TOOL_NAME = 'name'` + `server.tool(TOOL_NAME, ...)` indirection some older files
 *  (e.g. kala_temporal.ts's kala_bundle_get) use. */
function isRegisteredAnywhere(name: string, sources: { file: string; content: string }[]): boolean {
  const patterns = [
    new RegExp(`server\\.tool\\(\\s*['"]${name}['"]`),
    new RegExp(`regAlias\\(server,\\s*['"]${name}['"]`),
    new RegExp(`globalAlias\\(server,\\s*['"]${name}['"]`),
    new RegExp(`TOOL_NAME\\s*=\\s*['"]${name}['"]`),
  ]
  return sources.some(({ content }) => patterns.some((p) => p.test(content)))
}

describe('item 43 — static census: every tri_plane instrument cited by a view facade is a REAL registered tool', () => {
  it('resolves every pointerTo() instrument literal in tools/kala_views/*.ts to an actually-registered tool', () => {
    const sources = readAllToolSources()
    const cited = collectCitedInstruments(sources)

    // Sanity: the census itself must have found SOMETHING, or this test is vacuously green
    // (CLAUDE.md §N.8 — a check with nothing behind it is null, not a pass).
    expect(cited.size, 'static scan found zero pointerTo() call sites — the scan itself is broken').toBeGreaterThan(0)

    const unresolved: string[] = []
    for (const [name, files] of cited) {
      if (!isRegisteredAnywhere(name, sources)) {
        unresolved.push(`${name} (cited from: ${files.map((f) => path.basename(f)).join(', ')})`)
      }
    }
    expect(unresolved, `dangling tri_plane pointer(s) — cited instrument not found registered anywhere:\n${unresolved.join('\n')}`).toEqual([])
  })

  it('the six view facades collectively cite more than one distinct real instrument (never all pointing at a single stub target)', () => {
    const sources = readAllToolSources()
    const cited = collectCitedInstruments(sources)
    expect(cited.size).toBeGreaterThan(1)
    // The core cross-references item 43 exists to guarantee: NOW/AHEAD/ELECT/EXPLAIN form a
    // real traversable ring, not a decorative loop back to one placeholder.
    expect(cited.has('kala_ahead_get')).toBe(true)
    expect(cited.has('kala_elect_get')).toBe(true)
  })
})

// ── (B) Conditional wiring — STORY (past vs current/future), deterministic, not
// wall-clock-dependent. ──────────────────────────────────────────────────────────────────

describe('item 43 — STORY conditional tri_plane wiring is real, not blanket no_lever (deterministic, not wall-clock-dependent)', () => {
  const PRINCIPAL: Principal = { user_uid: 'u1', key_id: 'k1', role: 'guest' }
  const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

  function mockParvaFetch(parvas: Array<Record<string, unknown>>) {
    return vi.fn(async (_url: unknown, opts: unknown) => {
      const body = JSON.parse((opts as { body: string }).body) as { uri: string }
      if (body.uri === 'marsys://tool/L3/query_life_arc') {
        return { ok: true, json: async () => ({ ok: true, content: { chart_id: CHART_ID, parvas } }) }
      }
      // Any other URI (e.g. LEL query) — honest empty, not this test's concern.
      return { ok: true, json: async () => ({ ok: true, content: {} }) }
    }) as unknown as typeof fetch
  }

  it('a chapter fully in the past gets HONEST no_lever prediction_ref/intervention_ref (never a fabricated forward pointer)', async () => {
    global.fetch = mockParvaFetch([
      {
        id: 1, parva_index: 1, dasha_planet: 'Saturn', start_year: 1950, end_year: 1970,
        parva_quality: 'building', theme_keywords: ['discipline'], high_convergence_count: 1,
        avg_effective_score: 0.3, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-01T00:00:00Z',
      },
    ])
    const { handleKalaStoryGet } = await import('../tools/kala_views/story.js')
    const { response, error } = await handleKalaStoryGet({ chart_id: CHART_ID }, PRINCIPAL)
    expect(error).toBeUndefined()
    const chapter = response!.chapters[0]!
    expect(chapter.temporal_position).toBe('past')
    assertRealPointer(chapter.tri_plane.interpretation_ref, 'STORY past chapter interpretation_ref')
    assertHonestNoLever(chapter.tri_plane.prediction_ref, 'STORY past chapter prediction_ref')
    assertHonestNoLever(chapter.tri_plane.intervention_ref, 'STORY past chapter intervention_ref')
    // The whole-response (envelope-level) intervention_ref ALSO branches on "any chapter not
    // past" — with every served chapter past, it too must be an honest no_lever, not a
    // dangling pointer to an election that has nothing left to elect for.
    assertHonestNoLever(response!.tri_plane.intervention_ref, 'STORY envelope-level intervention_ref (all chapters past)')
  })

  it('a chapter running now/future gets REAL prediction_ref/intervention_ref pointers (never a stubbed no_lever)', async () => {
    global.fetch = mockParvaFetch([
      {
        id: 2, parva_index: 2, dasha_planet: 'Mercury', start_year: 2020, end_year: 2100,
        parva_quality: 'building', theme_keywords: ['communication'], high_convergence_count: 4,
        avg_effective_score: 0.6, narrative: {}, source_citation: 'ka_jivana_parva:v1.0', computed_at: '2026-07-01T00:00:00Z',
      },
    ])
    const { handleKalaStoryGet } = await import('../tools/kala_views/story.js')
    const { response, error } = await handleKalaStoryGet({ chart_id: CHART_ID }, PRINCIPAL)
    expect(error).toBeUndefined()
    const chapter = response!.chapters[0]!
    expect(chapter.temporal_position).not.toBe('past')
    assertRealPointer(chapter.tri_plane.interpretation_ref, 'STORY current chapter interpretation_ref')
    assertRealPointer(chapter.tri_plane.prediction_ref, 'STORY current chapter prediction_ref')
    assertRealPointer(chapter.tri_plane.intervention_ref, 'STORY current chapter intervention_ref')
    expect((chapter.tri_plane.intervention_ref as { instrument: string }).instrument).toBe('kala_elect_get')
    // Envelope-level intervention_ref flips to a real pointer once ANY served chapter is not past.
    assertRealPointer(response!.tri_plane.intervention_ref, 'STORY envelope-level intervention_ref (a chapter is current/future)')
  })
})

// ── (C) NOW/AHEAD — the tri_plane pointer to sibling views survives total data
// unreachability (view-level fact, not data-conditional where it should not be). ──────────

describe('item 43 — NOW/AHEAD tri_plane pointers to sibling views are real even when this call\'s OWN substrate is fully unreachable', () => {
  const PRINCIPAL: Principal = { user_uid: 'u1', key_id: 'k1', role: 'guest' }
  const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

  function unreachableFetch() {
    return vi.fn(async () => ({ ok: false, status: 500, text: async () => 'down' })) as unknown as typeof fetch
  }

  it('kala_now_get: interpretation_ref honestly null (NOW IS the interpretation plane); prediction_ref/intervention_ref remain real pointers to kala_ahead_get/kala_elect_get', async () => {
    global.fetch = unreachableFetch()
    const { computeKalaNow } = await import('../tools/kala_views/now.js')
    const result = await computeKalaNow(CHART_ID, {}, PRINCIPAL)
    expect(result.tri_plane.interpretation_ref).toBeNull()
    assertRealPointer(result.tri_plane.prediction_ref, 'NOW prediction_ref (unreachable substrate)')
    assertRealPointer(result.tri_plane.intervention_ref, 'NOW intervention_ref (unreachable substrate)')
    expect((result.tri_plane.prediction_ref as { instrument: string }).instrument).toBe('kala_ahead_get')
    expect((result.tri_plane.intervention_ref as { instrument: string }).instrument).toBe('kala_elect_get')
  })

  it('kala_ahead_get: prediction_ref honestly null (AHEAD IS the prediction plane); interpretation_ref/intervention_ref remain real pointers to kala_explain_get/kala_elect_get', async () => {
    global.fetch = unreachableFetch()
    const { computeKalaAhead } = await import('../tools/kala_views/ahead.js')
    const result = await computeKalaAhead(CHART_ID, {}, PRINCIPAL)
    expect(result.tri_plane.prediction_ref).toBeNull()
    assertRealPointer(result.tri_plane.interpretation_ref, 'AHEAD interpretation_ref (unreachable substrate)')
    assertRealPointer(result.tri_plane.intervention_ref, 'AHEAD intervention_ref (unreachable substrate)')
    expect((result.tri_plane.interpretation_ref as { instrument: string }).instrument).toBe('kala_explain_get')
    expect((result.tri_plane.intervention_ref as { instrument: string }).instrument).toBe('kala_elect_get')
  })
})
