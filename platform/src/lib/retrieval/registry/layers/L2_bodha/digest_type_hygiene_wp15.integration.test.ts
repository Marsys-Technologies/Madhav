/**
 * digest_type_hygiene_wp15.integration.test.ts — WP-1.5 type hygiene (F-0963 class).
 *
 * vw_chart_digest's count columns are bigint — node-postgres serializes bigint as a JS
 * STRING ("573"), so the chart-orientation digest previously shipped string counts a
 * consumer could not do arithmetic on. query_ucd now casts them ::int; this proves the
 * served digest counts are real JSON numbers against the real DB (native chart).
 *
 * Run with: INTEGRATION=true DATABASE_URL=... vitest run \
 *   src/lib/retrieval/registry/layers/L2_bodha/digest_type_hygiene_wp15.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
const D = process.env.INTEGRATION === 'true' ? describe : describe.skip
D('WP-1.5 digest counts are JSON numbers, not bigint strings', () => {
  it('msr_signal_count/yoga_count/dosha_count/contradiction_count are numbers', async () => {
    const { queryUcdCapability } = await import('./query_ucd')
    const h = (queryUcdCapability.handler) as (a: Record<string, unknown>, c?: unknown)=>Promise<{content: Record<string,unknown>}>
    const res = await h({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', ayanamsha_id: 'lahiri_chitrapaksha', response_format: 'digest', top_k_entities: 3 })
    const d = res.content['digest'] as Record<string, unknown> | undefined
    expect(d).toBeTruthy()
    for (const k of ['msr_signal_count','yoga_count','dosha_count','contradiction_count']) {
      if (d![k] != null) expect(typeof d![k], `${k} type`).toBe('number')
    }
  })
})
