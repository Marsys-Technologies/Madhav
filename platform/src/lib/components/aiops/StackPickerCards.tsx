'use client'

import { useEffect, useState, useTransition } from 'react'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import type { ModelStack } from '@/lib/models/registry'
import { stackPicker } from '@/lib/models/registry'
import { STACK_DISPLAY } from './displayNames'

interface StackPickerCardsProps {
  viewingStack: ModelStack
}

interface HealthCounts {
  green: number
  red:   number
  amber: number
  dim:   number
  total: number
}

type HealthSummaryResponse = Partial<Record<ModelStack, HealthCounts>>

export function StackPickerCards({ viewingStack }: StackPickerCardsProps) {
  const [health, setHealth]       = useState<HealthSummaryResponse | null>(null)
  const [, startTransition]       = useTransition()
  const router                    = useRouter()
  const pathname                  = usePathname()
  const searchParams              = useSearchParams()

  const stacks = stackPicker()

  useEffect(() => {
    let cancelled = false
    fetch('/api/admin/aiops/health/summary')
      .then(r => r.ok ? r.json() as Promise<HealthSummaryResponse> : null)
      .then(data => { if (!cancelled && data) setHealth(data) })
      .catch(() => null)
    return () => { cancelled = true }
  }, [])

  function viewStack(stack: ModelStack) {
    if (stack === viewingStack) return
    const params = new URLSearchParams(searchParams?.toString() ?? '')
    params.set('stack', stack)
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`, { scroll: false })
    })
  }

  return (
    <div className="flex flex-wrap gap-2">
      {stacks.map(card => {
        const isViewing = card.stack === viewingStack
        const counts    = health?.[card.stack]
        return (
          <button
            key={card.stack}
            type="button"
            onClick={() => viewStack(card.stack)}
            aria-pressed={isViewing}
            aria-label={`View ${STACK_DISPLAY[card.stack]} pipeline`}
            className={[
              'inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-medium transition-all',
              isViewing
                ? 'border-[var(--brand-gold)] bg-[rgba(var(--brand-gold-rgb),0.12)] text-[var(--brand-gold)]'
                : 'cursor-pointer border-border text-muted-foreground hover:border-[rgba(var(--brand-gold-rgb),0.35)] hover:text-foreground',
            ].join(' ')}
          >
            <span>{STACK_DISPLAY[card.stack]}</span>
            <HealthPip counts={counts} active={isViewing} />
          </button>
        )
      })}
    </div>
  )
}

function HealthPip({ counts, active }: { counts: HealthCounts | undefined; active: boolean }) {
  if (!counts || counts.total === 0) {
    return <span className="text-[10px] opacity-50">—</span>
  }

  let color = 'var(--muted-foreground)'
  if (counts.red > 0)        color = 'var(--status-halt)'
  else if (counts.amber > 0) color = 'var(--status-warn)'
  else if (counts.green > 0) color = 'var(--status-success)'

  return (
    <span
      className="inline-flex items-center gap-1 text-[10px]"
      title={`${counts.green} pass · ${counts.amber} stale · ${counts.red} fail · ${counts.dim} never_probed`}
    >
      <span
        aria-hidden
        className="inline-block size-1.5 rounded-full"
        style={{ background: color, boxShadow: active ? `0 0 5px ${color}` : undefined }}
      />
      <span className="tabular-nums">{counts.green}/{counts.total}</span>
    </span>
  )
}
