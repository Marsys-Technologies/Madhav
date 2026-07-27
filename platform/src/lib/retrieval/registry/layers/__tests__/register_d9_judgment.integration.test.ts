/**
 * register_d9_judgment.integration.test.ts — live-DB gate for
 * marsys://tool/L-JUDGMENT/judgment_query (R5 W3, design §28.1).
 *
 * THE W3 GATE: "how is the marriage?" resolves as ONE judgment_query call with a
 * COMPLETE classical checklist receipt — verified against BOTH canonical charts.
 *
 * Run with: INTEGRATION=true npx vitest run src/lib/retrieval/registry/layers/__tests__/register_d9_judgment.integration.test.ts
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { registerD9JudgmentCapabilities } from '../register_d9_judgment'
import { clearRegistry, getCapability } from '../../index'
import { checkAllCapabilities } from '../../chart_agnostic_gate'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('judgment_query (marsys://tool/L-JUDGMENT/judgment_query) — live DB', () => {
  beforeAll(() => {
    clearRegistry()
    registerD9JudgmentCapabilities()
  })

  function handler() {
    const cap = getCapability('marsys://tool/L-JUDGMENT/judgment_query')
    if (!cap) throw new Error('capability not registered')
    return cap.handler
  }

  it('passes the chart-agnostic gate (per_chart, chart_id required)', () => {
    const cap = getCapability('marsys://tool/L-JUDGMENT/judgment_query')
    expect(cap).toBeTruthy()
    const violations = checkAllCapabilities([cap!])
    expect(violations, violations.map(v => `${v.rule}`).join('\n')).toHaveLength(0)
  })

  it('errors cleanly when neither domain nor bhava is given', async () => {
    const result = await handler()({ chart_id: NATIVE_CHART_ID })
    expect(result.is_error).toBe(true)
  })

  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] "how is the marriage?" — domain:"marriage" resolves as ONE call with a COMPLETE classical checklist receipt`, async () => {
      const result = await handler()({ chart_id: chartId, domain: 'marriage' })
      expect(result.is_error, JSON.stringify(result.content)).toBe(false)
      const content = result.content as Record<string, unknown>

      // ── §27.1 about resolution: bhava 7, Venus karaka, D9 varga (design §28.5 shastra map) ──
      const about = content['about'] as Record<string, unknown>
      expect(about['bhava']).toBe(7)
      expect(about['karakas']).toEqual(['Venus'])
      expect(about['operative_varga']).toBe('D9')

      // ── §28.1 checklist — every named element is PRESENT (not stubbed/partial) ──
      const checklist = content['checklist'] as Record<string, unknown>
      expect(checklist).toBeTruthy()

      const bhavaCondition = checklist['bhava_condition'] as Record<string, unknown>
      const fromLagna = bhavaCondition['from_lagna'] as Record<string, unknown>
      expect(fromLagna['sign']).toBeTruthy()
      expect(fromLagna['house_number']).toBe(7)
      const fromChandra = bhavaCondition['from_chandra'] as Record<string, unknown> | null
      expect(fromChandra, 'Sudarshana from-Moon resolution must be present').toBeTruthy()
      expect(fromChandra!['sign']).toBeTruthy()

      const bhaveshaCondition = checklist['bhavesha_condition'] as Record<string, unknown>
      const lordLagna = bhaveshaCondition['from_lagna'] as Record<string, unknown>
      expect(lordLagna['graha']).toBeTruthy()
      expect(lordLagna['graha_code']).toBeTruthy()
      // dignity_state / shadbala_rupa are best-effort annotations — assert they were attempted
      // (present as keys), not necessarily non-null for every possible chart.
      expect('dignity_state' in lordLagna).toBe(true)
      expect('shadbala_rupa' in lordLagna).toBe(true)

      const karakaCondition = checklist['karaka_condition'] as Record<string, unknown>[]
      expect(karakaCondition.length).toBe(1) // Venus
      expect(karakaCondition[0]!['graha']).toBe('Venus')

      expect(Array.isArray(checklist['occupants'])).toBe(false) // it's an object, not array
      const occupants = checklist['occupants'] as Record<string, unknown>
      expect(Array.isArray(occupants['from_lagna'])).toBe(true)

      expect(Array.isArray(checklist['aspecting_grahas'])).toBe(true)

      const vargaConfirmation = checklist['varga_confirmation'] as Record<string, unknown>
      expect(vargaConfirmation['varga']).toBe('D9')
      expect(Array.isArray(vargaConfirmation['rows'])).toBe(true)

      expect(Array.isArray(checklist['bearing_yogas'])).toBe(true)

      const timingHooks = checklist['timing_hooks'] as Record<string, unknown>
      expect(timingHooks).toBeTruthy()
      expect('mahadasha_windows_by_graha' in timingHooks).toBe(true)

      // ── §28.1 promise-register verdict — deterministic, graded, never null ──
      const verdict = content['verdict'] as Record<string, unknown>
      expect(verdict['verdict_grade']).toBeTruthy()
      expect(typeof verdict['composite_score']).toBe('number')
      expect(verdict['domain']).toBe('marriage')

      // ── §28.6 THE RECEIPT — the completeness contract itself ──
      const receipt = content['receipt'] as Record<string, unknown>
      expect(receipt['bhava']).toBe(true)
      expect(receipt['bhavesha']).toBe(true)
      expect(receipt['karaka']).toBe(true)          // Venus resolved
      expect(receipt['from_moon']).toBe(true)        // Sudarshana leg completed
      expect(typeof receipt['varga_confirmed']).toBe('string')
      expect(typeof receipt['yogas_checked']).toBe('number')
      expect(receipt['bhanga_checked']).toBe(false)  // honest gap (D3 unbuilt) — never fabricated
      expect(receipt['timing_anchored']).toBe(true)

      // ── grounding — real fact_id references back to chart_facts (§N.5) ──
      const factIdRefs = content['fact_id_refs'] as string[]
      expect(factIdRefs.length).toBeGreaterThan(0)

      // ── drill pointers present (astrologically typed, design §28.4) ──
      const drillPointers = content['drill_pointers'] as Record<string, unknown>[]
      expect(drillPointers.length).toBeGreaterThan(0)
    })

    it(`[${chartId}] T5 (PŪRTI): wealth judgment carries the three joined legs + a truthful reading_checklist`, async () => {
      const result = await handler()({ chart_id: chartId, domain: 'wealth' })
      expect(result.is_error, JSON.stringify(result.content)).toBe(false)
      const content = result.content as Record<string, unknown>
      const checklist = content['checklist'] as Record<string, unknown>

      // ── the three computed-but-never-joined legs are now served inline ──
      expect(Array.isArray(checklist['sensitive_degree_firings'])).toBe(true)
      const kp = checklist['kp_cusp_chain'] as Record<string, unknown>
      expect(kp).toBeTruthy()
      expect(Array.isArray(kp['cusps'])).toBe(true)
      // wealth → KP cusps 2 + 11 (MC-031)
      const kpHouses = (kp['cusps'] as Record<string, unknown>[]).map(c => c['house']).sort()
      expect(kpHouses).toEqual([2, 11])
      const gochara = checklist['gochara_sweep'] as Record<string, unknown>
      expect(gochara).toBeTruthy()
      expect('domain_covered' in gochara).toBe(true)

      // ── the reading_checklist receipt is present ──
      const rc = content['reading_checklist'] as Record<string, unknown>
      expect(rc).toBeTruthy()
      const units = rc['units'] as Array<Record<string, unknown>>
      expect(Array.isArray(units)).toBe(true)
      const unitByName = new Map(units.map(u => [u['unit'] as string, u]))
      expect(unitByName.has('sensitive_degree_firings')).toBe(true)
      expect(unitByName.has('kp_cusp_chain')).toBe(true)
      expect(unitByName.has('gochara_sweep')).toBe(true)
      // yogi/avayogi honestly not_joined (T6/MC-029 computed it; this instrument doesn't fold it in yet)
      expect(unitByName.get('yogi_avayogi')!['state']).toBe('not_joined')

      // ── AC3: the reading_checklist is TRUTHFUL — cross-count each leg's claimed state
      //         against what is actually served in content.checklist ──
      const sensState = unitByName.get('sensitive_degree_firings')!['state']
      const sensServed = (checklist['sensitive_degree_firings'] as unknown[]).length
      if (sensState === 'served') expect(sensServed).toBeGreaterThan(0)
      if (sensServed === 0) expect(['empty_for_this_chart', 'not_computed']).toContain(sensState)
      const kpState = unitByName.get('kp_cusp_chain')!['state']
      const kpServed = (kp['cusps'] as unknown[]).length
      if (kpState === 'served') expect(kpServed).toBeGreaterThan(0)
      const gochState = unitByName.get('gochara_sweep')!['state']
      if (gochState === 'served') expect(gochara['domain_covered']).toBe(true)

      // ── non_exhaustive self-disclosure is present and honest ──
      expect('non_exhaustive' in rc).toBe(true)
      if (rc['exhaustive'] === false) expect(rc['non_exhaustive']).toBe('salience_sampled')

      // ── AC1 (native chart only): Mars-in-puṣkara surfaces WITHOUT asking for sensitive degrees ──
      if (chartId === NATIVE_CHART_ID) {
        const firings = checklist['sensitive_degree_firings'] as Array<Record<string, unknown>>
        const marsPushkara = firings.find(
          f => f['check_type'] === 'pushkara' && String(f['graha']).toLowerCase() === 'mars',
        )
        expect(marsPushkara, 'Mars-in-puṣkara must surface in the wealth judgment unprompted (MC-030)').toBeTruthy()
        expect(marsPushkara!['state']).toBe('pushkara')
      }
    })

    it(`[${chartId}] bare bhava (no domain) still runs the full recipe, honestly reporting no karaka`, async () => {
      const result = await handler()({ chart_id: chartId, bhava: 3 })
      expect(result.is_error, JSON.stringify(result.content)).toBe(false)
      const content = result.content as Record<string, unknown>
      const about = content['about'] as Record<string, unknown>
      expect(about['bhava']).toBe(3)
      expect(about['karakas']).toEqual([])
      const receipt = content['receipt'] as Record<string, unknown>
      expect(receipt['bhava']).toBe(true)
      expect(receipt['bhavesha']).toBe(true)
      expect(receipt['karaka']).toBe(false) // honest — no karaka mapped for a bare bhava-3 question
    })

    it(`[${chartId}] career domain resolves bhava 10 / Sun+Mercury+Saturn / D10`, async () => {
      const result = await handler()({ chart_id: chartId, domain: 'career' })
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const about = content['about'] as Record<string, unknown>
      expect(about['bhava']).toBe(10)
      expect(about['karakas']).toEqual(['Sun', 'Mercury', 'Saturn'])
      expect(about['operative_varga']).toBe('D10')
      const karakaCondition = (content['checklist'] as Record<string, unknown>)['karaka_condition'] as unknown[]
      expect(karakaCondition.length).toBe(3)
    })

    it(`[${chartId}] wealth domain: domain-matching bearing_yogas survive the response-budget trim (D-1.5a gate finding)`, async () => {
      // The response-budget trimmer's minKeep cut is a blind slice(0, N) — without sorting
      // domain-matching firings first, a high-strength but domain-irrelevant yoga (e.g.
      // Sasa on career) can rank ahead of a lower-strength domain-matching one (e.g. a
      // Dhana Yoga at ~1.02), silently dropping the exact row the verdict's yoga_term
      // already counted. Caught live post-deploy: composite score moved correctly but
      // the served bearing_yogas array contradicted it.
      const result = await handler()({ chart_id: chartId, domain: 'wealth' })
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const verdict = content['verdict'] as Record<string, unknown>
      const yogaSubscore = verdict['yoga_subscore'] as Record<string, unknown> | undefined
      const domainBearingFirings = (yogaSubscore?.['domain_bearing_firings'] as number) ?? 0
      const bearingYogas = (content['checklist'] as Record<string, unknown>)['bearing_yogas'] as Array<Record<string, unknown>>
      if (domainBearingFirings > 0) {
        // If the verdict counted at least one domain-matching firing, at least one must
        // actually be visible in the served (possibly trimmed) bearing_yogas array —
        // the served data must not contradict the score it's supposed to justify.
        expect(bearingYogas.some(y => y['domain_match'] === true)).toBe(true)
      }
    })
  }
})
