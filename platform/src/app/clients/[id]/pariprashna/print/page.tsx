import { redirect, notFound } from 'next/navigation'
import { getServerUser } from '@/lib/firebase/server'
import { ownedReading, readingMessages } from '@/lib/conversations/reading'
import { uuidLike } from '@/lib/conversations/consultation'
import { ReadingView, PrintReadingButton } from '@/components/chat/ReadingView'
export const dynamic = 'force-dynamic'
export default async function PrintPage({ params, searchParams }: {
  params: Promise<{ id: string }>; searchParams: Promise<{ conversationId?: string; messageId?: string }>
}) {
  const user = await getServerUser()
  if (!user) redirect('/login')
  const { id } = await params
  const { conversationId, messageId } = await searchParams
  if (!conversationId || !uuidLike.test(conversationId) || (messageId && !uuidLike.test(messageId))) notFound()
  const conversation = await ownedReading(conversationId, user.uid)
  if (!conversation || conversation.chart_id !== id) notFound()
  const messages = await readingMessages(conversationId, messageId)
  if (!messages.length) notFound()
  return <main className="dark mx-auto max-w-3xl bg-background px-4 py-8 text-foreground print:max-w-none print:bg-white print:text-black">
    <style>{`@media print { body { background:white!important; color:black!important; font-size:12pt } nav, aside {display:none!important} }`}</style>
    <h1 className="mb-6 text-2xl font-heading">{conversation.title ?? 'Consultation reading'}</h1>
    <PrintReadingButton /><ReadingView messages={messages} />
  </main>
}
