/**
 * demand_ranking_w3.test.ts
 * ==========================
 * W3 Lane L7 (Retrieval Plane Elevation, plan §8 R-2 item 5) — proves the
 * `demand_ranking.family_rank`/`rank_rationale` extension is REAL: populated
 * on the live L-DOMAIN `assess_*` family through the same `getCatalog()`
 * backfill path both channels consume, not just declared as a type.
 *
 * Loads the REAL registered catalog (same aggregator the MCP + chat channels
 * use) — no fixtures.
 */
import { describe, it, expect } from 'vitest'
import { getCatalog } from '../catalog'
import { __backfillClassificationTables as CLASSIFICATION } from '../descriptor_defaults'

const ASSESS_FAMILY = [
  'marsys://tool/L-DOMAIN/assess_career',
  'marsys://tool/L-DOMAIN/assess_wealth',
  'marsys://tool/L-DOMAIN/assess_marriage',
  'marsys://tool/L-DOMAIN/assess_health',
] as const

describe('W3 L7 — demand_ranking.family_rank on the assess_* family', () => {
  it('every assess_* sibling carries a family_rank + rank_rationale in the live catalog', () => {
    const caps = getCatalog()
    const byUri = new Map(caps.map((c) => [c.uri, c]))
    for (const uri of ASSESS_FAMILY) {
      const cap = byUri.get(uri)
      expect(cap, `${uri} not registered`).toBeDefined()
      const dr = cap!.demand_ranking
      expect(dr, `${uri} missing demand_ranking`).toBeDefined()
      expect(typeof dr!.family_rank, `${uri} family_rank`).toBe('number')
      expect(dr!.family_rank).toBeGreaterThanOrEqual(1)
      expect(typeof dr!.rank_rationale, `${uri} rank_rationale`).toBe('string')
      expect((dr!.rank_rationale ?? '').length).toBeGreaterThan(0)
    }
  })

  it('family_rank is a dense 1..N permutation across the four siblings (a real ordering, no ties/gaps)', () => {
    const caps = getCatalog()
    const byUri = new Map(caps.map((c) => [c.uri, c]))
    const ranks = ASSESS_FAMILY.map((uri) => byUri.get(uri)!.demand_ranking!.family_rank!)
    expect([...ranks].sort((a, b) => a - b)).toEqual([1, 2, 3, 4])
  })

  it('the ranking table is the single source; catalog values match it exactly', () => {
    const caps = getCatalog()
    const byUri = new Map(caps.map((c) => [c.uri, c]))
    for (const [uri, spec] of CLASSIFICATION.ASSESS_FAMILY_RANK.entries()) {
      const dr = byUri.get(uri)!.demand_ranking!
      expect(dr.family_rank).toBe(spec.family_rank)
      expect(dr.rank_rationale).toBe(spec.rank_rationale)
    }
  })

  it('is family-RELATIVE, not cross-family: no kala_*/gochara or other family was stamped', () => {
    const caps = getCatalog()
    const ranked = caps.filter((c) => c.demand_ranking?.family_rank !== undefined)
    // Only the four assess_* siblings carry a family_rank in this worked example.
    expect(ranked.map((c) => c.uri).sort()).toEqual([...ASSESS_FAMILY].sort())
    // Guard the must_not_touch boundary explicitly.
    for (const cap of ranked) {
      expect(cap.uri.toLowerCase()).not.toContain('kala')
      expect(cap.uri.toLowerCase()).not.toContain('gochara')
    }
  })

  it('the pre-existing judgment_query bearing_first ranking is untouched by this extension', () => {
    const caps = getCatalog()
    const jq = caps.find((c) => c.uri === 'marsys://tool/L-JUDGMENT/judgment_query')
    expect(jq?.demand_ranking?.bearing_first).toBe(true)
    // judgment_query is NOT in the assess_* family, so it carries no family_rank.
    expect(jq?.demand_ranking?.family_rank).toBeUndefined()
  })
})
