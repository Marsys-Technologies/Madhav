/**
 * wp12a_grounding.integration.test.ts — WP-1.2 (a)/(d)/(e) live-DB gate on both canonical charts.
 *
 * Proves against the live corpus:
 *   (a) query_ucd surfaces a non-empty content.grounding.fact_ids, EVERY id resolves to
 *       chart_facts.fact_id (§N.5), and UNATTRIBUTED is not the top entity_profile.
 *   (d) no served orientation top_signal carries major/chart_defining while being
 *       descriptive/per-varga.
 *   (e) get_domain_reading signal_refs carry headline text (not bare IDs; LCA-18c).
 *
 * Run with: INTEGRATION=true npx vitest run src/lib/retrieval/registry/layers/L2_bodha/__tests__/wp12a_grounding.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { queryUcdCapability } from '../query_ucd'
import { queryDomainReadingCapability } from '../query_domain_reading'
import { query } from '@/lib/db/client'
import { isDescriptiveOrPerVarga } from '../../../../ranking/salience_demotion'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('WP-1.2 (a)/(d)/(e) — live grounding, attribution, demotion, hydration', () => {
  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] (a) grounding.fact_ids non-empty and ALL resolve to chart_facts (§N.5)`, async () => {
      const res = await queryUcdCapability.handler({ chart_id: chartId, top_k_signals: 20 }, undefined)
      expect(res.is_error).toBe(false)
      const content = res.content as Record<string, unknown>
      const grounding = content['grounding'] as Record<string, unknown>
      const factIds = grounding['fact_ids'] as string[]
      expect(Array.isArray(factIds)).toBe(true)
      expect(factIds.length).toBeGreaterThan(0)
      // Every surfaced fact_id must exist in chart_facts.
      const check = await query<{ fact_id: string }>(
        `SELECT fact_id FROM chart_facts WHERE chart_id = $1 AND fact_id = ANY($2::text[])`,
        [chartId, factIds],
      )
      const resolved = new Set(check.rows.map(r => r.fact_id))
      for (const fid of factIds) expect(resolved.has(fid)).toBe(true)
    })

    it(`[${chartId}] (a) UNATTRIBUTED is not the top entity_profile`, async () => {
      const res = await queryUcdCapability.handler({ chart_id: chartId, top_k_entities: 10 }, undefined)
      const content = res.content as Record<string, unknown>
      const profiles = content['entity_profiles'] as Array<Record<string, unknown>>
      expect(profiles.length).toBeGreaterThan(0)
      expect(profiles[0]['entity']).not.toBe('UNATTRIBUTED')
      expect(profiles[0]['entity_type']).not.toBe('unattributed')
    })

    it(`[${chartId}] (d) no descriptive/per-varga top_signal is served at major/chart_defining`, async () => {
      const res = await queryUcdCapability.handler({ chart_id: chartId, top_k_signals: 100, response_format: 'full' }, undefined)
      const content = res.content as Record<string, unknown>
      const signals = (content['top_signals'] as Array<Record<string, unknown>>) ?? []
      for (const s of signals) {
        if (isDescriptiveOrPerVarga(s)) {
          expect(['major', 'chart_defining']).not.toContain(s['signature_tier'])
        }
      }
    })

    it(`[${chartId}] (e) get_domain_reading signal_refs carry headline text`, async () => {
      const res = await queryDomainReadingCapability.handler({ chart_id: chartId, domain: 'career' }, undefined)
      expect(res.is_error).toBe(false)
      const content = res.content as Record<string, unknown>
      const refs = (content['signal_refs'] as Array<Record<string, unknown>>) ?? []
      if (refs.length > 0) {
        const withText = refs.filter(r => typeof r['headline'] === 'string' && (r['headline'] as string).length > 0)
        expect(withText.length).toBeGreaterThan(0)
      }
    })
  }
})
