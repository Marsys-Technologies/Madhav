import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Next.js navigation ──────────────────────────────────────────────────────
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => null,
  usePathname: () => '/clients/chart-123/build',
}))

// ── Hooks ────────────────────────────────────────────────────────────────────
vi.mock('@/hooks/useBuildChatAdapter', () => ({
  useBuildChat: () => ({
    messages: [],
    status: 'ready',
    error: undefined,
    isStreaming: false,
    canSend: true,
    send: vi.fn(),
    stop: vi.fn(),
    regenerate: vi.fn(),
    setMessages: vi.fn(),
    conversationId: undefined,
  }),
}))

vi.mock('@/hooks/useBranches', () => ({
  useBranches: () => ({
    viewingMessages: null,
    isViewingArchived: false,
    stats: {},
    archiveBranch: vi.fn(),
    stepBranch: vi.fn(),
    returnToLive: vi.fn(),
  }),
}))

vi.mock('@/hooks/useFeedback', () => ({
  useFeedback: () => ({
    ratings: {},
    rate: vi.fn(),
  }),
}))

vi.mock('@/hooks/useScrollAnchor', () => ({
  useScrollAnchor: () => ({
    scrollRef: { current: null },
    bottomRef: { current: null },
    isAtBottom: true,
    scrollToBottom: vi.fn(),
  }),
}))

vi.mock('@/hooks/useHotkeys', () => ({
  useHotkeys: vi.fn(),
}))

vi.mock('@/hooks/useAttachments', () => ({
  useAttachments: () => ({
    attachments: [],
    addFiles: vi.fn(),
    remove: vi.fn(),
    canSend: true,
  }),
}))

// ── Heavy child components — mock as labelled divs ───────────────────────────
vi.mock('@/components/chat/ChatShell', () => ({
  ChatShell: ({ children, sidebar, rightPanel }: {
    children?: React.ReactNode
    sidebar?: React.ReactNode
    rightPanel?: React.ReactNode
  }) => (
    <div data-testid="chat-shell">
      {sidebar}
      <div data-testid="chat-shell-main">{children}</div>
      {rightPanel}
    </div>
  ),
}))

vi.mock('@/components/chat/ConversationSidebar', () => ({
  ConversationSidebar: () => <div data-testid="conversation-sidebar" />,
}))

vi.mock('@/components/chat/AdaptiveMessageList', () => ({
  AdaptiveMessageList: () => <div data-testid="adaptive-message-list" />,
}))

vi.mock('@/components/chat/Composer', () => ({
  Composer: ({ placeholder }: { placeholder?: string }) => (
    <div data-testid="composer">
      <textarea placeholder={placeholder} aria-label="Composer input" />
    </div>
  ),
}))

vi.mock('@/components/build/BuildRightPane', () => ({
  BuildRightPane: () => <div data-testid="build-right-pane" />,
}))

// ── Other chat components that BuildChat imports ─────────────────────────────
vi.mock('@/components/chat/WelcomeGreeting', () => ({
  WelcomeGreeting: ({ chartName }: { chartName: string }) => (
    <div data-testid="welcome-greeting">{chartName}</div>
  ),
}))

vi.mock('@/components/chat/PendingAssistantBubble', () => ({
  PendingAssistantBubble: () => <div data-testid="pending-assistant-bubble" />,
}))

vi.mock('@/components/chat/ScrollToBottomButton', () => ({
  ScrollToBottomButton: () => <div data-testid="scroll-to-bottom" />,
}))

vi.mock('@/components/chat/ShortcutsDialog', () => ({
  ShortcutsDialog: () => <div data-testid="shortcuts-dialog" />,
}))

vi.mock('@/components/chat/CommandPalette', () => ({
  CommandPalette: () => <div data-testid="command-palette" />,
}))

vi.mock('@/components/chat/ShareButton', () => ({
  ShareButton: () => <div data-testid="share-button" />,
}))

// ── Import the component under test ──────────────────────────────────────────
import { BuildChat } from '@/components/build/BuildChat'

const defaultProps = {
  chartId: 'chart-123',
  chartName: 'Test Chart',
  conversations: [],
  arc: [],
  activePhaseId: 'M1',
  brief: null,
  insights: [],
  mirrorPairs: [],
  layers: [],
}

describe('BuildChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes chartName through to WelcomeGreeting', () => {
    render(<BuildChat {...defaultProps} chartName="My Chart" />)
    expect(screen.getByTestId('welcome-greeting').textContent).toContain('My Chart')
  })

  it('does not render AdaptiveMessageList when messages are empty', () => {
    render(<BuildChat {...defaultProps} />)
    expect(screen.queryByTestId('adaptive-message-list')).toBeNull()
  })
})
