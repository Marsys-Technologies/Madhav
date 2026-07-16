/**
 * wealth_conclusions.test.ts — D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 1).
 *
 * Offline coverage of the six §G.0 conclusion assertions' PARSING/classification logic against
 * fixtures shaped like the LIVE response envelopes doctrine_harness/lib/assertions.ts already
 * verified (structuredContent.object unwrapping happens inside McpClient; these fixtures model
 * the post-unwrap `content` shape each assertion actually receives). This is deliberately NOT a
 * substitute for the live run against the deployed connector (only that run can confirm the
 * conclusions are ACTUALLY traceable on 482012f1 today) — it proves the assertion logic itself
 * correctly discriminates a present-and-correct conclusion from an absent/wrong one, per §F1.7's
 * "data over flags" rule applied to the harness's own code.
 */
import { describe, it, expect } from 'vitest'
import { WEALTH_CONCLUSION_ASSERTIONS, runWealthConclusionGate } from '../wealth_conclusions.js'
import type { RunContext } from '../types'
import type { McpClient } from '../mcp_client.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

type ToolMap = Record<string, (args: Record<string, unknown>) => unknown>

function ctxWith(toolMap: ToolMap): RunContext {
  const client = {
    callTool: async (name: string, args: Record<string, unknown>) => {
      const fn = toolMap[name]
      if (!fn) throw new Error(`unmocked tool: ${name}`)
      return { raw: { ok: true, status: 200, body: '' }, content: fn(args), isToolError: false }
    },
  } as unknown as McpClient
  return { client, chartId: CHART_ID, secondChartId: 'other' }
}

// A fixture that satisfies ALL six §G.0 conclusions — the "instrument does the work" case.
function allGreenToolMap(): ToolMap {
  return {
    judgment_query: () => ({
      content: { checklist: { bearing_yogas: [{ name: 'Dhana Yoga', actors: ['Venus', 'Jupiter'], house: 9 }] } },
      verdict: { verdict_grade: 'strong', composite_score: 2.1 },
    }),
    bodha_signals_get: (args) => {
      if (args.signal_type_class === 'varga_ratification_divergence') {
        return { content: { signals: [{ citation_human: 'SATURN: D1 exalted vs D9 debilitated — wealth ratification fails' }] } }
      }
      // wealth top-15 default page
      return {
        content: {
          signals: [
            { signal_type_id: 'bhava_significance_link:lord_aspects', citation_human: 'Mars (8L) aspects house 2 at full strength', valence: 'malefic', valence_source: 'ga_vichara_v1', configuration_jsonb: { target_house: 2 } },
            { signal_type_id: 'varga_ratification_divergence', citation_human: 'SATURN D9 divergence' },
          ],
        },
      }
    },
    ganita_yoga_firings_get: () => ({
      content: {
        rows: [
          {
            fired: true,
            grounds_jsonb: [
              { planet: 'saturn', varga: 'D9', debilitation_sign: 'aries', grounds: [{ fired: true }] },
              { planet: 'venus', varga: 'D9', debilitation_sign: 'virgo', grounds: [{ fired: true }] },
            ],
          },
        ],
      },
    }),
    // Live-verified shape (2026-07-16 probe): weakest_graha sits at content.digest.weakest_graha.
    bodha_chart_digest_get: () => ({ content: { digest: { weakest_graha: 'Venus' } } }),
    ganita_dasha_lord_capability_get: () => ({
      rows: [
        { lord: 'Ketu', warning_tier: 'watch', house_class: 'dusthana', shadbala_percentile: 0.125 },
        { lord: 'Venus', warning_tier: 'watch', shadbala_percentile: 0.25 },
      ],
    }),
  }
}

describe('wealth_conclusions — 6/6 on a fully-served estate', () => {
  it('all six assertions report green when every domain surface serves the conclusion', async () => {
    const ctx = ctxWith(allGreenToolMap())
    const gate = await runWealthConclusionGate(ctx)
    expect(gate.sixOfSix).toBe(true)
    expect(gate.green).toBe(6)
    expect(gate.red).toBe(0)
  })
})

describe('wealth_conclusions — never fabricates green on an absent conclusion', () => {
  it('G0-1 reports red when bearing_yogas has no Dhana Yoga specimen', async () => {
    const toolMap = allGreenToolMap()
    toolMap.judgment_query = () => ({ content: { checklist: { bearing_yogas: [] } }, verdict: {} })
    const ctx = ctxWith(toolMap)
    const def = WEALTH_CONCLUSION_ASSERTIONS.find((a) => a.id === 'G0-1')!
    const result = await def.run(ctx)
    expect(result.status).toBe('red')
  })

  it('G0-4 reports red when the wealth-loss mechanism is served but valence is still neutral (the pre-fix CR-54 shape)', async () => {
    const toolMap = allGreenToolMap()
    toolMap.bodha_signals_get = (args) => {
      if (args.signal_type_class === 'varga_ratification_divergence') return { content: { signals: [] } }
      return {
        content: {
          signals: [
            { signal_type_id: 'bhava_significance_link:lord_aspects', citation_human: 'Mars (8L) aspects house 2', valence: 'neutral', valence_source: 'keyword_heuristic_v1', configuration_jsonb: { target_house: 2 } },
          ],
        },
      }
    }
    const ctx = ctxWith(toolMap)
    const def = WEALTH_CONCLUSION_ASSERTIONS.find((a) => a.id === 'G0-4')!
    const result = await def.run(ctx)
    expect(result.status).toBe('red')
    expect(result.evidence).toContain('valence')
  })

  it('G0-5 reports red when the digest still reports the pre-fix wrong weakest_graha', async () => {
    const toolMap = allGreenToolMap()
    toolMap.bodha_chart_digest_get = () => ({ content: { digest: { weakest_graha: 'Mercury' } } })
    const ctx = ctxWith(toolMap)
    const def = WEALTH_CONCLUSION_ASSERTIONS.find((a) => a.id === 'G0-5')!
    const result = await def.run(ctx)
    expect(result.status).toBe('red')
  })

  it('G0-6 reports red when the Ketu row exists but carries no interpreted warning_tier (bare number only)', async () => {
    const toolMap = allGreenToolMap()
    toolMap.ganita_dasha_lord_capability_get = () => ({ rows: [{ lord: 'Ketu', shadbala_percentile: 0.125 }] })
    const ctx = ctxWith(toolMap)
    const def = WEALTH_CONCLUSION_ASSERTIONS.find((a) => a.id === 'G0-6')!
    const result = await def.run(ctx)
    expect(result.status).toBe('red')
  })

  it('an assertion that throws is reported red by runWealthConclusionGate, never silently dropped', async () => {
    const ctx = ctxWith({}) // every tool call throws "unmocked tool"
    const gate = await runWealthConclusionGate(ctx)
    expect(gate.total).toBe(6)
    expect(gate.red).toBe(6)
    expect(gate.results.every((r) => r.status === 'red')).toBe(true)
  })
})
