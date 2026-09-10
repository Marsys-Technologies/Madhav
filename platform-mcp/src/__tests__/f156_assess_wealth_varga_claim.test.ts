/**
 * F-156 — assess_wealth's kernel.verdict cited `varga_analysis.per_varga` by name via the
 * `varga_grounding` clause (register_d8_assess_domain.ts), while `varga_analysis` itself lived
 * only in the `evidence` layer, which `assembleSaraContent` (response_budget.ts) drops
 * ALL-OR-NOTHING under budget pressure. Live diagnosis on chart 482012f1-710e-4a25-994a-
 * 93821f5871aa (2026-08-22) measured `composition_report.included_layers: ["kernel"]` /
 * `omitted_sections: ["grounding", "evidence"]` at the default 40KB budget — confirming cause
 * (b), the all-or-nothing size gate (response_budget.ts assembleSaraContent), NOT a
 * `definedFields`/`undefined`-stripping bug. `kernel_bytes` measured 1909B — close to, and
 * almost certainly the origin of, the finding ledger's stale "1839 bytes of a 40KB budget"
 * framing, which measures the kernel alone (ceiling 2048), not the whole assembly.
 *
 * The fix has two halves:
 *   Half 1 (register_d8_assess_domain.ts) — the varga_grounding clause no longer names the
 *   varga_analysis section by path; it cites what it already carries directly (fact_ids).
 *   A claim that names no omittable referent cannot be falsified by trimming.
 *   Half 2 (registry_bridge.ts, §N.6 item 2) — a SLIMMED varga_analysis projection
 *   (consumed_vargas + per-varga dignity summary, no full Ashtakavarga arrays) now rides in
 *   `grounding`, which is greedily included independent of the `evidence` layer's own
 *   all-or-nothing fate. The full object still ships in `evidence` when budget allows.
 *
 * Harness copied from assessment_response_contract.test.ts's pattern.
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _description: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function stubFetch(assessmentPayload: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const { uri, args } = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const payload = uri.startsWith('marsys://tool/L-DOMAIN/assess_')
      ? assessmentPayload
      : { chart_id: args.chart_id, digest: {}, entity_profiles: [] }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: payload, is_error: false } }),
      text: async () => '',
    }
  }))
}

const VARGA_ANALYSIS_FIXTURE = {
  direct_consumption: true,
  consumed_vargas: ['D2', 'D9'],
  fact_ids: ['fact-d2-jup', 'fact-d9-jup', 'fact-d2-moon'],
  per_varga: {
    D2: {
      varga_display: 'Horā (D2)',
      graha_dignity: [
        { graha: 'Jupiter', dignity: 'moolatrikona', sign: 'Sagittarius', house: 9, house_display: '9th', humanized: 'd2_jupiter', fact_id: 'fact-d2-jup' },
        { graha: 'Moon', dignity: 'own_sign', sign: 'Cancer', house: 4, house_display: '4th', humanized: 'd2_moon', fact_id: 'fact-d2-moon' },
      ],
      ashtakavarga_pinda_sarva: null,
      ashtakavarga_available: false,
      empty_reason: 'ashtakavarga_pinda_sarva_per_varga has no D2 rows for this chart.',
    },
    D9: {
      varga_display: 'Navāṃśa (D9)',
      graha_dignity: [
        { graha: 'Jupiter', dignity: 'exalted', sign: 'Cancer', house: 4, house_display: '4th', humanized: 'd9_jupiter', fact_id: 'fact-d9-jup' },
      ],
      ashtakavarga_pinda_sarva: [{ graha: 'Jupiter', pinda_sarva: 32, fact_id: 'fact-d9-av-jup' }],
      ashtakavarga_available: true,
    },
  },
  note: 'Horā (D2) + Navāṃśa (D9) consumed directly from L1 chart_facts.',
}

// The Half-1 corrected clause text (register_d8_assess_domain.ts) — cites fact_ids, not a
// named section.
const VARGA_CLAUSE_TEXT_FIXED =
  "Horā (D2) + Navāṃśa (D9) placements were consumed directly from L1 to confirm this domain's " +
  "operative-varga promise (per-graha dignity and, where computed, per-varga Ashtakavarga " +
  'confirmed from L1 divisional placements — see fact_ids below).'

beforeEach(() => vi.unstubAllGlobals())

describe('F-156 — assess_wealth varga_analysis citation vs. served payload', () => {
  it('the varga_grounding clause source no longer names the varga_analysis section by path (Half 1)', () => {
    // Static regression guard: the pre-fix clause literally embedded the string
    // "varga_analysis.per_varga" in its served verdict text, which rides in the
    // budget-immune kernel even when varga_analysis itself is dropped by the evidence-layer
    // all-or-nothing gate. This must fail on today's (pre-fix) code.
    const here = path.dirname(fileURLToPath(import.meta.url))
    const sourcePath = path.resolve(here, '../../../platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts')
    const source = readFileSync(sourcePath, 'utf8')
    expect(source).not.toContain('varga_analysis.per_varga')
  })

  it('grounding carries a slimmed varga_analysis_summary when varga_analysis data exists and grounding fits (Half 2)', async () => {
    stubFetch({
      chart_id: CHART_ID,
      varga_analysis: VARGA_ANALYSIS_FIXTURE,
      verdict: { clauses: [{ text: VARGA_CLAUSE_TEXT_FIXED, fact_ids: VARGA_ANALYSIS_FIXTURE.fact_ids, grounded: true, clause_id: 'varga_grounding' }] },
    })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const { server, handlers } = makeCapturingServer()
    registerRegistryBridgeTools(server, PRINCIPAL)

    const result = await handlers.get('assess_wealth')!({ chart_id: CHART_ID })
    const object = result.structuredContent!.object as Record<string, unknown>
    const grounding = object.grounding as Record<string, unknown> | undefined
    const composition_report = object.composition_report as Record<string, unknown>

    expect((composition_report.included_layers as string[])).toContain('grounding')
    expect(grounding).toBeDefined()
    const summary = grounding?.varga_analysis_summary as Record<string, unknown> | undefined
    expect(summary).toBeDefined()
    expect(summary?.consumed_vargas).toEqual(['D2', 'D9'])
    const perVargaSummary = summary?.per_varga_summary as Record<string, unknown>
    expect(perVargaSummary.D9).toBeDefined()
    expect((perVargaSummary.D9 as Record<string, unknown>).graha_dignity_summary).toEqual([
      { graha: 'Jupiter', dignity: 'exalted' },
    ])
  })

  it('claim-iff-section-present: grounding evidence for the varga claim survives even when the ' +
    'evidence layer is dropped by an oversized sibling (F-56/F-111 all-or-nothing gate)', async () => {
    // Pad `activating_dasha` (an evidence-only field) well past the 40KB assess_wealth budget
    // so `evidence` is dropped as a whole (F-56/F-111 all-or-nothing gate), while `grounding`
    // — which does not carry activating_dasha — still fits comfortably.
    const oversizedActivatingDasha = { note: 'x'.repeat(60 * 1024) }
    stubFetch({
      chart_id: CHART_ID,
      varga_analysis: VARGA_ANALYSIS_FIXTURE,
      activating_dasha: oversizedActivatingDasha,
      verdict: { clauses: [{ text: VARGA_CLAUSE_TEXT_FIXED, fact_ids: VARGA_ANALYSIS_FIXTURE.fact_ids, grounded: true, clause_id: 'varga_grounding' }] },
    })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const { server, handlers } = makeCapturingServer()
    registerRegistryBridgeTools(server, PRINCIPAL)

    const result = await handlers.get('assess_wealth')!({ chart_id: CHART_ID })
    const object = result.structuredContent!.object as Record<string, unknown>
    const kernel = object.kernel as Record<string, unknown>
    const grounding = object.grounding as Record<string, unknown> | undefined
    const composition_report = object.composition_report as Record<string, unknown>

    // The all-or-nothing gate did fire against evidence (proves the test set up real budget
    // pressure, not a no-op).
    expect((composition_report.omitted_sections as string[])).toContain('evidence')
    // The verdict text (budget-immune kernel) still carries the varga claim...
    expect(String(kernel.verdict)).toContain('operative-varga promise')
    // ...but per Half 1 it no longer names a section by path, so it cannot be falsified by the
    // omission above:
    expect(String(kernel.verdict)).not.toContain('varga_analysis.per_varga')
    // ...and per Half 2, grounding evidence for that claim shipped anyway (this must fail on
    // pre-fix registry_bridge.ts, which never populated grounding.varga_analysis_summary at all
    // regardless of budget pressure).
    expect((composition_report.included_layers as string[])).toContain('grounding')
    const summary = grounding?.varga_analysis_summary as Record<string, unknown> | undefined
    expect(summary).toBeDefined()
    expect(summary?.consumed_vargas).toEqual(['D2', 'D9'])
  })
})
