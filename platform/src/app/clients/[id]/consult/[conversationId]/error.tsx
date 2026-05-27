'use client'

import { useEffect } from 'react'
import { SharedConsumeError } from '@/components/consume/SharedConsumeError'

export default function ConversationError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[consult/conversation] route error:', error)
  }, [error])

  return <SharedConsumeError title="This conversation hit a snag" error={error} reset={reset} />
}
