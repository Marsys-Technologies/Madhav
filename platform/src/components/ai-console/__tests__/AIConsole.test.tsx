import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { onlineManager, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import axe from 'axe-core'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { AIConsole } from '../AIConsole'
import type { AiConsoleStateDto } from '../types'

const CONNECTION_ID = '11111111-1111-4111-8111-111111111111'
const CONFIG_ID = '22222222-2222-4222-8222-222222222222'

const state: AiConsoleStateDto = {
  connections: [{
    id: CONNECTION_ID, providerId: 'openai', name: 'Personal OpenAI', maskedSuffix: '•••1234',
    validationState: 'validated', lastValidatedAt: '2026-09-27T10:00:00.000Z', lastCheckedAt: '2026-09-27T10:00:00.000Z',
    confirmedValid: true, lastErrorCode: null, deletedAt: null,
  }],
  models: [{ connectionId: CONNECTION_ID, modelId: 'gpt-safe', displayName: 'GPT Safe',
    compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false, supportsStructuredOutput: true, available: true }],
  configurations: [{ id: CONFIG_ID, name: 'Research quartet', version: 1, deletedAt: null, roles: {
    synthesizer: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    deep_planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    worker: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
  }}],
  defaultChoice: null,
  validationDisclosure: 'Testing this connection makes a tiny generation request and may incur a tiny provider charge.',
}

const cliState = { clis: [
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
  duplicateNameError?: boolean
}

function setup(overrides?: Partial<typeof state>, options: SetupOptions = {}) {
  const current = { ...state, ...overrides }
  const calls: Array<[RequestInfo | URL, RequestInit | undefined]> = []
  vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
    calls.push([url, init])
    if (String(url) === '/api/ai-console/clis' && options.cliPending) return new Promise<Response>(() => {})
    if (String(url) === '/api/ai-console/clis') return options.cliError
      ? response({ error: 'AI_CLI_UNREACHABLE' }, 503)
      : response(cliState)
    if (String(url) === '/api/ai-console' && options.aggregatePending) return new Promise<Response>(() => {})
    if (String(url) === '/api/ai-console' && options.aggregateError) return response({ error: 'AI_PROVIDER_UNREACHABLE' }, 503)
    if (String(url) === '/api/ai-console/default' && init?.method === 'PUT') return response({ defaultChoice: JSON.parse(String(init.body)).choice })
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
  it('renders exactly the three approved sections and one unchecked shared default group', async () => {
    setup()
    await screen.findByText('Personal OpenAI')
    expect(screen.getAllByRole('heading', { level: 2 }).map(node => node.textContent)).toEqual([
      'Provider connections', 'Custom configurations', 'Local CLIs',
    ])
    expect(screen.queryByRole('heading', { name: /default ai/i })).toBeNull()
    const radios = screen.getAllByRole('radio') as HTMLInputElement[]
    expect(radios.length).toBe(3)
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
    expect(screen.getAllByText('Built-in default')).toHaveLength(2)
  })

  it('sends the exact direct choice and waits for accepted mutation before reflecting server state', async () => {
    const { calls } = setup()
    const radio = await screen.findByRole('radio', { name: /use personal openai gpt safe as default ai/i })
    fireEvent.click(radio)
    await waitFor(() => expect(calls.some(([url]) => String(url) === '/api/ai-console/default')).toBe(true))
    const call = calls.find(([url]) => String(url) === '/api/ai-console/default')!
    expect(JSON.parse(String(call[1]?.body))).toEqual({ choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' } })
  })

  it('requires the server-provided charge acknowledgement before a user-triggered provider probe', async () => {
    const { calls } = setup()
    await screen.findByText('Personal OpenAI')
    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))
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

  it('uses four roles only, source before model, fill-all convenience, and disables incomplete save', async () => {
    setup()
    await screen.findByText('Research quartet')
    fireEvent.click(screen.getByRole('button', { name: /new configuration/i }))
    const dialog = await screen.findByRole('dialog')
    for (const label of ['Synthesizer', 'Planner', 'Deep Planner', 'Worker']) expect(within(dialog).getByText(label)).toBeTruthy()
    expect(within(dialog).queryByText(/inspector/i)).toBeNull()
    expect(dialog.querySelector('#aic-synthesizer-source')?.tagName).toBe('SELECT')
    expect((dialog.querySelector('#aic-synthesizer-model') as HTMLSelectElement).disabled).toBe(true)
    const fillAll = within(dialog).getByRole('button', { name: 'Use this model for every role' }) as HTMLButtonElement
    const save = within(dialog).getByRole('button', { name: 'Save configuration' }) as HTMLButtonElement
    expect(fillAll.disabled).toBe(true)
    expect(save.disabled).toBe(true)

    fireEvent.change(dialog.querySelector('#aic-config-name')!, { target: { value: 'One model' } })
    fireEvent.change(dialog.querySelector('#aic-synthesizer-source')!, { target: { value: `provider:${CONNECTION_ID}` } })
    await waitFor(() => expect((dialog.querySelector('#aic-synthesizer-model') as HTMLSelectElement).disabled).toBe(false))
    fireEvent.change(dialog.querySelector('#aic-synthesizer-model')!, { target: { value: 'gpt-safe' } })
    await waitFor(() => expect(fillAll.disabled).toBe(false))
    fireEvent.click(fillAll)
    await waitFor(() => expect(save.disabled).toBe(false))
    for (const role of ['synthesizer', 'planner', 'deep_planner', 'worker']) {
      expect((dialog.querySelector(`#aic-${role}-source`) as HTMLSelectElement).value).toBe(`provider:${CONNECTION_ID}`)
      expect((dialog.querySelector(`#aic-${role}-model`) as HTMLSelectElement).value).toBe('gpt-safe')
    }
  })

  it('keeps a broken default visibly identified and never substitutes another radio', async () => {
    setup({ defaultChoice: { kind: 'provider_model', connectionId: '99999999-9999-4999-8999-999999999999', modelId: 'removed-model' } })
    await screen.findByText(/broken default/i)
    expect(screen.getByText(/removed-model/)).toBeTruthy()
    expect((screen.getByRole('radio', { name: /personal openai gpt safe/i }) as HTMLInputElement).checked).toBe(false)
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
    const unverifiedCli = screen.getByRole('radio', { name: /claude code.*default verification unavailable/i })
    expect(unverifiedCli).toBeDisabled()
    expect(unverifiedCli).not.toBeChecked()
    expect(unverifiedCli.parentElement).toHaveTextContent('Default verification unavailable')
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
    const retainedDirect = await screen.findByRole('radio', { name: /personal openai gpt safe/i })
    expect(retainedDirect).not.toBeDisabled()
    const retainedConfiguration = screen.getByText('Research quartet').closest('article')!
    expect(within(retainedConfiguration).getByRole('radio')).not.toBeDisabled()
    cleanup()

    setup({ connections: [{ ...state.connections[0], validationState: 'validating', confirmedValid: false, lastValidatedAt: '2026-09-01T10:00:00.000Z' }] })
    const unknownDirect = await screen.findByRole('radio', { name: /personal openai gpt safe/i })
    expect(unknownDirect).toBeDisabled()
    const unknownConfiguration = screen.getByText('Research quartet').closest('article')!
    expect(within(unknownConfiguration).getByText(/needs repair/i)).toBeTruthy()
    expect(within(unknownConfiguration).getByRole('radio')).toBeDisabled()
  })

  it('does not enable reachable CLI defaults until aggregate default authority is ready', async () => {
    setup(undefined, { aggregatePending: true })
    const radio = await screen.findByRole('radio', { name: /claude code.*default verification unavailable/i })
    expect(radio).toBeDisabled()
    expect(radio).not.toBeChecked()
    expect(radio.parentElement).toHaveTextContent('Default verification unavailable')
  })

  it('does not call a saved CLI default broken while CLI authority is still loading', async () => {
    setup({ defaultChoice: { kind: 'local_cli', cliId: 'claude_code', modelId: null } }, { cliPending: true })
    await screen.findByText('Personal OpenAI')
    expect(screen.getByText('Checking local CLI access…')).toBeTruthy()
    expect(screen.queryByText(/broken default/i)).toBeNull()
  })

  it('distinguishes a checked unverified configuration default from a proven unavailable default', async () => {
    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    const cliConfiguration = { ...state.configurations[0], roles: {
      synthesizer: cliTarget, planner: cliTarget, deep_planner: cliTarget, worker: cliTarget,
    } }
    setup({ configurations: [cliConfiguration], defaultChoice: { kind: 'custom_configuration', configurationId: CONFIG_ID } }, { cliError: true })
    let card = (await screen.findByText('Research quartet')).closest('article')!
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
    card = (await screen.findByText('Research quartet')).closest('article')!
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
    expect(within(synthesizerModel).getByRole('option', { name: /saved model.*no longer available/i })).toBeDisabled()
    expect(synthesizerModel).toHaveAttribute('aria-invalid', 'true')
    expect(synthesizerModel).toHaveAttribute('aria-describedby', 'aic-model-repair')
    expect(within(dialog).getByText(/saved model choices are no longer available or compatible/i)).toBeTruthy()
    expect(within(dialog).getByRole('button', { name: 'Save configuration' })).toBeDisabled()
  })

  it('treats paused offline queries as pending instead of ready empty resources', async () => {
    onlineManager.setOnline(false)
    setup()
    expect(await screen.findByText('Loading provider connections…')).toBeTruthy()
    expect(screen.getByText('Loading custom configurations…')).toBeTruthy()
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
