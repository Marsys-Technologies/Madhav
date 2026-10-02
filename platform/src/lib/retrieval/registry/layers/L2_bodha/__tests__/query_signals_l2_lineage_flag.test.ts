/**
 * query_signals — N-91 L2 lineage flag, MERGED into judgment_flags (never overwriting).
 *
 * query_signals already returned `judgment_flags` conditionally (the ayurdaya disclosure) by
 * assignment; the lineage flag must be merged beside it, in content (what the MCP bridge reads)
 * and on the top-level result. REAL detector over a SQL-routed `query` mock.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const BASE = 'base_only_haranas_deferred_to_w3'

type Lineage = 'stale' | 'current' | 'error'
let LINEAGE: Lineage = 'current'
let ROWS: Record<string, unknown>[] = []

const sigRow = (id: string, typeId: string, cfg: Record<string, unknown>): Record<string, unknown> => ({
  signal_id: id, signal_type_id: typeId, signal_type_class: 'composite_state', signal_tradition: 'parashari',
  signal_summary_text: 'x', signal_headline_text: `h ${id}`,
  computed_salience: 0.46, top_k_salience_rank: 1, domains_affected_array: ['career'],
  constituent_facts_array: ['F-1'], source_subsystem: 'structural', valence: 'neutral', verification_pass_status: 'pass',
  citation_human: 'x', lel_origin: false, signature_tier: 'minor', configuration_jsonb: cfg,
})
const ayurdayaTotal = () => sigRow('s-total', 'ayurdaya:total_years', { fact_key: 'total_years', method: 'pindayu', harana_status: BASE })
const plain = () => sigRow('s-plain', 'yoga:gajakesari', {})

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('asset_output_digest_specs') && sql.includes('l1_pins')) {
      if (LINEAGE === 'error') throw new Error('permission denied for table asset_provenance_receipts')
      return {
        rows: [
          { asset_id: 'ga_structural', chart_id: CHART, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-10-04T10:00:00Z'), output_digest: LINEAGE === 'stale' ? 'NEW' : 'PINNED', spec_active: true, registry_current: true, l1_pins: null },
          { asset_id: 'bo_laksana', chart_id: CHART, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-09-08T18:22:33Z'), output_digest: 'l2', spec_active: true, registry_current: true,
            l1_pins: [{ asset_id: 'ga_structural', output_digest: 'PINNED', observed_at: '2026-09-07T08:37:20Z' }] },
        ],
      }
    }
    if (sql.includes('COUNT(*)')) return { rows: [{ total: String(ROWS.length) }] }
    if (sql.includes('FROM bodha_msr_signals')) return { rows: ROWS }
    return { rows: [] }
  }),
}))

import { querySignalsCapability } from '../query_signals'

type Resp = { content: Record<string, unknown>; is_error: boolean; judgment_flags?: Array<Record<string, unknown>> }
let seq = 5000
async function serve(lineage: Lineage, rows: Record<string, unknown>[]): Promise<Resp> {
  LINEAGE = lineage
  ROWS = rows
  // distinct top_k per call -> distinct memo key (query_signals memoises for 60 s)
  return await querySignalsCapability.handler({ chart_id: CHART, top_k: seq++ }, {}) as Resp
}
const codes = (flags: Array<Record<string, unknown>> | undefined) => (flags ?? []).map(f => f['code'])

beforeEach(() => { ROWS = []; LINEAGE = 'current' })

describe('query_signals — l2 lineage flag', () => {
  it('stale pin, no other flag: judgment_flags = [l2_receipts_predate_l1], in content AND on the result', async () => {
    const r = await serve('stale', [plain()])
    expect(r.is_error).toBe(false)
    expect(codes(r.judgment_flags)).toEqual(['l2_receipts_predate_l1'])
    expect(codes(r.content['judgment_flags'] as Array<Record<string, unknown>>)).toEqual(['l2_receipts_predate_l1'])
  })

  it('stale pin AND an ayurdaya page: BOTH flags survive (merged, ayurdaya first) — the lineage flag does not overwrite the ayurdaya one', async () => {
    const r = await serve('stale', [ayurdayaTotal()])
    expect(codes(r.judgment_flags)).toEqual(['ayurdaya_unreduced_base_figures', 'l2_receipts_predate_l1'])
    expect(codes(r.content['judgment_flags'] as Array<Record<string, unknown>>)).toEqual(['ayurdaya_unreduced_base_figures', 'l2_receipts_predate_l1'])
    expect(r.content['ayurdaya_figure_disclosure']).toBeDefined()
  })

  it('current pin: unchanged — no flag on a plain page, only the ayurdaya flag on an ayurdaya page', async () => {
    const plainPage = await serve('current', [plain()])
    expect(plainPage.judgment_flags).toBeUndefined()
    expect(plainPage.content['judgment_flags']).toBeUndefined()
    const ayuPage = await serve('current', [ayurdayaTotal()])
    expect(codes(ayuPage.judgment_flags)).toEqual(['ayurdaya_unreduced_base_figures'])
  })

  it('detector error: fail closed — l2_lineage_check_failed served; signals still served', async () => {
    const r = await serve('error', [plain()])
    expect(r.is_error).toBe(false)
    expect(codes(r.judgment_flags)).toEqual(['l2_lineage_check_failed'])
    expect((r.content['signals'] as unknown[]).length).toBe(1)
  })
})
