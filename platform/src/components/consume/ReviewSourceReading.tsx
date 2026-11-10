import Link from 'next/link'
import { notFound } from 'next/navigation'
import { readReviewSource } from '@/lib/conversations/reviewSource'
import { HistoricalConversationView } from './HistoricalConversationView'
import { ReviewSourceFocus } from './ReviewSourceFocus'

export async function ReviewSourceReading({
  chartId, conversationId, partId, userId, focusAnswer = false,
}: {
  chartId: string
  conversationId: string
  partId: string | string[]
  userId: string
  focusAnswer?: boolean
}) {
  const source = await readReviewSource(chartId, conversationId, partId, userId)
  if (!source) notFound()
  const answerId = `pp-answer-${source.answer.id}`
  return (
    <>
      {source.historical ? (
        <HistoricalConversationView conversation={source.conversation} messages={source.messages} targetAnswerId={source.answer.id} />
      ) : (
        <main className="jw-root mx-auto max-w-3xl space-y-4 px-6 py-8">
          <Link href={`/clients/${chartId}`} className="underline">Back to chart</Link>
          <h1 className="jw-display text-3xl">Source reading</h1>
          <article id={answerId} tabIndex={-1} className="whitespace-pre-wrap">
            {source.answer.text}
          </article>
        </main>
      )}
      {focusAnswer && <ReviewSourceFocus answerId={answerId} />}
    </>
  )
}
