import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest'
import { render, screen, act, cleanup } from '@testing-library/react'
import type { ReactNode } from 'react'
import type { UIMessage } from 'ai'

const mocks = vi.hoisted(() => ({
  pathname: '/clients/chart-1/consult/conv-1',
}))

vi.mock('next/link', () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string
    children: ReactNode
  } & Record<string, unknown>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}))

vi.mock('next/navigation', () => ({
  usePathname: () => mocks.pathname,
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}))

vi.mock('next/dynamic', () => ({
  default: () => function DynamicStub() {
    return null
  },
}))

vi.mock('@/lib/firebase/client', () => ({
  auth: {},
  default: {},
}))

import { AppShell } from '@/components/shared/AppShell'
import { ConditionalChartSwitcherBar } from '@/components/nav/ConditionalChartSwitcherBar'
import { ConsumeOverlayPortal } from '../ConsumeOverlayPortal'
import { ConsumeChatV2 } from '../ConsumeChatV2'
import { HistoricalConversationView } from '../HistoricalConversationView'

const sampleMessages: UIMessage[] = [
  {
    id: 'u-1',
    role: 'user',
    parts: [{ type: 'text', text: 'What does D10 show for my career?' }],
  },
  {
    id: 'a-1',
    role: 'assistant',
    parts: [{ type: 'text', text: 'Your D10 tenth lord shows methodical progression.' }],
  },
]

function mockFetch(readiness: Record<string, unknown>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/build/data-readiness')) {
        return new Response(JSON.stringify(readiness), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      if (url.includes('/api/conversations')) {
        return new Response(JSON.stringify({ conversations: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      if (url.includes('/api/personas')) {
        return new Response(JSON.stringify({ personas: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response('{}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }),
  )
}

beforeAll(() => {
  if (typeof window.ResizeObserver === 'undefined') {
    window.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
  if (typeof window.matchMedia === 'undefined') {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  }
  if (typeof HTMLElement.prototype.scrollIntoView === 'undefined') {
    HTMLElement.prototype.scrollIntoView = vi.fn()
  }
})

beforeEach(() => {
  mocks.pathname = '/clients/chart-1/consult/conv-1'
  mockFetch({
    chart_id: 'chart-1',
    build_status: 'complete',
    ready: ['A3', 'A7', 'A8', 'A10', 'A15'],
    missing: [],
    partial_count: 5,
    total_count: 5,
  })
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('NIR-10 Consume / Consult Viewport Containment', () => {
  it('fills parent flex chain without nested h-dvh and keeps locked UI invariants', async () => {
    render(
      <ConsumeChatV2
        chartId="chart-1"
        chartName="Fictional Native"
        chartMeta="1984-02-05 · Bhubaneswar"
        reports={[]}
        conversations={[]}
        currentConversationId="conv-1"
        initialMessages={sampleMessages}
        audienceTier="super_admin"
        slashEnabled
        exportEnabled
        tokensEnabled
        buildPreparationHref="/clients/chart-1/nirmana"
      />,
    )

    const shell = await screen.findByTestId('v2-chat-shell')
    expect(shell.className).toContain('h-full')
    expect(shell.className).toContain('min-h-0')
    expect(shell.className).toContain('flex-1')
    expect(shell.className).not.toContain('h-dvh')

    const chatColumn = screen.getByTestId('v2-chat-column')
    expect(chatColumn.className).toContain('min-h-0')

    const mainChat = chatColumn.querySelector('main')
    expect(mainChat).not.toBeNull()
    expect(mainChat?.className).toContain('min-h-0')
    expect(mainChat?.className).toContain('flex-1')
    expect(mainChat?.className).toContain('overflow-hidden')

    const threadRoot = screen.getByTestId('v2-thread-root')
    expect(threadRoot.className).toContain('min-h-0')
    expect(threadRoot.className).toContain('flex-1')
    expect(threadRoot.className).toContain('overflow-hidden')

    const threadViewport = screen.getByTestId('v2-thread-viewport')
    expect(threadViewport.className).toContain('min-h-0')
    expect(threadViewport.className).toContain('flex-1')
    expect(threadViewport.className).toContain('overflow-y-auto')

    const bottomBar = screen.getByTestId('v2-bottom-bar')
    expect(bottomBar.className).toContain('shrink-0')

    const composerRoot = screen.getByTestId('v2-composer')
    expect(composerRoot.parentElement?.className).toContain('shrink-0')

    // Locked Consume UI invariants (platform/AGENTS.md)
    expect(screen.queryByTestId('v2-sidebar')).toBeNull()
    expect(screen.getByTestId('v2-trace-btn')).toBeInTheDocument()

    const input = screen.getByTestId('v2-composer-input') as HTMLTextAreaElement
    expect(input.getAttribute('rows')).toBe('3')
    expect(input.className).toContain('resize-none')
    expect(input.className).toContain('overflow-y-auto')
    expect(input.className).toContain('max-h-28')

    // Mobile 44px touch target preserved on send button
    const sendBtn = screen.getByTestId('v2-send-btn')
    expect(sendBtn.className).toContain('h-11')
    expect(sendBtn.className).toContain('w-11')
  })

  it('places QuestionSuggester inside ThreadPrimitive.Empty on fresh consult and hides it on saved consult', async () => {
    const { unmount } = render(
      <ConsumeChatV2
        chartId="chart-1"
        chartName="Fictional Native"
        reports={[]}
        conversations={[]}
        audienceTier="super_admin"
      />,
    )

    const suggesterHeading = await screen.findByText('Suggested questions')
    const viewport = screen.getByTestId('v2-thread-viewport')
    expect(viewport.contains(suggesterHeading)).toBe(true)

    unmount()
    render(
      <ConsumeChatV2
        chartId="chart-1"
        chartName="Fictional Native"
        reports={[]}
        conversations={[]}
        currentConversationId="conv-1"
        initialMessages={sampleMessages}
        audienceTier="super_admin"
      />,
    )

    await screen.findByTestId('v2-thread-viewport')
    expect(screen.queryByText('Suggested questions')).toBeNull()
  })

  it('keeps PartialDataBanner as a shrink-0 sibling outside the scrolling message viewport', async () => {
    mockFetch({
      chart_id: 'chart-1',
      build_status: 'partial',
      ready: ['A3', 'A7'],
      missing: ['A8', 'A10'],
      partial_count: 2,
      total_count: 4,
    })

    render(
      <ConsumeChatV2
        chartId="chart-1"
        chartName="Fictional Native"
        reports={[]}
        conversations={[]}
        currentConversationId="conv-1"
        initialMessages={sampleMessages}
        audienceTier="super_admin"
        buildPreparationHref="/clients/chart-1/nirmana"
      />,
    )

    const banner = await screen.findByRole('status')
    expect(banner.textContent).toMatch(/Chart partially built/i)
    const viewport = screen.getByTestId('v2-thread-viewport')
    expect(viewport.contains(banner)).toBe(false)
    expect(banner.parentElement?.className).toContain('shrink-0')
  })

  it('uses bounded h-full flex containment on NoBuildGate when zero assets are ready', async () => {
    mockFetch({
      chart_id: 'chart-1',
      build_status: 'empty',
      ready: [],
      missing: ['A3', 'A7', 'A8', 'A10', 'A15'],
      partial_count: 0,
      total_count: 5,
    })

    render(
      <ConsumeChatV2
        chartId="chart-1"
        chartName="Fictional Native"
        reports={[]}
        conversations={[]}
        audienceTier="super_admin"
        buildPreparationHref="/clients/chart-1/nirmana"
      />,
    )

    const shell = await screen.findByTestId('v2-chat-shell')
    expect(shell.className).toContain('h-full')
    expect(shell.className).toContain('min-h-0')
    expect(shell.className).not.toContain('h-dvh')
  })

  it('wires AppShell main and ConditionalChartSwitcherBar for inline flex propagation without altering non-consult routes', () => {
    const { container } = render(
      <AppShell
        user={{ uid: 'u-1', email: 'test@example.com', name: 'Test' }}
        profile={{ role: 'super_admin', status: 'active' }}
        breadcrumb={[{ label: 'Chart', href: '/clients/chart-1', current: true }]}
      >
        <div data-testid="chart-page-frame">
          <ConditionalChartSwitcherBar
            currentChartId="chart-1"
            charts={[{ id: 'chart-1', name: 'Fictional Native' }]}
          />
          <div data-testid="sibling-route">Sibling</div>
        </div>
      </AppShell>,
    )

    const mainEl = container.querySelector('#main-content')
    expect(mainEl?.className).toContain('min-h-0')
    expect(mainEl?.className).toContain('overflow-auto')
    expect(mainEl?.className).toContain('has-[[data-testid=v2-chat-shell]]:flex')
    expect(mainEl?.className).toContain('has-[[data-testid=v2-chat-shell]]:flex-col')
    expect(mainEl?.className).toContain('has-[[data-testid=v2-chat-shell]]:overflow-hidden')
    expect(mainEl?.className).toContain('has-[[data-testid=historical-reading]]:flex')

    const switcherBar = container.querySelector('[data-testid="chart-page-frame"] > div')
    expect(switcherBar?.className).toContain('shrink-0')
  })

  it('sizes ConsumeOverlayPortal from visualViewport when a virtual keyboard opens', async () => {
    const listeners = new Set<() => void>()
    let vvHeight = 844
    let vvOffsetTop = 0
    const originalVV = window.visualViewport
    Object.defineProperty(window, 'visualViewport', {
      configurable: true,
      value: {
        get height() {
          return vvHeight
        },
        get width() {
          return 390
        },
        get offsetTop() {
          return vvOffsetTop
        },
        get offsetLeft() {
          return 0
        },
        addEventListener: (_type: string, fn: () => void) => listeners.add(fn),
        removeEventListener: (_type: string, fn: () => void) => listeners.delete(fn),
      },
    })

    try {
      render(
        <ConsumeOverlayPortal>
          <div data-testid="portal-inner">Consult content</div>
        </ConsumeOverlayPortal>,
      )

      const inner = await screen.findByTestId('portal-inner')
      const portalOverlay = inner.parentElement?.parentElement as HTMLElement
      expect(portalOverlay.style.height).toBe('844px')
      expect(portalOverlay.style.top).toBe('0px')

      act(() => {
        vvHeight = 490
        vvOffsetTop = 12
        listeners.forEach((fn) => fn())
      })

      expect(portalOverlay.style.height).toBe('490px')
      expect(portalOverlay.style.top).toBe('12px')
    } finally {
      Object.defineProperty(window, 'visualViewport', {
        configurable: true,
        value: originalVV,
      })
    }
  })

  it('preserves HistoricalConversationView read-only archive layout and return link', () => {
    const { container } = render(
      <HistoricalConversationView
        conversation={{
          id: 'conv-1',
          chart_id: 'chart-1',
          title: 'Archived Career Reading',
          archived_at: '2026-11-20T10:00:00Z',
          archive_reason: 'chart_details_changed',
          archived_chart_snapshot: {
            name: 'Fictional Native',
            preferred_name: null,
            subject_name: null,
            birth_date: '1984-02-05',
            birth_time: '10:43:00',
            birth_place: 'Bhubaneswar',
            birth_lat: 20.2961,
            birth_lng: 85.8245,
            timezone_id: 'Asia/Kolkata',
            effective_tz_offset_minutes: 330,
            ayanamshas: ['lahiri'],
            captured_at: '2026-11-20T10:00:00Z',
          },
        }}
        messages={[{ id: 'm1', role: 'user', text: 'Career question', createdAt: '2026-11-20T10:00:00Z' }]}
      />,
    )

    const main = screen.getByTestId('historical-reading')
    expect(main.tagName).toBe('MAIN')
    expect(main.className).toContain('min-h-0')
    expect(main.className).toContain('flex-1')
    expect(main.className).toContain('overflow-y-auto')
    expect(screen.queryByTestId('v2-composer')).toBeNull()
    expect(container.querySelector('textarea')).toBeNull()

    const link = screen.getByRole('link', { name: /Jātaka workspace/i })
    expect(link).toHaveAttribute('href', '/clients/chart-1')
  })
})
