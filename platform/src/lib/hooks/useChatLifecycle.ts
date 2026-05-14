'use client'

import { useEffect, useReducer } from 'react'
import type { ModelInteraction, ModelInteractionEvent } from '@/lib/adapters/types'

// ── State machine types ────────────────────────────────────────────────────────

export type ChatLifecycleState =
  | 'idle'
  | 'queued'
  | 'planning'
  | 'retrieving'
  | 'reasoning'
  | 'tool_calling'
  | 'composing'
  | 'complete'
  | 'error'
  | 'cancelled'

export interface ToolCallRecord {
  callId: string
  name: string
  args: unknown
  result?: unknown
  ts: number
}

export interface ChatLifecycleSnapshot {
  state: ChatLifecycleState
  /** Accumulated text from all reasoning_delta events. */
  reasoningText: string
  /** Chronological tool_call + tool_result pairs, matched by callId. */
  toolCalls: ToolCallRecord[]
  /** Accumulated text from all text_delta events. */
  finalText: string
  /** Populated from the finish event's ModelInteraction. */
  modelMeta: {
    modelId: string
    cost?: number
    latencyMs?: number
    usage?: unknown
  } | null
  error?: { message: string; code?: string }
}

export interface UseChatLifecycleOptions {
  stream: ReadableStream<ModelInteractionEvent> | null
}

// ── Reducer ────────────────────────────────────────────────────────────────────

export type ChatLifecycleAction =
  | { type: 'STATUS'; status: ChatLifecycleState }
  | { type: 'REASONING_DELTA'; text: string }
  | { type: 'TOOL_CALL'; callId: string; name: string; args: unknown; ts: number }
  | { type: 'TOOL_RESULT'; callId: string; result: unknown }
  | { type: 'TEXT_DELTA'; text: string }
  | { type: 'FINISH'; interaction: ModelInteraction }
  | { type: 'ERROR'; error: { message: string; code?: string } }
  | { type: 'CANCEL' }
  | { type: 'RESET' }

export const INITIAL_SNAPSHOT: ChatLifecycleSnapshot = {
  state: 'idle',
  reasoningText: '',
  toolCalls: [],
  finalText: '',
  modelMeta: null,
}

export function chatLifecycleReducer(
  state: ChatLifecycleSnapshot,
  action: ChatLifecycleAction,
): ChatLifecycleSnapshot {
  switch (action.type) {
    case 'STATUS':
      return { ...state, state: action.status }

    case 'REASONING_DELTA':
      return { ...state, reasoningText: state.reasoningText + action.text }

    case 'TOOL_CALL':
      return {
        ...state,
        toolCalls: [
          ...state.toolCalls,
          { callId: action.callId, name: action.name, args: action.args, ts: action.ts },
        ],
      }

    case 'TOOL_RESULT':
      return {
        ...state,
        toolCalls: state.toolCalls.map(tc =>
          tc.callId === action.callId ? { ...tc, result: action.result } : tc,
        ),
      }

    case 'TEXT_DELTA':
      return { ...state, finalText: state.finalText + action.text }

    case 'FINISH':
      return {
        ...state,
        state: 'complete',
        modelMeta: {
          modelId: action.interaction.modelId,
          cost: action.interaction.usage.costUsd,
          latencyMs: action.interaction.usage.latencyMs,
          usage: action.interaction.usage,
        },
      }

    case 'ERROR':
      return { ...state, state: 'error', error: action.error }

    case 'CANCEL':
      return { ...state, state: 'cancelled' }

    case 'RESET':
      return INITIAL_SNAPSHOT

    default:
      return state
  }
}

// ── Hook ───────────────────────────────────────────────────────────────────────

/**
 * Subscribes to a ReadableStream<ModelInteractionEvent> and returns a
 * ChatLifecycleSnapshot that React can render.
 *
 * The state machine inside mirrors the Phase 2 ModelInteractionEvent union:
 *   status events → state transitions
 *   reasoning_delta events → reasoningText accumulation
 *   tool_call / tool_result → toolCalls chronology
 *   text_delta → finalText accumulation
 *   finish → complete + modelMeta populated
 *   error → error state
 *
 * When stream is null, the snapshot stays in 'idle'. This is the CO.1 default
 * since the full stream wiring is completed in CO.2/CO.3.
 */
export function useChatLifecycle({ stream }: UseChatLifecycleOptions): ChatLifecycleSnapshot {
  const [snapshot, dispatch] = useReducer(chatLifecycleReducer, INITIAL_SNAPSHOT)

  useEffect(() => {
    if (!stream) {
      dispatch({ type: 'RESET' })
      return
    }

    let cancelled = false
    const reader = stream.getReader()

    async function consume() {
      try {
        while (!cancelled) {
          const { done, value } = await reader.read()
          if (done || cancelled) break

          const event = value
          switch (event.type) {
            case 'status':
              dispatch({ type: 'STATUS', status: event.status })
              break
            case 'reasoning_delta':
              dispatch({ type: 'REASONING_DELTA', text: event.text })
              break
            case 'tool_call':
              dispatch({
                type: 'TOOL_CALL',
                callId: event.callId,
                name: event.name,
                args: event.args,
                ts: event.ts,
              })
              break
            case 'tool_result':
              dispatch({ type: 'TOOL_RESULT', callId: event.callId, result: event.result })
              break
            case 'text_delta':
              dispatch({ type: 'TEXT_DELTA', text: event.text })
              break
            case 'finish':
              dispatch({ type: 'FINISH', interaction: event.interaction })
              break
            case 'error':
              dispatch({ type: 'ERROR', error: event.error })
              break
          }
        }
      } catch {
        if (!cancelled) {
          dispatch({ type: 'ERROR', error: { message: 'Stream read error' } })
        }
      } finally {
        reader.releaseLock()
      }
    }

    consume()

    return () => {
      cancelled = true
      reader.cancel().catch(() => {})
    }
  }, [stream])

  return snapshot
}
