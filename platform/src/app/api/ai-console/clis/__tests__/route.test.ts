import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ auth: vi.fn(), flag: vi.fn(), list: vi.fn(), validate: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/repository', () => ({ listAiConsoleState: mocks.list }))
vi.mock('@/lib/ai-console/cli/validation', () => ({ validateCli: mocks.validate }))

import * as route from '../route'
import * as validateRoute from '../[cliId]/validate/route'

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
  it('reveals only product and not-granted state for ungranted CLIs and projects built-in model to null', async () => {
    const response = await route.GET(); const body = await response.json()
    expect(body.clis[0]).toEqual({ cliId: 'codex', productName: 'Codex CLI', state: 'not_granted' })
    expect(JSON.stringify(body.clis[0])).not.toContain('SECRET')
    expect(body.clis[1].models[0].modelId).toBeNull()
  })

  it('masks a stale reachable catalog for a detect-only CLI', async () => {
    mocks.list.mockResolvedValueOnce({ connections: [], models: [], configurations: [], roles: [], defaultChoice: null,
      clis: [{ cli_id: 'codex', granted_at: new Date(), revoked_at: null, detected_product: 'Codex CLI',
        detected_version: '0.155.1', validation_state: 'reachable', last_checked_at: new Date('2026-09-27T00:00:00Z') }],
      cliModels: [{ cli_id: 'codex', model_id: '__madhav_builtin_default__', display_name: 'Built-in default',
        compatible_roles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supports_tools: false,
        supports_structured_output: true, available: true, is_builtin_default: true }],
    })
    const body = await (await route.GET()).json()
    expect(body.clis[0]).toMatchObject({ cliId: 'codex', state: 'needs_attention', models: [] })
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
