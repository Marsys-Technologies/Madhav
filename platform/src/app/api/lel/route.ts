import { NextRequest, NextResponse } from 'next/server'
import { validate as isUuid } from 'uuid'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { appendPrediction, markPredictionOutcome } from '@/lib/lel/writer'
import { res } from '@/lib/errors'
import type { NewLELPrediction } from '@/lib/lel/writer'
import { EVENT_CLASSES } from '@/lib/event_classes'
import { deriveLelEventId, recordLelEvent, type LelEvent } from '@/lib/mcp/lel_event_writer'

const PORTAL_EVENT_SOURCE = 'portal-life-events'

function parseEventDate(value: unknown): Pick<LelEvent, 'event_date' | 'date_confidence'> | null {
  if (typeof value !== 'string') return null
  const match = /^(\d{4})(?:-(\d{2}|XX)-(\d{2}|XX))?$/.exec(value.trim())
  if (!match || match[1] === '0000' || (match[2] === 'XX' && match[3] !== 'XX')) return null
  const [, year, month, day] = match
  const hasMonth = !!month && month !== 'XX'
  const hasDay = !!day && day !== 'XX'
  const date = `${year}-${hasMonth ? month : '01'}-${hasDay ? day : '01'}`
  const parsed = new Date(`${date}T00:00:00Z`)
  if (!Number.isFinite(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== date) return null
  return { event_date: date, date_confidence: hasDay ? 'exact' : hasMonth ? 'month_known' : 'year_only' }
}

async function appendChartEvent(chartId: unknown, payload: unknown, actorUid: string) {
  if (typeof chartId !== 'string' || !isUuid(chartId)) return res.badRequest('A valid chart is required.')
  if (!payload || typeof payload !== 'object') return res.badRequest('Event details are required.')

  const fields = payload as Record<string, unknown>
  const date = parseEventDate(fields.date)
  if (!date) return res.badRequest('Enter a valid date, month, or year.')
  const eventClass = EVENT_CLASSES.find(item => item.event_class_id === fields.eventClass)
  if (!eventClass) return res.badRequest('Choose an event type.')
  const description = typeof fields.description === 'string' ? fields.description.trim() : ''
  if (!description || description.length > 4000 || description.includes('\0')) {
    return res.badRequest('Enter an event description of up to 4,000 characters.')
  }

  const { rows } = await query('SELECT id FROM charts WHERE id = $1', [chartId])
  if (!rows.length) return res.notFound('Chart not found.')

  const event: LelEvent = {
    ...date,
    event_class: eventClass.event_class_id,
    category: eventClass.lel_category,
    domain: eventClass.domain,
    description,
    outcome_observed: true,
    source_citation: PORTAL_EVENT_SOURCE,
  }
  const result = await recordLelEvent({
    chartId,
    event: { ...event, event_id: deriveLelEventId(chartId, event, PORTAL_EVENT_SOURCE) },
    provenance: { key_id: null, trace_id: null, actor_uid: actorUid },
  })
  return NextResponse.json(result)
}

export async function POST(req: NextRequest) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  if (req.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
    return res.badRequest('Send the request as JSON.')
  }

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return res.badRequest('Invalid JSON')
  }

  if (!body || typeof body !== 'object') {
    return res.badRequest('Invalid body')
  }

  const { action, chartId, payload } = body as Record<string, unknown>

  try {
    if (action === 'append_event') {
      return await appendChartEvent(chartId, payload, auth.user.uid)
    }

    if (action === 'append_prediction') {
      if (!chartId || typeof chartId !== 'string') {
        return res.badRequest('chartId required')
      }
      const result = await appendPrediction(chartId, payload as NewLELPrediction)
      return NextResponse.json(result)
    }

    if (action === 'mark_outcome') {
      const { predId, outcome } = body as Record<string, unknown>
      if (!predId || typeof predId !== 'string') {
        return res.badRequest('predId required')
      }
      await markPredictionOutcome(
        predId,
        outcome as { status: 'observed_confirmed' | 'observed_refuted'; body: string }
      )
      return NextResponse.json({ ok: true })
    }

    return res.badRequest(`Unknown action: ${action}`)
  } catch (e) {
    if (action === 'append_event') {
      console.error('[api/lel] Chart event could not be saved.')
      return res.internal('Could not save the event. Try again.')
    }
    console.error('[api/lel]', e)
    return res.internal(e instanceof Error ? e.message : undefined)
  }
}
