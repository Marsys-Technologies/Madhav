import { beforeEach, describe, expect, it, vi } from 'vitest'

const m = vi.hoisted(() => ({
  order: [] as string[],
  prepare: vi.fn(), build: vi.fn(),
  createExecutor: vi.fn(), trackExecutor: vi.fn(), admit: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: vi.fn() }))
vi.mock('@/lib/ai-console/repository', () => ({
  prepareTurnRouting: m.prepare,
}))
vi.mock('@/lib/ai-console/routing', () => ({
  buildResolvedExecutionPlan: m.build,
}))
vi.mock('@/lib/ai-console/execution', () => ({ createRoleExecutor: m.createExecutor }))
vi.mock('@/lib/ai-console/execution/tracked-executor', () => ({ trackRoleExecutor: m.trackExecutor }))
vi.mock('@/lib/limits/byok_admission', () => ({ admitByokTurn: m.admit }))

import { prepareByokTurn } from '../byok_preflight'

const USER = 'alice'
const CHART = '10000000-0000-4000-8000-000000000001'
const CONVERSATION = '20000000-0000-4000-8000-000000000002'
const TURN = 'turn-1'
const selection = { kind: 'default' as const }
const target = { kind: 'provider_model' as const, connectionId: 'c', providerId: 'openai' as const, modelId: 'm' }
const roles = Object.fromEntries(['synthesizer', 'planner', 'deep_planner', 'worker'].map(role => [role, { role }]))
const snapshot = { roles: { synthesizer: target, planner: target, deep_planner: target, worker: target } }

describe('prepareByokTurn', () => {
  beforeEach(() => {
    vi.clearAllMocks(); m.order.length = 0
    m.prepare.mockImplementation(async () => { m.order.push('atomic-authority-selection-resolve-snapshot'); return {
      selection, resolution: {}, safeSnapshot: snapshot,
      snapshotId: '30000000-0000-4000-8000-000000000003',
    } })
    m.build.mockImplementation(() => { m.order.push('build'); return { roles } })
    m.admit.mockImplementation(() => { m.order.push('admit'); return { allowed: true, release: vi.fn() } })
    m.createExecutor.mockImplementation((role) => { m.order.push(`executor:${role.role}`); return { descriptor: { role: role.role, ...target } } })
    m.trackExecutor.mockImplementation(executor => executor)
  })

  it('persists a first-turn selection before one resolve, snapshot, admission and all executors', async () => {
    const runtime = await prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: true, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })
    expect(runtime.kind).toBe('byok')
    expect(m.order).toEqual(['atomic-authority-selection-resolve-snapshot', 'build', 'admit',
      'executor:synthesizer', 'executor:planner', 'executor:deep_planner', 'executor:worker'])
    expect(m.prepare).toHaveBeenCalledOnce()
  })

  it('rejects stale existing-turn identity without overwriting or resolving', async () => {
    m.prepare.mockRejectedValue(new (await import('@/lib/ai-console/errors')).AiConsoleError('AI_CHOICE_BROKEN'))
    await expect(prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: false, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(m.build).not.toHaveBeenCalled()
    expect(m.createExecutor).not.toHaveBeenCalled()
  })

  it('does not admit or create an executor when snapshot commit fails', async () => {
    m.prepare.mockRejectedValue(new Error('db unavailable'))
    await expect(prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: false, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })).rejects.toThrow('db unavailable')
    expect(m.admit).not.toHaveBeenCalled()
    expect(m.createExecutor).not.toHaveBeenCalled()
  })
})
