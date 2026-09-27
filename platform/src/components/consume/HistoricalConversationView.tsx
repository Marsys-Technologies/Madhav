import Link from 'next/link'
import type { ChartInputSnapshot } from '@/lib/charts/types'
import type { HistoricalTranscriptMessage } from '@/lib/conversations/historicalReading'

/**
 * Read-only transcript of a conversation archived because its chart's birth
 * details were corrected (Jātaka chart workspace, Task 8).
 *
 * Deliberately has no composer and no actions: the server refuses new turns
 * and mutations on this conversation, and this view never offers them. The
 * header shows the pre-correction inputs from the stored snapshot — never the
 * corrected chart row — so the historical context is not reconstructed.
 */
export interface HistoricalConversation {
  id: string
  chart_id: string
  title: string | null
  archived_at: string | null
  archive_reason: 'chart_details_changed' | null
  archived_chart_snapshot: ChartInputSnapshot | null
}

function formatBirthDate(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  if (!y || !m || !d) return isoDate
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

function formatOffset(minutes: number): string {
  const sign = minutes < 0 ? '−' : '+'
  const abs = Math.abs(minutes)
  return `UTC${sign}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`
}

// Display labels for VALID_AYANAMSHAS. Kept here because this is a server
// component and NewClientForm's AYANAMSHA_OPTIONS lives in a 'use client' module.
const AYANAMSHA_LABELS: Record<string, string> = {
  lahiri: 'Lahiri',
  true_chitra: 'True Chitra',
  kp: 'KP',
  raman: 'Raman',
  surya_siddhanta: 'Surya Sidd.',
}

function ayanamshaLabels(ids: string[]): string {
  return ids.map((id) => AYANAMSHA_LABELS[id] ?? id).join(', ')
}

function SnapshotDetails({ snapshot }: { snapshot: ChartInputSnapshot | null }) {
  if (!snapshot) return <p>The earlier chart details were not recorded for this reading.</p>
  const timezone =
    snapshot.timezone_id === null
      ? 'Timezone not recorded'
      : `${snapshot.timezone_id}${snapshot.effective_tz_offset_minutes === null ? '' : ` (${formatOffset(snapshot.effective_tz_offset_minutes)})`}`
  const coordinates =
    snapshot.birth_lat === null || snapshot.birth_lng === null
      ? 'Coordinates not recorded'
      : `${snapshot.birth_lat}, ${snapshot.birth_lng}`
  return (
    <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
      <div><dt className="jw-eyebrow">Born</dt><dd>{formatBirthDate(snapshot.birth_date)} · {snapshot.birth_time.slice(0, 5)}</dd></div>
      <div><dt className="jw-eyebrow">Place</dt><dd>{snapshot.birth_place}</dd></div>
      <div><dt className="jw-eyebrow">Time standard</dt><dd>{timezone}</dd></div>
      <div><dt className="jw-eyebrow">Coordinates</dt><dd>{coordinates}</dd></div>
      <div className="sm:col-span-2"><dt className="jw-eyebrow">Ayanāṃśas</dt><dd>{ayanamshaLabels(snapshot.ayanamshas)}</dd></div>
    </dl>
  )
}

export function HistoricalConversationView({
  conversation,
  messages,
}: {
  conversation: HistoricalConversation
  messages: HistoricalTranscriptMessage[]
}) {
  return (
    <main className="jw-root min-h-full px-4 py-8 sm:px-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-6">
        <header className="flex flex-col gap-3">
          <Link
            href={`/clients/${conversation.chart_id}`}
            className="jw-touch inline-flex min-h-11 w-fit items-center text-xs uppercase tracking-[0.2em] text-[var(--jw-gold-dim)] hover:text-[var(--jw-gold)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
          >
            ← Jātaka workspace
          </Link>
          <p className="jw-eyebrow">Historical · read-only</p>
          <h1 className="jw-display text-3xl">{conversation.title ?? 'Earlier reading'}</h1>
          <div role="note" className="jw-panel px-5 py-4 text-[var(--jw-ink-dim)]">
            <p className="text-sm text-[var(--jw-ink)]">
              This reading was made before the chart details were corrected. It is kept as history and cannot be
              continued; it reflects these earlier details:
            </p>
            <SnapshotDetails snapshot={conversation.archived_chart_snapshot} />
          </div>
        </header>

        <ol className="flex flex-col gap-4" aria-label="Transcript">
          {messages.map((message) => (
            <li
              key={message.id}
              className={
                message.role === 'user'
                  ? 'jw-panel self-end px-4 py-3 text-sm text-[var(--jw-ink)] sm:max-w-[80%]'
                  : 'px-1 text-[15px] leading-relaxed text-[var(--jw-ink)]'
              }
            >
              <p className="jw-eyebrow mb-1">{message.role === 'user' ? 'Question' : 'Reading'}</p>
              <p className="whitespace-pre-wrap">{message.text}</p>
            </li>
          ))}
          {messages.length === 0 && <li className="text-sm text-[var(--jw-ink-dim)]">No readable messages were kept.</li>}
        </ol>
      </div>
    </main>
  )
}
