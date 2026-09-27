import { beforeEach, describe, expect, it, vi } from 'vitest'

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

import { AiConsoleError } from '../errors'
import { resolveUserRouting } from '../routing'

const input = {
  userId: 'alice',
  source: 'backend' as const,
  selection: { kind: 'default' as const },
  turnId: 'job-1',
}

describe('routing has no fallback path', () => {
  beforeEach(() => {
    mocks.loadRoutingResolution.mockReset()
    mocks.createConnectionRuntimeBinding.mockReset()
    mocks.markConnectionForRevalidation.mockReset()
  })

  it.each([
    'AI_DEFAULT_REQUIRED', 'AI_CHOICE_BROKEN', 'AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE',
    'AI_CLI_NOT_GRANTED', 'AI_CLI_UNREACHABLE', 'AI_PROVIDER_UNREACHABLE',
  ] as const)('stops on exact-choice failure %s without querying or binding an alternative', async code => {
    mocks.loadRoutingResolution.mockRejectedValue(new AiConsoleError(code))
    await expect(resolveUserRouting(input)).rejects.toMatchObject({ code })
    expect(mocks.loadRoutingResolution).toHaveBeenCalledOnce()
    expect(mocks.createConnectionRuntimeBinding).not.toHaveBeenCalled()
  })

  it('fails closed for a disabled user and never attempts another owner', async () => {
    mocks.loadRoutingResolution.mockRejectedValue(new AiConsoleError('AI_PERMISSION_DENIED'))
    await expect(resolveUserRouting(input)).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(mocks.loadRoutingResolution).toHaveBeenCalledExactlyOnceWith('alice', input.selection, undefined)
  })

  it('does not construct a plan for a foreign conversation', async () => {
    const conversationId = '00000000-0000-4000-8000-000000000004'
    mocks.loadRoutingResolution.mockRejectedValue(new AiConsoleError('AI_PERMISSION_DENIED'))
    await expect(resolveUserRouting({ ...input, conversationId })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(mocks.loadRoutingResolution).toHaveBeenCalledExactlyOnceWith('alice', input.selection, conversationId)
    expect(mocks.createConnectionRuntimeBinding).not.toHaveBeenCalled()
  })

  it('rejects a malformed conversation reference with a stable error before persistence access', async () => {
    await expect(resolveUserRouting({ ...input, conversationId: 'not-a-uuid' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(mocks.loadRoutingResolution).not.toHaveBeenCalled()
  })

  it('fails closed before persistence access for an ownerless job', async () => {
    await expect(resolveUserRouting({ ...input, userId: '' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(mocks.loadRoutingResolution).not.toHaveBeenCalled()
  })
})
