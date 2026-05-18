import { useMemo } from 'react'

/**
 * A normalized data part as seen by V2 consumers.
 * Live-stream (during request) and post-stream (after persistence) data parts
 * are surfaced with the same shape regardless of which transport landed them.
 */
export interface NormalizedDataPart {
  /** Discriminator e.g. 'data-stage', 'data-citation', 'data-correction', 'data-tool', 'data-panel-member', 'data-panel-meta', 'data-citation-gate', 'data-prediction-candidate', 'data-out-of-domain', 'data-title'. */
  type: `data-${string}`
  data: unknown
  /** Provenance — useful for tests + debugging. */
  source: 'metadata' | 'content'
}

/** Minimal structural type — matches ThreadMessage from @assistant-ui/react. */
interface MessageWithDataSources {
  metadata?: unknown
  content: ReadonlyArray<unknown>
}

/**
 * Returns the merged set of data parts associated with `message`, drawn from
 * both `message.metadata.unstable_data` (live-stream during request) and
 * `message.content` filtered to assistant-ui DataMessagePart shape
 * (`{type:'data', name:'<x>', data:...}` — post-stream after persistence).
 *
 * The two sources may emit the same logical part once each (during a session
 * that streams then persists). De-duplication is intentionally not applied
 * here — consumers that need uniqueness should de-dupe on a semantic key
 * (e.g. by `data.signal_id` for citations). Most consumers use array
 * .filter()/.find() and tolerate duplicate-but-identical entries.
 */
export function useDataParts(message: MessageWithDataSources): readonly NormalizedDataPart[] {
  return useMemo(() => {
    const result: NormalizedDataPart[] = []

    // Source 1: live-stream — message.metadata.unstable_data
    const metaParts = (message.metadata as { unstable_data?: ReadonlyArray<unknown> } | undefined)?.unstable_data ?? []
    for (const d of metaParts) {
      if (typeof d === 'object' && d !== null) {
        const obj = d as Record<string, unknown>
        if (typeof obj.type === 'string' && obj.type.startsWith('data-')) {
          result.push({ type: obj.type as `data-${string}`, data: obj.data, source: 'metadata' })
        }
      }
    }

    // Source 2: post-stream — message.content as DataMessagePart array
    const contentParts = (message.content as ReadonlyArray<unknown>) ?? []
    for (const p of contentParts) {
      if (typeof p === 'object' && p !== null) {
        const obj = p as Record<string, unknown>
        if (obj.type === 'data' && typeof obj.name === 'string') {
          result.push({ type: `data-${obj.name}` as `data-${string}`, data: obj.data, source: 'content' })
        }
      }
    }

    return result
  }, [message.metadata, message.content])
}
