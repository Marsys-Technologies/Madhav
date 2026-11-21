import { createRoot } from 'react-dom/client'
import type { ComponentProps } from 'react'
import type { UIMessage } from 'ai'
import '@/app/globals.css'
import '@/app/journey1.css'
import '@/styles/theme_tokens.css'
import '@/lib/styles/marsys-theme.css'
import '@/components/profile/jataka-workspace.css'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { ConditionalChartSwitcherBar } from '@/components/nav/ConditionalChartSwitcherBar'
import ConsultLayout from '@/app/clients/[id]/consult/layout'
import { ConsumeChat } from '@/components/consume/ConsumeChat'
import { HistoricalConversationView } from '@/components/consume/HistoricalConversationView'

const params = new URLSearchParams(window.location.search)
// Modes: 'saved-portal' | 'saved-inline' | 'fresh-portal' | 'fresh-inline' | 'historical-portal' | 'historical-inline' | 'timeline'
const mode = params.get('mode') ?? 'saved-portal'
const withMessages = params.get('messages') !== '0'

const sampleMessages: UIMessage[] = withMessages
  ? [
      {
        id: 'u-1',
        role: 'user',
        parts: [{ type: 'text', text: 'What does my D10 chart show for career progression over the next two years?' }],
      },
      {
        id: 'a-1',
        role: 'assistant',
        parts: [
          {
            type: 'text',
            text:
              'Looking across your natal D1 and Dasamsa (D10) placements, the tenth lord receives structural reinforcement in the career division.\n\n' +
              '1. First factor: steady consolidation through sustained responsibility and disciplined execution.\n' +
              '2. Second factor: planetary period timing favors methodical restructuring rather than sudden pivots.\n' +
              '3. Third factor: watch transit triggers around the tenth house cusp for key milestones and role transitions.\n\n' +
              'Additional context: in longer consultations with multiple turns, the message thread can easily exceed the viewport height, so the message viewport must scroll cleanly inside its flex container while keeping the composer anchored below.',
          },
        ],
      },
      {
        id: 'u-2',
        role: 'user',
        parts: [{ type: 'text', text: 'How does Saturn influence that window specifically?' }],
      },
      {
        id: 'a-2',
        role: 'assistant',
        parts: [
          {
            type: 'text',
            text:
              'Saturn acts as a stabilizing anchor when well-disposed in D10, rewarding patience, governance, and verifiable results over short-term risk.\n\n' +
              'Ensure steady execution through mid-cycle transits and review major commitments around the upcoming dasha sub-period shift.',
          },
        ],
      },
    ]
  : []

function buildContent() {
  if (mode === 'timeline') {
    return (
      <div className="mx-auto max-w-[1000px] px-4 py-6" data-testid="timeline-sibling-root">
        <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h1 className="text-lg font-semibold text-zinc-100">Timeline Sibling Route Check</h1>
          <p className="text-sm text-zinc-400">Verifies AppShell main scrolling stays intact for non-consult routes.</p>
        </div>
        <div style={{ height: '1800px' }} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-zinc-300">
          Tall sibling content block (1800px)
        </div>
        <div data-testid="timeline-bottom-marker" className="mt-4 rounded-lg border border-zinc-800 p-3 text-sm text-zinc-200">
          Bottom marker reached
        </div>
      </div>
    )
  }

  if (mode === 'historical-portal' || mode === 'historical-inline') {
    const view = (
      <HistoricalConversationView
        conversation={{
          id: 'conv-1',
          chart_id: 'chart-1',
          title: 'Saved Career Reading',
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
            ayanamshas: ['lahiri', 'true_chitra'],
            captured_at: '2026-11-20T10:00:00Z',
          },
        }}
        messages={[
          { id: 'm1', role: 'user', text: 'What about career?', createdAt: '2026-11-20T10:00:00Z' },
          {
            id: 'm2',
            role: 'assistant',
            text: Array.from({ length: 18 }, (_, i) => `Paragraph ${i + 1}: Detailed historical analysis text for scrolling verification.`).join('\n\n'),
            createdAt: '2026-11-20T10:00:05Z',
          },
        ]}
      />
    )
    return mode === 'historical-portal' ? <ConsultLayout>{view}</ConsultLayout> : view
  }

  const isSaved = mode.startsWith('saved')
  const isPortal = mode.endsWith('portal')
  const chatProps: ComponentProps<typeof ConsumeChat> = {
    chartId: 'chart-1',
    chartName: 'Fictional Native',
    chartMeta: '1984-02-05 · Bhubaneswar',
    reports: [],
    conversations: [
      {
        id: 'conv-1',
        title: 'Career reading',
        created_at: '2026-11-20T10:00:00Z',
        chart_id: 'chart-1',
        user_id: 'user-1',
        module: 'consume',
      },
    ],
    currentConversationId: isSaved ? 'conv-1' : undefined,
    initialMessages: isSaved ? sampleMessages : undefined,
    panelModeEnabled: false,
    costVisibilityEnabled: false,
    audienceTier: 'super_admin',
    slashEnabled: true,
    exportEnabled: true,
    tokensEnabled: true,
    buildPreparationHref: '/clients/chart-1/nirmana',
  }
  const chat = <ConsumeChat {...chatProps} />

  const wrappedChat = !isSaved ? (
    <div data-testid="consult-page-root" data-permission="all" className="flex h-full min-h-0 flex-1 flex-col">
      {chat}
    </div>
  ) : (
    chat
  )

  return isPortal ? <ConsultLayout>{wrappedChat}</ConsultLayout> : wrappedChat
}

type AppShellProps = ComponentProps<typeof AppShell>

createRoot(document.getElementById('root')!).render(
  <ZoneRoot zone="ink">
    <AppShell
      user={{ uid: 'user-1', email: 'test@example.com', name: 'Test User' } as AppShellProps['user']}
      profile={{ role: 'super_admin', status: 'active' } as AppShellProps['profile']}
      breadcrumb={[
        { label: 'Birth Charts', href: '/dashboard' },
        { label: 'Fictional Native', href: '/clients/chart-1', current: true },
      ]}
    >
      <div
        data-testid="chart-page-frame"
        data-permission="all"
        data-chart-id="chart-1"
        className="has-[[data-testid=v2-chat-shell]]:flex has-[[data-testid=v2-chat-shell]]:h-full has-[[data-testid=v2-chat-shell]]:min-h-0 has-[[data-testid=v2-chat-shell]]:flex-1 has-[[data-testid=v2-chat-shell]]:flex-col has-[[data-testid=historical-reading]]:flex has-[[data-testid=historical-reading]]:h-full has-[[data-testid=historical-reading]]:min-h-0 has-[[data-testid=historical-reading]]:flex-1 has-[[data-testid=historical-reading]]:flex-col"
      >
        <ConditionalChartSwitcherBar
          currentChartId="chart-1"
          charts={[
            { id: 'chart-1', name: 'Fictional Native' },
            { id: 'chart-2', name: 'Second Native' },
          ]}
        />
        {buildContent()}
      </div>
    </AppShell>
  </ZoneRoot>,
)
