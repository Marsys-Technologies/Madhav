import { readFileSync } from 'node:fs'
import path from 'node:path'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  prepareMcpRouting: vi.fn(),
  buildResolvedExecutionPlan: vi.fn(),
  admitByokTurn: vi.fn(),
  createRoleExecutor: vi.fn(),
  trackRoleExecutor: vi.fn(),
}))

vi.mock('@/lib/ai-console/repository', () => ({ prepareMcpRouting: mocks.prepareMcpRouting }))
vi.mock('@/lib/ai-console/routing', () => ({ buildResolvedExecutionPlan: mocks.buildResolvedExecutionPlan }))
vi.mock('@/lib/limits/byok_admission', () => ({ admitByokTurn: mocks.admitByokTurn }))
vi.mock('@/lib/ai-console/execution', () => ({ createRoleExecutor: mocks.createRoleExecutor }))
vi.mock('@/lib/ai-console/execution/tracked-executor', () => ({ trackRoleExecutor: mocks.trackRoleExecutor }))

import { prepareMcpByokRuntime } from '@/lib/mcp/prashna_ask/byok_preflight'

const INPUT = {
  userId: 'user-1',
  keyId: 'key-1',
  authKind: 'api_key' as const,
  chartId: '11111111-1111-4111-8111-111111111111',
  correlationId: '22222222-2222-4222-8222-222222222222',
  questionChars: 42,
}

describe('MCP BYOK routing seam', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    const safeSnapshot = { source: 'mcp', roles: { synthesizer: {}, planner: {}, deep_planner: {}, worker: {} } }
    mocks.prepareMcpRouting.mockResolvedValue({
      role: 'guest', selection: { kind: 'default' }, resolution: { roles: {} },
      safeSnapshot, snapshotId: 'snapshot-1',
    })
    mocks.buildResolvedExecutionPlan.mockReturnValue({
      source: 'mcp', roles: {
        synthesizer: { role: 'synthesizer' },
        planner: { role: 'planner' },
        deep_planner: { role: 'deep_planner' },
        worker: { role: 'worker' },
      },
    })
    mocks.admitByokTurn.mockReturnValue({ allowed: true, release: vi.fn() })
    mocks.createRoleExecutor.mockImplementation(target => ({ target, execute: vi.fn() }))
    mocks.trackRoleExecutor.mockImplementation(executor => executor)
  })

  it('preflights authority and admission before constructing only the three executable roles', async () => {
    const runtime = await prepareMcpByokRuntime(INPUT)

    expect(mocks.prepareMcpRouting).toHaveBeenCalledExactlyOnceWith({
      userId: INPUT.userId,
      keyId: INPUT.keyId,
      authKind: INPUT.authKind,
      chartId: INPUT.chartId,
      correlationId: INPUT.correlationId,
    })
    expect(mocks.admitByokTurn).toHaveBeenCalledExactlyOnceWith({ userId: INPUT.userId, questionChars: 42 })
    expect(mocks.createRoleExecutor.mock.calls.map(([target]) => target.role)).toEqual([
      'planner', 'deep_planner', 'worker',
    ])
    expect(mocks.createRoleExecutor).not.toHaveBeenCalledWith(expect.objectContaining({ role: 'synthesizer' }))
    expect(runtime.executors).toEqual({
      planner: expect.objectContaining({ target: expect.objectContaining({ role: 'planner' }) }),
      deep_planner: expect.objectContaining({ target: expect.objectContaining({ role: 'deep_planner' }) }),
      worker: expect.objectContaining({ target: expect.objectContaining({ role: 'worker' }) }),
    })
    for (const [, context] of mocks.trackRoleExecutor.mock.calls) {
      expect(context).toMatchObject({ snapshotId: 'snapshot-1', observation: { snapshot: runtime.safeSnapshot } })
    }
    expect(mocks.prepareMcpRouting.mock.invocationCallOrder[0]).toBeLessThan(mocks.admitByokTurn.mock.invocationCallOrder[0])
    expect(mocks.admitByokTurn.mock.invocationCallOrder[0]).toBeLessThan(mocks.createRoleExecutor.mock.invocationCallOrder[0])
  })

  it('releases the one admission lease if executor construction fails', async () => {
    const release = vi.fn()
    mocks.admitByokTurn.mockReturnValue({ allowed: true, release })
    mocks.createRoleExecutor.mockImplementationOnce(() => { throw new Error('construction failed') })

    await expect(prepareMcpByokRuntime(INPUT)).rejects.toThrow('construction failed')
    expect(release).toHaveBeenCalledTimes(1)
  })

  it('preserves legacy model resolution and synthesis behind the flag-off branch', () => {
    const source = readFileSync(path.join(process.cwd(), 'src/app/api/mcp/prashna_ask/route.ts'), 'utf8')
    expect(source).toContain('if (!byokEnabled)')
    expect(source).toContain("import('@/lib/models/registry')")
    expect(source).toContain("import('@/lib/models/runtime_config')")
    expect(source).toContain("import('@/lib/pipeline/prashna_ask_synthesis')")
    expect(source).toContain('if (byokRuntime)')
    expect(source).toContain('observeMcpExternalSynthesis(byokRuntime.safeSnapshot)')
    expect(source).not.toContain('await observeMcpExternalSynthesis')
    expect(source).toMatch(/observeMcpExternalSynthesis\(byokRuntime\.safeSnapshot\)\s+controller\.enqueue\(encoder\.encode\(finalLine\)\)/)
  })
})
