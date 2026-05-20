'use client'

import { useEffect } from 'react'

export default function PanchangError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    console.error('[Panchang] Error boundary caught:', error)
  }, [error])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <p
          className="mb-2 font-serif text-2xl"
          style={{ color: 'var(--brand-gold)' }}
        >
          ॥ Panchang Unavailable ॥
        </p>
        <p className="text-sm text-muted-foreground max-w-sm">
          The Panchang engine could not be reached. This is likely a transient
          sidecar failure. Please try again.
        </p>
        {error.digest && (
          <p className="mt-2 text-xs opacity-50 font-mono">
            digest: {error.digest}
          </p>
        )}
      </div>
      <button
        onClick={unstable_retry}
        className="brand-cta inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm"
      >
        Retry
      </button>
    </div>
  )
}
