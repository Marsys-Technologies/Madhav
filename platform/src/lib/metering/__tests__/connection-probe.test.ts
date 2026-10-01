import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  authorize: vi.fn(), load: vi.fn(), decrypt: vi.fn(), start: vi.fn(), finish: vi.fn(), http: vi.fn(),
}))
vi.mock('@/lib/ai-console/repository', () => ({
  assertConnectionRequestAuthorized: mocks.authorize,
  assertRuntimeModelRequestAuthorized: vi.fn(),
  loadConnectionCredential: mocks.load,
  loadRuntimeModelCredential: vi.fn(),
}))
vi.mock('@/lib/ai-console/crypto', () => ({ decryptCredential: mocks.decrypt }))
vi.mock('@/lib/metering/service', () => ({ startAttempt: mocks.start, finishAttempt: mocks.finish }))

import { probeConnectionModel } from '@/lib/ai-console/providers'

const connection = { userId: 'alice', connectionId: '11111111-1111-4111-8111-111111111111',
  providerId: 'openai' as const, credentialVersion: 1 }
const model = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['planner' as const],
  supportsTools: true, supportsStructuredOutput: true }

beforeEach(() => {
  vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'true')
  for (const mock of Object.values(mocks)) mock.mockReset()
  mocks.authorize.mockResolvedValue(undefined)
  mocks.load.mockResolvedValue({})
  mocks.decrypt.mockReturnValue('synthetic-key-123456')
  mocks.start.mockImplementation(async context => ({ ...context,
    attemptId: '22222222-2222-4222-8222-222222222222', startedAt: '2026-09-30T00:00:00Z' }))
  mocks.finish.mockResolvedValue(undefined)
  mocks.http.mockImplementation(async () => Response.json({ choices: [{ message: { content: 'OK' } }],
    usage: { prompt_tokens: 4, completion_tokens: 2 } }))
  vi.stubGlobal('fetch', mocks.http)
})
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs() })

describe('enabled owned-connection validation probe', () => {
  it('starts before HTTP and records provider usage before returning', async () => {
    const result = await probeConnectionModel(connection, model, new AbortController().signal)
    expect(result).toEqual({ inputTokens: 4, outputTokens: 2 })
    expect(mocks.start).toHaveBeenCalledOnce()
    expect(mocks.start.mock.calls[0][0]).toMatchObject({ userId: 'alice', channel: 'backend',
      purpose: 'validation', connectionId: connection.connectionId, model: model.modelId })
    expect(mocks.http).toHaveBeenCalledOnce()
    expect(mocks.finish).toHaveBeenCalledOnce()
    expect(mocks.finish.mock.calls[0][1]).toMatchObject({ status: 'success',
      usage: { input: 4, output: 2, source: 'provider_reported' } })
    expect(mocks.start.mock.invocationCallOrder[0]).toBeLessThan(mocks.http.mock.invocationCallOrder[0])
    expect(mocks.http.mock.invocationCallOrder[0]).toBeLessThan(mocks.finish.mock.invocationCallOrder[0])
    expect(JSON.stringify(mocks.finish.mock.calls)).not.toContain('synthetic-key-123456')
  })

  it('never contacts the provider when metering start fails', async () => {
    mocks.start.mockRejectedValue(new Error('ledger unavailable'))
    await expect(probeConnectionModel(connection, model, new AbortController().signal))
      .rejects.toThrow('ledger unavailable')
    expect(mocks.http).not.toHaveBeenCalled()
    expect(mocks.finish).not.toHaveBeenCalled()
  })

  it('records an error with unknown usage after a provider failure', async () => {
    mocks.http.mockResolvedValue(Response.json({ error: { message: 'private' } }, { status: 503 }))
    await expect(probeConnectionModel(connection, model, new AbortController().signal)).rejects.toBeDefined()
    expect(mocks.finish).toHaveBeenCalledOnce()
    expect(mocks.finish.mock.calls[0][1]).toMatchObject({ status: 'error',
      usage: { input: null, output: null, source: 'unavailable' } })
    expect(JSON.stringify(mocks.finish.mock.calls)).not.toContain('private')
  })
})
