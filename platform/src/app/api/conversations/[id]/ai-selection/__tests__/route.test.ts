import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '@/lib/ai-console/errors'

const OWNER = 'owner-1'
const CONVERSATION_ID = '11111111-1111-4111-8111-111111111111'
const CONNECTION_ID = '22222222-2222-4222-8222-222222222222'
const SECOND_CONNECTION_ID = '33333333-3333-4333-8333-333333333333'
const CONFIGURATION_ID = '44444444-4444-4444-8444-444444444444'

const mocks = vi.hoisted(() => ({
  auth: vi.fn(),
  flag: vi.fn(),
  getConversationSelection: vi.fn(),
  setConversationSelection: vi.fn(),
  listAiConsoleState: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/repository', () => ({
  getConversationSelection: mocks.getConversationSelection,
  setConversationSelection: mocks.setConversationSelection,
  listAiConsoleState: mocks.listAiConsoleState,
}))

import * as route from '../route'

const context = (id = CONVERSATION_ID) => ({ params: Promise.resolve({ id }) })
const request = (body: unknown) => new Request(`http://localhost/api/conversations/${CONVERSATION_ID}/ai-selection`, {
  method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
})

function state(defaultChoice: unknown = { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' }) {
  return {
    connections: [{
      id: CONNECTION_ID, provider_id: 'openai', name: 'Personal OpenAI', masked_suffix: '•••1234',
      validation_state: 'validated', credential_validity: 'valid', deleted_at: null,
      last_validated_at: null, last_checked_at: null, last_error_code: null,
    }],
    models: [{ connection_id: CONNECTION_ID, model_id: 'gpt-safe', display_name: 'GPT Safe',
      compatible_roles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supports_tools: false,
      supports_structured_output: true, available: true }],
    configurations: [], roles: [], defaultChoice, clis: [], cliModels: [],
  }
}

function stateWithAlternatives(defaultChoice: unknown = { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' }) {
  const base = state(defaultChoice)
  return {
    ...base,
    connections: [...base.connections, {
      id: SECOND_CONNECTION_ID, provider_id: 'anthropic', name: 'Personal Anthropic', masked_suffix: '•••5678',
      validation_state: 'validated', credential_validity: 'valid', deleted_at: null,
      last_validated_at: null, last_checked_at: null, last_error_code: null,
      encrypted_credential: 'must-never-leave-the-server',
    }],
    models: [...base.models, { connection_id: SECOND_CONNECTION_ID, model_id: 'claude-safe', display_name: 'Claude Safe',
      compatible_roles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supports_tools: false,
      supports_structured_output: true, available: true }],
    configurations: [{ id: CONFIGURATION_ID, name: 'Research quartet', version: 2, deleted_at: null }],
    roles: ['synthesizer', 'planner', 'deep_planner', 'worker'].map(role => ({
      configuration_id: CONFIGURATION_ID, role, kind: 'provider_model', connection_id: CONNECTION_ID,
      model_id: 'gpt-safe', cli_id: null,
    })),
  }
}

beforeEach(() => {
  vi.resetAllMocks()
  mocks.flag.mockReturnValue(true)
  mocks.auth.mockResolvedValue({ user: { uid: OWNER }, profile: { id: OWNER, status: 'active', role: 'guest' } })
  mocks.getConversationSelection.mockResolvedValue({ kind: 'default' })
  mocks.listAiConsoleState.mockResolvedValue(state())
})

describe('conversation AI selection route', () => {
  it('is flag-gated, authenticated, active-user only, and never grants super-admin cross-owner access', async () => {
    mocks.flag.mockReturnValue(false)
    expect((await route.GET(new Request('http://localhost'), context())).status).toBe(404)

    mocks.flag.mockReturnValue(true)
    mocks.auth.mockResolvedValue(null)
    expect((await route.GET(new Request('http://localhost'), context())).status).toBe(401)

    mocks.auth.mockResolvedValue({ user: { uid: OWNER }, profile: { id: OWNER, status: 'disabled', role: 'super_admin' } })
    expect((await route.GET(new Request('http://localhost'), context())).status).toBe(403)

    mocks.auth.mockResolvedValue({ user: { uid: OWNER }, profile: { id: OWNER, status: 'active', role: 'super_admin' } })
    mocks.getConversationSelection.mockRejectedValue(new AiConsoleError('AI_CHOICE_BROKEN'))
    expect((await route.GET(new Request('http://localhost'), context())).status).toBe(409)
    expect(mocks.getConversationSelection).toHaveBeenCalledWith(OWNER, CONVERSATION_ID)
  })

  it('rejects invalid IDs and strict malformed or extra-field bodies before persistence', async () => {
    expect((await route.GET(new Request('http://localhost'), context('not-a-uuid'))).status).toBe(400)
    expect((await route.PUT(request({ kind: 'default', providerId: 'untrusted' }), context())).status).toBe(400)
    expect((await route.PUT(request({ kind: 'explicit', choice: {
      kind: 'provider_model', connectionId: 'not-a-uuid', modelId: 'gpt-safe',
    } }), context())).status).toBe(400)
    expect(mocks.setConversationSelection).not.toHaveBeenCalled()
  })

  it('returns symbolic Default for a missing row with a live safe resolved label and no secrets', async () => {
    const response = await route.GET(new Request('http://localhost'), context())
    const body = await response.json()
    expect(response.status).toBe(200)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(body).toEqual({
      selection: { kind: 'default' }, availability: 'ready', label: 'Default',
      resolvedLabel: 'Personal OpenAI · GPT Safe', remediation: null,
    })
    expect(JSON.stringify(body)).not.toMatch(/credential|maskedSuffix|providerId/i)
  })

  it('keeps Default symbolic while its safe resolved label follows the current global default', async () => {
    mocks.listAiConsoleState
      .mockResolvedValueOnce(stateWithAlternatives())
      .mockResolvedValueOnce(stateWithAlternatives({ kind: 'provider_model', connectionId: SECOND_CONNECTION_ID, modelId: 'claude-safe' }))

    const first = await (await route.GET(new Request('http://localhost'), context())).json()
    const second = await (await route.GET(new Request('http://localhost'), context())).json()
    expect(first).toMatchObject({ selection: { kind: 'default' }, label: 'Default', resolvedLabel: 'Personal OpenAI · GPT Safe' })
    expect(second).toMatchObject({ selection: { kind: 'default' }, label: 'Default', resolvedLabel: 'Personal Anthropic · Claude Safe' })
  })

  it('persists the exact raw reference and returns a freshly projected view', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' } } as const
    mocks.getConversationSelection.mockResolvedValue(selection)
    const response = await route.PUT(request(selection), context())
    expect(response.status).toBe(200)
    expect(mocks.setConversationSelection).toHaveBeenCalledWith(OWNER, CONVERSATION_ID, selection)
    expect(mocks.getConversationSelection).toHaveBeenCalledWith(OWNER, CONVERSATION_ID)
    expect(await response.json()).toMatchObject({ selection, availability: 'ready', label: 'Personal OpenAI · GPT Safe' })
  })

  it('requires a usable global default even for a valid explicit choice', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' } } as const
    mocks.getConversationSelection.mockResolvedValue(selection)
    mocks.listAiConsoleState.mockResolvedValue(state(null))
    expect(await (await route.GET(new Request('http://localhost'), context())).json()).toMatchObject({
      selection, availability: 'default_required', remediation: 'Choose a default in AI Console before asking a question.',
    })
  })

  it('keeps a broken explicit identity visible with generic remediation', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'removed-model' } } as const
    mocks.getConversationSelection.mockResolvedValue(selection)
    expect(await (await route.GET(new Request('http://localhost'), context())).json()).toEqual({
      selection, availability: 'selection_broken', label: 'Personal OpenAI · removed-model', resolvedLabel: null,
      remediation: 'This AI choice is unavailable. Repair it in AI Console or choose another available option.',
    })
  })

  it('keeps an explicit model pinned while the global default changes', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' } } as const
    mocks.getConversationSelection.mockResolvedValue(selection)
    mocks.listAiConsoleState
      .mockResolvedValueOnce(stateWithAlternatives())
      .mockResolvedValueOnce(stateWithAlternatives({ kind: 'provider_model', connectionId: SECOND_CONNECTION_ID, modelId: 'claude-safe' }))

    const first = await (await route.GET(new Request('http://localhost'), context())).json()
    const second = await (await route.GET(new Request('http://localhost'), context())).json()
    expect(first).toMatchObject({ selection, availability: 'ready', label: 'Personal OpenAI · GPT Safe', resolvedLabel: null })
    expect(second).toMatchObject({ selection, availability: 'ready', label: 'Personal OpenAI · GPT Safe', resolvedLabel: null })
  })

  it('keeps a named configuration identity pinned while its safe name stays live', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'custom_configuration', configurationId: CONFIGURATION_ID } } as const
    mocks.getConversationSelection.mockResolvedValue(selection)
    const renamed = stateWithAlternatives()
    renamed.configurations[0].name = 'Research quartet v2'
    mocks.listAiConsoleState.mockResolvedValueOnce(stateWithAlternatives()).mockResolvedValueOnce(renamed)

    expect(await (await route.GET(new Request('http://localhost'), context())).json()).toMatchObject({
      selection, availability: 'ready', label: 'Research quartet',
    })
    expect(await (await route.GET(new Request('http://localhost'), context())).json()).toMatchObject({
      selection, availability: 'ready', label: 'Research quartet v2',
    })
  })

  it('keeps a broken symbolic default visible with safe remediation', async () => {
    const broken = state({ kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'removed-default' })
    mocks.listAiConsoleState.mockResolvedValue(broken)
    expect(await (await route.GET(new Request('http://localhost'), context())).json()).toEqual({
      selection: { kind: 'default' }, availability: 'selection_broken', label: 'Default',
      resolvedLabel: 'Personal OpenAI · removed-default',
      remediation: 'This AI choice is unavailable. Repair it in AI Console or choose another available option.',
    })
  })

  it('keeps a revoked CLI selection visible without host, auth, or model diagnostics', async () => {
    const selection = { kind: 'explicit', choice: { kind: 'local_cli', cliId: 'codex', modelId: 'gpt-5' } } as const
    const revoked = { ...state(), clis: [{ cli_id: 'codex', granted_at: '2026-09-27T00:00:00Z', revoked_at: '2026-09-27T01:00:00Z',
      detected_product: 'sensitive-host-product', detected_version: '/sensitive/auth/path', validation_state: 'auth_unavailable', last_checked_at: null }] }
    mocks.getConversationSelection.mockResolvedValue(selection)
    mocks.listAiConsoleState.mockResolvedValue(revoked)
    const body = await (await route.GET(new Request('http://localhost'), context())).json()
    expect(body).toEqual({
      selection, availability: 'selection_broken', label: 'Unavailable local CLI choice', resolvedLabel: null,
      remediation: 'This AI choice is unavailable. Repair it in AI Console or choose another available option.',
    })
    expect(JSON.stringify(body)).not.toMatch(/sensitive|auth_unavailable/i)
  })

  it('never exposes provider claims, masked keys, credentials, or CLI diagnostics in presentation', async () => {
    const projected = stateWithAlternatives({ kind: 'provider_model', connectionId: SECOND_CONNECTION_ID, modelId: 'claude-safe' })
    mocks.listAiConsoleState.mockResolvedValue(projected)
    const serialized = JSON.stringify(await (await route.GET(new Request('http://localhost'), context())).json())
    expect(serialized).not.toMatch(/providerId|masked|credential|must-never|detected|auth_/i)
  })
})
