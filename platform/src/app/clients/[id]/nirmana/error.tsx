// Surface: /clients/[id]/nirmana (Nirmāṇa build tracker). Catches build-stream errors, /api/chat/build failures, and pyramid query errors.
'use client'

import { useEffect } from 'react'
import { Button, buttonVariants } from '@/components/ui/button'
import Link from 'next/link'

export default function BuildError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[Build error]', error.digest ?? error.name)
  }, [error])

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <h2 className="text-xl font-semibold">Something went wrong on our end</h2>
      <p className="max-w-sm text-sm text-muted-foreground">
        The build workspace could not be loaded. Try again in a moment.
      </p>
      <div className="flex gap-2">
        <Button onClick={reset}>Try again</Button>
        <Link href="/dashboard" className={buttonVariants({ variant: 'outline' })}>
          Go to dashboard
        </Link>
      </div>
    </div>
  )
}
