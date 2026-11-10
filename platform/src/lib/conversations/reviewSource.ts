import 'server-only'
import { query } from '@/lib/db/client'
import { consultationMessages, ownedConsultation, uuidLike } from './consultation'
import { loadHistoricalConversationMessages } from './historicalReading'
import { isCorrectionArchived } from './readOnly'

export async function readReviewSource(
  chartId: string,
  conversationId: string,
  partId: string | string[],
  userId: string,
) {
  if (!uuidLike.test(chartId) || !uuidLike.test(conversationId) ||
      typeof partId !== 'string' || !uuidLike.test(partId)) return null

  const conversation = await ownedConsultation(conversationId, userId)
  if (conversation?.chart_id !== chartId) return null

  const { rows } = await query<{ id: string }>(
    `SELECT m.id FROM message_parts p
       JOIN conversation_messages m ON m.id = p.message_id
       JOIN conversations c ON c.id = m.conversation_id
      WHERE p.id = $1 AND m.conversation_id = $2 AND m.role = 'assistant'
        AND c.chart_id = $3 AND c.user_id = $4`,
    [partId, conversationId, chartId, userId],
  )
  const answerId = rows[0]?.id
  if (!answerId) return null

  const historical = isCorrectionArchived(conversation)
  if (!historical) {
    const messages = await consultationMessages(conversationId)
    if (!messages.some(message => message.id === answerId &&
      message.role === 'assistant' && message.metadata_json?.acharya_reading_receipt)) return null
  }

  const messages = await loadHistoricalConversationMessages(conversationId)
  const answer = messages.find(message => message.id === answerId && message.role === 'assistant')
  return answer ? { conversation, historical, messages, answer } : null
}
