import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../../errors'

const mocks = vi.hoisted(() => ({ claim: vi.fn(), finish: vi.fn(), validate: vi.fn() }))
vi.mock('../../repository', () => ({ claimCliCatalogRefresh: mocks.claim, finishCliCatalogRefresh: mocks.finish }))
vi.mock('../validation', () => ({ validateCli: mocks.validate }))
import { refreshCliCatalog } from '../refresh'

const result = { cliId: 'codex', productName: 'Codex CLI', state: 'reachable',
  detectedVersion: '0.155.1', modelCount: 7 }

beforeEach(() => {
  vi.resetAllMocks()
  mocks.claim.mockResolvedValue('lease-42')
  mocks.finish.mockResolvedValue(true)
  mocks.validate.mockResolvedValue(result)
})
afterEach(() => { vi.restoreAllMocks() })

describe('CLI catalogue metadata refresh', () => {
  it('uses the authenticated user and metadata-only validation, then completes its lease', async () => {
    const caller = new AbortController()
    expect(await refreshCliCatalog('owner', 'codex', { force: true, signal: caller.signal }))
      .toEqual({ status: 'refreshed', ...result })
    expect(mocks.claim).toHaveBeenCalledWith('owner', 'codex', true)
    expect(mocks.validate).toHaveBeenCalledWith('owner', 'codex', expect.any(AbortSignal), { metadataOnly: true })
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', undefined)
  })

  it('skips fresh, cooling-down, or leased inventories before contacting a CLI', async () => {
    mocks.claim.mockResolvedValue(null)
    expect(await refreshCliCatalog('owner', 'codex')).toEqual({ status: 'skipped' })
    expect(mocks.claim).toHaveBeenCalledWith('owner', 'codex', false)
    expect(mocks.validate).not.toHaveBeenCalled()
    expect(mocks.finish).not.toHaveBeenCalled()
  })

  it('checks caller cancellation before claiming a lease', async () => {
    const caller = new AbortController(); caller.abort()
    await expect(refreshCliCatalog('owner', 'codex', { signal: caller.signal }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.claim).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })

  it('releases an acquired lease with a safe error when a caller cancels discovery', async () => {
    const caller = new AbortController()
    mocks.validate.mockImplementation((_user, _cli, signal: AbortSignal) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(new AiConsoleError('AI_EXECUTION_FAILED')), { once: true })
    }))
    const refresh = refreshCliCatalog('owner', 'codex', { signal: caller.signal }).catch(error => error)
    await vi.waitFor(() => expect(mocks.validate).toHaveBeenCalledOnce())
    caller.abort()
    expect(await refresh).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', 'AI_EXECUTION_FAILED')
  })

  it('does not publish success after cancellation even if a CLI ignores its signal', async () => {
    const caller = new AbortController()
    mocks.validate.mockImplementation(async () => { caller.abort(); return result })
    await expect(refreshCliCatalog('owner', 'codex', { signal: caller.signal }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', 'AI_EXECUTION_FAILED')
  })

  it('classifies its total deadline as a retryable CLI timeout and releases the lease', async () => {
    const deadline = new AbortController()
    vi.spyOn(AbortSignal, 'timeout').mockReturnValue(deadline.signal)
    mocks.validate.mockImplementation((_user, _cli, signal: AbortSignal) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(new Error('private-timeout-details')), { once: true })
    }))
    const refresh = refreshCliCatalog('owner', 'codex').catch(error => error)
    await vi.waitFor(() => expect(mocks.validate).toHaveBeenCalledOnce())
    deadline.abort()
    const error = await refresh
    expect(error).toMatchObject({ code: 'AI_CLI_TIMEOUT' })
    expect(String(error)).not.toContain('private-timeout-details')
    expect(AbortSignal.timeout).toHaveBeenCalledWith(60_000)
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', 'AI_CLI_TIMEOUT')
  })

  it('stores discovery failures separately while preserving a reachable installation', async () => {
    mocks.validate.mockResolvedValue({ ...result, errorCode: 'AI_CLI_TIMEOUT' })
    expect(await refreshCliCatalog('owner', 'codex')).toMatchObject({
      status: 'refreshed', state: 'reachable', errorCode: 'AI_CLI_TIMEOUT',
    })
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', 'AI_CLI_TIMEOUT')
  })

  it('normalizes private discovery errors before storing and returning them', async () => {
    mocks.validate.mockRejectedValue(new Error('private-provider-or-account-content'))
    const error = await refreshCliCatalog('owner', 'codex').catch(cause => cause)
    expect(error).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(String(error)).not.toContain('private-provider-or-account-content')
    expect(mocks.finish).toHaveBeenCalledExactlyOnceWith('codex', 'lease-42', 'AI_EXECUTION_FAILED')
  })

  it('does not repeat completion writes for a superseded lease', async () => {
    mocks.finish.mockResolvedValue(false)
    await expect(refreshCliCatalog('owner', 'codex')).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.finish).toHaveBeenCalledOnce()
  })

  it('returns a safe failure if releasing its lease fails', async () => {
    mocks.validate.mockRejectedValue(new AiConsoleError('AI_CLI_UNREACHABLE'))
    mocks.finish.mockRejectedValue(new Error('private-database-details'))
    const error = await refreshCliCatalog('owner', 'codex').catch(cause => cause)
    expect(error).toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    expect(String(error)).not.toContain('private-database-details')
  })

  it('never contacts a CLI or completes an unacquired lease when access is denied', async () => {
    mocks.claim.mockRejectedValue(new AiConsoleError('AI_CLI_NOT_GRANTED'))
    await expect(refreshCliCatalog('owner', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(mocks.validate).not.toHaveBeenCalled()
    expect(mocks.finish).not.toHaveBeenCalled()
  })
})
