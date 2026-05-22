/**
 * ToolDisableToggle — toggle tool_registry.tool_enabled for a single MCP tool.
 *
 * Calls PATCH /api/admin/mcp/tool-registry/:toolName with {tool_enabled: boolean}.
 * The primitive dispatcher checks tool_enabled before executing (wired in S5).
 *
 * Disabled tools return 503 {tool_disabled: true} from the dispatcher.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

interface Props {
  toolName: string
  enabled: boolean
  onToggle?: () => void
}

async function setToolEnabled(toolName: string, enabled: boolean): Promise<void> {
  const res = await fetch(`/api/admin/mcp/tool-registry/${toolName}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_enabled: enabled }),
  })
  if (!res.ok) throw new Error(`Failed to update tool registry: ${res.status}`)
}

export function ToolDisableToggle({ toolName, enabled, onToggle }: Props) {
  const [optimistic, setOptimistic] = useState(enabled)
  const [confirming, setConfirming] = useState(false)

  const mutation = useMutation({
    mutationFn: (next: boolean) => setToolEnabled(toolName, next),
    onMutate: (next) => {
      setOptimistic(next)
    },
    onSuccess: () => {
      setConfirming(false)
      onToggle?.()
    },
    onError: () => {
      // Roll back optimistic update
      setOptimistic(enabled)
      setConfirming(false)
    },
  })

  // Require confirm before disabling (disabling is destructive — causes 503s)
  function handleClick() {
    if (optimistic) {
      // Trying to disable — require confirmation
      setConfirming(true)
    } else {
      // Re-enabling — no confirm needed
      mutation.mutate(true)
    }
  }

  if (confirming) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-yellow-400">Disable {toolName}?</span>
        <button
          onClick={() => mutation.mutate(false)}
          disabled={mutation.isPending}
          className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-300 hover:bg-red-500/30 disabled:opacity-40"
        >
          {mutation.isPending ? '…' : 'Confirm'}
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={handleClick}
      disabled={mutation.isPending}
      title={optimistic ? `Disable ${toolName}` : `Re-enable ${toolName}`}
      className={`
        relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent
        transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2
        focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50
        ${optimistic ? 'bg-green-600' : 'bg-muted-foreground/30'}
      `}
    >
      <span className="sr-only">{optimistic ? 'Enabled' : 'Disabled'}</span>
      <span
        className={`
          pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-lg ring-0
          transition-transform duration-200 ease-in-out
          ${optimistic ? 'translate-x-4' : 'translate-x-0'}
        `}
      />
    </button>
  )
}
