'use client'

import { useState } from 'react'
import type { ModelStack } from '@/lib/models/registry'
import { stackPicker } from '@/lib/models/registry'
import { shouldShowCostDialog, CostConfirmDialog } from './CostConfirmDialog'

const MARSYS_CARD = {
  stack:                  'marsys' as ModelStack,
  label:                  'MARSYS Stack',
  synthesisModelId:       'gemini-2.5-pro',
  synthesisContextWindow: 2_000_000,
  isDefault:              false,
}

interface StackPickerCardsProps {
  activeStack:  ModelStack
  onStackChange?: (newStack: ModelStack) => void
}

export function StackPickerCards({ activeStack, onStackChange }: StackPickerCardsProps) {
  const [active,  setActive]  = useState<ModelStack>(activeStack)
  const [pending, setPending] = useState<ModelStack | null>(null)
  const [saving,  setSaving]  = useState(false)

  const cards = [...stackPicker(), MARSYS_CARD]

  function requestSwitch(stack: ModelStack) {
    if (stack === active) return
    if (shouldShowCostDialog(stack)) {
      setPending(stack)
    } else {
      commitSwitch(stack)
    }
  }

  async function commitSwitch(stack: ModelStack) {
    setPending(null)
    setSaving(true)
    try {
      await fetch('/api/admin/aiops/stack', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active_stack: stack }),
      })
      setActive(stack)
      onStackChange?.(stack)
    } catch { /* silently fail */ }
    setSaving(false)
  }

  return (
    <>
      {pending && (
        <CostConfirmDialog
          targetStack={pending}
          onConfirm={() => commitSwitch(pending)}
          onCancel={() => setPending(null)}
        />
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {cards.map(card => {
          const isActive = card.stack === active
          return (
            <button
              key={card.stack}
              type="button"
              disabled={saving}
              onClick={() => requestSwitch(card.stack)}
              className={[
                'rounded-lg border p-3 text-left transition-colors disabled:cursor-not-allowed',
                isActive
                  ? 'border-primary bg-primary/10 ring-1 ring-primary'
                  : 'border-border bg-card hover:border-muted-foreground/40 cursor-pointer',
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
            </button>
          )
        })}
      </div>
    </>
  )
}
