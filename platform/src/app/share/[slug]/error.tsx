'use client'

import { useEffect } from 'react'
import { buttonVariants } from '@/components/ui/button'
import Link from 'next/link'

export default function ShareError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    console.error('[Share error]', error.digest ?? error.name)
  }, [error])

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-xl font-semibold">Shared reading unavailable</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        The shared reading is temporarily unavailable.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        <button
          type="button"
          onClick={unstable_retry}
          className={buttonVariants({ variant: 'default', className: 'min-h-11' })}
        >
          Try again
        </button>
        <Link href="/" className={buttonVariants({ variant: 'outline', className: 'min-h-11' })}>
          Go to home
        </Link>
      </div>
    </div>
  )
}
