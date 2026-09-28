'use client'

import type { AiChoice } from './types'

interface AiChoiceRadioProps {
  choice: AiChoice
  checked: boolean
  disabled?: boolean
  label: string
  onSelect: (choice: AiChoice) => Promise<unknown> | void
  unavailable?: boolean
  unverified?: boolean
}

export function AiChoiceRadio({ choice, checked, disabled, label, onSelect, unavailable, unverified }: AiChoiceRadioProps) {
  const accessibleLabel = unverified
    ? `${label} default verification unavailable`
    : `Use ${label} as default AI`
  const statusLabel = checked
    ? unavailable ? 'Default unavailable' : unverified ? 'Default unverified' : 'Default'
    : unverified ? 'Default verification unavailable' : 'Make default'
  return (
    <label className="aic-default-control">
      <input
        type="radio"
        name="ai-console-default"
        checked={checked}
        disabled={disabled}
        onChange={() => { void Promise.resolve(onSelect(choice)).catch(() => {}) }}
        aria-label={accessibleLabel}
      />
      <span>{statusLabel}</span>
    </label>
  )
}
