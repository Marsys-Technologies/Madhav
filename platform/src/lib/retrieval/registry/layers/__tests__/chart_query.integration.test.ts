/**
 * chart_query.integration.test.ts — live-DB conformance + payload-size gate for
 * marsys://tool/L1/chart_facts_query (chart_query lane, R5 W1).
 *
 * Covers:
 *   - NF-1 regression guard: the handler must NOT call the sidecar / 404 (it queries
 *     chart_facts directly now — this test would hang/fail if it ever fetch()'d again
 *     without a running sidecar, since no sidecar is started for this test).
 *   - EAV-crosstab pivot: "pivoted" shape collapses many raw rows into one wide row/subject.
 *   - `about` facet: string alias ("lagna"), {graha}, {bhava}, {house_lord} indirection,
 *     each verified against chart_facts on BOTH the native and Abhinandan charts (W1 gate).
 *   - Facet-conformance: each declared facet demonstrably alters the result (design §19
 *     mandate — "a CI contract test round-trips every declared facet ... and asserts it
 *     altered the result"), scoped to this instrument.
 *   - Gate: a lagna lookup via this tool returns <=2KB in one call.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { registerD7ChannelCapabilities } from '../register_d7_channel'
import { clearRegistry, getCapability } from '../../index'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('chart_query (marsys://tool/L1/chart_facts_query) — live DB', () => {
  beforeAll(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
  })

  function handler() {
    const cap = getCapability('marsys://tool/L1/chart_facts_query')
    if (!cap) throw new Error('capability not registered')
    return cap.handler
  }

  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] lagna lookup via about:"lagna" is ONE call, <=2KB, pivoted, and resolves against chart_facts`, async () => {
      const result = await handler()({ chart_id: chartId, about: 'lagna' })
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      expect(content['shape']).toBe('pivoted')
      const facts = content['facts'] as Array<Record<string, unknown>>
      expect(facts.length).toBe(1)
      expect(facts[0]['fact_subject']).toBe('LAGNA')
      expect(facts[0]['sign']).toBeTruthy()
      expect(facts[0]['sign_lord']).toBeTruthy()
      expect(facts[0]['house_d1']).toBe(1)
      // fact_ids must be real chart_facts.fact_id values (§N.5 — L1 is the authority)
      expect(Object.keys(facts[0]['fact_ids'] as object).length).toBeGreaterThan(0)

      const bytes = Buffer.byteLength(JSON.stringify(content), 'utf8')
      expect(bytes, `lagna payload was ${bytes} bytes`).toBeLessThanOrEqual(2048)
    })

    it(`[${chartId}] about:{house_lord:10} resolves the 10th lord (via the canonical address resolver) and serves a chain grounded in chart_facts`, async () => {
      const result = await handler()({ chart_id: chartId, about: { house_lord: 10 } })
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const resolution = content['about_resolution'] as Record<string, unknown>
      expect(resolution['subjects']).toHaveLength(1)
      // Post-Ring-1-reconciliation (JL-010): `chain` is now the canonical address resolver's
      // human-readable string chain (`ResolvedAddress.chain`), not the retired stopgap
      // resolver's `{step, output}` object chain.
      const chain = resolution['chain'] as string[]
      expect(chain.length).toBeGreaterThanOrEqual(3)
      expect(chain.some(step => /counted from lagna/i.test(step))).toBe(true)
      expect(chain.some(step => /ruled by/i.test(step))).toBe(true)
      expect(chain.some(step => /lord is/i.test(step))).toBe(true)
      const facts = content['facts'] as Array<Record<string, unknown>>
      expect(facts.length).toBe(1)
      expect(facts[0]['fact_subject']).toBe((resolution['subjects'] as string[])[0])
    })

    it(`[${chartId}] about:{graha:"Saturn"} returns exactly Saturn's pivoted position row`, async () => {
      const result = await handler()({ chart_id: chartId, about: { graha: 'Saturn' } })
      const content = result.content as Record<string, unknown>
      const facts = content['facts'] as Array<Record<string, unknown>>
      expect(facts.length).toBe(1)
      expect(facts[0]['fact_subject']).toBe('SAT')
    })

    it(`[${chartId}] shape:"rows" vs default "pivoted" produce different, non-trivial shapes (facet-conformance)`, async () => {
      const pivoted = await handler()({ chart_id: chartId, about: 'lagna', shape: 'pivoted' })
      const rows = await handler()({ chart_id: chartId, about: 'lagna', shape: 'rows' })
      const pivotedContent = pivoted.content as Record<string, unknown>
      const rowsContent = rows.content as Record<string, unknown>
      expect(pivotedContent['shape']).toBe('pivoted')
      expect(rowsContent['shape']).toBe('rows')
      expect((pivotedContent['facts'] as unknown[]).length).toBe(1)
      // Flat rows must be strictly more numerous than the one pivoted row (facet altered the result)
      expect((rowsContent['rows'] as unknown[]).length).toBeGreaterThan(1)
    })

    it(`[${chartId}] planet filter alters the result vs no filter (facet-conformance)`, async () => {
      const unfiltered = await handler()({ chart_id: chartId, category: 'graha_position', limit: 20 })
      const filtered = await handler()({ chart_id: chartId, category: 'graha_position', planet: 'Jupiter', limit: 20 })
      const unfilteredFacts = (unfiltered.content as Record<string, unknown>)['facts'] as unknown[]
      const filteredFacts = (filtered.content as Record<string, unknown>)['facts'] as unknown[]
      expect(filteredFacts.length).toBe(1)
      expect(unfilteredFacts.length).toBeGreaterThan(filteredFacts.length)
    })
  }

  // D-1.5b Gate B (CR-18 / B_shadbala_ratio): graha_shadbala_total rows must carry BOTH the
  // per-ayanamsha `ratio` AND the ayanamsha-INVARIANT `required_rupa` (stored under
  // ayanamsha_id='INVARIANT'). The single-ayanamsha WHERE filter used to drop required_rupa (0/9);
  // the widened `ayanamsha_id IN ($2,'INVARIANT')` clause surfaces it in the same pivoted row.
  it('[native] graha_shadbala_total serves BOTH ratio and required_rupa on the same graha row (Gate B)', async () => {
    const result = await handler()({ chart_id: NATIVE_CHART_ID, category: 'graha_shadbala_total', limit: 20 })
    expect(result.is_error).toBe(false)
    const facts = (result.content as Record<string, unknown>)['facts'] as Array<Record<string, unknown>>
    // The 7 real grahas (Sun..Saturn) all carry required_rupa; nodes (RAH/KET) carry only rupa.
    const withRatio = facts.filter(f => f['ratio'] != null)
    const withRequiredRupa = facts.filter(f => f['required_rupa'] != null)
    expect(withRatio.length).toBeGreaterThanOrEqual(7)
    expect(withRequiredRupa.length).toBeGreaterThanOrEqual(7)
    // Every graha that has a ratio must ALSO carry required_rupa (the Gate B pairing).
    for (const f of withRatio) {
      expect(f['required_rupa'], `${f['fact_subject']} missing required_rupa`).not.toBeNull()
      expect(f['required_rupa']).toBeDefined()
      // required_rupa must ground back to a real chart_facts.fact_id (§N.5).
      expect((f['fact_ids'] as Record<string, string>)['required_rupa']).toBeTruthy()
    }
    // Spot-check SUN's known classical minimum shadbala (5 rupas) and that shape="rows" also serves it.
    const sunPivot = facts.find(f => f['fact_subject'] === 'SUN')
    expect(sunPivot?.['required_rupa']).toBe(5)
    const rowsResult = await handler()({ chart_id: NATIVE_CHART_ID, category: 'graha_shadbala_total', shape: 'rows', limit: 100 })
    const rows = (rowsResult.content as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>
    expect(rows.some(r => r['fact_key'] === 'required_rupa')).toBe(true)
  })

  it('rejects an unrecognized planet name honestly (no silent empty)', async () => {
    const result = await handler()({ chart_id: NATIVE_CHART_ID, planet: 'Pluto' })
    expect(result.is_error).toBe(true)
  })

  it('requires chart_id', async () => {
    const result = await handler()({})
    expect(result.is_error).toBe(true)
  })
})
