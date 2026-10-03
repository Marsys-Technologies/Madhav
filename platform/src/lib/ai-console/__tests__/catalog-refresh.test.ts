import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../errors'

const mocks = vi.hoisted(() => ({ claim: vi.fn(), load: vi.fn(), store: vi.fn(), authorize: vi.fn(),
  discover: vi.fn(), probe: vi.fn(), validate: vi.fn() }))
vi.mock('../repository', () => ({ claimConnectionCatalogRefresh: mocks.claim,
  loadConnectionCredential: mocks.load, storeConnectionCatalogRefresh: mocks.store,
  assertConnectionRequestAuthorized: mocks.authorize }))
vi.mock('../crypto', () => ({ decryptCredential: () => 'fixture-key-never-real' }))
vi.mock('../providers', async importOriginal => ({
  ...await importOriginal<typeof import('../providers')>(),
  discoverConnectionModels: mocks.discover, probeConnectionModel: mocks.probe,
}))
vi.mock('../validation', () => ({ validateConnection: mocks.validate }))

import { refreshProviderCatalog } from '../catalog-refresh'

const id = '11111111-1111-4111-8111-111111111111'
const claim = { credentialVersion: 2, providerId: 'openai' as const, epoch: 'fixture-epoch' }
const model = { modelId: 'gpt-4.1', displayName: 'GPT 4.1', compatibleRoles: ['synthesizer' as const],
  supportsTools: false, supportsStructuredOutput: false }

beforeEach(() => {
  vi.resetAllMocks()
  mocks.claim.mockResolvedValue(claim)
  mocks.load.mockResolvedValue({ workspaceId: null })
  mocks.store.mockResolvedValue(true)
  mocks.discover.mockResolvedValue([model])
})
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('provider catalogue metadata refresh', () => {
  it('passes the pinned credential version and lease without invoking generation', async () => {
    expect(await refreshProviderCatalog('owner', id, { force: true })).toEqual({ status: 'refreshed', modelCount: 1 })
    expect(mocks.claim).toHaveBeenCalledWith('owner', id, true)
    expect(mocks.load).toHaveBeenCalledWith('owner', id, 2)
    expect(mocks.discover).toHaveBeenCalledWith({ userId: 'owner', connectionId: id,
      providerId: 'openai', credentialVersion: 2 }, expect.any(AbortSignal))
    expect(mocks.store).toHaveBeenCalledWith('owner', id, { credentialVersion: 2, epoch: claim.epoch, models: [model] })
    expect(mocks.probe).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })

  it('skips a fresh, cooling-down or leased connection before loading credentials', async () => {
    mocks.claim.mockResolvedValue(null)
    expect(await refreshProviderCatalog('owner', id)).toEqual({ status: 'skipped' })
    expect(mocks.claim).toHaveBeenCalledWith('owner', id, false)
    expect(mocks.load).not.toHaveBeenCalled()
    expect(mocks.discover).not.toHaveBeenCalled()
    expect(mocks.store).not.toHaveBeenCalled()
  })

  it('accepts an authoritative empty catalogue without pretending a model was tested', async () => {
    mocks.discover.mockResolvedValue([])
    expect(await refreshProviderCatalog('owner', id)).toEqual({ status: 'refreshed', modelCount: 0 })
    expect(mocks.store).toHaveBeenCalledWith('owner', id, { credentialVersion: 2, epoch: claim.epoch, models: [] })
  })

  it.each([[401, 'AI_CONNECTION_INVALID'], [403, 'AI_PERMISSION_DENIED'], [429, 'AI_RATE_LIMITED'],
    [503, 'AI_PROVIDER_UNREACHABLE']] as const)('normalizes HTTP %s without storing upstream content', async (status, code) => {
    mocks.discover.mockRejectedValue({ status, message: 'fixture-private-upstream-content' })
    const error = await refreshProviderCatalog('owner', id).catch(cause => cause)
    expect(error).toMatchObject({ code })
    expect(String(error)).not.toContain('fixture-private-upstream-content')
    expect(mocks.store).toHaveBeenCalledWith('owner', id, { credentialVersion: 2, epoch: claim.epoch, errorCode: code })
  })

  it('does not write a health result if ownership or credential version changed', async () => {
    mocks.load.mockRejectedValue(new AiConsoleError('AI_CHOICE_BROKEN'))
    await expect(refreshProviderCatalog('owner', id)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(mocks.discover).not.toHaveBeenCalled()
    expect(mocks.store).not.toHaveBeenCalled()
  })

  it('rejects a stale lease result instead of reporting a successful refresh', async () => {
    mocks.store.mockResolvedValue(false)
    await expect(refreshProviderCatalog('owner', id)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
  })

  it('checks caller cancellation before claiming and before persisting discovery', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(refreshProviderCatalog('owner', id, { signal: controller.signal })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.claim).not.toHaveBeenCalled()
    const during = new AbortController()
    mocks.discover.mockImplementation(async () => { during.abort(); return [model] })
    await expect(refreshProviderCatalog('owner', id, { signal: during.signal })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.store).toHaveBeenCalledWith('owner', id, { credentialVersion: 2, epoch: claim.epoch, errorCode: 'AI_EXECUTION_FAILED' })
  })

  it('normalizes total deadline expiry and stores a retryable provider failure', async () => {
    const deadline = new AbortController()
    vi.spyOn(AbortSignal, 'timeout').mockReturnValue(deadline.signal)
    mocks.discover.mockImplementation((_connection, signal: AbortSignal) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(new Error('private-timeout')), { once: true })
    }))
    const result = refreshProviderCatalog('owner', id).catch(cause => cause)
    await vi.waitFor(() => expect(mocks.discover).toHaveBeenCalledOnce())
    deadline.abort()
    expect(await result).toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(AbortSignal.timeout).toHaveBeenCalledWith(30_000)
    expect(mocks.store).toHaveBeenCalledWith('owner', id, { credentialVersion: 2,
      epoch: claim.epoch, errorCode: 'AI_PROVIDER_UNREACHABLE' })
  })

  it('releases a claimed lease if the caller cancels while the claim is acquired', async () => {
    const caller = new AbortController()
    mocks.claim.mockImplementation(async () => { caller.abort(); return claim })
    await expect(refreshProviderCatalog('owner', id, { signal: caller.signal }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.load).not.toHaveBeenCalled()
    expect(mocks.discover).not.toHaveBeenCalled()
    expect(mocks.store).toHaveBeenCalledWith('owner', id,
      { credentialVersion: 2, epoch: claim.epoch, errorCode: 'AI_EXECUTION_FAILED' })
  })

  it.each(['openai', 'anthropic', 'google', 'openrouter'] as const)('uses only authenticated GET catalogue requests for %s', async providerId => {
    const actual = await vi.importActual<typeof import('../providers')>('../providers')
    mocks.claim.mockResolvedValue({ ...claim, providerId })
    mocks.discover.mockImplementation(actual.discoverConnectionModels)
    const http = vi.fn().mockImplementation(async () => Response.json(providerId === 'google'
      ? { models: [{ name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'] }] }
      : providerId === 'anthropic' ? { data: [{ id: 'claude-haiku-4-5' }], has_more: false }
        : providerId === 'openrouter' ? { data: [{ id: 'openai/gpt-4.1', architecture: { output_modalities: ['text'] } }] }
          : { data: [{ id: 'gpt-4.1' }] }))
    vi.stubGlobal('fetch', http)
    expect(await refreshProviderCatalog('owner', id)).toEqual({ status: 'refreshed', modelCount: 1 })
    expect(http).toHaveBeenCalledOnce()
    expect(http.mock.calls[0][1]).toMatchObject({ method: 'GET' })
    expect(http.mock.calls[0][1].body).toBeUndefined()
    expect(String(http.mock.calls[0][0])).toContain('/models')
    expect(mocks.probe).not.toHaveBeenCalled()
  })

  it('passes refreshed Anthropic advertised effort levels through to persistence', async () => {
    const actual = await vi.importActual<typeof import('../providers')>('../providers')
    mocks.claim.mockResolvedValue({ ...claim, providerId: 'anthropic' })
    mocks.discover.mockImplementation(actual.discoverConnectionModels)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ data: [{ id: 'claude-new-model',
      capabilities: { effort: { high: { supported: true }, max: { supported: true } } } }], has_more: false })))
    expect(await refreshProviderCatalog('owner', id)).toEqual({ status: 'refreshed', modelCount: 1 })
    expect(mocks.store.mock.calls[0][2].models[0]).toMatchObject({ modelId: 'claude-new-model',
      supportedEfforts: ['high', 'max'], defaultEffort: null })
  })
})
