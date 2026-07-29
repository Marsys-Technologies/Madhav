/**
 * query_life_arc_dedup.integration.test.ts — shad-darshana/parva-dedup live-DB proof.
 *
 * Regression test for a pre-existing serving-layer defect in kala_life_arc_get /
 * query_life_arc.ts (marsys://tool/L3/query_life_arc): the ka_jivana_parva writer
 * (platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py)
 * double-emits the antardasha sitting exactly on a mahadasha boundary — once
 * (wrongly) as the trailing AD of the outgoing MD, once (correctly) as the leading
 * AD of the incoming MD — because its MD-span filter is inclusive on both ends and
 * Vimshottari's own-lord-first rule means every MD's first antardasha shares the
 * MD's own lord, so the boundary AD's start_date satisfies both adjoining MD spans.
 *
 * Live-confirmed (query against kala_jivana_parva, pre-fix): every chart with L3
 * Kāla built carries N pairs of rows sharing an identical (start_year, end_year,
 * dasha_planet) span at the identical AD level — one MD boundary duplicate per
 * mahadasha transition (8-9 pairs on a full-life chart). Before this fix,
 * query_life_arc.ts passed these straight through to kala_life_arc_get callers.
 *
 * Fix (query_life_arc.ts): dedup by (span, level) in SQL via DISTINCT ON, keeping
 * the highest parva_index per group — the later-inserted, correctly-attributed row.
 *
 * Run with: INTEGRATION=true vitest run \
 *   src/lib/retrieval/registry/layers/L3_kala/query_life_arc_dedup.integration.test.ts
 */
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

// Every chart live-confirmed (via direct kala_jivana_parva query) to carry MD-boundary
// duplicate pairs as of this fix.
const CHARTS_WITH_KNOWN_DUPLICATES = [
  '482012f1-710e-4a25-994a-93821f5871aa', // native
  '1c826d5a-41cb-4450-b4dc-59d440e5f75a', // Abhinandan
  'cb73cd3d-9eba-4220-9902-0de91566e980',
]

type ParvaRow = {
  start_year: number
  end_year: number | null
  dasha_planet: string
  source_citation: string
  parva_index: number
}

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>

async function handler(): Promise<Handler> {
  const { queryLifeArcCapability } = await import('./query_life_arc')
  return queryLifeArcCapability.handler as Handler
}

/** Mirrors the SQL CASE in query_life_arc.ts: derive the daśā level from source_citation,
 *  since kala_jivana_parva carries no explicit level column. */
function parvaLevel(sourceCitation: string): 'MD' | 'AD' | 'PD' {
  if (sourceCitation.includes(':AD=')) return 'AD'
  if (sourceCitation.includes(':PD=')) return 'PD'
  return 'MD'
}

function spanLevelKey(row: ParvaRow): string {
  return `${row.start_year}|${row.end_year ?? 'null'}|${row.dasha_planet}|${parvaLevel(row.source_citation)}`
}

describeIf('shad-darshana/parva-dedup — kala_life_arc_get: no (span, level) duplicates', () => {
  for (const chartId of CHARTS_WITH_KNOWN_DUPLICATES) {
    it(`chart ${chartId}: every (start_year, end_year, dasha_planet, level) group has exactly 1 row`, async () => {
      const h = await handler()
      const res = await h({ chart_id: chartId, top_k: 739, offset: 0 })
      expect(res.is_error).not.toBe(true)

      const parvas = res.content['parvas'] as ParvaRow[]
      expect(parvas.length).toBeGreaterThan(0)

      const counts = new Map<string, ParvaRow[]>()
      for (const row of parvas) {
        const key = spanLevelKey(row)
        const bucket = counts.get(key) ?? []
        bucket.push(row)
        counts.set(key, bucket)
      }

      const duplicateGroups = [...counts.entries()].filter(([, rows]) => rows.length > 1)
      expect(
        duplicateGroups,
        `found (span, level) duplicate groups: ${JSON.stringify(duplicateGroups)}`
      ).toHaveLength(0)

      // parva_count must match the deduped array length (no drift between the two).
      expect(res.content['parva_count']).toBe(parvas.length)
    })
  }

  it('native chart 482012f1: the known MD=Jupiter/Saturn boundary collapses to the ' +
     'correctly-attributed MD=Saturn:AD=Saturn row (not the MD=Jupiter:AD=Saturn misattribution)', async () => {
    const h = await handler()
    const res = await h({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', top_k: 739, offset: 0 })
    const parvas = res.content['parvas'] as ParvaRow[]

    const matches = parvas.filter(
      (row) => row.start_year === 1991 && row.end_year === 1994 && row.dasha_planet === 'Saturn'
    )
    expect(matches).toHaveLength(1)
    expect(matches[0]!.source_citation).toContain('MD=Saturn:AD=Saturn')
    expect(matches[0]!.source_citation).not.toContain('MD=Jupiter:AD=Saturn')
  })
})
