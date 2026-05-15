'use client'

import type { ModelStack } from '@/lib/models/registry'
import { STACK_DISPLAY } from './displayNames'

// Stacks that always require confirmation (per standing native rule)
const ALWAYS_CONFIRM: ModelStack[] = ['anthropic']

// Cost threshold (USD per 1M input tokens) that triggers the dialog
const COST_THRESHOLD_PER_1M = 1.0

// Approximate input cost per 1M tokens for each stack's synthesis primary model.
// Conservative estimates — exact values from the catalog may differ.
const STACK_APPROX_COST: Partial<Record<ModelStack, number>> = {
  anthropic: 3.0,   // claude-opus-4-7
  gpt:       2.5,   // gpt-4o
  nim:       0.35,  // llama-70b via NIM
  gemini:    1.25,  // gemini-2.5-pro
  deepseek:  0.27,  // deepseek-v3
  marsys:    1.25,  // cross-provider; use gemini-pro estimate
}

export function shouldShowCostDialog(stack: ModelStack): boolean {
  if (ALWAYS_CONFIRM.includes(stack)) return true
  const cost = STACK_APPROX_COST[stack] ?? 0
  return cost >= COST_THRESHOLD_PER_1M
}

interface CostConfirmDialogProps {
  targetStack: ModelStack
  onConfirm:   () => void
  onCancel:    () => void
}

export function CostConfirmDialog({ targetStack, onConfirm, onCancel }: CostConfirmDialogProps) {
  const approxCost = STACK_APPROX_COST[targetStack] ?? 0
  const isAnthropicBanned = ALWAYS_CONFIRM.includes(targetStack)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-5 shadow-xl">
        <h3 className="text-sm font-semibold text-foreground">
          Set {STACK_DISPLAY[targetStack]} as system default?
        </h3>

        <p className="mt-2 text-xs text-muted-foreground">
          This affects background jobs that don&apos;t pick a stack themselves
          (health probes, scheduled tasks, internal pipelines). Live chat queries
          continue to use whatever the user selects in the composer.
        </p>

        {isAnthropicBanned && (
          <p className="mt-2 rounded bg-amber-500/10 px-2 py-1.5 text-xs text-amber-700 dark:text-amber-400">
            Note: Anthropic API usage is restricted by default. Confirm this is intentional.
          </p>
        )}

        <p className="mt-2 text-xs text-muted-foreground">
          Estimated synthesis cost: ~${approxCost.toFixed(2)} per 1M input tokens.
          Each query may consume 100K–2M tokens.
        </p>

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded border border-border px-3 py-1.5 text-xs text-foreground hover:bg-muted"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Set as default
          </button>
        </div>
      </div>
    </div>
  )
}
