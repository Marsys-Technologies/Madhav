'use client'

/**
 * MARSYS-JIS Query Trace Panel — SSE subscription hook
 *
 * Subscribes to /api/trace/stream/[queryId] when queryId is provided.
 * Steps arrive as SSE events and are merged into the steps array by step_seq.
 * When queryId changes, the previous EventSource is closed and a new one opened.
 */

import { useEffect, useRef, useState } from 'react'
import type { TraceStep, TraceEvent } from '@/lib/trace/types'

export interface TraceState {
  steps: TraceStep[]
  done: boolean
  error: string | null
  planningActive: boolean
  planningModel: string | null
  capabilityRouteCount: number | null
  toolsSelected: string[] | null
  planningDoneAt: number | null
  queryIntentSummary: string | null
}

export function useTraceStream(queryId: string | null, historical = false): TraceState {
  const [steps, setSteps] = useState<TraceStep[]>([])
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [planningActive, setPlanningActive] = useState(false)
  const [planningModel, setPlanningModel] = useState<string | null>(null)
  const [capabilityRouteCount, setCapabilityRouteCount] = useState<number | null>(null)
  const [toolsSelected, setToolsSelected] = useState<string[] | null>(null)
  const [planningDoneAt, setPlanningDoneAt] = useState<number | null>(null)
  const [queryIntentSummary, setQueryIntentSummary] = useState<string | null>(null)
  const esRef = useRef<EventSource | null>(null)
  const activeQueryId = useRef<string | null>(null)

  useEffect(() => {
    if (!queryId) return

    // Close previous connection if queryId changed
    if (esRef.current && activeQueryId.current !== queryId) {
      esRef.current.close()
      esRef.current = null
    }

    // Reset state for new query — intentional synchronous reset on queryId change.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSteps([])
    setDone(false)
    setError(null)
    setPlanningActive(false)
    setPlanningModel(null)
    setCapabilityRouteCount(null)
    setToolsSelected(null)
    setPlanningDoneAt(null)
    setQueryIntentSummary(null)
    activeQueryId.current = queryId

    // EventSource doesn't support custom headers — pass mode as a URL query param instead.
    const url = `/api/trace/stream/${encodeURIComponent(queryId)}${historical ? '?mode=historical' : ''}`
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e: MessageEvent) => {
      try {
        const event: TraceEvent = JSON.parse(e.data as string)

        if (event.event === 'done') {
          setDone(true)
          es.close()
          return
        }

        if (event.event === 'planning_start') {
          setPlanningActive(true)
          setPlanningModel(event.planner_model_id ?? null)
          setCapabilityRouteCount(event.capability_route_count ?? null)
          return
        }

        if (event.event === 'planning_done') {
          setPlanningActive(false)
          setToolsSelected(event.tools_selected ?? null)
          setPlanningDoneAt(Date.now())
          setQueryIntentSummary(event.query_intent_summary ?? null)
          return
        }

        if (event.step) {
          setSteps(prev => {
            const idx = prev.findIndex(s => s.step_seq === event.step!.step_seq)
            if (idx >= 0) {
              // Update existing step (e.g. running → done)
              const next = [...prev]
              next[idx] = event.step!
              return next
            }
            // Insert new step, keep sorted by seq
            return [...prev, event.step!].sort((a, b) => a.step_seq - b.step_seq)
          })
        }
      } catch (err) {
        console.error('[useTraceStream] parse error', err)
      }
    }

    es.onerror = () => {
      setError('SSE connection error — check console.')
      es.close()
    }

    return () => {
      es.close()
      if (activeQueryId.current === queryId) {
        esRef.current = null
      }
    }
  }, [queryId, historical])

  return {
    steps,
    done,
    error,
    planningActive,
    planningModel,
    capabilityRouteCount,
    toolsSelected,
    planningDoneAt,
    queryIntentSummary,
  }
}
