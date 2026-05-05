'use client'

import * as React from 'react'

interface StatusBadgeProps {
  status: string
}

const STATUS_STYLES: Record<string, string> = {
  success: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
  error:   'bg-red-500/15 text-red-400 border border-red-500/25',
  timeout: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  pending: 'bg-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.60)] border border-[rgba(212,175,55,0.18)]',
}

const DEFAULT_STYLE =
  'bg-[rgba(212,175,55,0.08)] text-[rgba(212,175,55,0.50)] border border-[rgba(212,175,55,0.12)]'

export function StatusBadge({ status }: StatusBadgeProps): React.ReactElement {
  const tone = STATUS_STYLES[status] ?? DEFAULT_STYLE
  return (
    <span
      data-testid={`status-badge-${status}`}
      data-status={status}
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${tone}`}
    >
      {status}
    </span>
  )
}
