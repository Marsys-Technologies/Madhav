// Surface: /dashboard (Roster). Catches roster fetch failures, RLS denials, and any unhandled render error.
'use client'

import { useEffect } from 'react'
import { Button, buttonVariants } from '@/components/ui/button'
import Link from 'next/link'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[Dashboard error]', error.digest ?? error.name)
  }, [error])

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <h2 className="text-xl font-semibold">Something went wrong on our end</h2>
      <p className="max-w-sm text-sm text-muted-foreground">
        The roster could not be loaded. Try again in a moment. You can also return to sign-in.
      </p>
      <div className="flex gap-2">
        <Button onClick={reset}>Try again</Button>
        <Link href="/login" className={buttonVariants({ variant: 'outline' })}>
          Back to sign-in
        </Link>
      </div>
    </div>
  )
}
