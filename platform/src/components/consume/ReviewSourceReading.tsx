import Link from 'next/link'
import { notFound } from 'next/navigation'
import { readReviewSource } from '@/lib/conversations/reviewSource'
import { HistoricalConversationView } from './HistoricalConversationView'
import { ReviewSourceFocus } from './ReviewSourceFocus'
import styles from './historical-folio.module.css'

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
        <main
          aria-label="Source reading"
          tabIndex={0}
          className="jw-root h-full min-w-0 overflow-y-auto px-4 py-8 [overflow-wrap:anywhere] sm:px-6"
        >
          <div className="mx-auto max-w-3xl space-y-4">
            <header className={styles.header}>
              <Link href={`/clients/${chartId}`} className={`inline-flex min-h-11 items-center ${styles.returnLink}`}>
                Back to chart
              </Link>
              <h1 className="jw-display text-3xl">Source reading</h1>
            </header>
            <article id={answerId} tabIndex={-1} className="whitespace-pre-wrap">
              {source.answer.text}
            </article>
          </div>
        </main>
      )}
      {focusAnswer && <ReviewSourceFocus answerId={answerId} />}
    </>
  )
}
