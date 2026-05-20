/**
 * Y-S4 — Reasoning Step Labels
 *
 * Amendment 2: parent-context integration tests for ReasoningProgress
 * timeline rendering. Mounts the component inside a shell that provides
 * the @assistant-ui/react message context via vi.mock.
 *
 * Click-path: Chat V2 → synthesis query → reasoning accordion opens →
 *   ### Step: <label> markers in text → left-margin timeline appears with
 *   active/completed indicators → response renders below.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import React from 'react'
import { ReasoningProgress } from '@/components/chat/ReasoningProgress'

// ── Mock @assistant-ui/react useMessagePartReasoning ─────────────────────────

let mockStatus: { type: 'running' | 'complete' | 'incomplete' } = { type: 'complete' }

vi.mock('@assistant-ui/react', () => ({
  useMessagePartReasoning: () => ({ status: mockStatus }),
}))

// ── Helper ────────────────────────────────────────────────────────────────────

function renderReasoning(text: string) {
  return render(<ReasoningProgress text={text} />)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ReasoningProgress step timeline — parent-context (Y-S4)', () => {
  beforeEach(() => {
    mockStatus = { type: 'complete' }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the reasoning accordion with no timeline when no step markers', () => {
    const { getByTestId, queryByTestId } = renderReasoning(
      'Some reasoning without any step markers.',
    )
    expect(getByTestId('reasoning-progress')).toBeTruthy()
    expect(queryByTestId('v2-reasoning-step-timeline')).toBeNull()
  })

  it('renders step timeline when ### Step: markers are present', () => {
    const text = [
      '### Step: Signal Assembly',
      'Assembled relevant signals from MSR.',
      '### Step: Cross-Domain Linking',
      'Linked signals across domains.',
      '### Step: Interpretation',
      'Interpreted the combined pattern.',
      '### Step: Response',
      'Drafted the final answer.',
    ].join('\n')

    const { getByTestId } = renderReasoning(text)
    expect(getByTestId('v2-reasoning-step-timeline')).toBeTruthy()
  })

  it('renders step labels in order', () => {
    const text = '### Step: Signal Assembly\ntext1\n### Step: Cross-Domain Linking\ntext2\n### Step: Interpretation\ntext3'
    const { getByTestId } = renderReasoning(text)

    expect(getByTestId('v2-reasoning-step-0').textContent).toContain('Signal Assembly')
    expect(getByTestId('v2-reasoning-step-1').textContent).toContain('Cross-Domain Linking')
    expect(getByTestId('v2-reasoning-step-2').textContent).toContain('Interpretation')
  })

  it('all steps show completed indicators when streaming is done', () => {
    mockStatus = { type: 'complete' }
    const text = '### Step: Signal Assembly\n### Step: Cross-Domain Linking'
    const { getAllByTestId } = renderReasoning(text)

    const doneIndicators = getAllByTestId('v2-step-done-indicator')
    expect(doneIndicators).toHaveLength(2)
  })

  it('last step shows active pulsing indicator while streaming', () => {
    mockStatus = { type: 'running' }
    const text = '### Step: Signal Assembly\n### Step: Cross-Domain Linking'
    const { getByTestId, getAllByTestId } = renderReasoning(text)

    // Last step is active
    expect(getByTestId('v2-step-active-indicator')).toBeTruthy()
    // First step is done
    const doneIndicators = getAllByTestId('v2-step-done-indicator')
    expect(doneIndicators).toHaveLength(1)
  })

  it('active indicator shows · character, completed indicators show ✓', () => {
    mockStatus = { type: 'running' }
    const text = '### Step: Signal Assembly\n### Step: Interpretation'
    const { getByTestId, getAllByTestId } = renderReasoning(text)

    expect(getByTestId('v2-step-active-indicator').textContent).toBe('·')
    expect(getAllByTestId('v2-step-done-indicator')[0].textContent).toBe('✓')
  })

  it('reasoning text is still visible alongside timeline', () => {
    const text = '### Step: Signal Assembly\nThis is the reasoning narration text.'
    const { getByTestId } = renderReasoning(text)

    expect(getByTestId('reasoning-content').textContent).toContain('Signal Assembly')
    expect(getByTestId('reasoning-content').textContent).toContain('This is the reasoning narration text.')
  })

  it('single step renders timeline with one entry', () => {
    const text = '### Step: Signal Assembly\nAnalyzing signals...'
    const { getByTestId, queryByTestId } = renderReasoning(text)

    expect(getByTestId('v2-reasoning-step-timeline')).toBeTruthy()
    expect(getByTestId('v2-reasoning-step-0').textContent).toContain('Signal Assembly')
    expect(queryByTestId('v2-reasoning-step-1')).toBeNull()
  })
})

// ── parseStepLabels unit tests (logic guard) ─────────────────────────────────

describe('parseStepLabels logic', () => {
  function parseStepLabels(text: string): string[] {
    const lines = text.split('\n')
    const steps: string[] = []
    for (const line of lines) {
      const m = line.match(/^### Step: (.+)$/)
      if (m) steps.push(m[1].trim())
    }
    return steps
  }

  it('returns empty for text with no markers', () => {
    expect(parseStepLabels('Just some text.')).toEqual([])
  })

  it('extracts single step', () => {
    expect(parseStepLabels('### Step: Signal Assembly')).toEqual(['Signal Assembly'])
  })

  it('extracts all four standard steps in order', () => {
    const text = '### Step: Signal Assembly\n### Step: Cross-Domain Linking\n### Step: Interpretation\n### Step: Response'
    expect(parseStepLabels(text)).toEqual([
      'Signal Assembly',
      'Cross-Domain Linking',
      'Interpretation',
      'Response',
    ])
  })

  it('ignores lines that do not start with ### Step:', () => {
    const text = 'preamble\n## Step: Not a step\n### Step: Real Step\n#### Step: Also not'
    expect(parseStepLabels(text)).toEqual(['Real Step'])
  })
})
