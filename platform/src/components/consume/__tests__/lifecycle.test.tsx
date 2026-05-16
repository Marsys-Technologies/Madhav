import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { StatusPip } from '../lifecycle/StatusPip'
import { ReasoningSlot } from '../lifecycle/ReasoningSlot'
import { ToolCallChronology } from '../lifecycle/ToolCallChronology'
import { FinalAnswerSlot } from '../lifecycle/FinalAnswerSlot'
import { MetadataBadge } from '../lifecycle/MetadataBadge'
import type { ToolCallRecord } from '@/lib/hooks/useChatLifecycle'

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock('@/lib/utils', () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/components/chat/StreamingMarkdown', () => ({
  StreamingMarkdown: ({ children }: { children: string }) => (
    <div data-testid="streaming-markdown">{children}</div>
  ),
}))

vi.mock('@/components/chat/StreamingDots', () => ({
  StreamingDots: () => <div data-testid="streaming-dots" />,
}))

vi.mock('@/lib/models/registry', () => ({
  getModelMeta: (id: string) => id === 'gemini-2.5-pro'
    ? { label: 'Gemini 2.5 Pro', provider: 'google' }
    : null,
  PROVIDER_LABEL: { google: 'Google', anthropic: 'Anthropic' },
}))

// ── StatusPip ──────────────────────────────────────────────────────────────────

describe('StatusPip', () => {
  it('renders processing label for queued state', () => {
    render(<StatusPip state="queued" />)
    expect(screen.getByText('Queuing request…')).toBeDefined()
  })

  it('renders processing label for planning state', () => {
    render(<StatusPip state="planning" />)
    expect(screen.getByText('Planning the response…')).toBeDefined()
  })

  it('renders processing label for composing state', () => {
    render(<StatusPip state="composing" />)
    expect(screen.getByText('Composing answer…')).toBeDefined()
  })

  it('renders nothing for idle state', () => {
    const { container } = render(<StatusPip state="idle" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing for complete state', () => {
    const { container } = render(<StatusPip state="complete" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing for error state', () => {
    const { container } = render(<StatusPip state="error" />)
    expect(container.firstChild).toBeNull()
  })

  it('has aria-live="polite" for screen reader support', () => {
    const { container } = render(<StatusPip state="planning" />)
    expect(container.querySelector('[aria-live="polite"]')).toBeDefined()
  })
})

// ── ReasoningSlot ──────────────────────────────────────────────────────────────

describe('ReasoningSlot', () => {
  it('renders nothing for idle state', () => {
    const { container } = render(
      <ReasoningSlot state="idle" reasoningText="" />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when modelHasReasoning is false', () => {
    const { container } = render(
      <ReasoningSlot state="reasoning" reasoningText="x" modelHasReasoning={false} />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows "Reasoning…" placeholder during reasoning state with no text', () => {
    render(<ReasoningSlot state="reasoning" reasoningText="" />)
    expect(screen.getByText('Reasoning…')).toBeDefined()
  })

  it('shows reasoning text when provided', () => {
    render(<ReasoningSlot state="reasoning" reasoningText="Deep thought" />)
    const matches = screen.getAllByText(/Deep thought/)
    expect(matches.length).toBeGreaterThan(0)
  })
})

// ── ToolCallChronology ─────────────────────────────────────────────────────────

describe('ToolCallChronology', () => {
  const sampleCalls: ToolCallRecord[] = [
    { callId: 'c1', name: 'msr_sql', args: { limit: 10 }, ts: 1000 },
  ]

  it('renders nothing when toolCalls is empty', () => {
    const { container } = render(
      <ToolCallChronology state="complete" toolCalls={[]} audienceTier="super_admin" />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing for client tier', () => {
    const { container } = render(
      <ToolCallChronology state="complete" toolCalls={sampleCalls} audienceTier="client" />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders tool call count for super_admin tier', () => {
    render(
      <ToolCallChronology state="complete" toolCalls={sampleCalls} audienceTier="super_admin" />,
    )
    expect(screen.getByText('1 tool call')).toBeDefined()
  })
})

// ── FinalAnswerSlot ────────────────────────────────────────────────────────────

describe('FinalAnswerSlot', () => {
  it('renders nothing for idle state with no text', () => {
    const { container } = render(<FinalAnswerSlot state="idle" finalText="" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders StreamingDots when composing with empty text', () => {
    render(<FinalAnswerSlot state="composing" finalText="" />)
    expect(screen.getByTestId('streaming-dots')).toBeDefined()
  })

  it('renders StreamingMarkdown with text when composing', () => {
    render(<FinalAnswerSlot state="composing" finalText="Answer text" />)
    expect(screen.getByTestId('streaming-markdown')).toBeDefined()
    expect(screen.getByText('Answer text')).toBeDefined()
  })

  it('renders StreamingMarkdown for complete state', () => {
    render(<FinalAnswerSlot state="complete" finalText="Final answer" />)
    expect(screen.getByTestId('streaming-markdown')).toBeDefined()
  })

  it('renders nothing for queued state with no text', () => {
    const { container } = render(<FinalAnswerSlot state="queued" finalText="" />)
    expect(container.firstChild).toBeNull()
  })
})

// ── MetadataBadge ──────────────────────────────────────────────────────────────

describe('MetadataBadge', () => {
  it('renders nothing when modelMeta is null', () => {
    const { container } = render(<MetadataBadge modelMeta={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders model label when modelMeta is provided', () => {
    render(
      <MetadataBadge
        modelMeta={{ modelId: 'gemini-2.5-pro', cost: 0.002, latencyMs: 1200 }}
      />,
    )
    expect(screen.getByText('Gemini 2.5 Pro')).toBeDefined()
  })

  it('renders cost capsule', () => {
    render(
      <MetadataBadge
        modelMeta={{ modelId: 'gemini-2.5-pro', cost: 0.0042, latencyMs: 900 }}
      />,
    )
    expect(screen.getByText('$0.0042')).toBeDefined()
  })

  it('renders latency capsule', () => {
    render(
      <MetadataBadge
        modelMeta={{ modelId: 'gemini-2.5-pro', cost: 0.001, latencyMs: 2500 }}
      />,
    )
    expect(screen.getByText('2.5s')).toBeDefined()
  })
})

// ── MetadataBadge CO.2: click-to-expand + requestId (AC.CO2.3, AC.CO2.4) ──────

describe('MetadataBadge CO.2 — expanded token breakdown', () => {
  const FULL_META = {
    modelId: 'gemini-2.5-pro',
    cost: 0.012,
    latencyMs: 4200,
    requestId: 'req-abc-123',
    usage: {
      inputTokens: 1500,
      outputTokens: 300,
      reasoningTokens: 50,
      cacheReadTokens: 200,
      cacheWriteTokens: 100,
    },
  }

  it('does not show token breakdown before clicking', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    expect(screen.queryByText('Input tokens')).toBeNull()
    expect(screen.queryByText('req-abc-123')).toBeNull()
  })

  it('shows input token count after clicking expand', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    const btn = screen.getByRole('button', { name: /Model metadata/i })
    fireEvent.click(btn)
    expect(screen.getByText('Input tokens')).toBeDefined()
    expect(screen.getByText('1,500')).toBeDefined()
  })

  it('shows output token count after clicking expand', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.getByText('Output tokens')).toBeDefined()
    expect(screen.getByText('300')).toBeDefined()
  })

  it('shows reasoning tokens when > 0', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.getByText('Reasoning tokens')).toBeDefined()
    expect(screen.getByText('50')).toBeDefined()
  })

  it('shows cache read tokens when > 0', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.getByText('Cache read')).toBeDefined()
    expect(screen.getByText('200')).toBeDefined()
  })

  it('shows cache write tokens when > 0', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.getByText('Cache write')).toBeDefined()
    expect(screen.getByText('100')).toBeDefined()
  })

  it('shows requestId in expanded view (AC.CO2.4)', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.getByText('Request ID')).toBeDefined()
    expect(screen.getByText('req-abc-123')).toBeDefined()
  })

  it('toggles collapse on second click', () => {
    render(<MetadataBadge modelMeta={FULL_META} />)
    const btn = screen.getByRole('button', { name: /Model metadata/i })
    fireEvent.click(btn)
    expect(screen.getByText('Input tokens')).toBeDefined()
    fireEvent.click(btn)
    expect(screen.queryByText('Input tokens')).toBeNull()
  })

  it('omits reasoning tokens row when 0', () => {
    render(
      <MetadataBadge
        modelMeta={{ ...FULL_META, usage: { ...FULL_META.usage, reasoningTokens: 0 } }}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.queryByText('Reasoning tokens')).toBeNull()
  })

  it('omits requestId row when not provided', () => {
    const { modelId, cost, latencyMs, usage } = FULL_META
    render(<MetadataBadge modelMeta={{ modelId, cost, latencyMs, usage }} />)
    fireEvent.click(screen.getByRole('button', { name: /Model metadata/i }))
    expect(screen.queryByText('Request ID')).toBeNull()
  })
})

// ── Source-level guard: AC.CO2.1 (input panel cleanup) ────────────────────────
// After α7: legacy content lives in ConsumeChatLegacy.tsx; ConsumeChat.tsx is the thin switch.

describe('AC.CO2.1 — model name removed from input panel for flag-ON', () => {
  it('consumeUiV2Enabled ternary controls lifecycle-slot vs legacy-path in legacy file', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChatLegacy.tsx'),
      'utf8',
    )
    // consumeUiV2Enabled branches into lifecycle slot (true) vs legacy path (false)
    expect(src).toContain('consumeUiV2Enabled ?')
    expect(src).toContain('Flag-OFF: legacy path')
  })

  it('ModelStylePicker (stack selector) is always rendered in legacy file', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChatLegacy.tsx'),
      'utf8',
    )
    expect(src).toContain('ModelStylePicker')
    expect(src).toContain('TierPicker')
  })
})

// ── Source-level guard: AC.CO1.5 ──────────────────────────────────────────────
// After α7: legacy content lives in ConsumeChatLegacy.tsx; ConsumeChat.tsx is the thin switch.

describe('AC.CO1.5 — flag-off path preserves legacy components', () => {
  it('ConsumeChatLegacy.tsx contains legacy LiveReasoningCard (flag-off path)', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChatLegacy.tsx'),
      'utf8',
    )
    expect(src).toContain('LiveReasoningCard')
    expect(src).toContain('StreamingAnswer')
  })

  it('ConsumeChatLegacy.tsx contains lifecycle slot components (flag-on branch within legacy)', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChatLegacy.tsx'),
      'utf8',
    )
    expect(src).toContain('StatusPip')
    expect(src).toContain('ReasoningSlot')
    expect(src).toContain('FinalAnswerSlot')
    expect(src).toContain('useChatLifecycle')
  })

  it('ConsumeChat.tsx thin switch delegates to ConsumeChatLegacy and ConsumeChatV2', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChat.tsx'),
      'utf8',
    )
    expect(src).toContain('ConsumeChatLegacy')
    expect(src).toContain('ConsumeChatV2')
    expect(src).toContain('chatV2Enabled')
  })
})
