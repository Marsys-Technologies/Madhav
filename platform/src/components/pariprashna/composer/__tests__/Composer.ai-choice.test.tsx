import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Composer } from '../Composer'
import type { UseAiChoicesResult } from '../../hooks/useAiChoices'

const readyChoices: UseAiChoicesResult = {
  enabled: true, legacy: false, selection: { kind: 'default' },
  options: [{ key: 'default', group: null, label: 'Default — Personal OpenAI · GPT Safe',
    selection: { kind: 'default' }, disabled: false }],
  availability: 'ready', loading: false, mutationPending: false, canSubmit: true,
  statusMessage: '', select: vi.fn(), refresh: vi.fn(),
}

afterEach(cleanup)

describe('Composer AI choice integration', () => {
  it('keeps exact AI → Depth → Length order and fixed three-row 96px internal-scroll geometry', () => {
    render(<Composer streaming={false} onSubmit={vi.fn()} onStop={vi.fn()} aiChoices={readyChoices} />)
    const controls = screen.getByTestId('pp-composer-controls')
    const firstThreeControls = Array.from(controls.querySelectorAll('button')).slice(0, 3)
    expect(firstThreeControls[0]).toHaveAttribute('data-control', 'ai')
    expect(firstThreeControls[1]).toHaveTextContent('Depth')
    expect(firstThreeControls[2]).toHaveTextContent('Length')
    const textarea = screen.getByTestId('pp-composer-textarea')
    expect(textarea).toHaveAttribute('rows', '3')
    expect(textarea).toHaveStyle({ height: '96px', minHeight: '96px', maxHeight: '96px', overflowY: 'auto' })
    fireEvent.change(textarea, { target: { value: 'one\ntwo\nthree\nfour\nfive\nsix' } })
    expect(textarea).toHaveStyle({ height: '96px' })
  })

  it('submits strict AI selection identity with unchanged depth and length semantics', () => {
    const onSubmit = vi.fn()
    render(<Composer streaming={false} onSubmit={onSubmit} onStop={vi.fn()} aiChoices={readyChoices} />)
    fireEvent.change(screen.getByTestId('pp-composer-textarea'), { target: { value: 'Question' } })
    fireEvent.click(screen.getByTestId('pp-composer-send'))
    expect(onSubmit).toHaveBeenCalledWith('Question', 'adaptive', {
      aiSelection: { kind: 'default' }, readingDepth: 'auto', lengthTier: 'standard',
    })
  })

  it.each([
    ['loading', { loading: true, canSubmit: false, statusMessage: 'Loading AI choices…' }],
    ['mutation', { mutationPending: true, canSubmit: false, statusMessage: 'Saving AI choice…' }],
    ['missing default', { availability: 'default_required' as const, canSubmit: false, statusMessage: 'Choose a default in AI Console.' }],
    ['broken selection', { availability: 'selection_broken' as const, canSubmit: false, statusMessage: 'Repair this AI choice in AI Console.' }],
  ])('blocks Send for %s and announces safe remediation', (_name, overrides) => {
    const choices = { ...readyChoices, ...overrides }
    render(<Composer streaming={false} onSubmit={vi.fn()} onStop={vi.fn()} aiChoices={choices} />)
    fireEvent.change(screen.getByTestId('pp-composer-textarea'), { target: { value: 'Question' } })
    expect(screen.getByTestId('pp-composer-send')).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent(choices.statusMessage)
  })

  it('keeps the legacy model request byte-compatible when AI Console is flag-off', () => {
    const onSubmit = vi.fn()
    render(<Composer streaming={false} onSubmit={onSubmit} onStop={vi.fn()} aiChoices={{ ...readyChoices, enabled: false, legacy: true, options: [] }} />)
    fireEvent.change(screen.getByTestId('pp-composer-textarea'), { target: { value: 'Legacy question' } })
    fireEvent.click(screen.getByTestId('pp-composer-send'))
    expect(onSubmit).toHaveBeenCalledWith('Legacy question', 'adaptive', {
      modelId: undefined, readingDepth: 'auto', lengthTier: 'standard',
    })
  })
})
