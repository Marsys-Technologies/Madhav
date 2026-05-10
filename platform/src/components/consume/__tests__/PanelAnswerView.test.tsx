import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DivergenceReport } from '../DivergenceReport'
import { PanelAnswerView } from '../PanelAnswerView'
import { ConsumeChat } from '../ConsumeChat'
import type { DivergenceSummary, PanelResult, MemberAlignment } from '@/lib/synthesis/panel/types'
import type { DivergenceClassification, DivergenceInstance } from '@/lib/synthesis/panel/divergence_detector'

// ── Mock lucide-react ───────────────────────────────────────────────────────────

vi.mock('lucide-react', () => ({
  ChevronDown: ({ className }: { className?: string }) => (
    <span data-testid="chevron-down" className={className} />
  ),
  ChevronUp: ({ className }: { className?: string }) => (
    <span data-testid="chevron-up" className={className} />
  ),
  AlertTriangle: ({ className }: { className?: string }) => (
    <span data-testid="alert-triangle" className={className} />
  ),
  // Icons used by ConsumeChat and other deps
  Plus: () => <span />,
  PanelLeft: () => <span />,
  FileText: () => <span />,
  Keyboard: () => <span />,
  Gauge: () => <span />,
  Zap: () => <span />,
  Sparkles: () => <span />,
  FileQuestion: () => <span />,
  BookOpenText: () => <span />,
  User: () => <span />,
  RotateCcw: () => <span />,
}))

// ── Mock ConsumeChat dependencies ───────────────────────────────────────────────

vi.mock('@/hooks/useChatSession', () => ({
  useChatSession: vi.fn(() => ({
    messages: [],
    status: 'ready',
    error: null,
    isStreaming: false,
    canSend: true,
    send: vi.fn(),
    stop: vi.fn(),
    regenerate: vi.fn(),
    setMessages: vi.fn(),
    editAndResubmit: vi.fn(),
    conversationId: undefined,
  })),
}))

vi.mock('@/hooks/useScrollAnchor', () => ({
  useScrollAnchor: vi.fn(() => ({
    scrollRef: { current: null },
    bottomRef: { current: null },
    isAtBottom: true,
    scrollToBottom: vi.fn(),
  })),
}))

vi.mock('@/hooks/useHotkeys', () => ({ useHotkeys: vi.fn() }))

vi.mock('@/hooks/useFeedback', () => ({
  useFeedback: vi.fn(() => ({ ratings: {}, rate: vi.fn() })),
}))

vi.mock('@/hooks/useChatPreferences', () => ({
  useChatPreferences: vi.fn(() => ({
    model: 'claude-3-5-haiku-20241022',
    style: 'acharya',
    setModel: vi.fn(),
    setStyle: vi.fn(),
  })),
}))

vi.mock('@/hooks/useAttachments', () => ({
  useAttachments: vi.fn(() => ({
    attachments: [],
    addFiles: vi.fn(),
    remove: vi.fn(),
    clear: vi.fn(),
    canSend: true,
  })),
}))

vi.mock('@/hooks/useBranches', () => ({
  useBranches: vi.fn(() => ({
    viewingMessages: null,
    isViewingArchived: false,
    stats: {},
    stepBranch: vi.fn(),
    archiveBranch: vi.fn(),
    returnToLive: vi.fn(),
  })),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: vi.fn(), replace: vi.fn() })),
}))

vi.mock('@/components/chat/ChatShell', () => ({
  ChatShell: ({ children }: { children: React.ReactNode }) => <div data-testid="chat-shell">{children}</div>,
}))

vi.mock('@/components/chat/ConversationSidebar', () => ({
  ConversationSidebar: () => <div />,
}))

vi.mock('@/components/chat/AdaptiveMessageList', () => ({
  AdaptiveMessageList: () => <div />,
}))

vi.mock('@/components/chat/PendingAssistantBubble', () => ({
  PendingAssistantBubble: () => <div />,
}))

vi.mock('@/components/chat/Composer', () => ({
  Composer: vi.fn(({ onSubmit }: { onSubmit: (text: string) => void }) => (
    <button data-testid="composer-submit" onClick={() => onSubmit('test query')}>
      Submit
    </button>
  )),
}))

vi.mock('@/components/chat/WelcomeGreeting', () => ({
  WelcomeGreeting: () => <div data-testid="welcome-greeting" />,
}))

vi.mock('@/components/chat/ScrollToBottomButton', () => ({
  ScrollToBottomButton: () => <div />,
}))

vi.mock('@/components/chat/ShortcutsDialog', () => ({
  ShortcutsDialog: () => <div />,
}))

vi.mock('@/components/chat/CommandPalette', () => ({
  CommandPalette: () => <div />,
}))

vi.mock('@/components/chat/ModelStylePicker', () => ({
  ModelStylePicker: () => <div />,
}))

vi.mock('@/components/chat/ShareButton', () => ({
  ShareButton: () => <div />,
}))

vi.mock('@/components/disclosure/DisclosureTierBadge', () => ({
  DisclosureTierBadge: () => <div />,
}))

vi.mock('./ReportLibrary', () => ({
  ReportLibrary: () => <div />,
}))

vi.mock('./ReportReader', () => ({
  ReportReader: () => <div />,
}))

vi.mock('./StreamingAnswer', () => ({
  StreamingAnswer: () => <div />,
}))

vi.mock('./ValidatorFailureView', () => ({
  ValidatorFailureView: () => <div />,
}))

vi.mock('@/lib/chat/classify-error', () => ({
  classifyChatError: vi.fn(() => null),
}))

vi.mock('@/lib/ui/validator-error', () => ({
  parseValidatorError: vi.fn(() => null),
}))

vi.mock('@/lib/models/registry', () => ({
  MODELS: [],
  PROVIDER_LABEL: {},
}))

// ── Test fixtures ───────────────────────────────────────────────────────────────

const noOpClassification: DivergenceClassification = {
  has_divergence: false,
  instances: [],
  member_alignment_summary: {},
}

const noOpSummary: DivergenceSummary = {
  has_divergence: false,
  divergence_count: 0,
  summary_text: 'All panel members were in agreement.',
}

const divergentClassification: DivergenceClassification = {
  has_divergence: true,
  instances: [
    {
      class: 'DIS.class.factual',
      description: 'Members disagree on the exact date of a key event.',
      member_indices: [0, 2],
    } as DivergenceInstance,
    {
      class: 'DIS.class.interpretive',
      description: 'Members differ on the significance of Saturn transit.',
      member_indices: [1],
    } as DivergenceInstance,
    {
      class: 'DIS.class.scope',
      description: 'One member went beyond the stated question scope.',
      member_indices: [2],
    } as DivergenceInstance,
    {
      class: 'DIS.class.confidence',
      description: 'Members diverge on confidence level for career prediction.',
      member_indices: [0, 1],
    } as DivergenceInstance,
    {
      class: 'DIS.class.extension',
      description: 'One member extended the analysis to a related domain.',
      member_indices: [1],
    } as DivergenceInstance,
  ],
  member_alignment_summary: {
    M1: 'aligned',
    M2: 'partial',
    M3: 'dissent',
  },
}

const divergentSummary: DivergenceSummary = {
  has_divergence: true,
  divergence_count: 5,
  summary_text: 'Panel showed 5 divergence instances across multiple classes.',
}

function buildPanelResult(overrides: Partial<PanelResult> = {}): PanelResult {
  return {
    member_outputs: [
      {
        member_index: 0,
        model_id: 'claude-3-5-haiku-20241022',
        provider_family: 'anthropic',
        status: 'success',
        answer: 'Member 1 answer text here.',
        latency_ms: 1200,
      },
      {
        member_index: 1,
        model_id: 'gpt-4o-mini',
        provider_family: 'openai',
        status: 'success',
        answer: 'Member 2 answer text here.',
        latency_ms: 980,
      },
      {
        member_index: 2,
        model_id: 'gemini-1.5-flash',
        provider_family: 'google',
        status: 'success',
        answer: 'Member 3 answer text here.',
        latency_ms: 1450,
      },
    ],
    adjudication: {
      final_answer: 'This is the adjudicated final answer from the panel.',
      divergence_summary: noOpSummary,
      member_alignment: { M1: 'aligned', M2: 'aligned', M3: 'aligned' },
      adjudicator_model_id: 'claude-3-5-sonnet-20241022',
      latency_ms: 2100,
    },
    ...overrides,
  }
}

// ── DivergenceReport tests ──────────────────────────────────────────────────────

describe('DivergenceReport', () => {
  it('shows "Panel agreed" badge when no divergence', () => {
    render(
      <DivergenceReport
        classification={noOpClassification}
        divergenceSummary={noOpSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByLabelText('Panel agreed')).toBeInTheDocument()
  })

  it('shows summary text in the no-divergence path', () => {
    render(
      <DivergenceReport
        classification={noOpClassification}
        divergenceSummary={noOpSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('All panel members were in agreement.')).toBeInTheDocument()
  })

  it('renders color-coded rows for DIS.class.factual', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('Factual')).toBeInTheDocument()
    expect(screen.getByText(/Members disagree on the exact date/)).toBeInTheDocument()
  })

  it('renders color-coded rows for DIS.class.interpretive', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('Interpretive')).toBeInTheDocument()
    expect(screen.getByText(/significance of Saturn transit/)).toBeInTheDocument()
  })

  it('renders color-coded rows for DIS.class.scope', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('Scope')).toBeInTheDocument()
    expect(screen.getByText(/beyond the stated question scope/)).toBeInTheDocument()
  })

  it('renders color-coded rows for DIS.class.confidence', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('Confidence')).toBeInTheDocument()
    expect(screen.getByText(/confidence level for career/)).toBeInTheDocument()
  })

  it('renders color-coded rows for DIS.class.extension', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{}}
      />
    )
    expect(screen.getByText('Extension')).toBeInTheDocument()
    expect(screen.getByText(/extended the analysis/)).toBeInTheDocument()
  })

  it('renders aligned badge (green) for member alignment', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{ M1: 'aligned' as MemberAlignment }}
      />
    )
    expect(screen.getByText('aligned')).toBeInTheDocument()
    const badge = screen.getByText('aligned')
    expect(badge.className).toContain('green')
  })

  it('renders partial badge (amber) for member alignment', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{ M2: 'partial' as MemberAlignment }}
      />
    )
    expect(screen.getByText('partial')).toBeInTheDocument()
    const badge = screen.getByText('partial')
    expect(badge.className).toContain('amber')
  })

  it('renders dissent badge (rose/red) for member alignment', () => {
    render(
      <DivergenceReport
        classification={divergentClassification}
        divergenceSummary={divergentSummary}
        memberAlignment={{ M3: 'dissent' as MemberAlignment }}
      />
    )
    expect(screen.getByText('dissent')).toBeInTheDocument()
    const badge = screen.getByText('dissent')
    expect(badge.className).toContain('rose')
  })
})

// ── PanelAnswerView tests ───────────────────────────────────────────────────────

describe('PanelAnswerView', () => {
  it('renders the adjudicator final_answer as the main text', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    expect(
      screen.getByText('This is the adjudicated final answer from the panel.')
    ).toBeInTheDocument()
  })

  it('divergence section is collapsed by default', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    const divergenceRegion = screen.queryByRole('region', { name: 'Divergence analysis' })
    expect(divergenceRegion).not.toBeInTheDocument()
  })

  it('divergence section expands on toggle button click', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    const btn = screen.getByRole('button', { name: /show divergence analysis/i })
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('region', { name: 'Divergence analysis' })).toBeInTheDocument()
  })

  it('member outputs section is hidden by default', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    const membersRegion = screen.queryByRole('region', { name: 'Panel member outputs' })
    expect(membersRegion).not.toBeInTheDocument()
  })

  it('member outputs section expands on click', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    const btn = screen.getByRole('button', { name: /show panel members/i })
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('region', { name: 'Panel member outputs' })).toBeInTheDocument()
  })

  it('member answers are visible after expanding panel members', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    fireEvent.click(screen.getByRole('button', { name: /show panel members/i }))
    expect(screen.getByText('Member 1 answer text here.')).toBeInTheDocument()
    expect(screen.getByText('Member 2 answer text here.')).toBeInTheDocument()
    expect(screen.getByText('Member 3 answer text here.')).toBeInTheDocument()
  })

  it('degrade notice shown when degrade_notice is present', () => {
    const panelWithDegrade = buildPanelResult({
      degrade_notice: {
        failed_member_index: 2,
        reason: 'Model timeout',
        surviving_members: 2,
      },
    })
    render(<PanelAnswerView panel={panelWithDegrade} chartId="chart-123" />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent(/one panel member failed/i)
    expect(alert).toHaveTextContent(/proceeding with 2 member/i)
  })

  it('degrade notice absent when degrade_notice is not present', () => {
    render(<PanelAnswerView panel={buildPanelResult()} chartId="chart-123" />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

// ── ConsumeChat panel checkbox tests ───────────────────────────────────────────

const baseChatProps = {
  chartId: 'chart-abc',
  chartName: 'Test Chart',
  reports: [],
  conversations: [],
}

describe('ConsumeChat — panel checkbox', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('checkbox is hidden when panelModeEnabled=false', () => {
    render(<ConsumeChat {...baseChatProps} panelModeEnabled={false} />)
    expect(screen.queryByLabelText(/panel mode/i)).not.toBeInTheDocument()
  })

  it('checkbox is hidden when panelModeEnabled is not provided (defaults false)', () => {
    render(<ConsumeChat {...baseChatProps} />)
    expect(screen.queryByLabelText(/panel mode/i)).not.toBeInTheDocument()
  })

  it('checkbox is visible when panelModeEnabled=true', () => {
    render(<ConsumeChat {...baseChatProps} panelModeEnabled={true} />)
    expect(screen.getByLabelText(/panel mode/i)).toBeInTheDocument()
  })

  it('checkbox is initially unchecked', () => {
    render(<ConsumeChat {...baseChatProps} panelModeEnabled={true} />)
    const checkbox = screen.getByLabelText(/panel mode/i) as HTMLInputElement
    expect(checkbox.checked).toBe(false)
  })

  it('checkbox can be checked by the user', () => {
    render(<ConsumeChat {...baseChatProps} panelModeEnabled={true} />)
    const checkbox = screen.getByLabelText(/panel mode/i) as HTMLInputElement
    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)
  })

  it('checkbox auto-resets to unchecked after submit', () => {
    render(<ConsumeChat {...baseChatProps} panelModeEnabled={true} />)
    const checkbox = screen.getByLabelText(/panel mode/i) as HTMLInputElement
    // Check the box
    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)
    // Trigger submit via the mocked Composer button
    fireEvent.click(screen.getByTestId('composer-submit'))
    // Checkbox should be reset
    expect(checkbox.checked).toBe(false)
  })
})
