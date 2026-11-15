import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import * as path from 'path'

const m = vi.hoisted(() => ({ user: vi.fn(), query: vi.fn(), exists: vi.fn(), append: vi.fn(), fetch: vi.fn() }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: m.user }))
vi.mock('@/lib/db/client', () => ({ query: m.query }))
vi.mock('fs', () => ({ existsSync: m.exists, appendFileSync: m.append }))
import { POST } from '../route'
import { appendNativeLifeEvent } from '@/lib/mimamsa/nativeLifeEventAppend'

const native = '482012f1-710e-4a25-994a-93821f5871aa'
const other = '00000000-0000-4000-8000-000000000001'
const body = { action: 'lel_entry', event_id: 'EVT.SYNTHETIC.001', category: 'career',
  subcategory: 'fictional', magnitude: 'major', date: '2026-01-01', notes: 'Synthetic "quoted" note' }
function request(id = native, payload: unknown = body) {
  return POST(new NextRequest(`http://localhost/api/clients/${id}/learning`, {
    method: 'POST', body: JSON.stringify(payload), headers: { 'Content-Type': 'application/json' },
  }), { params: Promise.resolve({ id }) })
}
function actor({ role = 'guest', owner = true, admitted = true } = {}) {
  m.query.mockImplementation(async (sql: string, params: unknown[]) => {
    if (sql.includes('LEFT JOIN chart_grants')) return { rows: admitted ? [{ id: params[0] }] : [] }
    if (sql.includes('FROM profiles')) return { rows: [{ role }] }
    if (sql.includes('SELECT owner_id')) return { rows: [{ owner_id: owner ? 'synthetic-owner' : 'someone-else' }] }
    if (sql.includes('FROM chart_grants')) return { rows: [{ permission: 'view' }] }
    throw new Error(`Unexpected SQL: ${sql}`)
  })
}
beforeEach(() => {
  vi.resetAllMocks()
  m.user.mockResolvedValue({ uid: 'synthetic-owner' })
  actor()
  m.exists.mockReturnValue(true)
  m.fetch.mockResolvedValue({ ok: true })
  vi.stubGlobal('fetch', m.fetch)
  vi.stubEnv('PYTHON_SIDECAR_URL', 'http://synthetic.invalid/')
  vi.stubEnv('PYTHON_SIDECAR_API_KEY', 'synthetic-key')
})
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs() })

describe('native-only Mimamsa LEL append through existing route guards', () => {
  it.each(['owner', 'super_admin'])('refuses an authorized non-native %s before any filesystem or resync effect', async role => {
    actor({ role: role === 'owner' ? 'guest' : role, owner: role === 'owner' })
    const response = await request(other)
    expect(response.status).toBe(403)
    expect(await response.json()).toEqual({ error: 'Life event intake is available only for the native chart.' })
    expect(m.query).toHaveBeenCalled()
    expect(m.user).toHaveBeenCalledBefore(m.query)
    expect(m.exists).not.toHaveBeenCalled()
    expect(m.append).not.toHaveBeenCalled()
    expect(m.fetch).not.toHaveBeenCalled()
  })
  it('also refuses non-native direct port calls before body validation or filesystem effects', () => {
    expect(appendNativeLifeEvent(other, null).status).toBe(403)
    expect(m.exists).not.toHaveBeenCalled()
    expect(m.append).not.toHaveBeenCalled()
    expect(m.fetch).not.toHaveBeenCalled()
  })
  it.each(['unsigned', 'no-admission', 'view-only'])('applies %s denial before native append scope and effects', async mode => {
    if (mode === 'unsigned') m.user.mockResolvedValue(null)
    if (mode === 'no-admission') actor({ admitted: false })
    if (mode === 'view-only') actor({ owner: false })
    const response = await request()
    expect(response.status).toBe(mode === 'unsigned' ? 401 : 403)
    if (mode === 'unsigned') expect(m.query).not.toHaveBeenCalled()
    if (mode === 'no-admission') expect(m.query).toHaveBeenCalledTimes(1)
    expect(m.exists).not.toHaveBeenCalled()
    expect(m.append).not.toHaveBeenCalled()
    expect(m.fetch).not.toHaveBeenCalled()
  })
  it('preserves exact synthetic native YAML, path, encoding, append ordering and transport tuple', async () => {
    const response = await request()
    expect(response.status).toBe(200)
    expect(m.query).toHaveBeenCalledBefore(m.exists)
    expect(m.exists).toHaveBeenCalledBefore(m.append)
    expect(m.append).toHaveBeenCalledBefore(m.fetch)
    expect(m.append).toHaveBeenCalledExactlyOnceWith(
      path.resolve(process.cwd(), '..', '01_FACTS_LAYER', 'LIFE_EVENT_LOG_v1_2.md'),
      '```yaml\nEVT.SYNTHETIC.001:\n  date: "2026-01-01"\n  category: "career"\n  subcategory: "fictional"\n  magnitude: "major"\n  disclosure_timing: "prospective"\n  notes: "Synthetic \'quoted\' note"\n  shaped_predictor: false\n```',
      'utf-8',
    )
    expect(m.fetch).toHaveBeenCalledExactlyOnceWith('http://synthetic.invalid/mimamsa/provenance-resync', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Api-Key': 'synthetic-key' },
      body: JSON.stringify({ chart_id: native }),
    })
    expect(await response.json()).toEqual({ ok: true, event_id: body.event_id,
      appended_to: 'LIFE_EVENT_LOG_v1_2.md', next: 'Life event appended; provenance resync completion is unconfirmed.' })
  })
  it('omits optional fields without adding whitespace/newlines', async () => {
    await request(native, { ...body, subcategory: '', notes: '' })
    const yaml = m.append.mock.calls[0][1]
    expect(yaml).not.toContain('subcategory:')
    expect(yaml).not.toContain('notes:')
    expect(yaml.startsWith('```yaml\n')).toBe(true)
    expect(yaml.endsWith('false\n```')).toBe(true)
  })
  it.each([
    [{ ...body, event_id: '' }, 'event_id, category, magnitude, date required'],
    [{ ...body, magnitude: 'invalid' }, 'invalid magnitude'],
  ])('preserves native validation before filesystem access', async (payload, error) => {
    const response = await request(native, payload)
    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error })
    expect(m.exists).not.toHaveBeenCalled()
    expect(m.append).not.toHaveBeenCalled()
    expect(m.fetch).not.toHaveBeenCalled()
  })
  it.each(['missing', 'exists-throws', 'append-throws'])('preserves primary %s errors and never requests resync', async mode => {
    if (mode === 'missing') m.exists.mockReturnValue(false)
    if (mode === 'exists-throws') m.exists.mockImplementation(() => { throw new Error('synthetic file failure') })
    if (mode === 'append-throws') m.append.mockImplementation(() => { throw new Error('synthetic file failure') })
    const response = await request()
    expect(response.status).toBe(500)
    expect(await response.json()).toEqual({ error: mode === 'missing'
      ? 'LEL markdown not found at expected path' : 'LEL append failed: Error: synthetic file failure' })
    expect(m.fetch).not.toHaveBeenCalled()
  })
  it.each(['rejected', 'non-2xx', 'pending'])('acknowledges one durable append with sync completion unconfirmed when dispatch is %s', async mode => {
    if (mode === 'rejected') m.fetch.mockRejectedValue(new Error('synthetic network failure'))
    if (mode === 'non-2xx') m.fetch.mockResolvedValue({ ok: false, status: 503 })
    if (mode === 'pending') m.fetch.mockReturnValue(new Promise(() => {}))
    const response = await request()
    expect(response.status).toBe(200)
    const result = await response.json()
    expect(result).toMatchObject({ ok: true, appended_to: 'LIFE_EVENT_LOG_v1_2.md', next: expect.stringContaining('completion is unconfirmed') })
    expect(m.append).toHaveBeenCalledTimes(1)
    expect(m.fetch).toHaveBeenCalledTimes(1)
    await Promise.resolve()
    expect(m.append).toHaveBeenCalledTimes(1)
  })
})
