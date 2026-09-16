import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function dasha(id: string) {
  return {
    dasha_row_id: id,
    system_id: 'vimshottari',
    ayanamsha_id: 'lahiri_chitrapaksha',
    start_date: '2000-01-01',
    start_iso: `2000-01-0${id.charCodeAt(0) - 96}T00:00:00.000Z`,
  }
}

function args(overrides: Record<string, unknown> = {}) {
  return {
    chart_id: CHART_ID,
    limit: 2,
    fields: 'all',
    window_start: '2000-01-01',
    window_end: '2100-01-01',
    ...overrides,
  }
}

function mockBuildPages(state: {
  eligibleBuild: string | null
  replacementInProgress?: boolean
  unrelatedCompletedBuild?: string | null
  rowsByBuild: Record<string, readonly Record<string, unknown>[]>
}) {
  const pageCalls: Array<{ params: readonly unknown[]; sql: string }> = []
  queryMock.mockImplementation((sql: string, params: unknown[] = []) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    if (sql.includes('WITH replacement_fence')) {
      const buildId = state.eligibleBuild
      const offset = Number(params[2])
      const fetchLimit = Number(params[1])
      pageCalls.push({ sql, params })
      return Promise.resolve({ rows: [{
        replacement_in_progress: state.replacementInProgress ?? false,
        eligible_build_id: buildId,
        rows: buildId ? (state.rowsByBuild[buildId] ?? []).slice(offset, offset + fetchLimit) : [],
      }] })
    }
    if (sql.startsWith('SELECT MAX(level_n)')) return Promise.resolve({ rows: [{ max_level: 3 }] })
    throw new Error(`unexpected query: ${sql}`)
  })
  return { pageCalls }
}

const signingEnvironment = {
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1',
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(32, 7).toString('base64url'),
}
const originalSigningEnvironment = {
  currentKid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID,
  current: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT,
  previousKid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID,
  previous: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS,
}

function setSigningEnvironment(overrides: Record<string, string | undefined> = {}) {
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID ?? signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT ?? signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
  if (overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
  else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID = overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
  if (overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
  else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS = overrides.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
}

function tamperCursor(cursor: string, mutate: (payload: Record<string, unknown>) => void): string {
  const [kid, encoded, signature] = cursor.split('.')
  const payload = JSON.parse(Buffer.from(encoded!, 'base64url').toString('utf8')) as Record<string, unknown>
  mutate(payload)
  return `${kid}.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.${signature}`
}

function restoreSigningEnvironment() {
  for (const [name, value] of Object.entries({
    INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: originalSigningEnvironment.currentKid,
    INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: originalSigningEnvironment.current,
    INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: originalSigningEnvironment.previousKid,
    INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: originalSigningEnvironment.previous,
  })) {
    if (value === undefined) delete process.env[name]
    else process.env[name] = value
  }
}

describe('get_dashas build-pinned cursor pagination', () => {
  beforeEach(() => {
    queryMock.mockReset()
    setSigningEnvironment()
  })
  afterEach(restoreSigningEnvironment)

  it('pins first, middle, and final pages to one completed build without duplicate progression', async () => {
    const state = {
      eligibleBuild: 'build-a',
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c'), dasha('d'), dasha('e')] },
    }
    const database = mockBuildPages(state)

    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    const middle = (await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)).content as Record<string, unknown>
    const final = (await getDashasCapability.handler(args({ page_cursor: middle.next_page_cursor }), undefined)).content as Record<string, unknown>
    const served = [first, middle, final].flatMap((content) => (content.rows as Array<Record<string, unknown>>).map((row) => row.dasha_row_id))

    expect(served).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(new Set(served).size).toBe(served.length)
    expect([first.more_available, middle.more_available, final.more_available]).toEqual([true, true, false])
    expect([first.next_offset, middle.next_offset, final.next_offset]).toEqual([2, 4, null])
    expect([first.next_page_cursor, middle.next_page_cursor, final.next_page_cursor]).toEqual([expect.any(String), expect.any(String), null])
    expect(database.pageCalls.map((call) => call.params[2])).toEqual([0, 2, 4])
    expect(database.pageCalls.every((call) => call.sql.includes('asset_provenance_receipts') && call.sql.includes('asset_freshness') && call.sql.includes('eligible_receipt'))).toBe(true)
    expect(database.pageCalls[0]?.params).toEqual(expect.arrayContaining([
      'ga_dashas',
      '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14',
    ]))
  })

  it('marks a first-page empty filter as exhausted only after confirming the active build snapshot', async () => {
    mockBuildPages({ eligibleBuild: 'build-a', rowsByBuild: { 'build-a': [] } })

    const result = await getDashasCapability.handler(args(), undefined)

    expect(result).toMatchObject({
      is_error: false,
      content: { build_id: 'build-a', rows: [], total: 0, more_available: false, next_page_cursor: null },
    })
  })

  it('rejects fractional and huge finite pagination before issuing SQL, while safely flooring usable values', async () => {
    mockBuildPages({ eligibleBuild: 'build-a', rowsByBuild: { 'build-a': [dasha('a')] } })

    for (const invalid of [{ limit: 0.5 }, { limit: Number.POSITIVE_INFINITY }, { offset: 1_000_001 }]) {
      queryMock.mockClear()
      const result = await getDashasCapability.handler(args(invalid), undefined)
      expect(result).toMatchObject({ is_error: true, content: { code: 'invalid_pagination', restart_required: true } })
      expect(queryMock).not.toHaveBeenCalled()
    }

    const result = await getDashasCapability.handler(args({ limit: 3.9, offset: 1.9 }), undefined)
    expect(result).toMatchObject({ is_error: true, content: { code: 'page_cursor_required', restart_required: true } })
    expect(queryMock).not.toHaveBeenCalled()

    const firstPageResult = await getDashasCapability.handler(args({ limit: 3.9 }), undefined)
    expect(firstPageResult.is_error).toBe(false)
    const pageCall = queryMock.mock.calls.find(([sql]) => String(sql).includes('WITH replacement_fence'))!
    expect(pageCall[1]).toEqual(expect.arrayContaining([CHART_ID, 4, 0]))
  })

  it('denies a cursor replay when a query filter changes instead of serving another family', async () => {
    const state = {
      eligibleBuild: 'build-a',
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')] },
    }
    const database = mockBuildPages(state)
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    const result = await getDashasCapability.handler(args({ system: 'yogini', page_cursor: first.next_page_cursor }), undefined)

    expect(result).toMatchObject({ is_error: true, content: { code: 'page_cursor_filter_mismatch', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)
  })

  it('requires restart rather than falsely exhausting after a fresh receipt build switch', async () => {
    const state = {
      eligibleBuild: 'build-a',
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')], 'build-b': [dasha('x')] },
    }
    const database = mockBuildPages(state)
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>

    state.eligibleBuild = 'build-b'
    const rebuilt = await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)
    expect(rebuilt).toMatchObject({ is_error: true, content: { code: 'page_cursor_build_changed', restart_required: true } })
    expect(database.pageCalls).toHaveLength(2)
  })

  it('rejects payload tampering of the signed cursor build, offset, and filter fingerprint before querying', async () => {
    const database = mockBuildPages({ eligibleBuild: 'build-a', rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')] } })
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    const original = first.next_page_cursor as string

    for (const mutate of [
      (payload: Record<string, unknown>) => { payload.offset = 0 },
      (payload: Record<string, unknown>) => { payload.build_id = 'build-b' },
      (payload: Record<string, unknown>) => { payload.filter_fingerprint = 'f'.repeat(64) },
    ]) {
      const result = await getDashasCapability.handler(args({ page_cursor: tamperCursor(original, mutate) }), undefined)
      expect(result).toMatchObject({ is_error: true, content: { code: 'invalid_page_cursor', restart_required: true } })
    }
    const [kid, payload, signature] = original.split('.')
    const alteredSignature = `${kid}.${payload}.${signature![0] === 'A' ? 'B' : 'A'}${signature!.slice(1)}`
    const signatureResult = await getDashasCapability.handler(args({ page_cursor: alteredSignature }), undefined)
    expect(signatureResult).toMatchObject({ is_error: true, content: { code: 'invalid_page_cursor', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)
  })

  it('accepts a cursor signed with the configured previous lifecycle key during key rotation', async () => {
    const state = { eligibleBuild: 'build-a', rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')] } }
    mockBuildPages(state)
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    setSigningEnvironment({
      INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v2',
      INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(32, 9).toString('base64url'),
      INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v1',
      INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT,
    })

    const continued = await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)

    expect(continued).toMatchObject({ is_error: false, content: { rows: [expect.objectContaining({ dasha_row_id: 'c' })] } })
  })

  it('fails visibly without a valid lifecycle signing key rather than emitting a forgeable cursor', async () => {
    mockBuildPages({ eligibleBuild: 'build-a', rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')] } })
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT

    const result = await getDashasCapability.handler(args(), undefined)

    expect(result).toMatchObject({ is_error: true, content: { code: 'page_cursor_signing_unavailable', restart_required: true } })
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('does not select an unrelated completed build without a fresh proven ga_dashas receipt', async () => {
    const database = mockBuildPages({
      eligibleBuild: 'build-a', unrelatedCompletedBuild: 'unrelated-build-z',
      rowsByBuild: { 'build-a': [dasha('a')], 'unrelated-build-z': [dasha('z')] },
    })

    const result = await getDashasCapability.handler(args(), undefined)

    expect(result).toMatchObject({ is_error: false, content: { build_id: 'build-a', rows: [expect.objectContaining({ dasha_row_id: 'a' })] } })
    expect(database.pageCalls[0]?.sql).toContain("receipt.asset_id")
    expect(database.pageCalls[0]?.sql).toContain("receipt.output_digest_spec_sha256")
  })

  it('fences a partial ga_dashas replacement even while an older receipt snapshot remains readable', async () => {
    const database = mockBuildPages({
      eligibleBuild: 'build-a', replacementInProgress: true,
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b')] },
    })

    const result = await getDashasCapability.handler(args(), undefined)

    expect(result).toMatchObject({ is_error: true, content: { code: 'ga_dashas_replacement_in_progress', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)
    expect(database.pageCalls[0]?.sql).toContain('build_run_assets')
    expect(database.pageCalls[0]?.sql).toContain("fenced_run.state IN ('planned', 'running', 'paused')")
  })
})
