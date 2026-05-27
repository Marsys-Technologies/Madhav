'use client'

import { useEffect } from 'react'
import { SharedConsumeError } from '@/components/consume/SharedConsumeError'

export default function ConsultError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[consult] route error:', error)
  }, [error])

  return <SharedConsumeError title="The chat hit a snag" error={error} reset={reset} />
}
