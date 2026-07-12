/**
 * instrument.test.ts — WP-1.4 Large-N Synthesis Instrument (LCA-15 / R-48)
 * ========================================================================
 * Proves the acceptance criteria WITHOUT a live DB, via an injected fake gateway whose
 * family sizes mirror the real native chart (career=12,364, relationship=7,014, …):
 *
 *   1. Composes a multi-family answer WITHOUT a flat top-K wall — total atomic signal
 *      rows served is budget-bounded (≤ total_signal_rows), even though the families
 *      contain tens of thousands of signals; each family declares its true total.
 *   2. The derivation ledger's signal_ids/fact_ids resolve (against the injected universe).
 *   3. Degrades honestly where a stage is thin (contradictions=0) — discloses, doesn't dump.
 */

import { describe, it, expect } from 'vitest'
import { composeLargeN } from '../instrument'
import { decompose } from '../intent'
import type { SurfaceGateway, FamilyDrill, GestaltOrientation, DispositorPath, TensionResult } from '../surface_gateway'
import type { Domain } from '../types'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

// Real native-chart family sizes (from bounded prod probe) — the flat-wall universe.
const FAMILY_TOTALS: Record<string, number> = {
  career: 12364, character: 7294, relationship: 7014,
  spirituality: 3338, wealth: 2003, health: 748, other: 0,
}

// A known signal-id universe so ledger resolvability is checkable in-process.
const KNOWN_SIGNAL_IDS = new Set<string>()
const KNOWN_FACT_IDS = new Set<string>()

function makeExemplars(domain: Domain, n: number) {
  const out = []
  for (let i = 0; i < n; i++) {
    const sid = `sig-${domain}-${i}`
    const fid = `F-${domain}-${i}`
    KNOWN_SIGNAL_IDS.add(sid)
    KNOWN_FACT_IDS.add(fid)
    out.push({
      signal_id: sid,
      headline: `${domain} factor ${i}`,
      summary: `summary ${i}`,
      salience: 1 - i * 0.01,
      constituent_fact_ids: [fid],
    })
  }
  return out
}

/** Fake gateway: unlimited supply per family, real totals, a gestalt verdict, 0 contradictions. */
class FakeGateway implements SurfaceGateway {
  constructor(private opts: { contradictions?: number; gestalt?: boolean } = {}) {}

  async gestalt(): Promise<GestaltOrientation> {
    if (this.opts.gestalt === false) return { verdict_map: {}, central_question: null, found: false }
    const sid = 'sig-gestalt-verdict-1'
    KNOWN_SIGNAL_IDS.add(sid)
    return {
      verdict_map: { relationship: { signal_id: sid, confidence: 0.23, verdict_class: 'neutral' },
                     spirituality: { signal_id: sid, confidence: 0.23, verdict_class: 'neutral' } },
      central_question: { note: 'x' },
      found: true,
    }
  }

  async familyDrill(_c: string, _a: string, domain: Domain, cap: number): Promise<FamilyDrill> {
    const total = FAMILY_TOTALS[domain] ?? 0
    const n = Math.min(cap, total)
    return {
      exemplars: makeExemplars(domain, n),
      total_in_family: total,
      linkages: total > 0
        ? [{ domain_row: 'relationship', domain_col: 'career', shared_signal_count: 6160, linkage_strength: 6764.5, contradiction_flag: false }]
        : [],
    }
  }

  async dispositorPaths(): Promise<DispositorPath[]> {
    return [{ path_id: 'p1', path_label: 'Ve→Sa', path_strength: 0.8, is_final_dispositor: true }]
  }

  async tension(): Promise<TensionResult> {
    const n = this.opts.contradictions ?? 0
    return { contradiction_count: n, contradictions: [], note: n === 0 ? 'bodha_contradictions=0' : '' }
  }
}

describe('WP-1.4 large-N instrument — intent decomposition (P-10)', () => {
  it('marriage question → relationship primary + cross-domain families (marriage_universe)', () => {
    const c = decompose('Map the whole marriage universe for this native')
    expect(c.primary_domain).toBe('relationship')
    expect(c.matched_template).toBe('marriage_universe')
    const domains = c.families.map(f => f.domain)
    expect(domains).toContain('relationship')
    expect(domains).toContain('career') // strongest cross-domain linkage
    // orientation family is always first
    expect(c.families[0].role).toBe('orientation')
  })

  it('moksha question → spirituality primary (moksha_universe)', () => {
    const c = decompose('What does the chart say about moksha and liberation?')
    expect(c.primary_domain).toBe('spirituality')
    expect(c.matched_template).toBe('moksha_universe')
  })

  it('unmatched question → generic decomposition, disclosed method', () => {
    const c = decompose('tell me something')
    expect(c.decomposition_method).toBe('keyword_generic')
  })
})

describe('WP-1.4 large-N instrument — staged composition (no flat top-K wall)', () => {
  it('composes marriage universe budget-bounded: total atomic rows ≤ budget despite 30k+ signals', async () => {
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe', budget: { total_signal_rows: 40, per_family_cap: 10 } },
      new FakeGateway(),
    )

    // (1) NO FLAT WALL: total atomic signal rows served is budget-bounded.
    const totalServed = answer.families.reduce((n, f) => n + f.served, 0)
    expect(totalServed).toBeLessThanOrEqual(40)
    expect(answer.budget.total_signal_rows_served).toBe(totalServed)

    // No single family monopolizes — each ≤ per_family_cap.
    for (const f of answer.families) expect(f.served).toBeLessThanOrEqual(10)

    // Yet the composed universe spans tens of thousands — disclosed, not dumped.
    const universe = answer.families.reduce((n, f) => n + f.total_in_family, 0)
    expect(universe).toBeGreaterThan(20000)

    // Every family that has more than it served declares more_available (receipt honesty).
    for (const f of answer.families) {
      if (f.total_in_family > f.served) expect(f.more_available).toBe(true)
    }
  })

  it('running budget exhausts: later families are DISCLOSED (served=0, total>0), not dumped', async () => {
    // Tiny budget forces exhaustion before all families are drilled.
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe', budget: { total_signal_rows: 15, per_family_cap: 10 } },
      new FakeGateway(),
    )
    const disclosed = answer.families.filter(f => f.disposition === 'budget_exhausted')
    expect(disclosed.length).toBeGreaterThan(0)
    for (const f of disclosed) {
      expect(f.served).toBe(0)
      expect(f.total_in_family).toBeGreaterThan(0) // still discloses the real size
      expect(f.more_available).toBe(true)
    }
    expect(answer.budget.families_disclosed_not_dumped).toBe(disclosed.length)
  })

  it('plans against PRE-AGGREGATED surfaces before atomic drill (order + kind)', async () => {
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe' },
      new FakeGateway(),
    )
    const stages = answer.plan.map(p => p.stage)
    // orient must precede the atomic map-reduce
    expect(stages.indexOf('orient')).toBeLessThan(stages.indexOf('map_reduce_families'))
    // orient + cross-domain + dispositor are pre-aggregated; only map_reduce is atomic_drill
    const orient = answer.plan.find(p => p.stage === 'orient')!
    const mapreduce = answer.plan.find(p => p.stage === 'map_reduce_families')!
    expect(orient.kind).toBe('pre_aggregated')
    expect(mapreduce.kind).toBe('atomic_drill')
  })
})

describe('WP-1.4 large-N instrument — derivation ledger resolvability (§N.5)', () => {
  it('every ledger signal_id and fact_id resolves against the served universe', async () => {
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe' },
      new FakeGateway(),
    )
    expect(answer.derivation_ledger.length).toBeGreaterThan(0)
    let checkedSignals = 0
    let checkedFacts = 0
    for (const entry of answer.derivation_ledger) {
      for (const sid of entry.signal_ids) {
        expect(KNOWN_SIGNAL_IDS.has(sid)).toBe(true) // resolves
        checkedSignals++
      }
      for (const fid of entry.fact_ids) {
        expect(KNOWN_FACT_IDS.has(fid)).toBe(true) // resolves
        checkedFacts++
      }
    }
    expect(checkedSignals).toBeGreaterThan(0)
    expect(checkedFacts).toBeGreaterThan(0)
    // The orientation claim is grounded in the gestalt verdict signal_id.
    const orient = answer.narrative.find(s => s.heading.startsWith('Orientation'))!
    expect(orient.ledger[0].signal_ids).toContain('sig-gestalt-verdict-1')
  })
})

describe('WP-1.4 large-N instrument — honest degradation', () => {
  it('contradictions=0 → discloses the thin stage, does not fabricate', async () => {
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe' },
      new FakeGateway({ contradictions: 0 }),
    )
    const tensionSection = answer.narrative.find(s => s.heading.startsWith('Tension'))!
    expect(tensionSection.body).toMatch(/thin stage disclosed|not fabricated/i)
    expect(answer.disclosures.some(d => /contradiction/i.test(d))).toBe(true)
  })

  it('missing gestalt → orientation disclosed thin, still composes families', async () => {
    const answer = await composeLargeN(
      { chart_id: CHART, question: 'Map the whole marriage universe' },
      new FakeGateway({ gestalt: false }),
    )
    expect(answer.disclosures.some(d => /gestalt|orientation/i.test(d))).toBe(true)
    // still produced family composites despite thin orientation
    expect(answer.families.length).toBeGreaterThan(0)
  })
})
