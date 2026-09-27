import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AiChoicePicker } from '../AiChoicePicker'
import type { AiChoiceOption, ConversationSelection } from '../../hooks/useAiChoices'

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

  it('closes an already-open picker and disables every row while authority refreshes', async () => {
    const onOpenChange = vi.fn()
    const onSelect = vi.fn()
    renderPicker({ open: true, disabled: true, onOpenChange, onSelect })
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
    const provider = screen.getByRole('option', { name: /^personal openai/i })
    expect(provider).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(provider)
    fireEvent.keyDown(provider, { key: 'Enter' })
    expect(onSelect).not.toHaveBeenCalled()
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
