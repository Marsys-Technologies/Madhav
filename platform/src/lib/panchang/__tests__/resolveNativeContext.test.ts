import { beforeEach, describe, expect, it, vi } from 'vitest'

const { query } = vi.hoisted(() => ({
  query: vi.fn<(sql: string, params?: unknown[]) => Promise<{ rows: Record<string, unknown>[] }>>(),
}))

vi.mock('@/lib/db/client', () => ({
  query,
  withTransaction: (read: (db: { query: typeof query }) => Promise<unknown>) => read({ query }),
}))

import { resolveNativeContext } from '../resolveNativeContext'

const CHART = '00000000-0000-4000-8000-000000000001'
const PANCHANGA_BUILD = '00000000-0000-4000-8000-000000000002'
const POSITIONS_BUILD = '00000000-0000-4000-8000-000000000003'
const VIEWER = { uid: 'fixture-viewer', role: 'guest' } as const
const FRAME = 'raman'
const UNAVAILABLE = { native_context: null, native_context_error: 'Chart overlay unavailable' }

const GENERATION_SQL = /FROM asset_provenance_receipts/
const FACTS_SQL = /FROM chart_facts/

function receipt(asset_id: string, buildId: string): Record<string, unknown> {
  return {
    chart_id: CHART,
    asset_id,
    partition_key: '__whole_asset__',
    receipt_version: 'fixture-v1',
    receipt_build_id: buildId,
    rows_build_id: buildId,
    receipt_state: 'proven',
    freshness_state: 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64),
    spec_active: true,
    receipt_run_state: 'completed',
    receipt_asset_present: true,
    receipt_asset_state: 'complete',
    receipt_disposition: 'build',
    observed_at: '2026-09-07T02:00:00Z',
  }
}

function facts(ayanamsha_id = FRAME): Record<string, unknown>[] {
  return [
    { build_id: PANCHANGA_BUILD, fact_category: 'panchanga_nakshatra_moon', fact_subject: 'NAKSHATRA_MOON_BIRTH',
      fact_key: 'number', fact_value_num: 3, fact_id: 'fixture-nakshatra-number' },
    { build_id: PANCHANGA_BUILD, fact_category: 'panchanga_nakshatra_moon', fact_subject: 'NAKSHATRA_MOON_BIRTH',
      fact_key: 'name', fact_value_text: 'Krittika', fact_id: 'fixture-nakshatra-name' },
    { build_id: POSITIONS_BUILD, fact_category: 'graha_sign_attributes', fact_subject: 'MOON',
      fact_key: 'sign_num', fact_value_num: 2, fact_id: 'fixture-moon-number' },
    { build_id: POSITIONS_BUILD, fact_category: 'graha_position', fact_subject: 'MOON',
      fact_key: 'sign', fact_value_text: 'Vrishabha', fact_id: 'fixture-moon-name' },
  ].map((row) => ({ chart_id: CHART, ayanamsha_id, fact_value_text: null, fact_value_num: null, ...row }))
}

let storedFrame: string | null
let chartExists: boolean
let grantExists: boolean
let receiptRows: Record<string, unknown>[]
let factRows: Record<string, unknown>[]

beforeEach(() => {
  storedFrame = FRAME
  chartExists = true
  grantExists = true
  receiptRows = [receipt('ga_panchanga', PANCHANGA_BUILD), receipt('ga_positions', POSITIONS_BUILD)]
  factRows = facts()
  query.mockReset()
  query.mockImplementation(async (sql, params) => {
    if (/^SET TRANSACTION /.test(sql)) return { rows: [] }
    expect(params?.[0]).toBe(CHART)
    if (/SELECT owner_id FROM charts/.test(sql)) {
      return { rows: chartExists ? [{ owner_id: 'fixture-owner' }] : [] }
    }
    if (/FROM chart_grants/.test(sql)) {
      expect(params?.[1]).toBe(VIEWER.uid)
      return { rows: chartExists && grantExists ? [{ permission: 'view' }] : [] }
    }
    if (/SELECT id, name, ayanamsa FROM charts/.test(sql)) {
      return { rows: chartExists ? [{ id: CHART, name: 'Fixture chart', ayanamsa: storedFrame }] : [] }
    }
    if (GENERATION_SQL.test(sql)) {
      expect(params).toEqual([CHART, null])
      return { rows: receiptRows }
    }
    if (FACTS_SQL.test(sql)) return { rows: factRows }
    throw new Error('Unexpected fixture query')
  })
})

function factRead() {
  return query.mock.calls.find(([sql]) => FACTS_SQL.test(sql))
}

describe('resolveNativeContext', () => {
  it('reads the unambiguous chart frame and returns only the exact stored values and identities', async () => {
    const result = await resolveNativeContext({ principal: VIEWER, chartId: CHART })
    expect(result).toEqual({
      native_context: {
        chart_id: CHART,
        native_name: 'Fixture chart',
        ayanamsha_id: FRAME,
        birth_nakshatra_id: 3,
        birth_nakshatra_name: 'Krittika',
        moon_sign_id: 2,
        moon_sign_name: 'Vrishabha',
        active_dasha_lord: null,
        fact_ids: {
          birth_nakshatra_id: 'fixture-nakshatra-number',
          birth_nakshatra_name: 'fixture-nakshatra-name',
          moon_sign_id: 'fixture-moon-number',
          moon_sign_name: 'fixture-moon-name',
        },
      },
      native_context_error: null,
    })
    expect(query.mock.calls[0]?.[0]).toContain('REPEATABLE READ READ ONLY')
    const statements = query.mock.calls.map(([sql]) => sql)
    expect(statements.findIndex((sql) => /FROM chart_grants/.test(sql)))
      .toBeLessThan(statements.findIndex((sql) => GENERATION_SQL.test(sql)))
    expect(factRead()?.[1]).toEqual([CHART, FRAME, PANCHANGA_BUILD, POSITIONS_BUILD])
    expect(factRead()?.[0]).toContain('ORDER BY fact_category, fact_subject, fact_key, fact_id')
  })

  it('normalizes an explicitly requested supported frame without falling back to chart settings', async () => {
    storedFrame = 'lahiri,raman'
    factRows = facts('krishnamurti')
    const result = await resolveNativeContext({ principal: VIEWER, chartId: CHART, requestedFrame: ' KP ' })
    expect(result.native_context?.ayanamsha_id).toBe('krishnamurti')
    expect(factRead()?.[1]).toEqual([CHART, 'krishnamurti', PANCHANGA_BUILD, POSITIONS_BUILD])
  })

  it.each([null, '', 'unsupported', 'lahiri,raman'])('refuses omitted requests with stored selection %j', async (selection) => {
    storedFrame = selection
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(factRead()).toBeUndefined()
  })

  it.each([null, ' ', 'all', 'INVARIANT', 'unsupported', 'constructor'])('refuses explicit frame %j', async (requestedFrame) => {
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART, requestedFrame })).resolves.toEqual(UNAVAILABLE)
    expect(factRead()).toBeUndefined()
  })

  it('rechecks a shared grant after a prior success, with no subsequent private read after revocation', async () => {
    expect((await resolveNativeContext({ principal: VIEWER, chartId: CHART })).native_context).not.toBeNull()
    query.mockClear()
    grantExists = false
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(query.mock.calls.map(([sql]) => sql)).toEqual([
      'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY',
      'SELECT owner_id FROM charts WHERE id=$1',
      'SELECT permission FROM chart_grants WHERE chart_id=$1 AND principal_id=$2 LIMIT 1',
    ])
  })

  it('uses the same unavailable shape for an unknown chart', async () => {
    chartExists = false
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(factRead()).toBeUndefined()
  })

  it('refuses an inactive principal without reading chart or fact records', async () => {
    const principal = { ...VIEWER, role: 'inactive' } as const
    await expect(resolveNativeContext({ principal, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(query.mock.calls).toEqual([['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY']])
  })

  it('refuses incomplete receipts and writes no fallback query', async () => {
    receiptRows[0] = { ...receiptRows[0], receipt_run_state: 'running' }
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(factRead()).toBeUndefined()
  })

  it('refuses a producer build withheld because of a failed co-writer', async () => {
    receiptRows[0] = {
      ...receiptRows[0],
      failed_cowriter_attempts: [{ asset_id: 'ga_fixture', run_id: PANCHANGA_BUILD }],
    }
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
    expect(factRead()).toBeUndefined()
  })

  it.each([
    { chart_id: 'another-chart' },
    { ayanamsha_id: 'lahiri_chitrapaksha' },
    { build_id: POSITIONS_BUILD },
    { fact_id: 'fixture-nakshatra-name' },
    { fact_key: 'name' },
    { fact_value_num: 0 },
    { fact_value_num: null },
  ])('refuses mismatched, duplicate or malformed facts %j', async (change) => {
    factRows[0] = { ...factRows[0], ...change }
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
  })

  it('refuses a partial stored fact set', async () => {
    factRows.pop()
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
  })

  it('returns a generic failure when the backing read throws', async () => {
    query.mockRejectedValueOnce(new Error('Fixture detail must not be exposed'))
    await expect(resolveNativeContext({ principal: VIEWER, chartId: CHART })).resolves.toEqual(UNAVAILABLE)
  })
})
