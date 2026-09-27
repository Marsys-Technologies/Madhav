import { beforeEach, describe, expect, it, vi } from 'vitest'
import { randomUUID } from 'node:crypto'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { AI_ROLES } from '@/lib/ai-console/types'

const mocks = vi.hoisted(() => ({
  auth: vi.fn(), flag: vi.fn(), encrypt: vi.fn(), validate: vi.fn(),
  listAiConsoleState: vi.fn(), createConnection: vi.fn(), renameConnection: vi.fn(),
  replaceConnectionCredential: vi.fn(), saveConfiguration: vi.fn(), duplicateConfiguration: vi.fn(),
  previewChoiceDependencies: vi.fn(), deleteConnection: vi.fn(), deleteConfiguration: vi.fn(), setUserDefault: vi.fn(),
}))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/crypto', () => ({ encryptCredential: mocks.encrypt }))
vi.mock('@/lib/ai-console/validation', () => ({ validateConnection: mocks.validate }))
vi.mock('@/lib/ai-console/repository', () => mocks)

import * as root from '../route'
import * as connections from '../connections/route'
import * as connection from '../connections/[id]/route'
import * as validation from '../connections/[id]/validate/route'
import * as configurations from '../configurations/route'
import * as configuration from '../configurations/[id]/route'
import * as defaults from '../default/route'

const id = '11111111-1111-4111-8111-111111111111'
const configId = '22222222-2222-4222-8222-222222222222'
const context = (value = id) => ({ params: Promise.resolve({ id: value }) })
const target = { kind: 'provider_model' as const, connectionId: id, modelId: 'test-model' }
const roles = Object.fromEntries(AI_ROLES.map(role => [role, target]))
const safeConnection = { id, providerId: 'openai', name: 'Personal', maskedSuffix: '••••abcd', validationState: 'untested' }
const row = { id, provider_id: 'openai', name: 'Personal', masked_suffix: '••••abcd', validation_state: 'validated',
  credential_version: 2, deleted_at: null, last_validated_at: null, last_checked_at: null, last_error_code: null }
const makeState = () => ({ connections: [{ ...row }],
  models: [{ connection_id: id, model_id: 'test-model', display_name: 'Test model', compatible_roles: [...AI_ROLES], available: true }],
  configurations: [{ id: configId, name: 'Four roles', version: 3, deleted_at: null }],
  roles: AI_ROLES.map(role => ({ configuration_id: configId, role, kind: target.kind, connection_id: id, model_id: target.modelId, cli_id: null })),
  defaultChoice: { kind: 'custom_configuration', configurationId: configId }, clis: [], cliModels: [],
})
const request = (method: string, body?: unknown) => new Request('http://localhost/api/ai-console', {
  method, headers: { 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }),
})

beforeEach(() => {
  vi.resetAllMocks()
  mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { id: 'owner', status: 'active', role: 'guest' } })
  mocks.flag.mockReturnValue(true)
  mocks.listAiConsoleState.mockResolvedValue(makeState())
  mocks.encrypt.mockReturnValue({ ciphertext: Buffer.from('test-only-ciphertext'), mask: '••••abcd' })
  mocks.createConnection.mockResolvedValue(safeConnection)
  mocks.renameConnection.mockResolvedValue({ ...safeConnection, name: 'Renamed' })
  mocks.replaceConnectionCredential.mockResolvedValue({ connection: safeConnection, credentialVersion: 4 })
  mocks.validate.mockResolvedValue({ state: 'validated', modelCount: 1 })
  mocks.saveConfiguration.mockResolvedValue({ id: configId, name: 'Four roles', version: 4, roles })
  mocks.duplicateConfiguration.mockResolvedValue({ id: configId, name: 'Copy', version: 1, roles })
  mocks.previewChoiceDependencies.mockResolvedValue({ configurations: [{ id: configId, name: 'Four roles' }],
    defaultAffected: true, conversations: [{ conversation_id: '33333333-3333-4333-8333-333333333333' }] })
})

describe('AI Console safe API contracts', () => {
  it('declares every route dynamic and disables caching for successful responses', async () => {
    for (const route of [root, connections, connection, validation, configurations, configuration, defaults]) {
      expect(route.dynamic).toBe('force-dynamic')
    }
    const response = await root.GET()
    expect(response.headers.get('Cache-Control')).toBe('no-store')
  })

  it('projects aggregate data and keeps broken identities visible without secret-bearing extras', async () => {
    const sentinel = randomUUID()
    const state = makeState()
    Object.assign(state.connections[0], { ciphertext: sentinel, keyed_fingerprint: sentinel, apiKey: sentinel, deleted_at: '2026-09-27T00:00:00Z' })
    Object.assign(state.models[0], { upstream_body: sentinel })
    Object.assign(state.configurations[0], { secret: sentinel })
    Object.assign(state.roles[0], { secret: sentinel })
    mocks.listAiConsoleState.mockResolvedValue(state)
    const response = await root.GET()
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(body.connections[0]).toMatchObject({ id, maskedSuffix: '••••abcd', deletedAt: '2026-09-27T00:00:00Z' })
    expect(body.defaultChoice).toEqual(state.defaultChoice)
    expect(body.configurations[0].roles).toEqual(roles)
    expect(body.validationDisclosure).toMatch(/tiny.*provider charge/i)
    expect(JSON.stringify(body)).not.toContain(sentinel)
    expect(JSON.stringify(body)).not.toMatch(/credential_version|ciphertext|fingerprint|apiKey/)
  })

  it('lists connections and configurations using the same safe shape', async () => {
    expect((await (await connections.GET()).json()).connections[0]).toMatchObject({ id, providerId: 'openai' })
    expect((await (await configurations.GET()).json()).configurations[0]).toMatchObject({ id: configId, version: 3, roles })
  })

  it('redacts CLI host metadata and models for ungranted or revoked users', async () => {
    const state = makeState()
    const sentinel = randomUUID()
    mocks.listAiConsoleState.mockResolvedValue({ ...state,
      clis: [{ cli_id: 'codex', granted_at: null, revoked_at: null, detected_product: sentinel,
        detected_version: sentinel, validation_state: sentinel, last_checked_at: null }],
      cliModels: [{ cli_id: 'codex', model_id: sentinel, display_name: sentinel, compatible_roles: [...AI_ROLES], available: true, is_builtin_default: true }],
    })
    const response = await root.GET()
    const body = await response.json()
    expect(body.clis).toEqual([{ cliId: 'codex', granted: false, detectedProduct: null, detectedVersion: null, validationState: null, lastCheckedAt: null }])
    expect(body.cliModels).toEqual([])
    expect(JSON.stringify(body)).not.toContain(sentinel)
  })

  it('encrypts before persistence, never sends plaintext metadata, then automatically validates', async () => {
    const apiKey = randomUUID()
    const response = await connections.POST(request('POST', { name: ' Personal ', providerId: 'openai', apiKey, acknowledgeCharge: true }))
    expect(response.status).toBe(201)
    expect(mocks.encrypt).toHaveBeenCalledWith(apiKey)
    expect(mocks.createConnection).toHaveBeenCalledWith('owner', { name: 'Personal', providerId: 'openai' }, mocks.encrypt.mock.results[0].value)
    expect(mocks.encrypt.mock.invocationCallOrder[0]).toBeLessThan(mocks.createConnection.mock.invocationCallOrder[0])
    expect(mocks.createConnection.mock.invocationCallOrder[0]).toBeLessThan(mocks.validate.mock.invocationCallOrder[0])
    expect(mocks.validate).toHaveBeenCalledWith('owner', id, expect.objectContaining({ credentialVersion: 1, signal: expect.any(AbortSignal) }))
    const body = await response.json()
    expect(body.connection.validationState).toBe('validated')
    expect(body.validation).toEqual({ state: 'validated', modelCount: 1 })
    expect(JSON.stringify(body)).not.toContain(apiKey)
    expect(mocks.setUserDefault).not.toHaveBeenCalled()
  })

  it.each(['invalid', 'unreachable', 'needs_attention'] as const)('returns the saved connection with honest %s validation', async state => {
    mocks.validate.mockResolvedValue({ state, modelCount: 0, error: new AiConsoleError('AI_PROVIDER_UNREACHABLE').toJSON() })
    const response = await connections.POST(request('POST', { name: 'Personal', providerId: 'openai', apiKey: randomUUID(), acknowledgeCharge: true }))
    expect(response.status).toBe(201)
    expect((await response.json()).connection.validationState).toBe(state)
    expect(mocks.deleteConnection).not.toHaveBeenCalled()
  })

  it.each([
    { name: 'Personal', providerId: 'other', apiKey: 'test-only', acknowledgeCharge: true },
    { name: 'Personal', providerId: 'openai', apiKey: '', acknowledgeCharge: true },
    { name: 'Personal', providerId: 'openai', apiKey: 'test\nonly', acknowledgeCharge: true },
    { name: 'Personal', providerId: 'openai', apiKey: 'test-only' },
    { name: 'Personal', providerId: 'openai', apiKey: 'test-only', acknowledgeCharge: false },
    { name: 'Personal', providerId: 'openai', apiKey: 'test-only', acknowledgeCharge: true, userId: 'other' },
    { name: 'Personal', providerId: 'openai', apiKey: 'test-only', acknowledgeCharge: true, baseUrl: 'https://example.invalid' },
  ])('rejects invalid create input without encrypting or persisting', async body => {
    const response = await connections.POST(request('POST', body))
    expect(response.status).toBe(400)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(mocks.encrypt).not.toHaveBeenCalled()
    expect(mocks.createConnection).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })

  it('rejects malformed JSON without returning parser input', async () => {
    const sentinel = randomUUID()
    const response = await connections.POST(new Request('http://localhost', { method: 'POST', body: sentinel }))
    expect(response.status).toBe(400)
    expect(await response.text()).not.toContain(sentinel)
  })

  it('renames without charge acknowledgement or validation', async () => {
    const response = await connection.PATCH(request('PATCH', { name: 'Renamed' }), context())
    expect(response.status).toBe(200)
    expect(mocks.renameConnection).toHaveBeenCalledWith('owner', id, 'Renamed')
    expect(mocks.encrypt).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })

  it('replaces a key and validates exactly the returned credential version', async () => {
    const apiKey = randomUUID()
    const req = request('PATCH', { apiKey, acknowledgeCharge: true })
    const response = await connection.PATCH(req, context())
    expect(response.status).toBe(200)
    expect(mocks.replaceConnectionCredential).toHaveBeenCalledWith('owner', id, mocks.encrypt.mock.results[0].value)
    expect(mocks.validate).toHaveBeenCalledWith('owner', id, { credentialVersion: 4, signal: req.signal })
    expect(await response.text()).not.toContain(apiKey)
  })

  it('rejects combined rename and replacement before any mutation', async () => {
    const response = await connection.PATCH(request('PATCH', { name: 'Renamed', apiKey: randomUUID(), acknowledgeCharge: true }), context())
    expect(response.status).toBe(400)
    expect(mocks.encrypt).not.toHaveBeenCalled()
    expect(mocks.renameConnection).not.toHaveBeenCalled()
    expect(mocks.replaceConnectionCredential).not.toHaveBeenCalled()
    expect(mocks.validate).not.toHaveBeenCalled()
  })

  it.each([{}, { acknowledgeCharge: true }, { name: 'Renamed', acknowledgeCharge: true }, { apiKey: 'test-only' }, { name: 'Renamed', providerId: 'anthropic' }])('rejects contradictory or unknown patch fields', async body => {
    expect((await connection.PATCH(request('PATCH', body), context())).status).toBe(400)
    expect(mocks.renameConnection).not.toHaveBeenCalled()
    expect(mocks.replaceConnectionCredential).not.toHaveBeenCalled()
  })

  it('discloses the charge before testing and requires explicit acknowledgement', async () => {
    const info = await validation.GET(request('GET'), context())
    expect((await info.json()).validationDisclosure).toMatch(/tiny.*provider charge/i)
    expect((await validation.POST(request('POST', {}), context())).status).toBe(400)
    expect(mocks.validate).not.toHaveBeenCalled()
    const req = request('POST', { acknowledgeCharge: true })
    expect((await validation.POST(req, context())).status).toBe(200)
    expect(mocks.validate).toHaveBeenCalledWith('owner', id, { credentialVersion: 2, signal: req.signal })
  })

  it.each(['connection', 'configuration'])('previews %s dependencies before confirmed tombstone deletion', async kind => {
    const endpoint = kind === 'connection' ? connection : configuration
    const itemId = kind === 'connection' ? id : configId
    const remove = kind === 'connection' ? mocks.deleteConnection : mocks.deleteConfiguration
    const preview = await endpoint.DELETE(request('DELETE'), context(itemId))
    expect(preview.status).toBe(409)
    expect(await preview.json()).toMatchObject({ error: 'confirmation_required', dependencies: { defaultAffected: true,
      configurations: [{ id: configId, name: 'Four roles' }], conversations: [{ conversationId: '33333333-3333-4333-8333-333333333333' }] } })
    expect(remove).not.toHaveBeenCalled()
    expect((await endpoint.DELETE(request('DELETE', { confirm: 'true' }), context(itemId))).status).toBe(400)
    const confirmed = await endpoint.DELETE(request('DELETE', { confirm: true }), context(itemId))
    expect(confirmed.status).toBe(200)
    expect(remove).toHaveBeenCalledWith('owner', itemId, true)
    expect(mocks.setUserDefault).not.toHaveBeenCalled()
    expect(mocks.saveConfiguration).not.toHaveBeenCalled()
  })

  it('creates and duplicates configurations with distinct strict shapes', async () => {
    expect((await configurations.POST(request('POST', { name: 'Four roles', roles }))).status).toBe(201)
    expect(mocks.saveConfiguration).toHaveBeenCalledWith('owner', { name: 'Four roles', roles })
    expect((await configurations.POST(request('POST', { name: 'Copy', duplicateFrom: configId }))).status).toBe(201)
    expect(mocks.duplicateConfiguration).toHaveBeenCalledWith('owner', configId, 'Copy')
    expect((await configurations.POST(request('POST', { name: 'Copy', duplicateFrom: configId, roles }))).status).toBe(400)
  })

  it('requires exactly four roles and performs a full version-checked atomic edit', async () => {
    expect((await configurations.POST(request('POST', { name: 'Invalid', roles: { planner: target } }))).status).toBe(400)
    expect((await configurations.POST(request('POST', { name: 'Invalid', roles: { ...roles, inspector: target } }))).status).toBe(400)
    expect((await configuration.PATCH(request('PATCH', { name: 'Four roles', roles }), context(configId))).status).toBe(400)
    expect((await configuration.PATCH(request('PATCH', { name: 'Four roles', expectedVersion: 3, roles }), context(configId))).status).toBe(200)
    expect(mocks.saveConfiguration).toHaveBeenCalledWith('owner', { id: configId, name: 'Four roles', expectedVersion: 3, roles })
  })

  it('reports a concurrent configuration edit as a conflict without retry or alternate save', async () => {
    mocks.saveConfiguration.mockRejectedValue(new AiConsoleError('AI_CHOICE_BROKEN'))
    const response = await configuration.PATCH(request('PATCH', { name: 'Four roles', expectedVersion: 3, roles }), context(configId))
    expect(response.status).toBe(409)
    expect(mocks.saveConfiguration).toHaveBeenCalledOnce()
  })

  it('rejects unknown fields on every mutation, including nested targets', async () => {
    for (const run of [
      () => validation.POST(request('POST', { acknowledgeCharge: true, prompt: 'override' }), context()),
      () => connection.DELETE(request('DELETE', { confirm: true, cascade: true }), context()),
      () => configuration.DELETE(request('DELETE', { confirm: true, cascade: true }), context(configId)),
      () => configurations.POST(request('POST', { name: 'Four roles', roles, expectedVersion: 1 })),
      () => configuration.PATCH(request('PATCH', { name: 'Four roles', roles, expectedVersion: 3, id: configId }), context(configId)),
      () => defaults.PUT(request('PUT', { choice: { ...target, providerId: 'openai' } })),
      () => configurations.POST(request('POST', { name: 'Four roles', roles: { ...roles, worker: { ...target, apiKey: 'untrusted' } } })),
    ]) expect((await run()).status).toBe(400)
    expect(mocks.validate).not.toHaveBeenCalled()
    expect(mocks.deleteConnection).not.toHaveBeenCalled()
    expect(mocks.deleteConfiguration).not.toHaveBeenCalled()
    expect(mocks.saveConfiguration).not.toHaveBeenCalled()
    expect(mocks.setUserDefault).not.toHaveBeenCalled()
  })

  it('drops unapproved success fields from mutation and validation results', async () => {
    const sentinel = randomUUID()
    mocks.createConnection.mockResolvedValue({ ...safeConnection, apiKey: sentinel, ciphertext: sentinel })
    mocks.validate.mockResolvedValue({ state: 'invalid', modelCount: 0, probeText: sentinel,
      error: { ...new AiConsoleError('AI_CONNECTION_INVALID').toJSON(), message: sentinel, cause: sentinel } })
    const response = await connections.POST(request('POST', { name: 'Personal', providerId: 'openai', apiKey: randomUUID(), acknowledgeCharge: true }))
    expect(response.status).toBe(201)
    expect(await response.text()).not.toContain(sentinel)
  })

  it('sets only an exact choice through the user-scoped transaction', async () => {
    expect((await defaults.PUT(request('PUT', { choice: target }))).status).toBe(200)
    expect(mocks.setUserDefault).toHaveBeenCalledWith('owner', target)
    expect((await defaults.PUT(request('PUT', { choice: { kind: 'provider_model', connectionId: id } }))).status).toBe(400)
    expect((await defaults.PUT(request('PUT', { choice: target, userId: 'other' }))).status).toBe(400)
  })

  it('rejects malformed reference IDs before they reach database-backed operations', async () => {
    const malformed = { ...target, connectionId: 'not-a-uuid' }
    expect((await defaults.PUT(request('PUT', { choice: malformed }))).status).toBe(400)
    expect((await defaults.PUT(request('PUT', { choice: { kind: 'custom_configuration', configurationId: 'not-a-uuid' } }))).status).toBe(400)
    expect((await configurations.POST(request('POST', { name: 'Four roles', roles: { ...roles, planner: malformed } }))).status).toBe(400)
    expect(mocks.setUserDefault).not.toHaveBeenCalled()
    expect(mocks.saveConfiguration).not.toHaveBeenCalled()
  })

  it.each([
    ['AI_CHOICE_BROKEN', 409], ['AI_CONNECTION_INVALID', 422], ['AI_ROLE_INCOMPATIBLE', 422],
    ['AI_CLI_NOT_GRANTED', 403], ['AI_PROVIDER_UNREACHABLE', 503], ['AI_RATE_LIMITED', 429],
  ] as const)('maps typed %s failures to %s without leaking attached causes', async (code, status) => {
    const sentinel = randomUUID()
    const error = new AiConsoleError(code)
    Object.assign(error, { cause: sentinel, upstream_body: sentinel })
    mocks.setUserDefault.mockRejectedValue(error)
    const response = await defaults.PUT(request('PUT', { choice: target }))
    expect(response.status).toBe(status)
    expect((await response.json()).error).toEqual(error.toJSON())
  })

  it('normalizes uniqueness errors and hides unexpected crypto/database messages', async () => {
    const sentinel = randomUUID()
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    mocks.createConnection.mockRejectedValue({ code: '23505', detail: sentinel })
    const body = { name: 'Personal', providerId: 'openai', apiKey: sentinel, acknowledgeCharge: true }
    const conflict = await connections.POST(request('POST', body))
    expect(conflict.status).toBe(409)
    expect(await conflict.text()).not.toContain(sentinel)
    mocks.encrypt.mockImplementation(() => { throw new Error(sentinel) })
    const failure = await connections.POST(request('POST', body))
    expect(failure.status).toBe(500)
    expect(await failure.text()).not.toContain(sentinel)
    expect(log).not.toHaveBeenCalled()
    log.mockRestore()
  })
})
