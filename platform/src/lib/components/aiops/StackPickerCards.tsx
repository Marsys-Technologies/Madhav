'use client'

import type { ModelStack } from '@/lib/models/registry'
import { stackPicker } from '@/lib/models/registry'

const MARSYS_CARD = {
  stack:                 'marsys' as ModelStack,
  label:                 'MARSYS Stack',
  synthesisModelId:      'gemini-2.5-pro',
  synthesisContextWindow: 2_000_000,
  isDefault:             false,
}

export function StackPickerCards({ activeStack }: { activeStack: ModelStack }) {
  const cards = [...stackPicker(), MARSYS_CARD]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map(card => {
        const isActive = card.stack === activeStack
        return (
          <div
            key={card.stack}
            title="Selection editable in CP.2"
            className={[
              'cursor-not-allowed rounded-lg border p-3 transition-colors',
              isActive
                ? 'border-primary bg-primary/10 ring-1 ring-primary'
                : 'border-border bg-card hover:border-muted-foreground/40',
            ].join(' ')}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {card.stack.toUpperCase()}
              </span>
              {isActive && (
                <span className="rounded bg-primary px-1.5 py-0.5 text-[10px] font-bold text-primary-foreground">
                  ACTIVE
                </span>
              )}
            </div>
            <p className="mt-1 text-sm font-medium text-foreground">{card.label}</p>
            <p className="mt-0.5 truncate text-xs text-muted-foreground">{card.synthesisModelId}</p>
            {card.synthesisContextWindow && (
              <p className="mt-0.5 text-xs text-muted-foreground">
                {(card.synthesisContextWindow / 1_000_000).toFixed(0)}M ctx
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
