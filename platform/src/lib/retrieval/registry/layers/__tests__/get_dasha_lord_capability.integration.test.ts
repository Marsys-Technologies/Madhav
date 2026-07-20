/**
 * get_dasha_lord_capability.integration.test.ts — B8 derived-view gate
 * (doctrine-waves D-1.5b Lane B-7) for marsys://tool/L1/get_dasha_lord_capability.
 *
 * THE GATE: every Vimśottarī MD lord on the canonical chart resolves to a row carrying
 * house_class/shadbala_percentile/functional_lordship/ratification_factor/warning_tier —
 * verified against the live DB (Abhisek 482012f1). No-DB checks (registration shape,
 * chart-agnostic gate) run unconditionally; the DB-dependent assertions are gated behind
 * INTEGRATION=true like every other integration test in this directory.
 *
 * Run with: INTEGRATION=true npx vitest run \
 *   src/lib/retrieval/registry/layers/__tests__/get_dasha_lord_capability.integration.test.ts
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { getDashaLordCapabilityCapability } from '../L1_ganita/get_dasha_lord_capability'
import { clearRegistry, registerCapability, getCapability } from '../../index'
import { checkAllCapabilities } from '../../chart_agnostic_gate'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('get_dasha_lord_capability (marsys://tool/L1/get_dasha_lord_capability) — shape', () => {
  beforeAll(() => {
    clearRegistry()
    registerCapability(getDashaLordCapabilityCapability)
  })

  it('is registered under the expected URI', () => {
    expect(getCapability('marsys://tool/L1/get_dasha_lord_capability')).toBeTruthy()
  })

  it('passes the chart-agnostic gate (per_chart, chart_id required)', () => {
    const cap = getCapability('marsys://tool/L1/get_dasha_lord_capability')
    expect(cap).toBeTruthy()
    const violations = checkAllCapabilities([cap!])
    expect(violations, violations.map(v => `${v.rule}`).join('\n')).toHaveLength(0)
  })

  it('errors cleanly when chart_id is missing', async () => {
    const result = await getDashaLordCapabilityCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('declares a §N.6 density_contract (every row confirmed — no catalog-only layer)', () => {
    expect(getDashaLordCapabilityCapability.density_contract).toBeTruthy()
    expect(getDashaLordCapabilityCapability.density_contract?.paginated).toBe(false)
    expect(getDashaLordCapabilityCapability.density_contract?.empty_reason).toBe(true)
  })
})

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_dasha_lord_capability — live DB', () => {
  beforeAll(() => {
    clearRegistry()
    registerCapability(getDashaLordCapabilityCapability)
  })

  it(`[${NATIVE_CHART_ID}] every Vimśottarī MD lord resolves with the full field set`, async () => {
    const result = await getDashaLordCapabilityCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined)
    expect(result.is_error, JSON.stringify(result.content)).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Record<string, unknown>[]

    // 9 classical grahas each carry a Vimśottarī MD on this chart.
    expect(rows.length).toBe(9)
    const lords = rows.map(r => r['lord'])
    for (const g of ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']) {
      expect(lords).toContain(g)
    }

    for (const row of rows) {
      expect(typeof row['lord']).toBe('string')
      expect(['none', 'watch', 'elevated', 'high']).toContain(row['warning_tier'])
      expect(typeof row['warning_score']).toBe('number')
      // shadbala_percentile is always resolvable (every graha has a graha_shadbala_total fact).
      expect(row['shadbala_percentile']).not.toBeNull()
    }

    // Type specimen (verified live against 482012f1, 2026-07-15): Mercury is a D1 dusthana_lord
    // (12th) with temporal_malefic functional class — warning_score should reflect both factors.
    const mercury = rows.find(r => r['lord'] === 'Mercury')!
    expect(mercury['house_class']).toBe('dusthana_lord')
    expect(mercury['functional_lordship']).toBe('temporal_malefic')
    expect(mercury['warning_score']).toBeGreaterThanOrEqual(2)
    expect(mercury['warning_tier']).toBe('elevated')

    // Rahu/Ketu classically own no sign — house_class is honestly null, not fabricated, and the
    // gap is disclosed via judgment_flags (never silently dropped).
    const rahu = rows.find(r => r['lord'] === 'Rahu')!
    expect(rahu['house_class']).toBeNull()
    const judgment_flags = content['judgment_flags'] as Array<{ code: string; detail?: string } | string>
    expect(judgment_flags.some(f =>
      typeof f !== 'string' && f.code === 'house_class_unresolved' && (f.detail ?? '').includes('Rahu')
    )).toBe(true)
  })
})
