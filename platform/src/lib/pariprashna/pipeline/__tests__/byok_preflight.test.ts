import { beforeEach, describe, expect, it, vi } from 'vitest'

const m = vi.hoisted(() => ({
  order: [] as string[],
  authorize: vi.fn(), getConversation: vi.fn(), insertConversation: vi.fn(),
  getSelection: vi.fn(), setSelection: vi.fn(), resolve: vi.fn(), snapshot: vi.fn(),
  createExecutor: vi.fn(), trackExecutor: vi.fn(), admit: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: vi.fn() }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: m.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/conversations', () => ({
  getConversation: m.getConversation,
  insertConversationWithId: m.insertConversation,
}))
vi.mock('@/lib/ai-console/repository', () => ({
  getConversationSelection: m.getSelection,
  setConversationSelection: m.setSelection,
  insertRoutingSnapshot: m.snapshot,
}))
vi.mock('@/lib/ai-console/routing', () => ({
  resolveUserRouting: m.resolve,
  toSafeRoutingSnapshot: (plan: { snapshot: unknown }) => plan.snapshot,
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
    m.authorize.mockImplementation(async () => { m.order.push('authorize'); return 'allow' })
    m.getConversation.mockResolvedValue({ chart_id: CHART })
    m.insertConversation.mockImplementation(async () => { m.order.push('conversation') })
    m.setSelection.mockImplementation(async () => { m.order.push('selection') })
    m.getSelection.mockResolvedValue(selection)
    m.resolve.mockImplementation(async () => { m.order.push('resolve'); return { roles, snapshot } })
    m.snapshot.mockImplementation(async () => { m.order.push('snapshot'); return '30000000-0000-4000-8000-000000000003' })
    m.admit.mockImplementation(() => { m.order.push('admit'); return { allowed: true, release: vi.fn() } })
    m.createExecutor.mockImplementation((role) => { m.order.push(`executor:${role.role}`); return { descriptor: { role: role.role, ...target } } })
    m.trackExecutor.mockImplementation(executor => executor)
  })

  it('persists a first-turn selection before one resolve, snapshot, admission and all executors', async () => {
    const runtime = await prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: true, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })
    expect(runtime.kind).toBe('byok')
    expect(m.order).toEqual(['authorize', 'conversation', 'selection', 'resolve', 'snapshot', 'admit',
      'executor:synthesizer', 'executor:planner', 'executor:deep_planner', 'executor:worker'])
    expect(m.resolve).toHaveBeenCalledOnce()
  })

  it('rejects stale existing-turn identity without overwriting or resolving', async () => {
    m.getSelection.mockResolvedValue({ kind: 'explicit', choice: { kind: 'local_cli', cliId: 'codex', modelId: null } })
    await expect(prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: false, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(m.setSelection).not.toHaveBeenCalled()
    expect(m.resolve).not.toHaveBeenCalled()
    expect(m.createExecutor).not.toHaveBeenCalled()
  })

  it('does not admit or create an executor when snapshot commit fails', async () => {
    m.snapshot.mockRejectedValue(new Error('db unavailable'))
    await expect(prepareByokTurn({ userId: USER, role: 'guest', chartId: CHART,
      conversationId: CONVERSATION, isFirstTurn: false, turnId: TURN,
      requestedSelection: selection, questionChars: 12 })).rejects.toThrow('db unavailable')
    expect(m.admit).not.toHaveBeenCalled()
    expect(m.createExecutor).not.toHaveBeenCalled()
  })
})
