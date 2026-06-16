import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { ConsumeChat } from '@/components/consume/ConsumeChat'
import { listConversations } from '@/lib/conversations'
import { configService } from '@/lib/config/index'
import type { AudienceTier } from '@/lib/prompts/types'
import type { UIMessage } from 'ai'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import type { CapabilityGateState } from '@/components/consume/ConsumeChatV2'

/**
 * Build an initialMessages array from ?prompt + ?context URL params.
 *
 * When the /panchang page's AskMadhavLink navigates here, it passes:
 *   ?prompt=<url-encoded visible question>
 *   ?context=<url-encoded JSON panchang context>
 *
 * We inject those as a single UIMessage with role=user whose content is:
 *
 *   <panchang_context>
 *   <!-- AUTO-INJECTED FROM /panchang ON YYYY-MM-DD -->
 *   { ...full panchang JSON... }
 *   </panchang_context>
 *
 *   <user_question>
 *   {the visible prompt}
 *   </user_question>
 *
 * The synthesis prompt recognises <panchang_context> blocks and cites them
 * without re-calling query_panchanga for the same date/location.
 *
 * Phase: 4C-8 (Item 2)
 */
function buildPanchangInitialMessages(
  prompt: string | undefined,
  contextJson: string | undefined,
): UIMessage[] | undefined {
  if (!prompt) return undefined

  let content: string

  if (contextJson) {
    let parsedDate = ''
    try {
      const parsed = JSON.parse(contextJson) as Record<string, unknown>
      parsedDate = parsed['date'] as string ?? ''
    } catch {
      // malformed context — skip the wrapper, just use the prompt
      return [
        {
          id: crypto.randomUUID(),
          role: 'user',
          content: prompt,
          parts: [{ type: 'text', text: prompt }],
        } as UIMessage,
      ]
    }

    const dateLine = parsedDate
      ? `<!-- AUTO-INJECTED FROM /panchang ON ${parsedDate} -->`
      : '<!-- AUTO-INJECTED FROM /panchang -->'

    content = [
      `<panchang_context>`,
      dateLine,
      contextJson,
      `</panchang_context>`,
      ``,
      `<user_question>`,
      prompt,
      `</user_question>`,
    ].join('\n')
  } else {
    content = prompt
  }

  return [
    {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      parts: [{ type: 'text', text: content }],
    } as UIMessage,
  ]
}

export default async function ConsultPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { id } = await params
  const sp = await searchParams

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string; birth_date: string; birth_place: string; client_id: string }>(
    'SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1',
    [id]
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  // WS-1-S3-B: Fetch pyramid layer status to derive capability gate state.
  // Runs in parallel with the reports + conversations queries.
  const [reportsResult, conversations, pyramidResult] = await Promise.all([
    query('SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain ASC', [id]),
    listConversations({ chartId: id, userId: access.user.uid, module: 'consume' }),
    query<{ layer_key: string; status: string }>(
      `SELECT layer_key, status FROM pyramid_layers WHERE chart_id = $1`,
      [id],
    ).catch(() => ({ rows: [] as { layer_key: string; status: string }[] })),
  ])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reports = reportsResult.rows as any[]

  const chartMeta = [chart.birth_date, chart.birth_place].filter(Boolean).join(' · ')

  const panelModeEnabled = configService.getFlag('PANEL_MODE_ENABLED')
  const costVisibilityEnabled = configService.getFlag('COST_VISIBILITY_FOR_USERS')
  const slashEnabled = true
  const exportEnabled = true
  const tokensEnabled = true
  const audienceTier: AudienceTier = access.role === 'super_admin' ? 'super_admin' : 'client'

  // 4C-8: Read ?prompt + ?context for AskMadhavLink deep links from /panchang
  const promptParam = typeof sp['prompt'] === 'string' ? sp['prompt'] : undefined
  const contextParam = typeof sp['context'] === 'string' ? sp['context'] : undefined
  const initialMessages = buildPanchangInitialMessages(promptParam, contextParam)

  // WS-1-S3-B: Derive capability gate state from pyramid layers.
  const cockpitHref = `/clients/${id}/nirmana`
  const pyramidRows = pyramidResult.rows
  const l1Row = pyramidRows.find((r) => r.layer_key === 'L1')
  const isL1Built = l1Row?.status === 'built' || l1Row?.status === 'complete'
  const isL1Building = l1Row?.status === 'building' || l1Row?.status === 'in_progress'

  const capabilityGateState: CapabilityGateState = pyramidRows.length === 0
    ? { state: 'no-build', cockpitHref }
    : isL1Built
      ? { state: 'ready', capabilities: [] } // capabilities populated client-side if needed
      : isL1Building
        ? { state: 'l1-building', cockpitHref }
        : { state: 'no-build', cockpitHref } // layers exist but L1 not started

  return (
    <div data-testid="consult-page-root" data-permission={access.permission}>
    <ConsumeChat
      chartId={id}
      chartName={chart.name}
      chartMeta={chartMeta}
      reports={reports}
      conversations={conversations.map(c => ({
        id: c.id,
        title: c.title,
        created_at: c.created_at,
        chart_id: c.chart_id,
        user_id: c.user_id,
        module: c.module,
      }))}
      panelModeEnabled={panelModeEnabled}
      costVisibilityEnabled={costVisibilityEnabled}
      audienceTier={audienceTier}
      initialMessages={initialMessages}
      slashEnabled={slashEnabled}
      exportEnabled={exportEnabled}
      tokensEnabled={tokensEnabled}
      capabilityGateState={capabilityGateState}
    />
    </div>
  )
}
