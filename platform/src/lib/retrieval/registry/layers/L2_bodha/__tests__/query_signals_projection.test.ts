/**
 * query_signals (msr_sql) — the PROJECTION facet: WP-1.3(g) / LCA-7
 * =================================================================
 * msr_sql served a FIXED 17-of-82-column projection regardless of request. This
 * facet lets a caller pick which bodha_msr_signals columns are served, validated
 * against a static whitelist of real column names (NO arbitrary SQL — injection-safe),
 * and makes the FULL column set reachable via projection: ['*'].
 *
 * DB is mocked — no live connection required.
 */

import { beforeEach, describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'
const BUILD_A = '11111111-1111-4111-8111-111111111111'
const BUILD_B = '22222222-2222-4222-8222-222222222222'

// A representative row carrying every column the internal pipeline + a few extras touch.
const FAKE_ROW = {
  signal_id: 'sig-1', signal_type_id: 't1', signal_type_class: 'yoga',
  signal_tradition: 'parashari', signal_summary_text: 's', signal_headline_text: 'h',
  computed_salience: 0.9, top_k_salience_rank: 1, domains_affected_array: ['career'],
  constituent_facts_array: ['F-1'], source_subsystem: 'parashara', valence: 'positive',
  verification_pass_status: 'pass', citation_human: 'BPHS', lel_origin: false,
  signature_tier: 'major', configuration_jsonb: {},
  // extra columns beyond the default 17:
  orb_tightness: 0.5, dignity_score: 0.7, shadbala_norm: 0.6, epistemic_tier: 'A',
}

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '5' }] }
    if (sql.includes('FROM bodha_msr_signals')) return { rows: [FAKE_ROW] }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { querySignalsCapability } from '../query_signals'
import { __clearRetrievalCache, cacheGet, cacheKey, cacheSet } from '../../../../cache'
import { applyCompositeRanking } from '../../../../ranking/composite_ranker'
import { PRIORS_VERSION } from '../../../../ranking/priors_config'

vi.mock('../../../../ranking/composite_ranker', () => ({
  applyCompositeRanking: vi.fn(),
  buildRankingBasis: () => ({ mode: 'synthetic-ranked' }),
}))
vi.mock('../../../../ranking/l1_context_fetcher', () => ({ fetchL1Context: async () => ({}) }))

/** Extract the served signal object from a handler response. */
function servedSignal(result: Awaited<ReturnType<typeof querySignalsCapability.handler>>) {
  const content = result.content as Record<string, unknown>
  const signals = content.signals as Record<string, unknown>[]
  return signals[0]
}

describe('query_signals — projection facet (WP-1.3(g) / LCA-7)', () => {
  it('default (no projection): serves the legacy 17-column set, unchanged', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    // legacy columns present
    expect(sig).toHaveProperty('signal_id')
    expect(sig).toHaveProperty('computed_salience')
    // columns OUTSIDE the default 17 are NOT served by default
    expect(sig).not.toHaveProperty('orb_tightness')
    expect(sig).not.toHaveProperty('dignity_score')
  })

  it('projection: [subset] serves ONLY the requested columns (plus the always-served verification tier)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'valence', 'orb_tightness', 'dignity_score'] }, {},
    )
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    // SS N-212 (M2): the row's verification tier is part of EVERY served row, whatever the projection
    expect(Object.keys(sig).sort()).toEqual(['dignity_score', 'orb_tightness', 'signal_id', 'valence', 'verification_pass_status'])
  })

  it("projection: ['*'] makes the full column set reachable", async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A, projection: ['*'] }, {})
    expect(result.is_error).toBe(false)
    const sig = servedSignal(result)
    // columns beyond the default 17 are now reachable
    expect(sig).toHaveProperty('orb_tightness')
    expect(sig).toHaveProperty('epistemic_tier')
    expect(sig).toHaveProperty('shadbala_norm')
    const content = result.content as Record<string, unknown>
    const prov = content.provenance as Record<string, unknown>
    expect(prov).toHaveProperty('projection_note')
  })

  it('rejects an unknown/injected column WITHOUT touching the DB (injection-safe)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'valence; DROP TABLE bodha_msr_signals'] }, {},
    )
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>).error)).toMatch(/[Uu]nknown|not a projectable/)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it('rejects a plausible-but-nonexistent column name (whitelist, not just syntax)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_id', 'made_up_column'] }, {},
    )
    expect(result.is_error).toBe(true)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it('SELECT always fetches internal-required columns even when the caller projects a narrow set', async () => {
    // Composite ranking / demotion / freshness depend on computed_salience etc.;
    // narrowing the SERVED projection must not starve the internal pipeline.
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_A, projection: ['signal_headline_text'] }, {},
    )
    expect(result.is_error).toBe(false)
    const signalSelect = vi.mocked(mockQuery).mock.calls
      .map(c => String(c[0]))
      .find(s => s.includes('FROM bodha_msr_signals') && !s.includes('COUNT(*)'))!
    expect(signalSelect).toContain('computed_salience')
    expect(signalSelect).toContain('signal_headline_text')
    // served row is projected down to the requested single column
    expect(Object.keys(servedSignal(result)).sort()).toEqual(['signal_headline_text', 'verification_pass_status'])      // SS N-212 M2: the tier is always served
  })

  it('fences page/count SQL and partitions the response cache by build_id', async () => {
    vi.mocked(mockQuery).mockClear()

    await querySignalsCapability.handler({ chart_id: CHART_A, build_id: BUILD_A, projection: ['signal_id'] }, {})
    await querySignalsCapability.handler({ chart_id: CHART_A, build_id: BUILD_B, projection: ['signal_id'] }, {})

    const buildScopedCalls = vi.mocked(mockQuery).mock.calls.filter(([sql]) =>
      String(sql).includes('FROM bodha_msr_signals m'),
    )
    const pageCalls = buildScopedCalls.filter(([sql]) =>
      String(sql).includes('ORDER BY m.computed_salience DESC NULLS LAST'),
    )
    expect(pageCalls).toHaveLength(2) // a cache key without build_id would have returned the second call from BUILD_A
    for (const [sql, params] of buildScopedCalls) {
      expect(String(sql)).toMatch(/m\.build_id = ANY\(\$\d+::uuid\[\]\)/)
      expect(params).toEqual(expect.arrayContaining([[expect.stringMatching(/^([12])\1{7}-/)]]))
    }
    expect((pageCalls[0]?.[1] as unknown[])).toContainEqual([BUILD_A])
    expect((pageCalls[1]?.[1] as unknown[])).toContainEqual([BUILD_B])
  })
})

const DISCLOSURE_CHART = '11111111-2222-4333-8444-555555555555'
const DISCLOSURE_BUILD = '66666666-7777-4888-8999-000000000000'
const NARROW_PROJECTION = ['signal_id', 'valence']
const DISCLOSURE_ROW = {
  ...FAKE_ROW,
  signal_id: 'synthetic-target',
  signal_type_id: 'graha_position:longitude_sidereal',
  signal_type_class: 'graha_position',
  valence: 'neutral',
  configuration_jsonb: { fact_key: 'longitude_sidereal', fact_value_num: 42.125 },
  constituent_facts_array: ['synthetic-fact'],
  verification_pass_status: 'two_pass_verified',
  verification_method: 'L1_fact_projection',
  producer_asset_id: 'bo_laksana',
}
const EXPECTED_DISCLOSURE = {
  row_index: 0,
  verification_method: 'L1_fact_projection',
  inherited_l1_verification_pass_status: 'two_pass_verified',
  l2_verification_pass_status: null,
}

function mockDisclosureRows(rows: Record<string, unknown>[]) {
  const result = (selected: Record<string, unknown>[]) => ({
    rows: selected, command: 'SELECT', rowCount: selected.length, oid: 0, fields: [],
  })
  vi.mocked(mockQuery).mockImplementation(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return result([{ total: String(rows.length) }])
    if (!sql.includes('FROM bodha_msr_signals m')) return result([])
    if (sql.includes('m.signal_type_class = ANY(')) return result([]) // synthetic pool B
    // Return only the fields named in the SELECT, including aliases. This catches a
    // missing private input instead of making unselected fields magically available.
    const select = sql.split('FROM bodha_msr_signals m')[0]
    const columns = [...select.matchAll(/\bm\.(\w+)(?: AS (\w+))?/g)]
    return result(rows.map(row => Object.fromEntries(columns.map(([, column, alias]) =>
      [alias ?? column, row[column]],
    ))))
  })
}

function sizedDisclosureRow(legacyBytes: number) {
  const legacyRow: Record<string, unknown> = { ...DISCLOSURE_ROW }
  for (const field of ['producer_asset_id', 'verification_method', 'orb_tightness', 'dignity_score', 'shadbala_norm', 'epistemic_tier']) {
    delete legacyRow[field]
  }
  const emptyPaddingBytes = Buffer.byteLength(JSON.stringify([legacyRow]), 'utf8')
  return {
    ...DISCLOSURE_ROW,
    signal_summary_text: DISCLOSURE_ROW.signal_summary_text + 'x'.repeat(legacyBytes - emptyPaddingBytes),
  }
}

function signalSelects() {
  return vi.mocked(mockQuery).mock.calls.map(([sql]) => String(sql))
    .filter(sql => sql.includes('SELECT m.verification_pass_status,'))
}

async function queryDisclosure(args: Record<string, unknown> = {}) {
  const result = await querySignalsCapability.handler({ chart_id: DISCLOSURE_CHART, ...args }, {})
  expect(result.is_error).toBe(false)
  return result.content as {
    signals: Record<string, unknown>[]
    provenance: Record<string, unknown>
    returned_count: number
    total_matching_filters: number
    truncated: boolean
    truncated_from?: number
  }
}

describe('query_signals — inherited L1 verification disclosure', () => {
  beforeEach(() => {
    __clearRetrievalCache()
    vi.mocked(mockQuery).mockClear()
    mockDisclosureRows([DISCLOSURE_ROW])
  })

  it('keeps the legacy default row and adds the exact inherited-status disclosure', async () => {
    const content = await queryDisclosure()
    expect(content.signals[0]).toEqual({
      signal_id: 'synthetic-target',
      signal_type_id: 'graha_position:longitude_sidereal',
      signal_type_class: 'graha_position',
      signal_tradition: 'parashari',
      signal_summary_text: 's',
      signal_headline_text: 'h',
      computed_salience: 0.9,
      top_k_salience_rank: 1,
      domains_affected_array: ['career'],
      constituent_facts_array: ['synthetic-fact'],
      source_subsystem: 'parashara',
      valence: 'neutral',
      verification_pass_status: 'two_pass_verified',
      citation_human: 'BPHS',
      lel_origin: false,
      signature_tier: 'major',
      configuration_jsonb: { fact_key: 'longitude_sidereal', fact_value_num: 42.125 },
    })
    expect(content.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    expect(content.provenance.tables).toEqual(['bodha_msr_signals'])
    expect(signalSelects()).toHaveLength(1)
    expect(signalSelects()[0]).toContain('m.producer_asset_id AS _signal_verification_producer_asset_id')
    expect(signalSelects()[0]).toContain('m.verification_method AS _signal_verification_method')
    expect(signalSelects()[0].match(/m\.verification_pass_status/g)).toHaveLength(1)
  })

  it('keeps narrow keys exact and public verification_method available without private fields', async () => {
    const narrow = await queryDisclosure({ projection: NARROW_PROJECTION })
    expect(narrow.signals).toEqual([{
      signal_id: 'synthetic-target',
      valence: 'neutral',
      verification_pass_status: 'two_pass_verified',
    }])
    expect(narrow.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    const method = await queryDisclosure({ projection: ['verification_method'] })
    expect(method.signals).toEqual([{
      verification_method: 'L1_fact_projection',
      verification_pass_status: 'two_pass_verified',
    }])
    expect(method.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    const all = await queryDisclosure({ projection: ['*'] })
    expect(all.signals[0].verification_method).toBe('L1_fact_projection')
    expect(all.signals[0].verification_pass_status).toBe('two_pass_verified')
    expect(all.signals[0]).not.toHaveProperty('producer_asset_id')
    expect(Object.keys(all.signals[0]).filter(key => key.startsWith('_signal_verification_'))).toEqual([])
    expect(all.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
  })

  it('uses the final ranked page index, with no companion for off-page or wrong-producer rows', async () => {
    mockDisclosureRows([
      { ...DISCLOSURE_ROW, signal_id: 'synthetic-tail' },
      DISCLOSURE_ROW,
      { ...DISCLOSURE_ROW, signal_id: 'synthetic-control', producer_asset_id: 'bo_arudha' },
    ])
    vi.mocked(applyCompositeRanking).mockImplementation(rows =>
      [...rows].reverse() as ReturnType<typeof applyCompositeRanking>,
    )
    const first = await queryDisclosure({ domain: 'career', top_k: 2, projection: NARROW_PROJECTION })
    expect(first.signals.map(row => row.signal_id)).toEqual(['synthetic-control', 'synthetic-target'])
    expect(first.provenance.signal_verification).toEqual([{ ...EXPECTED_DISCLOSURE, row_index: 1 }])
    const second = await queryDisclosure({ domain: 'career', offset: 1, top_k: 1, projection: NARROW_PROJECTION })
    expect(second.signals.map(row => row.signal_id)).toEqual(['synthetic-target'])
    expect(second.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
  })

  it.each([
    { producer_asset_id: 'bo_arudha' },
    { signal_type_id: 'graha_position:sign' },
    { verification_method: 'synthetic-other-method' },
    { verification_pass_status: 'single_pass' },
    { verification_method: null },
    { producer_asset_id: undefined },
  ])('keeps unqualified rows and omits the companion for %j', async (mismatch) => {
    const row = { ...DISCLOSURE_ROW, ...mismatch }
    mockDisclosureRows([row])
    const content = await queryDisclosure({ projection: NARROW_PROJECTION })
    expect(content.signals).toEqual([{
      signal_id: row.signal_id,
      valence: row.valence,
      verification_pass_status: row.verification_pass_status,
    }])
    expect(content.provenance).not.toHaveProperty('signal_verification')
  })

  it('keeps an empty page free of disclosure', async () => {
    mockDisclosureRows([])
    const content = await queryDisclosure()
    expect(content.signals).toEqual([])
    expect(content.returned_count).toBe(0)
    expect(content.provenance).not.toHaveProperty('signal_verification')
  })

  it('retains the row and its companion at the exact H-12 boundary', async () => {
    const companionBytes = Buffer.byteLength(JSON.stringify({ signal_verification: [EXPECTED_DISCLOSURE] }), 'utf8') - 1
    mockDisclosureRows([sizedDisclosureRow(1_500_000 - companionBytes)])
    const content = await queryDisclosure()
    expect(content.signals.map(row => row.signal_id)).toEqual(['synthetic-target'])
    expect(content.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    expect(content.truncated).toBe(false)
  })

  it('counts companion bytes at H-12 and removes the disclosure when the row is clipped', async () => {
    mockDisclosureRows([sizedDisclosureRow(1_500_000)])
    const content = await queryDisclosure()
    expect(content.signals).toEqual([])
    expect(content).toMatchObject({ returned_count: 0, total_matching_filters: 1, truncated: true, truncated_from: 1 })
    expect(content.provenance).not.toHaveProperty('signal_verification')
  })

  it('bounds the actual H-12 prefix when an oversized first row defeats the uniform estimate', async () => {
    mockDisclosureRows([sizedDisclosureRow(1_500_001), { ...DISCLOSURE_ROW, signal_id: 'synthetic-tail' }])
    const content = await queryDisclosure()
    expect(content.signals).toEqual([])
    expect(content).toMatchObject({ returned_count: 0, total_matching_filters: 2, truncated: true, truncated_from: 2 })
    expect(content.provenance).not.toHaveProperty('signal_verification')
  })

  it('bypasses the exact legacy key, then serves the same versioned narrow response from cache', async () => {
    const previousKeyArgs = {
      chart_id: DISCLOSURE_CHART,
      ayanamsha_id: 'lahiri_chitrapaksha',
      build_id: DISCLOSURE_BUILD,
      frame: 'lagna',
      projection: NARROW_PROJECTION,
      priors_version: PRIORS_VERSION,
    }
    const oldKey = cacheKey('query_signals', previousKeyArgs)
    const legacy = { content: { signals: [{ signal_id: 'synthetic-stale' }], provenance: {} }, is_error: false }
    cacheSet(oldKey, legacy)
    const args = { build_id: DISCLOSURE_BUILD, projection: NARROW_PROJECTION }
    const first = await queryDisclosure(args)
    expect(first.signals.map(row => row.signal_id)).toEqual(['synthetic-target'])
    expect(first.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    expect(signalSelects()).toHaveLength(1)
    expect(await queryDisclosure(args)).toEqual(first)
    expect(signalSelects()).toHaveLength(1)
    expect(cacheGet(oldKey)).toEqual(legacy)
    const versioned = cacheKey('query_signals', { ...previousKeyArgs, signal_verification_contract_version: 1 })
    expect(cacheGet(versioned)).toEqual({ content: first, is_error: false })
    const defaultPage = await queryDisclosure({ build_id: DISCLOSURE_BUILD })
    expect(defaultPage.signals[0]).toHaveProperty('configuration_jsonb')
    expect(defaultPage.provenance.signal_verification).toEqual([EXPECTED_DISCLOSURE])
    expect(signalSelects()).toHaveLength(2)
  })
})
