import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AI_ROLES, type AiChoiceRef } from '../types'
import type { RoutingResolution } from '../repository'

const mocks = vi.hoisted(() => ({
  loadRoutingResolution: vi.fn(),
  createConnectionRuntimeBinding: vi.fn(),
  markConnectionForRevalidation: vi.fn(),
}))

vi.mock('../repository', () => ({
  loadRoutingResolution: mocks.loadRoutingResolution,
  markConnectionForRevalidation: mocks.markConnectionForRevalidation,
}))
vi.mock('../providers', () => ({ createConnectionRuntimeBinding: mocks.createConnectionRuntimeBinding }))

import { resolveUserRouting, toSafeRoutingSnapshot } from '../routing'

const connectionId = '00000000-0000-4000-8000-000000000001'
const configurationId = '00000000-0000-4000-8000-000000000002'

function provider(modelId = 'gpt-4.1-mini', id = connectionId) {
  return {
    kind: 'provider_model' as const,
    connectionId: id,
    providerId: 'openai' as const,
    credentialVersion: 3,
    modelId,
    displayName: modelId,
    compatibleRoles: [...AI_ROLES],
    supportsTools: true,
    supportsStructuredOutput: true,
  }
}

function directResolution(choice: AiChoiceRef = { kind: 'provider_model', connectionId, modelId: 'gpt-4.1-mini' }): RoutingResolution {
  const target = provider(choice.kind === 'provider_model' ? choice.modelId : 'gpt-4.1-mini')
  return {
    resolvedChoice: choice,
    configurationVersion: null,
    roles: { synthesizer: target, planner: target, deep_planner: target, worker: target },
  }
}

const baseInput = {
  userId: 'alice',
  source: 'pariprashna' as const,
  selection: { kind: 'default' as const },
  conversationId: '00000000-0000-4000-8000-000000000004',
  turnId: 'turn-1',
}

describe('central AI routing resolver', () => {
  beforeEach(() => {
    mocks.loadRoutingResolution.mockReset()
    mocks.createConnectionRuntimeBinding.mockReset().mockResolvedValue({
      providerId: 'openai', connectionId, modelId: 'gpt-4.1-mini', model: {}, dispose: vi.fn(),
    })
    mocks.markConnectionForRevalidation.mockReset().mockResolvedValue(undefined)
  })

  it('resolves one exact direct provider model for all four roles with lazy non-serializable bindings', async () => {
    mocks.loadRoutingResolution.mockResolvedValue(directResolution())
    const plan = await resolveUserRouting(baseInput)

    expect(Object.keys(plan.roles)).toEqual(AI_ROLES)
    for (const role of AI_ROLES) {
      expect(plan.roles[role].target).toEqual({
        kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'gpt-4.1-mini',
      })
      expect(Object.keys(plan.roles[role])).not.toContain('createRuntimeBinding')
      expect(Object.keys(plan.roles[role])).not.toContain('markRuntimeFailure')
    }
    expect(mocks.createConnectionRuntimeBinding).not.toHaveBeenCalled()
    const ownedBinding = await plan.roles.worker.createRuntimeBinding!()
    expect(ownedBinding).toMatchObject({ providerId: 'openai', connectionId, modelId: 'gpt-4.1-mini' })
    expect(plan.roles.worker.capabilities).toEqual({ supportsTools: true, supportsStructuredOutput: true })
    expect(mocks.createConnectionRuntimeBinding).toHaveBeenCalledOnce()
    expect(mocks.createConnectionRuntimeBinding).toHaveBeenCalledWith(
      { userId: 'alice', connectionId, providerId: 'openai', credentialVersion: 3 },
      expect.objectContaining({ modelId: 'gpt-4.1-mini', compatibleRoles: AI_ROLES }),
    )
    const normalized = { code: 'AI_PROVIDER_UNREACHABLE' as const,
      message: 'The selected provider could not be reached. Try the same choice again later.', retryable: true }
    await plan.roles.worker.markRuntimeFailure!(normalized)
    expect(mocks.markConnectionForRevalidation).toHaveBeenCalledWith('alice', connectionId, 3, normalized)
    expect(() => JSON.stringify(plan)).toThrow()

    const snapshot = toSafeRoutingSnapshot(plan)
    expect(snapshot.roles.worker).toEqual({ kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'gpt-4.1-mini' })
    expect(JSON.stringify(snapshot)).not.toMatch(/credential|binding|secret|api.?key/i)
    expect(Object.isFrozen(snapshot)).toBe(true)
    expect(Object.isFrozen(snapshot.roles)).toBe(true)
  })

  it('resolves an exact local CLI model for every role without starting it', async () => {
    const target = { kind: 'local_cli' as const, cliId: 'codex' as const, modelId: 'gpt-5.1-codex' }
    const resolvedTarget = { ...target, displayName: 'Codex', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }
    mocks.loadRoutingResolution.mockResolvedValue({
      resolvedChoice: target,
      configurationVersion: null,
      roles: { synthesizer: resolvedTarget, planner: resolvedTarget, deep_planner: resolvedTarget, worker: resolvedTarget },
    } satisfies RoutingResolution)

    const plan = await resolveUserRouting({ ...baseInput, selection: { kind: 'explicit', choice: target } })
    for (const role of AI_ROLES) {
      expect(plan.roles[role].target).toEqual(target)
      expect(plan.roles[role].adapterType).toBe('cli')
      expect(plan.roles[role].createRuntimeBinding).toBeUndefined()
      expect(plan.roles[role].cliUserId).toBe('alice')
      expect(Object.keys(plan.roles[role])).not.toContain('cliUserId')
    }
    expect(mocks.createConnectionRuntimeBinding).not.toHaveBeenCalled()
  })

  it('resolves four independent current assignments for a named configuration', async () => {
    const p2 = provider('claude-opus-4-1', '00000000-0000-4000-8000-000000000003')
    const cli = { kind: 'local_cli' as const, cliId: 'kimi_code' as const, modelId: null }
    const resolvedCli = { ...cli, displayName: 'Kimi', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }
    mocks.loadRoutingResolution.mockResolvedValue({
      resolvedChoice: { kind: 'custom_configuration', configurationId },
      configurationVersion: 7,
      roles: { synthesizer: provider(), planner: p2, deep_planner: resolvedCli, worker: provider('gpt-4.1') },
    } satisfies RoutingResolution)

    const plan = await resolveUserRouting({
      ...baseInput,
      selection: { kind: 'explicit', choice: { kind: 'custom_configuration', configurationId } },
    })
    expect(plan.configurationVersion).toBe(7)
    expect(toSafeRoutingSnapshot(plan).roles).toEqual({
      synthesizer: { kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'gpt-4.1-mini' },
      planner: { kind: 'provider_model', connectionId: p2.connectionId, providerId: 'openai', modelId: 'claude-opus-4-1' },
      deep_planner: cli,
      worker: { kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'gpt-4.1' },
    })
  })

  it('keeps Default live, explicit direct choices pinned, and named configurations live for later turns', async () => {
    const first = directResolution()
    const secondChoice = { kind: 'provider_model' as const, connectionId, modelId: 'gpt-4.1' }
    const second = directResolution(secondChoice)
    mocks.loadRoutingResolution.mockResolvedValueOnce(first).mockResolvedValueOnce(second)
    const oldDefault = toSafeRoutingSnapshot(await resolveUserRouting(baseInput))
    const newDefault = toSafeRoutingSnapshot(await resolveUserRouting({ ...baseInput, turnId: 'turn-2' }))
    expect(oldDefault.resolvedChoice).toEqual(first.resolvedChoice)
    expect(newDefault.resolvedChoice).toEqual(secondChoice)

    mocks.loadRoutingResolution.mockResolvedValueOnce(second)
    const explicit = { kind: 'explicit' as const, choice: secondChoice }
    await resolveUserRouting({ ...baseInput, selection: explicit, turnId: 'turn-3' })
    expect(mocks.loadRoutingResolution).toHaveBeenLastCalledWith('alice', explicit, baseInput.conversationId)

    const configChoice = { kind: 'custom_configuration' as const, configurationId }
    mocks.loadRoutingResolution
      .mockResolvedValueOnce({ ...first, resolvedChoice: configChoice, configurationVersion: 1 })
      .mockResolvedValueOnce({ ...second, resolvedChoice: configChoice, configurationVersion: 2 })
    const oldConfig = toSafeRoutingSnapshot(await resolveUserRouting({ ...baseInput, selection: { kind: 'explicit', choice: configChoice }, turnId: 'turn-4' }))
    const newConfig = toSafeRoutingSnapshot(await resolveUserRouting({ ...baseInput, selection: { kind: 'explicit', choice: configChoice }, turnId: 'turn-5' }))
    expect(oldConfig.configurationVersion).toBe(1)
    expect(newConfig.configurationVersion).toBe(2)
    expect(oldConfig.roles.synthesizer.modelId).toBe('gpt-4.1-mini')
    expect(newConfig.roles.synthesizer.modelId).toBe('gpt-4.1')
  })

  it('normalizes legacy consult to the canonical Pariprashna snapshot source', async () => {
    mocks.loadRoutingResolution.mockResolvedValue(directResolution())
    const plan = await resolveUserRouting({ ...baseInput, source: 'consult' })
    expect(plan.source).toBe('pariprashna')
    expect(toSafeRoutingSnapshot(plan).source).toBe('pariprashna')
  })
})
