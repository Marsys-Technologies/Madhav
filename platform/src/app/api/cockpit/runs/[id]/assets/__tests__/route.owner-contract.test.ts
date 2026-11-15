import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const { query, getServerUser, readBuildRunAssets } = vi.hoisted(() => ({
  query: vi.fn(), getServerUser: vi.fn(), readBuildRunAssets: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser }))
vi.mock('@/lib/build/runAssets', () => ({ readBuildRunAssets }))

import { GET, maxDuration } from '../route'

const request = new NextRequest('http://localhost/api/cockpit/runs/run-1/assets')
const context = { params: Promise.resolve({ id: 'run-1' }) }

beforeEach(() => {
  vi.resetAllMocks()
  getServerUser.mockResolvedValue({ uid: 'admin-1' })
  query.mockResolvedValue({ rows: [{ role: 'super_admin' }] })
})
afterEach(() => vi.restoreAllMocks())

describe('run-assets Portal → Identity → Build port', () => {
  it('keeps the existing duration budget', () => expect(maxDuration).toBe(8))

  it('authenticates and checks the role before awaiting params or reading Build data', async () => {
    const order: string[] = []
    getServerUser.mockImplementation(async () => { order.push('session'); return { uid: 'admin-1' } })
    query.mockImplementation(async () => { order.push('role'); return { rows: [{ role: 'super_admin' }] } })
    readBuildRunAssets.mockImplementation(async id => { order.push(`build:${id}`); return [{ rows_written: 70 }] })
    const params = { then(resolve: (value: { id: string }) => void) { order.push('params'); resolve({ id: 'run-1' }) } }
    const response = await GET(request, { params: params as unknown as Promise<{ id: string }> })
    expect(order).toEqual(['session', 'role', 'params', 'build:run-1'])
    expect(query).toHaveBeenCalledExactlyOnceWith('SELECT role FROM profiles WHERE id=$1', ['admin-1'])
    expect(await response.json()).toEqual({ data: { run_assets: [{ rows_written: 70 }] } })
  })

  it('rejects an unsigned request before the role or Build reads', async () => {
    getServerUser.mockResolvedValue(null)
    const response = await GET(request, context)
    expect(response.status).toBe(403)
    expect(await response.json()).toEqual({ error: 'Forbidden' })
    expect(query).not.toHaveBeenCalled()
    expect(readBuildRunAssets).not.toHaveBeenCalled()
  })

  it.each([
    { label: 'missing', rows: [] },
    { label: 'guest', rows: [{ role: 'guest' }] },
  ])('rejects a $label role', async ({ rows }) => {
    query.mockResolvedValue({ rows })
    expect((await GET(request, context)).status).toBe(403)
    expect(readBuildRunAssets).not.toHaveBeenCalled()
  })

  it('retains the existing caught Build-read error response and log label', async () => {
    const error = new Error('read failed')
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    readBuildRunAssets.mockRejectedValue(error)
    const response = await GET(request, context)
    expect(response.status).toBe(500)
    expect(await response.json()).toEqual({ error: 'db error' })
    expect(log).toHaveBeenCalledExactlyOnceWith('[cockpit/runs/assets]', error)
  })

  it('preserves the pre-existing role-read failure boundary', async () => {
    const error = new Error('role failed')
    query.mockRejectedValue(error)
    await expect(GET(request, context)).rejects.toBe(error)
    expect(readBuildRunAssets).not.toHaveBeenCalled()
  })

  it('preserves params rejection before the caught Build-read section', async () => {
    const error = new Error('bad params')
    const params = { then(_resolve: unknown, reject: (reason: Error) => void) { reject(error) } }
    await expect(GET(request, { params: params as unknown as Promise<{ id: string }> })).rejects.toBe(error)
    expect(readBuildRunAssets).not.toHaveBeenCalled()
  })
})
