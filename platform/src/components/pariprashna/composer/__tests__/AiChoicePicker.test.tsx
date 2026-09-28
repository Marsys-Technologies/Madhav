import { useState } from 'react'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AiChoicePicker } from '../AiChoicePicker'
import { useAiChoices, type AiChoiceOption, type ConversationSelection } from '../../hooks/useAiChoices'

const CONNECTION_ID = '22222222-2222-4222-8222-222222222222'
const defaultSelection: ConversationSelection = { kind: 'default' }
const explicit: ConversationSelection = { kind: 'explicit', choice: {
  kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe',
} }
const options: AiChoiceOption[] = [
  { key: 'default', group: null, label: 'Default — Personal OpenAI · GPT Safe', selection: defaultSelection, disabled: false },
  { key: `provider:${CONNECTION_ID}:gpt-safe`, group: 'Provider connections', label: 'Personal OpenAI · GPT Safe', selection: explicit, disabled: false },
  { key: 'config:config-1', group: 'Custom configurations', label: 'Research quartet', selection: {
    kind: 'explicit', choice: { kind: 'custom_configuration', configurationId: '33333333-3333-4333-8333-333333333333' },
  }, disabled: false },
  { key: 'cli:claude_code:builtin', group: 'Local CLIs', label: 'Claude Code · Built-in default', selection: {
    kind: 'explicit', choice: { kind: 'local_cli', cliId: 'claude_code', modelId: null },
  }, disabled: false },
]

const pickerAggregate = {
  connections: [{ id: CONNECTION_ID, providerId: 'openai', name: 'Personal OpenAI', maskedSuffix: '•••1234',
    validationState: 'validated', confirmedValid: true, lastValidatedAt: null, lastCheckedAt: null, lastErrorCode: null, deletedAt: null }],
  models: [{ connectionId: CONNECTION_ID, modelId: 'gpt-safe', displayName: 'GPT Safe',
    compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
    supportsStructuredOutput: true, available: true }],
  configurations: [],
  defaultChoice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
  validationDisclosure: 'tiny charge',
}
const pickerClis = { clis: [] }

function jsonResponse(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } }))
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => { resolve = done })
  return { promise, resolve }
}

function IntegratedPicker() {
  const choices = useAiChoices(null, true)
  const [open, setOpen] = useState(false)
  return <AiChoicePicker options={choices.options} selected={choices.selection} open={open}
    disabled={choices.loading || choices.mutationPending} onOpenChange={setOpen}
    onSelect={choices.select} onRefresh={choices.refresh} />
}

function deferredRefresh() {
  const refreshed = deferred<Response>()
  let aggregateGets = 0
  vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL) => {
    if (String(url) === '/api/ai-console') {
      aggregateGets += 1
      return aggregateGets === 1 ? jsonResponse(pickerAggregate) : refreshed.promise
    }
    if (String(url) === '/api/ai-console/clis') return jsonResponse(pickerClis)
    throw new Error(`unexpected ${url}`)
  }))
  return { refreshed, aggregateGets: () => aggregateGets }
}

function renderPicker(overrides: Partial<React.ComponentProps<typeof AiChoicePicker>> = {}) {
  const props: React.ComponentProps<typeof AiChoicePicker> = {
    options, selected: defaultSelection, open: false, disabled: false,
    onOpenChange: vi.fn(), onSelect: vi.fn(), onRefresh: vi.fn(), ...overrides,
  }
  return { ...render(<AiChoicePicker {...props} />), props }
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('AiChoicePicker', () => {
  it('renders Default first and exactly the three approved explicit groups', () => {
    renderPicker({ open: true })
    expect(screen.getAllByRole('option').map(row => row.textContent)).toEqual(expect.arrayContaining([
      expect.stringContaining('Default'), expect.stringContaining('Personal OpenAI'),
      expect.stringContaining('Research quartet'), expect.stringContaining('Claude Code'),
    ]))
    expect(screen.getAllByRole('group').map(group => group.getAttribute('aria-label'))).toEqual([
      'Provider connections', 'Custom configurations', 'Local CLIs',
    ])
  })

  it('uses stable typed identities for Enter/Space and supports Escape dismissal with focus restoration', async () => {
    const onSelect = vi.fn()
    const onOpenChange = vi.fn()
    const { rerender } = renderPicker({ onSelect, onOpenChange })
    const trigger = screen.getByRole('button', { name: /ai default/i })
    await userEvent.click(trigger)
    expect(onOpenChange).toHaveBeenCalledWith(true)

    rerender(<AiChoicePicker options={options} selected={defaultSelection} open disabled={false}
      onOpenChange={onOpenChange} onSelect={onSelect} onRefresh={vi.fn()} />)
    const provider = screen.getByRole('option', { name: /^personal openai/i })
    fireEvent.keyDown(provider, { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledWith(explicit)

    const configuration = screen.getByRole('option', { name: /^research quartet/i })
    fireEvent.keyDown(configuration, { key: ' ' })
    expect(onSelect).toHaveBeenCalledWith(options[2].selection)

    fireEvent.keyDown(screen.getByRole('listbox'), { key: 'Escape' })
    expect(onOpenChange).toHaveBeenCalledWith(false)
    await waitFor(() => expect(screen.getByRole('button', { name: /ai default/i })).toHaveFocus())
  })

  it('dismisses the desktop popover on an outside pointer without selecting a row', () => {
    const onOpenChange = vi.fn()
    const onSelect = vi.fn()
    renderPicker({ open: true, onOpenChange, onSelect })
    fireEvent.mouseDown(document.body)
    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('keeps an already-open picker visible but disables every row while authority refreshes', async () => {
    const onOpenChange = vi.fn()
    const onSelect = vi.fn()
    renderPicker({ open: true, disabled: true, onOpenChange, onSelect })
    expect(screen.getByRole('listbox', { name: 'AI choices' })).toBeInTheDocument()
    expect(onOpenChange).not.toHaveBeenCalled()
    const provider = screen.getByRole('option', { name: /^personal openai/i })
    expect(provider).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(provider)
    fireEvent.keyDown(provider, { key: 'Enter' })
    expect(onSelect).not.toHaveBeenCalled()
  })

  it.each([
    ['desktop listbox', false],
    ['mobile sheet', true],
  ])('uses one click to refresh the %s while staying open, then focuses the refreshed selected row', async (_surface, mobile) => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({
      matches: mobile, addEventListener: vi.fn(), removeEventListener: vi.fn(),
    })))
    const { refreshed, aggregateGets } = deferredRefresh()
    render(<IntegratedPicker />)
    const trigger = screen.getByRole('button', { name: /ai default/i })
    await waitFor(() => expect(trigger).toBeEnabled())

    await userEvent.click(trigger)

    expect(aggregateGets()).toBe(2)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    const listbox = screen.getByRole('listbox', { name: 'AI choices' })
    expect(listbox.closest('.pp-sheet') !== null).toBe(mobile)
    expect(screen.getAllByRole('option').every(row => row.getAttribute('aria-disabled') === 'true')).toBe(true)

    await act(async () => {
      refreshed.resolve(await jsonResponse({ ...pickerAggregate,
        connections: [{ ...pickerAggregate.connections[0], name: 'Refreshed OpenAI' }] }))
      await refreshed.promise
    })
    const refreshedDefault = await screen.findByRole('option', { name: /default — refreshed openai/i })
    await waitFor(() => expect(refreshedDefault).toHaveFocus())
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
  })

  it.each([
    ['Enter', '{Enter}'],
    ['Space', ' '],
  ])('uses one %s activation and restores trigger focus only after Escape', async (_label, key) => {
    const { refreshed, aggregateGets } = deferredRefresh()
    render(<IntegratedPicker />)
    const trigger = screen.getByRole('button', { name: /ai default/i })
    await waitFor(() => expect(trigger).toBeEnabled())
    trigger.focus()

    await userEvent.keyboard(key)

    expect(aggregateGets()).toBe(2)
    expect(screen.getByRole('listbox', { name: 'AI choices' })).toBeInTheDocument()
    await act(async () => {
      refreshed.resolve(await jsonResponse(pickerAggregate))
      await refreshed.promise
    })
    const selected = await screen.findByRole('option', { name: /default — personal openai/i })
    await waitFor(() => expect(selected).toHaveFocus())

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('listbox', { name: 'AI choices' })).not.toBeInTheDocument()
    await waitFor(() => expect(trigger).toHaveFocus())
  })

  it('shows a selected broken identity as a disabled repair row and remains axe-clean', async () => {
    const broken: AiChoiceOption = { key: 'broken', group: null, label: 'Unavailable AI choice',
      selection: { kind: 'explicit', choice: { kind: 'local_cli', cliId: 'codex', modelId: null } }, disabled: true,
      detail: 'Repair this choice in AI Console.' }
    const { container } = renderPicker({ open: true, options: [options[0], broken], selected: broken.selection })
    expect(screen.getByRole('option', { name: /unavailable ai choice/i })).toHaveAttribute('aria-disabled', 'true')
    const results = await axe.run(container)
    expect(results.violations.filter(item => item.impact === 'critical' || item.impact === 'serious')).toEqual([])
  })

  it('renders the existing mobile sheet treatment and dismisses on the scrim', () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({
      matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn(),
    })))
    const onOpenChange = vi.fn()
    renderPicker({ open: true, onOpenChange })
    expect(screen.getByRole('listbox').closest('.pp-sheet')).toBeTruthy()
    fireEvent.click(document.querySelector('.pp-sheet-scrim')!)
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
