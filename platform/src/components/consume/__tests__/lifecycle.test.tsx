import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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

// ── Source-level guard: AC.CO1.5 ──────────────────────────────────────────────

describe('AC.CO1.5 — flag-off path preserves legacy components', () => {
  it('ConsumeChat.tsx references legacy LiveReasoningCard in flag-off branch', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChat.tsx'),
      'utf8',
    )
    expect(src).toContain('LiveReasoningCard')
    expect(src).toContain('StreamingAnswer')
    expect(src).toContain('Flag-OFF: legacy path')
  })

  it('ConsumeChat.tsx references lifecycle slot components in flag-on branch', () => {
    const src = fs.readFileSync(
      path.resolve(__dirname, '..', 'ConsumeChat.tsx'),
      'utf8',
    )
    expect(src).toContain('StatusPip')
    expect(src).toContain('ReasoningSlot')
    expect(src).toContain('FinalAnswerSlot')
    expect(src).toContain('useChatLifecycle')
  })
})
