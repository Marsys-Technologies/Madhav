import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
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
    lastErrorCode: null, deletedAt: null,
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

function setup(overrides?: Partial<typeof state>) {
  const current = { ...state, ...overrides }
  const calls: Array<[RequestInfo | URL, RequestInit | undefined]> = []
  vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
    calls.push([url, init])
    if (String(url) === '/api/ai-console/clis') return response(cliState)
    if (String(url) === '/api/ai-console/default' && init?.method === 'PUT') return response({ defaultChoice: JSON.parse(String(init.body)).choice })
    return response(current)
  }))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(<QueryClientProvider client={client}><AIConsole /></QueryClientProvider>)
  return { calls }
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

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
    expect(await within(dialog).findByRole('alert')).toHaveTextContent(/acknowledge/i)
    expect(calls.some(([url]) => String(url).endsWith('/validate'))).toBe(false)
    fireEvent.click(within(dialog).getByRole('checkbox'))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }))
    await waitFor(() => expect(calls.some(([url]) => String(url).endsWith('/validate'))).toBe(true))
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

  it('contains the mobile target, scoped selector, focus, and reduced-motion contracts', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/components/ai-console/ai-console.css'), 'utf8')
    expect(css).toContain('.pp-root .aic-')
    expect(css).toMatch(/min-height:\s*44px/)
    expect(css).toContain(':focus-visible')
    expect(css).toContain('prefers-reduced-motion: reduce')
  })
})
