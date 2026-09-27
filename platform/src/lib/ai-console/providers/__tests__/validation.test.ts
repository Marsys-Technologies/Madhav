import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import { encryptCredential } from '../../crypto'
import * as validation from '../../validation'
import * as revalidation from '../../revalidation'
import { createConnectionRuntimeBinding, discoverConnectionModels } from '../index'
import type { ProviderId } from '../../types'

// Real crypto/repository/adapters; only database and HTTP transports are replaced.
const execute = vi.fn()
const http = vi.fn()
const id = '00000000-0000-4000-8000-000000000001'
const key = 'test-user-owned-secret-1234'
let active = true
let deleted = false
let provider: ProviderId = 'openai'
let version = 1
let state = 'untested'
let validity = 'unknown'
let availableModels = new Set(['gpt-4.1', 'gpt-4.1-mini'])
let claimed: Record<string, unknown>[] = []
let maxConcurrent = 0
let concurrent = 0
beforeEach(() => {
  vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', 'test')
  vi.stubEnv('MARSYS_AI_KEK_test', Buffer.alloc(32, 1).toString('base64'))
  vi.stubEnv('MARSYS_AI_FINGERPRINT_SECRET', Buffer.alloc(32, 2).toString('base64'))
  const e = encryptCredential(key)
  active = true; deleted = false; provider = 'openai'; version = 1; state = 'untested'; validity = 'unknown';
  availableModels = new Set(['gpt-4.1', 'gpt-4.1-mini']); claimed = []; concurrent = 0; maxConcurrent = 0
  execute.mockReset().mockImplementation(async (sql: string, params: unknown[] = []) => {
    let rows: Record<string, unknown>[] = []
    if (sql.includes('SKIP LOCKED')) { rows = claimed; claimed = [] }
    else if (sql.includes('SELECT c.id FROM ai_provider_connections c')) {
      const exactModelAllowed = !sql.includes('ai_connection_models') || (validity !== 'invalid' && availableModels.has(String(params[4])))
      if (active && !deleted && exactModelAllowed && params[0] === 'alice' && params[1] === id && params[2] === provider && params[3] === version) rows = [{ id }]
    }
    else if (sql.includes('SELECT c.credential_ciphertext')) {
      const runtime = sql.includes('ai_connection_models')
      const exactAllowed = !runtime || (params[2] === provider && validity !== 'invalid' && availableModels.has(String(params[4])))
      const requestedVersion = runtime ? params[3] : params[2]
      if (active && !deleted && exactAllowed && params[0] === 'alice' && params[1] === id && requestedVersion === version) rows = [{ credential_ciphertext: e.ciphertext, credential_nonce: e.nonce, credential_tag: e.authTag, wrapped_dek: e.wrappedDataKey, wrap_nonce: e.wrapNonce, wrap_tag: e.wrapAuthTag, kek_version: e.keyVersion, masked_suffix: e.mask, keyed_fingerprint: e.fingerprint }]
    } else if (sql.includes('FROM ai_provider_connections') && sql.trim().startsWith('SELECT') && params[0] === 'alice') {
      rows = [{ id, provider_id: provider, credential_version: version, validation_state: state, credential_validity: validity, deleted_at: deleted ? '2026-09-27' : null }]
    } else if (sql.startsWith('UPDATE ai_provider_connections SET validation_state')) {
      state = String(params[2]); validity = String(params[3])
    }
    return { rows, rowCount: rows.length }
  });
  (globalThis as typeof globalThis & { __pgPool?: Pool }).__pgPool = { query: execute, connect: async () => ({ query: execute, release() {} }) } as unknown as Pool
  http.mockReset().mockImplementation(async (_url, init) => {
    concurrent++; maxConcurrent = Math.max(maxConcurrent, concurrent)
    await new Promise(resolve => setTimeout(resolve, 1)); concurrent--
    return Response.json(init.method === 'GET' ? { data: [{ id: 'gpt-4.1' }, { id: 'gpt-4.1-mini' }] } : { choices: [{ message: { content: 'never persist this' } }], usage: { prompt_tokens: 3, completion_tokens: 1 } })
  })
  vi.stubGlobal('fetch', http)
})
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.useRealTimers(); vi.restoreAllMocks() })
const writes = () => execute.mock.calls.filter(([sql]) => String(sql).startsWith('UPDATE ai_provider_connections SET validation_state')).map(([, params]) => params)
describe('owned validation state flow', () => {
  it.each(['disabled', 'deleted', 'replaced'] as const)('blocks every paginated request after the connection is %s', async change => {
    for (const source of ['anthropic', 'google', 'openrouter'] as const) {
      active = true; deleted = false; version = 1; provider = source
      http.mockReset().mockImplementation(async () => {
        if (change === 'disabled') active = false
        if (change === 'deleted') deleted = true
        if (change === 'replaced') version = 2
        return Response.json(source === 'anthropic' ? { data: [{ id: 'claude-haiku-4-5' }], has_more: true, last_id: 'claude-haiku-4-5' }
          : source === 'google' ? { models: [{ name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'] }], nextPageToken: 'page-two' }
            : { data: Array.from({ length: 500 }, () => ({ id: 'vendor/text', architecture: { output_modalities: ['text'] } })) })
      })
      await expect(discoverConnectionModels({ userId: 'alice', connectionId: id, providerId: source, credentialVersion: 1 }, new AbortController().signal)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
      expect(http).toHaveBeenCalledTimes(1)
    }
  })
  it.each(['disabled', 'deleted', 'replaced'] as const)('blocks extracted runtime models after the connection is %s', async change => {
    const binding = await createConnectionRuntimeBinding({ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 1 }, { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer'], supportsTools: true, supportsStructuredOutput: true })
    const model = binding.model
    if (change === 'disabled') active = false
    if (change === 'deleted') deleted = true
    if (change === 'replaced') version = 2
    await expect(model.doGenerate({ prompt: [] })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).not.toHaveBeenCalled(); binding.dispose()
  })
  it('cancels during the initial validating write with zero HTTP and no false health verdict', async () => {
    const controller = new AbortController()
    let entered!: () => void; let release!: () => void
    const barrier = new Promise<void>(resolve => { release = resolve })
    const writing = new Promise<void>(resolve => { entered = resolve })
    const transport = execute.getMockImplementation()!
    execute.mockImplementation(async (sql: string, params: unknown[]) => {
      if (sql.startsWith('UPDATE ai_provider_connections SET validation_state') && params[2] === 'validating') { entered(); await barrier }
      return transport(sql, params)
    })
    const pending = validation.validateConnection('alice', id, { signal: controller.signal }).catch(e => e)
    await writing; controller.abort('private-cancellation-reason'); release()
    expect(await pending).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(http).not.toHaveBeenCalled()
    expect(writes().map(p => p[2])).toEqual(['validating'])
  })
  it('does not misclassify caller cancellation during discovery as provider health', async () => {
    const controller = new AbortController()
    http.mockImplementation(async () => { controller.abort(); throw new Error('cancelled') })
    await expect(validation.validateConnection('alice', id, { signal: controller.signal })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(writes().map(p => p[2])).toEqual(['validating'])
  })
  it('retains unreachable semantics for the total validation deadline across slow pages', async () => {
    vi.useFakeTimers(); provider = 'anthropic'; validity = 'valid'
    let page = 0
    http.mockImplementation(async () => {
      page++
      await new Promise(resolve => setTimeout(resolve, 10_000))
      return Response.json({ data: [{ id: 'claude-haiku-4-5' }], has_more: true, last_id: `claude-cursor-${page}` })
    })
    const pending = validation.validateConnection('alice', id)
    await vi.advanceTimersByTimeAsync(30_001)
    expect(await pending).toMatchObject({ state: 'unreachable', error: { code: 'AI_PROVIDER_UNREACHABLE' } })
    expect(writes().map(p => p[2])).toEqual(['validating', 'unreachable'])
    expect(validity).toBe('valid'); expect(http).toHaveBeenCalledTimes(3)
  })
  it('requires discovery plus one tiny cheap-model probe, projects only catalog metadata', async () => {
    const result = await validation.validateConnection('alice', id)
    expect(result).toEqual({ state: 'validated', modelCount: 2 })
    expect(writes().map(p => p[2])).toEqual(['validating', 'validated'])
    expect(validity).toBe('valid')
    expect(http).toHaveBeenCalledTimes(2)
    expect(JSON.parse(http.mock.calls[1][1].body).model).toBe('gpt-4.1-mini')
    expect(JSON.stringify([result, execute.mock.calls.filter(([sql]) => !String(sql).includes('SELECT c.credential'))])).not.toContain(key)
    expect(JSON.stringify(execute.mock.calls)).not.toContain('never persist this')
  })
  it('does not probe an empty compatible catalog or mark it validated', async () => {
    http.mockResolvedValue(Response.json({ data: [{ id: 'text-embedding-3-small' }] }))
    expect(await validation.validateConnection('alice', id)).toMatchObject({ state: 'needs_attention', modelCount: 0, error: { code: 'AI_MODEL_UNAVAILABLE' } })
    expect(http).toHaveBeenCalledTimes(1)
    expect(writes().at(-1)[2]).toBe('needs_attention')
  })
  it.each([[401, 'invalid', 'invalid'], [403, 'needs_attention', 'valid'], [402, 'needs_attention', 'valid'], [404, 'needs_attention', 'valid'], [429, 'unreachable', 'valid'], [503, 'unreachable', 'valid']] as const)('classifies probe HTTP %s without losing established validity or trying fallback', async (status, expectedState, expectedValidity) => {
    validity = 'valid'
    http.mockImplementation(async (_url, init) => init.method === 'GET' ? Response.json({ data: [{ id: 'gpt-4.1-mini' }, { id: 'gpt-4.1' }] }) : Response.json({ secret: key }, { status }))
    const result = await validation.validateConnection('alice', id)
    expect(result.state).toBe(expectedState); expect(validity).toBe(expectedValidity)
    expect(http).toHaveBeenCalledTimes(2)
    expect(JSON.stringify(result)).not.toContain(key)
  })
  it('rejects foreign or disabled users and mismatched claimed versions before HTTP', async () => {
    await expect(validation.validateConnection('mallory', id)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    active = false
    await expect(validation.validateConnection('alice', id)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    active = true
    await expect(validation.validateConnection('alice', id, { credentialVersion: 2 })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).not.toHaveBeenCalled()
  })
  it('does not probe or persist a stale result when the key is replaced during discovery', async () => {
    http.mockImplementation(async () => { version = 2; return Response.json({ data: [{ id: 'gpt-4.1' }] }) })
    await expect(validation.validateConnection('alice', id)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).toHaveBeenCalledTimes(1)
    expect(writes().map(p => p[2])).toEqual(['validating'])
  })
  it('does not decrypt or send a connection credential to a different provider', async () => {
    await expect(discoverConnectionModels({ userId: 'alice', connectionId: id, providerId: 'deepseek', credentialVersion: 1 }, new AbortController().signal)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).not.toHaveBeenCalled()
  })
  it('creates an owned request-only runtime binding and rejects stale versions before exposing a model', async () => {
    const connection = { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 1 }
    const model = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer' as const], supportsTools: true, supportsStructuredOutput: true }
    const binding = await createConnectionRuntimeBinding(connection, model)
    expect(() => JSON.stringify(binding)).toThrow()
    binding.dispose(); version = 2
    await expect(createConnectionRuntimeBinding(connection, model)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).not.toHaveBeenCalled()
  })
  it('uses one atomic exact-model credential read when creating a runtime binding', async () => {
    const connection = { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 1 }
    const model = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer' as const], supportsTools: true, supportsStructuredOutput: true }
    const binding = await createConnectionRuntimeBinding(connection, model)
    const initialReads = execute.mock.calls.filter(([sql]) => String(sql).includes('ai_provider_connections'))
    expect(initialReads).toHaveLength(1)
    expect(String(initialReads[0][0])).toContain('SELECT c.credential_ciphertext')
    expect(String(initialReads[0][0])).toContain('ai_connection_models')
    expect(initialReads[0][1]).toEqual(['alice', id, 'openai', 1, 'gpt-4.1-mini'])
    binding.dispose()
  })
  it('rejects a removed exact runtime model before decrypting and on every outbound preflight', async () => {
    const connection = { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 1 }
    const model = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer' as const], supportsTools: true, supportsStructuredOutput: true }
    availableModels.clear()
    await expect(createConnectionRuntimeBinding(connection, model)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(execute.mock.calls.filter(([sql]) => String(sql).includes('SELECT c.credential_ciphertext'))).toHaveLength(1)
    availableModels.add(model.modelId)
    const binding = await createConnectionRuntimeBinding(connection, model)
    availableModels.clear()
    await expect(binding.model.doGenerate({ prompt: [] })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(http).not.toHaveBeenCalled()
    binding.dispose()
  })
  it('rejects a confirmed-invalid runtime credential before decrypting even when the exact model remains available', async () => {
    validity = 'invalid'
    const connection = { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 1 }
    const model = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer' as const], supportsTools: true, supportsStructuredOutput: true }
    await expect(createConnectionRuntimeBinding(connection, model)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(execute.mock.calls.filter(([sql]) => String(sql).includes('SELECT c.credential_ciphertext'))).toHaveLength(1)
    expect(http).not.toHaveBeenCalled()
  })
  it('preserves connection-only authorization for discovery before a model catalog exists', async () => {
    availableModels.clear()
    await expect(discoverConnectionModels({ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 1 },
      new AbortController().signal)).resolves.toHaveLength(2)
    expect(http).toHaveBeenCalledOnce()
  })
})
describe('conservative stale revalidation', () => {
  it('uses an aged recoverable lease and at most two simultaneous validations', async () => {
    vi.spyOn(Date, 'now').mockReturnValue(1_800_000_000_000)
    claimed = Array.from({ length: 5 }, () => ({ user_id: 'alice', id, provider_id: 'openai', credential_version: 1 }))
    const started = Date.now()
    expect(await revalidation.revalidateStaleConnections()).toEqual({ checked: 5, validated: 5, needsAttention: 0, unreachable: 0, invalid: 0, failed: 0 })
    expect(maxConcurrent).toBeLessThanOrEqual(2)
    const claim = execute.mock.calls.find(([sql]) => String(sql).includes('SKIP LOCKED'))!
    expect(claim[1][1]).toBeLessThanOrEqual(5)
    expect(claim[1][0].getTime()).toBeLessThanOrEqual(started - 86_400_000)
    expect(await revalidation.revalidateStaleConnections()).toEqual({ checked: 0, validated: 0, needsAttention: 0, unreachable: 0, invalid: 0, failed: 0 })
    expect(http).toHaveBeenCalledTimes(10)
  })
  it('does not validate replacement credentials from a stale claim', async () => {
    claimed = [{ user_id: 'alice', id, provider_id: 'openai', credential_version: 2 }]
    expect(await revalidation.revalidateStaleConnections()).toMatchObject({ checked: 1, failed: 1, validated: 0 })
    expect(http).not.toHaveBeenCalled()
  })
  it('marks only actionable exact runtime errors and returns no raw provider details', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('RETURNING') ? [{ id }] : [] }))
    const connection = { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 1 }
    expect(await revalidation.markRuntimeConnectionFailure(connection, { status: 404, body: key })).toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    const update = execute.mock.calls.find(([sql]) => String(sql).includes('UPDATE ai_provider_connections'))!
    expect(update[1]).toEqual(['alice', id, 1, 'needs_attention', 'AI_MODEL_UNAVAILABLE'])
    expect(JSON.stringify(execute.mock.calls)).not.toContain(key)
    execute.mockClear()
    expect(await revalidation.markRuntimeConnectionFailure(connection, new Error(key))).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(execute).not.toHaveBeenCalled()
  })
})
