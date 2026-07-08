/**
 * register_d10_pact.integration.test.ts — live-DB gate for
 * marsys://tool/L-PACT/pact_query (R5 W4, design §26/§28.3).
 *
 * THE W4 GATE: a real chart's marriage PACT investigation runs the full chain against LIVE
 * data — either it completes all four stages (citing fact_ids at every stage it reaches) or it
 * halts honestly at a real denied/pending stage. Either outcome is a PASS; what would FAIL the
 * gate is fabricating a later stage after an early one should have stopped it, or crashing.
 *
 * Run with: INTEGRATION=true npx vitest run src/lib/retrieval/registry/layers/__tests__/register_d10_pact.integration.test.ts
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { registerD10PactCapabilities } from '../register_d10_pact'
import { registerD9JudgmentCapabilities } from '../register_d9_judgment'
import { clearRegistry, getCapability } from '../../index'
import { checkAllCapabilities } from '../../chart_agnostic_gate'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

const VALID_PACT_STATUSES = [
  'denied_at_promise', 'denied_at_confirmation', 'denied_at_activation',
  'chain_pending_activation', 'chain_complete',
]
const VALID_STAGE_NAMES = ['PROMISE', 'CONFIRMATION', 'ACTIVATION', 'TRIGGER']

describeIf('pact_query (marsys://tool/L-PACT/pact_query) — live DB', () => {
  beforeAll(() => {
    clearRegistry()
    registerD9JudgmentCapabilities()
    registerD10PactCapabilities()
  })

  function handler() {
    const cap = getCapability('marsys://tool/L-PACT/pact_query')
    if (!cap) throw new Error('capability not registered')
    return cap.handler
  }

  it('passes the chart-agnostic gate (per_chart, chart_id required)', () => {
    const cap = getCapability('marsys://tool/L-PACT/pact_query')
    expect(cap).toBeTruthy()
    const violations = checkAllCapabilities([cap!])
    expect(violations, violations.map(v => `${v.rule}`).join('\n')).toHaveLength(0)
  })

  it('errors cleanly when neither domain nor bhava is given', async () => {
    const result = await handler()({ chart_id: NATIVE_CHART_ID })
    expect(result.is_error).toBe(true)
  })

  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] "will this marriage happen / how does it unfold?" — domain:"marriage" runs the real PACT chain, halting or completing HONESTLY`, async () => {
      const result = await handler()({ chart_id: chartId, domain: 'marriage' })
      expect(result.is_error, JSON.stringify(result.content)).toBe(false)
      const content = result.content as Record<string, unknown>

      const pactStatus = content['pact_status'] as string
      expect(VALID_PACT_STATUSES).toContain(pactStatus)

      const stages = content['stages'] as Array<Record<string, unknown>>
      expect(stages.length).toBeGreaterThanOrEqual(1)
      expect(stages.length).toBeLessThanOrEqual(4)
      for (const s of stages) {
        expect(VALID_STAGE_NAMES).toContain(s['stage'])
        expect(typeof s['status']).toBe('string')
      }

      // Chain-honesty invariant: the stage COUNT must match what pact_status claims.
      // A denial at stage N means exactly N stages ran — never more (no fabricated
      // downstream stages), never fewer (the halt is reported, not silently dropped).
      if (pactStatus === 'denied_at_promise') expect(stages).toHaveLength(1)
      if (pactStatus === 'denied_at_confirmation') expect(stages).toHaveLength(2)
      if (pactStatus === 'denied_at_activation') expect(stages).toHaveLength(3)
      if (pactStatus === 'chain_pending_activation') expect(stages).toHaveLength(4) // ACTIVATION(pending) + TRIGGER(not_yet)
      if (pactStatus === 'chain_complete') expect(stages).toHaveLength(4)

      // The PROMISE stage always cites the same about{} judgment_query itself resolves.
      const about = content['about'] as Record<string, unknown>
      expect(about['bhava']).toBe(7)
      expect(about['operative_varga']).toBe('D9')

      const factIdRefs = content['fact_id_refs'] as string[]
      expect(Array.isArray(factIdRefs)).toBe(true)
      if (pactStatus !== 'denied_at_promise') {
        // once PROMISE passes, judgment_query's own fact_id_refs must be inherited (§19 reuse).
        expect(factIdRefs.length).toBeGreaterThan(0)
      }

      // B.10: TRIGGER never claims an "open"/"closed" gate verdict — only ever an honest
      // gate_data_fetched/unreachable/not_yet status + a documented-gap reason.
      const triggerStage = stages.find(s => s['stage'] === 'TRIGGER')
      if (triggerStage) {
        expect(['gate_data_fetched', 'unreachable', 'not_yet']).toContain(triggerStage['status'])
      }
    })

    it(`[${chartId}] a bare bhava (5th, progeny) also runs the chain without crashing`, async () => {
      const result = await handler()({ chart_id: chartId, bhava: 5 })
      expect(result.is_error, JSON.stringify(result.content)).toBe(false)
      const content = result.content as Record<string, unknown>
      expect(VALID_PACT_STATUSES).toContain(content['pact_status'])
    })
  }
})
