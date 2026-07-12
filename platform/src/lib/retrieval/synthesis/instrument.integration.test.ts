/**
 * instrument.integration.test.ts — WP-1.4 Large-N instrument, LIVE DB (LCA-15 / R-48)
 * ====================================================================================
 * Runs the instrument end-to-end against the real served surfaces (RegistrySurfaceGateway →
 * registered L2 capabilities → bodha_* tables) for TWO Lane-7 heavy questions:
 *   - marriage universe  (F-0961)
 *   - moksha             (F-0973 / F-0974)
 * and proves against ground truth:
 *   1. Composes without a flat top-K wall — total atomic rows served ≤ budget, while the
 *      disclosed universe spans tens of thousands (career alone = 12,364).
 *   2. Every derivation-ledger signal_id RESOLVES in bodha_msr_signals (§N.5).
 *   3. Degrades honestly on the native chart's contradictions=0 (LCA-6/WP-2.2) — discloses.
 *
 * Run with (DATABASE_URL from platform/.env.local — the live Cloud SQL proxy creds):
 *   export DATABASE_URL="$(grep -E '^DATABASE_URL=' platform/.env.local | sed 's/^DATABASE_URL=//;s/^\"//;s/\"$//')"
 *   INTEGRATION=true vitest run src/lib/retrieval/synthesis/instrument.integration.test.ts
 */
import { describe, it, expect, beforeAll } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const D = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'

D('WP-1.4 large-N instrument — live composition on the native chart', () => {
  // Registers all capabilities (incl. the synthesis instrument) as a side-effect.
  beforeAll(async () => {
    await import('../registry/catalog')
  })

  it('marriage universe: budget-bounded, ledger resolves, honest degradation', async () => {
    const { composeLargeN } = await import('./instrument')
    const { query } = await import('@/lib/db/client')

    const answer = await composeLargeN({
      chart_id: NATIVE,
      question: 'Map the whole marriage universe for this native — timing, stability, and the tensions around it.',
      ayanamsha_id: LAHIRI,
      budget: { total_signal_rows: 60, per_family_cap: 10 },
    })

    // (1) NO FLAT WALL — total atomic rows bounded, universe large + disclosed.
    const served = answer.families.reduce((n, f) => n + f.served, 0)
    expect(served).toBeLessThanOrEqual(60)
    for (const f of answer.families) expect(f.served).toBeLessThanOrEqual(10)
    const universe = answer.families.reduce((n, f) => n + f.total_in_family, 0)
    expect(universe).toBeGreaterThan(1000) // the composed evidence universe is genuinely large
    // families with more than served must declare it
    for (const f of answer.families) {
      if (f.total_in_family > f.served) expect(f.more_available).toBe(true)
    }

    // (2) LEDGER RESOLVABILITY (§N.5) — every ledger signal_id resolves in bodha_msr_signals.
    const allSignalIds = Array.from(new Set(answer.derivation_ledger.flatMap(e => e.signal_ids))).filter(Boolean)
    expect(allSignalIds.length).toBeGreaterThan(0)
    const res = await query(
      `SELECT signal_id FROM bodha_msr_signals WHERE chart_id = $1 AND signal_id = ANY($2::uuid[])`,
      [NATIVE, allSignalIds],
    )
    const resolved = new Set(res.rows.map(r => String((r as Record<string, unknown>)['signal_id'])))
    const unresolved = allSignalIds.filter(id => !resolved.has(id))
    expect(unresolved).toEqual([]) // every id resolves — halt-worthy otherwise (§N.5)

    // (3) HONEST DEGRADATION — native chart contradictions=0 disclosed, not fabricated.
    expect(answer.disclosures.some(d => /contradiction/i.test(d))).toBe(true)

    // Plan consulted pre-aggregated surfaces before the atomic drill.
    const stages = answer.plan.map(p => p.stage)
    expect(stages.indexOf('orient')).toBeLessThan(stages.indexOf('map_reduce_families'))

    console.log('[WP-1.4 marriage] served=%d universe=%d families=%d ledger_sigs=%d disclosures=%d',
      served, universe, answer.families.length, allSignalIds.length, answer.disclosures.length)
  }, 60_000)

  it('moksha universe: composes spirituality primary with resolvable ledger', async () => {
    const { composeLargeN } = await import('./instrument')
    const { query } = await import('@/lib/db/client')

    const answer = await composeLargeN({
      chart_id: NATIVE,
      question: 'What does the chart say about moksha, renunciation, and the path to liberation?',
      ayanamsha_id: LAHIRI,
      budget: { total_signal_rows: 50, per_family_cap: 10 },
    })

    expect(answer.contract.primary_domain).toBe('spirituality')
    const served = answer.families.reduce((n, f) => n + f.served, 0)
    expect(served).toBeLessThanOrEqual(50)

    const allSignalIds = Array.from(new Set(answer.derivation_ledger.flatMap(e => e.signal_ids))).filter(Boolean)
    if (allSignalIds.length > 0) {
      const res = await query(
        `SELECT signal_id FROM bodha_msr_signals WHERE chart_id = $1 AND signal_id = ANY($2::uuid[])`,
        [NATIVE, allSignalIds],
      )
      const resolved = new Set(res.rows.map(r => String((r as Record<string, unknown>)['signal_id'])))
      expect(allSignalIds.filter(id => !resolved.has(id))).toEqual([])
    }

    console.log('[WP-1.4 moksha] served=%d families=%d ledger_sigs=%d',
      served, answer.families.length, allSignalIds.length)
  }, 60_000)

  it('capability wrapper: served envelope carries coverage + honest pagination', async () => {
    const { getCapability } = await import('../registry/catalog')
    const cap = getCapability('marsys://tool/synthesis/compose_large_n')
    expect(cap).toBeDefined()
    const res = await cap!.handler(
      { chart_id: NATIVE, question: 'Map the whole marriage universe', ayanamsha_id: LAHIRI, response_format: 'v3' },
      { chart_id: NATIVE },
    )
    expect(res.is_error).toBe(false)
    const env = res.content as Record<string, unknown>
    expect(env['tool']).toBe('compose_large_n')
    const coverage = env['coverage'] as Record<string, unknown> | null
    expect(coverage).not.toBeNull()
    expect(Number(coverage!['total'])).toBeGreaterThanOrEqual(Number(coverage!['served']))
    const pag = env['pagination'] as Record<string, unknown>
    expect(typeof pag['more_available']).toBe('boolean')
  }, 60_000)
})
