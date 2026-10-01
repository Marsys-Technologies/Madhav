'use client'

import { useRouter } from 'next/navigation'
import { useTransition } from 'react'
import { RotateCw } from 'lucide-react'

export function RefreshButton() {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()

  return (
    <button
      onClick={() => startTransition(() => router.refresh())}
      disabled={isPending}
      className="inline-flex items-center gap-1.5 rounded-md border border-[#4a381c] bg-[#14110b] px-2.5 py-1.5 text-xs font-medium text-[#d2a23c] transition-colors hover:bg-[#211a10] disabled:opacity-50"
      title="Refresh page"
    >
      <RotateCw className={`h-3.5 w-3.5 ${isPending ? 'animate-spin' : ''}`} />
      {isPending ? 'Refreshing…' : 'Refresh'}
    </button>
  )
}
