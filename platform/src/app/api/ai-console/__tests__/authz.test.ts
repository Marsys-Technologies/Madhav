import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '@/lib/ai-console/errors'

const mocks = vi.hoisted(() => ({ auth: vi.fn(), flag: vi.fn(), listAiConsoleState: vi.fn(), encrypt: vi.fn(), validate: vi.fn(),
  createConnection: vi.fn(), renameConnection: vi.fn(), replaceConnectionCredential: vi.fn(), saveConfiguration: vi.fn(),
  duplicateConfiguration: vi.fn(), previewChoiceDependencies: vi.fn(), deleteConnection: vi.fn(), deleteConfiguration: vi.fn(), setUserDefault: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/repository', () => mocks)
vi.mock('@/lib/ai-console/crypto', () => ({ encryptCredential: mocks.encrypt }))
vi.mock('@/lib/ai-console/validation', () => ({ validateConnection: mocks.validate }))

import * as root from '../route'
import * as connections from '../connections/route'
import * as connection from '../connections/[id]/route'
import * as validation from '../connections/[id]/validate/route'
import * as configurations from '../configurations/route'
import * as configuration from '../configurations/[id]/route'
import * as defaults from '../default/route'

const id = '11111111-1111-4111-8111-111111111111'
const context = () => ({ params: Promise.resolve({ id }) })
const request = (method: string, body = {}) => new Request('http://localhost/api/ai-console', {
  method, ...(method === 'GET' ? {} : { body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } }),
})
const routes = [
  ['state', () => root.GET()], ['connections', () => connections.GET()],
  ['create', () => connections.POST(request('POST'))], ['connection detail', () => connection.GET(request('GET'), context())],
  ['patch', () => connection.PATCH(request('PATCH'), context())], ['delete', () => connection.DELETE(request('DELETE'), context())],
  ['validation disclosure', () => validation.GET(request('GET'), context())], ['validate', () => validation.POST(request('POST'), context())],
  ['configurations', () => configurations.GET()], ['save', () => configurations.POST(request('POST'))],
  ['configuration detail', () => configuration.GET(request('GET'), context())],
  ['edit', () => configuration.PATCH(request('PATCH'), context())], ['remove', () => configuration.DELETE(request('DELETE'), context())],
  ['default', () => defaults.PUT(request('PUT'))],
] as const

beforeEach(() => {
  vi.resetAllMocks()
  mocks.flag.mockReturnValue(true)
  mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { id: 'owner', status: 'active', role: 'guest' } })
  mocks.listAiConsoleState.mockResolvedValue({ connections: [], models: [], configurations: [], roles: [], defaultChoice: null, clis: [], cliModels: [] })
})

describe.each(routes)('%s authorization', (_name, run) => {
  it('rejects missing authenticated profile before any owned operation', async () => {
    mocks.auth.mockResolvedValue(null)
    const response = await run()
    expect(response.status).toBe(401)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(mocks.listAiConsoleState).not.toHaveBeenCalled()
    expect(mocks.encrypt).not.toHaveBeenCalled()
    expect(mocks.createConnection).not.toHaveBeenCalled()
    expect(mocks.setUserDefault).not.toHaveBeenCalled()
    expect(mocks.saveConfiguration).not.toHaveBeenCalled()
  })
  it.each(['pending', 'disabled'])('rejects an %s account', async status => {
    mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { id: 'owner', status, role: 'super_admin' } })
    const response = await run()
    expect(response.status).toBe(403)
    expect(await response.json()).toEqual({ error: 'account_inactive' })
    expect(mocks.listAiConsoleState).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })
  it('uses the repository-standard disabled-feature response', async () => {
    mocks.flag.mockReturnValue(false)
    const response = await run()
    expect(response.status).toBe(404)
    expect(await response.json()).toEqual({ error: 'not_found' })
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(mocks.listAiConsoleState).not.toHaveBeenCalled()
  })
})

describe('owner isolation', () => {
  it.each(['guest', 'super_admin'])('keeps %s identity scoped to the authenticated owner', async role => {
    mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { id: 'owner', status: 'active', role } })
    expect((await root.GET()).status).toBe(200)
    expect(mocks.listAiConsoleState).toHaveBeenCalledWith('owner')
    for (const run of [
      () => connection.GET(request('GET'), context()),
      () => connection.PATCH(request('PATCH', { name: 'Other' }), context()),
      () => connection.PATCH(request('PATCH', { apiKey: 'test-only', acknowledgeCharge: true }), context()),
      () => connection.DELETE(request('DELETE', { confirm: true }), context()),
      () => validation.POST(request('POST', { acknowledgeCharge: true }), context()),
      () => configuration.GET(request('GET'), context()),
      () => configuration.DELETE(request('DELETE', { confirm: true }), context()),
    ]) expect((await run()).status).toBe(404)
    expect(mocks.encrypt).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
    expect(mocks.renameConnection).not.toHaveBeenCalled()
    expect(mocks.deleteConnection).not.toHaveBeenCalled()
    expect(mocks.previewChoiceDependencies).not.toHaveBeenCalled()
  })

  it('rejects foreign default targets through the owner-scoped repository', async () => {
    mocks.setUserDefault.mockRejectedValue(new AiConsoleError('AI_CHOICE_BROKEN'))
    const choice = { kind: 'provider_model', connectionId: id, modelId: 'test-model' }
    expect((await defaults.PUT(request('PUT', { choice }))).status).toBe(409)
    expect(mocks.setUserDefault).toHaveBeenCalledWith('owner', choice)
  })

  it('rejects foreign configuration edits and duplicates before repository mutations', async () => {
    const target = { kind: 'provider_model', connectionId: id, modelId: 'test-model' }
    const roles = { synthesizer: target, planner: target, deep_planner: target, worker: target }
    expect((await configurations.POST(request('POST', { name: 'Copy', duplicateFrom: id }))).status).toBe(404)
    expect((await configuration.PATCH(request('PATCH', { name: 'Other', expectedVersion: 1, roles }), context())).status).toBe(404)
    expect(mocks.duplicateConfiguration).not.toHaveBeenCalled()
    expect(mocks.saveConfiguration).not.toHaveBeenCalled()
  })

  it('validates IDs before any repository operation', async () => {
    expect((await connection.GET(request('GET'), { params: Promise.resolve({ id: 'invalid' }) })).status).toBe(400)
    expect(mocks.listAiConsoleState).not.toHaveBeenCalled()
  })
})
