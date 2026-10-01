import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { onlineManager, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import axe from 'axe-core'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { AIConsole } from '../AIConsole'
import type { AiConsoleStateDto, CliStateDto } from '../types'

const CONNECTION_ID = '11111111-1111-4111-8111-111111111111'
const CONFIG_ID = '22222222-2222-4222-8222-222222222222'

const state: AiConsoleStateDto = {
  connections: [{
    id: CONNECTION_ID, providerId: 'openai', name: 'Personal OpenAI', maskedSuffix: '•••1234',
    validationState: 'validated', lastValidatedAt: '2026-09-27T10:00:00.000Z', lastCheckedAt: '2026-09-27T10:00:00.000Z',
    confirmedValid: true, lastErrorCode: null, deletedAt: null,
  }],
  models: [{ connectionId: CONNECTION_ID, modelId: 'gpt-safe', displayName: 'GPT Safe',
    compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false, supportsStructuredOutput: true, available: true,
    userSelected: true, plainTestedAt: '2026-09-27T10:00:00.000Z' }],
  configurations: [{ id: CONFIG_ID, name: 'Research quartet', version: 1, deletedAt: null,
    configurationKind: 'custom_api', ownerConnectionId: null, ownerCliId: null, roles: {
    synthesizer: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    deep_planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    worker: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
  }}],
  defaultChoice: null,
  validationDisclosure: 'Testing this connection makes a tiny generation request and may incur a tiny provider charge.',
}

const cliState: CliStateDto = { clis: [
  { cliId: 'codex', productName: 'Codex CLI', state: 'needs_attention', detectedProduct: 'Codex CLI', detectedVersion: '0.155.1', lastCheckedAt: '2026-09-27T10:00:00.000Z', models: [] },
  { cliId: 'claude_code', productName: 'Claude Code', state: 'reachable', detectedProduct: 'Claude Code', detectedVersion: '2.1.56', lastCheckedAt: '2026-09-27T10:00:00.000Z', models: [{ modelId: null, displayName: 'Built-in default', compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false, supportsStructuredOutput: true, isBuiltinDefault: true }] },
  { cliId: 'gemini_antigravity', productName: 'Gemini / Antigravity', state: 'not_granted' },
  { cliId: 'kimi_code', productName: 'Kimi Code', state: 'needs_attention', detectedProduct: null, detectedVersion: null, lastCheckedAt: null, models: [] },
] }

function response(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
}

interface SetupOptions {
  aggregateError?: boolean
  aggregatePending?: boolean
  cliError?: boolean
  cliPending?: boolean
  cliResponse?: CliStateDto
  duplicateNameError?: boolean
  validationResponse?: unknown
}

function setup(overrides?: Partial<typeof state>, options: SetupOptions = {}) {
  const current = { ...state, ...overrides }
  const calls: Array<[RequestInfo | URL, RequestInit | undefined]> = []
  vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
    calls.push([url, init])
    if (String(url) === '/api/ai-console/clis' && options.cliPending) return new Promise<Response>(() => {})
    if (String(url) === '/api/ai-console/clis') return options.cliError
      ? response({ error: 'AI_CLI_UNREACHABLE' }, 503)
      : response(options.cliResponse ?? cliState)
    if (String(url) === '/api/ai-console' && options.aggregatePending) return new Promise<Response>(() => {})
    if (String(url) === '/api/ai-console' && options.aggregateError) return response({ error: 'AI_PROVIDER_UNREACHABLE' }, 503)
    if (String(url) === '/api/ai-console/default' && init?.method === 'PUT') return response({ defaultChoice: JSON.parse(String(init.body)).choice })
    if (String(url).endsWith('/validate') && init?.method === 'POST' && options.validationResponse) return response(options.validationResponse)
    if (String(url) === '/api/ai-console/configurations' && init?.method === 'POST'
      && options.duplicateNameError && String(init.body).includes('duplicateFrom')) {
      return response({ error: 'name_conflict' }, 409)
    }
    return response(current)
  }))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(<QueryClientProvider client={client}><AIConsole /></QueryClientProvider>)
  return { calls }
}

afterEach(() => { cleanup(); onlineManager.setOnline(true); vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('AI Console', () => {
  it('sets up a provider-owned four-role preset without offering CLI sources', async () => {
    const { calls } = setup()
    const card = (await screen.findByText('Personal OpenAI')).closest('article')!
    await userEvent.click(within(card).getByRole('button', { name: 'Set up four roles' }))
    const dialog = await screen.findByRole('dialog', { name: 'Set up four roles' })
    expect(within(dialog).getByLabelText('Configuration name')).toHaveValue('Personal OpenAI roles')
    expect(within(dialog).queryByLabelText(/source for synthesizer/i)).toBeNull()
    expect(within(dialog).getByLabelText(/model for synthesizer/i)).toHaveValue('gpt-safe')
    expect(within(dialog).getByLabelText(/effort for synthesizer/i)).toBeDisabled()
    expect(within(dialog).queryByText('Claude Code')).toBeNull()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save configuration' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === '/api/ai-console/configurations'
      && init?.method === 'POST')).toBe(true))
    const saved = calls.find(([url, init]) => String(url) === '/api/ai-console/configurations' && init?.method === 'POST')!
    expect(JSON.parse(String(saved[1]?.body))).toMatchObject({ configurationKind: 'provider_preset',
      ownerConnectionId: CONNECTION_ID, ownerCliId: null })
  })

  it('saves a supported effort for all four provider roles', async () => {
    const { calls } = setup({ models: [{ ...state.models[0], modelId: 'gpt-5.5', displayName: 'GPT 5.5' }],
      configurations: [] })
    const card = (await screen.findByText('Personal OpenAI')).closest('article')!
    await userEvent.click(within(card).getByRole('button', { name: 'Set up four roles' }))
    const dialog = await screen.findByRole('dialog', { name: 'Set up four roles' })
    await userEvent.selectOptions(within(dialog).getByLabelText(/effort for synthesizer/i), 'high')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Use this model for every role' }))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save configuration' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === '/api/ai-console/configurations'
      && init?.method === 'POST')).toBe(true))
    const saved = calls.find(([url, init]) => String(url) === '/api/ai-console/configurations'
      && init?.method === 'POST')!
    const roles = JSON.parse(String(saved[1]?.body)).roles
    for (const role of ['synthesizer', 'planner', 'deep_planner', 'worker']) {
      expect(roles[role]).toMatchObject({ kind: 'provider_model', modelId: 'gpt-5.5', effort: 'high' })
    }
  })

  it('offers card-level defaults only for complete provider and CLI role setups', async () => {
    const apiRoles = state.configurations[0].roles
    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    setup({ configurations: [
      { ...state.configurations[0], configurationKind: 'provider_preset', ownerConnectionId: CONNECTION_ID },
      { ...state.configurations[0], id: '33333333-3333-4333-8333-333333333333', name: 'Claude roles',
        configurationKind: 'cli_preset', ownerConnectionId: null, ownerCliId: 'claude_code',
        roles: { synthesizer: cliTarget, planner: cliTarget, deep_planner: cliTarget, worker: cliTarget } },
      { ...state.configurations[0], id: '44444444-4444-4444-8444-444444444444', name: 'API mix',
        configurationKind: 'custom_api', ownerConnectionId: null, roles: apiRoles },
    ] })
    const providerCard = (await screen.findByText('Personal OpenAI')).closest('article')!
    const cliCard = screen.getByText('Claude Code').closest('article')!
    expect(within(providerCard).getAllByRole('radio')).toHaveLength(1)
    expect(within(cliCard).getAllByRole('radio')).toHaveLength(1)
    expect(within(providerCard).getByRole('radio')).not.toBeDisabled()
    expect(within(cliCard).getByRole('radio')).not.toBeDisabled()
    expect(screen.getAllByRole('radio')).toHaveLength(3)
  })

  it('keeps a new custom CLI configuration separate from API providers', async () => {
    setup()
    await screen.findByText('Claude Code')
    await userEvent.click(within(screen.getByRole('region', { name: 'Custom CLI configurations' }))
      .getByRole('button', { name: 'New configuration' }))
    const dialog = await screen.findByRole('dialog', { name: 'New custom configuration' })
    const source = within(dialog).getByLabelText(/source for synthesizer/i) as HTMLSelectElement
    expect([...source.options].map(option => option.textContent)).toEqual(['Choose source', 'Claude Code'])
    expect([...source.options].some(option => option.textContent?.includes('OpenAI'))).toBe(false)
  })

  it('keeps a large provider catalog out of the page and tests one exact model on request', async () => {
    const models = [...state.models, ...Array.from({ length: 150 }, (_, index) => ({
      ...state.models[0], modelId: `catalog-${index}`, displayName: `Catalog ${index}`,
      userSelected: false, plainTestedAt: null,
    }))]
    const { calls } = setup({ models })
    await screen.findByText('Personal OpenAI')
    expect(screen.queryByText('Catalog 149')).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: /manage models/i }))
    expect(screen.getByText(/showing 1 of 1 matching models/i)).toBeTruthy()
    await userEvent.selectOptions(screen.getByLabelText('View'), 'catalog')
    expect(screen.getByText(/showing 30 of 151 matching models/i)).toBeTruthy()
    const search = screen.getByRole('searchbox', { name: 'Find a model' })
    await userEvent.type(search, 'Catalog 149')
    expect(screen.getByText('Catalog 149')).toBeTruthy()
    const test = screen.getByRole('button', { name: 'Test and add Catalog 149' })
    expect(test).toBeDisabled()
    await userEvent.click(screen.getByRole('checkbox', { name: /each model test makes a tiny provider request/i }))
    await userEvent.click(test)
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === `/api/ai-console/connections/${CONNECTION_ID}/models`
      && init?.method === 'POST')).toBe(true))
    const call = calls.find(([url, init]) => String(url) === `/api/ai-console/connections/${CONNECTION_ID}/models` && init?.method === 'POST')!
    expect(JSON.parse(String(call[1]?.body))).toEqual({ modelId: 'catalog-149', acknowledgeCharge: true })
  })

  it('can retest a shortlisted model after its key or availability changes', async () => {
    const { calls } = setup({ models: [{ ...state.models[0], plainTestedAt: null }] })
    await screen.findByText('Personal OpenAI')
    await userEvent.click(screen.getByRole('button', { name: /manage models/i }))
    const test = screen.getByRole('button', { name: 'Test GPT Safe' })
    expect(test).toBeDisabled()
    await userEvent.click(screen.getByRole('checkbox', { name: /each model test makes a tiny provider request/i }))
    await userEvent.click(test)
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === `/api/ai-console/connections/${CONNECTION_ID}/models`
      && init?.method === 'POST' && JSON.parse(String(init.body)).modelId === 'gpt-safe')).toBe(true))
  })

  it('opens a named four-role configuration from a reachable CLI card', async () => {
    setup()
    await screen.findByText('Claude Code')
    await userEvent.click(within(screen.getByText('Claude Code').closest('article')!).getByRole('button', { name: 'Set up four roles' }))
    const dialog = await screen.findByRole('dialog', { name: 'Set up four roles' })
    expect(within(dialog).getByLabelText('Configuration name')).toHaveValue('Claude Code roles')
    expect(within(dialog).getByLabelText(/model for synthesizer/i)).toHaveValue('__builtin__')
    expect(within(dialog).queryByLabelText(/source for synthesizer/i)).toBeNull()
    expect(within(dialog).getByLabelText(/effort for synthesizer/i)).toBeDisabled()
    expect(within(dialog).getByRole('textbox', { name: 'Add a model to the role lists' })).toBeTruthy()
  })

  it('saves a tested Claude CLI model and effort without offering another CLI family', async () => {
    const { calls } = setup(undefined, { cliResponse: { clis: cliState.clis.map(cli => cli.cliId === 'claude_code' && 'models' in cli
      ? { ...cli, models: [...cli.models, { modelId: 'claude-sonnet-4-6', displayName: 'Sonnet 4.6',
        compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: true,
        supportsStructuredOutput: true, isBuiltinDefault: false }] } : cli) } })
    await screen.findByText('Claude Code')
    await userEvent.click(within(screen.getByText('Claude Code').closest('article')!).getByRole('button', { name: 'Set up four roles' }))
    const dialog = await screen.findByRole('dialog', { name: 'Set up four roles' })
    const model = within(dialog).getByLabelText(/model for synthesizer/i) as HTMLSelectElement
    expect([...model.options].map(option => option.value)).toEqual(['', '__builtin__', 'claude-sonnet-4-6'])
    await userEvent.selectOptions(model, 'claude-sonnet-4-6')
    await userEvent.selectOptions(within(dialog).getByLabelText(/effort for synthesizer/i), 'medium')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Use this model for every role' }))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save configuration' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === '/api/ai-console/configurations'
      && init?.method === 'POST')).toBe(true))
    const call = calls.find(([url, init]) => String(url) === '/api/ai-console/configurations' && init?.method === 'POST')!
    const saved = JSON.parse(String(call[1]?.body))
    expect(saved.configurationKind).toBe('cli_preset')
    for (const role of ['synthesizer', 'planner', 'deep_planner', 'worker']) {
      expect(saved.roles[role]).toMatchObject({ kind: 'local_cli', cliId: 'claude_code',
        modelId: 'claude-sonnet-4-6', effort: 'medium' })
    }
  })

  it('tests a CLI model without leaving the role setup dialog', async () => {
    const { calls } = setup()
    await screen.findByText('Claude Code')
    await userEvent.click(within(screen.getByText('Claude Code').closest('article')!).getByRole('button', { name: 'Set up four roles' }))
    const dialog = await screen.findByRole('dialog', { name: 'Set up four roles' })
    await userEvent.type(within(dialog).getByRole('textbox', { name: 'Add a model to the role lists' }), 'claude-sonnet-4-6')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Test through CLI and add' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === '/api/ai-console/clis/claude_code/models'
      && init?.method === 'POST' && JSON.parse(String(init.body)).modelId === 'claude-sonnet-4-6')).toBe(true))
  })

  it('submits one exact CLI model ID for a local subscription test', async () => {
    const { calls } = setup()
    await screen.findByText('Claude Code')
    await userEvent.type(screen.getByRole('textbox', { name: 'Exact model ID for Claude Code' }), 'claude-test')
    await userEvent.click(screen.getByRole('button', { name: 'Test and add CLI model' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url) === '/api/ai-console/clis/claude_code/models'
      && init?.method === 'POST')).toBe(true))
    const call = calls.find(([url, init]) => String(url) === '/api/ai-console/clis/claude_code/models' && init?.method === 'POST')!
    expect(JSON.parse(String(call[1]?.body))).toEqual({ modelId: 'claude-test' })
  })

  it('renders two collapsible groups with separate API and CLI custom configurations', async () => {
    setup()
    await screen.findByText('Personal OpenAI')
    expect(screen.getAllByRole('heading', { level: 2 }).map(node => node.textContent)).toEqual([
      'API connections', 'Custom API configurations', 'Local CLIs', 'Custom CLI configurations',
    ])
    expect(document.querySelectorAll('details.aic-group')).toHaveLength(2)
    expect(screen.queryByRole('heading', { name: /default ai/i })).toBeNull()
    const radios = screen.getAllByRole('radio') as HTMLInputElement[]
    expect(radios.length).toBe(1)
    expect(radios.every(radio => radio.name === 'ai-console-default' && !radio.checked)).toBe(true)
  })

  it('shows only the credential mask, charge disclosure, textual states, and honest CLI availability', async () => {
    setup()
    await screen.findByText('Personal OpenAI')
    expect(screen.getByText('•••1234')).toBeTruthy()
    expect(screen.queryByText(/unmasked credential/i)).toBeNull()
    expect(screen.getByText(/may incur a tiny provider charge/i)).toBeTruthy()
    expect(screen.getByText('Validated')).toBeTruthy()
    expect(screen.getAllByText('Needs attention')).toHaveLength(2)
    const ungrantedCard = screen.getByText('Gemini / Antigravity').closest('article')!
    expect(within(ungrantedCard).getByText('Not granted')).toBeTruthy()
    expect(within(ungrantedCard).queryByText(/version|last check|model/i)).toBeNull()
    expect(screen.getAllByText('Built-in default').length).toBeGreaterThan(0)
  })

  it('explains saved billing and unknown failures without claiming their keys are rejected', async () => {
    setup({ connections: [
      { ...state.connections[0], validationState: 'needs_attention', confirmedValid: false, lastErrorCode: 'AI_BILLING_UNAVAILABLE' },
      { ...state.connections[0], id: '33333333-3333-4333-8333-333333333333', providerId: 'anthropic', name: 'Anthropic',
        validationState: 'needs_attention', confirmedValid: false, lastErrorCode: 'AI_EXECUTION_FAILED' },
    ] })
    await screen.findByText('Personal OpenAI')
    expect(screen.getByText(/API billing, credits, or a spending limit is blocking this connection/)).toBeTruthy()
    expect(screen.getByText(/precise reason was not identified/)).toBeTruthy()
    expect(screen.queryByText(/provider rejected this key/i)).toBeNull()
  })

  it('offers an Anthropic workspace edit without asking for the saved key again', async () => {
    const { calls } = setup({ connections: [{ ...state.connections[0], providerId: 'anthropic',
      name: 'Claude', validationState: 'needs_attention', confirmedValid: false, lastErrorCode: 'AI_EXECUTION_FAILED' }] })
    await screen.findByText('Claude')
    expect(screen.getByText(/Organization-wide Claude keys need a workspace ID/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Workspace ID' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).queryByLabelText('API key')).toBeNull()
    fireEvent.change(within(dialog).getByLabelText(/Claude workspace ID/),
      { target: { value: 'wrkspc_01JEueaSaKJ72sh4drDASzH2' } })
    fireEvent.click(within(dialog).getByRole('checkbox'))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(calls.some(([url, init]) => String(url).endsWith(`connections/${CONNECTION_ID}`)
      && init?.method === 'PATCH')).toBe(true))
    const mutation = calls.find(([url, init]) => String(url).endsWith(`connections/${CONNECTION_ID}`)
      && init?.method === 'PATCH')!
    expect(JSON.parse(String(mutation[1]?.body))).toEqual({ workspaceId: 'wrkspc_01JEueaSaKJ72sh4drDASzH2', acknowledgeCharge: true })
  })

  it('does not announce success when a connection test returns needs attention', async () => {
    const { calls } = setup(undefined, { validationResponse: { validation: { state: 'needs_attention', modelCount: 0,
      error: { code: 'AI_EXECUTION_FAILED' } } } })
    await screen.findByText('Personal OpenAI')
    fireEvent.click(screen.getByRole('button', { name: 'Test Personal OpenAI connection' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.click(within(dialog).getByRole('checkbox'))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }))
    await waitFor(() => expect(calls.some(([url]) => String(url).endsWith('/validate'))).toBe(true))
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Connection is not ready. Review the reason on its card.'))
  })

  it('sends the exact four-role configuration choice and waits for accepted mutation', async () => {
    const { calls } = setup()
    const radio = await screen.findByRole('radio', { name: /use research quartet as default ai/i })
    fireEvent.click(radio)
    await waitFor(() => expect(calls.some(([url]) => String(url) === '/api/ai-console/default')).toBe(true))
    const call = calls.find(([url]) => String(url) === '/api/ai-console/default')!
    expect(JSON.parse(String(call[1]?.body))).toEqual({ choice: { kind: 'custom_configuration', configurationId: CONFIG_ID } })
  })

  it('requires the server-provided charge acknowledgement before a user-triggered provider probe', async () => {
    const { calls } = setup()
    await screen.findByText('Personal OpenAI')
    fireEvent.click(screen.getByRole('button', { name: 'Test Personal OpenAI connection' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/tiny provider charge/i)).toBeTruthy()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }))
    const error = await within(dialog).findByRole('alert')
    expect(error).toHaveTextContent(/acknowledge/i)
    const acknowledgement = within(dialog).getByRole('checkbox')
    expect(acknowledgement.id).toBe('aic-charge-acknowledgement')
    expect(acknowledgement).toHaveAttribute('aria-invalid', 'true')
    expect(acknowledgement).toHaveAttribute('aria-describedby', error.id)
    expect(calls.some(([url]) => String(url).endsWith('/validate'))).toBe(false)
    fireEvent.click(acknowledgement)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }))
    await waitFor(() => expect(calls.some(([url]) => String(url).endsWith('/validate'))).toBe(true))
  })

  it('does not announce success when a validation request returns needs attention', async () => {
    setup(undefined, { validationResponse: { validation: { state: 'needs_attention', modelCount: 0 } } })
    await userEvent.click(await screen.findByRole('button', { name: 'Test Personal OpenAI connection' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('checkbox'))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }))
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Connection is not ready'))
  })

  it('associates each provider editor error only with its exact repair control', async () => {
    const user = userEvent.setup()
    setup()
    await user.click(await screen.findByRole('button', { name: /add connection/i }))
    const dialog = await screen.findByRole('dialog')
    const name = within(dialog).getByRole('textbox', { name: /connection name/i })
    const key = dialog.querySelector('#aic-api-key') as HTMLInputElement
    const acknowledgement = within(dialog).getByRole('checkbox')
    const save = within(dialog).getByRole('button', { name: 'Save' })

    await user.click(save)
    let error = await within(dialog).findByRole('alert')
    expect(name).toHaveAttribute('aria-describedby', error.id)
    expect(name).toHaveAttribute('aria-invalid', 'true')
    expect(key).not.toHaveAttribute('aria-describedby')
    expect(acknowledgement).not.toHaveAttribute('aria-describedby')

    await user.type(name, 'Second connection')
    await user.click(save)
    error = await within(dialog).findByRole('alert')
    expect(key).toHaveAttribute('aria-describedby', error.id)
    expect(key).toHaveAttribute('aria-invalid', 'true')
    expect(name).not.toHaveAttribute('aria-describedby')

    await user.type(key, 'credential-placeholder')
    await user.click(save)
    error = await within(dialog).findByRole('alert')
    expect(acknowledgement).toHaveAttribute('aria-describedby', error.id)
    expect(acknowledgement).toHaveAttribute('aria-invalid', 'true')
    expect(key).not.toHaveAttribute('aria-describedby')
  })

  it('suggests tested models for all four roles and still requires a name', async () => {
    setup()
    await screen.findByText('Research quartet')
    fireEvent.click(within(screen.getByRole('region', { name: 'Custom API configurations' })).getByRole('button', { name: /new configuration/i }))
    const dialog = await screen.findByRole('dialog')
    for (const label of ['Synthesizer', 'Planner', 'Deep Planner', 'Worker']) expect(within(dialog).getByText(label)).toBeTruthy()
    expect(within(dialog).queryByText(/inspector/i)).toBeNull()
    expect(dialog.querySelector('#aic-synthesizer-source')?.tagName).toBe('SELECT')
    expect((dialog.querySelector('#aic-synthesizer-model') as HTMLSelectElement).value).toBe('gpt-safe')
    const fillAll = within(dialog).getByRole('button', { name: 'Use this model for every role' }) as HTMLButtonElement
    const save = within(dialog).getByRole('button', { name: 'Save configuration' }) as HTMLButtonElement
    expect(fillAll.disabled).toBe(false)
    expect(save.disabled).toBe(true)

    fireEvent.change(dialog.querySelector('#aic-config-name')!, { target: { value: 'One model' } })
    await waitFor(() => expect(save.disabled).toBe(false))
    for (const role of ['synthesizer', 'planner', 'deep_planner', 'worker']) {
      expect((dialog.querySelector(`#aic-${role}-source`) as HTMLSelectElement).value).toBe(`provider:${CONNECTION_ID}`)
      expect((dialog.querySelector(`#aic-${role}-model`) as HTMLSelectElement).value).toBe('gpt-safe')
    }
  })

  it('keeps a broken default visibly identified and never substitutes another radio', async () => {
    setup({ defaultChoice: { kind: 'provider_model', connectionId: '99999999-9999-4999-8999-999999999999', modelId: 'removed-model' } })
    await screen.findByText(/broken default/i)
    expect(screen.getAllByText(/removed-model/).length).toBeGreaterThan(0)
    expect((screen.getByRole('radio', { name: /research quartet/i }) as HTMLInputElement).checked).toBe(false)
    expect((screen.getByRole('radio', { name: /99999999.*removed-model/i }) as HTMLInputElement).checked).toBe(true)
  })

  it('keeps portalled add, edit, duplicate, and delete dialogs inside the Paripraśna token scope and restores focus on Escape', async () => {
    const user = userEvent.setup()
    setup()
    const add = await screen.findByRole('button', { name: /add connection/i })
    await user.click(add)
    let dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveClass('pp-root', 'aic-dialog')
    const dialogAxe = await axe.run(dialog, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
    })
    expect(dialogAxe.violations.filter(item => item.impact === 'critical' || item.impact === 'serious')).toEqual([])
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(add).toHaveFocus()

    const edit = screen.getByRole('button', { name: 'Edit' })
    await user.click(edit)
    dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveClass('pp-root', 'aic-dialog')
    expect(within(dialog).getByRole('textbox', { name: /configuration name/i })).toHaveValue('Research quartet')
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(edit).toHaveFocus()

    const duplicate = screen.getByRole('button', { name: /duplicate/i })
    await user.click(duplicate)
    dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveClass('pp-root', 'aic-dialog')
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(duplicate).toHaveFocus()

    const card = screen.getByText('Research quartet').closest('article')!
    const remove = within(card).getByRole('button', { name: 'Delete' })
    await user.click(remove)
    const alert = await screen.findByRole('alertdialog')
    expect(alert).toHaveClass('pp-root', 'aic-dialog')
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull())
    expect(remove).toHaveFocus()
  })

  it('renders aggregate and CLI failures only in their own resource sections without false empty or broken states', async () => {
    const aggregateFailure = setup(undefined, { aggregateError: true })
    expect(await screen.findAllByText(/provider connections could not be loaded/i)).toHaveLength(1)
    expect(screen.getByText('Claude Code')).toBeTruthy()
    expect(screen.queryByText(/no provider connections yet/i)).toBeNull()
    expect(screen.queryByText(/no custom configurations yet/i)).toBeNull()
    expect(screen.queryByRole('button', { name: /add connection|new configuration/i })).toBeNull()
    expect(screen.queryByRole('radio')).toBeNull()
    expect(aggregateFailure.calls).toBeTruthy()
    cleanup()

    setup(undefined, { cliError: true })
    await screen.findByText('Personal OpenAI')
    expect(screen.getByText(/local cli access could not be loaded/i)).toBeTruthy()
    expect(screen.queryByText(/no local cli products/i)).toBeNull()
    expect(screen.queryByRole('button', { name: /test local cli/i })).toBeNull()
    const configuration = screen.getByText('Research quartet').closest('article')!
    expect(within(configuration).queryByText(/needs repair/i)).toBeNull()
    expect(within(configuration).getByRole('radio')).not.toBeDisabled()
    cleanup()

    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    setup({ configurations: [{ ...state.configurations[0], roles: {
      synthesizer: cliTarget, planner: cliTarget, deep_planner: cliTarget, worker: cliTarget,
    } }] }, { cliError: true })
    const cliConfiguration = (await screen.findByText('Research quartet')).closest('article')!
    expect(within(cliConfiguration).getByText('CLI availability unavailable')).toBeTruthy()
    expect(within(cliConfiguration).getByText('Local CLI availability could not be verified')).toBeTruthy()
    expect(within(cliConfiguration).queryByText(/needs repair/i)).toBeNull()
    expect(within(cliConfiguration).queryByText(/role choices are unavailable/i)).toBeNull()
    expect(within(cliConfiguration).getByRole('button', { name: 'Edit' })).toBeDisabled()
    expect(within(cliConfiguration).getByRole('radio')).toBeDisabled()
  })

  it('uses retained validation evidence while validating and blocks a first or replaced credential with no confirmation', async () => {
    setup({ connections: [{ ...state.connections[0], validationState: 'validating', confirmedValid: true }] })
    await screen.findByText('Research quartet')
    const retainedConfiguration = screen.getByText('Research quartet').closest('article')!
    expect(within(retainedConfiguration).getByRole('radio')).not.toBeDisabled()
    cleanup()

    setup({ connections: [{ ...state.connections[0], validationState: 'validating', confirmedValid: false, lastValidatedAt: '2026-09-01T10:00:00.000Z' }] })
    await screen.findByText('Research quartet')
    const unknownConfiguration = screen.getByText('Research quartet').closest('article')!
    expect(within(unknownConfiguration).getByText(/needs repair/i)).toBeTruthy()
    expect(within(unknownConfiguration).getByRole('radio')).toBeDisabled()
  })

  it('does not offer a CLI default until a four-role CLI setup exists', async () => {
    setup(undefined, { aggregatePending: true })
    await screen.findByText('Claude Code')
    expect(screen.queryByRole('radio')).toBeNull()
  })

  it('does not call a saved CLI default broken while CLI authority is still loading', async () => {
    setup({ defaultChoice: { kind: 'local_cli', cliId: 'claude_code', modelId: null } }, { cliPending: true })
    await screen.findByText('Personal OpenAI')
    expect(screen.getByText('Checking local CLI access…')).toBeTruthy()
    expect(screen.queryByText(/broken default/i)).toBeNull()
  })

  it('distinguishes a checked unverified configuration default from a proven unavailable default', async () => {
    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    const cliConfiguration = { ...state.configurations[0], configurationKind: 'custom_cli' as const, roles: {
      synthesizer: cliTarget, planner: cliTarget, deep_planner: cliTarget, worker: cliTarget,
    } }
    setup({ configurations: [cliConfiguration], defaultChoice: { kind: 'custom_configuration', configurationId: CONFIG_ID } }, { cliError: true })
    let card = (await screen.findByRole('heading', { name: 'Research quartet' })).closest('article')!
    let radio = within(card).getByRole('radio')
    expect(radio).toBeChecked()
    expect(radio).toBeDisabled()
    expect(radio.parentElement).toHaveTextContent('Default unverified')
    expect(radio.parentElement).not.toHaveTextContent('Default unavailable')
    cleanup()

    const unavailableTarget = { kind: 'local_cli' as const, cliId: 'kimi_code' as const, modelId: null }
    setup({ configurations: [{ ...cliConfiguration, roles: {
      synthesizer: unavailableTarget, planner: unavailableTarget, deep_planner: unavailableTarget, worker: unavailableTarget,
    } }], defaultChoice: { kind: 'custom_configuration', configurationId: CONFIG_ID } })
    card = (await screen.findByRole('heading', { name: 'Research quartet' })).closest('article')!
    radio = within(card).getByRole('radio')
    expect(radio).toBeChecked()
    expect(radio).toBeDisabled()
    expect(radio.parentElement).toHaveTextContent('Default unavailable')
  })

  it('keeps retained catalog rows incomplete when their provider source is no longer selectable', async () => {
    const user = userEvent.setup()
    setup({ connections: [{ ...state.connections[0], validationState: 'invalid', confirmedValid: false }] })
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/saved sources are no longer selectable/i)).toBeTruthy()
    for (const role of ['synthesizer', 'planner', 'deep_planner', 'worker']) {
      expect(dialog.querySelector(`#aic-${role}-model`)).toBeDisabled()
    }
    expect(within(dialog).getByRole('button', { name: 'Save configuration' })).toBeDisabled()
  })

  it.each([
    ['missing', [{ ...state.models[0], modelId: 'replacement-model', displayName: 'Replacement model' }]],
    ['unavailable', [{ ...state.models[0], available: false }]],
    ['role-incompatible', [{ ...state.models[0], compatibleRoles: ['planner', 'deep_planner', 'worker'] }]],
  ] satisfies Array<[string, AiConsoleStateDto['models']]>)('keeps an exact saved %s model visible for repair without silently substituting it', async (_reason, models) => {
    const user = userEvent.setup()
    setup({ models: [...models] })
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    const dialog = await screen.findByRole('dialog')
    const synthesizerModel = dialog.querySelector('#aic-synthesizer-model') as HTMLSelectElement
    expect(synthesizerModel.value).toBe('gpt-safe')
    expect(within(synthesizerModel).getByRole('option', { name: /saved model.*needs a current test or role check/i })).toBeDisabled()
    expect(synthesizerModel).toHaveAttribute('aria-invalid', 'true')
    expect(synthesizerModel).toHaveAttribute('aria-describedby', 'aic-model-repair')
    expect(within(dialog).getByText(/saved models need a current generation test/i)).toBeTruthy()
    expect(within(dialog).getByRole('button', { name: 'Save configuration' })).toBeDisabled()
  })

  it('labels a stale CLI built-in default without exposing its client-only draft encoding', async () => {
    const user = userEvent.setup()
    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    const cliConfiguration = { ...state.configurations[0], configurationKind: 'custom_cli' as const, roles: {
      synthesizer: cliTarget, planner: cliTarget, deep_planner: cliTarget, worker: cliTarget,
    } }
    const cliResponse: CliStateDto = { clis: cliState.clis.map(cli => cli.cliId === 'claude_code' && cli.state !== 'not_granted'
      ? { ...cli, models: cli.models.map(model => ({ ...model, compatibleRoles: ['planner', 'deep_planner', 'worker'] })) }
      : cli) }
    setup({ configurations: [cliConfiguration] }, { cliResponse })
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    const dialog = await screen.findByRole('dialog')
    const synthesizerModel = dialog.querySelector('#aic-synthesizer-model') as HTMLSelectElement
    expect(synthesizerModel.value).toBe('__builtin__')
    expect(within(synthesizerModel).getByRole('option', { name: /built-in default.*needs a current test or role check/i })).toBeDisabled()
    expect(dialog).not.toHaveTextContent('__builtin__')
    expect(synthesizerModel).toHaveAttribute('aria-invalid', 'true')
    expect(synthesizerModel).toHaveAttribute('aria-describedby', 'aic-model-repair')
    expect(within(dialog).getByRole('button', { name: 'Save configuration' })).toBeDisabled()
  })

  it('treats paused offline queries as pending instead of ready empty resources', async () => {
    onlineManager.setOnline(false)
    setup()
    expect(await screen.findByText('Loading provider connections…')).toBeTruthy()
    expect(screen.getAllByText('Loading custom configurations…')).toHaveLength(2)
    expect(screen.getByText('Checking local CLI access…')).toBeTruthy()
    expect(document.querySelector('.aic-sections')).toHaveAttribute('aria-busy', 'true')
    expect(screen.queryByText(/no provider connections yet/i)).toBeNull()
    expect(screen.queryByText(/no custom configurations yet/i)).toBeNull()
    expect(screen.queryByText(/no local CLI connections are available/i)).toBeNull()
    expect(screen.queryByRole('button', { name: /add connection|new configuration/i })).toBeNull()
  })

  it('associates duplicate-name server errors only with the duplicate name repair control', async () => {
    const user = userEvent.setup()
    setup(undefined, { duplicateNameError: true })
    await user.click(await screen.findByRole('button', { name: /duplicate/i }))
    const dialog = await screen.findByRole('dialog')
    const name = within(dialog).getByRole('textbox', { name: /configuration name/i })
    await user.click(within(dialog).getByRole('button', { name: 'Duplicate' }))
    const error = await within(dialog).findByRole('alert')
    expect(error).toHaveTextContent(/name is already in use/i)
    expect(name).toHaveAttribute('aria-invalid', 'true')
    expect(name).toHaveAttribute('aria-describedby', error.id)
  })

  it('renders a populated four-role configuration accessibly with no serious or critical axe violations', async () => {
    setup()
    const card = (await screen.findByText('Research quartet')).closest('article')!
    for (const role of ['Synthesizer', 'Planner', 'Deep Planner', 'Worker']) {
      expect(within(card).getByText(role)).toBeTruthy()
    }
    const results = await axe.run(document.body, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
    })
    expect(results.violations.filter(item => item.impact === 'critical' || item.impact === 'serious')).toEqual([])
  })

  it('contains the mobile target, scoped selector, focus, and reduced-motion contracts', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/components/ai-console/ai-console.css'), 'utf8')
    expect(css).toContain('.pp-root .aic-')
    expect(css).toMatch(/min-height:\s*44px/)
    expect(css).toContain(':focus-visible')
    expect(css).toContain('prefers-reduced-motion: reduce')
    expect(css).toContain('.pp-root.aic-dialog')
    expect(css).toMatch(/left:\s*0\s*!important/)
    expect(css).toMatch(/right:\s*0\s*!important/)
    expect(css).toMatch(/width:\s*100%\s*!important/)
    expect(css).toMatch(/aic-disclosure input:focus-visible/)
    expect(css).toMatch(/\.pp-root\.aic-dialog[^}]*transition-duration:\s*\.01ms/s)
  })
})
