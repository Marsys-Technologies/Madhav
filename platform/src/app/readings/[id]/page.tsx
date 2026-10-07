import { redirect, notFound } from 'next/navigation'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { ownedReading } from '@/lib/conversations/reading'
import { uuidLike } from '@/lib/conversations/consultation'
export const dynamic = 'force-dynamic'
export default async function LegacyReading({ params }: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) redirect('/login')
  const { id } = await params
  if (!uuidLike.test(id)) notFound()
  const { rows } = await query<{ conversation_id: string; answer: string | null }>(`SELECT c.id AS conversation_id, m.id AS answer
    FROM conversations c LEFT JOIN conversation_messages m ON m.conversation_id=c.id AND m.id=$1 AND m.role='assistant'
    WHERE c.user_id=$2 AND (c.id=$1 OR m.id=$1) LIMIT 1`, [id, user.uid])
  const target = rows[0]
  const conversation = target && await ownedReading(target.conversation_id, user.uid)
  if (!conversation) notFound()
  redirect(`/clients/${encodeURIComponent(conversation.chart_id)}/pariprashna?thread=${encodeURIComponent(conversation.id)}${target.answer ? `&answer=${target.answer}#pp-answer-${target.answer}` : ''}`)
}
