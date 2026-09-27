'use client'

import type { AiChoice } from './types'

interface AiChoiceRadioProps {
  choice: AiChoice
  checked: boolean
  disabled?: boolean
  label: string
  onSelect: (choice: AiChoice) => Promise<unknown> | void
  unavailable?: boolean
}

export function AiChoiceRadio({ choice, checked, disabled, label, onSelect, unavailable }: AiChoiceRadioProps) {
  return (
    <label className="aic-default-control">
      <input
        type="radio"
        name="ai-console-default"
        checked={checked}
        disabled={disabled}
        onChange={() => { void Promise.resolve(onSelect(choice)).catch(() => {}) }}
        aria-label={`Use ${label} as default AI`}
      />
      <span>{checked ? (unavailable ? 'Default unavailable' : 'Default') : 'Make default'}</span>
    </label>
  )
}
