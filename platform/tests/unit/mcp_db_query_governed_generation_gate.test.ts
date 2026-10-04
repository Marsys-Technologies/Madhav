/**
 * The governed-generation gate's seal lookup, through the route's REAL validator (Codex rounds 3 and 4 on PR 3110, follow-up (a)).
 *
 * The earlier reader asked `SELECT to_regclass('public.ka_gochara_generation_seal') IS NOT NULL AS present` — no FROM clause, so the
 * proxy rejected it ("Could not identify any referenced table") — and the seal table was not on the allowlist. These tests send the gate's
 * actual SQL to the route's POST handler (the validator is private to the module, so the handler is the only real entry), with the database
 * client and the service token mocked: a query the validator rejects answers 400 and never reaches the database mock.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const queryMock = vi.fn(async () => ({ rows: [{ sealed: true }], rowCount: 1 }))
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => (queryMock as unknown as (...a: unknown[]) => unknown)(...args) }))
vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: () => true }))

import { POST } from '@/app/api/mcp/db/query/route'
import { SEAL_LOOKUP_SQL } from '../../../platform-mcp/src/lib/governed_generation_gate'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function request(sql: string, params: unknown[] = [CHART, '5.0']): Request {
  return new Request('http://localhost/api/mcp/db/query', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-user': 'u', 'x-mcp-key-id': 'k' },
    body: JSON.stringify({ sql, params }),
  })
}

describe('the gate seal lookup through the route validator', () => {
  beforeEach(() => queryMock.mockClear())

  it('the gate\'s own SQL is ACCEPTED and reaches the database with its two parameters', async () => {
    const res = await POST(request(SEAL_LOOKUP_SQL))
    expect(res.status).toBe(200)
    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(queryMock.mock.calls[0]).toEqual([SEAL_LOOKUP_SQL, [CHART, '5.0']])
    expect(((await res.json()) as { rows: unknown[] }).rows).toEqual([{ sealed: true }])
  })

  it('the OLD presence probe (no FROM clause) is rejected — the defect this follow-up fixes', async () => {
    const res = await POST(request("SELECT to_regclass('public.ka_gochara_generation_seal') IS NOT NULL AS present", []))
    expect(res.status).toBe(400)
    expect(JSON.stringify(await res.json())).toMatch(/FROM\/JOIN clause required/)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('the seal table is on the allowlist (the same query is rejected when it names a table that is not)', async () => {
    const other = SEAL_LOOKUP_SQL.replace('ka_gochara_generation_seal', 'ka_gochara_generation_seal_history_not_allowed')
    const res = await POST(request(other))
    expect(res.status).toBe(400)
    expect(JSON.stringify(await res.json())).toMatch(/not in the read-only whitelist/)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('the proxy still refuses writes against the seal table', async () => {
    for (const sql of ['DELETE FROM ka_gochara_generation_seal WHERE chart_id = $1', 'UPDATE ka_gochara_generation_seal SET generation = $2',
                       'SELECT 1 FROM ka_gochara_generation_seal; DROP TABLE ka_gochara_generation_seal']) {
      expect((await POST(request(sql))).status).toBe(400)
    }
    expect(queryMock).not.toHaveBeenCalled()
  })
})
