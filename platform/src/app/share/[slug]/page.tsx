import { notFound } from 'next/navigation'
import Link from 'next/link'
import { query } from '@/lib/db/client'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { SharedConversation } from './SharedConversation'

export const dynamic = 'force-dynamic'

export default async function SharedConversationPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  const shareResult = await query<{
    conversation_id: string
    revoked_at: string | null
    expires_at: string | null
    hide_reasoning: boolean
    hide_methodology: boolean
  }>(
    'SELECT conversation_id, revoked_at, expires_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE slug=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())',
    [slug]
  )
  const share = shareResult.rows[0] ?? null

  if (!share) notFound()

  const conversationResult = await query<{
    id: string
    title: string
    chart_id: string
    created_at: string
  }>('SELECT * FROM conversations WHERE id=$1', [share.conversation_id])
  const conversation = conversationResult.rows[0] ?? null
  if (!conversation) notFound()

  const chartResult = await query<{ name: string; birth_date: string; birth_place: string }>(
    'SELECT name, birth_date, birth_place FROM charts WHERE id=$1',
    [conversation.chart_id]
  )
  const chart = chartResult.rows[0] ?? null

  const messages = await loadConversationMessagesV2(conversation.id)

  // X-S8: selective share — only apply when flag is enabled
  const selectiveShareEnabled = process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE === 'true'
  const hideReasoning = selectiveShareEnabled && (share.hide_reasoning ?? false)
  const hideMethodology = selectiveShareEnabled && (share.hide_methodology ?? false)

  return (
    <div className="mx-auto flex min-h-[100dvh] max-w-3xl flex-col px-4 py-6 print:max-w-none print:px-0 print:py-0">
      {/* X-S9: @media print — inline style ensures ≥12pt body text in print context */}
      <style>{`@media print { body { font-size: 12pt; } }`}</style>

      <header className="mb-6 border-b border-border pb-4 print:border-b-0 print:mb-4">
        {/* "Shared conversation" label is UI chrome — hidden in print */}
        <p className="text-[11px] font-medium uppercase tracking-widest text-muted-foreground print:hidden">
          Shared conversation
        </p>
        <h1 className="mt-1 font-heading text-2xl font-semibold text-foreground print:text-black print:mt-0">
          {conversation.title ?? 'Untitled chat'}
        </h1>
        {chart?.name && (
          <p className="mt-1 text-sm text-muted-foreground print:text-gray-600">{chart.name}</p>
        )}
      </header>
      <main className="flex-1 print:text-black">
        <SharedConversation
          messages={messages}
          hideReasoning={hideReasoning}
          hideMethodology={hideMethodology}
        />
      </main>
      {/* Footer is navigation chrome — hidden in print */}
      <footer className="mt-8 border-t border-border pt-4 text-center text-xs text-muted-foreground print:hidden">
        <Link href="/" className="hover:text-foreground">
          MARSYS-JIS
        </Link>
      </footer>
    </div>
  )
}
