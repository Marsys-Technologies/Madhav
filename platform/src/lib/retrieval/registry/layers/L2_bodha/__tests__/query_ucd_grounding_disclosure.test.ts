/**
 * DEFECT-1 (FactId served-impact audit) — query_ucd grounding disclosure.
 *
 * `grounding.resolvable` used to be the literal `true as const` even when cited fact_ids
 * failed to resolve in chart_facts (e.g. stale ids between an L1 rebuild and the L2
 * rebuild). It is now EARNED (CLAUDE.md §N.8): resolvable === (unresolved_fact_count === 0),
 * with cited/unresolved counts disclosed and the attribution note naming the real cause.
 *
 * Mutation proof: reintroducing `resolvable: true` in deriveGroundingBlock makes the
 * "1 of 4" and "0 of 4" cases below FAIL.
 */

import { describe, it, expect } from 'vitest'
import { citedFactIdsOf, countUnresolvedFactIds, deriveGroundingBlock, deriveAttributionNote } from '../query_ucd'

const IDS = ['F-1', 'F-2', 'F-3', 'F-4']
const cited = new Set(IDS)
const mapOf = (ids: string[]) => new Map(ids.map(id => [id, 'D108_SAT'] as [string, string]))

describe('DEFECT-1 — deriveGroundingBlock', () => {
  it('4 cited, 4 resolved -> resolvable true, unresolved 0, no disclosure sentence', () => {
    const g = deriveGroundingBlock({ cited, resolvedMap: mapOf(IDS), groundingFactIds: IDS })
    expect(g.resolvable).toBe(true)
    expect(g.unresolved_fact_count).toBe(0)
    expect(g.cited_fact_count).toBe(4)
    expect(g.resolved_fact_count).toBe(4)
    expect(g.fact_ids).toEqual(IDS)
    expect(g.note).not.toContain('DEFECT-1 disclosure')
  })

  it('4 cited, 1 resolved -> resolvable false, unresolved 3, disclosure names the stale ids', () => {
    const g = deriveGroundingBlock({ cited, resolvedMap: mapOf(['F-1']), groundingFactIds: ['F-1'] })
    expect(g.resolvable).toBe(false)
    expect(g.unresolved_fact_count).toBe(3)
    expect(g.cited_fact_count).toBe(4)
    expect(g.resolved_fact_count).toBe(1)
    expect(g.note).toContain('DEFECT-1 disclosure')
    expect(g.note).toContain('3 of 4')
  })

  it('4 cited, 0 resolved -> resolvable false, unresolved 4, resolved_fact_count 0', () => {
    const g = deriveGroundingBlock({ cited, resolvedMap: new Map(), groundingFactIds: [] })
    expect(g.resolvable).toBe(false)
    expect(g.unresolved_fact_count).toBe(4)
    expect(g.cited_fact_count).toBe(4)
    expect(g.resolved_fact_count).toBe(0)
  })

  it('empty cited -> vacuously resolvable true, unresolved 0 (nothing claimed, nothing stale)', () => {
    const g = deriveGroundingBlock({ cited: new Set(), resolvedMap: new Map(), groundingFactIds: [] })
    expect(g.resolvable).toBe(true)
    expect(g.unresolved_fact_count).toBe(0)
    expect(g.cited_fact_count).toBe(0)
  })

  it('resolvable is a boolean (not the literal true type) so false is representable', () => {
    const g = deriveGroundingBlock({ cited, resolvedMap: new Map(), groundingFactIds: [] })
    const asBool: boolean = g.resolvable
    expect(asBool).toBe(false)
  })
})

describe('DEFECT-1 — cited/unresolved helpers', () => {
  it('citedFactIdsOf dedupes and ignores null/empty/non-string entries', () => {
    const s = citedFactIdsOf([
      { constituent_facts_array: ['F-1', 'F-2', ''] },
      { constituent_facts_array: ['F-2', 'F-3'] },
      { constituent_facts_array: null },
      {},
    ])
    expect([...s].sort()).toEqual(['F-1', 'F-2', 'F-3'])
  })

  it('countUnresolvedFactIds counts only cited ids absent from the map (extra map ids do not offset)', () => {
    expect(countUnresolvedFactIds(cited, mapOf(['F-1', 'X-9']))).toBe(3)
  })
})

describe('DEFECT-1 — deriveAttributionNote names the real cause', () => {
  it('unresolved 0 -> the original WP-1.2β panchāṅga/muhūrta note, unchanged', () => {
    const n = deriveAttributionNote({ servedUnattributed: 0, unresolvedFactCount: 0 })
    expect(n).toContain('0% UNATTRIBUTED on the served ranked surface')
    expect(n).toContain('panchāṅga/muhūrta birth-moment descriptors')
  })

  it('unresolved > 0 -> blames stale/unresolved fact ids, not descriptors alone', () => {
    const n = deriveAttributionNote({ servedUnattributed: 0, unresolvedFactCount: 157 })
    expect(n).toContain('157 distinct constituent fact_id(s)')
    expect(n).toContain('stale/unresolved ids')
    expect(n).toContain('PARTIAL')
    expect(n).not.toContain('genuinely un-attributable')
  })

  it('served unattributed entities -> the existing gap sentence', () => {
    expect(deriveAttributionNote({ servedUnattributed: 2, unresolvedFactCount: 5 }))
      .toContain('2 UNATTRIBUTED entity(ies) surfaced')
  })
})
