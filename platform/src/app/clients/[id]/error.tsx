'use client'

import { useEffect } from 'react'
import { Button, buttonVariants } from '@/components/ui/button'
import Link from 'next/link'

export default function ClientError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-xl font-semibold">Chart workspace unavailable</h1>
      <p className="text-sm text-muted-foreground max-w-sm">
        The chart workspace could not be loaded.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        <Link href="/dashboard" className={buttonVariants({ variant: 'outline', className: 'min-h-11' })}>
          Back to Birth Charts
        </Link>
        <Button onClick={unstable_retry} className="min-h-11">Try again</Button>
      </div>
    </div>
  )
}
