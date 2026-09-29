import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ auth: vi.fn(), flag: vi.fn(), list: vi.fn(), validate: vi.fn(), addModel: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/repository', () => ({ listAiConsoleState: mocks.list }))
vi.mock('@/lib/ai-console/cli/validation', () => ({ validateCli: mocks.validate, testAndAddManualCliModel: mocks.addModel }))

import * as route from '../route'
import * as validateRoute from '../[cliId]/validate/route'
import * as modelRoute from '../[cliId]/models/route'

const context = (cliId: string) => ({ params: Promise.resolve({ cliId }) })

beforeEach(() => {
  vi.resetAllMocks(); mocks.flag.mockReturnValue(true)
  mocks.auth.mockResolvedValue({ user: { uid: 'alice' }, profile: { id: 'alice', role: 'guest', status: 'active' } })
  mocks.list.mockResolvedValue({ connections: [], models: [], configurations: [], roles: [], defaultChoice: null,
    clis: [
      { cli_id: 'codex', granted_at: null, revoked_at: null, detected_product: 'SECRET', detected_version: 'SECRET', validation_state: 'reachable' },
      { cli_id: 'claude_code', granted_at: new Date(), revoked_at: null, detected_product: 'Claude Code', detected_version: '2.1.56', validation_state: 'reachable', last_checked_at: new Date('2026-09-27T00:00:00Z') },
    ], cliModels: [{ cli_id: 'claude_code', model_id: '__madhav_builtin_default__', display_name: 'Built-in default',
      compatible_roles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supports_tools: false,
      supports_structured_output: true, available: true, is_builtin_default: true }],
  })
  mocks.validate.mockResolvedValue({ cliId: 'claude_code', productName: 'Claude Code', state: 'reachable', modelCount: 1 })
})

describe('user CLI routes', () => {
  it('admits one exact manual model test only for a valid request and signed-in user', async () => {
    const request = new Request('http://localhost/api/ai-console/clis/claude_code/models', { method: 'POST',
      body: JSON.stringify({ modelId: 'claude-test' }) })
    const response = await modelRoute.POST(request, context('claude_code'))
    expect(response.status).toBe(200)
    expect(mocks.addModel).toHaveBeenCalledWith('alice', 'claude_code', 'claude-test', request.signal)
    const invalid = new Request('http://localhost/api/ai-console/clis/claude_code/models', { method: 'POST',
      body: JSON.stringify({ modelId: 'claude-test', unsafe: true }) })
    expect((await modelRoute.POST(invalid, context('claude_code'))).status).toBe(400)
    mocks.auth.mockResolvedValueOnce(null)
    const denied = new Request('http://localhost/api/ai-console/clis/claude_code/models', { method: 'POST',
      body: JSON.stringify({ modelId: 'claude-test' }) })
    expect((await modelRoute.POST(denied, context('claude_code'))).status).toBe(401)
  })

  it('reveals only product and not-granted state for ungranted CLIs and projects built-in model to null', async () => {
    const response = await route.GET(); const body = await response.json()
    expect(body.clis[0]).toEqual({ cliId: 'codex', productName: 'Codex CLI', state: 'not_granted' })
    expect(JSON.stringify(body.clis[0])).not.toContain('SECRET')
    expect(body.clis[1].models[0].modelId).toBeNull()
  })

  it('normalizes the raw PostgreSQL timestamptz string returned by the shared DB parser', async () => {
    mocks.list.mockResolvedValueOnce({ connections: [], models: [], configurations: [], roles: [], defaultChoice: null,
      clis: [{ cli_id: 'codex', granted_at: '2026-09-28 06:57:37.901441+00', revoked_at: null,
        detected_product: 'Codex CLI', detected_version: '0.155.1', validation_state: 'reachable',
        last_checked_at: '2026-09-28 06:58:02.621422+00' }],
      cliModels: [],
    })

    const body = await (await route.GET()).json()
    expect(body.clis[0].lastCheckedAt).toBe('2026-09-28T06:58:02.621Z')
  })

  it('projects a validated Kimi subscription catalog now that its adapter is executable', async () => {
    mocks.list.mockResolvedValueOnce({ connections: [], models: [], configurations: [], roles: [], defaultChoice: null,
      clis: [{ cli_id: 'kimi_code', granted_at: new Date(), revoked_at: null, detected_product: 'Kimi Code',
        detected_version: '2.0.2', validation_state: 'reachable', last_checked_at: new Date('2026-09-27T00:00:00Z') }],
      cliModels: [{ cli_id: 'kimi_code', model_id: '__madhav_builtin_default__', display_name: 'Built-in default',
        compatible_roles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supports_tools: false,
        supports_structured_output: true, available: true, is_builtin_default: true }],
    })
    const body = await (await route.GET()).json()
    expect(body.clis[0]).toMatchObject({ cliId: 'kimi_code', state: 'reachable',
      models: [expect.objectContaining({ modelId: null, isBuiltinDefault: true })] })
  })

  it('uses active-user auth, closed IDs, request cancellation, and the shared validation admission', async () => {
    const request = new Request('http://localhost/api/ai-console/clis/claude_code/validate', { method: 'POST' })
    const response = await validateRoute.POST(request, context('claude_code'))
    expect(response.status).toBe(200)
    expect(mocks.validate).toHaveBeenCalledWith('alice', 'claude_code', request.signal)
    expect((await validateRoute.POST(request, context('unknown'))).status).toBe(400)
    mocks.auth.mockResolvedValueOnce(null)
    expect((await validateRoute.POST(request, context('claude_code'))).status).toBe(401)
  })

  it('single-flights one host CLI validation across different users', async () => {
    let finish!: () => void
    mocks.validate.mockImplementationOnce(() => new Promise(resolve => {
      finish = () => resolve({ cliId: 'claude_code', productName: 'Claude Code', state: 'reachable', modelCount: 1 })
    }))
    const firstRequest = new Request('http://localhost/api/ai-console/clis/claude_code/validate', { method: 'POST' })
    const first = validateRoute.POST(firstRequest, context('claude_code'))
    await vi.waitFor(() => expect(mocks.validate).toHaveBeenCalledOnce())
    mocks.auth.mockResolvedValueOnce({ user: { uid: 'bob' }, profile: { id: 'bob', role: 'guest', status: 'active' } })
    const secondRequest = new Request('http://localhost/api/ai-console/clis/claude_code/validate', { method: 'POST' })
    const second = await validateRoute.POST(secondRequest, context('claude_code'))
    expect(second.status).toBe(429)
    expect(mocks.validate).toHaveBeenCalledOnce()
    finish()
    expect((await first).status).toBe(200)
  })
})
